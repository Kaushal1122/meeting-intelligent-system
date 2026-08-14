import os

from transcript_loader import (
    load_transcript,
    get_clean_transcript,
    build_transcript_text
)


def main():

    # ------------------------------------------------
    # Path to processed transcript
    # ------------------------------------------------

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
    print("        TRANSCRIPT LOADER TEST")
    print("=" * 60)

    # ------------------------------------------------
    # 1. Load transcript
    # ------------------------------------------------

    print("\nLoading transcript...")

    transcript = load_transcript(file_path)

    print("Transcript loaded successfully.")

    # ------------------------------------------------
    # 2. Display metadata
    # ------------------------------------------------

    print("\nMeeting ID:")
    print(transcript["meeting_id"])

    print("\nLanguage:")
    print(transcript["language"])

    print("\nSource:")
    print(transcript["source"])

    # ------------------------------------------------
    # 3. Extract clean segments
    # ------------------------------------------------

    clean_segments = get_clean_transcript(
        transcript
    )

    print("\nNumber of clean segments:")
    print(len(clean_segments))

    # ------------------------------------------------
    # 4. Display first segment
    # ------------------------------------------------

    if clean_segments:

        first = clean_segments[0]

        print("\nFirst segment:")
        print("Speaker:", first["speaker"])
        print("Text:", first["text"])
        print("Start:", first["start"])
        print("End:", first["end"])

    # ------------------------------------------------
    # 5. Build speaker-aware transcript
    # ------------------------------------------------

    print("\nSpeaker-aware transcript:")
    print("-" * 60)

    formatted_text = build_transcript_text(
        transcript
    )

    print(formatted_text)

    # ------------------------------------------------
    # 6. Test completed
    # ------------------------------------------------

    print("\n" + "=" * 60)
    print("       TRANSCRIPT LOADER TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()