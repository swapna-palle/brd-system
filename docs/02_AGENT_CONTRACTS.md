# 2. Agent Output Contracts & Handoff Validation Matrix

All inter-agent handoffs enforce strict JSON schemas (`response_format: json_object`) validated inside the **Agent 1 Hub Control Plane** before downstream consumption. Every spoke invocation also carries the caller's `caller_role` context (`Engineering_Manager` or `Product_Owner`) verified at the Policy Enforcement Point (`Node 2: Input Guardrail` + `IF Authorized?`).

## 2.1 Producer-to-Consumer Contract Matrix (All 7 Agents)

| Agent | Producer | Downstream Consumers | Key JSON Contract Fields | Deterministic Validation Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Agent 1: Hub Orchestrator & BRD Parser** | n8n Main Workflow (`Node 3` Parser + `Node 8a` Final Package Preparation) | Agents 2, 3, 4, 5, 6, Agent 7 & Streamlit UI | `requirements[]` (`req_id`, `type`, `description`, `ambiguity_flag`, `clarification_questions`), `constraints[]`, `markdown_report` | Must output a non-empty `requirements` array; flags unstated NFR metrics via `ambiguity_flag: true` and prepares final `.md` + JSON package. |
| **Agent 2: Engineering Plan Generator** | Langflow Spoke 1 (`PgVector KB Retriever` + `gpt-4.1-mini`) | Agent 3, Agent 4, Agent 7, Agent 1 (Final Package Preparation) | `phases[]` (`phase_id`, `name`, `duration_weeks`, `deliverables`), `team_composition[]`, `risks[]`, `self_reflection_notes`, `all_covered_requirements[]`, `citations[]` | Must map all parsed `req_id`s in `all_covered_requirements` and cite valid `CHUNK_ID` UUIDs from `kb_chunks`. |
| **Agent 3: Schedule & Effort Estimator** | n8n Deterministic Code (`Node 5` inside Agent 1) | Agent 7, Agent 1 (Final Package Preparation) | `base_duration_weeks`, `integration_buffer_weeks` (`+20%`), `total_estimated_weeks`, `milestones[]`, `buffer_rationale` | Deterministically computes `Math.max(1, Math.ceil(baseWeeks * 0.20))` buffer per `TIME-HIST-001` without LLM arithmetic. |
| **Agent 4: Solution Architect** | Langflow Spoke 2 (`PgVector KB Retriever` + `gpt-4.1-mini`) | Agent 5, Agent 6, Agent 7, Agent 1 (Final Package Preparation) | `architecture_style`, `components[]`, `api_contracts[]`, `resilience_controls[]`, `all_covered_requirements[]`, `citations[]` | Must align with Clean Architecture & security standards (`STD-ENG-001`, `SEC-ENTRA-001`) and map all `req_id`s. |
| **Agent 6: Tech Stack & Trade-Off Recommender** | Langflow Spoke 3 (`PgVector KB Retriever` + `gpt-4.1-mini`) | Agent 5, Agent 7, Agent 1 (Final Package Preparation) | `recommended_stack{}`, `deployment_options[]` (2–3 multi-stack options with `pros`, `cons`, `cost_tier`), `citations[]` | Must contrast at least 2 multi-stack/deployment options grounded in organizational ADRs (`ADR-001`). |
| **Agent 5: PoC Risk & Exit Planner** | Langflow Spoke 4 (`PgVector KB Retriever` + `gpt-4.1-mini`) | Agent 7, Agent 1 (Final Package Preparation) | `poc_duration_weeks`, `hypotheses[]`, `exit_criteria[]` (quantitative pass/fail metrics), `fallback_plan`, `citations[]` | Every high-risk integration must include measurable Go/No-Go exit criteria and a concrete fallback plan. |
| **Agent 7: Critic & Quality Judge** | n8n Sub-Workflow (`Critic_and_Judge`) | Agent 1 Loop Router (`v0 -> v1`), PostgreSQL, HITL UI | `groundedness_score`, `completeness_score`, `consistency_score`, `actionability_score`, `overall_score`, `badge`, `revision_needed`, `critic_findings[]` | Combines LLM rubric scoring with deterministic SQL UUID verification (`kb_chunks`) and requirement coverage checks; assigns `GREEN` (`>= 8.0`), `AMBER` (`6.0–7.99` or `CRITICAL`), or `RED` (`< 6.0`). |

## 2.2 Targeted Revision Handoff (`v0 -> v1`)
When `Agent 7` sets `revision_needed: true` (`AMBER` or `RED` badge), **Agent 1 (`Node 7a: Targeted Revision Pass v1`)** re-invokes only the defective spoke(s) (`Agent 2` and/or `Agent 4`), passing:
- The initial draft artifact (`v0`)
- The specific `critic_findings[]` (`severity`, `target_agent`, `issue`, `repair_instruction`)
- The preserved `caller_role` context

The revised `v1` package is re-evaluated by `Agent 7` (`Node 7b`) before final package preparation by **Agent 1 (`Node 8a`)** and persistence to PostgreSQL.
