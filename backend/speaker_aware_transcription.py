import os
import torch
import json
from pathlib import Path
import whisperx
from whisperx.diarize import DiarizationPipeline
from preprocessing.text_cleaner import clean_text
from preprocessing.speaker_normalizer import normalize_speaker_label


# -----------------------------------------
# Configuration
# -----------------------------------------

AUDIO_FILE = r"..\data\ami\amicorpus\ES2002a\audio\ES2002a.Mix-Headset.wav"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"
MODEL_NAME = "small"

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is not set."
    )


# -----------------------------------------
# 1. Load audio
# -----------------------------------------

print("Loading audio...")

audio = whisperx.load_audio(AUDIO_FILE)

print("Audio loaded.")


# -----------------------------------------
# 2. Load WhisperX ASR
# -----------------------------------------

print("Loading WhisperX ASR model...")

model = whisperx.load_model(
    MODEL_NAME,
    DEVICE,
    compute_type=COMPUTE_TYPE,
    language="en"
)

print("ASR model loaded.")


# -----------------------------------------
# 3. Transcription
# -----------------------------------------

print("Transcribing...")

result = model.transcribe(
    audio,
    batch_size=4
)

print("Transcription completed.")


# -----------------------------------------
# 4. Word-level alignment
# -----------------------------------------

print("Loading alignment model...")

align_model, align_metadata = whisperx.load_align_model(
    language_code=result["language"],
    device=DEVICE
)

print("Aligning words...")

result = whisperx.align(
    result["segments"],
    align_model,
    align_metadata,
    audio,
    DEVICE,
    return_char_alignments=False
)

print("Alignment completed.")


# -----------------------------------------
# 5. Speaker diarization
# -----------------------------------------

print("Loading speaker diarization model...")

diarize_model = DiarizationPipeline(
    token=HF_TOKEN,
    device=DEVICE
)

print("Running speaker diarization...")

diarize_segments = diarize_model(
    audio,
    min_speakers=4,
    max_speakers=4
)

print("Speaker diarization completed.")


# -----------------------------------------
# 6. Assign speakers to transcript
# -----------------------------------------

print("Assigning speakers to transcript...")

result = whisperx.assign_word_speakers(
    diarize_segments,
    result
)

print("Speaker assignment completed.")


# -----------------------------------------
# 7. Create structured transcript
# -----------------------------------------

import json
from pathlib import Path

transcript_segments = []

for segment in result["segments"]:

    start = segment.get("start")
    end = segment.get("end")

    speaker = normalize_speaker_label(
        segment.get("speaker", "UNKNOWN")
    )

    text = segment.get(
        "text",
        ""
    ).strip()

    # Ignore empty segments
    if not text:
        continue

    raw_text = segment.get("text", "").strip()

    cleaned_text = clean_text(raw_text)

    if not cleaned_text:
        continue

    transcript_segments.append({
        "speaker": speaker,
        "start": round(start, 2) if start is not None else None,
        "end": round(end, 2) if end is not None else None,
        "raw_text": raw_text,
        "clean_text": cleaned_text
    })


# -----------------------------------------
# 8. Create complete output object
# -----------------------------------------

output = {
    "meeting_id": "ES2002a",
    "language": result.get("language", "en"),
    "source": "audio",
    "segments": transcript_segments
}


# -----------------------------------------
# 9. Save JSON
# -----------------------------------------

output_dir = Path("../data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "ES2002a_speaker_transcript.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(
        output,
        f,
        indent=4,
        ensure_ascii=False
    )


# -----------------------------------------
# 10. Display result
# -----------------------------------------

print("\n")
print("=" * 60)
print("SPEAKER-AWARE TRANSCRIPT")
print("=" * 60)

for segment in transcript_segments:

    print(
        f"[{segment['start']:.2f} --> "
        f"{segment['end']:.2f}] "
        f"{segment['speaker']}: "
        f"{segment['clean_text']}"
    )


print("\n")
print("=" * 60)
print(f"JSON saved to: {output_file}")
print("=" * 60)