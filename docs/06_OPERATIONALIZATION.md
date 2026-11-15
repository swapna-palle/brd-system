# 6. Operationalization, Monitoring & Production Readiness

## 6.1 Measurable Production Success Criteria
1. **First-Pass & Self-Healed Quality Rate:** `>= 90%` of authorized BRD runs achieve a **`GREEN` (`>= 8.0`)** quality badge by `v1` with zero `CRITICAL` defects.
2. **Citation Grounding Accuracy:** `100%` of cited `CHUNK_ID` UUIDs verified against `kb_chunks` (`0%` unverified citations released).
3. **End-to-End Latency & Policy Enforcement Efficiency:** `< 90 seconds` p95 latency for full 7-agent orchestration (including revision pass) and `< 0.5 seconds` deterministic rejection (`HTTP 403` / `HTTP 500`) for unauthorized roles or invalid inputs.

## 6.2 Production Failure Modes & Mitigations

| Failure Mode | Detection Mechanism | Automated / Operational Mitigation |
| :--- | :--- | :--- |
| **1. Langflow Spoke Timeout / Transient 5xx** | n8n HTTP Request timeout (`90s–180s`) & status check | Retry with exponential backoff; fallback to cached ADR baseline and flag `AMBER` for HITL review. |
| **2. Persistent `AMBER`/`RED` After `v1` Revision** | Critic Judge `overall_score < 8.0` on `v1` | Hard loop cap (`max 2 cycles: v0 -> v1`) prevents infinite token burn; halts auto-release and escalates findings to Engineering Manager in HITL console. |
| **3. Knowledge Base Drift / Outdated ADRs** | Periodic `kb_documents.updated_at` audit & Critic Groundedness score drops | Re-run `python kb_seed\03_ingest_kb.py` upsert pipeline when files in `kb_docs/` change; `is_stale` flag marks old artifacts. |

## 6.3 Pre-Release Gates & Audit Monitoring
- **Pre-Release Gates:** (1) Role Policy Enforcement Point (`IF Authorized?`) -> (2) Input Guardrail pass -> (3) `Critic_and_Judge` `GREEN` badge -> (4) Human Engineering Manager sign-off (`APPROVED_BY_EM`) -> (5) Jira Epic sync (`IF Can Sync Jira?`).
- **PostgreSQL Observability:** Every execution writes structured telemetry to `runs` (`status`, `package_badge`, `revision_round`), `evaluations` (4 rubric sub-scores + `critic_findings`), `artifacts` (versioned JSON + `payload_hash`), and `audit_events` (`input_hash`, `output_hash`, `latency_ms`, caller role & human sign-off decisions).
