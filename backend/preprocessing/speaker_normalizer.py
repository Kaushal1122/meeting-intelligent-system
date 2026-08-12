import re


def normalize_speaker_label(speaker: str) -> str:
    """
    Normalize anonymous speaker labels while preserving
    meaningful speaker names.
    """

    if not isinstance(speaker, str):
        return "UNKNOWN"

    speaker = speaker.strip()

    if not speaker:
        return "UNKNOWN"

    # Normalize multiple spaces
    speaker = re.sub(r"\s+", " ", speaker)

    # Convert:
    # SPEAKER_1
    # speaker 1
    # Speaker-1
    # participant 1
    # PARTICIPANT_01
    #
    # into:
    # SPEAKER_01
    match = re.fullmatch(
        r"(?:speaker|participant)[\s_-]*(\d+)",
        speaker,
        re.IGNORECASE
    )

    if match:
        number = int(match.group(1))
        return f"SPEAKER_{number:02d}"

    # Preserve actual names
    return speaker