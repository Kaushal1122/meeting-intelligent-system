from input_handler import validate_input


test_files = [
    r"..\data\ami\amicorpus\ES2002a\audio\ES2002a.Mix-Headset.wav",
    r"..\data\raw\test_transcript.txt"
]


for file_path in test_files:

    try:

        file_type = validate_input(file_path)

        print(
            f"{file_path} -> {file_type}"
        )

    except Exception as e:

        print(
            f"{file_path} -> ERROR: {e}"
        )