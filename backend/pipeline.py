import sys
import json
from pathlib import Path

from speaker_aware_transcription import (
    transcribe_audio
)

from summarization.topic_segmenter import (
    segment_transcript
)

from summarization.summarizer import (
    summarize_text
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PROJECT_DIR = BASE_DIR.parent

PROCESSED_DIR = (
    PROJECT_DIR
    / "data"
    / "processed"
)


# ============================================================
# PREPARE SENTENCES
# ============================================================

def prepare_sentences(data):

    sentences = []

    if not isinstance(data, dict):
        return sentences

    segments = data.get(
        "segments",
        []
    )

    if not isinstance(segments, list):
        return sentences

    for index, segment in enumerate(segments):

        if not isinstance(segment, dict):
            continue

        segment_id = segment.get(
            "segment_id",
            index + 1
        )

        speaker = segment.get(
            "speaker",
            "UNKNOWN"
        )

        text = segment.get(
            "clean_text",
            segment.get(
                "text",
                ""
            )
        )

        if text is None:
            continue

        text = str(text).strip()

        if not text:
            continue

        sentences.append({

            "segment_id": segment_id,

            "speaker": speaker,

            "text": text,

            "start": segment.get(
                "start"
            ),

            "end": segment.get(
                "end"
            )

        })

    return sentences


# ============================================================
# CONVERT TOPIC TO TEXT
# ============================================================

def topic_to_text(topic):

    if not isinstance(topic, list):
        return ""

    texts = []

    for segment in topic:

        if not isinstance(segment, dict):
            continue

        text = segment.get(
            "text",
            segment.get(
                "clean_text",
                ""
            )
        )

        if text is None:
            continue

        text = str(text).strip()

        if text:
            texts.append(text)

    return " ".join(texts)


# ============================================================
# PREPARE TOPIC DATA
# ============================================================

def prepare_topic_data(topics):

    topic_data = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        if not isinstance(topic, list):
            continue

        if not topic:
            continue

        topic_text = topic_to_text(
            topic
        )

        if not topic_text:
            continue

        # ----------------------------------------------------
        # Speakers
        # ----------------------------------------------------

        speakers = sorted(

            set(

                segment.get(
                    "speaker",
                    "UNKNOWN"
                )

                for segment in topic

                if isinstance(
                    segment,
                    dict
                )

            )

        )

        # ----------------------------------------------------
        # Start timestamp
        # ----------------------------------------------------

        start_time = None

        for segment in topic:

            if not isinstance(segment, dict):
                continue

            if segment.get("start") is not None:

                start_time = segment.get(
                    "start"
                )

                break

        # ----------------------------------------------------
        # End timestamp
        # ----------------------------------------------------

        end_time = None

        for segment in reversed(topic):

            if not isinstance(segment, dict):
                continue

            if segment.get("end") is not None:

                end_time = segment.get(
                    "end"
                )

                break

        # ----------------------------------------------------
        # Source segment IDs
        # ----------------------------------------------------

        source_segment_ids = []

        for segment in topic:

            if not isinstance(segment, dict):
                continue

            segment_id = segment.get(
                "segment_id"
            )

            if segment_id is not None:

                source_segment_ids.append(
                    segment_id
                )

        # ----------------------------------------------------
        # Store topic
        # ----------------------------------------------------

        topic_data.append({

            "topic_id": index,

            "segment_count": len(topic),

            "speakers": speakers,

            "start": start_time,

            "end": end_time,

            "text": topic_text,

            "segments": topic,

            "source_segment_ids":
                source_segment_ids

        })

    return topic_data


# ============================================================
# LOAD EXISTING TRANSCRIPT
# ============================================================

def load_existing_transcript(
    transcript_file
):

    transcript_file = Path(
        transcript_file
    ).resolve()

    print("\n" + "=" * 70)
    print("LOADING EXISTING TRANSCRIPT")
    print("=" * 70)

    print(
        f"\nTranscript:\n"
        f"{transcript_file}"
    )

    if not transcript_file.exists():

        raise FileNotFoundError(

            f"Transcript file not found:\n"
            f"{transcript_file}"

        )

    try:

        with open(
            transcript_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    except json.JSONDecodeError as e:

        raise RuntimeError(

            "Transcript JSON is invalid:\n"
            f"{e}"

        )

    if not isinstance(data, dict):

        raise RuntimeError(
            "Transcript must contain a JSON object."
        )

    segments = data.get(
        "segments"
    )

    if not isinstance(
        segments,
        list
    ):

        raise RuntimeError(

            "Transcript JSON must contain "
            "a 'segments' list."

        )

    if not segments:

        raise RuntimeError(

            "Transcript contains no segments."

        )

    print(
        "\n✓ Transcript loaded successfully."
    )

    print(
        f"✓ Raw segments: {len(segments)}"
    )

    return data


# ============================================================
# VALIDATE MEMBER 2 OUTPUT
# ============================================================

def validate_member2_output(
    topic_summaries
):

    if not topic_summaries:

        raise RuntimeError(
            "Member 2 produced no topic summaries."
        )

    required_fields = [

        "topic_id",
        "segment_count",
        "speakers",
        "start",
        "end",
        "text",
        "summary",
        "source_segment_ids",
        "segments"

    ]

    for topic in topic_summaries:

        missing_fields = [

            field

            for field in required_fields

            if field not in topic

        ]

        if missing_fields:

            raise RuntimeError(

                f"Topic "
                f"{topic.get('topic_id', '?')} "
                f"is missing fields: "
                f"{missing_fields}"

            )

        if not isinstance(
            topic["text"],
            str
        ):

            raise RuntimeError(

                f"Topic {topic['topic_id']} "
                f"text is not a string."

            )

        if not topic["text"].strip():

            raise RuntimeError(

                f"Topic {topic['topic_id']} "
                f"contains no source text."

            )

        if not isinstance(
            topic["summary"],
            str
        ):

            raise RuntimeError(

                f"Topic {topic['topic_id']} "
                f"summary is not a string."

            )

        if not topic["summary"].strip():

            raise RuntimeError(

                f"Topic {topic['topic_id']} "
                f"contains an empty summary."

            )

        if not isinstance(
            topic["source_segment_ids"],
            list
        ):

            raise RuntimeError(

                f"Topic {topic['topic_id']} "
                f"has invalid source_segment_ids."

            )

        if not isinstance(
            topic["segments"],
            list
        ):

            raise RuntimeError(

                f"Topic {topic['topic_id']} "
                f"has invalid segments."

            )


# ============================================================
# RUN MEMBER 2
# ============================================================

def process_transcript(
    transcript_data,
    meeting_id,
    audio_file=None
):

    # ========================================================
    # STEP 1 — PREPARE TRANSCRIPT
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "STEP 1: PREPARING TRANSCRIPT "
        "FOR TOPIC ANALYSIS"
    )

    print("=" * 70)

    sentences = prepare_sentences(
        transcript_data
    )

    print(
        f"\nPrepared {len(sentences)} "
        f"usable transcript segments."
    )

    if not sentences:

        raise RuntimeError(

            "No usable transcript segments found."

        )


    # ========================================================
    # STEP 2 — TOPIC SEGMENTATION
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "STEP 2: SEMANTIC TOPIC SEGMENTATION"
    )

    print("=" * 70)

    topics = segment_transcript(
        sentences
    )

    print(
        f"\nDetected {len(topics)} topics."
    )

    if not topics:

        raise RuntimeError(
            "No meaningful topics detected."
        )


    # ========================================================
    # STEP 3 — TOPIC CONTEXT
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "STEP 3: PREPARING TOPIC CONTEXT"
    )

    print("=" * 70)

    topic_data = prepare_topic_data(
        topics
    )

    if not topic_data:

        raise RuntimeError(

            "Topic segmentation produced "
            "no usable topic data."

        )


    for topic in topic_data:

        print(
            f"\nTopic {topic['topic_id']}"
        )

        print(
            f"Segments: "
            f"{topic['segment_count']}"
        )

        print(
            f"Speakers: "
            f"{', '.join(topic['speakers'])}"
        )

        print(
            f"Source IDs: "
            f"{topic['source_segment_ids']}"
        )

        preview = topic["text"][:300]

        if len(topic["text"]) > 300:

            preview += "..."

        print(
            f"Preview: {preview}"
        )


    # ========================================================
    # STEP 4 — BART SUMMARIZATION
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "STEP 4: GENERATING CONTEXT-AWARE "
        "TOPIC SUMMARIES"
    )

    print("=" * 70)

    topic_summaries = []

    for topic in topic_data:

        print(

            f"\nSummarizing Topic "
            f"{topic['topic_id']}..."

        )

        summary = summarize_text(
            topic["text"]
        )

        topic_summaries.append({

            "topic_id":
                topic["topic_id"],

            "segment_count":
                topic["segment_count"],

            "speakers":
                topic["speakers"],

            "start":
                topic["start"],

            "end":
                topic["end"],

            # Source text for Member 3
            "text":
                topic["text"],

            # BART result
            "summary":
                summary,

            # Provenance
            "source_segment_ids":
                topic["source_segment_ids"],

            # Original segments
            "segments":
                topic["segments"]

        })


    # ========================================================
    # STEP 5 — VALIDATION
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "STEP 5: VALIDATING MEMBER 2 OUTPUT"
    )

    print("=" * 70)

    validate_member2_output(
        topic_summaries
    )

    print(
        "\n✓ All topic outputs passed validation."
    )


    # ========================================================
    # STEP 6 — DISPLAY RESULTS
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "STEP 6: FINAL TOPIC SUMMARIES"
    )

    print("=" * 70)

    for topic in topic_summaries:

        print(

            f"\nTopic "
            f"{topic['topic_id']}"

        )

        print(

            f"Source segments: "
            f"{topic['source_segment_ids']}"

        )

        print(

            f"Summary:\n"
            f"{topic['summary']}"

        )


    # ========================================================
    # FINAL MEMBER 2 OUTPUT
    # ========================================================

    final_output = {

        "meeting_id":
            meeting_id,

        "audio_file":
            audio_file.relative_to(PROJECT_DIR).as_posix()
            if audio_file
            else None,

        "input_type":
            (
                "audio"
                if audio_file
                else "transcript"
            ),

        "processing_stage":
            "member_2_complete",

        "pipeline_scope": [

            "transcript_preparation",

            "semantic_topic_segmentation",

            "topic_context_generation",

            "topic_wise_bart_summarization"

        ],

        "transcript_segment_count":
            len(sentences),

        "topic_count":
            len(topic_summaries),

        "topics":
            topic_summaries

    }


    # ========================================================
    # SAVE RESULT
    # ========================================================

    output_file = (

        PROCESSED_DIR
        /
        f"{meeting_id}"
        f"_member2_results.json"

    )

    with open(

        output_file,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            final_output,

            f,

            indent=4,

            ensure_ascii=False

        )


    print("\n" + "=" * 70)

    print(
        "MEMBER 2 PIPELINE COMPLETED"
    )

    print("=" * 70)

    print(
        "\nCompleted modules:"
    )

    print(
        "✓ Transcript Preparation"
    )

    print(
        "✓ Semantic Topic Segmentation"
    )

    print(
        "✓ Topic Context Generation"
    )

    print(
        "✓ BART Topic-wise Summarization"
    )

    print(
        "✓ Member 2 Output Validation"
    )

    print(
        "\nMember 3 and Member 4 modules "
        "have NOT been executed."
    )

    print(
        f"\nResults saved to:\n"
        f"{output_file}"
    )

    return final_output


# ============================================================
# AUDIO PIPELINE
# ============================================================

def run_audio_pipeline(
    audio_file,
    force_transcription=False
):

    audio_file = Path(
        audio_file
    ).resolve()

    if not audio_file.exists():

        raise FileNotFoundError(

            f"Audio file not found:\n"
            f"{audio_file}"

        )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    transcript_file = (

        PROCESSED_DIR
        /
        f"{audio_file.stem}"
        f"_speaker_transcript.json"

    )


    # ========================================================
    # TRANSCRIPT REUSE
    # ========================================================

    if (
        transcript_file.exists()
        and
        not force_transcription
    ):

        print("\n" + "=" * 70)

        print(
            "EXISTING TRANSCRIPT DETECTED"
        )

        print("=" * 70)

        print(
            "\n✓ Skipping audio transcription."
        )

        transcript_data = load_existing_transcript(
            transcript_file
        )


    # ========================================================
    # NEW TRANSCRIPTION
    # ========================================================

    else:

        print("\n" + "=" * 70)

        print(
            "STEP 1: AUDIO TRANSCRIPTION + "
            "SPEAKER DIARIZATION"
        )

        print("=" * 70)

        transcript_data = transcribe_audio(

            audio_file,

            output_file=transcript_file

        )

        if not transcript_data:

            raise RuntimeError(

                "Audio transcription returned "
                "no data."

            )


    return process_transcript(

        transcript_data,

        meeting_id=audio_file.stem,

        audio_file=audio_file

    )


# ============================================================
# TRANSCRIPT PIPELINE
# ============================================================

def run_transcript_pipeline(
    transcript_file
):

    transcript_file = Path(
        transcript_file
    ).resolve()

    if not transcript_file.exists():

        raise FileNotFoundError(

            f"Transcript file not found:\n"
            f"{transcript_file}"

        )

    transcript_data = load_existing_transcript(
        transcript_file
    )

    meeting_id = transcript_file.stem

    # Remove common suffixes so output names
    # remain clean.

    suffixes = [

        "_speaker_transcript",
        "_transcript"

    ]

    for suffix in suffixes:

        if meeting_id.endswith(suffix):

            meeting_id = meeting_id[
                :-len(suffix)
            ]

            break

    return process_transcript(

        transcript_data,

        meeting_id=meeting_id,

        audio_file=None

    )


# ============================================================
# MAIN
# ============================================================

def print_usage():

    print("\nUsage:")

    print(
        "  python pipeline.py --audio <audio_file>"
    )

    print(
        "  python pipeline.py --transcript <json_file>"
    )

    print(
        "  python pipeline.py --audio <audio_file> "
        "--transcript <json_file>"
    )

    print("\nExamples:")

    print(
        r"  python pipeline.py --audio meeting.wav"
    )

    print(
        r"  python pipeline.py --transcript meeting_speaker_transcript.json"
    )

    print(
        r"  python pipeline.py --audio meeting.wav "
        r"--transcript meeting_speaker_transcript.json"
    )

    print("\nOptions:")

    print(
        "  --force-transcription"
        "  Regenerate transcript from audio."
    )


if __name__ == "__main__":

    args = sys.argv[1:]


    # ========================================================
    # NO ARGUMENTS
    # ========================================================

    if not args:

        print_usage()

        sys.exit(1)


    # ========================================================
    # READ ARGUMENTS
    # ========================================================

    audio_path = None

    transcript_path = None

    force_transcription = False

    i = 0

    while i < len(args):

        argument = args[i]


        if argument == "--audio":

            if i + 1 >= len(args):

                print(
                    "\nError: "
                    "--audio requires a file path."
                )

                sys.exit(1)

            audio_path = args[i + 1]

            i += 2

            continue


        if argument == "--transcript":

            if i + 1 >= len(args):

                print(
                    "\nError: "
                    "--transcript requires a file path."
                )

                sys.exit(1)

            transcript_path = args[i + 1]

            i += 2

            continue


        if argument == "--force-transcription":

            force_transcription = True

            i += 1

            continue


        if argument in (
            "--help",
            "-h"
        ):

            print_usage()

            sys.exit(0)


        print(
            f"\nUnknown argument: {argument}"
        )

        print_usage()

        sys.exit(1)


    # ========================================================
    # VALIDATE ARGUMENT COMBINATION
    # ========================================================

    if not audio_path and not transcript_path:

        print(
            "\nError: "
            "Provide --audio or --transcript."
        )

        print_usage()

        sys.exit(1)


    if (
        force_transcription
        and
        not audio_path
    ):

        print(

            "\nError: "
            "--force-transcription requires "
            "--audio."

        )

        sys.exit(1)


    # ========================================================
    # BOTH AUDIO + TRANSCRIPT
    # ========================================================

    if audio_path and transcript_path:

        print("\n" + "=" * 70)

        print(
            "AUDIO + TRANSCRIPT INPUT"
        )

        print("=" * 70)

        print(
            "\n✓ Both inputs were provided."
        )

        print(
            "✓ Existing transcript will be used."
        )

        print(
            "✓ Audio will NOT be retranscribed."
        )

        print(
            "\nUse --force-transcription if "
            "you want to regenerate the transcript "
            "from audio."
        )

        transcript_data = load_existing_transcript(
            transcript_path
        )

        transcript_file = Path(
            transcript_path
        ).resolve()

        meeting_id = transcript_file.stem

        suffixes = [

            "_speaker_transcript",
            "_transcript"

        ]

        for suffix in suffixes:

            if meeting_id.endswith(suffix):

                meeting_id = meeting_id[
                    :-len(suffix)
                ]

                break

        process_transcript(

            transcript_data,

            meeting_id=meeting_id,

            audio_file=Path(
                audio_path
            ).resolve()

        )

        sys.exit(0)


    # ========================================================
    # TRANSCRIPT ONLY
    # ========================================================

    if transcript_path:

        print("\n" + "=" * 70)

        print(
            "TRANSCRIPT-ONLY INPUT"
        )

        print("=" * 70)

        print(
            "\n✓ Skipping audio transcription."
        )

        run_transcript_pipeline(
            transcript_path
        )

        sys.exit(0)


    # ========================================================
    # AUDIO ONLY
    # ========================================================

    if audio_path:

        print("\n" + "=" * 70)

        print(
            "AUDIO INPUT"
        )

        print("=" * 70)

        print(
            "\n✓ Audio will be processed."
        )

        run_audio_pipeline(

            audio_path,

            force_transcription=
                force_transcription

        )

        sys.exit(0)