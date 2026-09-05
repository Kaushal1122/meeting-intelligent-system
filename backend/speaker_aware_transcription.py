import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load root .env file if available
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
for p in [PROJECT_ROOT, BACKEND_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

load_dotenv(PROJECT_ROOT / ".env")

import whisperx
from whisperx.diarize import DiarizationPipeline

from preprocessing.text_cleaner import clean_text
from preprocessing.speaker_normalizer import normalize_speaker_label



# ============================================================
# CONFIGURATION
# ============================================================

DEVICE = "cpu"
COMPUTE_TYPE = "int8"
MODEL_NAME = "small"
LANGUAGE = "en"


# ============================================================
# MAIN FUNCTION
# ============================================================

def transcribe_audio(
    audio_file,
    output_file=None,
    min_speakers=None,
    max_speakers=None
):

    # --------------------------------------------------------
    # Check Hugging Face token
    # --------------------------------------------------------

    hf_token = os.getenv("HF_TOKEN")

    if not hf_token:
        raise RuntimeError(
            "HF_TOKEN is not set."
        )


    audio_file = Path(audio_file)

    if not audio_file.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}"
        )


    # --------------------------------------------------------
    # 1. Load audio
    # --------------------------------------------------------

    print("\nLoading audio...")

    audio = whisperx.load_audio(
        str(audio_file)
    )

    print("Audio loaded.")


    # --------------------------------------------------------
    # 2. Load WhisperX ASR
    # --------------------------------------------------------

    print("\nLoading WhisperX ASR model...")

    model = whisperx.load_model(
        MODEL_NAME,
        DEVICE,
        compute_type=COMPUTE_TYPE,
        language=LANGUAGE
    )

    print("ASR model loaded.")


    # --------------------------------------------------------
    # 3. Transcription
    # --------------------------------------------------------

    print("\nTranscribing audio...")

    result = model.transcribe(
        audio,
        batch_size=4
    )

    print("Transcription completed.")


    # --------------------------------------------------------
    # 4. Word-level alignment
    # --------------------------------------------------------

    print("\nLoading alignment model...")

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


    # --------------------------------------------------------
    # 5. Speaker diarization & Assignment
    # --------------------------------------------------------

    try:
        print("\nLoading speaker diarization model...")

        diarize_model = DiarizationPipeline(
            token=hf_token,
            device=DEVICE
        )

        print("Running speaker diarization...")

        diarization_kwargs = {}

        if min_speakers is not None:
            diarization_kwargs["min_speakers"] = min_speakers

        if max_speakers is not None:
            diarization_kwargs["max_speakers"] = max_speakers

        diarize_segments = diarize_model(
            audio,
            **diarization_kwargs
        )

        print("Speaker diarization completed.")

        print("\nAssigning speakers...")

        result = whisperx.assign_word_speakers(
            diarize_segments,
            result
        )

        print("Speaker assignment completed.")

    except Exception as e:
        print(f"\n[WARNING] Speaker diarization could not be completed: {e}")
        print("[INFO] Proceeding with transcribed dialogue turns without diarization...")



    # --------------------------------------------------------
    # 7. Create structured transcript
    # --------------------------------------------------------

    transcript_segments = []

    for segment in result["segments"]:

        start = segment.get("start")
        end = segment.get("end")

        speaker = normalize_speaker_label(
            segment.get(
                "speaker",
                "UNKNOWN"
            )
        )

        raw_text = segment.get(
            "text",
            ""
        ).strip()

        if not raw_text:
            continue

        cleaned_text = clean_text(
            raw_text
        )

        if not cleaned_text:
            continue

        transcript_segments.append(
            {
                "speaker": speaker,
                "start": (
                    round(start, 2)
                    if start is not None
                    else None
                ),
                "end": (
                    round(end, 2)
                    if end is not None
                    else None
                ),
                "raw_text": raw_text,
                "clean_text": cleaned_text
            }
        )


    # --------------------------------------------------------
    # 8. Create output object
    # --------------------------------------------------------

    output = {
        "meeting_id": audio_file.stem,
        "language": result.get(
            "language",
            LANGUAGE
        ),
        "source": "audio",
        "audio_file": str(audio_file),
        "segments": transcript_segments
    }


    # --------------------------------------------------------
    # 9. Save JSON
    # --------------------------------------------------------

    if output_file is None:

        output_dir = Path(
            "../data/processed"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            output_dir /
            f"{audio_file.stem}_speaker_transcript.json"
        )

    else:

        output_file = Path(
            output_file
        )

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )


    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )


    # --------------------------------------------------------
    # 10. Display transcript
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("SPEAKER-AWARE TRANSCRIPT")
    print("=" * 70)

    for segment in transcript_segments:

        print(
            f"[{segment['start']:.2f} --> "
            f"{segment['end']:.2f}] "
            f"{segment['speaker']}: "
            f"{segment['clean_text']}"
        )


    print("\n")
    print("=" * 70)
    print(
        f"JSON saved to: {output_file}"
    )
    print("=" * 70)


    return output


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print("\nUsage:")
        print(
            "python speaker_aware_transcription.py <audio_file>"
        )

        print("\nExample:")
        print(
            r"python speaker_aware_transcription.py meeting.wav"
        )

        sys.exit(1)

    audio_path = sys.argv[1]

    transcribe_audio(
        audio_path
    )