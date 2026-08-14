import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# SEMANTIC MODEL
# ============================================================

print("Loading semantic model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Semantic model loaded.")


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_THRESHOLD = 0.38

# Minimum number of segments required before
# creating a new topic boundary.
DEFAULT_MIN_TOPIC_SIZE = 3

# Number of consecutive low-similarity segments
# required to confirm a topic change.
DEFAULT_PATIENCE = 3

# Number of recent meaningful segments used
# to calculate the current topic centroid.
RECENT_WINDOW = 4

# Very low similarity indicates a strong
# semantic topic change.
STRONG_BOUNDARY_THRESHOLD = 0.22


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
    "all right",
    "thanks",
    "thank you",
    "okay then",
    "very good"
}


# ============================================================
# GET SEGMENT TEXT
# ============================================================

def get_segment_text(segment):

    if isinstance(segment, dict):

        text = segment.get(
            "text",
            segment.get(
                "clean_text",
                ""
            )
        )

        if text is None:
            return ""

        return str(text).strip()


    if segment is None:
        return ""


    return str(segment).strip()


# ============================================================
# NORMALIZE TEXT FOR FILLER CHECK
# ============================================================

def normalize_for_filler_check(text):

    return (
        text.lower()
        .replace(".", "")
        .replace(",", "")
        .replace("!", "")
        .replace("?", "")
        .strip()
    )


# ============================================================
# FILLER DETECTION
# ============================================================

def is_filler_text(text):

    if not text:
        return True


    normalized = normalize_for_filler_check(
        text
    )


    # --------------------------------------------------------
    # Exact filler sentence
    # --------------------------------------------------------

    if normalized in FILLER_WORDS:
        return True


    # --------------------------------------------------------
    # Combination of filler words
    # Example:
    # "okay yeah"
    # "yes right"
    # --------------------------------------------------------

    words = normalized.split()


    if (
        len(words) <= 2
        and
        all(
            word in FILLER_WORDS
            for word in words
        )
    ):

        return True


    return False


def is_filler_segment(segment):

    return is_filler_text(
        get_segment_text(segment)
    )


# ============================================================
# VECTOR NORMALIZATION
# ============================================================

def normalize_vector(vector):

    norm = np.linalg.norm(
        vector
    )


    if norm == 0:
        return vector


    return vector / norm


# ============================================================
# CALCULATE TOPIC CENTROID
# ============================================================

def calculate_centroid(
    embeddings,
    meaningful_indices
):

    if not meaningful_indices:
        return None


    selected_embeddings = np.vstack(

        [
            embeddings[index]
            for index in meaningful_indices
        ]

    )


    centroid = np.mean(
        selected_embeddings,
        axis=0
    )


    return normalize_vector(
        centroid
    )


# ============================================================
# TOPIC SEGMENTATION
# ============================================================

def segment_topics(
    segments,
    threshold=DEFAULT_THRESHOLD,
    min_topic_size=DEFAULT_MIN_TOPIC_SIZE,
    patience=DEFAULT_PATIENCE
):

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    if not segments:
        return []


    # ========================================================
    # STEP 1: REMOVE EMPTY SEGMENTS
    # ========================================================

    valid_segments = []


    for segment in segments:

        if get_segment_text(segment):

            valid_segments.append(
                segment
            )


    if not valid_segments:
        return []


    # ========================================================
    # STEP 2: EXTRACT TEXT
    # ========================================================

    texts = [

        get_segment_text(segment)

        for segment in valid_segments

    ]


    # ========================================================
    # STEP 3: PRE-COMPUTE FILLER INFORMATION
    # ========================================================

    filler_flags = [

        is_filler_text(text)

        for text in texts

    ]


    # ========================================================
    # STEP 4: GENERATE EMBEDDINGS ONCE
    # ========================================================

    print(
        f"Generating embeddings for "
        f"{len(texts)} transcript segments..."
    )


    embeddings = model.encode(

        texts,

        convert_to_numpy=True,

        normalize_embeddings=True,

        show_progress_bar=False

    )


    # ========================================================
    # STEP 5: INITIALIZE
    # ========================================================

    topics = []

    current_topic = []

    current_indices = []

    low_similarity_segments = []

    low_similarity_indices = []


    # ========================================================
    # STEP 6: PROCESS EACH SEGMENT
    # ========================================================

    for i, segment in enumerate(
        valid_segments
    ):

        current_embedding = embeddings[i]


        # ====================================================
        # FIRST SEGMENT
        # ====================================================

        if not current_topic:

            current_topic.append(
                segment
            )

            current_indices.append(
                i
            )

            continue


        # ====================================================
        # FILLER SEGMENTS
        # ====================================================

        # Filler utterances such as "Okay" or "Right"
        # should remain in the current topic and should
        # not create semantic boundaries.

        if filler_flags[i]:

            current_topic.append(
                segment
            )

            current_indices.append(
                i
            )

            continue


        # ====================================================
        # FIND RECENT MEANINGFUL SEGMENTS
        # ====================================================

        meaningful_indices = [

            index

            for index in current_indices

            if not filler_flags[index]

        ]


        meaningful_indices = (

            meaningful_indices[
                -RECENT_WINDOW:
            ]

        )


        # ====================================================
        # CALCULATE CURRENT TOPIC CENTROID
        # ====================================================

        centroid = calculate_centroid(

            embeddings,

            meaningful_indices

        )


        # ====================================================
        # FALLBACK
        # ====================================================

        if centroid is None:

            centroid = current_embedding


        # ====================================================
        # CALCULATE SEMANTIC SIMILARITY
        # ====================================================

        similarity = cosine_similarity(

            [current_embedding],

            [centroid]

        )[0][0]


        print(

            f"Similarity: {similarity:.3f} | "

            f"{texts[i][:80]}"

        )


        # ====================================================
        # SAME TOPIC
        # ====================================================

        if similarity >= threshold:

            # ------------------------------------------------
            # The temporary low-similarity segments were
            # not enough to confirm a topic change.
            # Put them back into the current topic.
            # ------------------------------------------------

            if low_similarity_segments:

                current_topic.extend(
                    low_similarity_segments
                )

                current_indices.extend(
                    low_similarity_indices
                )

                low_similarity_segments = []

                low_similarity_indices = []


            current_topic.append(
                segment
            )

            current_indices.append(
                i
            )

            continue


        # ====================================================
        # POSSIBLE TOPIC CHANGE
        # ====================================================

        low_similarity_segments.append(
            segment
        )

        low_similarity_indices.append(
            i
        )


        # ====================================================
        # STRONG BOUNDARY
        # ====================================================

        strong_boundary = (

            similarity
            <
            STRONG_BOUNDARY_THRESHOLD

        )


        # ====================================================
        # CONFIRM TOPIC CHANGE
        # ====================================================

        boundary_confirmed = (

            len(low_similarity_segments)
            >= patience

            or

            (
                strong_boundary
                and
                len(current_topic) >= min_topic_size
            )

        )


        if not boundary_confirmed:

            continue


        # ====================================================
        # CREATE NEW TOPIC
        # ====================================================

        if len(current_topic) >= min_topic_size:

            # ------------------------------------------------
            # Save the completed topic
            # ------------------------------------------------

            topics.append(
                list(current_topic)
            )


            # ------------------------------------------------
            # Start new topic with the segments that
            # triggered the boundary.
            # ------------------------------------------------

            current_topic = list(
                low_similarity_segments
            )


            current_indices = list(
                low_similarity_indices
            )


        else:

            # ------------------------------------------------
            # Current topic is too small.
            #
            # Instead of creating a meaningless tiny topic,
            # keep the segments together.
            # ------------------------------------------------

            current_topic.extend(
                low_similarity_segments
            )

            current_indices.extend(
                low_similarity_indices
            )


        # ----------------------------------------------------
        # Clear temporary boundary candidates
        # ----------------------------------------------------

        low_similarity_segments = []

        low_similarity_indices = []


    # ========================================================
    # ADD REMAINING LOW-SIMILARITY SEGMENTS
    # ========================================================

    if low_similarity_segments:

        current_topic.extend(
            low_similarity_segments
        )

        current_indices.extend(
            low_similarity_indices
        )


    # ========================================================
    # ADD FINAL TOPIC
    # ========================================================

    if current_topic:

        topics.append(
            list(current_topic)
        )


    # ========================================================
    # RETURN TOPICS
    # ========================================================

    # IMPORTANT:
    #
    # We intentionally do NOT automatically merge small
    # topics here.
    #
    # A small topic can still contain an important event,
    # decision, deadline, responsibility, or issue that
    # Member 3 needs to process.
    #
    return topics


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def segment_transcript(segments):

    return segment_topics(

        segments,

        threshold=DEFAULT_THRESHOLD,

        min_topic_size=DEFAULT_MIN_TOPIC_SIZE,

        patience=DEFAULT_PATIENCE

    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample_segments = [

        {
            "segment_id": 1,
            "speaker": "SPEAKER_01",
            "text":
                "The initial design is almost complete."
        },

        {
            "segment_id": 2,
            "speaker": "SPEAKER_02",
            "text":
                "Please complete the design by Friday."
        },

        {
            "segment_id": 3,
            "speaker": "SPEAKER_01",
            "text":
                "I will finish the design tomorrow."
        },

        {
            "segment_id": 4,
            "speaker": "SPEAKER_03",
            "text":
                "Then we can review the design."
        },

        {
            "segment_id": 5,
            "speaker": "SPEAKER_02",
            "text":
                "The database connection is having problems."
        },

        {
            "segment_id": 6,
            "speaker": "SPEAKER_01",
            "text":
                "The PostgreSQL connection needs to be fixed."
        },

        {
            "segment_id": 7,
            "speaker": "SPEAKER_03",
            "text":
                "Okay."
        },

        {
            "segment_id": 8,
            "speaker": "SPEAKER_02",
            "text":
                "We should test the connection."
        }

    ]


    topics = segment_transcript(
        sample_segments
    )


    print("\n")
    print("=" * 70)
    print("TOPIC SEGMENTATION RESULT")
    print("=" * 70)


    print(
        f"\nTotal topics: {len(topics)}"
    )


    for i, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"\nTopic {i}"
        )


        print(
            f"Segments: {len(topic)}"
        )


        for segment in topic:

            print(

                f"  - "

                f"{segment.get('segment_id', '?')} | "

                f"{segment.get('speaker', 'UNKNOWN')}: "

                f"{get_segment_text(segment)}"

            )


    print("\n" + "=" * 70)
    print("TOPIC SEGMENTATION COMPLETED")
    print("=" * 70)