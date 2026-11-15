import json
import time
import requests

WEBHOOK_URL = "http://localhost:5678/webhook/brd-to-engineering"

TEST_CASES = [
    {
        "name": "Test 1: Simple Internal Approval Hub (Engineering_Manager)",
        "expect_reject": False,
        "payload": {
            "title": "Internal Operations Approval Hub (.NET)",
            "submitted_by": "em_lead@corp.internal",
            "user_role": "Engineering_Manager",
            "simulate_fault": False,
            "brd_text": (
                "Business Requirement Document: Internal Operations Approval Hub. "
                "REQ-001: Build an internal web application using .NET and PostgreSQL for managers to approve travel and equipment requests. "
                "REQ-002: Enforce Microsoft Entra ID single sign-on with role-based access control for Employees and Managers. "
                "REQ-003: Provide an immutable audit log of all approvals and rejections. "
                "NFR-001: Expected peak load is 150 concurrent internal users with p95 API latency under 300ms."
            ),
        },
    },
    {
        "name": "Test 2: Medium FinTech Vendor Onboarding Portal (Product_Owner - Read/Plan Only)",
        "expect_reject": False,
        "payload": {
            "title": "Enterprise Vendor Onboarding & Settlement Portal",
            "submitted_by": "po_lead@corp.internal",
            "user_role": "Product_Owner",
            "simulate_fault": False,
            "brd_text": (
                "Business Requirement Document: Enterprise Vendor Onboarding & Settlement Portal. "
                "REQ-001: Build a .NET Clean Architecture portal allowing enterprise vendors to register tax profiles and bank accounts. "
                "REQ-002: Integrate with a third-party external KYC verification REST API with resilience retries and circuit breakers. "
                "REQ-003: Publish VendorApproved domain events reliably to Azure Service Bus using a transactional outbox pattern. "
                "REQ-004: Enforce idempotency keys on all state-mutating payout and approval POST endpoints. "
                "NFR-001: System must support 1,200 requests per second, 99.95% availability, and Microsoft Entra ID authentication."
            ),
        },
    },
    {
        "name": "Test 3: Fault-Injection Self-Healing Test (v0 -> v1 Critic Loop)",
        "expect_reject": False,
        "payload": {
            "title": "Multi-Currency Treasury Payout Engine (Fault-Injected)",
            "submitted_by": "qa_audit@corp.internal",
            "user_role": "Engineering_Manager",
            "simulate_fault": True,
            "brd_text": (
                "Business Requirement Document: Multi-Currency Treasury Payout Engine. "
                "REQ-001: Process automated cross-border vendor payouts in USD, EUR, and GBP using .NET and PostgreSQL. "
                "REQ-002: Enforce dual-control manager approval workflow via Microsoft Entra ID RBAC before releasing funds. "
                "REQ-003: Guarantee exactly-once idempotent ledger postings with full audit trail."
            ),
        },
    },
    {
        "name": "Edge Case 1: Ambiguous BRD (Missing NFRs & Metrics)",
        "expect_reject": False,
        "payload": {
            "title": "Customer Notification Service (Ambiguous NFRs)",
            "submitted_by": "qa_edge@corp.internal",
            "user_role": "Engineering_Manager",
            "simulate_fault": False,
            "brd_text": (
                "Business Requirement Document: Customer Notification Service. "
                "REQ-001: Send email and SMS alerts when vendor invoices are approved. "
                "REQ-002: System must be fast, highly available, and secure for enterprise users."
            ),
        },
    },
    {
        "name": "Edge Case 2: Conflicting Constraints (Unrealistic 1-Week Timeline)",
        "expect_reject": False,
        "payload": {
            "title": "Global Real-Time Settlement Engine (Conflicting Constraints)",
            "submitted_by": "qa_edge@corp.internal",
            "user_role": "Engineering_Manager",
            "simulate_fault": False,
            "brd_text": (
                "Business Requirement Document: Global Real-Time Settlement Engine. "
                "REQ-001: Build a multi-region active-active cross-border banking settlement platform in .NET. "
                "NFR-001: Must support 50,000 TPS with 99.999% uptime and full PCI-DSS certification. "
                "CONSTRAINT-001: Total delivery timeline must be 1 week with 1 developer and zero infrastructure budget."
            ),
        },
    },
    {
        "name": "Edge Case 3: Malformed / Too-Short Input Guardrail Test",
        "expect_reject": True,
        "payload": {
            "title": "Invalid Short Input",
            "submitted_by": "qa_edge@corp.internal",
            "user_role": "Engineering_Manager",
            "simulate_fault": False,
            "brd_text": "Build an app quickly.",
        },
    },
    {
        "name": "Edge Case 4: Unauthorized Caller Role Policy Denial (Others -> HTTP 403)",
        "expect_reject": True,
        "payload": {
            "title": "Unauthorized Role Execution Test",
            "submitted_by": "guest@corp.internal",
            "user_role": "Others",
            "simulate_fault": False,
            "brd_text": (
                "Business Requirement Document: Unauthorized Access Test. "
                "REQ-001: Attempt to trigger multi-agent planning pipeline with an unprivileged role."
            ),
        },
    },
]


def main():
    summary_rows = []
    for idx, tc in enumerate(TEST_CASES, start=1):
        print(f"\n{'='*70}\nRunning {tc['name']}...\n{'='*70}")
        t0 = time.time()
        resp = requests.post(WEBHOOK_URL, json=tc["payload"], timeout=240)
        elapsed = round(time.time() - t0, 2)

        if tc.get("expect_reject"):
            blocked = resp.status_code >= 400
            print(f"Elapsed Time : {elapsed}s")
            print(f"Guardrail    : {'BLOCKED AS EXPECTED (HTTP ' + str(resp.status_code) + ')' if blocked else 'UNEXPECTED PASS'}")
            summary_rows.append({
                "test": tc["name"],
                "run_id": f"N/A (Blocked HTTP {resp.status_code})",
                "latency_sec": elapsed,
                "v0_score": None,
                "v0_badge": "REJECTED",
                "final_score": None,
                "final_badge": "REJECTED",
                "revisions": 0,
            })
            continue

        resp.raise_for_status()
        data = resp.json()

        v0 = data.get("v0_evaluation", {})
        vf = data.get("final_evaluation", {})
        ver = data.get("version", 0)

        print(f"Run ID       : {data.get('run_id')}")
        print(f"Elapsed Time : {elapsed}s")
        print(f"v0 Score     : {v0.get('overall_score')} ({v0.get('badge')})")
        print(f"Final Score  : {vf.get('overall_score')} ({vf.get('badge')}) [Version: v{ver}]")

        if ver > 0:
            print(f"Self-Healed  : v0={v0.get('overall_score')} ({v0.get('badge')}) -> v1={vf.get('overall_score')} ({vf.get('badge')})")
            for f in v0.get("critic_findings", []):
                print(f"  - Fixed [{f.get('severity')}]: {f.get('issue')}")

        if idx == 2 and data.get("markdown_report"):
            with open("sample_engineering_package.md", "w", encoding="utf-8") as f:
                f.write(data["markdown_report"])
            print("Saved sample_engineering_package.md for GitHub deliverables!")

        summary_rows.append({
            "test": tc["name"],
            "run_id": data.get("run_id"),
            "latency_sec": elapsed,
            "v0_score": v0.get("overall_score"),
            "v0_badge": v0.get("badge"),
            "final_score": vf.get("overall_score"),
            "final_badge": vf.get("badge"),
            "revisions": ver,
        })

    print("\n\n=== CAPSTONE EVALUATION BENCHMARK SUMMARY ===")
    print(json.dumps(summary_rows, indent=2))


if __name__ == "__main__":
    main()
