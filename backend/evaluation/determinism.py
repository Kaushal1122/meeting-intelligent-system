"""
Determinism and Stability Evaluation Module (Phase 11).
Verifies that the entire Member 4 pipeline produces 100% bit-for-bit identical,
zero-drift results across repeated runs on the reference ES2002a dataset.
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


def evaluate_determinism(num_runs: int = 5) -> Dict[str, Any]:
    """
    Run ES2002a through the full Member 4 pipeline num_runs times
    and verify zero drift across all outputs, scores, decisions,
    explanations, and role projections.
    """
    m3_file = PROCESSED_DIR / "ES2002a_member3_results.json"
    m2_file = PROCESSED_DIR / "ES2002a_member2_results.json"

    with open(m3_file, "r", encoding="utf-8") as f:
        m3_data = json.load(f)
    with open(m2_file, "r", encoding="utf-8") as f:
        m2_data = json.load(f)

    roles = [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]

    runs_data = []

    for run_idx in range(num_runs):
        # Deepcopy or reload to ensure clean slate
        m3_copy = json.loads(json.dumps(m3_data))
        m2_copy = json.loads(json.dumps(m2_data))

        explained = explain_meeting_triage(m3_copy, member2_data=m2_copy)

        role_views = {}
        for role in roles:
            role_views[role.value] = personalize_meeting_view(explained, role=role)

        # Snapshot of all items
        item_snapshots = {}
        for item in explained.action_items:
            evidence_serialized = [
                ev.model_dump() if hasattr(ev, "model_dump") else str(ev)
                for ev in (item.explanation.evidence_traces if item.explanation else [])
            ]
            item_snapshots[item.item_id] = {
                "priority_score": item.priority_assessment.score,
                "priority_level": item.priority_assessment.level.value if hasattr(item.priority_assessment.level, "value") else str(item.priority_assessment.level),
                "confidence_score": item.confidence_assessment.score,
                "confidence_level": item.confidence_assessment.level.value if hasattr(item.confidence_assessment.level, "value") else str(item.confidence_assessment.level),
                "review_status": item.review_decision.status.value if hasattr(item.review_decision.status, "value") else str(item.review_decision.status),
                "review_reasons": [r.value if hasattr(r, "value") else str(r) for r in (item.review_decision.reason_codes or [])],
                "explanation_narrative": item.explanation.unified_explanation if item.explanation else "",
                "evidence": evidence_serialized,
            }

        # Snapshot of role projections
        role_snapshots = {}
        for role_name, view in role_views.items():
            role_snapshots[role_name] = [
                {
                    "item_id": p_item.item_id,
                    "priority_score": p_item.priority_score,
                    "confidence_score": p_item.confidence_score,
                    "review_status": p_item.review_status.value if hasattr(p_item.review_status, "value") else str(p_item.review_status),
                }
                for p_item in view.action_items
            ]

        runs_data.append({
            "items": item_snapshots,
            "roles": role_snapshots,
        })

    # Compare Run 0 against all subsequent runs
    baseline = runs_data[0]
    baseline_items = baseline["items"]
    baseline_roles = baseline["roles"]

    priority_score_max_drift = 0.0
    confidence_score_max_drift = 0.0
    priority_level_flips = 0
    confidence_level_flips = 0
    review_status_flips = 0
    review_reason_flips = 0
    explanation_drifts = 0
    evidence_drifts = 0
    personalization_order_drifts = 0

    violations = []

    for run_idx in range(1, num_runs):
        current = runs_data[run_idx]
        curr_items = current["items"]
        curr_roles = current["roles"]

        # Item-by-item verification
        for item_id, base_snap in baseline_items.items():
            if item_id not in curr_items:
                violations.append(f"Run {run_idx}: Missing item {item_id}")
                continue

            curr_snap = curr_items[item_id]

            # Numerical drift
            p_drift = abs(base_snap["priority_score"] - curr_snap["priority_score"])
            if p_drift > priority_score_max_drift:
                priority_score_max_drift = p_drift

            c_drift = abs(base_snap["confidence_score"] - curr_snap["confidence_score"])
            if c_drift > confidence_score_max_drift:
                confidence_score_max_drift = c_drift

            # Categorical drift
            if base_snap["priority_level"] != curr_snap["priority_level"]:
                priority_level_flips += 1
                violations.append(f"Run {run_idx}, Item {item_id}: Priority level flip ({base_snap['priority_level']} -> {curr_snap['priority_level']})")

            if base_snap["confidence_level"] != curr_snap["confidence_level"]:
                confidence_level_flips += 1
                violations.append(f"Run {run_idx}, Item {item_id}: Confidence level flip ({base_snap['confidence_level']} -> {curr_snap['confidence_level']})")

            if base_snap["review_status"] != curr_snap["review_status"]:
                review_status_flips += 1
                violations.append(f"Run {run_idx}, Item {item_id}: Review status flip ({base_snap['review_status']} -> {curr_snap['review_status']})")

            if sorted(base_snap["review_reasons"]) != sorted(curr_snap["review_reasons"]):
                review_reason_flips += 1
                violations.append(f"Run {run_idx}, Item {item_id}: Review reasons mismatch")

            if base_snap["explanation_narrative"] != curr_snap["explanation_narrative"]:
                explanation_drifts += 1
                violations.append(f"Run {run_idx}, Item {item_id}: Explanation narrative text drift")

            if base_snap["evidence"] != curr_snap["evidence"]:
                evidence_drifts += 1
                violations.append(f"Run {run_idx}, Item {item_id}: Evidence drift")

        # Role projection verification
        for role_name, base_role_items in baseline_roles.items():
            curr_role_items = curr_roles.get(role_name, [])
            if len(base_role_items) != len(curr_role_items):
                personalization_order_drifts += 1
                violations.append(f"Run {run_idx}, Role {role_name}: Item count mismatch")
                continue

            for idx, (b_item, c_item) in enumerate(zip(base_role_items, curr_role_items)):
                if b_item["item_id"] != c_item["item_id"]:
                    personalization_order_drifts += 1
                    violations.append(f"Run {run_idx}, Role {role_name}, Index {idx}: Ordering flip ({b_item['item_id']} vs {c_item['item_id']})")

    determinism_pass = (
        priority_score_max_drift == 0.0 and
        confidence_score_max_drift == 0.0 and
        priority_level_flips == 0 and
        confidence_level_flips == 0 and
        review_status_flips == 0 and
        review_reason_flips == 0 and
        explanation_drifts == 0 and
        evidence_drifts == 0 and
        personalization_order_drifts == 0
    )

    return {
        "num_runs": num_runs,
        "items_per_run": len(baseline_items),
        "priority_score_max_drift": priority_score_max_drift,
        "confidence_score_max_drift": confidence_score_max_drift,
        "priority_level_flips": priority_level_flips,
        "confidence_level_flips": confidence_level_flips,
        "review_status_flips": review_status_flips,
        "review_reason_flips": review_reason_flips,
        "explanation_drifts": explanation_drifts,
        "evidence_drifts": evidence_drifts,
        "personalization_order_drifts": personalization_order_drifts,
        "determinism_pass": determinism_pass,
        "violations": violations,
    }


if __name__ == "__main__":
    result = evaluate_determinism(5)
    print("=== DETERMINISM EVALUATION ===")
    print(f"Runs tested: {result['num_runs']}")
    print(f"Items per run: {result['items_per_run']}")
    print(f"Max priority score drift: {result['priority_score_max_drift']:.6f}")
    print(f"Max confidence score drift: {result['confidence_score_max_drift']:.6f}")
    print(f"Level flips: {result['priority_level_flips'] + result['confidence_level_flips']}")
    print(f"Review flips: {result['review_status_flips']}")
    print(f"Explanation drifts: {result['explanation_drifts']}")
    print(f"Determinism Pass: {result['determinism_pass']}")
