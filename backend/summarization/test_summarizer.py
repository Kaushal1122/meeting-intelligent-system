import os

from transcript_loader import (
    load_transcript
)

from topic_segmenter import (
    segment_transcript
)

from summarizer import (
    summarize_topics
)


def main():

    # ------------------------------------------------
    # Find project root
    # ------------------------------------------------

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

    # ------------------------------------------------
    # Transcript path
    # ------------------------------------------------

    file_path = os.path.join(
        BASE_DIR,
        "data",
        "processed",
        "test_transcript.json"
    )

    print("=" * 70)
    print("       TOPIC-WISE BART SUMMARIZATION TEST")
    print("=" * 70)

    # ------------------------------------------------
    # 1. Load transcript
    # ------------------------------------------------

    print("\nLoading transcript...")

    transcript = load_transcript(
        file_path
    )

    print("Transcript loaded successfully.")

    # ------------------------------------------------
    # 2. Build speaker-aware transcript
    # ------------------------------------------------

    segments = [
        {
            "speaker": segment.get("speaker", "UNKNOWN"),
            "text": segment.get("clean_text", ""),
            "start": segment.get("start"),
            "end": segment.get("end")
        }
        for segment in transcript["segments"]
        if segment.get("clean_text")
    ]

    print("\nInput segments:")
    print("-" * 60)

    for segment in segments:
        print(
            f"{segment['speaker']}: "
            f"{segment['text']}"
        )

    # ------------------------------------------------
    # 3. Topic segmentation
    # ------------------------------------------------

    print("\n")
    print("Running topic segmentation...")
    print("-" * 70)

    topics = segment_transcript(
        segments
    )

    print(
        f"\nDetected {len(topics)} topics."
    )

    # ------------------------------------------------
    # 4. Display detected topics
    # ------------------------------------------------

    print("\n")
    print("=" * 70)
    print("                    DETECTED TOPICS")
    print("=" * 70)

    for index, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"\nTopic {index}:"
        )

        for sentence in topic:

            print(
                "  -",
                sentence
            )

    # ------------------------------------------------
    # 5. Topic-wise BART summarization
    # ------------------------------------------------

    print("\n")
    print("=" * 70)
    print("              GENERATING TOPIC SUMMARIES")
    print("=" * 70)

    topic_summaries = summarize_topics(
        topics
    )

    # ------------------------------------------------
    # 6. Display topic summaries
    # ------------------------------------------------

    print("\n")
    print("=" * 70)
    print("                  TOPIC SUMMARIES")
    print("=" * 70)

    for result in topic_summaries:

        print(
            f"\nTopic {result['topic_id']}:"
        )

        print(
            result["summary"]
        )

    # ------------------------------------------------
    # 7. Final test status
    # ------------------------------------------------

    print("\n")
    print("=" * 70)
    print("       TOPIC-WISE BART TEST PASSED")
    print("=" * 70)



if __name__ == "__main__":
    main()