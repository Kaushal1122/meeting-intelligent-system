import re
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "facebook/bart-large-cnn"

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

MAX_INPUT_TOKENS = 900

MAX_OUTPUT_TOKENS = 100

MIN_OUTPUT_TOKENS = 12

SHORT_TEXT_WORD_LIMIT = 12


# ============================================================
# LOAD MODEL
# ============================================================

print(
    "Loading BART summarization model..."
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME
)

model.to(
    DEVICE
)

model.eval()

print(
    "BART summarization model loaded."
)

print(
    "Device:",
    DEVICE
)


# ============================================================
# FILLER WORDS
# ============================================================

FILLER_WORDS = {

    "ok",
    "okay",
    "right",
    "great",
    "yeah",
    "yes",
    "no",
    "uh-huh",
    "mm-hmm",
    "sure",
    "good",
    "fine",
    "alright",
    "all right"

}


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_dialogue(text):

    if not text:
        return ""

    text = str(text)

    # --------------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()


    if not text:
        return ""


    # --------------------------------------------------------
    # Split into sentences
    # --------------------------------------------------------

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )


    cleaned = []


    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue


        normalized = (

            sentence.lower()

            .replace(".", "")
            .replace(",", "")
            .replace("!", "")
            .replace("?", "")

            .strip()

        )


        # ----------------------------------------------------
        # Ignore pure filler sentences
        # ----------------------------------------------------

        if normalized in FILLER_WORDS:
            continue


        words = normalized.split()


        if (

            len(words) <= 2

            and

            all(
                word in FILLER_WORDS
                for word in words
            )

        ):

            continue


        cleaned.append(
            sentence
        )


    return " ".join(
        cleaned
    )


# ============================================================
# SHORT TEXT CHECK
# ============================================================

def is_short_text(text):

    if not text:
        return True

    return (

        len(
            text.split()
        )

        <= SHORT_TEXT_WORD_LIMIT

    )


# ============================================================
# SUMMARIZE CHUNK
# ============================================================

def summarize_chunk(text):

    text = clean_dialogue(
        text
    )


    if not text:
        return ""


    # Very short text does not need BART.
    if is_short_text(text):
        return text


    # --------------------------------------------------------
    # Tokenization
    # --------------------------------------------------------

    inputs = tokenizer(

        text,

        return_tensors="pt",

        max_length=MAX_INPUT_TOKENS,

        truncation=True

    )


    inputs = {

        key: value.to(DEVICE)

        for key, value in inputs.items()

    }


    # --------------------------------------------------------
    # Generate summary
    # --------------------------------------------------------

    with torch.no_grad():

        summary_ids = model.generate(

            **inputs,

            max_new_tokens=MAX_OUTPUT_TOKENS,

            min_new_tokens=MIN_OUTPUT_TOKENS,

            num_beams=4,

            length_penalty=1.5,

            no_repeat_ngram_size=3,

            repetition_penalty=1.15,

            early_stopping=True

        )


    # --------------------------------------------------------
    # Decode
    # --------------------------------------------------------

    summary = tokenizer.decode(

        summary_ids[0],

        skip_special_tokens=True

    )


    return summary.strip()


# ============================================================
# SPLIT LONG TEXT
# ============================================================

def split_into_chunks(text):

    text = clean_dialogue(
        text
    )


    if not text:
        return []


    sentences = re.split(

        r"(?<=[.!?])\s+",

        text

    )


    chunks = []

    current_chunk = []

    current_tokens = 0


    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue


        token_count = len(

            tokenizer.encode(

                sentence,

                add_special_tokens=False

            )

        )


        # ----------------------------------------------------
        # If one sentence itself is very long
        # ----------------------------------------------------

        if (

            token_count
            > MAX_INPUT_TOKENS

        ):

            if current_chunk:

                chunks.append(

                    " ".join(
                        current_chunk
                    )

                )

                current_chunk = []

                current_tokens = 0


            chunks.append(
                sentence
            )

            continue


        # ----------------------------------------------------
        # Start a new chunk when limit is reached
        # ----------------------------------------------------

        if (

            current_chunk

            and

            current_tokens + token_count
            > MAX_INPUT_TOKENS

        ):

            chunks.append(

                " ".join(
                    current_chunk
                )

            )

            current_chunk = [
                sentence
            ]

            current_tokens = token_count


        else:

            current_chunk.append(
                sentence
            )

            current_tokens += token_count


    if current_chunk:

        chunks.append(

            " ".join(
                current_chunk
            )

        )


    return chunks


# ============================================================
# SUMMARIZE COMPLETE TEXT
# ============================================================

def summarize_text(text):

    text = clean_dialogue(
        text
    )


    if not text:
        return ""


    if is_short_text(text):
        return text


    chunks = split_into_chunks(
        text
    )


    if not chunks:
        return ""


    summaries = []


    for index, chunk in enumerate(

        chunks,

        start=1

    ):

        print(

            f"Summarizing chunk "
            f"{index}/{len(chunks)}..."

        )


        summary = summarize_chunk(
            chunk
        )


        if summary:

            summaries.append(
                summary
            )


    if not summaries:
        return ""


    # Only one BART call was necessary.
    if len(summaries) == 1:

        return summaries[0]


    # --------------------------------------------------------
    # Combine chunk summaries
    # --------------------------------------------------------

    combined_summary = " ".join(
        summaries
    )


    # --------------------------------------------------------
    # If combined result is already short,
    # avoid another expensive BART call.
    # --------------------------------------------------------

    if is_short_text(
        combined_summary
    ):

        return combined_summary


    print(
        "Generating final combined summary..."
    )


    return summarize_chunk(
        combined_summary
    )


# ============================================================
# TOPIC TO TEXT
# ============================================================

def topic_to_text(topic):

    if isinstance(
        topic,
        dict
    ):

        topic = topic.get(
            "segments",
            []
        )


    if not isinstance(
        topic,
        list
    ):

        return ""


    texts = []


    for segment in topic:

        if isinstance(
            segment,
            dict
        ):

            text = segment.get(

                "text",

                segment.get(
                    "clean_text",
                    ""
                )

            )

        else:

            text = str(
                segment
            )


        text = str(
            text
        ).strip()


        if text:

            texts.append(
                text
            )


    return " ".join(
        texts
    )


# ============================================================
# TOPIC-WISE SUMMARIZATION
# ============================================================

def summarize_topics(topics):

    results = []


    if not topics:
        return results


    for index, topic in enumerate(

        topics,

        start=1

    ):

        print(

            f"\nSummarizing topic "
            f"{index}/{len(topics)}..."

        )


        topic_text = topic_to_text(
            topic
        )


        if not topic_text:
            continue


        summary = summarize_text(
            topic_text
        )


        results.append({

            "topic_id": index,

            "summary": summary

        })


    return results