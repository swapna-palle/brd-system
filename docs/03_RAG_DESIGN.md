# 3. Knowledge Base & RAG Retrieval Design

## 3.1 Multi-Format Knowledge Base Corpus (`kb_docs/` + `kb_seed/03_ingest_kb.py`)
The enterprise knowledge base consists of **9 multi-format documents** stored in **`kb_docs/`** (Markdown `.md`, structured `.json`, and Confluence `.html`) and ingested via **`kb_seed/03_ingest_kb.py`** into PostgreSQL (`kb_documents` and `kb_chunks`). While the initial reference corpus uses Microsoft/.NET & Azure standards as an organizational baseline, the ingestion pipeline and vector schema are completely tech-stack agnostic—engineering teams can add or swap `.md`, `.json`, or `.html` standards for Java, Python, Node.js, or cloud-agnostic ADRs in `kb_docs/` without modifying agent prompts or orchestration logic:

| File in `kb_docs/` | Format | Source Type | Purpose in Multi-Agent Retrieval |
| :--- | :---: | :--- | :--- |
| `STD-ENG-001_org_standards.md` | Markdown | `org_standard` | Enterprise Clean Architecture, resilience policies (retries/circuit breakers), idempotency keys, and OpenTelemetry logging. |
| `CONF-CODE-001_dotnet_coding_patterns.md` | Markdown | `org_standard` | Organizational coding conventions, dependency injection, and API error-handling standards. |
| `GH-REF-001_dotnet_clean_arch_blueprint.md` | Markdown | `arch_pattern` | Reference Clean Architecture layer structure and repository blueprint. |
| `ARCH-PATTERNS.json` | JSON | `arch_pattern` | Structured architectural patterns (transactional outbox, event-driven messaging, gateway patterns). |
| `ADR-DECISIONS.json` | JSON | `tech_decision` | Architecture Decision Records (PostgreSQL + `pgvector`, message brokers, caching, and deployment trade-offs). |
| `CONF-SHAREPOINT-001.html` | HTML | `org_standard` | Exported Confluence/SharePoint engineering governance and security compliance guidelines. |
| `TPL-PLAN-001_plan_template.md` | Markdown | `plan_template` | Standard 4-phase enterprise delivery template (Discovery/PoC, Core Domain, Integration/Hardening, UAT/Cutover). |
| `TIMELINE-HISTORY.json` | JSON | `timeline_history` | Historical delivery velocity benchmarks and mandatory `+20%` buffer rules for external integrations. |
| `BRD-PAST-001_merchant_payouts.md` | Markdown | `past_brd` | Historical FinTech merchant payout BRD and approved engineering baseline. |

## 3.2 Multi-Format Parsing, Chunking & Vector Retrieval
- **Format-Aware Parsing (`kb_seed/03_ingest_kb.py`):** Automatically reads all `.md`, `.json`, and `.html` files from `kb_docs/`, strips HTML markup cleanly, serializes structured JSON records, and splits content along section boundaries (`~450` tokens per chunk with `60`-token overlap).
- **Metadata Schema (`kb_documents` & `kb_chunks`):** Each chunk stores `chunk_id` (UUID primary key), `doc_code`, `source_type`, `domain`, `version`, and `embedding vector(1536)` generated via OpenAI `text-embedding-3-small`.
- **Role-Specialized Retrieval (`PgVector KB Retriever` in Langflow):** Each cognitive spoke queries only the `source_type` categories relevant to its engineering responsibility using metadata filtering + cosine distance (`embedding <=> query_vector`, `LIMIT 4`):
  - **Agent 2 (Engineering Plan):** `["org_standard", "plan_template", "past_brd"]`
  - **Agent 4 (Solution Architect):** `["org_standard", "arch_pattern", "past_brd"]`
  - **Agent 6 (Tech Stack & Trade-Offs):** `["org_standard", "tech_decision", "arch_pattern"]`
  - **Agent 5 (PoC Risk & Exit Planner):** `["org_standard", "past_brd", "timeline_history"]`
- **Deterministic Citation Grounding:** Every retrieved chunk is injected into the spoke prompt with an explicit `[CHUNK_ID: <uuid>]` header. During evaluation, **Agent 7 (`Critic_and_Judge`)** extracts all UUIDs from agent outputs and verifies them directly against `SELECT chunk_id FROM kb_chunks`, penalizing any unverified UUID (`-2.0` Groundedness + `CRITICAL` defect).
