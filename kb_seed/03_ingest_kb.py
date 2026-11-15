import os
import re
import glob
import json
import hashlib
import tiktoken
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document as DocxDocument
from bs4 import BeautifulSoup

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")
KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kb_docs")


def parse_markdown_frontmatter(raw_text: str):
    """Extracts key: value metadata headers between --- markers and returns (meta_dict, body)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text.strip(), flags=re.DOTALL)
    if not match:
        return {}, raw_text.strip()
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, match.group(2).strip()


def extract_document_content(file_path: str):
    """Normalizes .md, .html, .docx, and .pdf files into (metadata_dict, markdown_sections_text)."""
    root_name, ext = os.path.splitext(file_path)
    ext = ext.lower()
    filename = os.path.basename(file_path)

    if ext == ".md":
        with open(file_path, "r", encoding="utf-8") as f:
            meta, body = parse_markdown_frontmatter(f.read())
        return meta, body

    elif ext in (".html", ".htm"):
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        meta = {"source_format": "html"}
        for m in soup.find_all("meta"):
            if m.get("name") and m.get("content"):
                meta[m["name"].strip()] = m["content"].strip()
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        for h in soup.find_all(["h1", "h2", "h3"]):
            h.string = f"\n## {h.get_text(strip=True)}\n"
        return meta, soup.get_text(separator="\n", strip=True)

    elif ext == ".docx":
        doc = DocxDocument(file_path)
        lines = []
        for p in doc.paragraphs:
            if p.style.name.startswith("Heading"):
                lines.append(f"## {p.text.strip()}")
            elif p.text.strip():
                lines.append(p.text.strip())
        return {"source_format": "docx"}, "\n".join(lines)

    elif ext == ".pdf":
        reader = PdfReader(file_path)
        pages = []
        for idx, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            if txt.strip():
                pages.append(f"## Page {idx}\n{txt.strip()}")
        return {"source_format": "pdf"}, "\n\n".join(pages)

    raise ValueError(f"Unsupported file format for {filename}: {ext}")


def chunk_narrative_by_section(text: str, max_tokens: int = 500, overlap_tokens: int = 75):
    """Splits normalized text along ## headings with sliding token overlap for oversized sections."""
    sections = re.split(r"(?=^##\s+)", text.strip(), flags=re.MULTILINE)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        lines = sec.splitlines()
        first_line = lines[0] if lines else "General"
        section_title = first_line.replace("#", "").strip() if first_line.startswith("#") else "General"
        tokens = tokenizer.encode(sec)

        if len(tokens) <= max_tokens:
            chunks.append({"section_title": section_title, "text": sec, "token_count": len(tokens)})
        else:
            start, part = 0, 1
            while start < len(tokens):
                end = min(start + max_tokens, len(tokens))
                chunks.append({
                    "section_title": f"{section_title} (Part {part})",
                    "text": tokenizer.decode(tokens[start:end]),
                    "token_count": end - start,
                })
                if end == len(tokens):
                    break
                start += (max_tokens - overlap_tokens)
                part += 1
    return chunks


def get_embedding(text: str):
    resp = client.embeddings.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding


def ingest_from_disk():
    conn = psycopg2.connect(
        host="localhost",
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("APP_DB", "brd_system_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE kb_chunks;")
    total_chunks = 0

    # 1. Process all narrative document formats (.md, .html, .docx, .pdf)
    narrative_files = []
    for pattern in ("*.md", "*.html", "*.htm", "*.docx", "*.pdf"):
        narrative_files.extend(glob.glob(os.path.join(KB_DIR, pattern)))

    for file_path in sorted(narrative_files):
        filename = os.path.basename(file_path)
        base_name, _ = os.path.splitext(filename)
        meta, body = extract_document_content(file_path)
        source_id = meta.pop("source_id", base_name)
        source_type = meta.pop("source_type", "org_standard")
        chunks = chunk_narrative_by_section(body, max_tokens=500, overlap_tokens=75)

        for idx, ch in enumerate(chunks):
            chunk_meta = {
                **meta,
                "file_name": filename,
                "section_title": ch["section_title"],
                "chunk_index": idx,
                "token_count": ch["token_count"],
                "chunking_strategy": "section_aware_500t_75overlap",
                "content_hash": hashlib.sha256(ch["text"].encode()).hexdigest(),
            }
            emb = get_embedding(ch["text"])
            cur.execute(
                """
                INSERT INTO kb_chunks (source_id, source_type, metadata, content, embedding)
                VALUES (%s, %s, %s::jsonb, %s, %s::vector)
                """,
                (source_id, source_type, json.dumps(chunk_meta), ch["text"], str(emb)),
            )
            total_chunks += 1
            print(f"[DOC ] {filename} -> {ch['section_title']} ({ch['token_count']} tokens)")

    # 2. Process all structured JSON records (.json)
    for json_path in sorted(glob.glob(os.path.join(KB_DIR, "*.json"))):
        filename = os.path.basename(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for rec in records:
            text = rec["content"].strip()
            token_count = len(tokenizer.encode(text))
            chunk_meta = {
                **rec.get("metadata", {}),
                "file_name": filename,
                "section_title": rec.get("title", rec["source_id"]),
                "token_count": token_count,
                "chunking_strategy": "atomic_record",
                "content_hash": hashlib.sha256(text.encode()).hexdigest(),
            }
            emb = get_embedding(text)
            cur.execute(
                """
                INSERT INTO kb_chunks (source_id, source_type, metadata, content, embedding)
                VALUES (%s, %s, %s::jsonb, %s, %s::vector)
                """,
                (rec["source_id"], rec["source_type"], json.dumps(chunk_meta), text, str(emb)),
            )
            total_chunks += 1
            print(f"[JSON] {filename} -> {rec['source_id']} ({token_count} tokens)")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nSuccess! Ingested {total_chunks} chunks from {KB_DIR} into brd_system_db.kb_chunks.")


if __name__ == "__main__":
    ingest_from_disk()
