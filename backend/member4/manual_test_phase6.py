"""
Manual Validation Script for Member 4 Phase 6: Human Review / Uncertainty Handling.

Runs Member 4 Phases 1–6 against actual AMI corpus artifacts:
- data/processed/ES2002a_member3_results.json
- data/processed/ES2002a_member2_results.json

Prints:
1. Complete table of all 32 action items with Priority, Confidence, and Triage Status.
2. Summary statistics (counts and percentages).
3. In-depth inspection for the 4 key representative cases:
   - Case A: Topic 40 remote-control design task
   - Case B: Topic 10 Beagle mascot task (competing decisions)
   - Case C: Topics 16, 17, 18 duplicated animal mascot tasks (weak dialogue grounding)
   - Case D: Topic 39 remote-control form-factor task (weak dialogue grounding)
"""

from pathlib import Path
import sys

# Ensure repository root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member4 import (
    ReviewStatus,
    triage_action_items,
)


def format_table_row(item_id: str, task: str, p_score: float, p_lvl: str, c_score: float, c_lvl: str, status: str, reasons: str) -> str:
    """Format a single table row with fixed column widths."""
    task_trunc = (task[:42] + "..") if len(task) > 44 else task
    return f"{item_id:<14} | {task_trunc:<44} | {p_score:.3f} ({p_lvl:<4}) | {c_score:.3f} ({c_lvl:<6}) | {status:<18} | {reasons}"


def print_case_details(title: str, item) -> None:
    """Print detailed semantic information for a representative case."""
    r_dec = item.review_decision
    p_ass = item.priority_assessment
    c_ass = item.confidence_assessment

    print("-" * 80)
    print(f"CASE: {title}")
    print("-" * 80)
    print(f"  Item ID            : {item.item_id}")
    print(f"  Task Text          : {item.task}")
    print(f"  Topic Reference    : Topic {item.topic_reference}")
    print(f"  Responsible Person : {item.responsible_person or '(Unassigned)'}")
    print(f"  Deadline           : {item.deadline or '(None)'}")
    print(f"  Context Status     : {item.context_status.value}")
    print(f"  Priority           : {p_ass.score:.4f} [{p_ass.level.value}]")
    print(f"  Confidence         : {c_ass.score:.4f} [{c_ass.level.value}]")
    print(f"  Review Status      : {r_dec.status.value}")
    print(f"  Review Required?   : {r_dec.review_required}")
    print(f"  Review Recommended?: {r_dec.review_recommended}")
    
    reason_strs = [code.value for code in r_dec.reason_codes]
    print(f"  Reason Codes       : {reason_strs if reason_strs else 'None (Clean evidence)'}")
    print(f"  Explanation        : {r_dec.explanation}")
    
    # Evidence flags inspection
    print("  Key Evidence Signals:")
    flags = r_dec.evidence_flags
    for k, v in flags.items():
        print(f"    - {k:30s}: {v}")
    
    # Related decisions
    if item.related_decisions:
        print(f"  Related Decisions ({len(item.related_decisions)}):")
        for idx, dec in enumerate(item.related_decisions, start=1):
            print(f"    [{idx}] {dec.decision}")
    else:
        print("  Related Decisions  : None")

    print()


def main():
    m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
    m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

    if not m3_path.exists():
        print(f"ERROR: Member 3 results not found at: {m3_path}")
        sys.exit(1)
    if not m2_path.exists():
        print(f"ERROR: Member 2 results not found at: {m2_path}")
        sys.exit(1)

    print("=" * 120)
    print("MEMBER 4 — PHASE 6 HUMAN REVIEW / UNCERTAINTY HANDLING VALIDATION")
    print("=" * 120)
    print(f"Input Member 3 Artifact: {m3_path}")
    print(f"Input Member 2 Artifact: {m2_path}\n")

    # Run the existing Member 4 pipeline end-to-end through Phase 6
    triage_output = triage_action_items(m3_path, member2_data=m2_path)

    # 1. Print Full Action Items Table
    print("=" * 120)
    print("ALL 32 EXTRACTED TASKS WITH PRIORITY, CONFIDENCE, AND HUMAN REVIEW TRIAGE DECISIONS")
    print("=" * 120)
    header = (
        f"{'ITEM ID':<14} | {'TASK TEXT':<44} | {'PRIORITY':<11} | {'CONFIDENCE':<13} | "
        f"{'REVIEW STATUS':<18} | {'REASON CODES'}"
    )
    print(header)
    print("-" * 120)

    for item in triage_output.action_items:
        p = item.priority_assessment
        c = item.confidence_assessment
        r = item.review_decision
        codes_str = ", ".join(code.value for code in r.reason_codes) if r.reason_codes else "-"
        print(
            format_table_row(
                item.item_id,
                item.task,
                p.score,
                p.level.value,
                c.score,
                c.level.value,
                r.status.value,
                codes_str,
            )
        )

    # 2. Print Summary Statistics
    total = triage_output.total_action_items
    auto = triage_output.auto_accept_count
    rec = triage_output.review_recommended_count
    req = triage_output.review_required_count

    print("\n" + "=" * 120)
    print("PHASE 6 TRIAGE SUMMARY STATISTICS")
    print("=" * 120)
    print(f"Total Action Items Evaluated : {total}")
    print(f"  - AUTO_ACCEPT              : {auto:2d} ({auto/total*100:5.1f}%)")
    print(f"  - REVIEW_RECOMMENDED       : {rec:2d} ({rec/total*100:5.1f}%)")
    print(f"  - REVIEW_REQUIRED          : {req:2d} ({req/total*100:5.1f}%)")

    print("\nTriggered Reason Code Distribution:")
    for code_name, count in sorted(triage_output.reason_code_counts.items(), key=lambda x: -x[1]):
        print(f"  - {code_name:<30s}: {count:2d} item(s)")

    # 3. Explicit In-Depth Inspection of 4 Representative Cases
    print("\n" + "=" * 120)
    print("IN-DEPTH INSPECTION: 4 REPRESENTATIVE CASES")
    print("=" * 120)

    # Case A: Topic 40 remote-control design task
    item_topic_40 = next(a for a in triage_output.action_items if a.topic_reference == 40)
    print_case_details("Topic 40 Remote-Control Design Task (High Priority + High Confidence)", item_topic_40)

    # Case B: Topic 10 Beagle mascot task (competing decisions)
    item_topic_10 = next(a for a in triage_output.action_items if a.topic_reference == 10)
    print_case_details("Topic 10 Beagle Mascot Task (Multiple Competing Decisions)", item_topic_10)

    # Case C: Topics 16, 17, 18 animal mascot tasks (duplicated into unrelated topics)
    items_mascot_dups = [a for a in triage_output.action_items if a.topic_reference in (16, 17, 18)]
    for item_dup in items_mascot_dups:
        print_case_details(
            f"Topic {item_dup.topic_reference} Duplicated Animal Mascot Task (Zero Dialogue Grounding)",
            item_dup,
        )

    # Case D: Topic 39 remote-control form-factor task
    item_topic_39 = next(a for a in triage_output.action_items if a.topic_reference == 39)
    print_case_details("Topic 39 Remote-Control Form-Factor Task (Weak Dialogue Grounding)", item_topic_39)

    print("=" * 120)
    print("MANUAL VALIDATION COMPLETE: All results generated directly from Phase 6 review engine.")
    print("=" * 120)


if __name__ == "__main__":
    main()
