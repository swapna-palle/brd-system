import json
import os
import requests
import psycopg2
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = "http://localhost:5678/webhook/brd-to-engineering"

st.set_page_config(page_title="BRD-to-Engineering AI Studio", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
button[kind="primary"],
div[data-testid="stForm"] button {
    background-color: #2563EB !important;
    color: white !important;
    border: none !important;
}
button[kind="primary"]:hover,
div[data-testid="stForm"] button:hover {
    background-color: #1D4ED8 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
    background-color: #16A34A !important;
    color: white !important;
    border: none !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
    background-color: #DC2626 !important;
    color: white !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# 1. Identity & Role Context Gate (Simulates Upstream Entra ID Claims)
if "session_user" not in st.session_state:
    st.title("🔐 BRD-to-Engineering Delivery Studio — Session Context")
    st.caption("Select your organizational identity & role claim to propagate into the Multi-Agent Orchestrator.")
    with st.form("role_login_form"):
        login_email = st.text_input("User Email", value="em_lead@corp.internal", placeholder="name@corp.internal")
        login_role = st.selectbox("Organizational Role", ["Engineering_Manager", "Product_Owner", "Others"])
        if st.form_submit_button("Continue to Delivery Studio →", type="primary"):
            if not login_email.strip() or "@" not in login_email:
                st.error("Please enter a valid corporate email address.")
            else:
                st.session_state["session_user"] = {
                    "email": login_email.strip(),
                    "role": login_role
                }
                st.rerun()
    st.stop()

current_user = st.session_state["session_user"]



def colored_badge(badge_text: str) -> str:
    colors = {"GREEN": "#16A34A", "AMBER": "#D97706", "RED": "#DC2626"}
    bg = colors.get(badge_text.upper(), "#4B5563")
    return f"<span style='background-color:{bg};color:white;padding:2px 10px;border-radius:6px;font-weight:700;font-size:0.85em;'>{badge_text}</span>"

st.title("📐 BRD-to-Engineering Delivery Studio")
st.caption("Multi-Agent Engineering Planning & Architecture System • n8n + Langflow + PostgreSQL pgvector")


# Sidebar: Sample Presets & Recent Runs from PostgreSQL
st.info(f"👤 **{current_user['email']}**\n\n🛡️ Role: `{current_user['role']}`")
if st.button("🔄 Switch User / Role"):
    del st.session_state["session_user"]
    st.session_state.pop("last_result", None)
    st.rerun()
st.divider()
with st.sidebar:
    st.header("📋 Quick BRD Presets")
    preset = st.selectbox(
        "Load a sample BRD:",
        [
            "Custom Input",
            "Simple: Internal Operations Approval Hub",
            "Medium: FinTech Vendor Onboarding Portal",
            "Fault-Injection Test: Treasury Payout Engine (v0 -> v1)",
            "Edge Case 1: Ambiguous BRD (Missing NFRs)",
            "Edge Case 2: Conflicting Constraints (Unrealistic 1-Week Timeline)"
        ]
    )

    st.divider()
    st.header("🗄️ Recent PostgreSQL Runs")
    try:
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        if db_host == "host.docker.internal":
            db_host = "localhost"      
        conn = psycopg2.connect(
            host=db_host,
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "brd_system_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "sa"),                  
        )
        
        cur = conn.cursor()
        cur.execute("""
            SELECT r.run_id::text, r.status, r.package_badge, r.revision_round, e.overall_score
            FROM runs r
            LEFT JOIN evaluations e ON r.run_id = e.run_id
            ORDER BY r.created_at DESC LIMIT 6;
        """)
        for r_id, status, badge, rev, score in cur.fetchall():
            icon = "🟢" if badge == "GREEN" else ("🟡" if badge == "AMBER" else "🔴")
            st.markdown(f"{icon} `{r_id[:8]}...` | **{badge}** ({score}/10) | `v{rev}` | `{status}`")
        cur.close()
        conn.close()
    except Exception as ex:
        st.caption(f"DB preview unavailable: {ex}")

PRESETS = {
    "Custom Input": ("", "", False),
    "Simple: Internal Operations Approval Hub": (
        "Internal Operations Approval Hub (.NET)",
        "Business Requirement Document: Internal Operations Approval Hub.\n"
        "REQ-001: Build an internal web application using .NET and PostgreSQL for managers to approve travel and equipment requests.\n"
        "REQ-002: Enforce Microsoft Entra ID single sign-on with role-based access control for Employees and Managers.\n"
        "REQ-003: Provide an immutable audit log of all approvals and rejections.\n"
        "NFR-001: Expected peak load is 150 concurrent internal users with p95 API latency under 300ms.",
        False
    ),
    "Medium: FinTech Vendor Onboarding Portal": (
        "Enterprise Vendor Onboarding & Settlement Portal",
        "Business Requirement Document: Enterprise Vendor Onboarding & Settlement Portal.\n"
        "REQ-001: Build a .NET Clean Architecture portal allowing enterprise vendors to register tax profiles and bank accounts.\n"
        "REQ-002: Integrate with a third-party external KYC verification REST API with resilience retries and circuit breakers.\n"
        "REQ-003: Publish VendorApproved domain events reliably to Azure Service Bus using a transactional outbox pattern.\n"
        "REQ-004: Enforce idempotency keys on all state-mutating payout and approval POST endpoints.\n"
        "NFR-001: System must support 1,200 requests per second, 99.95% availability, and Microsoft Entra ID authentication.",
        False
    ),
    "Fault-Injection Test: Treasury Payout Engine (v0 -> v1)": (
        "Multi-Currency Treasury Payout Engine (Fault-Injected)",
        "Business Requirement Document: Multi-Currency Treasury Payout Engine.\n"
        "REQ-001: Process automated cross-border vendor payouts in USD, EUR, and GBP using .NET and PostgreSQL.\n"
        "REQ-002: Enforce dual-control manager approval workflow via Microsoft Entra ID RBAC before releasing funds.\n"
        "REQ-003: Guarantee exactly-once idempotent ledger postings with full audit trail.",
        True
    ),
    "Edge Case 1: Ambiguous BRD (Missing NFRs)": (
        "Customer Notification Service (Ambiguous NFRs)",
        "Business Requirement Document: Customer Notification Service.\n"
        "REQ-001: Send email and SMS alerts when vendor invoices are approved.\n"
        "REQ-002: System must be fast, highly available, and secure for enterprise users.",
        False
    ),
    "Edge Case 2: Conflicting Constraints (Unrealistic 1-Week Timeline)": (
        "Global Real-Time Settlement Engine (Conflicting Constraints)",
        "Business Requirement Document: Global Real-Time Settlement Engine.\n"
        "REQ-001: Build a multi-region active-active cross-border banking settlement platform in .NET.\n"
        "NFR-001: Must support 50,000 TPS with 99.999% uptime and full PCI-DSS certification.\n"
        "CONSTRAINT-001: Total delivery timeline must be 1 week with 1 developer and zero infrastructure budget.",
        False
    )
}

default_title, default_brd, default_fault = PRESETS[preset]

col1, col2 = st.columns(2)
with col1:
    title = st.text_input("Project / BRD Title", value=default_title, placeholder="e.g., Enterprise Vendor Onboarding Portal")
with col2:
    submitted_by = st.text_input("Authenticated User Email", value=current_user["email"], disabled=True)

uploaded_file = st.file_uploader("Upload a BRD file from your computer (.txt or .md) — or skip and type/paste below", type=["txt", "md"])
if uploaded_file is not None:
    default_brd = uploaded_file.read().decode("utf-8")

brd_text = st.text_area("Business Requirement Document (BRD) Content", value=default_brd, height=180, placeholder="Enter FRs, NFRs, and constraints...")
simulate_fault = st.checkbox("Inject Fault (Drop requirement mappings on v0 to demonstrate Critic v0 → v1 self-healing loop)", value=default_fault)

if st.button("🚀 Generate Engineering Delivery Package", type="primary"):
    if len(brd_text.strip()) < 50:
        st.error("Guardrail Rejected: BRD text must be at least 50 characters.")
    else:
        with st.spinner("Orchestrating 7 Agents (RAG Retrieval → Plan → Schedule → Architecture → Stack → PoC → Critic Judge)..."):
            try:
                resp = requests.post(
                WEBHOOK_URL,
                json={
                    "title": title or "Untitled BRD",
                    "submitted_by": current_user["email"],
                    "user_role": current_user["role"],
                    "brd_text": brd_text,
                    "simulate_fault": simulate_fault
                },
                timeout=240
                )
                if resp.status_code == 403:
                    err_data = resp.json()
                    st.error(f"⛔ **{err_data.get('error', 'AGENT_AUTHORIZATION_DENIED')}**: {err_data.get('message')}")
                else:
                    resp.raise_for_status()
                    st.session_state["last_result"] = resp.json()
            except Exception as e:
                st.error(f"Orchestration failed: {e}")

# Render Results Dashboard
if "last_result" in st.session_state:
    res = st.session_state["last_result"]
    final_eval = res.get("final_evaluation", {})
    v0_eval = res.get("v0_evaluation", {})
    artifacts = res.get("artifacts", {})
    badge = final_eval.get("badge", "AMBER")
    findings = final_eval.get("critic_findings", [])

    st.divider()
    display_title = res.get("title") if res.get("title") not in (None, "", "None", "null") else "No Title"
    st.subheader(f"📦 Delivery Package: {display_title} (Run ID: `{res['run_id']}`)")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Quality Badge", badge, f"v{res.get('version', 0)}")
    m2.metric("Overall Score", f"{final_eval.get('overall_score', 0)}/10", f"v0: {v0_eval.get('overall_score', 0)}")
    m3.metric("Groundedness", f"{final_eval.get('groundedness_score', 0)}/10")
    m4.metric("Completeness", f"{final_eval.get('completeness_score', 0)}/10")
    m5.metric("Consistency", f"{final_eval.get('consistency_score', 0)}/10")
    m6.metric("Actionability", f"{final_eval.get('actionability_score', 0)}/10")

    # Self-Healing Critic Loop (v0 -> v1) Comparison Card
    if res.get("version", 0) > 0:
        st.divider()
        st.subheader("🔄 Bounded Self-Healing Loop Executed (`v0 → v1`)")
        v0_findings = v0_eval.get("critic_findings", [])
        c_v0, c_v1 = st.columns(2)
        with c_v0:
            v0_b = v0_eval.get("badge", "AMBER")
            st.markdown(f"**Initial Draft (`v0`):** {colored_badge(v0_b)} — **{v0_eval.get('overall_score', 0)}/10**", unsafe_allow_html=True)
            st.caption(
                f"Groundedness: {v0_eval.get('groundedness_score', 0)} | "
                f"Completeness: {v0_eval.get('completeness_score', 0)} | "
                f"Consistency: {v0_eval.get('consistency_score', 0)} | "
                f"Actionability: {v0_eval.get('actionability_score', 0)}"
            )
            st.markdown("**Defects Diagnosed by Critic (`v0`):**")
            if v0_findings:
                for f in v0_findings:
                    st.error(f"**[{f.get('severity', 'ISSUE')}]** ({f.get('target_agent', 'agent')}): {f.get('issue', '')} → *Fix applied:* {f.get('repair_instruction', '')}")
            else:
                st.write("Quality gate threshold (< 8.0) triggered targeted refinement.")
        with c_v1:
            delta = round(final_eval.get("overall_score", 0) - v0_eval.get("overall_score", 0), 2)
            st.markdown(f"**Self-Healed Package (`v1`):** {colored_badge(badge)} — **{final_eval.get('overall_score', 0)}/10** (`{delta:+}`)", unsafe_allow_html=True)
            st.caption(
                f"Groundedness: {final_eval.get('groundedness_score', 0)} | "
                f"Completeness: {final_eval.get('completeness_score', 0)} | "
                f"Consistency: {final_eval.get('consistency_score', 0)} | "
                f"Actionability: {final_eval.get('actionability_score', 0)}"
            )
            st.success("✅ Targeted agents re-executed with Critic repair instructions and re-verified against PostgreSQL `kb_chunks`.")

    if res.get("markdown_report"):
        st.download_button(
            "⬇️ Download Full Markdown Package (.md)",
            data=res["markdown_report"],
            file_name=f"engineering_package_{res.get('run_id', 'output')[:8]}.md",
            mime="text/markdown"
        )

    # Human-in-the-Loop (HITL) Engineering Manager Sign-Off & Escalation Console
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    if db_host == "host.docker.internal":
        db_host = "localhost"
    st.divider()
    st.subheader("👤 Human-in-the-Loop: Engineering Manager Sign-Off & Escalation Gate")
    if badge != "GREEN":
        st.warning(
            f"⚠️ **Human Escalation Required:** Quality gate returned **{badge}** ({final_eval.get('overall_score')}/10) after bounded revision `v{res.get('version', 0)}`. "
            "Review open ambiguities or Critic findings below before releasing to Jira."
        )
        if findings:
            st.dataframe(findings, use_container_width=True, hide_index=True)
    else:
        st.info("✅ Quality gate passed **GREEN**. Confirm Engineering Manager sign-off to log human audit approval.")

    reviewer_notes = st.text_input("Reviewer Comments / Clarification Notes", value="Reviewed solution architecture, tech stack trade-offs, NFR assumptions, and PoC exit criteria.")
    c_app, c_rej = st.columns(2)

    def record_hitl_decision(decision_status: str):
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=os.getenv("POSTGRES_PORT", "5432"),
                dbname=os.getenv("POSTGRES_DB", "brd_system_db"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "sa"),
            )
            cur = conn.cursor()
            cur.execute("UPDATE runs SET status = %s, updated_at = NOW() WHERE run_id = %s::uuid;", (decision_status, res["run_id"]))
            cur.execute(
                """INSERT INTO audit_events (run_id, agent_name, input_hash, output_hash, guardrail_flags, latency_ms, tokens_used)
                   VALUES (%s::uuid, 'Human_Engineering_Manager', md5(%s), md5(%s), %s::jsonb, 0, 0);""",
                (
                    res["run_id"],
                    res["run_id"],
                    decision_status,
                    json.dumps({"decision": decision_status, "reviewer": submitted_by, "badge_at_review": badge, "notes": reviewer_notes})
                )
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"Human-in-the-Loop audit recorded: **{decision_status}** by `{submitted_by}`")
        except Exception as db_err:
            st.error(f"Could not record sign-off in DB: {db_err}")

    if current_user["role"] != "Engineering_Manager":
        st.warning(f"🔒 Role `{current_user['role']}` has read-only review access. Only an **Engineering_Manager** can approve or reject release.")
    else:
        with c_app:
            if st.button("✅ Approve & Release Package", type="primary"):
                record_hitl_decision("APPROVED_BY_EM")
        with c_rej:
            if st.button("❌ Reject & Request Customer Clarification"):
                record_hitl_decision("REJECTED_BY_EM")

    def render_agent_tab(data):
        if not isinstance(data, dict) or not data:
            st.info("No output generated for this agent.")
            return
        for k, v in data.items():
            if k in ("agent", "citations", "all_covered_requirements"):
                continue
            label = k.replace("_", " ").title()
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                st.markdown(f"**{label}**")
                st.dataframe(v, use_container_width=True, hide_index=True)
            elif isinstance(v, list):
                st.markdown(f"**{label}:**")
                for item in v:
                    st.markdown(f"- {item}")
            elif isinstance(v, dict):
                st.markdown(f"**{label}:**")
                for dk, dv in v.items():
                    st.markdown(f"- **{dk.replace('_', ' ').title()}:** {dv}")
            else:
                st.markdown(f"**{label}:** {v}")
        if data.get("all_covered_requirements"):
            st.markdown(f"**Covered Requirements:** `{', '.join(str(r) for r in data['all_covered_requirements'])}`")
        if data.get("citations"):
            st.markdown(f"**KB Citations (`CHUNK_ID`):** `{', '.join(str(c) for c in data['citations'])}`")

    if res.get("markdown_report"):
        with st.expander("📄 Formatted Engineering Delivery Package (Executive View)", expanded=False):
            st.markdown(res["markdown_report"])

    # Toggleable Agent Execution Logs (Deselected by default)
    st.divider()
    show_agent_logs = st.checkbox("🔍 Show Agent Execution Outputs & Critic Logs", value=False)
    if show_agent_logs:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📅 Engineering Plan (Agent 2)",
            "⏱️ Schedule & Buffer (Agent 3)",
            "🏛️ Solution Architecture (Agent 4)",
            "🧰 Tech Stack Trade-Offs (Agent 6)",
            "🧪 PoC Plan (Agent 5)",
            "⚖️ Critic & Judge Findings (Agent 7)"
        ])
        with tab1:
            render_agent_tab(artifacts.get("engineering_plan", {}))
        with tab2:
            render_agent_tab(artifacts.get("schedule_estimator", {}))
        with tab3:
            render_agent_tab(artifacts.get("solution_architect", {}))
        with tab4:
            render_agent_tab(artifacts.get("tech_stack", {}))
        with tab5:
            render_agent_tab(artifacts.get("poc_planner", {}))
        with tab6:
            render_agent_tab(final_eval)