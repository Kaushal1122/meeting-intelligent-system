import ollama
from typing import List
from .schemas import ExtractionOnlyPayload

SPEAKER_ROSTER = """
TEAM ROSTER:
- SPEAKER_03: Laura (Project Manager / Chair / Meeting Lead)
- SPEAKER_00: David (Industrial Designer)
- SPEAKER_01: Craig (User Interface / UI Designer)
- SPEAKER_02: Andrew (Marketing Executive)
"""

def extract_actions_and_decisions(
    member2_data: dict,
    model_name: str = "qwen2.5:3b",
    batch_size: int = 3
) -> dict:
    topics = member2_data.get("topics", [])
    meeting_id = member2_data.get("meeting_id", "Unknown_Meeting")
    
    all_action_items = []
    all_decisions = []
    total_topics = len(topics)
    
    print(f"[Member 3] Processing {total_topics} topics with high-precision semantic prompt...")

    for i in range(0, total_topics, batch_size):
        chunk = topics[i : i + batch_size]
        context_blocks = []
        
        for topic in chunk:
            t_id = topic.get("topic_id")
            speakers = ", ".join(topic.get("speakers", []))
            summary = topic.get("summary", "")
            dialogue = topic.get("text", "")[:200]
            
            context_blocks.append(
                f"[TOPIC_ID: {t_id}]\nActive Speakers: {speakers}\nSummary: {summary}\nTranscript Excerpt: {dialogue}"
            )
        
        formatted_context = "\n\n".join(context_blocks)
        
        # FEW-SHOT SEMANTIC PROMPT (PURE LLM)
        system_prompt = (
            "You are a strict, high-precision meeting intelligence engine.\n\n"
            f"{SPEAKER_ROSTER}\n\n"
            "MANDATORY EXTRACTION PROTOCOL:\n"
            "1. ONLY extract tasks when a person is EXPLICITLY assigned the work. Do NOT extract tasks early when the team is just discussing the agenda.\n"
            "2. 'topic_reference' MUST be the exact integer X from [TOPIC_ID: X]. You must include this for BOTH action items and decisions. Never use null.\n"
            "3. 'deadline' MUST be the exact timeframe mentioned (e.g., '30 minutes'). If truly none is stated, write 'None mentioned'.\n"
            "4. If a batch has no explicit assignments or final decisions, return empty arrays [].\n\n"
            "=== EXAMPLE INPUT ===\n"
            "[TOPIC_ID: 10]\n"
            "Active Speakers: SPEAKER_03\n"
            "Transcript Excerpt: Today we are going to draw animals.\n\n"
            "[TOPIC_ID: 39]\n"
            "Active Speakers: SPEAKER_03, SPEAKER_00\n"
            "Transcript Excerpt: SPEAKER_03: The next meeting is in 30 minutes. David, as the industrial designer, work on the physical design.\n\n"
            "=== EXAMPLE OUTPUT ===\n"
            "{\n"
            "  \"action_items\": [\n"
            "    {\n"
            "      \"task\": \"Work on the actual working design of the remote control\",\n"
            "      \"responsible_person\": \"SPEAKER_00\",\n"
            "      \"deadline\": \"30 minutes\",\n"
            "      \"topic_reference\": 39,\n"
            "      \"priority\": \"High\",\n"
            "      \"confidence_score\": 0.95\n"
            "    }\n"
            "  ],\n"
            "  \"key_decisions\": []\n"
            "}\n"
        )
        
        try:
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze these meeting topics and extract actions/decisions:\n\n{formatted_context}"}
                ],
                format=ExtractionOnlyPayload.model_json_schema(),
                options={
                    "temperature": 0.0,
                    "num_ctx": 8192,
                    "num_predict": 1024
                }
            )
            
            parsed = ExtractionOnlyPayload.model_validate_json(response["message"]["content"])
            
            for item in parsed.action_items:
                all_action_items.append(item.model_dump())
            for dec in parsed.key_decisions:
                all_decisions.append(dec.model_dump())
                
            print(f"[OK] Processed Topics {i+1} to {min(i + batch_size, total_topics)}")

        except Exception as e:
            print(f"[WARN] Extraction Error (Topics {i+1}-{min(i+batch_size, total_topics)}): {e}")
            
    return {
        "meeting_id": meeting_id,
        "processing_stage": "member_3_complete",
        "total_action_items": len(all_action_items),
        "total_decisions": len(all_decisions),
        "action_items": all_action_items,
        "key_decisions": all_decisions
    }
