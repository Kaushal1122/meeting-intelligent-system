import whisperx

# -----------------------------
# Configuration
# -----------------------------

AUDIO_FILE = r"..\data\ami\amicorpus\ES2002a\audio\ES2002a.Mix-Headset.wav"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"
MODEL_NAME = "small"
LANGUAGE = "en"


# -----------------------------
# 1. Load WhisperX ASR model
# -----------------------------

print("Loading WhisperX model...")

model = whisperx.load_model(
    MODEL_NAME,
    DEVICE,
    compute_type=COMPUTE_TYPE,
    language=LANGUAGE
)

print("ASR model loaded.")


# -----------------------------
# 2. Load audio
# -----------------------------

print("Loading audio...")

audio = whisperx.load_audio(AUDIO_FILE)

print("Audio loaded.")


# -----------------------------
# 3. Transcription
# -----------------------------

print("Starting transcription...")

result = model.transcribe(
    audio,
    batch_size=4
)

print("Transcription completed.")

print("\nDetected language:", result["language"])


# -----------------------------
# 4. Word-level alignment
# -----------------------------

print("\nLoading alignment model...")

align_model, align_metadata = whisperx.load_align_model(
    language_code=result["language"],
    device=DEVICE
)

print("Alignment model loaded.")

print("Starting word-level alignment...")

aligned_result = whisperx.align(
    result["segments"],
    align_model,
    align_metadata,
    audio,
    DEVICE,
    return_char_alignments=False
)

print("Alignment completed.")


# -----------------------------
# 5. Display aligned result
# -----------------------------

print("\n========== ALIGNED TRANSCRIPT ==========\n")

for segment in aligned_result["segments"]:

    start = segment.get("start", 0)
    end = segment.get("end", 0)
    text = segment.get("text", "").strip()

    print(f"[{start:.2f} --> {end:.2f}] {text}")

    if "words" in segment:

        for word in segment["words"]:
            word_text = word.get("word", "").strip()
            word_start = word.get("start")
            word_end = word.get("end")

            if word_start is not None and word_end is not None:
                print(
                    f"    {word_text} "
                    f"[{word_start:.2f} --> {word_end:.2f}]"
                )


print("\n========== DONE ==========")