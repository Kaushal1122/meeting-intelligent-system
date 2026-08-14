import json
import os


def load_transcript(file_path):
    """
    Load a processed meeting transcript from a JSON file.

    Expected structure:

    {
        "meeting_id": "...",
        "language": "...",
        "source": "...",
        "segments": [
            {
                "speaker": "...",
                "start": ...,
                "end": ...,
                "raw_text": "...",
                "clean_text": "..."
            }
        ]
    }

    Returns:
        dict: Loaded transcript data.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Transcript file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        transcript = json.load(file)

    # Basic validation
    required_fields = [
        "meeting_id",
        "language",
        "source",
        "segments"
    ]

    for field in required_fields:
        if field not in transcript:
            raise ValueError(
                f"Missing required field: {field}"
            )

    if not isinstance(transcript["segments"], list):
        raise ValueError(
            "'segments' must be a list."
        )

    return transcript


def get_clean_transcript(transcript):
    """
    Extract clean text from all transcript segments.

    Returns:
        list: List of speaker-aware text segments.
    """

    clean_segments = []

    for segment in transcript["segments"]:

        speaker = segment.get(
            "speaker",
            "UNKNOWN"
        )

        text = segment.get(
            "clean_text",
            ""
        ).strip()

        if text:

            clean_segments.append({
                "speaker": speaker,
                "text": text,
                "start": segment.get("start"),
                "end": segment.get("end")
            })

    return clean_segments


def build_transcript_text(transcript):
    """
    Convert the structured transcript into plain text
    while preserving speaker information.

    Example:

    SPEAKER_01: Good morning everyone.
    SPEAKER_02: Let's begin the meeting.
    """

    segments = get_clean_transcript(transcript)

    lines = []

    for segment in segments:

        line = (
            f"{segment['speaker']}: "
            f"{segment['text']}"
        )

        lines.append(line)

    return "\n".join(lines)