# 📐 BRD-to-Engineering Delivery Studio (Multi-Agent System)

A **stack-agnostic Multi-Agent Hub-and-Spoke System** that converts Business Requirement Documents (BRDs) into grounded, audit-ready **Engineering Delivery Packages**—complete with phased delivery plans, effort estimates (`+20%` integration buffer), Clean Architecture designs, multi-stack technology trade-offs, PoC exit criteria, bounded self-healing (`v0 -> v1`), role-based agent authorization, and Human-in-the-Loop (HITL) sign-off.

> **Pluggable Organizational Standards:** All architectural baselines, security policies, and ADRs live as multi-format source documents (`.md`, `.json`, `.html`) inside **`kb_docs/`** and are indexed into **PostgreSQL `pgvector`**. The included seed corpus uses enterprise **.NET & Azure** standards as a reference baseline, and Engineering Managers across Java, Python, Node.js, or .NET teams can swap or extend `kb_docs/` without modifying agent code.

---

## 🏗️ Architecture & Tech Stack
- **Control Plane / Orchestrator:** **n8n** (`Agent1_Main_Orchestrator` + `Critic_and_Judge` sub-workflow)
- **Cognitive RAG Spokes:** **Langflow** (4 specialized agents with custom `PgVector KB Retriever` tools)
- **LLM & Embeddings:** OpenAI `gpt-4.1-mini` (`temperature=0.1`, JSON Object mode) & `text-embedding-3-small` (`1536d`)
- **Database & Vector Store:** **PostgreSQL 16+ with `pgvector` (`v0.7.0+`)** (`runs`, `artifacts`, `evaluations`, `audit_events`, `kb_documents`, `kb_chunks`)
- **Engineering Manager Studio UI:** **Streamlit** (`ui/app.py`) with Role-Based Session Context, `v0 -> v1` Self-Healing Diff Card, and HITL Sign-Off Console

---

## 📁 Repository Structure
```text
brd-system/
├── db/                         # PostgreSQL schema & pgvector setup scripts
├── kb_docs/                    # Multi-format RAG knowledge base (.md, .json, .html standards, ADRs & timelines)
├── kb_seed/
│   ├── procedures/             # PostgreSQL stored procedures (fn_create_run, fn_save_evaluation, fn_finalize_run)
│   └── 03_ingest_kb.py         # Multi-format parser & pgvector embedding ingestion script (reads kb_docs/)
├── langflow_flows/             # Exported Langflow JSON definitions (Agents 2, 4, 5, 6)
├── n8n_workflows/              # Scrubbed n8n workflow JSONs (Agent1_Main_Orchestrator & Critic_and_Judge)
├── ui/
│   └── app.py                  # Streamlit Studio (Role Sign-In Gate, v0->v1 Diff & HITL Sign-Off)
├── tests/
│   └── run_e2e_eval.py         # 7-scenario automated evaluation & edge-case benchmark suite
├── docs/                       # Complete 8-section Capstone Architecture & Evaluation Docs
├── sample_engineering_package.md
├── requirements.txt
└── .env.example
```

---

## 🚀 Installation & Setup Guide

### Prerequisites
- **Python 3.9+**
- **PostgreSQL 16+** installed locally (or via Docker) with the **`pgvector` (`v0.7.0+` / `v0.8.0+`)** extension installed and enabled (`CREATE EXTENSION IF NOT EXISTS vector;`)
- **Docker Desktop** (for running **n8n** on port `5678` and **Langflow** on port `7860`)
- **OpenAI API Key** (`gpt-4.1-mini` & `text-embedding-3-small`)

### Step 1: Clone Repository & Install Python Dependencies
```cmd
git clone <your-github-repo-url>
cd brd-system
python -m pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
```cmd
copy .env.example .env
```
Edit `.env` and set your credentials:
- `OPENAI_API_KEY` — Your OpenAI API key
- `POSTGRES_HOST` — `host.docker.internal` (for Dockerized n8n/Langflow; `ui/app.py` automatically resolves this to `localhost` on Windows)
- `POSTGRES_PORT` — `5432`
- `APP_DB` — `brd_system_db`
- `POSTGRES_USER` / `POSTGRES_PASSWORD` — Your PostgreSQL credentials

### Step 3: Initialize PostgreSQL Schema, Procedures & Knowledge Base
> **Database Prerequisite:** Ensure **PostgreSQL 16+** is installed and running on port `5432` with the **`pgvector` (`v0.7.0+` or `v0.8.0+`)** extension installed (supports `vector(1536)` and cosine distance operator `<=>`), and create three empty databases: `brd_system_db`, `n8n_db`, and `langflow_db`.

1. Connect to `brd_system_db` (via `psql` or pgAdmin 4) and enable `pgvector`:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. Execute the DDL scripts in `db/` against `brd_system_db` to create the tables (`runs`, `artifacts`, `evaluations`, `audit_events`, `kb_documents`, `kb_chunks`).
3. Execute the stored procedures inside `kb_seed\procedures\` against `brd_system_db`.
4. Run the knowledge base ingestion script to parse all `.md`, `.json`, and `.html` files in `kb_docs/` and load their embeddings into `pgvector`:
   ```cmd
   python kb_seed\03_ingest_kb.py
   ```

### Step 4: Start n8n & Langflow Containers (Docker)
Create a shared Docker network (`brd-net`) so n8n can communicate directly with Langflow (`http://brd-system-langflow:7860`) and host PostgreSQL (`host.docker.internal:5432`):

```cmd
docker network create brd-net

docker run -d --name brd-system-langflow --network brd-net ^
  -p 7860:7860 ^
  -e LANGFLOW_DATABASE_URL="postgresql://postgres:<password>@host.docker.internal:5432/langflow_db" ^
  --add-host=host.docker.internal:host-gateway ^
  langflowai/langflow:latest

docker run -d --name brd-system-n8n --network brd-net ^
  -p 5678:5678 ^
  -e DB_TYPE=postgresdb ^
  -e DB_POSTGRESDB_HOST=host.docker.internal ^
  -e DB_POSTGRESDB_PORT=5432 ^
  -e DB_POSTGRESDB_DATABASE=n8n_db ^
  -e DB_POSTGRESDB_USER=postgres ^
  -e DB_POSTGRESDB_PASSWORD=<password> ^
  --add-host=host.docker.internal:host-gateway ^
  n8nio/n8n:latest
```
Verify both services are healthy at `http://localhost:7860` (Langflow) and `http://localhost:5678` (n8n) before importing the JSON workflows.

### Step 5: Import & Activate Langflow and n8n Workflows
1. **Langflow (`http://localhost:7860`):**
   - Import all 4 JSON files from `langflow_flows/`.
   - Add your `OPENAI_API_KEY` and PostgreSQL connection string (`postgresql://postgres:<password>@host.docker.internal:5432/brd_system_db`) in each flow, and copy each Flow ID + your Langflow API key.
2. **n8n (`http://localhost:5678`):**
   - Import `n8n_workflows/Critic_and_Judge.json` and `n8n_workflows/Agent1_Main_Orchestrator.json`.
   - Attach your OpenAI and PostgreSQL (`brd_system_db`) credentials in n8n.
   - Update `FLOW_IDS` and `LANGFLOW_KEY` inside `Run Cognitive Spokes v0` and `Targeted Revision Pass v1`.
   - Click **Publish** on both workflows.

---

## 💻 How to Use the Application

### Option A: Interactive Streamlit Studio (Recommended)
1. Start the Streamlit web application:
   ```cmd
   python -m streamlit run ui\app.py
   ```
2. Open **`http://localhost:8501`** in your browser.
3. **Sign In with Organizational Role Context:**
   - **`Engineering_Manager`:** Full access to run all 7 agents, sync Jira backlog items, and sign off (`Approve` / `Reject`) in the Human-in-the-Loop (HITL) console.
   - **`Product_Owner`:** Can generate and download `.md` engineering packages, but external Jira writes and HITL release approvals are restricted.
   - **`Others`:** Deterministically blocked at n8n's Policy Enforcement Point (`HTTP 403 AGENT_AUTHORIZATION_DENIED`) before any LLM tokens are spent.
4. Select a **Quick BRD Preset** from the left sidebar (or upload a `.txt` / `.md` BRD file / paste custom requirements), optionally toggle **Inject Fault** to observe the `v0 -> v1` self-healing loop, and click **Generate Engineering Delivery Package**.
5. Download the **Full Markdown Package (`.md`)** and record your **HITL Sign-Off** decision into PostgreSQL `audit_events`.

### Option B: Automated 7-Scenario Benchmark & Edge-Case Evaluation
Run the end-to-end evaluation suite (covering low/medium complexity BRDs, `v0 -> v1` fault injection, ambiguous NFRs, conflicting constraints, malformed input guardrails, and unauthorized role policy denials):
```cmd
python tests\run_e2e_eval.py
```

---

## 📚 Capstone Documentation Index
- [01 — System Architecture & Design Decisions](docs/01_ARCHITECTURE_AND_DECISIONS.md)
- [02 — Agent Output Contracts & Handoff Validation](docs/02_AGENT_CONTRACTS.md)
- [03 — Knowledge Base & RAG Retrieval Design](docs/03_RAG_DESIGN.md)
- [04 — Evaluation Framework, Edge Cases & Benchmark Report](docs/04_EVALUATION_REPORT.md)
- [05 — Guardrails, Agent RBAC & Safety Controls](docs/05_GUARDRAILS_AND_SAFETY.md)
- [06 — Operationalization, Monitoring & Production Readiness](docs/06_OPERATIONALIZATION.md)
