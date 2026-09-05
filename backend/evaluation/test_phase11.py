"""
Automated Unit Test Suite for Phase 11 Evaluation and Ablation Study.
Validates all evaluations, monotonicity checks, independence proofs,
trigger coverage, read-only invariance, and determinism.
"""

from pathlib import Path
import unittest
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


class TestPhase11EvaluationSuite(unittest.TestCase):
    """Phase 11 scientific evaluation and ablation test suite."""

    def test_deadline_sensitivity_monotonicity(self):
        """Verify deadline monotonicity and dashboard case mathematical consistency."""
        res = evaluate_deadline_sensitivity()
        self.assertEqual(res["monotonicity"]["status"], "PASS")
        self.assertEqual(res["comparative_study"]["verdict"], "PASS")
        self.assertTrue(res["dashboard_case_analysis"]["is_justified"])
        # Check delta: tomorrow > Friday >= Monday
        self.assertGreater(res["comparative_study"]["delta_tomorrow_to_friday"], 0.0)
        self.assertGreaterEqual(res["comparative_study"]["delta_friday_to_monday"], 0.0)

    def test_priority_engine_evaluation(self):
        """Verify priority engine on ES2002a data and synthetic test cases."""
        res = evaluate_priority_engine()
        es = res["es2002a_priority_evaluation"]
        self.assertEqual(es["total_items"], 32)
        self.assertTrue(es["mathematical_consistency"]["all_factors_sum_to_score"])
        self.assertEqual(es["mathematical_consistency"]["violations_count"], 0)
        self.assertEqual(res["synthetic_behavior_evaluation"]["total_cases"], 12)

    def test_confidence_engine_evaluation(self):
        """Verify confidence calibration, 4-quadrant independence, and Member 3 isolation."""
        res = evaluate_confidence_engine()
        es = res["es2002a_confidence_evaluation"]
        self.assertEqual(es["total_tasks"], 32)
        self.assertEqual(res["independence_evaluation"]["status"], "PASS")
        self.assertEqual(res["member3_isolation_evaluation"]["status"], "PASS")
        self.assertTrue(res["member3_isolation_evaluation"]["isolated"])

    def test_review_engine_trigger_coverage(self):
        """Verify all 6 REVIEW_REQUIRED and 7 REVIEW_RECOMMENDED triggers."""
        res = evaluate_review_engine()
        es = res["es2002a_review_evaluation"]
        self.assertEqual(es["total_tasks"], 32)
        triggers = res["trigger_coverage_evaluation"]
        self.assertEqual(triggers["status"], "PASS")
        self.assertEqual(triggers["total_triggers_tested"], 13)

    def test_explainability_read_only_invariance(self):
        """Verify zero decision drift and zero fabricated evidence in explainability."""
        res = evaluate_explainability_engine()
        self.assertEqual(res["total_items_evaluated"], 32)
        self.assertEqual(res["read_only_preservation"]["status"], "PASS")
        self.assertEqual(res["read_only_preservation"]["decision_drift_count"], 0)
        self.assertEqual(res["explanation_completeness"]["status"], "PASS")
        self.assertEqual(res["evidence_fabrication_check"]["status"], "PASS")
        self.assertEqual(res["evidence_fabrication_check"]["fabricated_evidence_count"], 0)

    def test_personalization_invariance(self):
        """Verify 100% canonical value invariance across all role projections."""
        res = evaluate_personalization_engine()
        self.assertTrue(res["all_invariance_passed"])
        self.assertEqual(res["total_violations_count"], 0)
        self.assertIn("MANAGER", res["roles_evaluated"])
        self.assertIn("DEVELOPER", res["roles_evaluated"])
        self.assertIn("INTERN", res["roles_evaluated"])
        self.assertIn("DEFAULT", res["roles_evaluated"])

    def test_pipeline_determinism(self):
        """Verify bit-for-bit determinism across repeated runs."""
        res = evaluate_determinism(num_runs=3)
        self.assertTrue(res["determinism_pass"])
        self.assertEqual(res["priority_score_max_drift"], 0.0)
        self.assertEqual(res["confidence_score_max_drift"], 0.0)
        self.assertEqual(res["priority_level_flips"], 0)
        self.assertEqual(res["confidence_level_flips"], 0)
        self.assertEqual(res["review_status_flips"], 0)

    def test_ablation_study(self):
        """Verify 7-stage ablation study executes and quantifies information loss."""
        res = run_ablation_study()
        self.assertEqual(res["baseline"]["total_tasks"], 32)
        self.assertEqual(len(res["ablations"]), 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
