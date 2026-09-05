"""
Phase 8: Personalization Engine for Member 4.

Transforms canonical Member 4 intelligence outputs (Phase 7 Explained Action Items)
into role-specific and user-specific views without modifying, recalculating, or
overriding any underlying intelligence decisions.

Supported Roles:
- MANAGER   : Emphasizes high-priority items, deadlines, ownership, and review triggers.
- DEVELOPER : Emphasizes implementation specs, transcript evidence, and dependencies.
- INTERN    : Emphasizes clear task descriptions, owner clarity, and straightforward guidance.
- DEFAULT   : Preserves canonical sequence and complete intelligence metadata.

Strictly deterministic, zero LLM calls, zero network dependencies.
Guarantees 100% canonical result preservation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.member4.explainability_engine import explain_meeting_triage
from backend.member4.schemas import (
    ConfidenceLevel,
    ContextRichDecision,
    ExplainedActionItem,
    Member4ExplainedOutput,
    PersonalizedActionItem,
    PersonalizedMeetingView,
    PersonalizedViewFilter,
    PriorityLevel,
    ReviewStatus,
    RoleEmphasis,
    UserRole,
)


def build_role_emphasis(item: ExplainedActionItem, role: UserRole) -> RoleEmphasis:
    """
    Construct role-specific presentation guidance and highlighted fields.
    Does NOT modify canonical intelligence values.
    """
    p_lvl = item.priority_assessment.level
    c_lvl = item.confidence_assessment.level
    r_stat = item.review_decision.status
    has_deadline = bool(item.deadline and item.deadline.strip())
    is_unassigned = item.is_unassigned

    # Extract dependency info from priority explanation if present
    dep_summary = None
    for f in item.explanation.priority_explanation.factors:
        if f.factor_name == "dependency_blocker" and f.weighted_contribution > 0.0:
            dep_summary = f.evidence_text or "Task has blocker or prerequisite dependency."
            break

    if role == UserRole.MANAGER:
        highlighted = [
            "task",
            "responsible_person",
            "deadline",
            "priority_level",
            "review_status",
            "related_decisions",
        ]
        display_urgency = (p_lvl == PriorityLevel.HIGH) or has_deadline
        display_review = (r_stat != ReviewStatus.AUTO_ACCEPT)

        if r_stat == ReviewStatus.REVIEW_REQUIRED:
            guidance = "Critical attention required: verify unassigned owner or ambiguous deadline before sprint sign-off."
        elif r_stat == ReviewStatus.REVIEW_RECOMMENDED:
            guidance = "Review recommended: team consensus or dialogue grounding requires confirmation."
        elif p_lvl == PriorityLevel.HIGH:
            guidance = "High-priority deliverable: ensure ownership and timeline commitments are strictly tracked."
        else:
            guidance = "Routine operational item: standard status tracking."

    elif role == UserRole.DEVELOPER:
        highlighted = [
            "task",
            "responsible_person",
            "deadline",
            "localized_context",
            "transcript_segments",
            "priority_explanation",
            "confidence_explanation",
        ]
        display_urgency = (p_lvl == PriorityLevel.HIGH)
        display_review = (r_stat != ReviewStatus.AUTO_ACCEPT)

        if dep_summary:
            guidance = f"Technical dependency: {dep_summary}"
        elif r_stat != ReviewStatus.AUTO_ACCEPT:
            guidance = "Specification review recommended: verify dialogue grounding and technical details."
        else:
            guidance = "Implementation task: execute according to corroborated context and specifications."

    elif role == UserRole.INTERN:
        highlighted = [
            "task",
            "responsible_person",
            "deadline",
            "topic_summary",
            "explanation",
        ]
        display_urgency = (p_lvl == PriorityLevel.HIGH)
        display_review = (r_stat != ReviewStatus.AUTO_ACCEPT)

        if is_unassigned:
            guidance = "Unassigned deliverable: please check with team lead before claiming this task."
        elif r_stat != ReviewStatus.AUTO_ACCEPT:
            guidance = "Task flagged for review: coordinate with task owner or mentor before proceeding."
        else:
            guidance = "Task clear: review context summary and coordinate with owner."

    else:  # DEFAULT
        highlighted = [
            "task",
            "responsible_person",
            "deadline",
            "topic_reference",
            "priority_level",
            "confidence_level",
            "review_status",
        ]
        display_urgency = (p_lvl == PriorityLevel.HIGH)
        display_review = (r_stat != ReviewStatus.AUTO_ACCEPT)
        guidance = "Canonical presentation: standard intelligence view."

    return RoleEmphasis(
        role=role,
        highlighted_fields=highlighted,
        display_urgency_badge=display_urgency,
        display_review_badge=display_review,
        role_guidance=guidance,
        dependency_summary=dep_summary,
    )


def project_action_item(item: ExplainedActionItem, role: UserRole) -> PersonalizedActionItem:
    """
    Project an ExplainedActionItem into a PersonalizedActionItem for a specific role.
    Guarantees that canonical priority, confidence, review status, and explanations
    remain bit-for-bit identical to upstream values.
    """
    emphasis = build_role_emphasis(item, role)

    # Invariance check: canonical decisions must match
    p_score = item.priority_assessment.score
    p_lvl = item.priority_assessment.level
    c_score = item.confidence_assessment.score
    c_lvl = item.confidence_assessment.level
    r_stat = item.review_decision.status
    r_codes = list(item.review_decision.reason_codes)

    return PersonalizedActionItem(
        item_id=item.item_id,
        task=item.task,
        responsible_person=item.responsible_person,
        speaker_id=item.speaker_id,
        display_name=item.display_name,
        name_source=item.name_source,
        is_unassigned=item.is_unassigned,
        deadline=item.deadline,
        is_ambiguous_deadline=item.is_ambiguous_deadline,
        topic_reference=item.topic_reference,
        context_status=item.context_status,
        priority_score=p_score,
        priority_level=p_lvl,
        confidence_score=c_score,
        confidence_level=c_lvl,
        review_status=r_stat,
        review_reason_codes=r_codes,
        explanation=item.explanation,
        role_emphasis=emphasis,
    )


def sort_personalized_items(items: List[PersonalizedActionItem], role: UserRole) -> List[PersonalizedActionItem]:
    """
    Deterministically order personalized items according to role priorities.
    Tie-breaker is always item_id ascending.
    """
    p_rank = {PriorityLevel.HIGH: 0, PriorityLevel.MEDIUM: 1, PriorityLevel.LOW: 2}
    r_rank = {ReviewStatus.REVIEW_REQUIRED: 0, ReviewStatus.REVIEW_RECOMMENDED: 1, ReviewStatus.AUTO_ACCEPT: 2}

    if role == UserRole.MANAGER:
        # Manager ordering:
        # 1. Priority level (HIGH -> MEDIUM -> LOW)
        # 2. Has deadline first (0 for has deadline, 1 for none)
        # 3. Review status (REQUIRED -> RECOMMENDED -> AUTO_ACCEPT)
        # 4. Item ID tie-break
        return sorted(
            items,
            key=lambda x: (
                p_rank.get(x.priority_level, 3),
                0 if (x.deadline and x.deadline.strip()) else 1,
                r_rank.get(x.review_status, 3),
                x.item_id,
            ),
        )

    elif role == UserRole.DEVELOPER:
        # Developer ordering:
        # 1. Dependency / technical blocker present first
        # 2. Priority score descending
        # 3. Confidence level (MEDIUM uncertainty first to catch issues, then HIGH)
        # 4. Item ID tie-break
        return sorted(
            items,
            key=lambda x: (
                0 if x.role_emphasis.dependency_summary else 1,
                -x.priority_score,
                0 if x.confidence_level == ConfidenceLevel.MEDIUM else 1,
                x.item_id,
            ),
        )

    elif role == UserRole.INTERN:
        # Intern ordering:
        # 1. Assigned tasks first (0 if assigned, 1 if unassigned)
        # 2. Priority level (HIGH -> MEDIUM -> LOW)
        # 3. Has deadline first
        # 4. Item ID tie-break
        return sorted(
            items,
            key=lambda x: (
                1 if x.is_unassigned else 0,
                p_rank.get(x.priority_level, 3),
                0 if (x.deadline and x.deadline.strip()) else 1,
                x.item_id,
            ),
        )

    else:  # DEFAULT
        # Default ordering: preserve canonical item_id ascending order
        return sorted(items, key=lambda x: x.item_id)


def filter_personalized_items(
    items: List[PersonalizedActionItem],
    filter_query: Optional[PersonalizedViewFilter] = None,
) -> List[PersonalizedActionItem]:
    """
    Apply optional deterministic filters.
    Filtering never modifies underlying items; it only subsets display items.
    """
    if not filter_query:
        return list(items)

    filtered = []
    for item in items:
        if filter_query.priority_level and item.priority_level != filter_query.priority_level:
            continue
        if filter_query.confidence_level and item.confidence_level != filter_query.confidence_level:
            continue
        if filter_query.review_status and item.review_status != filter_query.review_status:
            continue
        if filter_query.assigned_only and item.is_unassigned:
            continue
        if filter_query.unassigned_only and not item.is_unassigned:
            continue
        if filter_query.has_deadline_only and not (item.deadline and item.deadline.strip()):
            continue
        if filter_query.topic_reference is not None and item.topic_reference != filter_query.topic_reference:
            continue
        filtered.append(item)

    return filtered


def build_role_headline(
    role: UserRole,
    total_canonical: int,
    high_count: int,
    review_count: int,
    has_deadline_count: int,
    unassigned_count: int,
) -> str:
    """
    Construct dynamic, non-hardcoded summary headline for a role view.
    """
    if role == UserRole.MANAGER:
        return (
            f"{total_canonical} action items tracked, including {high_count} high-priority item(s), "
            f"{review_count} item(s) flagged for review, and {has_deadline_count} with explicit deadlines."
        )
    elif role == UserRole.DEVELOPER:
        return (
            f"Action items organized around implementation deliverables, context evidence, "
            f"and technical dependencies ({total_canonical} total items, {high_count} high-priority)."
        )
    elif role == UserRole.INTERN:
        return (
            f"Action items presented with clear task descriptions, ownership, deadlines, "
            f"and review signals ({total_canonical} items, {unassigned_count} unassigned)."
        )
    else:  # DEFAULT
        return (
            f"Canonical meeting view presenting all {total_canonical} extracted action items "
            f"with complete multi-factor intelligence assessments."
        )


def personalize_meeting_view(
    explained_output: Union[Member4ExplainedOutput, dict, str, Path],
    role: UserRole = UserRole.DEFAULT,
    filter_query: Optional[PersonalizedViewFilter] = None,
    member2_data: Optional[Union[dict, str, Path]] = None,
) -> PersonalizedMeetingView:
    """
    Top-level entry point for Phase 8 Personalization Engine.

    Consumes Member4ExplainedOutput (or runs upstream Phases 1–7 if raw data is provided)
    and transforms the intelligence into a role-tailored view without altering decisions.
    """
    if not isinstance(explained_output, Member4ExplainedOutput):
        explained_res = explain_meeting_triage(explained_output, member2_data=member2_data)
    else:
        explained_res = explained_output

    total_canonical = len(explained_res.action_items)

    # 1. Project every item to the target role with canonical preservation checks
    projected_items: List[PersonalizedActionItem] = []
    for item in explained_res.action_items:
        p_item = project_action_item(item, role)

        # STRICT CANONICAL INVARIANCE VERIFICATION
        assert p_item.priority_score == item.priority_assessment.score, "Decision drift: priority score changed!"
        assert p_item.priority_level == item.priority_assessment.level, "Decision drift: priority level changed!"
        assert p_item.confidence_score == item.confidence_assessment.score, "Decision drift: confidence score changed!"
        assert p_item.confidence_level == item.confidence_assessment.level, "Decision drift: confidence level changed!"
        assert p_item.review_status == item.review_decision.status, "Decision drift: review status changed!"
        assert p_item.review_reason_codes == item.review_decision.reason_codes, "Decision drift: reason codes changed!"

        projected_items.append(p_item)

    # 2. Sort deterministically according to role rules
    sorted_items = sort_personalized_items(projected_items, role)

    # 3. Apply optional filters
    displayed_items = filter_personalized_items(sorted_items, filter_query)

    # 4. Compute dynamic aggregations from canonical data
    high_count = sum(1 for a in projected_items if a.priority_level == PriorityLevel.HIGH)
    med_count = sum(1 for a in projected_items if a.priority_level == PriorityLevel.MEDIUM)
    low_count = sum(1 for a in projected_items if a.priority_level == PriorityLevel.LOW)
    auto_count = sum(1 for a in projected_items if a.review_status == ReviewStatus.AUTO_ACCEPT)
    rec_count = sum(1 for a in projected_items if a.review_status == ReviewStatus.REVIEW_RECOMMENDED)
    req_count = sum(1 for a in projected_items if a.review_status == ReviewStatus.REVIEW_REQUIRED)
    unassigned_count = sum(1 for a in projected_items if a.is_unassigned)
    deadline_count = sum(1 for a in projected_items if a.deadline and a.deadline.strip())

    headline = build_role_headline(
        role=role,
        total_canonical=total_canonical,
        high_count=high_count,
        review_count=(rec_count + req_count),
        has_deadline_count=deadline_count,
        unassigned_count=unassigned_count,
    )

    return PersonalizedMeetingView(
        meeting_id=explained_res.meeting_id,
        role=role,
        summary_headline=headline,
        total_canonical_items=total_canonical,
        displayed_items_count=len(displayed_items),
        high_priority_count=high_count,
        medium_priority_count=med_count,
        low_priority_count=low_count,
        auto_accept_count=auto_count,
        review_recommended_count=rec_count,
        review_required_count=req_count,
        unassigned_count=unassigned_count,
        has_deadline_count=deadline_count,
        speakers=getattr(explained_res, "speakers", {}),
        action_items=displayed_items,
        key_decisions=explained_res.key_decisions,
        diagnostics=explained_res.diagnostics,
    )
