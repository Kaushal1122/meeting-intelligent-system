from speaker_normalizer import normalize_speaker_label


test_speakers = [
    "SPEAKER_01",
    "speaker_1",
    "Speaker 2",
    "speaker-3",
    "PARTICIPANT_4",
    "participant 05",
    "Laura",
    " David ",
    "",
    "   "
]


for speaker in test_speakers:

    normalized = normalize_speaker_label(speaker)

    print(
        f"{speaker!r} -> {normalized!r}"
    )