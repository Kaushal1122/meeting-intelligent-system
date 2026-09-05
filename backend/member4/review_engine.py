"""
Phase 6: Human Review / Uncertainty Handling Engine for Member 4.

Consumes enriched action items from Phase 5 (Confidence Intelligence) and applies
deterministic triage rules to classify items into:
- AUTO_ACCEPT: Evidence is sufficiently strong; no material uncertainty signals.
- REVIEW_RECOMMENDED: Usable but contains moderate uncertainty (e.g. competing decisions,
  weak dialogue grounding, partial context, high priority + medium confidence).
- REVIEW_REQUIRED: Material evidence problem or high-risk combination (e.g. high priority
  + low confidence, unresolved/missing context, unassigned high-priority deliverable).

Strictly deterministic, zero LLM calls, zero network dependencies, and preserves all
existing Priority (Phase 4) and Confidence (Phase 5) assessments unchanged.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from backend.member4.confidence_engine import infer_task_confidence
from backend.member4.schemas import (
    ConfidenceEnrichedActionItem,
    ConfidenceLevel,
    Member4ConfidenceOutput,
    Member4TriageOutput,
    PriorityLevel,
    ReviewDecision,
    ReviewReasonCode,
    ReviewStatus,
    TopicContextStatus,
    TriageEnrichedActionItem,
)


class ReviewModelConfig(BaseModel):
    """Configuration thresholds and policies for Human Review Triage."""
    model_config = ConfigDict(extra="ignore")

    require_review_on_high_priority_low_confidence: bool = Field(
        default=True,
        description="Trigger REVIEW_REQUIRED if HIGH priority and LOW confidence."
    )
    require_review_on_high_priority_ambiguous_deadline: bool = Field(
        default=True,
        description="Trigger REVIEW_REQUIRED if HIGH priority deliverable has ambiguous deadline."
    )
    require_review_on_unassigned_high_priority: bool = Field(
        default=True,
        description="Trigger REVIEW_REQUIRED if HIGH priority deliverable has no designated owner."
    )
    require_review_on_unresolved_context: bool = Field(
        default=True,
        description="Trigger REVIEW_REQUIRED if topic reference is unresolved or missing."
    )
    require_review_on_low_confidence: bool = Field(
        default=True,
        description="Trigger REVIEW_REQUIRED for any task with overall LOW confidence."
    )
    recommend_review_on_high_priority_medium_confidence: bool = Field(
        default=True,
        description="Trigger REVIEW_RECOMMENDED if HIGH priority and MEDIUM confidence."
    )
    recommend_review_on_conflicting_decisions: bool = Field(
        default=True,
        description="Trigger REVIEW_RECOMMENDED if multiple competing decisions exist under topic."
    )
    recommend_review_on_weak_grounding: bool = Field(
        default=True,
        description="Trigger REVIEW_RECOMMENDED if dialogue grounding factor is below threshold."
    )
    weak_grounding_threshold: float = Field(
        default=0.50,
        description="Factor raw value below which dialogue grounding is considered weak."
    )


DEFAULT_REVIEW_CONFIG = ReviewModelConfig()


def evaluate_task_triage(
    item: ConfidenceEnrichedActionItem,
    config: ReviewModelConfig = DEFAULT_REVIEW_CONFIG,
) -> ReviewDecision:
    """
    Deterministically evaluate human review triage status for a confidence-enriched action item.

    Does NOT recompute or modify priority or confidence scores.
    Uses existing Phase 2–5 outputs as structural evidence.
    """
    priority_level = item.priority_assessment.level
    confidence_level = item.confidence_assessment.level
    confidence_score = item.confidence_assessment.score

    reason_codes: List[ReviewReasonCode] = []
    explanation_parts: List[str] = []
    evidence_flags: Dict[str, Any] = {}

    # Extract factor values for localized grounding and decisions from Phase 5 assessment
    localized_factor = next(
        (f for f in item.confidence_assessment.factor_contributions if f.factor_name == "localized_evidence_grounding"),
        None
    )
    decision_factor = next(
        (f for f in item.confidence_assessment.factor_contributions if f.factor_name == "decision_evidence_consistency"),
        None
    )

    is_weak_grounding = (
        localized_factor is not None
        and localized_factor.raw_value < config.weak_grounding_threshold
    )
    has_competing_decisions = len(item.related_decisions) > 1

    # ------------------------------------------------------------------------
    # 1. EVALUATE CRITICAL SIGNALS (Trigger REVIEW_REQUIRED)
    # ------------------------------------------------------------------------
    is_required = False

    # A. HIGH Priority + LOW Confidence
    if (
        config.require_review_on_high_priority_low_confidence
        and priority_level == PriorityLevel.HIGH
        and confidence_level == ConfidenceLevel.LOW
    ):
        is_required = True
        reason_codes.append(ReviewReasonCode.HIGH_PRIORITY_LOW_CONFIDENCE)
        explanation_parts.append(
            f"High-priority task ({item.priority_assessment.score:.2f}) has critically low contextual evidence ({confidence_score:.2f})."
        )
        evidence_flags["high_priority_low_confidence"] = True

    # B. HIGH Priority + Ambiguous Deadline
    if (
        config.require_review_on_high_priority_ambiguous_deadline
        and priority_level == PriorityLevel.HIGH
        and item.is_ambiguous_deadline
    ):
        is_required = True
        reason_codes.append(ReviewReasonCode.HIGH_PRIORITY_AMBIGUOUS_DEADLINE)
        explanation_parts.append(
            f"High-priority deliverable has an ambiguous deadline ('{item.deadline}') posing scheduling risk."
        )
        evidence_flags["high_priority_ambiguous_deadline"] = True

    # C. Unassigned HIGH Priority Task
    if (
        config.require_review_on_unassigned_high_priority
        and priority_level == PriorityLevel.HIGH
        and item.is_unassigned
    ):
        is_required = True
        reason_codes.append(ReviewReasonCode.UNASSIGNED_HIGH_PRIORITY_TASK)
        explanation_parts.append(
            "High-priority deliverable lacks a designated owner and requires explicit task assignment."
        )
        evidence_flags["unassigned_high_priority"] = True

    # D. Missing Topic Reference
    if item.context_status == TopicContextStatus.MISSING_REFERENCE:
        if config.require_review_on_unresolved_context:
            is_required = True
        reason_codes.append(ReviewReasonCode.MISSING_TOPIC_REFERENCE)
        explanation_parts.append("Task payload contains no topic reference and cannot be anchored in meeting dialogue.")
        evidence_flags["missing_topic_reference"] = True

    # E. Unresolved Topic Reference
    elif item.context_status == TopicContextStatus.UNRESOLVED:
        if config.require_review_on_unresolved_context:
            is_required = True
        reason_codes.append(ReviewReasonCode.UNRESOLVED_CONTEXT)
        explanation_parts.append(f"Topic reference {item.topic_reference} could not be resolved in meeting segmentation.")
        evidence_flags["unresolved_context"] = True

    # F. General LOW Confidence (if not already captured under combination)
    if (
        config.require_review_on_low_confidence
        and confidence_level == ConfidenceLevel.LOW
        and ReviewReasonCode.HIGH_PRIORITY_LOW_CONFIDENCE not in reason_codes
    ):
        is_required = True
        reason_codes.append(ReviewReasonCode.LOW_CONFIDENCE)
        explanation_parts.append(f"Task has low overall evidence reliability ({confidence_score:.2f}).")
        evidence_flags["low_confidence"] = True

    # ------------------------------------------------------------------------
    # 2. EVALUATE MODERATE SIGNALS (Trigger REVIEW_RECOMMENDED)
    # ------------------------------------------------------------------------
    is_recommended = False

    # G. HIGH Priority + MEDIUM Confidence
    if (
        config.recommend_review_on_high_priority_medium_confidence
        and priority_level == PriorityLevel.HIGH
        and confidence_level == ConfidenceLevel.MEDIUM
    ):
        is_recommended = True
        reason_codes.append(ReviewReasonCode.HIGH_PRIORITY_MEDIUM_CONFIDENCE)
        explanation_parts.append(
            f"High-priority task ({item.priority_assessment.score:.2f}) possesses moderate evidence certainty ({confidence_score:.2f}); human verification advised."
        )
        evidence_flags["high_priority_medium_confidence"] = True

    # H. General MEDIUM Confidence (when priority != HIGH)
    elif confidence_level == ConfidenceLevel.MEDIUM:
        is_recommended = True
        reason_codes.append(ReviewReasonCode.MEDIUM_CONFIDENCE)
        explanation_parts.append(f"Task exhibits moderate evidence reliability ({confidence_score:.2f}).")
        evidence_flags["medium_confidence"] = True

    # I. Partially Resolved Context
    if item.context_status == TopicContextStatus.PARTIALLY_RESOLVED:
        is_recommended = True
        reason_codes.append(ReviewReasonCode.PARTIAL_CONTEXT)
        explanation_parts.append("Topic summary exists but localized dialogue segment turns are missing.")
        evidence_flags["partial_context"] = True

    # J. Conflicting Decisions in Topic
    if config.recommend_review_on_conflicting_decisions and has_competing_decisions:
        is_recommended = True
        reason_codes.append(ReviewReasonCode.CONFLICTING_DECISIONS)
        explanation_parts.append(
            f"Multiple competing decisions ({len(item.related_decisions)}) indicate unresolved consensus in topic."
        )
        evidence_flags["conflicting_decisions"] = True

    # K. Weak Dialogue Grounding (e.g. 0 lexical overlap in window)
    if config.recommend_review_on_weak_grounding and is_weak_grounding:
        is_recommended = True
        reason_codes.append(ReviewReasonCode.WEAK_DIALOGUE_GROUNDING)
        explanation_parts.append("Task description lacks lexical corroboration in localized dialogue turns.")
        evidence_flags["weak_dialogue_grounding"] = True

    # L. Ambiguous Deadline (when priority is not HIGH)
    if item.is_ambiguous_deadline and priority_level != PriorityLevel.HIGH:
        is_recommended = True
        reason_codes.append(ReviewReasonCode.AMBIGUOUS_DEADLINE)
        explanation_parts.append(f"Task deadline constraint is ambiguous ('{item.deadline}').")
        evidence_flags["ambiguous_deadline"] = True

    # M. Unassigned Task (when priority is not HIGH)
    if item.is_unassigned and priority_level != PriorityLevel.HIGH:
        is_recommended = True
        reason_codes.append(ReviewReasonCode.UNASSIGNED_TASK)
        explanation_parts.append("Task lacks an assigned owner.")
        evidence_flags["unassigned_task"] = True

    # ------------------------------------------------------------------------
    # 3. DETERMINE FINAL STATUS AND SYNTHESIZE EXPLANATION
    # ------------------------------------------------------------------------
    cleaned_parts = [p.rstrip(".") for p in explanation_parts]

    if is_required:
        status = ReviewStatus.REVIEW_REQUIRED
        explanation = "Review required: " + "; ".join(cleaned_parts) + "."
    elif is_recommended:
        status = ReviewStatus.REVIEW_RECOMMENDED
        explanation = "Review recommended: " + "; ".join(cleaned_parts) + "."
    else:
        status = ReviewStatus.AUTO_ACCEPT
        explanation = "Evidence is sufficiently strong with no material uncertainty signals; automatically accepted."

    return ReviewDecision(

        status=status,
        review_required=(status == ReviewStatus.REVIEW_REQUIRED),
        review_recommended=(status == ReviewStatus.REVIEW_RECOMMENDED),
        reason_codes=reason_codes,
        explanation=explanation,
        evidence_flags=evidence_flags,
    )


def triage_action_items(
    confidence_output: Union[Member4ConfidenceOutput, dict, str, Path],
    member2_data: Optional[Union[dict, str, Path]] = None,
    config: ReviewModelConfig = DEFAULT_REVIEW_CONFIG,
) -> Member4TriageOutput:
    """
    Top-level entry point for Phase 6 Human Review & Uncertainty Handling.

    Accepts either an already-evaluated Member4ConfidenceOutput, or runs Phase 5
    Confidence Engine on the input if needed, then applies deterministic triage.
    """
    if not isinstance(confidence_output, Member4ConfidenceOutput):
        confidence_res = infer_task_confidence(confidence_output, member2_data=member2_data)
    else:
        confidence_res = confidence_output

    triage_items: List[TriageEnrichedActionItem] = []
    auto_accept_count = 0
    review_recommended_count = 0
    review_required_count = 0
    reason_code_counts: Dict[str, int] = {}

    for item in confidence_res.action_items:
        decision = evaluate_task_triage(item, config=config)

        if decision.status == ReviewStatus.AUTO_ACCEPT:
            auto_accept_count += 1
        elif decision.status == ReviewStatus.REVIEW_RECOMMENDED:
            review_recommended_count += 1
        elif decision.status == ReviewStatus.REVIEW_REQUIRED:
            review_required_count += 1

        for code in decision.reason_codes:
            code_str = code.value
            reason_code_counts[code_str] = reason_code_counts.get(code_str, 0) + 1

        triage_item = TriageEnrichedActionItem(
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
            topic_summary=item.topic_summary,
            topic_speakers=item.topic_speakers,
            localized_context=item.localized_context,
            context_start=item.context_start,
            context_end=item.context_end,
            related_decisions=item.related_decisions,
            deadline_context_snippet=item.deadline_context_snippet,
            source_priority=item.source_priority,
            source_confidence_score=item.source_confidence_score,
            is_duplicate=item.is_duplicate,
            duplicate_of=item.duplicate_of,
            context_diagnostics=item.context_diagnostics,
            priority_assessment=item.priority_assessment,
            confidence_assessment=item.confidence_assessment,
            review_decision=decision,
        )
        triage_items.append(triage_item)

    return Member4TriageOutput(
        meeting_id=confidence_res.meeting_id,
        processing_stage="member_4_triage_enriched",
        total_action_items=len(triage_items),
        auto_accept_count=auto_accept_count,
        review_recommended_count=review_recommended_count,
        review_required_count=review_required_count,
        reason_code_counts=reason_code_counts,
        action_items=triage_items,
        speakers=getattr(confidence_res, "speakers", {}),
        key_decisions=confidence_res.key_decisions,
        diagnostics=confidence_res.diagnostics,
    )
