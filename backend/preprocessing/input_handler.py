from pathlib import Path


# Audio formats supported by our system
AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
    ".ogg",
    ".webm",
    ".mp4"
}

# Text transcript formats
TEXT_EXTENSIONS = {
    ".txt"
}


def validate_input(file_path: str) -> str:
    """
    Validate the input file and determine its type.

    Returns:
        "audio" or "text"
    """

    path = Path(file_path)

    # Check whether file exists
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    # Check that it is actually a file
    if not path.is_file():
        raise ValueError(
            f"Input path is not a file: {file_path}"
        )

    extension = path.suffix.lower()

    # Audio input
    if extension in AUDIO_EXTENSIONS:
        return "audio"

    # Existing transcript
    if extension in TEXT_EXTENSIONS:
        return "text"

    raise ValueError(
        f"Unsupported file format: {extension}"
    )