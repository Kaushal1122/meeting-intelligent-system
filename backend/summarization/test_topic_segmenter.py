import os

from transcript_loader import (
    load_transcript,
    build_transcript_text
)

from topic_segmenter import (
    segment_transcript
)


def main():

    # -----------------------------------------
    # Find project root
    # -----------------------------------------

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

    file_path = os.path.join(
        BASE_DIR,
        "data",
        "processed",
        "test_transcript.json"
    )

    print("=" * 60)
    print("       TOPIC SEGMENTATION TEST")
    print("=" * 60)

    # -----------------------------------------
    # Load transcript
    # -----------------------------------------

    print("\nLoading transcript...")

    transcript = load_transcript(file_path)

    print("Transcript loaded successfully.")

    # -----------------------------------------
    # Build clean transcript text
    # -----------------------------------------

    segments = [
        {
            "speaker": segment["speaker"],
            "text": segment["text"],
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

    # -----------------------------------------
    # Perform topic segmentation
    # -----------------------------------------

    print("\n\nRunning topic segmentation...")

    topics = segment_transcript(
        segments
    )

    # -----------------------------------------
    # Display topics
    # -----------------------------------------

    print("\n")
    print("=" * 60)
    print("              DETECTED TOPICS")
    print("=" * 60)

    for i, topic in enumerate(topics, start=1):

        print(f"\nTopic {i}")

        for sentence in topic:
            print(" -", sentence)

    # -----------------------------------------
    # Test completed
    # -----------------------------------------

    print("\n" + "=" * 60)
    print("       TOPIC SEGMENTATION TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()