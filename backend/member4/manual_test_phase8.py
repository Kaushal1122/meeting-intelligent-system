"""
Manual Validation Script for Member 4 Phase 8: Personalization Engine.

Runs complete Member 4 pipeline end-to-end against real AMI corpus data:
  Phase 2 Normalizer -> Phase 3 Context Engine -> Phase 4 Priority Engine ->
  Phase 5 Confidence Engine -> Phase 6 Review Engine -> Phase 7 Explainability Engine ->
  Phase 8 Personalization Engine

Generates and validates all 4 role views:
- MANAGER
- DEVELOPER
- INTERN
- DEFAULT

Validates 100% canonical decision invariance and inspects Representative Cases A, B, C, D.
"""

from pathlib import Path
import sys

# Ensure repository root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member4 import (
    ConfidenceLevel,
    PersonalizedViewFilter,
    PriorityLevel,
    ReviewStatus,
    UserRole,
    explain_meeting_triage,
    personalize_meeting_view,
)


def print_case_inspection(title: str, item_id: str, explained_canonical, views):
    canonical_item = next(a for a in explained_canonical.action_items if a.item_id == item_id)
    p_ass = canonical_item.priority_assessment
    c_ass = canonical_item.confidence_assessment
    r_dec = canonical_item.review_decision

    print("\n" + "=" * 100)
    print(f"{title} ({item_id})")
    print("=" * 100)
    print(f"Task Text       : {canonical_item.task}")
    print(f"Topic Reference : Topic {canonical_item.topic_reference}")
    print(f"Responsible     : {canonical_item.responsible_person or '(Unassigned)'}")
    print(f"Deadline        : {canonical_item.deadline or '(None)'}")
    print(
        f"Canonical Score : Priority={p_ass.score:.4f} [{p_ass.level.value}], "
        f"Confidence={c_ass.score:.4f} [{c_ass.level.value}], "
        f"Review={r_dec.status.value}"
    )
    if r_dec.reason_codes:
        print(f"Reason Codes    : {[c.value for c in r_dec.reason_codes]}")

    print("\nRole Projections & Presentations:")
    for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]:
        view = views[role]
        item_r = next(a for a in view.action_items if a.item_id == item_id)
        pos = [a.item_id for a in view.action_items].index(item_id) + 1

        print(f"  [{role.value:<9}] Rank #{pos:2d}/32 | UrgencyBadge={item_r.role_emphasis.display_urgency_badge} | ReviewBadge={item_r.role_emphasis.display_review_badge}")
        print(f"             Guidance: \"{item_r.role_emphasis.role_guidance}\"")
        if item_r.role_emphasis.dependency_summary:
            print(f"             Dependency: {item_r.role_emphasis.dependency_summary}")


def main():
    m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
    m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

    if not m3_path.exists() or not m2_path.exists():
        print("ERROR: Missing input artifacts.")
        sys.exit(1)

    print("=" * 125)
    print("MEMBER 4 — PHASE 8 PERSONALIZATION ENGINE MANUAL VALIDATION")
    print("=" * 125)
    print(f"Member 3 Artifact: {m3_path}")
    print(f"Member 2 Artifact: {m2_path}\n")

    # Step 1: Run complete upstream intelligence pipeline (Phase 2 -> Phase 7)
    explained_canonical = explain_meeting_triage(m3_path, member2_data=m2_path)
    total_canonical = len(explained_canonical.action_items)

    # Step 2: Generate all four role views
    views = {
        role: personalize_meeting_view(explained_canonical, role=role)
        for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]
    }

    # Print Views Overview & Dynamic Headlines
    print("=" * 125)
    print("ROLE VIEWS & DYNAMIC EXECUTIVE HEADLINES")
    print("=" * 125)
    for role, view in views.items():
        print(f"[{role.value:<9}] Total: {view.displayed_items_count}/{view.total_canonical_items} items")
        print(f"           Headline: \"{view.summary_headline}\"\n")

    # Metrics Breakdown
    mgr = views[UserRole.MANAGER]
    print("=" * 125)
    print("CANONICAL INTELLIGENCE METRICS (Preserved identically across all 4 views)")
    print("=" * 125)
    print(f"Total Canonical Action Items : {total_canonical}")
    print(f"Total MANAGER Items          : {len(views[UserRole.MANAGER].action_items)}")
    print(f"Total DEVELOPER Items        : {len(views[UserRole.DEVELOPER].action_items)}")
    print(f"Total INTERN Items           : {len(views[UserRole.INTERN].action_items)}")
    print(f"Total DEFAULT Items          : {len(views[UserRole.DEFAULT].action_items)}")
    print(f"Priority Distribution        : HIGH={mgr.high_priority_count}, MEDIUM={mgr.medium_priority_count}, LOW={mgr.low_priority_count}")
    print(f"Review Triage Distribution   : AUTO_ACCEPT={mgr.auto_accept_count}, REVIEW_RECOMMENDED={mgr.review_recommended_count}, REVIEW_REQUIRED={mgr.review_required_count}")
    print(f"Medium Confidence Items      : {sum(1 for a in mgr.action_items if a.confidence_level == ConfidenceLevel.MEDIUM)}")
    print(f"Unassigned Items             : {mgr.unassigned_count}")
    print(f"Items With Explicit Deadline : {mgr.has_deadline_count}")

    # Strict Invariance Validation Across All Items & All Views
    drift_count = 0
    for role, view in views.items():
        for p_item in view.action_items:
            orig = next(a for a in explained_canonical.action_items if a.item_id == p_item.item_id)
            if (
                p_item.priority_score != orig.priority_assessment.score
                or p_item.priority_level != orig.priority_assessment.level
                or p_item.confidence_score != orig.confidence_assessment.score
                or p_item.confidence_level != orig.confidence_assessment.level
                or p_item.review_status != orig.review_decision.status
                or p_item.review_reason_codes != orig.review_decision.reason_codes
            ):
                drift_count += 1

    print(f"\nCanonical Invariance Check (128 item projections): {'PASS (Zero Drift Detected)' if drift_count == 0 else 'FAIL'}")

    # Inspect Representative Cases A, B, C, D
    print_case_inspection("CASE A: Topic 40 Working Remote Design", "norm_act_031", explained_canonical, views)
    print_case_inspection("CASE B: Topic 10 Beagle Mascot (Conflicting Decisions)", "norm_act_006", explained_canonical, views)
    print_case_inspection("CASE C (1): Topic 16 Animal Mascot (Weak Dialogue Grounding)", "norm_act_011", explained_canonical, views)
    print_case_inspection("CASE C (2): Topic 17 Animal Mascot (Weak Dialogue Grounding)", "norm_act_012", explained_canonical, views)
    print_case_inspection("CASE C (3): Topic 18 Animal Mascot (Weak Dialogue Grounding)", "norm_act_013", explained_canonical, views)
    print_case_inspection("CASE D: Topic 39 Remote Control Form Factor", "norm_act_030", explained_canonical, views)

    # Optional Filtering Demonstration
    print("\n" + "=" * 125)
    print("DETERMINISTIC FILTERING DEMONSTRATION (MANAGER VIEW)")
    print("=" * 125)
    filter_review = PersonalizedViewFilter(review_status=ReviewStatus.REVIEW_RECOMMENDED)
    view_filtered = personalize_meeting_view(
        explained_canonical, role=UserRole.MANAGER, filter_query=filter_review
    )
    print(f"Filter: review_status == REVIEW_RECOMMENDED")
    print(f"Displayed Items: {view_filtered.displayed_items_count}/{view_filtered.total_canonical_items}")
    for item in view_filtered.action_items:
        print(f"  - {item.item_id} | {item.task[:45]:<45} | Reason: {[c.value for c in item.review_reason_codes]}")

    print("\n" + "=" * 125)
    print("PHASE 8 MANUAL VALIDATION COMPLETE")
    print("=" * 125)


if __name__ == "__main__":
    main()
