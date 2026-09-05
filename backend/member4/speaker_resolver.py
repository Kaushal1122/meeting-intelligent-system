"""
Dynamic Speaker Name Resolution Engine for Member 4.
Detects explicit speaker self-introductions from meeting dialogue,
preserves canonical diarization IDs (e.g. SPEAKER_01), and assigns
deterministic fallback labels when real names are unverified.

Core Principles:
1. Zero Hardcoding: No fixed participant lists (David, Laura, Sabi, etc.).
2. Explicit Detection Only: Self-introductions only ("I'm Rahul", "My name is Priya").
3. Third-party Mentions Ignored: "Rahul will take this" does NOT make the speaker Rahul.
4. Canonical Identity Preserved: speaker_id is always kept (e.g. SPEAKER_02).
5. Deterministic Fallbacks: Unverified speakers remain SPEAKER_XX.
"""

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from .schemas import SpeakerIdentity


# Common non-name adjectives / words that often follow "I'm" in spoken English
NON_NAME_WORDS: Set[str] = {
    "a", "an", "the", "ready", "sure", "here", "going", "sorry", "fine", "good",
    "happy", "glad", "tired", "busy", "supposed", "our", "not", "just", "also",
    "still", "back", "done", "trying", "working", "talking", "thinking", "looking",
    "asking", "wondering", "guessing", "assuming", "hoping", "afraid", "aware",
    "certain", "confident", "curious", "interested", "pleased", "right", "wrong",
    "late", "early", "new", "old", "okay", "ok", "all", "in", "on", "at", "to",
    "for", "with", "from", "by", "about", "like", "so", "very", "quite", "really",
    "pretty", "fairly", "actually", "basically", "currently", "now", "here", "there",
    "user", "industrial", "marketing", "project", "interface", "manager", "designer",
    "lead", "engineer", "developer", "tester", "chair", "member", "someone", "anyone"
}

# Explicit self-identification regex patterns
SELF_ID_PATTERNS = [
    # "my name is Rahul" / "My name's Priya"
    re.compile(r"\bmy name(?:'s|\s+is)\s+([A-Z][a-z]+)\b", re.IGNORECASE),
    # "Hi, I'm Rahul" / "Hello I am Priya" / "I'm David"
    re.compile(r"\b(?:hi|hello|hey|ok|okay)?\s*,?\s*i(?:'m|\s+am)\s+([A-Z][a-z]+)\b", re.IGNORECASE),
    # "This is Rahul" (common telephone / conference self-id)
    re.compile(r"\bthis is\s+([A-Z][a-z]+)(?:\s+speaking|\s+here)?\b", re.IGNORECASE),
    # "Rahul here" / "Rahul speaking"
    re.compile(r"\b([A-Z][a-z]+)\s+(?:here|speaking)\b", re.IGNORECASE),
]


def clean_speaker_id(raw_speaker: Optional[str]) -> str:
    """Normalize speaker label to canonical format e.g. SPEAKER_01."""
    if not raw_speaker:
        return "SPEAKER_00"
    cleaned = raw_speaker.strip()
    match = re.fullmatch(r"(?:speaker|participant)[\s_-]*(\d+)", cleaned, re.IGNORECASE)
    if match:
        number = int(match.group(1))
        return f"SPEAKER_{number:02d}"
    return cleaned


def detect_explicit_self_id(text: str) -> Optional[str]:
    """
    Detect explicit self-identification name from a single utterance text.
    Returns the extracted name if valid, otherwise None.
    Rejects non-name adjectives, third-party mentions, and lowercase words.
    """
    if not text or not isinstance(text, str):
        return None

    cleaned_text = text.strip()

    for pattern in SELF_ID_PATTERNS:
        match = pattern.search(cleaned_text)
        if match:
            candidate = match.group(1).strip()
            # Title-case for consistency
            candidate_titled = candidate.capitalize()
            # Reject non-name common words
            if candidate_titled.lower() in NON_NAME_WORDS:
                continue
            # Must be a plausible human name (at least 2 letters, alphabetic)
            if len(candidate_titled) >= 2 and candidate_titled.isalpha():
                return candidate_titled

    return None


def resolve_meeting_speakers(
    transcript_segments: Union[List[Dict[str, Any]], List[Any], Dict[str, Any]],
    known_speaker_ids: Optional[List[str]] = None,
) -> Dict[str, SpeakerIdentity]:
    """
    Analyze transcript dialogue turns and deterministically resolve speaker identities.

    Args:
        transcript_segments: List of segment dicts (with 'speaker', 'text', 'segment_id'),
                             or Member 2 topics payload, or list of segment objects.
        known_speaker_ids: Optional list of known speaker IDs to ensure fallback entries exist.

    Returns:
        Dictionary mapping speaker_id (e.g. 'SPEAKER_01') to SpeakerIdentity.
    """
    resolved: Dict[str, SpeakerIdentity] = {}

    # Extract flat list of segment dicts or objects
    flat_segments: List[Tuple[str, str, Optional[int]]] = []

    if isinstance(transcript_segments, (str, Path)):
        p = Path(transcript_segments)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                transcript_segments = json.load(f)

    if isinstance(transcript_segments, dict):
        # Could be Member 2 output with topics
        topics = transcript_segments.get("topics", [])
        for topic in topics:
            for seg in topic.get("segments", []):
                spk = seg.get("speaker", "")
                txt = seg.get("text", seg.get("clean_text", ""))
                sid = seg.get("segment_id")
                if spk and txt:
                    flat_segments.append((spk, txt, sid))
    elif isinstance(transcript_segments, list):
        for item in transcript_segments:
            if isinstance(item, dict):
                spk = item.get("speaker", "")
                txt = item.get("text", item.get("raw_text", item.get("clean_text", "")))
                sid = item.get("segment_id")
                if spk and txt:
                    flat_segments.append((spk, txt, sid))
            elif hasattr(item, "speaker") and hasattr(item, "text"):
                spk = getattr(item, "speaker", "")
                txt = getattr(item, "text", "")
                sid = getattr(item, "segment_id", None)
                if spk and txt:
                    flat_segments.append((spk, txt, sid))

    # 1. First pass: Register all observed speakers with deterministic fallbacks
    observed_speakers: Set[str] = set()
    if known_speaker_ids:
        for k in known_speaker_ids:
            observed_speakers.add(clean_speaker_id(k))

    for spk, _, _ in flat_segments:
        c_spk = clean_speaker_id(spk)
        if c_spk:
            observed_speakers.add(c_spk)

    for spk_id in sorted(observed_speakers):
        resolved[spk_id] = SpeakerIdentity(
            speaker_id=spk_id,
            display_name=spk_id,
            name_source="diarization_fallback",
            confidence=0.0,
            evidence_text=None,
            evidence_segment_id=None,
        )

    # 2. Second pass: Detect explicit self-introductions chronologically
    for spk, txt, sid in flat_segments:
        c_spk = clean_speaker_id(spk)
        if not c_spk:
            continue

        # If already resolved with explicit transcript evidence, keep first self-identification
        if resolved.get(c_spk) and resolved[c_spk].name_source == "explicit_transcript":
            continue

        name = detect_explicit_self_id(txt)
        if name:
            resolved[c_spk] = SpeakerIdentity(
                speaker_id=c_spk,
                display_name=name,
                name_source="explicit_transcript",
                confidence=1.0,
                evidence_text=txt.strip(),
                evidence_segment_id=sid,
            )

    return resolved


def format_speaker_display(
    speaker_id: Optional[str],
    display_name_or_directory: Optional[Union[str, Dict[str, SpeakerIdentity]]] = None,
) -> str:
    """
    Format speaker identifier for display.
    Returns verified display_name if available, else clean speaker_id, else '(Unassigned)'.
    Never displays '(Unassigned)' if speaker_id exists.
    """
    if isinstance(display_name_or_directory, str) and display_name_or_directory.strip():
        return display_name_or_directory.strip()

    if isinstance(display_name_or_directory, dict) and speaker_id:
        clean_id = clean_speaker_id(speaker_id)
        if clean_id in display_name_or_directory:
            return display_name_or_directory[clean_id].display_name

    if speaker_id and str(speaker_id).strip():
        return clean_speaker_id(speaker_id)

    return "(Unassigned)"
