"""
Member 4 Contextual Task Intelligence Engine (Phase 3).

Transforms Phase 2 normalized action items and decisions into context-rich
representations by synthesizing topic-level summaries, localized dialogue
utterance windows (+/-2 turns), temporal anchors, speaker rosters, and
co-occurring decisions sharing the same topic reference.

Core Guarantees:
1. Grounded Context: Anchors tasks to Member 2 topic summaries, speakers, and timestamps.
2. Localized Dialogue Window: Deterministically extracts triggering segment +/-2 utterances.
3. Decision Association: Links co-occurring decisions established within the same topic.
4. Transparent Quality: Categorizes context as RESOLVED, PARTIALLY_RESOLVED, UNRESOLVED, or MISSING_REFERENCE.
5. Non-Destructive: Preserves normalized task text, assignee, deadline, and source metadata.
6. Zero LLM / Zero Models: 100% deterministic, local, and offline execution.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .normalizer import normalize_member3_input
from .schemas import (
    ContextRichActionItem,
    ContextRichDecision,
    LocalizedDialogueContext,
    Member2TopicContextInput,
    Member2TranscriptSegment,
    Member4ContextOutput,
    Member4NormalizedOutput,
    NormalizedActionItem,
    NormalizedDecision,
    RelatedDecisionContext,
    TopicContextStatus,
)


# ============================================================================
# CONSTANTS
# ============================================================================

# Common stopwords to ignore during deterministic segment keyword matching
STOPWORDS: Set[str] = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was",
    "will", "have", "has", "had", "about", "what", "which", "when",
    "where", "who", "whom", "how", "been", "being", "were", "they",
    "them", "their", "there", "then", "into", "onto", "your", "ours",
    "shall", "should", "could", "would", "does", "done", "doing",
}

# Window size: triggering utterance plus up to +/-2 neighboring turns
DEFAULT_WINDOW_RADIUS: int = 2


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_keywords(text: Optional[str]) -> Set[str]:
    """
    Extract alphanumeric tokens of length >= 3, excluding common stopwords.
    """
    if not text:
        return set()
    tokens = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
    return {tok for tok in tokens if tok not in STOPWORDS}


def find_triggering_segment(
    segments: List[Member2TranscriptSegment],
    task_text: str,
    deadline_text: Optional[str] = None,
    assignee_label: Optional[str] = None,
) -> Tuple[int, Optional[Member2TranscriptSegment]]:
    """
    Deterministically find the index of the segment within a topic that most
    closely triggers or matches the task description.
    """
    if not segments:
        return 0, None

    task_keywords = extract_keywords(task_text)
    deadline_keywords = extract_keywords(deadline_text) if deadline_text else set()

    best_score = -1
    best_idx = 0

    for idx, seg in enumerate(segments):
        seg_text_lower = seg.text.lower()
        seg_keywords = extract_keywords(seg.text)

        # Lexical keyword overlap score
        overlap = len(task_keywords & seg_keywords)
        score = overlap * 3

        # Deadline keyword overlap bonus
        if deadline_keywords:
            dl_overlap = len(deadline_keywords & seg_keywords)
            score += dl_overlap * 2

        # Assignee speaker match bonus
        if assignee_label and seg.speaker.lower() == assignee_label.lower():
            score += 1

        # Check for imperative task markers
        if any(marker in seg_text_lower for marker in ["working on", "work on", "design", "make sure", "need to"]):
            score += 2

        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx, segments[best_idx]


def build_localized_window(
    segments: List[Member2TranscriptSegment],
    trigger_idx: int,
    radius: int = DEFAULT_WINDOW_RADIUS,
) -> LocalizedDialogueContext:
    """
    Extract a localized dialogue turn window around the triggering segment (+/- radius turns).
    """
    start_idx = max(0, trigger_idx - radius)
    end_idx = min(len(segments) - 1, trigger_idx + radius)
    window_segs = segments[start_idx : end_idx + 1]

    # Format dialogue turns
    dialogue_lines = [f"{s.speaker}: {s.text.strip()}" for s in window_segs if s.text.strip()]
    window_text = "\n".join(dialogue_lines)

    segment_ids = [s.segment_id for s in window_segs]
    trigger_seg_id = segments[trigger_idx].segment_id if segments else None

    speakers = list(dict.fromkeys(s.speaker for s in window_segs if s.speaker))

    # Timestamp boundaries
    start_time = window_segs[0].start if window_segs and window_segs[0].start is not None else None
    end_time = window_segs[-1].end if window_segs and window_segs[-1].end is not None else None

    return LocalizedDialogueContext(
        window_text=window_text,
        segment_ids=segment_ids,
        trigger_segment_id=trigger_seg_id,
        speakers=speakers,
        start=start_time,
        end=end_time,
    )


# ============================================================================
# PRIMARY CONTEXT ENGINE ENTRYPOINT
# ============================================================================

def build_task_context(
    normalized_data: Union[Member4NormalizedOutput, Dict[str, Any], str, Path],
    member2_data: Optional[Union[Dict[str, Any], str, Path, List[Dict[str, Any]]]] = None,
) -> Member4ContextOutput:
    """
    Synthesize topic-level summaries, localized dialogue windows, timestamps,
    and co-occurring decisions into context-rich representations.

    Args:
        normalized_data: Phase 2 normalized output, raw dict, or path to Member 3 JSON.
        member2_data: Optional Member 2 topic results dict, list of topics, or file path.

    Returns:
        Member4ContextOutput containing context-rich action items and decisions.
    """
    # ------------------------------------------------------------------------
    # 1. Ingest / Normalize Input
    # ------------------------------------------------------------------------
    diagnostics: List[str] = []

    if isinstance(normalized_data, Member4NormalizedOutput):
        norm_output = normalized_data
    elif isinstance(normalized_data, (str, Path, dict)):
        # Check if already normalized JSON dict
        if isinstance(normalized_data, dict) and normalized_data.get("processing_stage") == "member_4_normalized":
            norm_output = Member4NormalizedOutput.model_validate(normalized_data)
        else:
            # Run normalization on raw Member 3 input
            norm_output = normalize_member3_input(normalized_data, member2_data=member2_data)
    else:
        raise TypeError(f"Unsupported normalized_data type: {type(normalized_data)}")

    meeting_id = norm_output.meeting_id

    # ------------------------------------------------------------------------
    # 2. Build Topic Context Dictionary from Member 2
    # ------------------------------------------------------------------------
    topics_by_id: Dict[int, Member2TopicContextInput] = {}

    # Check if topics were already attached in normalized output
    for item in norm_output.action_items:
        if item.topic_context and item.topic_context.topic_id not in topics_by_id:
            topics_by_id[item.topic_context.topic_id] = item.topic_context

    # Ingest direct member2_data if provided
    if member2_data is not None:
        raw_m2 = None
        if isinstance(member2_data, (str, Path)):
            p2 = Path(member2_data)
            if p2.exists():
                with open(p2, "r", encoding="utf-8") as f:
                    raw_m2 = json.load(f)
            else:
                diagnostics.append(f"Member 2 context file not found: {p2}")
        elif isinstance(member2_data, dict):
            raw_m2 = member2_data
        elif isinstance(member2_data, list):
            raw_m2 = {"topics": member2_data}

        if raw_m2 and isinstance(raw_m2, dict):
            for t in raw_m2.get("topics", []):
                if isinstance(t, dict) and "topic_id" in t:
                    try:
                        parsed = Member2TopicContextInput.model_validate(t)
                        topics_by_id[parsed.topic_id] = parsed
                    except Exception as e:
                        diagnostics.append(f"Error parsing Member 2 topic: {e}")

    # ------------------------------------------------------------------------
    # 3. Index Normalized Decisions by topic_reference
    # ------------------------------------------------------------------------
    decisions_by_topic: Dict[int, List[RelatedDecisionContext]] = {}
    for dec in norm_output.key_decisions:
        if dec.topic_reference is not None:
            rel = RelatedDecisionContext(
                decision_id=dec.decision_id,
                decision=dec.decision,
                topic_reference=dec.topic_reference,
            )
            decisions_by_topic.setdefault(dec.topic_reference, []).append(rel)

    # ------------------------------------------------------------------------
    # 4. Contextualize Action Items
    # ------------------------------------------------------------------------
    context_rich_action_items: List[ContextRichActionItem] = []
    resolved_topics_count = 0
    partially_resolved_count = 0
    unresolved_topics_count = 0
    missing_topics_count = 0
    items_with_localized_context = 0
    items_with_related_decisions = 0

    for item in norm_output.action_items:
        t_ref = item.topic_reference
        item_diag: List[str] = list(item.validation_diagnostics)

        topic_summary = None
        topic_speakers: List[str] = []
        context_start = None
        context_end = None
        localized_ctx: Optional[LocalizedDialogueContext] = None
        deadline_snippet: Optional[str] = None

        if t_ref is None:
            status = TopicContextStatus.MISSING_REFERENCE
            missing_topics_count += 1
            item_diag.append("Missing topic_reference: No topic context can be attached.")
        elif t_ref not in topics_by_id:
            status = TopicContextStatus.UNRESOLVED
            unresolved_topics_count += 1
            item_diag.append(f"Unresolved topic_reference {t_ref}: Topic not found in Member 2 data.")
        else:
            topic = topics_by_id[t_ref]
            topic_summary = topic.summary
            topic_speakers = list(topic.speakers)
            context_start = topic.start
            context_end = topic.end

            if not topic.segments:
                # Topic summary is available, but individual segment turns are missing
                status = TopicContextStatus.PARTIALLY_RESOLVED
                partially_resolved_count += 1
                item_diag.append("Topic resolved but source segment details are unavailable.")
            else:
                status = TopicContextStatus.RESOLVED
                resolved_topics_count += 1

                # Localized +/-2 segment window extraction
                trigger_idx, trigger_seg = find_triggering_segment(
                    topic.segments,
                    task_text=item.task,
                    deadline_text=item.deadline,
                    assignee_label=item.responsible_person,
                )
                localized_ctx = build_localized_window(topic.segments, trigger_idx)
                items_with_localized_context += 1

                # Update context start/end with the precise localized window timestamps
                if localized_ctx.start is not None:
                    context_start = localized_ctx.start
                if localized_ctx.end is not None:
                    context_end = localized_ctx.end

                # Deadline snippet extraction if deadline is present
                if item.deadline and localized_ctx:
                    dl_lower = item.deadline.lower()
                    for seg in topic.segments:
                        if dl_lower in seg.text.lower() or any(
                            kw in seg.text.lower() for kw in extract_keywords(item.deadline)
                        ):
                            deadline_snippet = f"{seg.speaker}: {seg.text.strip()}"
                            break

        # Associate co-occurring decisions from the same topic
        related_decs = decisions_by_topic.get(t_ref, []) if t_ref is not None else []
        if related_decs:
            items_with_related_decisions += 1

        rich_item = ContextRichActionItem(
            item_id=item.item_id,
            task=item.task,
            responsible_person=item.responsible_person,
            speaker_id=item.speaker_id,
            display_name=item.display_name,
            name_source=item.name_source,
            is_unassigned=item.is_unassigned,
            deadline=item.deadline,
            is_ambiguous_deadline=item.is_ambiguous_deadline,
            topic_reference=t_ref,
            context_status=status,
            topic_summary=topic_summary,
            topic_speakers=topic_speakers,
            localized_context=localized_ctx,
            context_start=context_start,
            context_end=context_end,
            related_decisions=related_decs,
            deadline_context_snippet=deadline_snippet,
            source_priority=item.source_priority,
            source_confidence_score=item.source_confidence_score,
            is_duplicate=item.is_duplicate,
            duplicate_of=item.duplicate_of,
            context_diagnostics=item_diag,
        )
        context_rich_action_items.append(rich_item)

    # ------------------------------------------------------------------------
    # 5. Contextualize Key Decisions
    # ------------------------------------------------------------------------
    context_rich_decisions: List[ContextRichDecision] = []

    for dec in norm_output.key_decisions:
        t_ref = dec.topic_reference
        dec_diag: List[str] = list(dec.validation_diagnostics)

        topic_summary = None
        topic_speakers: List[str] = []
        context_start = None
        context_end = None
        localized_ctx = None

        if t_ref is None:
            status = TopicContextStatus.MISSING_REFERENCE
            dec_diag.append("Missing topic_reference: No topic context can be attached.")
        elif t_ref not in topics_by_id:
            status = TopicContextStatus.UNRESOLVED
            dec_diag.append(f"Unresolved topic_reference {t_ref}: Topic not found in Member 2 data.")
        else:
            topic = topics_by_id[t_ref]
            topic_summary = topic.summary
            topic_speakers = list(topic.speakers)
            context_start = topic.start
            context_end = topic.end

            if not topic.segments:
                status = TopicContextStatus.PARTIALLY_RESOLVED
            else:
                status = TopicContextStatus.RESOLVED
                trigger_idx, _ = find_triggering_segment(topic.segments, task_text=dec.decision)
                localized_ctx = build_localized_window(topic.segments, trigger_idx)
                if localized_ctx.start is not None:
                    context_start = localized_ctx.start
                if localized_ctx.end is not None:
                    context_end = localized_ctx.end

        rich_dec = ContextRichDecision(
            decision_id=dec.decision_id,
            decision=dec.decision,
            topic_reference=t_ref,
            context_status=status,
            topic_summary=topic_summary,
            topic_speakers=topic_speakers,
            localized_context=localized_ctx,
            context_start=context_start,
            context_end=context_end,
            context_diagnostics=dec_diag,
        )
        context_rich_decisions.append(rich_dec)

    # ------------------------------------------------------------------------
    # 6. Build Final Context Output
    # ------------------------------------------------------------------------
    return Member4ContextOutput(
        meeting_id=meeting_id,
        processing_stage="member_4_context_enriched",
        total_action_items=len(context_rich_action_items),
        total_decisions=len(context_rich_decisions),
        resolved_topics_count=resolved_topics_count,
        partially_resolved_count=partially_resolved_count,
        unresolved_topics_count=unresolved_topics_count,
        missing_topics_count=missing_topics_count,
        items_with_localized_context=items_with_localized_context,
        items_with_related_decisions=items_with_related_decisions,
        speakers=getattr(norm_output, "speakers", {}),
        action_items=context_rich_action_items,
        key_decisions=context_rich_decisions,
        diagnostics=diagnostics,
    )
