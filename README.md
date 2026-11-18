# Multi-Agent BRD-to-Engineering Delivery System

An enterprise-grade **Hub-and-Spoke Multi-Agent AI System** that transforms raw Business Requirement Documents (BRDs) into grounded, evaluated, and Engineering Manager-approved technical delivery packages. Built with **n8n** (Control Plane & Deterministic Orchestrator), **Langflow** (Cognitive RAG Spokes), **PostgreSQL + pgvector** (Unified State, Audit & Vector Store), and **Streamlit** (Engineering Manager Delivery Studio).

> **Pluggable Organizational Standards:** All architectural baselines, security policies, and ADRs live as multi-format source documents (`.md`, `.json`, `.html`) inside `kb_docs/` and are indexed into PostgreSQL `pgvector`. The included seed corpus uses enterprise `.NET` & Azure standards as a reference baseline, and Engineering Managers across Java, Python, Node.js, or `.NET` teams can swap or extend `kb_docs/` without modifying agent code.

---

## 🏗️ Architecture & Tech Stack

- **Control Plane / Orchestrator:** n8n (`Agent1_Main_Orchestrator` + `Critic_and_Judge` sub-workflow) enforcing Role-Based Authorization (`Engineering_Manager`, `Product_Owner`), input guardrails, and bounded `v0 -> v1` revision loops.
- **Cognitive RAG Spokes:** Langflow (4 specialized agents with custom `PgVector KB Retriever` tools covering Engineering Planning, Solution Architecture, Tech Stack Trade-Offs, and PoC Planning) + deterministic Effort & Schedule Estimator (`+20%` integration contingency buffer).
- **LLM & Embeddings:** OpenAI `gpt-4.1-mini` (`temperature=0.1`, JSON Object mode) & `text-embedding-3-small` (`1536d`).
- **Database & Vector Store:** PostgreSQL 16+ with `pgvector` (`v0.7.0+`) (`runs`, `artifacts`, `evaluations`, `audit_events`, `kb_documents`, `kb_chunks`).
- **Engineering Manager Studio UI:** Streamlit (`ui/app.py`) with Role-Based Session Context, formatted executive tables, `v0 -> v1` Self-Healing Diff Card, and Human-in-the-Loop (HITL) Sign-Off Console.

---

## 📥 RAG Knowledge Base Ingestion Pipeline

Before running BRD workflows, organizational reference documents in `kb_docs/` are ingested into PostgreSQL (`pgvector`) via an offline, idempotent ETL pipeline (`kb_seed/03_ingest_kb.py`):

1. **Multi-Format Document Loader:** Scans `kb_docs/` (12 source documents across `.md`, `.json`, and `.html` covering past BRDs, engineering plan templates, 7 architecture patterns, 8 project timeline benchmarks, org engineering standards, and 12 ADRs), strips HTML/boilerplate tags, and extracts structured metadata (`doc_type`, `domain`, `tech_stack`, `version`).
2. **Recursive Semantic Chunking:** Splits each document into `800`-character overlapping chunks (`120`-character overlap) preserving section headings and requirement boundaries.
3. **Dense Vector Embedding:** Generates `1536`-dimensional embeddings for each chunk using OpenAI `text-embedding-3-small`.
4. **Idempotent `pgvector` Upsert & Indexing:** Upserts document headers into `kb_documents` and chunk vectors + `CHUNK_ID` UUIDs into `kb_chunks` with an HNSW cosine-similarity index (`vector_cosine_ops`).

### Run & Verify RAG Ingestion
```bash
# 1. Ingest all documents from kb_docs/ into PostgreSQL pgvector
python kb_seed/03_ingest_kb.py

# 2. Verify ingested document and chunk counts in PostgreSQL
psql -U postgres -d brd_system_db -c "SELECT d.doc_type, COUNT(c.chunk_id) AS chunks FROM kb_documents d JOIN kb_chunks c ON d.doc_id = c.doc_id GROUP BY d.doc_type;"
```

---

## 📁 Repository Structure

```text
brd-system/
├── docker-compose.yml                  # Local n8n + Langflow orchestration containers
├── .env.example                        # Environment variable template (no real secrets)
├── README.md                           # Project overview & setup guide
├── sample_engineering_package.md       # Golden reference output package (EVAL-002)
├── database/
│   └── procedures/                     # PostgreSQL + pgvector schema & stored procedures
├── docs/
│   ├── 01_ARCHITECTURE_AND_DECISIONS.md # Hub-and-Spoke architecture, Mermaid diagram & stack rationale
│   ├── 02_AGENT_CONTRACTS.md            # Input/output JSON schemas & producer-consumer contracts
│   ├── 03_RAG_DESIGN.md                 # Offline ingestion, chunking, embeddings, retrieval & citations
│   ├── 04_EVALUATION_REPORT.md          # 7-scenario benchmark dataset, methods & v0->v1 metrics
│   ├── 05_GUARDRAILS_AND_GOVERNANCE.md  # Security guardrails, SQL UUID verification & RBAC policy
│   └── 06_OPERATIONALIZATION.md         # KPIs, failure recovery, release gates & observability
├── eval_dataset/
│   └── benchmark_brds.json             # Evaluation dataset (Simple, Medium, Complex & Edge Cases)
├── kb_docs/                            # Multi-format RAG Knowledge Base (12 source documents)
├── kb_seed/
│   └── 03_ingest_kb.py                 # Offline RAG ingestion, chunking & embedding script
├── langflow_flows/                     # Exported Langflow JSON definitions for Cognitive Spokes
├── n8n_workflows/
│   ├── Agent1_Main_Orchestrator.json   # Master Control Plane workflow (scrubbed)
│   └── Critic_and_Judge.json           # Critic & Hybrid LLM-as-Judge sub-workflow
├── tests/
│   └── run_e2e_eval.py                 # Automated 7-scenario end-to-end evaluation runner
└── ui/
    └── app.py                          # Streamlit Engineering Manager Delivery Studio
```

---

## 🚀 Quickstart Setup & Execution

### 1. Prerequisites
- **Docker Desktop** (for n8n & Langflow)
- **PostgreSQL 16+** with the **`pgvector`** extension installed
- **Python 3.10+** with `pip`
- **OpenAI API Key**

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```
Required keys in `.env`:
- `OPENAI_API_KEY`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` (`brd_system_db`), `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `N8N_WEBHOOK_URL` (`http://localhost:5678/webhook/brd-to-engineering`)
- `LANGFLOW_API_URL` (`http://localhost:7860`) & `LANGFLOW_KEY`

### 3. Initialize PostgreSQL Schema & Ingest RAG Knowledge Base
```bash
# Install Python dependencies
pip install psycopg2-binary openai requests streamlit python-dotenv beautifulsoup4

# Create database & apply schema + stored procedures from database/procedures/
psql -U postgres -c "CREATE DATABASE brd_system_db;"
for f in database/procedures/*.sql; do psql -U postgres -d brd_system_db -f "\$f"; done

# Run offline RAG ingestion (chunks + embeds kb_docs/ into pgvector)
python kb_seed/03_ingest_kb.py
```

### 4. Start n8n & Langflow Services
```bash
docker compose up -d
```
- **Langflow (`http://localhost:7860`):** Import the JSON flows from `langflow_flows/` and configure your PostgreSQL & OpenAI credentials.
- **n8n (`http://localhost:5678`):** Import `n8n_workflows/Critic_and_Judge.json` and `n8n_workflows/Agent1_Main_Orchestrator.json`, link your Postgres & OpenAI credentials, and **Publish** both workflows.

### 5. Launch the Engineering Manager Delivery Studio (Streamlit)
```bash
python -m streamlit run ui/app.py
```
Open **`http://localhost:8501`** in your browser, sign in as **`Engineering_Manager`**, upload or select a BRD, inspect the grounded agent outputs, record HITL sign-off, and export the formatted `.md` package.

### 6. Run the Automated Evaluation Suite
```bash
python tests/run_e2e_eval.py
```
Executes all 7 scenarios from `eval_dataset/benchmark_brds.json` (Low, Medium, Fault-Injected `v0 -> v1` Self-Healing, Missing NFR Ambiguity, Contradictory Constraints, Short Input Guardrail, and `HTTP 403` Unauthorized Role check).
