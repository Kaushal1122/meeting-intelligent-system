import json
import os
import sys

sys.path.append(os.path.abspath("."))
from backend.extraction.task_extractor import extract_actions_and_decisions

def main():
    input_path = None
    search_dirs = ["data/processed", "data"]
    
    for directory in search_dirs:
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if "member2" in file and file.endswith(".json"):
                    input_path = os.path.join(directory, file)
                    break
        if input_path:
            break

    if not input_path:
        print("Error: No Member 2 JSON found in data/processed/ or data/")
        return

    os.makedirs("data/processed", exist_ok=True)
    base_name = os.path.basename(input_path).replace("member2_results", "member3_results").replace("member2_output", "member3_output")
    if "member3" not in base_name:
        base_name = "ES2002a.Mix-Headset_member3_results.json"
    output_path = os.path.join("data/processed", base_name)

    print(f"Step 1: Reading input from: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        member2_data = json.load(f)

    print("Step 2: Running Member 3 semantic extraction...")
    standalone_output = extract_actions_and_decisions(member2_data)

    print(f"Step 3: Saving output to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(standalone_output, f, indent=4)

    print("\nMember 3 Execution Finished Successfully!")
    print(f"- Output File: {output_path}")
    print(f"- Total Action Items: {standalone_output.get('total_action_items', 0)}")
    print(f"- Total Key Decisions: {standalone_output.get('total_decisions', 0)}")

if __name__ == "__main__":
    main()
