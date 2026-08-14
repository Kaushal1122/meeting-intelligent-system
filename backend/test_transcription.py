import os
import torch
import pandas as pd
import whisperx
from pyannote.audio import Pipeline

# -----------------------------------
# Configuration
# -----------------------------------

AUDIO_FILE = "../data/ami/amicorpus/ES2002a/audio/ES2002a.Mix-Headset.wav"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"
MODEL_NAME = "small"
LANGUAGE = "en"
BATCH_SIZE = 4

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is not set."
    )


# -----------------------------------
# 1. Load audio
# -----------------------------------

print("Loading audio...")

audio = whisperx.load_audio(AUDIO_FILE)

print("Audio loaded successfully.")


# -----------------------------------
# 2. Load WhisperX ASR model
# -----------------------------------

print("\nLoading WhisperX ASR model...")

model = whisperx.load_model(
    MODEL_NAME,
    DEVICE,
    compute_type=COMPUTE_TYPE,
    language=LANGUAGE
)

print("ASR model loaded successfully.")


# -----------------------------------
# 3. Speech-to-Text
# -----------------------------------

print("\nStarting transcription...")

result = model.transcribe(
    audio,
    batch_size=BATCH_SIZE
)

print("Transcription completed.")

print("Detected language:", result["language"])


# -----------------------------------
# 4. Word-level alignment
# -----------------------------------

print("\nLoading alignment model...")

align_model, align_metadata = whisperx.load_align_model(
    language_code=result["language"],
    device=DEVICE
)

print("Alignment model loaded.")

print("\nStarting alignment...")

result = whisperx.align(
    result["segments"],
    align_model,
    align_metadata,
    audio,
    DEVICE,
    return_char_alignments=False
)

print("Alignment completed.")


# -----------------------------------
# 5. Speaker diarization
# -----------------------------------

print("\nLoading speaker diarization model...")

diarize_model = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1",
    token=HF_TOKEN
)

print("Diarization model loaded.")


print("\nStarting speaker diarization...")

diarize_segments = diarize_model(
    {"waveform": torch.from_numpy(audio).float().unsqueeze(0),
     "sample_rate": 16000},
    min_speakers=4,
    max_speakers=4
)

print("Speaker diarization completed.")


## -----------------------------------
# 6. Convert diarization output
# -----------------------------------

print("\nConverting diarization output...")

diarization_data = []

for turn, _, speaker in diarize_segments.speaker_diarization.itertracks(
    yield_label=True
):
    diarization_data.append({
        "start": turn.start,
        "end": turn.end,
        "speaker": speaker
    })

diarization_df = pd.DataFrame(diarization_data)

print("Diarization output converted successfully.")


# -----------------------------------
# 7. Assign speakers to transcript
# -----------------------------------

print("\nAssigning speakers to transcript...")

result = whisperx.assign_word_speakers(
    diarization_df,
    result
)

print("Speaker assignment completed.")


# -----------------------------------
# 8. Display final transcript
# -----------------------------------

print("\n")
print("=" * 60)
print("       SPEAKER-AWARE TRANSCRIPT")
print("=" * 60)

for segment in result["segments"]:

    start = segment.get("start", 0)
    end = segment.get("end", 0)

    speaker = segment.get(
        "speaker",
        "UNKNOWN"
    )

    text = segment.get(
        "text",
        ""
    ).strip()

    if text:

        print(
            f"[{start:.2f} --> {end:.2f}] "
            f"{speaker}: {text}"
        )


print("\n" + "=" * 60)
print("                 DONE")
print("=" * 60)