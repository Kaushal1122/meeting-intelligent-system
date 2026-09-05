"""
Phase 11 Master Runner Module.
Aggregates all evaluation suites, sensitivity experiments, ablation studies,
and determinism verifications into a single canonical metrics payload.
"""

from typing import Any, Dict, Optional
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
for p in [PROJECT_ROOT, BACKEND_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from backend.evaluation.deadline_sensitivity import evaluate_deadline_sensitivity
from backend.evaluation.priority_evaluation import evaluate_priority_engine
from backend.evaluation.confidence_evaluation import evaluate_confidence_engine
from backend.evaluation.review_evaluation import evaluate_review_engine
from backend.evaluation.explainability_evaluation import evaluate_explainability_engine
from backend.evaluation.personalization_evaluation import evaluate_personalization_engine
from backend.evaluation.ablation import run_ablation_study
from backend.evaluation.determinism import evaluate_determinism


def run_full_phase11_evaluation(save_json: bool = True) -> Dict[str, Any]:
    """
    Execute all Phase 11 evaluations and aggregate results.
    """
    print("Executing Phase 11 Deadline Sensitivity Analysis...")
    deadline_results = evaluate_deadline_sensitivity()

    print("Executing Phase 11 Priority Engine Evaluation...")
    priority_results = evaluate_priority_engine()

    print("Executing Phase 11 Confidence Engine Evaluation...")
    confidence_results = evaluate_confidence_engine()

    print("Executing Phase 11 Review Engine Evaluation...")
    review_results = evaluate_review_engine()

    print("Executing Phase 11 Explainability Engine Evaluation...")
    explainability_results = evaluate_explainability_engine()

    print("Executing Phase 11 Personalization Engine Evaluation...")
    personalization_results = evaluate_personalization_engine()

    print("Executing Phase 11 Ablation Study...")
    ablation_results = run_ablation_study()

    print("Executing Phase 11 Determinism Evaluation (5 runs)...")
    determinism_results = evaluate_determinism(num_runs=5)

    # Master pass/fail assessment
    all_passed = (
        deadline_results["monotonicity"]["status"] == "PASS"
        and deadline_results["comparative_study"]["verdict"] == "PASS"
        and deadline_results["dashboard_case_analysis"]["is_justified"]
        and priority_results["es2002a_priority_evaluation"]["mathematical_consistency"]["all_factors_sum_to_score"]
        and confidence_results["independence_evaluation"]["status"] == "PASS"
        and confidence_results["member3_isolation_evaluation"]["status"] == "PASS"
        and review_results["trigger_coverage_evaluation"]["status"] == "PASS"
        and explainability_results["read_only_preservation"]["status"] == "PASS"
        and explainability_results["evidence_fabrication_check"]["status"] == "PASS"
        and personalization_results["all_invariance_passed"]
        and determinism_results["determinism_pass"]
    )

    aggregated = {
        "phase": "PHASE_11_EVALUATION_ABLATION_STUDY",
        "overall_status": "PASS" if all_passed else "FAIL",
        "deadline_sensitivity": deadline_results,
        "priority_evaluation": priority_results,
        "confidence_evaluation": confidence_results,
        "review_evaluation": review_results,
        "explainability_evaluation": explainability_results,
        "personalization_evaluation": personalization_results,
        "ablation_study": ablation_results,
        "determinism": determinism_results,
    }

    if save_json:
        out_dir = PROJECT_ROOT / "docs" / "evaluation_results"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "phase11_metrics.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(aggregated, f, indent=2)
        print(f"Metrics saved to {out_file}")

    return aggregated


if __name__ == "__main__":
    results = run_full_phase11_evaluation(save_json=True)
    print(f"\nPhase 11 Master Evaluation Complete. Overall Status: {results['overall_status']}")
