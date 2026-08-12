from text_cleaner import clean_text


test_cases = [
    "   Hello    everyone.   ",
    "Well , this is a meeting.",
    "What???",
    "Hello    world!!!",
    "  “Good morning”  ",
    "This\tis\ta\ttest."
]


for text in test_cases:
    print("RAW:   ", repr(text))
    print("CLEAN: ", repr(clean_text(text)))
    print("-" * 40)