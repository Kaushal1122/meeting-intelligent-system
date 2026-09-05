"""
Phase 7: Explainability Engine for Member 4.

Provides deterministic, read-only multi-factor explainability and evidence traceability
for Member 4 intelligence outputs. Answers:
"WHY did the system assign this priority, confidence, and human-review status?"

Consumes Phase 6 Triage-Enriched action items without altering any priority scores,
confidence scores, review statuses, or reason codes.
Strictly deterministic, zero LLM calls, zero network dependencies.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.member4.review_engine import triage_action_items
from backend.member4.schemas import (
    ActionItemExplanation,
    ConfidenceAssessment,
    ConfidenceExplainability,
    ConfidenceFactorContribution,
    ConfidenceLevel,
    EvidenceReference,
    ExplainedActionItem,
    ExplanationFactor,
    Member4ExplainedOutput,
    Member4TriageOutput,
    PriorityAssessment,
    PriorityExplainability,
    PriorityFactorContribution,
    PriorityLevel,
    ReviewDecision,
    ReviewExplainability,
    ReviewReasonCode,
    ReviewStatus,
    TopicContextStatus,
    TriageEnrichedActionItem,
)


def rank_explanation_factors(factors: List[ExplanationFactor]) -> List[ExplanationFactor]:
    """
    Deterministically rank factors by weighted contribution descending.
    Tie-breaker: factor_name ascending (alphabetical).
    """
    return sorted(
        factors,
        key=lambda f: (-f.weighted_contribution, f.factor_name),
    )


def explain_priority(item: TriageEnrichedActionItem) -> PriorityExplainability:
    """
    Construct read-only explainability trail for Phase 4 Priority score.
    Does NOT recalculate or modify the priority score.
    """
    p_assess = item.priority_assessment
    score = p_assess.score
    level = p_assess.level

    explanation_factors: List[ExplanationFactor] = []
    supporting_evidence: List[str] = []
    limiting_factors: List[str] = []

    for fc in p_assess.factor_contributions:
        # Determine factor interpretation
        if fc.weighted_contribution >= 0.15:
            interpretation = f"Strong driver (+{fc.weighted_contribution:.4f}): {fc.evidence_text or 'Substantial positive contribution.'}"
        elif fc.weighted_contribution > 0.05:
            interpretation = f"Moderate contributor (+{fc.weighted_contribution:.4f}): {fc.evidence_text or 'Moderate positive contribution.'}"
        elif fc.weighted_contribution > 0.0:
            interpretation = f"Minor contributor (+{fc.weighted_contribution:.4f}): {fc.evidence_text or 'Slight positive contribution.'}"
        else:
            interpretation = f"Neutral / zero contribution (+0.0000): {fc.evidence_text or 'No explicit evidence detected.'}"

        ef = ExplanationFactor(
            factor_name=fc.factor_name,
            raw_value=fc.raw_value,
            weight=fc.weight,
            weighted_contribution=fc.weighted_contribution,
            interpretation=interpretation,
            evidence_text=fc.evidence_text,
            evidence_segment_ids=fc.evidence_segment_ids,
        )
        explanation_factors.append(ef)

        if fc.weighted_contribution >= 0.05:
            supporting_evidence.append(f"{fc.factor_name} (+{fc.weighted_contribution:.4f}): {fc.evidence_text}")
        elif fc.weighted_contribution == 0.0 and fc.factor_name in [
            "deadline_urgency", "explicit_urgency_language", "dependency_blocker"
        ]:
            limiting_factors.append(f"No {fc.factor_name.replace('_', ' ')} detected (+0.0000).")

    # Deterministic ranking
    ranked_factors = rank_explanation_factors(explanation_factors)
    top_contributors = [f for f in ranked_factors if f.weighted_contribution > 0.0]

    # Synthesize concise explanation text
    top_names = [f"{f.factor_name} (+{f.weighted_contribution:.4f})" for f in top_contributors[:3]]
    if top_names:
        explanation_text = (
            f"Priority is {level.value} (score: {score:.4f}), driven primarily by "
            f"{', '.join(top_names)}."
        )
    else:
        explanation_text = (
            f"Priority is {level.value} (score: {score:.4f}) due to absence of urgent deadlines, "
            f"critical keywords, or sequential blocker dependencies."
        )

    return PriorityExplainability(
        score=score,
        level=level,
        factors=explanation_factors,
        top_contributors=top_contributors,
        supporting_evidence=supporting_evidence,
        limiting_factors=limiting_factors,
        explanation_text=explanation_text,
    )


def explain_confidence(item: TriageEnrichedActionItem) -> ConfidenceExplainability:
    """
    Construct read-only explainability trail for Phase 5 Confidence score.
    Does NOT recalculate or modify the confidence score.
    """
    c_assess = item.confidence_assessment
    score = c_assess.score
    level = c_assess.level

    explanation_factors: List[ExplanationFactor] = []
    supporting_evidence: List[str] = []
    limiting_evidence: List[str] = []

    for fc in c_assess.factor_contributions:
        if fc.raw_value >= 0.80:
            interpretation = f"High reliability (+{fc.weighted_contribution:.4f}): {fc.evidence_text or 'Strong evidence corroboration.'}"
        elif fc.raw_value >= 0.50:
            interpretation = f"Moderate reliability (+{fc.weighted_contribution:.4f}): {fc.evidence_text or 'Standard baseline or partial evidence.'}"
        else:
            interpretation = f"Uncertainty signal (+{fc.weighted_contribution:.4f}): {fc.evidence_text or 'Weak grounding or competing alternatives.'}"

        ef = ExplanationFactor(
            factor_name=fc.factor_name,
            raw_value=fc.raw_value,
            weight=fc.weight,
            weighted_contribution=fc.weighted_contribution,
            interpretation=interpretation,
            evidence_text=fc.evidence_text,
            evidence_segment_ids=fc.evidence_segment_ids,
        )
        explanation_factors.append(ef)

        if fc.raw_value >= 0.70 and fc.has_evidence:
            supporting_evidence.append(f"{fc.factor_name} (+{fc.weighted_contribution:.4f}): {fc.evidence_text}")
        elif fc.raw_value < 0.50:
            limiting_evidence.append(f"{fc.factor_name} (+{fc.weighted_contribution:.4f}): {fc.evidence_text}")
        elif fc.raw_value <= 0.65 and not fc.has_evidence:
            # Document neutral unpenalized missing information accurately
            pass

    ranked_factors = rank_explanation_factors(explanation_factors)
    top_contributors = [f for f in ranked_factors if f.weighted_contribution >= 0.08]

    top_names = [f"{f.factor_name} (+{f.weighted_contribution:.4f})" for f in ranked_factors[:3]]
    if limiting_evidence:
        lim_summary = f" Limited by: {limiting_evidence[0]}."
    else:
        lim_summary = " Zero material evidence gaps detected."

    explanation_text = (
        f"Confidence is {level.value} (score: {score:.4f}), supported by {', '.join(top_names)}."
        f"{lim_summary}"
    )

    return ConfidenceExplainability(
        score=score,
        level=level,
        factors=explanation_factors,
        top_contributors=top_contributors,
        supporting_evidence=supporting_evidence,
        limiting_evidence=limiting_evidence,
        explanation_text=explanation_text,
    )


def explain_review(item: TriageEnrichedActionItem) -> ReviewExplainability:
    """
    Construct read-only explainability trail for Phase 6 Human Review decision.
    Does NOT modify review status or reason codes.
    """
    r_dec = item.review_decision
    status = r_dec.status
    reason_codes = r_dec.reason_codes

    if status == ReviewStatus.AUTO_ACCEPT:
        explanation_text = (
            "Review status is AUTO_ACCEPT: Evidence is sufficiently strong across dialogue "
            "and topic grounding with zero material uncertainty signals."
        )
    elif status == ReviewStatus.REVIEW_RECOMMENDED:
        code_str = ", ".join([c.value for c in reason_codes])
        explanation_text = (
            f"Review status is REVIEW_RECOMMENDED: Item is operationally usable but exhibits "
            f"moderate uncertainty signals ({code_str}). {r_dec.explanation}"
        )
    else:  # REVIEW_REQUIRED
        code_str = ", ".join([c.value for c in reason_codes])
        explanation_text = (
            f"Review status is REVIEW_REQUIRED: Mandatory human verification is required due to "
            f"critical evidence gaps or high operational risk ({code_str}). {r_dec.explanation}"
        )

    return ReviewExplainability(
        status=status,
        review_required=r_dec.review_required,
        review_recommended=r_dec.review_recommended,
        reason_codes=reason_codes,
        evidence_flags=r_dec.evidence_flags,
        explanation_text=explanation_text,
    )


def extract_evidence_traces(item: TriageEnrichedActionItem) -> List[EvidenceReference]:
    """
    Extract concrete, verifiable provenance references pointing to source artifacts.
    Does NOT invent fake quotes, synthetic speakers, or unverified timestamps.
    """
    traces: List[EvidenceReference] = []

    # 1. Topic Reference
    if item.topic_reference is not None:
        traces.append(
            EvidenceReference(
                source_type="topic",
                source_id=item.topic_reference,
                speaker=item.topic_speakers[0] if item.topic_speakers else None,
                start_time=item.context_start,
                end_time=item.context_end,
                text_excerpt=item.topic_summary[:150] if item.topic_summary else None,
            )
        )

    # 2. Localized Dialogue Window Turns
    if item.localized_context and item.localized_context.segment_ids:
        # Include first segment reference
        traces.append(
            EvidenceReference(
                source_type="transcript_segment",
                source_id=item.localized_context.segment_ids[0],
                speaker=item.localized_context.speakers[0] if item.localized_context.speakers else None,
                start_time=item.context_start,
                end_time=item.context_end,
                text_excerpt=item.localized_context.window_text[:150] if item.localized_context.window_text else None,
            )
        )

    # 3. Deadline Utterance Snippet
    if item.deadline_context_snippet:
        traces.append(
            EvidenceReference(
                source_type="deadline",
                source_id=item.deadline,
                speaker=None,
                start_time=None,
                end_time=None,
                text_excerpt=item.deadline_context_snippet[:150],
            )
        )

    # 4. Related Key Decisions
    for dec in item.related_decisions:
        traces.append(
            EvidenceReference(
                source_type="decision",
                source_id=dec.topic_reference,
                speaker=None,
                start_time=None,
                end_time=None,
                text_excerpt=dec.decision[:150],
            )
        )

    return traces


def explain_action_item(item: TriageEnrichedActionItem) -> ActionItemExplanation:
    """
    Synthesize complete multi-dimensional explainability object for an action item.
    """
    p_exp = explain_priority(item)
    c_exp = explain_confidence(item)
    r_exp = explain_review(item)
    traces = extract_evidence_traces(item)

    # Build unified natural-language synthesis
    unified_explanation = (
        f"Item '{item.item_id}': Priority is {p_exp.level.value} ({p_exp.score:.4f}) and "
        f"Confidence is {c_exp.level.value} ({c_exp.score:.4f}). "
        f"Triage decision is {r_exp.status.value}. "
        f"{p_exp.explanation_text} {c_exp.explanation_text}"
    )

    return ActionItemExplanation(
        item_id=item.item_id,
        task=item.task,
        priority_explanation=p_exp,
        confidence_explanation=c_exp,
        review_explanation=r_exp,
        evidence_traces=traces,
        unified_explanation=unified_explanation,
    )


def explain_meeting_triage(
    triage_output: Union[Member4TriageOutput, dict, str, Path],
    member2_data: Optional[Union[dict, str, Path]] = None,
) -> Member4ExplainedOutput:
    """
    Top-level entry point for Phase 7 Explainability Engine.

    Consumes Member4TriageOutput (or runs Phases 1–6 upstream if raw payload is given)
    and produces fully explained action items with mathematical audit trails.
    """
    if not isinstance(triage_output, Member4TriageOutput):
        triage_res = triage_action_items(triage_output, member2_data=member2_data)
    else:
        triage_res = triage_output

    explained_items: List[ExplainedActionItem] = []

    for item in triage_res.action_items:
        # Capture pre-explanation values to verify zero decision drift
        orig_p_score = item.priority_assessment.score
        orig_p_level = item.priority_assessment.level
        orig_c_score = item.confidence_assessment.score
        orig_c_level = item.confidence_assessment.level
        orig_status = item.review_decision.status
        orig_codes = list(item.review_decision.reason_codes)

        explanation = explain_action_item(item)

        # Verify mathematical consistency
        p_contrib_sum = round(sum(f.weighted_contribution for f in explanation.priority_explanation.factors), 4)
        assert abs(p_contrib_sum - orig_p_score) <= 1e-4, (
            f"Priority mathematical inconsistency: sum={p_contrib_sum} vs score={orig_p_score}"
        )

        c_contrib_sum = round(sum(f.weighted_contribution for f in explanation.confidence_explanation.factors), 4)
        assert abs(c_contrib_sum - orig_c_score) <= 1e-4, (
            f"Confidence mathematical inconsistency: sum={c_contrib_sum} vs score={orig_c_score}"
        )

        # Verify zero decision drift
        assert orig_p_score == item.priority_assessment.score, "Decision drift detected: priority score modified!"
        assert orig_p_level == item.priority_assessment.level, "Decision drift detected: priority level modified!"
        assert orig_c_score == item.confidence_assessment.score, "Decision drift detected: confidence score modified!"
        assert orig_c_level == item.confidence_assessment.level, "Decision drift detected: confidence level modified!"
        assert orig_status == item.review_decision.status, "Decision drift detected: review status modified!"
        assert orig_codes == item.review_decision.reason_codes, "Decision drift detected: reason codes modified!"

        explained_item = ExplainedActionItem(
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
            review_decision=item.review_decision,
            explanation=explanation,
        )
        explained_items.append(explained_item)

    return Member4ExplainedOutput(
        meeting_id=triage_res.meeting_id,
        processing_stage="member_4_explained",
        total_action_items=triage_res.total_action_items,
        auto_accept_count=triage_res.auto_accept_count,
        review_recommended_count=triage_res.review_recommended_count,
        review_required_count=triage_res.review_required_count,
        explained_action_items_count=len(explained_items),
        action_items=explained_items,
        speakers=getattr(triage_res, "speakers", {}),
        key_decisions=triage_res.key_decisions,
        diagnostics=triage_res.diagnostics,
    )
