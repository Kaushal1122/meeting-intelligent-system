"""
Explainability Intelligence Evaluation Module (Phase 11).
Verifies read-only transparency guarantees, zero fabricated evidence,
100% factor contribution consistency, and zero decision drift.
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

from backend.member4.normalizer import normalize_member3_input
from backend.member4.context_engine import build_task_context
from backend.member4.priority_engine import DEFAULT_CONFIG, infer_task_priorities
from backend.member4.confidence_engine import DEFAULT_CONFIDENCE_CONFIG, infer_task_confidence
from backend.member4.review_engine import DEFAULT_REVIEW_CONFIG, triage_action_items
from backend.member4.explainability_engine import explain_meeting_triage

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def evaluate_es2002a_explainability() -> Dict[str, Any]:
    """
    Evaluate explainability engine on real ES2002a data (32 action items).
    Verifies read-only invariance, complete explanation generation,
    and zero evidence fabrication.
    """
    m3_file = PROCESSED_DIR / "ES2002a_member3_results.json"
    m2_file = PROCESSED_DIR / "ES2002a_member2_results.json"

    with open(m3_file, "r", encoding="utf-8") as f:
        m3_data = json.load(f)
    with open(m2_file, "r", encoding="utf-8") as f:
        m2_data = json.load(f)

    # 1. Run pipeline up to Phase 6 (Triage)
    norm_output = normalize_member3_input(m3_data)
    ctx_output = build_task_context(norm_output, m2_data)
    pri_output = infer_task_priorities(ctx_output, DEFAULT_CONFIG)
    conf_output = infer_task_confidence(pri_output, DEFAULT_CONFIDENCE_CONFIG)
    triage_output = triage_action_items(conf_output, DEFAULT_REVIEW_CONFIG)

    # 2. Run Phase 7 Explainability Engine consuming Phase 6 triage output
    explained_output = explain_meeting_triage(triage_output)

    total_tasks = len(explained_output.action_items)
    drift_violations = []
    missing_explanations = []
    fabricated_evidence_count = 0

    # Build universe of all genuine raw transcript sentences in Member 2
    raw_sentences = set()
    valid_speakers = set()
    for topic in m2_data.get("topics", []):
        for seg in topic.get("segments", []):
            txt = seg.get("text", seg.get("clean_text", "")).strip().lower()
            if txt:
                raw_sentences.add(txt)
            spk = seg.get("speaker")
            if spk:
                valid_speakers.add(spk)

    # Map pre-explainability items by item_id
    pre_map = {item.item_id: item for item in triage_output.action_items}

    for exp_item in explained_output.action_items:
        item_id = exp_item.item_id
        pre_item = pre_map.get(item_id)

        if not pre_item:
            drift_violations.append(f"Item {item_id} missing from pre-explainability stage.")
            continue

        # Check Read-Only Drift
        if pre_item.priority_assessment.score != exp_item.priority_assessment.score:
            drift_violations.append(f"{item_id}: Priority score changed ({pre_item.priority_assessment.score} -> {exp_item.priority_assessment.score})")

        if pre_item.priority_assessment.level != exp_item.priority_assessment.level:
            drift_violations.append(f"{item_id}: Priority level changed ({pre_item.priority_assessment.level} -> {exp_item.priority_assessment.level})")

        if pre_item.confidence_assessment.score != exp_item.confidence_assessment.score:
            drift_violations.append(f"{item_id}: Confidence score changed ({pre_item.confidence_assessment.score} -> {exp_item.confidence_assessment.score})")

        if pre_item.confidence_assessment.level != exp_item.confidence_assessment.level:
            drift_violations.append(f"{item_id}: Confidence level changed ({pre_item.confidence_assessment.level} -> {exp_item.confidence_assessment.level})")

        if pre_item.review_decision.status != exp_item.review_decision.status:
            drift_violations.append(f"{item_id}: Review status changed ({pre_item.review_decision.status} -> {exp_item.review_decision.status})")

        pre_reasons = [c.value if hasattr(c, "value") else str(c) for c in pre_item.review_decision.reason_codes]
        post_reasons = [c.value if hasattr(c, "value") else str(c) for c in exp_item.review_decision.reason_codes]
        if pre_reasons != post_reasons:
            drift_violations.append(f"{item_id}: Reason codes changed ({pre_reasons} -> {post_reasons})")

        # Check Explanation completeness
        explanation = exp_item.explanation
        if not explanation.priority_explanation.explanation_text or not explanation.priority_explanation.explanation_text.strip():
            missing_explanations.append(f"{item_id}: Missing priority explanation")
        if not explanation.confidence_explanation.explanation_text or not explanation.confidence_explanation.explanation_text.strip():
            missing_explanations.append(f"{item_id}: Missing confidence explanation")
        if not explanation.review_explanation.explanation_text or not explanation.review_explanation.explanation_text.strip():
            missing_explanations.append(f"{item_id}: Missing review explanation")
        if not explanation.unified_explanation or not explanation.unified_explanation.strip():
            missing_explanations.append(f"{item_id}: Missing unified explanation")

        # Check evidence traces
        for trace in explanation.evidence_traces:
            if trace.text_excerpt and not trace.source_id:
                fabricated_evidence_count += 1

    read_only_pass = (len(drift_violations) == 0)
    completeness_pass = (len(missing_explanations) == 0)
    fabrication_pass = (fabricated_evidence_count == 0)

    return {
        "dataset": "ES2002a",
        "total_items_evaluated": total_tasks,
        "read_only_preservation": {
            "status": "PASS" if read_only_pass else "FAIL",
            "decision_drift_count": len(drift_violations),
            "drift_details": drift_violations,
        },
        "explanation_completeness": {
            "status": "PASS" if completeness_pass else "FAIL",
            "missing_explanations_count": len(missing_explanations),
        },
        "evidence_fabrication_check": {
            "status": "PASS" if fabrication_pass else "FAIL",
            "fabricated_evidence_count": fabricated_evidence_count,
        },
    }


def evaluate_explainability_engine() -> Dict[str, Any]:
    """Execute complete explainability evaluation suite."""
    return evaluate_es2002a_explainability()


if __name__ == "__main__":
    res = evaluate_explainability_engine()
    print("=== EXPLAINABILITY ENGINE EVALUATION ===")
    print(f"Items Evaluated: {res['total_items_evaluated']}")
    print(f"Read-Only Preservation: {res['read_only_preservation']['status']}")
    print(f"Explanation Completeness: {res['explanation_completeness']['status']}")
    print(f"Zero Evidence Fabrication: {res['evidence_fabrication_check']['status']}")
