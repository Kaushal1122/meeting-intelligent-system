"""
Member 4 Priority Intelligence Engine (Phase 4).

Consumes Phase 3 context-rich tasks and infers calibrated operational priority
using a transparent, deterministic, multi-factor scoring model.

Core Guarantees:
1. Multi-Factor Evidence Model: Combines deadline urgency, explicit urgency language,
   assignment explicitness, dependency/blocker signals, decision linkage,
   deliverable specificity, and context quality.
2. Context-Aware (Not Keyword-Only): Synthesizes localized dialogue utterances,
   session boundaries, and speaker commitments rather than isolated strings.
3. Member 3 Independence: Member 3 source priority is strictly preserved as reference
   metadata and does NOT control or bias the Member 4 priority calculation.
4. Bounded & Reproducible: Continuous score bounded [0.0, 1.0]; categorical tiers
   (HIGH, MEDIUM, LOW) strictly aligned to configurable thresholds.
5. Conservative Linkage: Competing or ambiguous same-topic decisions are handled
   conservatively and not assumed to be supportive.
6. Zero LLM / Zero External APIs: 100% deterministic, local, and offline.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from .context_engine import build_task_context
from .schemas import (
    ContextRichActionItem,
    ContextRichDecision,
    Member4ContextOutput,
    Member4PriorityOutput,
    PriorityAssessment,
    PriorityEnrichedActionItem,
    PriorityFactorContribution,
    PriorityLevel,
    TopicContextStatus,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

class PriorityModelConfig(BaseModel):
    """
    Configurable weights and classification thresholds for the Priority Engine.
    Weights sum to 1.00.
    """
    model_config = ConfigDict(extra="ignore")

    # Factor Weights (sum = 1.00)
    weight_deadline_urgency: float = Field(default=0.25, description="Weight for temporal deadline urgency.")
    weight_explicit_urgency: float = Field(default=0.15, description="Weight for explicit urgency keywords.")
    weight_assignment_explicitness: float = Field(default=0.15, description="Weight for direct dialogue assignment.")
    weight_dependency_blocker: float = Field(default=0.15, description="Weight for blocker/milestone dependency.")
    weight_decision_linkage: float = Field(default=0.10, description="Weight for co-occurring key decisions.")
    weight_deliverable_specificity: float = Field(default=0.10, description="Weight for concrete operational deliverable.")
    weight_context_quality: float = Field(default=0.10, description="Weight for context resolution completeness.")

    # Classification Thresholds
    threshold_high: float = Field(default=0.65, description="Score threshold for HIGH priority tier.")
    threshold_medium: float = Field(default=0.35, description="Score threshold for MEDIUM priority tier.")


# Default instance
DEFAULT_CONFIG = PriorityModelConfig()


# ============================================================================
# FACTOR EVALUATION UTILITIES
# ============================================================================

def eval_deadline_urgency(
    item: ContextRichActionItem,
    weight: float,
) -> PriorityFactorContribution:
    """
    Evaluate temporal urgency based on explicit or ambiguous deadline evidence.
    Evaluates the task's assigned deadline string as primary evidence.
    """
    factor_name = "deadline_urgency"
    deadline_str = item.deadline
    snippet = (item.deadline_context_snippet or "").lower()

    if not deadline_str:
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=0.0,
            weight=weight,
            weighted_contribution=0.0,
            has_evidence=False,
            evidence_text="No deadline specified in source extraction.",
            evidence_segment_ids=[],
        )

    dl_lower = deadline_str.lower().strip()

    # 1. Distant deadline (weeks / next month) - checked directly on deadline string
    if any(k in dl_lower for k in ["next month", "in 3 weeks", "in 2 weeks", "next quarter", "months"]):
        raw_val = 0.15
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Distant deadline: '{deadline_str}'",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    # 2. Medium-term deadline (within a week / Friday / next Monday)
    if any(k in dl_lower for k in ["friday", "monday", "next week", "in a week", "by end of week"]):
        raw_val = 0.30
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Medium-term deadline: '{deadline_str}'",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    # 3. Near-term deadline (tomorrow / 1-2 days)
    if any(k in dl_lower for k in ["tomorrow", "by tomorrow", "1 day", "2 days"]):
        raw_val = 0.50
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Near-term deadline: '{deadline_str}'",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    # 4. Short-term deadline (same day / end of day / few hours)
    short_term_patterns = [
        r"\bthis afternoon\b",
        r"\bend of day\b",
        r"\bby tonight\b",
        r"\b(\d+)\s*(hours?|hrs?)\b",
    ]
    for pat in short_term_patterns:
        if re.search(pat, dl_lower):
            raw_val = 0.70
            return PriorityFactorContribution(
                factor_name=factor_name,
                raw_value=raw_val,
                weight=weight,
                weighted_contribution=round(raw_val * weight, 4),
                has_evidence=True,
                evidence_text=f"Short-term deadline: '{deadline_str}'",
                evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
            )

    # 5. Imminent / Immediate breakout deadline (<= 1 hour, today, immediately, or confirmed by snippet)
    imminent_patterns = [
        r"\b(\d+)\s*(mins?|minutes?)\b",
        r"\b(1|one)\s*(hour|hr)\b",
        r"\bimmediately\b",
        r"\btoday\b",
        r"\bbefore the next meeting\b",
    ]
    is_imminent = False
    for pat in imminent_patterns:
        if re.search(pat, dl_lower):
            is_imminent = True
            break
    if not is_imminent and "next meeting" in dl_lower and re.search(r"\b(\d+)\s*(mins?|minutes?)\b", snippet):
        is_imminent = True

    if is_imminent:
        raw_val = 0.95
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Imminent session deadline: '{deadline_str}'",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    # 6. Ambiguous deadline handled conservatively
    if item.is_ambiguous_deadline:
        if "asap" in dl_lower or "as soon as possible" in dl_lower:
            raw_val = 0.40
        elif "soon" in dl_lower:
            raw_val = 0.30
        else:
            raw_val = 0.10

        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Ambiguous temporal deadline: '{deadline_str}' (handled conservatively)",
            evidence_segment_ids=[],
        )

    # Default fallback for unrecognized non-empty string
    raw_val = 0.30
    return PriorityFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text=f"Standard deadline mention: '{deadline_str}'",
        evidence_segment_ids=[],
    )



def eval_explicit_urgency(
    item: ContextRichActionItem,
    weight: float,
) -> PriorityFactorContribution:
    """
    Scan task and localized context turns for explicit urgency indicators.
    Avoids overreacting to ordinary words.
    """
    factor_name = "explicit_urgency_language"
    task_lower = item.task.lower()
    window_lower = item.localized_context.window_text.lower() if item.localized_context else ""
    combined = f"{task_lower} {window_lower}"

    # Critical / High urgency terminology
    critical_terms = [
        "urgent", "urgently", "critical", "emergency", "immediately",
        "straight away", "top priority", "high priority", "right now"
    ]
    for term in critical_terms:
        if re.search(rf"\b{re.escape(term)}\b", combined):
            raw_val = 0.90
            return PriorityFactorContribution(
                factor_name=factor_name,
                raw_value=raw_val,
                weight=weight,
                weighted_contribution=round(raw_val * weight, 4),
                has_evidence=True,
                evidence_text=f"Explicit critical urgency term detected: '{term}'",
                evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
            )

    # Moderate urgency indicators
    moderate_terms = ["important", "crucial", "wrap up", "needed soon", "hurry", "vital"]
    for term in moderate_terms:
        if re.search(rf"\b{re.escape(term)}\b", combined):
            raw_val = 0.50
            return PriorityFactorContribution(
                factor_name=factor_name,
                raw_value=raw_val,
                weight=weight,
                weighted_contribution=round(raw_val * weight, 4),
                has_evidence=True,
                evidence_text=f"Moderate urgency indicator detected: '{term}'",
                evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
            )

    return PriorityFactorContribution(
        factor_name=factor_name,
        raw_value=0.0,
        weight=weight,
        weighted_contribution=0.0,
        has_evidence=False,
        evidence_text="No explicit urgency terminology detected.",
        evidence_segment_ids=[],
    )


def eval_assignment_explicitness(
    item: ContextRichActionItem,
    weight: float,
) -> PriorityFactorContribution:
    """
    Determine whether contextual dialogue contains evidence of an explicit direct assignment.
    Distinguishes responsible person from assignment speaker.
    """
    factor_name = "assignment_explicitness"

    if item.is_unassigned or not item.responsible_person:
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=0.0,
            weight=weight,
            weighted_contribution=0.0,
            has_evidence=False,
            evidence_text="Unassigned task; no specific owner established.",
            evidence_segment_ids=[],
        )

    person = item.responsible_person
    window = item.localized_context.window_text if item.localized_context else ""

    # Check for direct second-person or imperative address in dialogue
    direct_address_patterns = [
        r"\b(you're going to be|you will be|you need to|you'll be|your task is|i want you to)\b",
        r"\b(as the industrial designer|as the project manager|as the user interface)\b",
    ]
    target_name = item.display_name or person
    if target_name:
        escaped_name = re.escape(target_name)
        direct_address_patterns.append(
            rf"\b{escaped_name}\b.*?\b(work on|prepare|design|do|take care)\b"
        )
    has_direct_assignment = any(
        re.search(pat, window, re.IGNORECASE) for pat in direct_address_patterns
    )

    if has_direct_assignment:
        raw_val = 0.85
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Direct imperative assignment to '{person}' documented in dialogue turns.",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    # Check for first-person commitment / self-volunteer
    if any(k in window.lower() for k in ["i will", "i'll do", "i can do", "i'll prepare"]):
        raw_val = 0.50
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Self-commitment or passive assignment documented for '{person}'.",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    # Extraction attribution metadata only (no dialogue evidence)
    raw_val = 0.40
    return PriorityFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text=f"Task assigned to '{person}' in extraction metadata without explicit dialogue command.",
        evidence_segment_ids=[],
    )


def eval_dependency_blocker(
    item: ContextRichActionItem,
    weight: float,
) -> PriorityFactorContribution:
    """
    Detect explicit dependency, blocker, or sequential milestone commitments.
    Does NOT infer dependencies merely because two tasks share a topic.
    """
    factor_name = "dependency_blocker"
    task_lower = item.task.lower()
    window_lower = item.localized_context.window_text.lower() if item.localized_context else ""
    summary_lower = item.topic_summary.lower() if item.topic_summary else ""
    combined = f"{task_lower} {window_lower} {summary_lower}"

    # Critical blocker / hard dependency terminology
    blocker_patterns = [
        r"\b(blocker|blocking|prerequisite|depends on|dependency|can't proceed|cannot proceed|need this before|in order to start|first step)\b",
    ]
    for pat in blocker_patterns:
        m = re.search(pat, combined)
        if m:
            raw_val = 0.85
            return PriorityFactorContribution(
                factor_name=factor_name,
                raw_value=raw_val,
                weight=weight,
                weighted_contribution=round(raw_val * weight, 4),
                has_evidence=True,
                evidence_text=f"Direct dependency/blocker evidence detected: '{m.group(0)}'",
                evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
            )

    # Sequential breakout milestone prerequisite (e.g. "in between now and then")
    milestone_patterns = [
        r"\bin between now and then\b",
        r"\bbefore the next meeting\b",
        r"\bfor the next meeting\b",
        r"\bwhen we meet next\b",
        r"\breconvene\b",
    ]
    for pat in milestone_patterns:
        m = re.search(pat, combined)
        if m:
            raw_val = 0.60
            return PriorityFactorContribution(
                factor_name=factor_name,
                raw_value=raw_val,
                weight=weight,
                weighted_contribution=round(raw_val * weight, 4),
                has_evidence=True,
                evidence_text=f"Sequential milestone prerequisite: work required before reconvening meeting ('{m.group(0)}')",
                evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
            )

    return PriorityFactorContribution(
        factor_name=factor_name,
        raw_value=0.0,
        weight=weight,
        weighted_contribution=0.0,
        has_evidence=False,
        evidence_text="No explicit dependency or blocker evidence found in context.",
        evidence_segment_ids=[],
    )


def eval_decision_linkage(
    item: ContextRichActionItem,
    weight: float,
) -> PriorityFactorContribution:
    """
    Evaluate linkage to co-occurring decisions.
    IMPORTANT: Same-topic decisions are handled conservatively.
    Multiple decisions (e.g. Topic 10 contradictory mascot alternatives) are NOT
    treated as additive supporting evidence.
    """
    factor_name = "decision_linkage"
    num_decisions = len(item.related_decisions)

    if num_decisions == 0:
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=0.0,
            weight=weight,
            weighted_contribution=0.0,
            has_evidence=False,
            evidence_text="No key decisions linked to this topic.",
            evidence_segment_ids=[],
        )

    if num_decisions == 1:
        # Single aligned decision
        single_dec = item.related_decisions[0].decision
        raw_val = 0.40
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text=f"Single aligned decision linked: '{single_dec[:60]}...'",
            evidence_segment_ids=[],
        )

    # Multiple decisions in same topic: treat conservatively as potential alternatives / conflicting proposals
    raw_val = 0.20
    return PriorityFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text=f"Multiple same-topic decisions ({num_decisions}) detected representing potential alternatives/competing proposals; linkage weighted conservatively.",
        evidence_segment_ids=[],
    )


def eval_deliverable_specificity(
    item: ContextRichActionItem,
    weight: float,
) -> PriorityFactorContribution:
    """
    Evaluate whether task specifies a concrete, operationally defined deliverable
    versus an exploratory, open-ended intention.
    """
    factor_name = "deliverable_specificity"
    task_lower = item.task.lower()

    # Concrete operational deliverables (verbs + tangible artifacts)
    concrete_patterns = [
        r"\b(actual working design|design of the|casing drawings|layout|prototype|specification|manual|dimensions|calculate|measure|wiring|batteries|buttons)\b",
    ]
    if any(re.search(p, task_lower) for p in concrete_patterns):
        raw_val = 0.85
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text="Concrete operational deliverable with specific engineering artifact.",
            evidence_segment_ids=[],
        )

    # Exploratory / open-ended tasks
    exploratory_patterns = [
        r"\b(discuss|think about|consider|maybe look into|general presentation|chat with|ideas)\b",
    ]
    if any(re.search(p, task_lower) for p in exploratory_patterns):
        raw_val = 0.30
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text="Exploratory discussion or open-ended intention without tangible deliverable.",
            evidence_segment_ids=[],
        )

    # Standard actionable clarity
    raw_val = 0.55
    return PriorityFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=round(raw_val * weight, 4),
        has_evidence=True,
        evidence_text="Standard task operational clarity.",
        evidence_segment_ids=[],
    )


def eval_context_quality(
    item: ContextRichActionItem,
    weight: float,
) -> PriorityFactorContribution:
    """
    Assess the completeness of contextual evidence available for priority reasoning.
    """
    factor_name = "context_quality"

    if item.context_status == TopicContextStatus.RESOLVED:
        raw_val = 1.00
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text="Context fully resolved with localized dialogue turns and topic summary.",
            evidence_segment_ids=item.localized_context.segment_ids if item.localized_context else [],
        )

    if item.context_status == TopicContextStatus.PARTIALLY_RESOLVED:
        raw_val = 0.50
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=True,
            evidence_text="Topic summary available, but localized dialogue turns were absent.",
            evidence_segment_ids=[],
        )

    if item.context_status == TopicContextStatus.UNRESOLVED:
        raw_val = 0.20
        return PriorityFactorContribution(
            factor_name=factor_name,
            raw_value=raw_val,
            weight=weight,
            weighted_contribution=round(raw_val * weight, 4),
            has_evidence=False,
            evidence_text="Topic reference could not be resolved against Member 2 topic results.",
            evidence_segment_ids=[],
        )

    # MISSING_REFERENCE
    raw_val = 0.00
    return PriorityFactorContribution(
        factor_name=factor_name,
        raw_value=raw_val,
        weight=weight,
        weighted_contribution=0.0,
        has_evidence=False,
        evidence_text="No topic reference provided in extraction payload.",
        evidence_segment_ids=[],
    )


# ============================================================================
# PRIMARY PRIORITY ENGINE ENTRYPOINT
# ============================================================================

def infer_task_priorities(
    context_data: Union[Member4ContextOutput, Dict[str, Any], str, Path],
    member2_data: Optional[Union[Dict[str, Any], str, Path, List[Dict[str, Any]]]] = None,
    config: Optional[PriorityModelConfig] = None,
) -> Member4PriorityOutput:
    """
    Infer multi-factor priorities for context-rich tasks.

    Args:
        context_data: Phase 3 Member4ContextOutput, raw dict, or path to Member 3 JSON.
        member2_data: Optional Member 2 topic results (used if context needs to be built).
        config: Optional custom PriorityModelConfig weights and thresholds.

    Returns:
        Member4PriorityOutput containing priority-enriched action items and breakdown.
    """
    active_config = config or DEFAULT_CONFIG
    diagnostics: List[str] = []

    # ------------------------------------------------------------------------
    # 1. Ingest / Build Context Data
    # ------------------------------------------------------------------------
    if isinstance(context_data, Member4ContextOutput):
        ctx_output = context_data
    elif isinstance(context_data, dict) and context_data.get("processing_stage") == "member_4_context_enriched":
        ctx_output = Member4ContextOutput.model_validate(context_data)
    else:
        # Composable: build context from input
        ctx_output = build_task_context(context_data, member2_data=member2_data)

    meeting_id = ctx_output.meeting_id

    # ------------------------------------------------------------------------
    # 2. Evaluate Each Action Item
    # ------------------------------------------------------------------------
    enriched_items: List[PriorityEnrichedActionItem] = []
    scores: List[float] = []
    high_count = 0
    med_count = 0
    low_count = 0

    for item in ctx_output.action_items:
        # Evaluate all 7 candidate factors
        f_deadline = eval_deadline_urgency(item, active_config.weight_deadline_urgency)
        f_urgency = eval_explicit_urgency(item, active_config.weight_explicit_urgency)
        f_assign = eval_assignment_explicitness(item, active_config.weight_assignment_explicitness)
        f_depend = eval_dependency_blocker(item, active_config.weight_dependency_blocker)
        f_decis = eval_decision_linkage(item, active_config.weight_decision_linkage)
        f_spec = eval_deliverable_specificity(item, active_config.weight_deliverable_specificity)
        f_qual = eval_context_quality(item, active_config.weight_context_quality)

        factors = [f_deadline, f_urgency, f_assign, f_depend, f_decis, f_spec, f_qual]

        # Calculate continuous score: bounded sum of weighted contributions
        raw_score = sum(f.weighted_contribution for f in factors)
        score = round(max(0.0, min(1.0, raw_score)), 4)
        scores.append(score)

        # Categorical tier assignment strictly according to configured thresholds
        if score >= active_config.threshold_high:
            level = PriorityLevel.HIGH
            high_count += 1
        elif score >= active_config.threshold_medium:
            level = PriorityLevel.MEDIUM
            med_count += 1
        else:
            level = PriorityLevel.LOW
            low_count += 1

        scoring_breakdown = {f.factor_name: f.weighted_contribution for f in factors}
        evidence_summary = [f.evidence_text for f in factors if f.has_evidence and f.evidence_text]

        assessment = PriorityAssessment(
            score=score,
            level=level,
            factor_contributions=factors,
            scoring_breakdown=scoring_breakdown,
            evidence_summary=evidence_summary,
        )

        enriched_item = PriorityEnrichedActionItem(
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
            priority_assessment=assessment,
        )
        enriched_items.append(enriched_item)

    # ------------------------------------------------------------------------
    # 3. Assemble Output Summary
    # ------------------------------------------------------------------------
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    return Member4PriorityOutput(
        meeting_id=meeting_id,
        processing_stage="member_4_priority_enriched",
        total_action_items=len(enriched_items),
        high_priority_count=high_count,
        medium_priority_count=med_count,
        low_priority_count=low_count,
        min_score=min_score,
        max_score=max_score,
        avg_score=avg_score,
        action_items=enriched_items,
        speakers=getattr(ctx_output, "speakers", {}),
        key_decisions=ctx_output.key_decisions,
        diagnostics=diagnostics,
    )
