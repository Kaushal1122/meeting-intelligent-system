"""
Meeting Processing Service for Member 4 API.
Orchestrates inputs through Member 1-3 pipeline and executes Member 4 intelligence.
"""

from pathlib import Path
import json
import re
import sys
import tempfile
from typing import Any, Dict, Optional

# Ensure project root, backend dir, and preprocessing dir are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
PREPROCESSING_DIR = BACKEND_DIR / "preprocessing"

for path in [PROJECT_ROOT, BACKEND_DIR, PREPROCESSING_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


from backend.preprocessing.input_handler import AUDIO_EXTENSIONS
from backend.preprocessing.speaker_normalizer import normalize_speaker_label
from backend.preprocessing.text_cleaner import clean_text
from backend.preprocessing.transcript_processor import parse_line, split_sentences
from backend.member4 import (
    UserRole,
    explain_meeting_triage,
    personalize_meeting_view,
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def validate_meeting_id(meeting_id: str) -> str:
    """Validate that meeting_id is safe and contains no path traversal."""
    if not meeting_id or not meeting_id.strip():
        raise ValueError("Meeting ID cannot be empty.")
    cleaned = meeting_id.strip()
    if not re.match(r"^[A-Za-z0-9_\-]+$", cleaned):
        raise ValueError(
            f"Invalid meeting ID '{cleaned}'. Only alphanumeric characters, underscores, and hyphens are allowed."
        )
    return cleaned


def parse_raw_transcript_text(text: str, meeting_id: str) -> Dict[str, Any]:
    """Parse raw transcript text with optional speaker labels and timestamps."""
    lines = text.strip().splitlines()
    segments = []

    for index, line in enumerate(lines, start=1):
        parsed = parse_line(line)
        if parsed is None:
            continue

        speaker = normalize_speaker_label(parsed["speaker"])
        start = parsed["start"]
        raw_text = parsed["text"]

        sentences = split_sentences(raw_text)
        for sentence in sentences:
            cleaned = clean_text(sentence)
            if not cleaned:
                continue

            segments.append({
                "segment_id": len(segments) + 1,
                "speaker": speaker,
                "start": start,
                "end": None,
                "raw_text": sentence,
                "clean_text": cleaned,
            })

    if not segments:
        raise ValueError("The provided transcript contains no usable text segments.")

    return {
        "meeting_id": meeting_id,
        "language": "en",
        "source": "text",
        "segments": segments,
    }


def execute_member4_pipeline(
    member3_data: Dict[str, Any], member2_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute complete Member 4 pipeline (Normalization -> Explainability -> Personalization)."""
    canonical_explained = explain_meeting_triage(member3_data, member2_data=member2_data)

    views = {}
    for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]:
        view = personalize_meeting_view(canonical_explained, role=role)
        views[role.value] = view.model_dump()

    return {
        "meeting_id": canonical_explained.meeting_id,
        "processing_stage": "member_4_dashboard_ready",
        "total_canonical_items": len(canonical_explained.action_items),
        "speakers": {k: v.model_dump() for k, v in canonical_explained.speakers.items()},
        "views": views,
        "key_decisions": [d.model_dump() for d in canonical_explained.key_decisions],
        "diagnostics": canonical_explained.diagnostics,
    }


def process_meeting_input(
    meeting_id: str,
    audio_bytes: Optional[bytes] = None,
    audio_filename: Optional[str] = None,
    transcript_bytes: Optional[bytes] = None,
    transcript_filename: Optional[str] = None,
    transcript_text: Optional[str] = None,
    force_reprocess: bool = False,
) -> Dict[str, Any]:
    """Process incoming meeting input through pipeline and return Member 4 payload."""
    clean_id = validate_meeting_id(meeting_id)

    if transcript_text is not None and not transcript_text.strip():
        raise ValueError("Pasted transcript text cannot be empty.")

    # Validate input exclusivity
    inputs_provided = sum([
        bool(audio_bytes),
        bool(transcript_bytes),
        bool(transcript_text and transcript_text.strip()),
    ])


    if inputs_provided == 0:
        raise ValueError(
            "No input provided. Please provide an audio file, transcript file, or transcript text."
        )
    if inputs_provided > 1:
        raise ValueError(
            "Multiple inputs provided. Please provide only one of: audio file, transcript file, or transcript text."
        )

    # -------------------------------------------------------------
    # 1. ES2002a Canonical Fast-Path / Regression Reference
    # -------------------------------------------------------------
    m3_ref = PROCESSED_DIR / f"{clean_id}_member3_results.json"
    m2_ref = PROCESSED_DIR / f"{clean_id}_member2_results.json"

    if clean_id == "ES2002a" and not force_reprocess and m3_ref.exists() and m2_ref.exists():
        with open(m3_ref, "r", encoding="utf-8") as f:
            m3_data = json.load(f)
        with open(m2_ref, "r", encoding="utf-8") as f:
            m2_data = json.load(f)
        return execute_member4_pipeline(m3_data, m2_data)

    # -------------------------------------------------------------
    # 2. Audio Processing (Member 1)
    # -------------------------------------------------------------
    if audio_bytes:
        if not audio_filename:
            raise ValueError("Audio filename is required for audio upload.")
        ext = Path(audio_filename).suffix.lower()
        if ext not in AUDIO_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio format '{ext}'. Supported formats: {', '.join(sorted(AUDIO_EXTENSIONS))}"
            )

        # Write to temporary file with auto cleanup inside PROJECT_ROOT/data/temp_uploads
        temp_base = PROJECT_ROOT / "data" / "temp_uploads"
        temp_base.mkdir(parents=True, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix="audio_upload_", dir=temp_base)
        temp_audio = Path(temp_dir) / f"{clean_id}{ext}"
        try:
            with open(temp_audio, "wb") as f:
                f.write(audio_bytes)


            from backend.pipeline import run_audio_pipeline
            pipeline_results = run_audio_pipeline(temp_audio, force_transcription=True)
            return execute_member4_pipeline(
                pipeline_results["member3"], pipeline_results["member2"]
            )
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


    # -------------------------------------------------------------
    # 3. Transcript Processing (Member 2 + Member 3)
    # -------------------------------------------------------------
    transcript_data = None

    if transcript_bytes:
        if not transcript_filename:
            raise ValueError("Transcript filename is required for file upload.")
        ext = Path(transcript_filename).suffix.lower()
        if ext not in [".txt", ".json"]:
            raise ValueError(f"Unsupported transcript format '{ext}'. Supported formats: .txt, .json")

        content_str = transcript_bytes.decode("utf-8", errors="replace").strip()
        if not content_str:
            raise ValueError("Uploaded transcript file is empty.")

        if ext == ".json":
            try:
                parsed_json = json.loads(content_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Uploaded transcript JSON is malformed: {e}")

            # If it's already a complete member3 result
            if "action_items" in parsed_json and "key_decisions" in parsed_json:
                m2_file = PROCESSED_DIR / f"{clean_id}_member2_results.json"
                m2_data = {}
                if m2_file.exists():
                    with open(m2_file, "r", encoding="utf-8") as f:
                        m2_data = json.load(f)
                return execute_member4_pipeline(parsed_json, m2_data)

            # If it's a speaker transcript containing segments
            if "segments" in parsed_json and isinstance(parsed_json["segments"], list):
                transcript_data = parsed_json
            else:
                raise ValueError("JSON transcript must contain a 'segments' list.")
        else:
            # .txt file
            transcript_data = parse_raw_transcript_text(content_str, clean_id)

    elif transcript_text:
        content_str = transcript_text.strip()
        if not content_str:
            raise ValueError("Pasted transcript text cannot be empty.")
        transcript_data = parse_raw_transcript_text(content_str, clean_id)

    if not transcript_data:
        raise ValueError("Failed to parse transcript data.")

    # -------------------------------------------------------------
    # 4. Run Upstream Pipeline (Member 2 & 3)
    # -------------------------------------------------------------
    # Check if pre-processed results already exist for this meeting_id
    if not force_reprocess and m3_ref.exists() and m2_ref.exists():
        with open(m3_ref, "r", encoding="utf-8") as f:
            m3_data = json.load(f)
        with open(m2_ref, "r", encoding="utf-8") as f:
            m2_data = json.load(f)
    else:
        from backend.pipeline import process_transcript
        pipeline_results = process_transcript(transcript_data, meeting_id=clean_id)
        m3_data = pipeline_results["member3"]
        m2_data = pipeline_results["member2"]

    # -------------------------------------------------------------
    # 5. Run Member 4 Intelligence
    # -------------------------------------------------------------
    return execute_member4_pipeline(m3_data, m2_data)
