import json
from pathlib import Path


REQUIRED_SEGMENT_FIELDS = {
    "speaker",
    "start",
    "end",
    "raw_text",
    "clean_text"
}


def validate_transcript(file_path):

    path = Path(file_path)

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return False

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    errors = []

    # Top-level validation
    for field in ["meeting_id", "language", "source", "segments"]:
        if field not in data:
            errors.append(
                f"Missing top-level field: {field}"
            )

    if not isinstance(data.get("segments"), list):
        errors.append("segments must be a list")
        return False

    # Segment validation
    for index, segment in enumerate(data["segments"]):

        missing = REQUIRED_SEGMENT_FIELDS - set(segment.keys())

        if missing:
            errors.append(
                f"Segment {index}: missing {missing}"
            )

        if not segment.get("speaker"):
            errors.append(
                f"Segment {index}: missing speaker"
            )

        if not segment.get("raw_text"):
            errors.append(
                f"Segment {index}: empty raw_text"
            )

        if not segment.get("clean_text"):
            errors.append(
                f"Segment {index}: empty clean_text"
            )

        start = segment.get("start")
        end = segment.get("end")

        if start is not None and end is not None:
            if start < 0:
                errors.append(
                    f"Segment {index}: negative start time"
                )

            if end < start:
                errors.append(
                    f"Segment {index}: end before start"
                )

    if errors:

        print("\nVALIDATION FAILED")
        print("=" * 50)

        for error in errors:
            print("-", error)

        return False

    print("\nTRANSCRIPT VALIDATION PASSED")
    print("=" * 50)
    print(f"Meeting ID : {data['meeting_id']}")
    print(f"Language   : {data['language']}")
    print(f"Source     : {data['source']}")
    print(f"Segments   : {len(data['segments'])}")

    speakers = sorted(
        set(
            segment["speaker"]
            for segment in data["segments"]
        )
    )

    print(f"Speakers   : {len(speakers)}")
    print("Labels     :", ", ".join(speakers))

    return True


if __name__ == "__main__":

    validate_transcript(
        r"..\data\processed\ES2002a_speaker_transcript.json"
    )