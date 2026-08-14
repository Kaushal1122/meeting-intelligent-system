import os
import whisperx
from pyannote.audio import Pipeline

# -----------------------------------
# Configuration
# -----------------------------------

# AUDIO_FILE = r"..\data\ami\amicorpus\ES2002a\audio\ES2002a.Mix-Headset.wav"
AUDIO_FILE = "../data/ami/amicorpus/ES2002a/audio/ES2002a.Mix-Headset.wav"

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is not set. Set it in PowerShell before running this script."
    )


# -----------------------------------
# Load diarization pipeline
# -----------------------------------

print("Loading Community-1 speaker diarization model...")

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1",
    token=HF_TOKEN
)

print("Diarization model loaded successfully.")


# -----------------------------------
# Load audio through WhisperX
# This avoids relying on TorchCodec
# -----------------------------------

print("Loading audio...")

audio = whisperx.load_audio(AUDIO_FILE)

print("Audio loaded successfully.")


# -----------------------------------
# Run speaker diarization
# -----------------------------------

print("Starting speaker diarization...")
print("This may take some time on CPU.")

# pyannote expects:
# waveform: (channel, time)
# sample_rate: integer

import torch

waveform = torch.from_numpy(audio).float().unsqueeze(0)

audio_input = {
    "waveform": waveform,
    "sample_rate": 16000
}

output = pipeline(
    audio_input,
    min_speakers=4,
    max_speakers=4
)

print("Diarization completed.")


# -----------------------------------
# Display speaker turns
# -----------------------------------

print("\n========== SPEAKER DIARIZATION ==========\n")

for turn, speaker in output.speaker_diarization:

    print(
        f"[{turn.start:.2f} --> {turn.end:.2f}] "
        f"{speaker}"
    )


print("\n========== DONE ==========")