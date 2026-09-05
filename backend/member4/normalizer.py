"""
Member 4 Validation & Normalization Module (Phase 2).

Transforms raw Member 3 extraction payloads into clean, validated,
and context-enriched internal representations for downstream intelligence layers.

Core Guarantees:
1. Strict Validation: Invalid or empty task strings are rejected deterministically.
2. Attribution Grounding: Unassigned/unknown persons remain None; no identities are invented.
3. Deadline Safety: Meaningful timeframes are preserved; ambiguous deadlines are flagged; no fake dates.
4. Topic Reference Resolution: Reconciles Member 3 topic_reference with Member 2 topic context if provided.
5. Deterministic Deduplication: Identifies duplicate action items without destroying records.
6. Source Independence: Preserves Member 3 priority & confidence strictly as source metadata.
7. Zero External Calls: No LLM, no model inference, no network access.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .schemas import (
    Member2TopicContextInput,
    Member4ActionItemInput,
    Member4DecisionInput,
    Member4Input,
    Member4NormalizedOutput,
    NormalizedActionItem,
    NormalizedDecision,
    TopicContextStatus,
    SpeakerIdentity,
)
from .speaker_resolver import resolve_meeting_speakers


# ============================================================================
# CONSTANTS & FILTER PATTERNS
# ============================================================================

# Missing assignee indicator strings
UNASSIGNED_MARKERS = {
    "",
    "none",
    "null",
    "unknown",
    "unassigned",
    "n/a",
    "nobody",
    "no one",
    "tbd",
    "not specified",
}

# Missing deadline indicator strings
MISSING_DEADLINE_MARKERS = {
    "",
    "none",
    "none mentioned",
    "null",
    "n/a",
    "tbd",
    "no deadline",
    "not mentioned",
    "unspecified",
}

# Ambiguous / vague temporal keywords that do not specify a clear deadline
AMBIGUOUS_DEADLINE_PATTERNS = [
    r"\bsoon\b",
    r"\basap\b",
    r"\bas soon as possible\b",
    r"\blater\b",
    r"\bsometime\b",
    r"\bin the future\b",
    r"\bat some point\b",
    r"\bwhenever\b",
    r"\beventually\b",
    r"\bdown the line\b",
]


# ============================================================================
# HELPER NORMALIZATION UTILITIES
# ============================================================================

def clean_whitespace(text: Optional[str]) -> str:
    """Collapse multiple spaces, tabs, and newlines into a single clean string."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_person(raw_person: Optional[str]) -> Tuple[Optional[str], bool, List[str]]:
    """
    Normalize responsible person string.
    Returns: (normalized_name, is_unassigned, diagnostics)
    """
    diagnostics = []
    if raw_person is None:
        return None, True, ["Unassigned responsible person"]

    cleaned = clean_whitespace(raw_person)
    if cleaned.lower() in UNASSIGNED_MARKERS:
        return None, True, ["Unassigned responsible person"]

    # Trim accidental outer quotes
    cleaned = cleaned.strip("\"'")
    return cleaned, False, diagnostics


def normalize_deadline(raw_deadline: Optional[str]) -> Tuple[Optional[str], bool, List[str]]:
    """
    Normalize deadline string.
    Returns: (normalized_deadline, is_ambiguous, diagnostics)
    """
    diagnostics = []
    if raw_deadline is None:
        return None, False, []

    cleaned = clean_whitespace(raw_deadline)
    cleaned_lower = cleaned.lower()

    if cleaned_lower in MISSING_DEADLINE_MARKERS:
        return None, False, []

    # Check for ambiguous / vague temporal markers
    is_ambiguous = any(
        re.search(pattern, cleaned_lower) for pattern in AMBIGUOUS_DEADLINE_PATTERNS
    )
    if is_ambiguous:
        diagnostics.append(f"Ambiguous deadline timeframe: '{cleaned}'")

    return cleaned, is_ambiguous, diagnostics


def make_canonical_signature(task: str, person: Optional[str], topic_ref: Optional[int]) -> Tuple[str, str, Optional[int]]:
    """
    Generate a normalized tuple key for deterministic duplicate detection.
    Strips punctuation and lowercases task and person.
    """
    norm_task = re.sub(r"[^\w\s]", "", task.lower())
    norm_task = re.sub(r"\s+", " ", norm_task).strip()
    norm_person = person.lower() if person else "none"
    return (norm_task, norm_person, topic_ref)


# ============================================================================
# PRIMARY NORMALIZATION ENTRYPOINT
# ============================================================================

def normalize_member3_input(
    member3_data: Union[Dict[str, Any], Member4Input, str, Path],
    member2_data: Optional[Union[Dict[str, Any], str, Path, List[Dict[str, Any]]]] = None,
    strict: bool = False,
) -> Member4NormalizedOutput:
    """
    Normalize Member 3 extractions into a clean, validated internal representation.

    Args:
        member3_data: Member 3 JSON dict, Member4Input object, or file path.
        member2_data: Optional Member 2 topic results dict, list of topics, or file path.
        strict: If True, raises ValueError on invalid items; if False, records rejected items.

    Returns:
        Member4NormalizedOutput containing clean action items, decisions, and diagnostics.
    """
    diagnostics: List[str] = []

    # ------------------------------------------------------------------------
    # 1. Ingest Member 3 Data
    # ------------------------------------------------------------------------
    if isinstance(member3_data, (str, Path)):
        p = Path(member3_data)
        if not p.exists():
            raise FileNotFoundError(f"Member 3 input file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            raw_m3 = json.load(f)
    elif isinstance(member3_data, Member4Input):
        raw_m3 = member3_data.model_dump()
    elif isinstance(member3_data, dict):
        raw_m3 = member3_data
    else:
        raise TypeError(f"Unsupported member3_data type: {type(member3_data)}")

    meeting_id = clean_whitespace(raw_m3.get("meeting_id"))
    if not meeting_id:
        raise ValueError("meeting_id cannot be empty or missing in Member 3 payload.")

    # ------------------------------------------------------------------------
    # 2. Ingest Optional Member 2 Topic Context
    # ------------------------------------------------------------------------
    topics_by_id: Dict[int, Member2TopicContextInput] = {}
    member2_context_enriched = False
    raw_m2 = None

    if member2_data is not None:
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
            raw_topics = raw_m2.get("topics", [])
            for t in raw_topics:
                if isinstance(t, dict) and "topic_id" in t:
                    try:
                        parsed_topic = Member2TopicContextInput.model_validate(t)
                        topics_by_id[parsed_topic.topic_id] = parsed_topic
                    except Exception as e:
                        diagnostics.append(f"Failed to parse Member 2 topic: {e}")

            if topics_by_id:
                member2_context_enriched = True
                diagnostics.append(
                    f"Successfully loaded {len(topics_by_id)} topics from Member 2 context."
                )

    # ------------------------------------------------------------------------
    # 2.5 Resolve Speaker Identities
    # ------------------------------------------------------------------------
    speaker_registry: Dict[str, SpeakerIdentity] = {}
    if member2_data is not None or raw_m2:
        try:
            speaker_registry = resolve_meeting_speakers(raw_m2 if raw_m2 is not None else member2_data)
            if speaker_registry:
                diagnostics.append(
                    f"Resolved {len(speaker_registry)} speaker identities ({sum(1 for s in speaker_registry.values() if s.name_source == 'explicit_transcript')} explicit names)."
                )
        except Exception as e:
            diagnostics.append(f"Failed to resolve speakers: {e}")

    # ------------------------------------------------------------------------
    # 3. Process Action Items
    # ------------------------------------------------------------------------
    raw_action_items = raw_m3.get("action_items", [])
    normalized_action_items: List[NormalizedActionItem] = []
    rejected_items: List[Dict[str, Any]] = []
    seen_signatures: Dict[Tuple[str, str, Optional[int]], str] = {}
    duplicates_detected = 0
    unresolved_topics_count = 0

    item_idx = 1
    for raw_item in raw_action_items:
        if not isinstance(raw_item, dict):
            if hasattr(raw_item, "model_dump"):
                raw_item = raw_item.model_dump()
            else:
                continue

        raw_task = raw_item.get("task")
        cleaned_task = clean_whitespace(raw_task)

        # Validation: check for empty or whitespace-only task description
        if not cleaned_task:
            rejection_info = {
                "index": item_idx,
                "raw_item": raw_item,
                "reason": "Empty or whitespace-only task description",
            }
            if strict:
                raise ValueError(
                    f"Action item {item_idx} rejected: Task description cannot be empty."
                )
            rejected_items.append(rejection_info)
            diagnostics.append(f"Rejected action item {item_idx}: empty task description.")
            item_idx += 1
            continue

        item_diagnostics: List[str] = []
        item_id = f"norm_act_{len(normalized_action_items) + 1:03d}"

        # Normalize Responsible Person
        person, is_unassigned, person_diag = normalize_person(
            raw_item.get("responsible_person")
        )
        item_diagnostics.extend(person_diag)

        # Normalize Deadline
        deadline, is_ambiguous, deadline_diag = normalize_deadline(
            raw_item.get("deadline")
        )
        item_diagnostics.extend(deadline_diag)

        # Validate Topic Reference & Enrich with Member 2 Context
        raw_topic_ref = raw_item.get("topic_reference")
        topic_ref = None
        context_status = TopicContextStatus.MISSING_REFERENCE
        topic_context = None

        if raw_topic_ref is not None:
            try:
                topic_ref = int(raw_topic_ref)
                if member2_context_enriched:
                    if topic_ref in topics_by_id:
                        context_status = TopicContextStatus.RESOLVED
                        topic_context = topics_by_id[topic_ref]
                    else:
                        context_status = TopicContextStatus.UNRESOLVED
                        item_diagnostics.append(
                            f"Topic reference {topic_ref} not found in Member 2 data."
                        )
                        unresolved_topics_count += 1
                else:
                    context_status = TopicContextStatus.UNRESOLVED
                    item_diagnostics.append(
                        "Member 2 context not available; topic reference remains unverified."
                    )
                    unresolved_topics_count += 1
            except (ValueError, TypeError):
                item_diagnostics.append(f"Invalid topic_reference value: '{raw_topic_ref}'.")
                unresolved_topics_count += 1
        else:
            item_diagnostics.append("Missing topic_reference.")
            unresolved_topics_count += 1

        # Preserve Source Priority & Confidence (Source metadata only)
        src_priority = raw_item.get("priority")
        if src_priority is not None:
            src_priority = clean_whitespace(str(src_priority))

        src_confidence = raw_item.get("confidence_score")
        if src_confidence is not None:
            try:
                src_confidence = float(src_confidence)
                if not (0.0 <= src_confidence <= 1.0):
                    item_diagnostics.append(
                        f"Source confidence score out of bounds [0, 1]: {src_confidence}"
                    )
            except (ValueError, TypeError):
                item_diagnostics.append(
                    f"Invalid source confidence score: '{src_confidence}'"
                )
                src_confidence = None

        # Speaker Identity Resolution
        raw_spk_id = raw_item.get("speaker_id")
        spk_id = clean_whitespace(str(raw_spk_id)) if raw_spk_id else None

        if person:
            parts = [p.strip() for p in person.split(",") if p.strip()]
            resolved_parts_sids: List[str] = []
            resolved_parts_names: List[str] = []
            has_explicit_source = False
            has_diarization = False

            for part in parts:
                part_sid = None
                part_display = part
                part_source = "explicit_transcript"

                if re.match(r"^SPEAKER_\d+$", part, re.IGNORECASE):
                    part_sid = part.upper()
                    has_diarization = True
                    if part_sid in speaker_registry:
                        part_display = speaker_registry[part_sid].display_name
                        part_source = speaker_registry[part_sid].name_source
                    else:
                        part_display = part_sid
                        part_source = "diarization_fallback"
                        speaker_registry[part_sid] = SpeakerIdentity(
                            speaker_id=part_sid,
                            display_name=part_sid,
                            name_source="diarization_fallback",
                            evidence_segment_id=None,
                            evidence_text=None,
                        )
                else:
                    if speaker_registry:
                        for sid, identity in speaker_registry.items():
                            if identity.display_name and identity.display_name.lower() == part.lower():
                                part_sid = sid
                                part_display = identity.display_name
                                part_source = identity.name_source
                                break

                if part_source == "explicit_transcript":
                    has_explicit_source = True

                if part_sid:
                    resolved_parts_sids.append(part_sid)
                resolved_parts_names.append(part_display)

            if resolved_parts_sids:
                spk_id = ", ".join(resolved_parts_sids)
            resolved_display_name = ", ".join(resolved_parts_names)
            resolved_name_source = "explicit_transcript" if has_explicit_source else "diarization_fallback"

            if has_diarization and all(re.match(r"^SPEAKER_\d+$", p, re.IGNORECASE) for p in parts):
                person = resolved_display_name
        elif spk_id:
            if spk_id in speaker_registry:
                identity = speaker_registry[spk_id]
                resolved_display_name = identity.display_name
                resolved_name_source = identity.name_source
            else:
                resolved_display_name = spk_id
                resolved_name_source = "diarization_fallback"
                speaker_registry[spk_id] = SpeakerIdentity(
                    speaker_id=spk_id,
                    display_name=spk_id,
                    name_source="diarization_fallback",
                    evidence_segment_id=None,
                    evidence_text=None,
                )
            person = resolved_display_name
        else:
            resolved_display_name = None
            resolved_name_source = None

        # Deterministic Duplicate Detection
        sig = make_canonical_signature(cleaned_task, person, topic_ref)
        is_duplicate = False
        duplicate_of = None

        if sig in seen_signatures:
            is_duplicate = True
            duplicate_of = seen_signatures[sig]
            duplicates_detected += 1
            item_diagnostics.append(f"Deterministic duplicate of {duplicate_of}")
        else:
            seen_signatures[sig] = item_id

        # Build Normalized Item
        norm_item = NormalizedActionItem(
            item_id=item_id,
            raw_task=str(raw_task),
            task=cleaned_task,
            responsible_person=person,
            speaker_id=spk_id,
            display_name=resolved_display_name,
            name_source=resolved_name_source,
            is_unassigned=is_unassigned,
            deadline=deadline,
            is_ambiguous_deadline=is_ambiguous,
            topic_reference=topic_ref,
            context_status=context_status,
            topic_context=topic_context,
            source_priority=src_priority,
            source_confidence_score=src_confidence,
            is_duplicate=is_duplicate,
            duplicate_of=duplicate_of,
            validation_diagnostics=item_diagnostics,
        )
        normalized_action_items.append(norm_item)
        item_idx += 1

    # ------------------------------------------------------------------------
    # 4. Process Key Decisions
    # ------------------------------------------------------------------------
    raw_decisions = raw_m3.get("key_decisions", [])
    normalized_decisions: List[NormalizedDecision] = []

    dec_idx = 1
    for raw_dec in raw_decisions:
        if not isinstance(raw_dec, dict):
            if hasattr(raw_dec, "model_dump"):
                raw_dec = raw_dec.model_dump()
            else:
                continue

        raw_text = raw_dec.get("decision")
        cleaned_text = clean_whitespace(raw_text)

        if not cleaned_text:
            rejection_info = {
                "index": dec_idx,
                "raw_item": raw_dec,
                "reason": "Empty or whitespace-only decision statement",
            }
            if strict:
                raise ValueError(
                    f"Decision {dec_idx} rejected: Decision text cannot be empty."
                )
            rejected_items.append(rejection_info)
            diagnostics.append(f"Rejected decision {dec_idx}: empty decision text.")
            dec_idx += 1
            continue

        dec_diagnostics: List[str] = []
        decision_id = f"norm_dec_{len(normalized_decisions) + 1:03d}"

        # Validate Topic Reference & Enrich
        raw_topic_ref = raw_dec.get("topic_reference")
        topic_ref = None
        context_status = TopicContextStatus.MISSING_REFERENCE
        topic_context = None

        if raw_topic_ref is not None:
            try:
                topic_ref = int(raw_topic_ref)
                if member2_context_enriched:
                    if topic_ref in topics_by_id:
                        context_status = TopicContextStatus.RESOLVED
                        topic_context = topics_by_id[topic_ref]
                    else:
                        context_status = TopicContextStatus.UNRESOLVED
                        dec_diagnostics.append(
                            f"Topic reference {topic_ref} not found in Member 2 data."
                        )
                else:
                    context_status = TopicContextStatus.UNRESOLVED
            except (ValueError, TypeError):
                dec_diagnostics.append(f"Invalid topic_reference value: '{raw_topic_ref}'.")

        norm_dec = NormalizedDecision(
            decision_id=decision_id,
            raw_decision=str(raw_text),
            decision=cleaned_text,
            topic_reference=topic_ref,
            context_status=context_status,
            topic_context=topic_context,
            validation_diagnostics=dec_diagnostics,
        )
        normalized_decisions.append(norm_dec)
        dec_idx += 1

    # ------------------------------------------------------------------------
    # 5. Build Final Normalized Output
    # ------------------------------------------------------------------------
    return Member4NormalizedOutput(
        meeting_id=meeting_id,
        processing_stage="member_4_normalized",
        total_action_items=len(normalized_action_items),
        total_decisions=len(normalized_decisions),
        duplicates_detected=duplicates_detected,
        unresolved_topics_count=unresolved_topics_count,
        member2_context_enriched=member2_context_enriched,
        speakers=speaker_registry,
        action_items=normalized_action_items,
        key_decisions=normalized_decisions,
        rejected_items=rejected_items,
        diagnostics=diagnostics,
    )
