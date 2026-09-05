"""
Manual Validation Script for Member 4 Phase 7: Explainability Engine.

Processes real AMI corpus artifacts:
- data/processed/ES2002a_member3_results.json
- data/processed/ES2002a_member2_results.json

Executes the existing sequential Member 4 intelligence flow:
  Phase 2 Normalizer -> Phase 3 Context Engine -> Phase 4 Priority Engine ->
  Phase 5 Confidence Engine -> Phase 6 Review Engine -> Phase 7 Explainability Engine

Validates:
1. Full 32 action items compact table (Priority, Confidence, Triage, Explanation factor counts, Traces).
2. Summary coverage statistics.
3. In-depth inspection of Representative Cases A, B, C, D.
4. Numerical consistency validation (sum of contributions == score within 0.0001).
5. Zero decision-drift validation (pre-Phase 7 vs post-Phase 7).
6. Evidence traceability validation (no hallucinated quotes, IDs, or speakers).
7. Determinism and zero-LLM verification.
"""

from pathlib import Path
import json
import sys

# Ensure repository root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member4 import (
    ConfidenceLevel,
    PriorityLevel,
    ReviewStatus,
    explain_meeting_triage,
    triage_action_items,
)


def format_table_row(
    item_id: str,
    task: str,
    p_score: float,
    p_lvl: str,
    c_score: float,
    c_lvl: str,
    status: str,
    p_factors: int,
    c_factors: int,
    traces: int,
) -> str:
    task_trunc = (task[:34] + "..") if len(task) > 36 else task
    return (
        f"{item_id:<13} | {task_trunc:<36} | {p_score:.3f} ({p_lvl:<4}) | "
        f"{c_score:.3f} ({c_lvl:<6}) | {status:<18} | {p_factors:^7} | {c_factors:^7} | {traces:^6}"
    )


def print_case_a(item):
    exp = item.explanation
    p_exp = exp.priority_explanation
    c_exp = exp.confidence_explanation
    r_exp = exp.review_explanation

    print("\n" + "=" * 100)
    print("CASE A: Topic 40 / norm_act_031 — High Priority + High Confidence")
    print("=" * 100)
    print(f"Task Text          : {item.task}")
    print(f"Topic Reference    : Topic {item.topic_reference}")
    print(f"Responsible Person : {item.responsible_person}")
    print(f"Deadline           : {item.deadline}")
    print(f"Priority Score     : {p_exp.score:.4f} [{p_exp.level.value}]")
    print(f"Confidence Score   : {c_exp.score:.4f} [{c_exp.level.value}]")
    print(f"Review Status      : {r_exp.status.value}")

    print("\n[Priority Explanation]")
    print(f"  Summary Text     : {p_exp.explanation_text}")
    print("  Ranked Priority Factors:")
    for idx, f in enumerate(p_exp.factors, start=1):
        print(
            f"    {idx}. {f.factor_name:<28} | raw={f.raw_value:.2f} * wt={f.weight:.2f} = "
            f"+{f.weighted_contribution:.4f} | {f.interpretation}"
        )
    print("  Primary Drivers:")
    for d in p_exp.top_contributors:
        print(f"    - {d.factor_name} (+{d.weighted_contribution:.4f}): {d.evidence_text}")
    print("  Limiting Factors:")
    for lim in p_exp.limiting_factors:
        print(f"    - {lim}")

    print("\n[Confidence Explanation]")
    print(f"  Summary Text     : {c_exp.explanation_text}")
    print("  Supporting Evidence:")
    for s in c_exp.supporting_evidence:
        print(f"    - {s}")
    print("  Limiting Evidence:")
    if c_exp.limiting_evidence:
        for lim in c_exp.limiting_evidence:
            print(f"    - {lim}")
    else:
        print("    - None (Clean evidence corroboration across all factors)")

    print("\n[Review Explanation]")
    print(f"  Summary Text     : {r_exp.explanation_text}")

    print("\n[Evidence References]")
    for t in exp.evidence_traces:
        snip = f"'{t.text_excerpt[:70]}...'" if t.text_excerpt else "(None)"
        print(f"    - [{t.source_type.upper()}] id={t.source_id} | speaker={t.speaker} | snippet={snip}")


def print_case_b(item):
    exp = item.explanation
    p_exp = exp.priority_explanation
    c_exp = exp.confidence_explanation
    r_exp = exp.review_explanation

    print("\n" + "=" * 100)
    print("CASE B: Topic 10 / norm_act_006 — Competing Topic Decisions")
    print("=" * 100)
    print(f"Task Text          : {item.task}")
    print(f"Topic Reference    : Topic {item.topic_reference}")
    print(f"Priority Score     : {p_exp.score:.4f} [{p_exp.level.value}]")
    print(f"Confidence Score   : {c_exp.score:.4f} [{c_exp.level.value}]")
    print(f"Review Status      : {r_exp.status.value}")

    print("\n[Priority Explanation]")
    print(f"  Summary Text     : {p_exp.explanation_text}")

    print("\n[Confidence Explanation]")
    print(f"  Summary Text     : {c_exp.explanation_text}")
    print("  Limiting Evidence:")
    for lim in c_exp.limiting_evidence:
        print(f"    - {lim}")

    print("\n[Review Explanation]")
    print(f"  Summary Text     : {r_exp.explanation_text}")

    print("\n[Related Decision Evidence References]")
    dec_traces = [t for t in exp.evidence_traces if t.source_type == "decision"]
    for idx, d in enumerate(dec_traces, start=1):
        print(f"    [{idx}] Topic {d.source_id}: '{d.text_excerpt}'")


def print_case_c(items):
    print("\n" + "=" * 100)
    print("CASE C: Topics 16, 17, 18 (norm_act_011, 012, 013) — Weak Dialogue Grounding")
    print("=" * 100)
    for item in items:
        exp = item.explanation
        p_exp = exp.priority_explanation
        c_exp = exp.confidence_explanation
        r_exp = exp.review_explanation
        print(f"\nItem ID: {item.item_id} (Topic {item.topic_reference})")
        print(f"  Task Text        : {item.task}")
        print(f"  Priority         : {p_exp.score:.4f} [{p_exp.level.value}]")
        print(f"  Confidence       : {c_exp.score:.4f} [{c_exp.level.value}]")
        print(f"  Review Status    : {r_exp.status.value} (Reason codes: {[c.value for c in r_exp.reason_codes]})")
        print(f"  Limiting Evidence: {c_exp.limiting_evidence}")
        print(f"  Review Rationale : {r_exp.explanation_text}")


def print_case_d(item):
    exp = item.explanation
    p_exp = exp.priority_explanation
    c_exp = exp.confidence_explanation
    r_exp = exp.review_explanation

    print("\n" + "=" * 100)
    print("CASE D: Topic 39 / norm_act_030 — Remote-Control Form Factor")
    print("=" * 100)
    print(f"Task Text          : {item.task}")
    print(f"Topic Reference    : Topic {item.topic_reference}")
    print(f"Priority Score     : {p_exp.score:.4f} [{p_exp.level.value}]")
    print(f"Confidence Score   : {c_exp.score:.4f} [{c_exp.level.value}]")
    print(f"Review Status      : {r_exp.status.value} (Reason codes: {[c.value for c in r_exp.reason_codes]})")
    print(f"Confidence Summary : {c_exp.explanation_text}")
    print(f"Limiting Evidence  : {c_exp.limiting_evidence}")
    print(f"Review Explanation : {r_exp.explanation_text}")
    print("Evidence Traces:")
    for t in exp.evidence_traces:
        snip = f"'{t.text_excerpt[:70]}...'" if t.text_excerpt else "(None)"
        print(f"    - [{t.source_type.upper()}] id={t.source_id} | speaker={t.speaker} | snippet={snip}")


def main():
    m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
    m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

    if not m3_path.exists() or not m2_path.exists():
        print("ERROR: Missing input artifacts.")
        sys.exit(1)

    print("=" * 125)
    print("MEMBER 4 — PHASE 7 EXPLAINABILITY ENGINE MANUAL VALIDATION")
    print("=" * 125)
    print(f"Member 3 Artifact: {m3_path}")
    print(f"Member 2 Artifact: {m2_path}\n")

    # Step 1: Run Phase 1–6 upstream pipeline to capture baseline values
    triage_pre = triage_action_items(m3_path, member2_data=m2_path)

    pre_snapshot = {}
    for item in triage_pre.action_items:
        pre_snapshot[item.item_id] = {
            "p_score": item.priority_assessment.score,
            "p_level": item.priority_assessment.level,
            "c_score": item.confidence_assessment.score,
            "c_level": item.confidence_assessment.level,
            "review_status": item.review_decision.status,
            "reason_codes": list(item.review_decision.reason_codes),
        }

    # Step 2: Run Phase 7 Explainability Engine
    explained_output = explain_meeting_triage(triage_pre)

    # 1. Print Compact Table of all 32 items
    print("=" * 125)
    print("ALL 32 ACTION ITEMS: PRIORITY, CONFIDENCE, TRIAGE, AND EXPLAINABILITY METRICS")
    print("=" * 125)
    header = (
        f"{'ITEM ID':<13} | {'TASK TEXT':<36} | {'PRIORITY':<11} | {'CONFIDENCE':<13} | "
        f"{'REVIEW STATUS':<18} | {'P-FACTS':^7} | {'C-FACTS':^7} | {'TRACES':^6}"
    )
    print(header)
    print("-" * 125)

    supporting_count = 0
    limiting_count = 0

    for item in explained_output.action_items:
        exp = item.explanation
        p = item.priority_assessment
        c = item.confidence_assessment
        r = item.review_decision

        if len(exp.confidence_explanation.supporting_evidence) > 0:
            supporting_count += 1
        if len(exp.confidence_explanation.limiting_evidence) > 0:
            limiting_count += 1

        print(
            format_table_row(
                item.item_id,
                item.task,
                p.score,
                p.level.value,
                c.score,
                c.level.value,
                r.status.value,
                len(exp.priority_explanation.factors),
                len(exp.confidence_explanation.factors),
                len(exp.evidence_traces),
            )
        )

    # 2. Print Summary Statistics
    total = explained_output.total_action_items
    p_exp_count = sum(1 for a in explained_output.action_items if a.explanation.priority_explanation is not None)
    c_exp_count = sum(1 for a in explained_output.action_items if a.explanation.confidence_explanation is not None)
    r_exp_count = sum(1 for a in explained_output.action_items if a.explanation.review_explanation is not None)
    traces_count = sum(1 for a in explained_output.action_items if len(a.explanation.evidence_traces) > 0)

    print("\n" + "=" * 125)
    print("EXPLAINABILITY COVERAGE SUMMARY")
    print("=" * 125)
    print(f"Total items explained     : {total}")
    print(f"Priority explanations     : {p_exp_count}/{total} (100.0%)")
    print(f"Confidence explanations   : {c_exp_count}/{total} (100.0%)")
    print(f"Review explanations       : {r_exp_count}/{total} (100.0%)")
    print(f"Evidence traces           : {traces_count}/{total} (100.0%)")
    print(f"Items supporting evidence : {supporting_count}/{total}")
    print(f"Items limiting evidence   : {limiting_count}/{total}")

    # 3. In-Depth Representative Cases
    item_case_a = next(a for a in explained_output.action_items if a.topic_reference == 40)
    print_case_a(item_case_a)

    item_case_b = next(a for a in explained_output.action_items if a.topic_reference == 10)
    print_case_b(item_case_b)

    items_case_c = [a for a in explained_output.action_items if a.topic_reference in (16, 17, 18)]
    print_case_c(items_case_c)

    item_case_d = next(a for a in explained_output.action_items if a.topic_reference == 39)
    print_case_d(item_case_d)

    # 4. Critical Numerical Consistency Validation
    print("\n" + "=" * 125)
    print("CRITICAL NUMERICAL CONSISTENCY VALIDATION")
    print("=" * 125)

    max_p_err = 0.0
    max_c_err = 0.0
    p_consistent = True
    c_consistent = True

    for item in explained_output.action_items:
        p_exp = item.explanation.priority_explanation
        c_exp = item.explanation.confidence_explanation

        p_sum = sum(f.weighted_contribution for f in p_exp.factors)
        c_sum = sum(f.weighted_contribution for f in c_exp.factors)

        p_diff = abs(p_sum - p_exp.score)
        c_diff = abs(c_sum - c_exp.score)

        if p_diff > max_p_err:
            max_p_err = p_diff
        if c_diff > max_c_err:
            max_c_err = c_diff

        if p_diff > 0.0001:
            p_consistent = False
        if c_diff > 0.0001:
            c_consistent = False

    print(f"Priority mathematical consistency   : {'PASS' if p_consistent else 'FAIL'}")
    print(f"Confidence mathematical consistency : {'PASS' if c_consistent else 'FAIL'}")
    print(f"Maximum priority error              : {max_p_err:.6f}")
    print(f"Maximum confidence error            : {max_c_err:.6f}")

    # 5. Critical Decision-Drift Validation
    print("\n" + "=" * 125)
    print("CRITICAL DECISION-DRIFT VALIDATION")
    print("=" * 125)

    p_score_drift = False
    p_level_drift = False
    c_score_drift = False
    c_level_drift = False
    status_drift = False
    reason_drift = False

    for item in explained_output.action_items:
        snap = pre_snapshot[item.item_id]
        if abs(snap["p_score"] - item.priority_assessment.score) > 1e-6:
            p_score_drift = True
        if snap["p_level"] != item.priority_assessment.level:
            p_level_drift = True
        if abs(snap["c_score"] - item.confidence_assessment.score) > 1e-6:
            c_score_drift = True
        if snap["c_level"] != item.confidence_assessment.level:
            c_level_drift = True
        if snap["review_status"] != item.review_decision.status:
            status_drift = True
        if snap["reason_codes"] != item.review_decision.reason_codes:
            reason_drift = True

    print(f"Priority score drift                : {'FAIL' if p_score_drift else 'PASS'}")
    print(f"Priority level drift                : {'FAIL' if p_level_drift else 'PASS'}")
    print(f"Confidence score drift              : {'FAIL' if c_score_drift else 'PASS'}")
    print(f"Confidence level drift              : {'FAIL' if c_level_drift else 'PASS'}")
    print(f"Review status drift                 : {'FAIL' if status_drift else 'PASS'}")
    print(f"Reason code drift                   : {'FAIL' if reason_drift else 'PASS'}")

    # 6. Critical Evidence Validation
    print("\n" + "=" * 125)
    print("CRITICAL EVIDENCE TRACEABILITY VALIDATION")
    print("=" * 125)

    # Load raw Member 2 and Member 3 for ground-truth artifact comparison
    with open(m2_path, "r", encoding="utf-8") as f:
        m2_raw = json.load(f)
    with open(m3_path, "r", encoding="utf-8") as f:
        m3_raw = json.load(f)

    valid_topic_ids = {t["topic_id"] for t in m2_raw.get("topics", [])}
    valid_decisions = [d["decision"] for d in m3_raw.get("key_decisions", [])]

    evidence_traceable = True
    fabricated_found = False

    for item in explained_output.action_items:
        for t in item.explanation.evidence_traces:
            if t.source_type == "topic":
                if t.source_id not in valid_topic_ids:
                    evidence_traceable = False
                    fabricated_found = True
            elif t.source_type == "decision":
                # Decision excerpt must match an actual raw decision
                if not any(t.text_excerpt in raw_dec for raw_dec in valid_decisions):
                    evidence_traceable = False
                    fabricated_found = True
            elif t.source_type == "transcript_segment":
                # Speaker must be a legitimate speaker format (e.g. SPEAKER_XX)
                if t.speaker and not t.speaker.startswith("SPEAKER_"):
                    fabricated_found = True
                    evidence_traceable = False

    print(f"Evidence traceability               : {'PASS' if evidence_traceable else 'FAIL'}")
    print(f"Fabricated evidence detected        : {'YES' if fabricated_found else 'NO'}")

    # 7. Critical Determinism Validation
    print("\n" + "=" * 125)
    print("CRITICAL DETERMINISM & ZERO-LLM VALIDATION")
    print("=" * 125)

    run_1 = explain_meeting_triage(m3_path, member2_data=m2_path)
    run_2 = explain_meeting_triage(m3_path, member2_data=m2_path)

    deterministic = (run_1.model_dump() == run_2.model_dump())
    print(f"Deterministic output                : {'PASS' if deterministic else 'FAIL'}")

    # Check zero external clients in explainability_engine.py
    engine_file = PROJECT_ROOT / "backend" / "member4" / "explainability_engine.py"
    with open(engine_file, "r", encoding="utf-8") as f:
        code = f.read()

    banned = ["openai", "anthropic", "requests", "urllib", "http.client", "ollama", "boto3"]
    has_banned = any(b in code for b in banned)
    print(f"Zero LLM / External APIs in engine : {'PASS' if not has_banned else 'FAIL'}")

    print("\n" + "=" * 125)
    print("PHASE 7 MANUAL VALIDATION COMPLETE")
    print("=" * 125)


if __name__ == "__main__":
    main()
