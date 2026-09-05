"""
Member 4 Confidence Intelligence Engine (Phase 5).

Estimates evidence reliability and factual grounding for Member 4 action items.
Decouples confidence (evidence reliability) from priority (task importance).

Core Guarantees:
1. Evidence-Driven Confidence: Evaluates context resolution completeness, localized
   dialogue grounding, task/assignee consistency, deadline evidence quality,
   topic resolution, decision consistency, and structural completeness.
2. Complete Independence from Priority: Confidence reflects evidence certainty, not
   task urgency. High priority can have low confidence; low priority can have high confidence.
3. Member 3 Independence: Member 3 source confidence is preserved strictly as
   `source_confidence_score` and never used as ground truth.
4. Non-Penalizing Baselines: Missing deadlines do not artificially degrade confidence;
   ambiguous deadlines specifically reflect uncertainty.
5. Contradiction Detection: Multiple competing same-topic decisions reduce confidence.
6. Zero LLM / Zero External APIs: 100% deterministic, local, and offline.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .priority_engine import infer_task_priorities
from .schemas import (
    ConfidenceAssessment,
    ConfidenceEnrichedActionItem,
    ConfidenceFactorContribution,
    ConfidenceLevel,
    ContextRichDecision,
    Member4ConfidenceOutput,
    Member4PriorityOutput,
    PriorityEnrichedActionItem,
    TopicContextStatus,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

class ConfidenceModelConfig(BaseModel):
    """
    Configurable factor weights and classification thresholds for the Confidence Engine.
    Weights sum to 1.00.
    """
    model_config = ConfigDict(extra="ignore")

    # Factor Weights (sum = 1.00)
    weight_context_resolution: float = Field(default=0.20, description="Weight for topic/segment resolution completeness.")
    weight_localized_evidence: float = Field(default=0.20, description="Weight for dialogue turns, segments, and timestamp grounding.")
    weight_assignee_consistency: float = Field(default=0.15, description="Weight for task ownership and dialogue attribution alignment.")
    weight_deadline_evidence: float = Field(default=0.15, description="Weight for deadline clarity and temporal evidence.")
    weight_topic_resolution: float = Field(default=0.10, description="Weight for topic metadata and summary quality.")
    weight_decision_consistency: float = Field(default=0.10, description="Weight for decision alignment vs conflicting alternatives.")
    weight_structural_completeness: float = Field(default=0.10, description="Weight for structural integrity and provenance completeness.")

    # Classification Thresholds
    threshold_high: float = Field(default=0.75, description="Score threshold for HIGH confidence tier.")
    threshold_medium: float = Field(default=0.50, description="Score threshold for MEDIUM confidence tier.")


# Default instance
DEFAULT_CONFIDENCE_CONFIG = ConfidenceModelConfig()


# ============================================================================
# FACTOR EVALUATION UTILITIES
# ============================================================================

def eval_context_resolution(
    item: PriorityEnrichedActionItem,
    weight: float,
) -> ConfidenceFactorContribution:
    """
    Assess context resolution status (RESOLVED, PARTIALLY_RESOLVED, UNRESOLVED, MISSING_REFERENCE).
    """
    factor_name = "context_resolution"

    if item.context_status == TopicContextStatus.RESOLVED:
        raw_val = 1.00
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text="Context fully resolved with localized dialogue turns and verified topic.",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    if item.context_status == TopicContextStatus.PARTIALLY_RESOLVED:
        raw_val = 0.50
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text="Context partially resolved: topic summary exists but transcript segment turns are missing.",
            evidence_segment_ids=[],
        )

    if item.context_status == TopicContextStatus.UNRESOLVED:
        raw_val = 0.20
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=False,
            evidence_text="Topic reference could not be resolved in Member 2 data.",
            evidence_segment_ids=[],
        )

    # MISSING_REFERENCE
    raw_val = 0.00
    return ConfidenceFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=0.0,
        has_evidence=False,
        evidence_text="No topic reference provided in extraction payload.",
        evidence_segment_ids=[],
    )


def eval_localized_evidence(
    item: PriorityEnrichedActionItem,
    weight: float,
) -> ConfidenceFactorContribution:
    """
    Assess presence and quality of localized dialogue, segment IDs, timestamps,
    speakers, and semantic corroboration of the task description within dialogue turns.
    """
    factor_name = "localized_evidence_grounding"
    ctx = item.localized_context

    if not ctx or not ctx.window_text.strip():
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=0.0,
            weight=weight,
            weighted_contribution=0.0,
            has_evidence=False,
            evidence_text="No localized dialogue window or transcript segment turns available.",
            evidence_segment_ids=[],
        )

    # 1. Base structural elements: up to 0.40
    struct_score = 0.0
    if ctx.window_text.strip():
        struct_score += 0.15
    if ctx.segment_ids:
        struct_score += 0.10
    if item.context_start is not None and item.context_end is not None:
        struct_score += 0.10
    if ctx.speakers:
        struct_score += 0.05

    # 2. Semantic content corroboration in dialogue turns: up to 0.60
    # Check lexical overlap of substantive task words in the dialogue window
    stopwords = {
        "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with",
        "by", "at", "from", "as", "is", "are", "was", "were", "it", "its",
        "be", "this", "that", "our", "we", "you", "they", "i", "discuss",
        "finalize", "work",
    }
    task_words = [
        w.lower().strip(".,!?:;\"'")
        for w in item.task.split()
        if w.lower().strip(".,!?:;\"'") not in stopwords and len(w) > 2
    ]
    window_lower = ctx.window_text.lower()
    matches = [w for w in task_words if w in window_lower] if task_words else []
    overlap_ratio = len(matches) / max(1, len(task_words)) if task_words else 0.50

    content_score = 0.60 * min(1.0, overlap_ratio / 0.40)
    raw_val = round(min(1.00, struct_score + content_score), 2)

    if overlap_ratio >= 0.40:
        notes = f"Strong localized grounding: task verified in dialogue ({len(matches)}/{len(task_words)} key terms), {len(ctx.segment_ids)} segments, timestamps ({item.context_start}s–{item.context_end}s), speakers {ctx.speakers}."
    elif overlap_ratio > 0.0:
        notes = f"Moderate localized grounding: partial dialogue overlap ({len(matches)}/{len(task_words)} terms), {len(ctx.segment_ids)} segments, speakers {ctx.speakers}."
    else:
        notes = f"Weak localized grounding: zero task keyword overlap in dialogue window despite {len(ctx.segment_ids)} segment turns, speakers {ctx.speakers}."


    return ConfidenceFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True if raw_val >= 0.50 else False,
        evidence_text=notes,
        evidence_segment_ids=ctx.segment_ids,
    )


def eval_assignee_consistency(
    item: PriorityEnrichedActionItem,
    weight: float,
) -> ConfidenceFactorContribution:
    """
    Assess consistency of task attribution and ownership.
    Distinguishes explicit dialogue delegation from passive metadata attribution.
    """
    factor_name = "task_assignee_consistency"

    if item.is_unassigned or not item.responsible_person:
        raw_val = 0.35
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=False,
            evidence_text="Unassigned task; lacks assignee evidence but task text is valid.",
            evidence_segment_ids=[],
        )

    person = item.responsible_person
    window = item.localized_context.window_text.lower() if item.localized_context else ""

    # Direct address or delegation in dialogue to this person (e.g. Topic 40)
    has_direct_delegation = any(k in window for k in [
        "you're going to be", "you will be working", "you'll be working", "your task is", "your job is",
        f"you, {person.lower()}", f"{person.lower()}, you"
    ]) or (
        item.localized_context
        and item.localized_context.speakers
        and item.localized_context.speakers[0] == person
        and any(k in window for k in ["i will", "i'll do", "i can do", "i am working"])
    )

    if has_direct_delegation:
        raw_val = 1.00
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Assignee '{person}' explicitly corroborated by direct dialogue delegation / commitment.",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    # Metadata attribution with active participant in dialogue
    if item.localized_context and person in item.localized_context.speakers:
        raw_val = 0.70
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Assignee '{person}' active in localized dialogue; attribution from metadata.",
            evidence_segment_ids=[],
        )

    # Metadata attribution without active participation in window
    raw_val = 0.50
    return ConfidenceFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text=f"Assignee '{person}' attributed in extraction metadata; passive alignment in context.",
        evidence_segment_ids=[],
    )


def eval_deadline_evidence(
    item: PriorityEnrichedActionItem,
    weight: float,
) -> ConfidenceFactorContribution:
    """
    Assess deadline evidence quality.
    Missing deadline is NOT penalized (common and normal in meetings; neutral baseline).
    Ambiguous deadline explicitly degrades confidence.
    """
    factor_name = "deadline_evidence_quality"

    if not item.deadline:
        # Neutral unpenalized baseline
        raw_val = 0.60
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=False,
            evidence_text="No deadline constraint specified; neutral baseline (unpenalized).",
            evidence_segment_ids=[],
        )

    if item.is_ambiguous_deadline:
        raw_val = 0.30
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Ambiguous temporal deadline ('{item.deadline}') reduces certainty in execution timeframe.",
            evidence_segment_ids=[],
        )

    # Explicit deadline verified by snippet
    if item.deadline_context_snippet:
        raw_val = 1.00
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Explicit deadline '{item.deadline}' verified and corroborated by dialogue snippet.",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    raw_val = 0.80
    return ConfidenceFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text=f"Explicit deadline '{item.deadline}' present in extraction metadata.",
        evidence_segment_ids=[],
    )


def eval_topic_resolution(
    item: PriorityEnrichedActionItem,
    weight: float,
) -> ConfidenceFactorContribution:
    """
    Assess topic metadata and abstractive summary grounding.
    """
    factor_name = "topic_resolution_quality"

    if item.context_status == TopicContextStatus.RESOLVED and item.topic_summary:
        raw_val = 1.00
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Topic {item.topic_reference} successfully verified with abstractive summary.",
            evidence_segment_ids=[],
        )

    if item.context_status == TopicContextStatus.PARTIALLY_RESOLVED:
        raw_val = 0.50
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Topic {item.topic_reference} metadata verified, but segment turns missing.",
            evidence_segment_ids=[],
        )

    if item.context_status == TopicContextStatus.UNRESOLVED:
        raw_val = 0.20
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=False,
            evidence_text=f"Topic reference {item.topic_reference} unverified against Member 2 dataset.",
            evidence_segment_ids=[],
        )

    # MISSING_REFERENCE
    raw_val = 0.00
    return ConfidenceFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=0.0,
        has_evidence=False,
        evidence_text="No topic reference available for verification.",
        evidence_segment_ids=[],
    )


def eval_decision_consistency(
    item: PriorityEnrichedActionItem,
    weight: float,
) -> ConfidenceFactorContribution:
    """
    Assess consistency of related key decisions.
    Multiple competing decisions (e.g. Topic 10 mascot alternatives) indicate consensus ambiguity.
    """
    factor_name = "decision_evidence_consistency"
    num_decisions = len(item.related_decisions)

    if num_decisions == 0:
        # Neutral unpenalized baseline
        raw_val = 0.60
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=False,
            evidence_text="No linked decisions; zero contradiction evidence.",
            evidence_segment_ids=[],
        )

    if num_decisions == 1:
        raw_val = 1.00
        return ConfidenceFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Consistent supporting decision linked: '{item.related_decisions[0].decision[:60]}...'",
            evidence_segment_ids=[],
        )

    # Multiple competing decisions in same topic (e.g. Topic 10 contradictory mascot alternatives)
    raw_val = 0.20
    return ConfidenceFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text=f"Multiple competing/alternative decisions ({num_decisions}) indicate topic ambiguity or unresolved consensus.",
        evidence_segment_ids=[],
    )



def eval_structural_completeness(
    item: PriorityEnrichedActionItem,
    weight: float,
) -> ConfidenceFactorContribution:
    """
    Assess structural completeness and provenance integrity of the action item.
    """
    factor_name = "structural_completeness"

    score_components = 0.0
    if item.item_id:
        score_components += 0.25
    if len(item.task.split()) >= 3:
        score_components += 0.25
    if item.topic_reference is not None:
        score_components += 0.25
    if not item.context_diagnostics or all("Unassigned" in d or "No topic" in d for d in item.context_diagnostics):
        score_components += 0.25

    raw_val = min(1.00, score_components)
    return ConfidenceFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text="Payload possesses structural integrity and source provenance.",
        evidence_segment_ids=[],
    )


# ============================================================================
# PRIMARY CONFIDENCE ENGINE ENTRYPOINT
# ============================================================================

def infer_task_confidence(
    priority_data: Union[Member4PriorityOutput, Dict[str, Any], str, Path],
    member2_data: Optional[Union[Dict[str, Any], str, Path, List[Dict[str, Any]]]] = None,
    config: Optional[ConfidenceModelConfig] = None,
) -> Member4ConfidenceOutput:
    """
    Infer evidence reliability confidence scores and factor breakdowns for action items.

    Args:
        priority_data: Phase 4 Member4PriorityOutput, raw dict, or path to Member 3 JSON.
        member2_data: Optional Member 2 topic results (used if upstream needs to be built).
        config: Optional custom ConfidenceModelConfig weights and thresholds.

    Returns:
        Member4ConfidenceOutput containing confidence-enriched action items and breakdown.
    """
    active_config = config or DEFAULT_CONFIDENCE_CONFIG
    diagnostics: List[str] = []

    # ------------------------------------------------------------------------
    # 1. Ingest / Run Upstream Pipeline
    # ------------------------------------------------------------------------
    if isinstance(priority_data, Member4PriorityOutput):
        prio_output = priority_data
    elif isinstance(priority_data, dict) and priority_data.get("processing_stage") == "member_4_priority_enriched":
        prio_output = Member4PriorityOutput.model_validate(priority_data)
    else:
        # Composable: run Phase 1-4 pipeline from input
        prio_output = infer_task_priorities(priority_data, member2_data=member2_data)

    meeting_id = prio_output.meeting_id

    # ------------------------------------------------------------------------
    # 2. Evaluate Confidence for Each Action Item
    # ------------------------------------------------------------------------
    enriched_items: List[ConfidenceEnrichedActionItem] = []
    scores: List[float] = []
    high_count = 0
    med_count = 0
    low_count = 0

    for item in prio_output.action_items:
        # Evaluate all 7 confidence factors
        f_ctx = eval_context_resolution(item, active_config.weight_context_resolution)
        f_loc = eval_localized_evidence(item, active_config.weight_localized_evidence)
        f_asg = eval_assignee_consistency(item, active_config.weight_assignee_consistency)
        f_dl = eval_deadline_evidence(item, active_config.weight_deadline_evidence)
        f_top = eval_topic_resolution(item, active_config.weight_topic_resolution)
        f_dec = eval_decision_consistency(item, active_config.weight_decision_consistency)
        f_str = eval_structural_completeness(item, active_config.weight_structural_completeness)

        factors = [f_ctx, f_loc, f_asg, f_dl, f_top, f_dec, f_str]

        # Calculate continuous confidence score: bounded sum of weighted contributions
        raw_score = sum(f.weighted_contribution for f in factors)
        score = round(max(0.0, min(1.0, raw_score)), 4)
        scores.append(score)

        # Categorical tier assignment strictly according to configured thresholds
        if score >= active_config.threshold_high:
            level = ConfidenceLevel.HIGH
            high_count += 1
        elif score >= active_config.threshold_medium:
            level = ConfidenceLevel.MEDIUM
            med_count += 1
        else:
            level = ConfidenceLevel.LOW
            low_count += 1

        scoring_breakdown = {f.factor_name: f.weighted_contribution for f in factors}
        evidence_notes = [f.evidence_text for f in factors if f.evidence_text]

        assessment = ConfidenceAssessment(
            score=score,
            level=level,
            factor_contributions=factors,
            scoring_breakdown=scoring_breakdown,
            evidence_quality_notes=evidence_notes,
        )

        enriched_item = ConfidenceEnrichedActionItem(
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
            confidence_assessment=assessment,
        )
        enriched_items.append(enriched_item)

    # ------------------------------------------------------------------------
    # 3. Assemble Output Summary
    # ------------------------------------------------------------------------
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    return Member4ConfidenceOutput(
        meeting_id=meeting_id,
        processing_stage="member_4_confidence_enriched",
        total_action_items=len(enriched_items),
        high_confidence_count=high_count,
        medium_confidence_count=med_count,
        low_confidence_count=low_count,
        min_score=min_score,
        max_score=max_score,
        avg_score=avg_score,
        action_items=enriched_items,
        speakers=getattr(prio_output, "speakers", {}),
        key_decisions=prio_output.key_decisions,
        diagnostics=diagnostics,
    )
