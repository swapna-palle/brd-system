import json
import os
import time
import requests

WEBHOOK_URL = "http://localhost:5678/webhook/brd-to-engineering"
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "eval_dataset", "benchmark_brds.json")


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    scenarios = dataset.get("scenarios", [])
    summary_rows = []

    for idx, sc in enumerate(scenarios, start=1):
        name = f"{sc['eval_id']}: {sc['title']}"
        expected = sc.get("expected_outputs", {})
        expect_reject = expected.get("blocked_before_llm", False)

        payload = {
            "title": sc["title"],
            "submitted_by": "qa_benchmark@corp.internal",
            "user_role": sc.get("user_role", "Engineering_Manager"),
            "simulate_fault": sc.get("simulate_fault", False),
            "brd_text": sc["brd_text"],
        }

        print(f"\n{'='*70}\nRunning {name}...\n{'='*70}")
        t0 = time.time()
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=240)
        elapsed = round(time.time() - t0, 2)

        if expect_reject:
            blocked = resp.status_code >= 400
            print(f"Elapsed Time : {elapsed}s")
            print(f"Guardrail    : {'BLOCKED AS EXPECTED (HTTP ' + str(resp.status_code) + ')' if blocked else 'UNEXPECTED PASS'}")
            summary_rows.append({
                "eval_id": sc["eval_id"],
                "test": sc["title"],
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
            for finding in v0.get("critic_findings", []):
                print(f"  - Fixed [{finding.get('severity')}]: {finding.get('issue')}")

        if sc["eval_id"] == "EVAL-002" and data.get("markdown_report"):
            out_path = os.path.join(os.path.dirname(__file__), "..", "sample_engineering_package.md")
            with open(out_path, "w", encoding="utf-8") as out_f:
                out_f.write(data["markdown_report"])
            print("Saved sample_engineering_package.md for GitHub deliverables!")

        summary_rows.append({
            "eval_id": sc["eval_id"],
            "test": sc["title"],
            "run_id": data.get("run_id"),
            "latency_sec": elapsed,
            "v0_score": v0.get("overall_score"),
            "v0_badge": v0.get("badge"),
            "final_score": vf.get("overall_score"),
            "final_badge": vf.get("badge"),
            "revisions": ver,
        })

    print("\n\n=== BRDSYSTEM EVALUATION BENCHMARK SUMMARY ===")
    print(json.dumps(summary_rows, indent=2))


if __name__ == "__main__":
    main()
