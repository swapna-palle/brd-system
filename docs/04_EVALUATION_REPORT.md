# 4. BrdSystem Evaluation & Benchmark Report

## 4.1 Multi-Method Evaluation Strategy
The system evaluates every generated engineering package using **three complementary evaluation layers**:
1. **Deterministic Rule-Based Verification (`Agent 7: Critic_and_Judge` + `Node 2` PEP):**
   - Enforces caller role authorization (`Engineering_Manager`, `Product_Owner`, `Others`) at entry before any LLM execution.
   - Verifies 100% requirement coverage (`all_covered_requirements` across `engineering_plan` and `solution_architect`).
   - Validates every cited `CHUNK_ID` UUID directly against PostgreSQL `kb_chunks` (`SELECT chunk_id FROM kb_chunks`), applying a `-2.0` Groundedness penalty and `CRITICAL` defect on any unverified citation.
   - Detects unstated NFR metrics (`ambiguity_flag: true`) and conflicting timeline/budget constraints, escalating runs to `AMBER` for human review.
2. **LLM-as-Judge Rubric (`gpt-4.1-mini`):**
   - Scores every package across four weighted dimensions: **Groundedness (30%)**, **Completeness (30%)**, **Consistency (25%)**, and **Actionability (15%)**.
   - Assigns an automated release gate badge: **`GREEN`** (`overall_score >= 8.0` and zero `CRITICAL` findings), **`AMBER`** (`6.0–7.99` or any `CRITICAL` finding), or **`RED`** (`< 6.0`).
3. **Human-in-the-Loop (HITL) Engineering Manager Sign-Off (`ui/app.py`):**
   - Engineering Managers inspect `AMBER`/`RED` escalations, Critic findings, and agent outputs in the Streamlit Delivery Studio and record `APPROVED_BY_EM` or `REJECTED_BY_EM` decisions into PostgreSQL `audit_events`.

## 4.2 End-to-End Benchmark & Edge-Case Results (`tests/run_e2e_eval.py` & Live UI Runs)

| Test Scenario | Role Context | Run ID / Gate | Latency | v0 Score & Badge | Final Score & Badge | Revisions | Outcome |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Test 1:** Internal Operations Approval Hub (Low) | `Engineering_Manager` | `099e8cf4-47e2-41c0-82dc-80ccdf072cdc` | 53.73s | 8.67 (`GREEN`) | 8.67 (`GREEN`) | 0 (`v0`) | Passed on first pass + Jira sync enabled |
| **Test 2:** FinTech Vendor Onboarding Portal (Medium) | `Product_Owner` | `142f0b07-b503-41c5-b25b-b263be94d65a` | 55.50s | 9.28 (`GREEN`) | 9.28 (`GREEN`) | 0 (`v0`) | Passed + `.md` exported; Jira write skipped |
| **Test 3:** Fault-Injection Self-Healing Test (`v0 -> v1`) | `Engineering_Manager` | Live UI Verified Run | ~78.0s | 6.95 (`AMBER`) | **8.00 (`GREEN`)** | **1 (`v0 -> v1`)** | Self-healed `+1.05` & HITL approved |
| **Edge Case 1:** Ambiguous BRD (Missing NFRs & Metrics) | `Engineering_Manager` | `fee31788-ab83-430c-929d-df92cbb010f5` | 46.10s | 8.32 (`GREEN`) | 8.32 (`GREEN`) | 0 (`v0`) | Flagged NFR clarification questions |
| **Edge Case 2:** Conflicting Constraints (1-Week Limit) | `Engineering_Manager` | `afe499c1-ba08-45c4-b01a-decb9ded1331` | 52.53s | 7.32 (`AMBER`) | 7.32 (`AMBER`) | 1 (`v0 -> v1`) | Escalated `AMBER` to HITL sign-off gate |
| **Edge Case 3:** Malformed / Short Input (`< 50 chars`) | `Engineering_Manager` | Blocked at `Node 2` | **0.20s** | N/A | `REJECTED` | 0 | Blocked before LLM ($0 token cost) |
| **Edge Case 4:** Unauthorized Caller Role (`Others`) | `Others` | Blocked at `IF Authorized?` | **0.18s** | N/A | `403 DENIED` | 0 | Deterministic Policy Denial ($0 token cost) |

## 4.3 Iterative Cycle Improvement Comparison (`v0` vs. `v1` Self-Healing Loop)

| Metric / Dimension | Initial Draft (`v0` Fault-Injected) | Revised Package (`v1` Self-Healed) | Delta (`v0 -> v1`) | Root Cause & Resolution |
| :--- | :---: | :---: | :---: | :--- |
| **Completeness Score (30%)** | `4.50 / 10` | **`8.00 / 10`** | **`+3.50`** | Critic caught missing BRD requirement mappings (`CRITICAL`) and re-ran targeted spokes (`Agent 2` & `Agent 4`). |
| **Overall Weighted Score** | `6.95 / 10` | **`8.00 / 10`** | **`+1.05`** | Automated targeted repair lifted package across the `8.0` quality gate threshold. |
| **Quality Gate Badge** | `AMBER` (Hold) | **`GREEN` (Ready)** | **Upgraded** | Eligible for Engineering Manager release sign-off in Streamlit HITL console. |
