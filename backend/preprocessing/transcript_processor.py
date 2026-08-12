import json
import re
from pathlib import Path

from text_cleaner import clean_text
from speaker_normalizer import normalize_speaker_label

# Matches:
# Laura: Hello everyone.
# David: Let's start.
SPEAKER_PATTERN = re.compile(
    r"^\s*([^:]+?)\s*:\s*(.+)$"
)

# Matches optional timestamps such as:
# [00:01:23] Laura: Hello
# [01:23] Laura: Hello
TIMESTAMP_PATTERN = re.compile(
    r"^\s*\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s*(.*)$"
)


def timestamp_to_seconds(timestamp_match):
    """
    Convert [MM:SS] or [HH:MM:SS] to seconds.
    """

    first = int(timestamp_match.group(1))
    second = int(timestamp_match.group(2))
    third = timestamp_match.group(3)

    if third is not None:
        # HH:MM:SS
        return first * 3600 + second * 60 + int(third)

    # MM:SS
    return first * 60 + second


def split_sentences(text):
    """
    Split transcript text into sentences while preserving
    basic punctuation.
    """

    text = clean_text(text)

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def parse_line(line):
    """
    Parse one transcript line.

    Supported examples:

        Laura: Hello everyone.

        [01:23] Laura: Hello everyone.

        [00:01:23] Laura: Hello everyone.

        Hello everyone.
    """

    line = line.strip()

    if not line:
        return None

    start_time = None
    remaining = line

    # Check for timestamp
    timestamp_match = TIMESTAMP_PATTERN.match(line)

    if timestamp_match:
        start_time = timestamp_to_seconds(
            timestamp_match
        )

        remaining = timestamp_match.group(4).strip()

    # Check for speaker
    speaker_match = SPEAKER_PATTERN.match(
        remaining
    )

    if speaker_match:
        speaker = speaker_match.group(1).strip()
        text = speaker_match.group(2).strip()
    else:
        speaker = "UNKNOWN"
        text = remaining

    return {
        "speaker": speaker,
        "start": start_time,
        "text": text
    }


def process_transcript(file_path, output_path):
    """
    Convert an existing transcript into the
    standard meeting JSON format.
    """

    input_file = Path(file_path)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Transcript not found: {file_path}"
        )

    if input_file.suffix.lower() != ".txt":
        raise ValueError(
            "Only .txt transcript files are supported."
        )

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:

        lines = file.readlines()

    segments = []

    for line in lines:

        parsed = parse_line(line)

        if parsed is None:
            continue

        speaker = normalize_speaker_label(
            parsed["speaker"]
        )
        start = parsed["start"]
        raw_text = parsed["text"]

        sentences = split_sentences(raw_text)

        for sentence in sentences:

            cleaned_text = clean_text(sentence)

            if not cleaned_text:
                continue

            segments.append({
                "speaker": speaker,
                "start": start,
                "end": None,
                "raw_text": sentence,
                "clean_text": cleaned_text
            })

    output = {
        "meeting_id": input_file.stem,
        "language": "en",
        "source": "text",
        "segments": segments
    }

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output