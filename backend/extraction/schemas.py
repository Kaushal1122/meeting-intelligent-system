from pydantic import BaseModel, Field
from typing import List, Optional

class ActionItem(BaseModel):
    task: str = Field(description="Clear, actionable task description extracted from dialogue.")
    responsible_person: Optional[str] = Field(
        default=None, 
        description="Speaker ID (e.g., SPEAKER_00) or name assigned. Resolved from conversation context/roles."
    )
    deadline: Optional[str] = Field(
        default=None, 
        description="Explicit date or relative timeframe (e.g., '30 minutes', 'by Friday', 'after lunch')."
    )
    topic_reference: Optional[int] = Field(
        default=None, 
        description="Topic ID where this action item was discussed."
    )
    priority: Optional[str] = Field(default="Medium", description="Extensible priority tag for Member 4.")
    confidence_score: Optional[float] = Field(default=None, description="Extensible confidence placeholder.")

class KeyDecision(BaseModel):
    decision: str = Field(description="Strategic agreement, product specification rule, or team conclusion.")
    topic_reference: Optional[int] = Field(
        default=None, 
        description="Topic ID where this decision was agreed upon."
    )

class ExtractionOnlyPayload(BaseModel):
    action_items: List[ActionItem] = Field(default_factory=list)
    key_decisions: List[KeyDecision] = Field(default_factory=list)
    needs_human_review: bool = Field(
        default=False, 
        description="Set to true ONLY IF you cannot find the integer topic reference."
    )

class ExtractionOnlyPayload(BaseModel):
    action_items: List[ActionItem] = Field(default_factory=list)
    key_decisions: List[KeyDecision] = Field(default_factory=list)
