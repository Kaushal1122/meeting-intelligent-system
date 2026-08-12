from transcript_processor import process_transcript


INPUT_FILE = r"..\data\raw\test_transcript.txt"

OUTPUT_FILE = (
    r"..\data\processed\test_transcript.json"
)


result = process_transcript(
    INPUT_FILE,
    OUTPUT_FILE
)


print("Transcript processed successfully.")
print(f"Output saved to: {OUTPUT_FILE}")

print("\nSegments:")

for segment in result["segments"]:

    print(
        f"{segment['speaker']}: "
        f"{segment['clean_text']}"
    )