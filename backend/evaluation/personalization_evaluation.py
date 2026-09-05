"""
Personalization Intelligence Evaluation Module (Phase 11).
Verifies that persona/role projections (MANAGER, DEVELOPER, INTERN, DEFAULT)
strictly maintain 100% canonical value invariance with zero decision drift.
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

from backend.member4.schemas import UserRole
from backend.member4.explainability_engine import explain_meeting_triage
from backend.member4.personalization_engine import personalize_meeting_view

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def evaluate_es2002a_personalization() -> Dict[str, Any]:
    """
    Evaluate personalization projections across all 4 roles on real ES2002a data.
    Verifies that item attributes, scores, levels, reasons, and decisions
    are 100% invariant across all role views.
    """
    m3_file = PROCESSED_DIR / "ES2002a_member3_results.json"
    m2_file = PROCESSED_DIR / "ES2002a_member2_results.json"

    with open(m3_file, "r", encoding="utf-8") as f:
        m3_data = json.load(f)
    with open(m2_file, "r", encoding="utf-8") as f:
        m2_data = json.load(f)

    # 1. Canonical explained meeting output
    canonical_output = explain_meeting_triage(m3_data, member2_data=m2_data)
    canonical_items_map = {item.item_id: item for item in canonical_output.action_items}

    roles = [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]
    role_results = {}
    total_violations = []

    for role in roles:
        view = personalize_meeting_view(canonical_output, role=role)

        item_count_matches = (view.total_canonical_items == len(canonical_items_map))
        if not item_count_matches:
            total_violations.append(f"Role {role.value}: Item count mismatch ({view.total_canonical_items} vs {len(canonical_items_map)})")

        role_violations = []

        for p_item in view.action_items:
            c_item = canonical_items_map.get(p_item.item_id)
            if not c_item:
                role_violations.append(f"Item {p_item.item_id} not found in canonical output")
                continue

            # Check mathematical and categorical invariance
            if p_item.priority_score != c_item.priority_assessment.score:
                role_violations.append(f"{p_item.item_id}: Priority score drifted ({p_item.priority_score} vs {c_item.priority_assessment.score})")

            if p_item.priority_level != c_item.priority_assessment.level:
                role_violations.append(f"{p_item.item_id}: Priority level drifted")

            if p_item.confidence_score != c_item.confidence_assessment.score:
                role_violations.append(f"{p_item.item_id}: Confidence score drifted")

            if p_item.confidence_level != c_item.confidence_assessment.level:
                role_violations.append(f"{p_item.item_id}: Confidence level drifted")

            if p_item.review_status != c_item.review_decision.status:
                role_violations.append(f"{p_item.item_id}: Review status drifted")

            c_reasons = [r.value if hasattr(r, "value") else str(r) for r in c_item.review_decision.reason_codes]
            p_reasons = [r.value if hasattr(r, "value") else str(r) for r in p_item.review_reason_codes]
            if p_reasons != c_reasons:
                role_violations.append(f"{p_item.item_id}: Reason codes drifted")

            if p_item.task != c_item.task:
                role_violations.append(f"{p_item.item_id}: Task text drifted")

            if p_item.responsible_person != c_item.responsible_person:
                role_violations.append(f"{p_item.item_id}: Responsible person drifted")

            if p_item.deadline != c_item.deadline:
                role_violations.append(f"{p_item.item_id}: Deadline drifted")

        total_violations.extend(role_violations)

        role_results[role.value] = {
            "total_items": len(view.action_items),
            "summary_headline": view.summary_headline,
            "violations_count": len(role_violations),
            "invariance_passed": (len(role_violations) == 0),
        }

    all_passed = (len(total_violations) == 0)

    return {
        "dataset": "ES2002a",
        "roles_evaluated": [r.value for r in roles],
        "all_invariance_passed": all_passed,
        "total_violations_count": len(total_violations),
        "violations": total_violations,
        "role_details": role_results,
    }


def evaluate_personalization_engine() -> Dict[str, Any]:
    """Execute complete personalization evaluation suite."""
    return evaluate_es2002a_personalization()


if __name__ == "__main__":
    res = evaluate_personalization_engine()
    print("=== PERSONALIZATION ENGINE EVALUATION ===")
    print(f"Roles Evaluated: {res['roles_evaluated']}")
    print(f"All Invariance Passed: {res['all_invariance_passed']}")
    print(f"Total Violations: {res['total_violations_count']}")
