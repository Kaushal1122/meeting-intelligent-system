"""
Human Review Triage Evaluation Module (Phase 11).
Evaluates real ES2002a review triage distribution, reason-code frequencies,
and exhaustive coverage of all 6 REVIEW_REQUIRED and 7 REVIEW_RECOMMENDED triggers.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
for p in [PROJECT_ROOT, BACKEND_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from backend.member4.schemas import (
    ConfidenceAssessment,
    ConfidenceEnrichedActionItem,
    ConfidenceFactorContribution,
    ConfidenceLevel,
    ContextRichActionItem,
    LocalizedDialogueContext,
    PriorityAssessment,
    PriorityFactorContribution,
    PriorityLevel,
    RelatedDecisionContext,
    ReviewReasonCode,
    ReviewStatus,
    TopicContextStatus,
)
from backend.member4.normalizer import normalize_member3_input
from backend.member4.context_engine import build_task_context
from backend.member4.priority_engine import (
    DEFAULT_CONFIG,
    infer_task_priorities,
)
from backend.member4.confidence_engine import (
    DEFAULT_CONFIDENCE_CONFIG,
    infer_task_confidence,
)
from backend.member4.review_engine import (
    DEFAULT_REVIEW_CONFIG,
    evaluate_task_triage,
    triage_action_items,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def evaluate_es2002a_review() -> Dict[str, Any]:
    """Evaluate review triage decisions on real ES2002a data (32 action items)."""
    m3_file = PROCESSED_DIR / "ES2002a_member3_results.json"
    m2_file = PROCESSED_DIR / "ES2002a_member2_results.json"

    with open(m3_file, "r", encoding="utf-8") as f:
        m3_data = json.load(f)
    with open(m2_file, "r", encoding="utf-8") as f:
        m2_data = json.load(f)

    norm_output = normalize_member3_input(m3_data)
    ctx_output = build_task_context(norm_output, m2_data)
    pri_output = infer_task_priorities(ctx_output, DEFAULT_CONFIG)
    conf_output = infer_task_confidence(pri_output, DEFAULT_CONFIDENCE_CONFIG)
    triage_output = triage_action_items(conf_output, DEFAULT_REVIEW_CONFIG)

    status_counts = {
        "AUTO_ACCEPT": 0,
        "REVIEW_RECOMMENDED": 0,
        "REVIEW_REQUIRED": 0,
    }
    reason_code_counts = {}

    for item in triage_output.action_items:
        st = item.review_decision.status.value if hasattr(item.review_decision.status, "value") else str(item.review_decision.status)
        status_counts[st] = status_counts.get(st, 0) + 1

        for code in item.review_decision.reason_codes:
            c_val = code.value if hasattr(code, "value") else str(code)
            reason_code_counts[c_val] = reason_code_counts.get(c_val, 0) + 1

    return {
        "dataset": "ES2002a",
        "total_tasks": len(triage_output.action_items),
        "review_status_distribution": status_counts,
        "reason_code_distribution": reason_code_counts,
    }


def evaluate_review_triggers() -> Dict[str, Any]:
    """
    Exhaustively verify all 6 REVIEW_REQUIRED triggers and 7 REVIEW_RECOMMENDED triggers
    under controlled synthetic test conditions.
    """
    # 1. REVIEW_REQUIRED triggers
    required_tests = [
        ("Trigger 1: HIGH priority + LOW confidence", 0.75, PriorityLevel.HIGH, 0.40, ConfidenceLevel.LOW, TopicContextStatus.RESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_REQUIRED),
        ("Trigger 2: HIGH priority + ambiguous deadline", 0.70, PriorityLevel.HIGH, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.RESOLVED, True, "SPEAKER_01", ReviewStatus.REVIEW_REQUIRED),
        ("Trigger 3: HIGH priority + unassigned", 0.70, PriorityLevel.HIGH, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.RESOLVED, False, None, ReviewStatus.REVIEW_REQUIRED),
        ("Trigger 4: MISSING_REFERENCE context", 0.20, PriorityLevel.LOW, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.MISSING_REFERENCE, False, "SPEAKER_01", ReviewStatus.REVIEW_REQUIRED),
        ("Trigger 5: UNRESOLVED context", 0.20, PriorityLevel.LOW, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.UNRESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_REQUIRED),
        ("Trigger 6: LOW confidence alone", 0.20, PriorityLevel.LOW, 0.35, ConfidenceLevel.LOW, TopicContextStatus.RESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_REQUIRED),
    ]

    # 2. REVIEW_RECOMMENDED triggers
    recommended_tests = [
        ("Trigger 1: HIGH priority + MEDIUM confidence", 0.70, PriorityLevel.HIGH, 0.65, ConfidenceLevel.MEDIUM, TopicContextStatus.RESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_RECOMMENDED),
        ("Trigger 2: MEDIUM confidence alone", 0.25, PriorityLevel.LOW, 0.60, ConfidenceLevel.MEDIUM, TopicContextStatus.RESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_RECOMMENDED),
        ("Trigger 3: PARTIALLY_RESOLVED context", 0.25, PriorityLevel.LOW, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.PARTIALLY_RESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_RECOMMENDED),
        ("Trigger 4: Multiple competing decisions (>=2)", 0.25, PriorityLevel.LOW, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.RESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_RECOMMENDED),
        ("Trigger 5: Weak dialogue grounding (<0.50)", 0.25, PriorityLevel.LOW, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.RESOLVED, False, "SPEAKER_01", ReviewStatus.REVIEW_RECOMMENDED),
        ("Trigger 6: Non-critical ambiguous deadline", 0.25, PriorityLevel.LOW, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.RESOLVED, True, "SPEAKER_01", ReviewStatus.REVIEW_RECOMMENDED),
        ("Trigger 7: Non-critical unassigned task", 0.25, PriorityLevel.LOW, 0.80, ConfidenceLevel.HIGH, TopicContextStatus.RESOLVED, False, None, ReviewStatus.REVIEW_RECOMMENDED),
    ]

    results = []

    for name, p_score, p_lvl, c_score, c_lvl, status_enum, is_amb, resp, exp_status in required_tests + recommended_tests:
        grounding = 0.30 if "Weak dialogue grounding" in name else 0.85

        has_context = (status_enum not in [TopicContextStatus.MISSING_REFERENCE, TopicContextStatus.UNRESOLVED])
        ctx = LocalizedDialogueContext(
            window_text="[01:00] SPEAKER_01: Review item.",
            segment_ids=[501, 502],
            trigger_segment_id=501,
            speakers=["SPEAKER_01"],
            start=60.0,
            end=65.0,
        ) if has_context else None

        related_decs = []
        if "Multiple competing decisions" in name:
            related_decs = [
                RelatedDecisionContext(decision_id="d1", topic_reference=50, decision="Decision A"),
                RelatedDecisionContext(decision_id="d2", topic_reference=50, decision="Decision B"),
            ]

        p_assess = PriorityAssessment(
            score=p_score,
            level=p_lvl,
            factor_contributions=[],
            scoring_breakdown={},
            evidence_summary=[],
        )

        c_factors = [
            ConfidenceFactorContribution(
                factor_name="localized_evidence_grounding",
                raw_value=grounding,
                weight=0.20,
                weighted_contribution=round(grounding * 0.20, 4),
                has_evidence=True,
                evidence_text="",
                evidence_segment_ids=[],
            )
        ]

        c_assess = ConfidenceAssessment(
            score=c_score,
            level=c_lvl,
            factor_contributions=c_factors,
            scoring_breakdown={},
            evidence_quality_notes=[],
        )

        item = ConfidenceEnrichedActionItem(
            item_id="synth_triage_001",
            task="Perform operational procedure.",
            responsible_person=resp,
            speaker_id=resp if resp else None,
            display_name=resp,
            name_source="diarization_fallback" if resp else None,
            is_unassigned=(resp is None),
            deadline="soon" if is_amb else None,
            is_ambiguous_deadline=is_amb,
            topic_reference=50 if status_enum != TopicContextStatus.MISSING_REFERENCE else None,
            context_status=status_enum,
            topic_summary="System sprint review." if has_context else None,
            topic_speakers=["SPEAKER_01"] if has_context else [],
            localized_context=ctx,
            context_start=60.0 if has_context else None,
            context_end=65.0 if has_context else None,
            related_decisions=related_decs,
            deadline_context_snippet="soon" if is_amb else None,
            source_priority=None,
            source_confidence_score=None,
            is_duplicate=False,
            duplicate_of=None,
            context_diagnostics=[],
            priority_assessment=p_assess,
            confidence_assessment=c_assess,
        )

        decision = evaluate_task_triage(item, DEFAULT_REVIEW_CONFIG)
        passed = (decision.status == exp_status)

        results.append({
            "trigger_name": name,
            "expected_status": exp_status.value,
            "actual_status": decision.status.value,
            "reason_codes": [c.value if hasattr(c, "value") else str(c) for c in decision.reason_codes],
            "passed": passed,
        })

    all_passed = all(r["passed"] for r in results)
    return {
        "status": "PASS" if all_passed else "FAIL",
        "total_triggers_tested": len(results),
        "results": results,
    }


def evaluate_review_engine() -> Dict[str, Any]:
    """Execute complete review evaluation suite."""
    es2002a_rev = evaluate_es2002a_review()
    triggers_rev = evaluate_review_triggers()

    return {
        "es2002a_review_evaluation": es2002a_rev,
        "trigger_coverage_evaluation": triggers_rev,
    }


if __name__ == "__main__":
    res = evaluate_review_engine()
    es = res["es2002a_review_evaluation"]
    print("=== REVIEW ENGINE EVALUATION ===")
    print(f"ES2002a Items: {es['total_tasks']}")
    print(f"Distribution: {es['review_status_distribution']}")
    print(f"Triggers Coverage: {res['trigger_coverage_evaluation']['status']} ({res['trigger_coverage_evaluation']['total_triggers_tested']} tested)")
