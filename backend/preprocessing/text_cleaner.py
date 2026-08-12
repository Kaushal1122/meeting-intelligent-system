import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean ASR-generated transcript text without changing its meaning.
    """

    if not isinstance(text, str):
        return ""

    # 1. Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # 2. Remove control characters
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Cc"
        or char in "\n\t"
    )

    # 3. Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # 4. Remove spaces before punctuation
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    # 5. Normalize repeated punctuation
    text = re.sub(r"([!?.,])\1+", r"\1", text)

    # 6. Normalize quotation marks
    text = text.replace("“", '"')
    text = text.replace("”", '"')
    text = text.replace("‘", "'")
    text = text.replace("’", "'")

    # 7. Remove accidental leading/trailing punctuation spacing
    text = text.strip()

    return text