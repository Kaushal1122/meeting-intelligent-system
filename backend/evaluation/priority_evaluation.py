"""
Priority Intelligence Evaluation Module (Phase 11).
Evaluates real ES2002a dataset priority metrics, factor contribution consistency,
deadline-bearing tasks in real data, and 12 controlled behavioral synthetic test cases.
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
    ContextRichActionItem,
    ContextRichDecision,
    LocalizedDialogueContext,
    Member4ContextOutput,
    PriorityLevel,
    RelatedDecisionContext,
    TopicContextStatus,
)
from backend.member4.normalizer import normalize_member3_input
from backend.member4.context_engine import build_task_context
from backend.member4.priority_engine import (
    DEFAULT_CONFIG,
    infer_task_priorities,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def evaluate_es2002a_priority() -> Dict[str, Any]:
    """
    Evaluate priority engine behavior on real ES2002a data (32 action items).
    Verifies mathematical contribution sum, factor statistics, and distributions.
    """
    m3_file = PROCESSED_DIR / "ES2002a_member3_results.json"
    m2_file = PROCESSED_DIR / "ES2002a_member2_results.json"

    with open(m3_file, "r", encoding="utf-8") as f:
        m3_data = json.load(f)
    with open(m2_file, "r", encoding="utf-8") as f:
        m2_data = json.load(f)

    norm_output = normalize_member3_input(m3_data)
    ctx_output = build_task_context(norm_output, m2_data)
    pri_output = infer_task_priorities(ctx_output, config=DEFAULT_CONFIG)

    total_tasks = len(pri_output.action_items)
    high_count = 0
    med_count = 0
    low_count = 0

    scores = []
    sum_checks = []
    factor_stats = {
        "deadline_urgency": {"weight": 0.25, "raw_values": [], "contributions": []},
        "explicit_urgency": {"weight": 0.15, "raw_values": [], "contributions": []},
        "assignment_explicitness": {"weight": 0.15, "raw_values": [], "contributions": []},
        "dependency_blocker": {"weight": 0.15, "raw_values": [], "contributions": []},
        "decision_linkage": {"weight": 0.10, "raw_values": [], "contributions": []},
        "deliverable_specificity": {"weight": 0.10, "raw_values": [], "contributions": []},
        "context_quality": {"weight": 0.10, "raw_values": [], "contributions": []},
    }

    deadline_tasks = []

    for item in pri_output.action_items:
        p_assess = item.priority_assessment
        scores.append(p_assess.score)

        if p_assess.level == PriorityLevel.HIGH:
            high_count += 1
        elif p_assess.level == PriorityLevel.MEDIUM:
            med_count += 1
        else:
            low_count += 1

        # Check contribution sum vs score
        contrib_sum = sum(f.weighted_contribution for f in p_assess.factor_contributions)
        sum_match = abs(contrib_sum - p_assess.score) < 1e-3
        sum_checks.append({
            "item_id": item.item_id,
            "calculated_score": p_assess.score,
            "factor_sum": round(contrib_sum, 4),
            "matches": sum_match,
        })

        for f in p_assess.factor_contributions:
            fname = f.factor_name
            if fname in factor_stats:
                factor_stats[fname]["raw_values"].append(f.raw_value)
                factor_stats[fname]["contributions"].append(f.weighted_contribution)

        # Check for any deadline-bearing language
        is_dl = bool(item.deadline and item.deadline.strip())
        has_dl_text = any(
            w in item.task.lower()
            for w in ["tomorrow", "today", "friday", "monday", "week", "minutes", "hours", "before", "by"]
        )
        if is_dl or has_dl_text:
            dl_factor = next(f for f in p_assess.factor_contributions if f.factor_name == "deadline_urgency")
            deadline_tasks.append({
                "item_id": item.item_id,
                "task": item.task,
                "deadline": item.deadline,
                "deadline_urgency_raw": dl_factor.raw_value,
                "deadline_contribution": dl_factor.weighted_contribution,
                "priority_score": p_assess.score,
                "priority_level": p_assess.level.value if hasattr(p_assess.level, "value") else str(p_assess.level),
            })

    # Summary stats for factors
    factor_summary = {}
    for fname, d in factor_stats.items():
        raws = d["raw_values"]
        contribs = d["contributions"]
        factor_summary[fname] = {
            "weight": d["weight"],
            "raw_min": min(raws) if raws else 0.0,
            "raw_max": max(raws) if raws else 0.0,
            "raw_avg": round(sum(raws) / len(raws), 4) if raws else 0.0,
            "contrib_min": min(contribs) if contribs else 0.0,
            "contrib_max": max(contribs) if contribs else 0.0,
            "contrib_avg": round(sum(contribs) / len(contribs), 4) if contribs else 0.0,
        }

    sum_violations = [c for c in sum_checks if not c["matches"]]

    return {
        "dataset": "ES2002a",
        "total_items": total_tasks,
        "priority_distribution": {
            "HIGH": high_count,
            "MEDIUM": med_count,
            "LOW": low_count,
            "high_pct": round(high_count / total_tasks * 100, 1),
            "med_pct": round(med_count / total_tasks * 100, 1),
            "low_pct": round(low_count / total_tasks * 100, 1),
        },
        "score_statistics": {
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "mean_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        },
        "factor_analysis": factor_summary,
        "mathematical_consistency": {
            "total_checked": len(sum_checks),
            "all_factors_sum_to_score": len(sum_violations) == 0,
            "violations_count": len(sum_violations),
            "violations": sum_violations,
        },
        "deadline_bearing_tasks_in_es2002a": {
            "count": len(deadline_tasks),
            "tasks": deadline_tasks,
        },
    }


def evaluate_synthetic_priority_behaviors() -> Dict[str, Any]:
    """
    Run 12 controlled synthetic cases to evaluate engine behaviors across
    blockers, missing deadlines, explicit urgency, unassigned tasks, and conflict.
    """
    test_cases_defs = [
        # (name, task, dl, is_amb, resp, is_blk, mode)
        ("1. Blocker Task", "Fix blocking memory leak in audio subsystem", "tomorrow", False, "SPEAKER_01", True, "BLOCKER"),
        ("2. Near-term Clean", "Collaborate with SPEAKER_02 to test 16kHz audio driver", "tomorrow afternoon", False, "SPEAKER_02", False, "NORMAL"),
        ("3. End of Week", "Prepare slide deck for design review", "this Friday", False, "SPEAKER_03", False, "NORMAL"),
        ("4. Next Sprint", "Benchmark power consumption of remote control", "next week", False, "SPEAKER_04", False, "NORMAL"),
        ("5. No Deadline Assigned", "Document API interface for audio codec", None, False, "SPEAKER_01", False, "NORMAL"),
        ("6. Ambiguous Deadline", "Investigate alternative DSP chips", "asap", True, "SPEAKER_03", False, "NORMAL"),
        ("7. Urgent Crisis Task", "Fix critical production crash immediately", "today", False, "SPEAKER_01", False, "URGENT"),
        ("8. Unassigned Task", "Review project schedule and assign owners", "tomorrow", False, None, False, "UNASSIGNED"),
        ("9. Weak Context Task", "Discuss remote control casing material", "tomorrow", False, "SPEAKER_03", False, "WEAK_CONTEXT"),
        ("10. Conflict Topic Task", "Select mascot design based on meeting consensus", "this Friday", False, "SPEAKER_01", False, "CONFLICT"),
        ("11. Routine Admin Task", "Archive past meeting audio recordings", None, False, "SPEAKER_04", False, "NORMAL"),
        ("12. High Blocker No DL", "Refactor core audio bus architecture blocking all teams", None, False, "SPEAKER_01", True, "BLOCKER"),
    ]

    items = []
    for idx, (name, task, dl, is_amb, resp, is_blk, mode) in enumerate(test_cases_defs):
        status = TopicContextStatus.RESOLVED
        if mode == "WEAK_CONTEXT":
            status = TopicContextStatus.PARTIALLY_RESOLVED

        task_desc = task
        if mode == "BLOCKER":
            task_desc += " This is a critical blocker for release."
        elif mode == "URGENT":
            task_desc += " This is urgent and critical."

        speakers = ["SPEAKER_01", "SPEAKER_03"]
        if resp and resp not in speakers:
            speakers.append(resp)

        context = LocalizedDialogueContext(
            window_text=f"[01:00] SPEAKER_01: {task_desc}",
            segment_ids=[201, 202],
            trigger_segment_id=201,
            speakers=speakers,
            start=60.0,
            end=65.0,
        )

        decisions = []
        if mode == "CONFLICT":
            decisions = [
                RelatedDecisionContext(decision_id="d1", topic_reference=20, decision="Use SQLite."),
                RelatedDecisionContext(decision_id="d2", topic_reference=20, decision="Use PostgreSQL."),
            ]

        item = ContextRichActionItem(
            item_id=f"synth_p_{idx:02d}",
            task=task_desc,
            responsible_person=resp,
            speaker_id=resp if resp else None,
            display_name=resp,
            name_source="diarization_fallback" if resp else None,
            is_unassigned=(resp is None),
            deadline=dl,
            is_ambiguous_deadline=is_amb,
            topic_reference=20,
            context_status=status,
            topic_summary="Technical development discussion.",
            topic_speakers=speakers,
            localized_context=context,
            context_start=60.0,
            context_end=65.0,
            related_decisions=decisions,
            deadline_context_snippet=dl,
            source_priority=None,
            source_confidence_score=None,
            is_duplicate=False,
            duplicate_of=None,
            context_diagnostics=[],
        )
        items.append(item)

    ctx_output = Member4ContextOutput(
        meeting_id="synth_priority_suite",
        processing_stage="member_4_context_enriched",
        total_action_items=len(items),
        total_decisions=0,
        resolved_topics_count=len(items),
        partially_resolved_count=0,
        unresolved_topics_count=0,
        missing_topics_count=0,
        items_with_localized_context=len(items),
        items_with_related_decisions=0,
        action_items=items,
        key_decisions=[],
        diagnostics=[],
    )

    pri_output = infer_task_priorities(ctx_output, config=DEFAULT_CONFIG)
    results = []

    for idx, (name, task, dl, is_amb, resp, is_blk, mode) in enumerate(test_cases_defs):
        p_item = pri_output.action_items[idx]
        p_assess = p_item.priority_assessment

        results.append({
            "test_name": name,
            "task": task,
            "deadline": dl,
            "priority_score": p_assess.score,
            "priority_level": p_assess.level.value if hasattr(p_assess.level, "value") else str(p_assess.level),
            "factors": {f.factor_name: f.weighted_contribution for f in p_assess.factor_contributions},
        })

    return {"total_cases": len(results), "cases": results}


def evaluate_priority_engine() -> Dict[str, Any]:
    """Execute complete priority evaluation suite."""
    real_data_eval = evaluate_es2002a_priority()
    synthetic_eval = evaluate_synthetic_priority_behaviors()
    return {
        "es2002a_priority_evaluation": real_data_eval,
        "synthetic_behavior_evaluation": synthetic_eval,
    }


if __name__ == "__main__":
    res = evaluate_priority_engine()
    es = res["es2002a_priority_evaluation"]
    print("=== PRIORITY ENGINE EVALUATION ===")
    print(f"ES2002a Items: {es['total_items']}")
    print(f"Distribution: {es['priority_distribution']}")
    print(f"Mathematical Consistency: {es['mathematical_consistency']['all_factors_sum_to_score']}")
    print(f"Synthetic Cases Evaluated: {res['synthetic_behavior_evaluation']['total_cases']}")
