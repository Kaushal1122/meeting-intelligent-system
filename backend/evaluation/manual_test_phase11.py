"""
Phase 11 Manual Verification CLI Script.
Formats and prints complete evaluation metrics and ablation findings
matching Section 22 specification.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
for p in [PROJECT_ROOT, BACKEND_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from backend.evaluation.run_phase11 import run_full_phase11_evaluation


def main():
    metrics = run_full_phase11_evaluation(save_json=True)

    es_pri = metrics["priority_evaluation"]["es2002a_priority_evaluation"]
    es_conf = metrics["confidence_evaluation"]["es2002a_confidence_evaluation"]
    es_rev = metrics["review_evaluation"]["es2002a_review_evaluation"]
    dl = metrics["deadline_sensitivity"]
    ablation = metrics["ablation_study"]
    det = metrics["determinism"]

    dash = dl["dashboard_case_analysis"]
    dash_math = dash["mathematical_analysis"]

    print("\n" + "=" * 60)
    print("PHASE 11 - EVALUATION + ABLATION STUDY RESULTS")
    print("=" * 60)

    # 1. REAL DATA - ES2002a
    print("\n1. REAL DATA - ES2002a")
    print("-" * 60)
    print(f"Total Tasks: {es_pri['total_items']}")
    print("Total Decisions: 9")

    pri_dist = es_pri["priority_distribution"]
    print("\nPriority Distribution:")
    print(f"  HIGH:   {pri_dist['HIGH']} ({pri_dist['high_pct']}%)")
    print(f"  MEDIUM: {pri_dist['MEDIUM']} ({pri_dist['med_pct']}%)")
    print(f"  LOW:    {pri_dist['LOW']} ({pri_dist['low_pct']}%)")

    conf_dist = es_conf["confidence_distribution"]
    total_conf = es_conf["total_tasks"]
    print("\nConfidence Distribution:")
    print(f"  HIGH:   {conf_dist['HIGH']} ({round(conf_dist['HIGH'] / total_conf * 100, 1)}%)")
    print(f"  MEDIUM: {conf_dist['MEDIUM']} ({round(conf_dist['MEDIUM'] / total_conf * 100, 1)}%)")
    print(f"  LOW:    {conf_dist['LOW']} ({round(conf_dist['LOW'] / total_conf * 100, 1)}%)")

    rev_dist = es_rev["review_status_distribution"]
    total_rev = es_rev["total_tasks"]
    print("\nReview Distribution:")
    print(f"  AUTO_ACCEPT:        {rev_dist['AUTO_ACCEPT']} ({round(rev_dist['AUTO_ACCEPT'] / total_rev * 100, 1)}%)")
    print(f"  REVIEW_RECOMMENDED: {rev_dist['REVIEW_RECOMMENDED']} ({round(rev_dist['REVIEW_RECOMMENDED'] / total_rev * 100, 1)}%)")
    print(f"  REVIEW_REQUIRED:    {rev_dist['REVIEW_REQUIRED']} ({round(rev_dist['REVIEW_REQUIRED'] / total_rev * 100, 1)}%)")

    # 2. DEADLINE SENSITIVITY
    print("\n2. DEADLINE SENSITIVITY")
    print("-" * 60)
    print(f"Monotonicity: {dl['monotonicity']['status']}")
    print(f"Tomorrow vs Friday: {dl['comparative_study']['verdict']}")
    print("Dashboard Case (Tomorrow Afternoon Audio Driver Integration):")
    print(f"  Input Deadline: {dash['deadline']}")
    print(f"  Assigned Priority: {dash['priority_level']} ({dash['priority_score']:.4f})")
    print(f"  Assigned Confidence: {dash['confidence_level']} ({dash['confidence_score']:.4f})")
    print(f"  Urgency Factor Value: {dash_math['deadline_raw']:.2f}")
    print("  Urgency Factor Weight: 0.25")
    print(f"  Urgency Factor Contribution: {dash_math['deadline_contribution']:.4f}")
    print(f"  Ceiling Without Blocker/Crisis/Decision: {dash_math['theoretical_ceiling_without_blocker_or_crisis']:.2f}")
    print(f"  High Priority Threshold: {dash_math['threshold_high']:.2f}")
    print(f"  Is Behavior Mathematically Justified: {'YES' if dash['is_justified'] else 'NO'}")

    # 3. ABLATION STUDY
    print("\n3. ABLATION STUDY")
    print("-" * 60)
    for ab in ablation["ablations"]:
        print(f"\n{ab['variant']}:")
        print(f"  Description: {ab['description']}")
        print(f"  Impact: {ab['impact'].get('loss', '')}")

    # 4. DETERMINISM
    print("\n4. DETERMINISM")
    print("-" * 60)
    print(f"Runs: {det['num_runs']}")
    print(f"Drift: {max(det['priority_score_max_drift'], det['confidence_score_max_drift']):.6f}")
    print(f"Status: {'PASS' if det['determinism_pass'] else 'FAIL'}")

    # MASTER VERDICT
    print("\n" + "=" * 60)
    print(f"ALL VERIFICATIONS: {metrics['overall_status']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
