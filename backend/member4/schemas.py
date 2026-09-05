"""
Member 4 Data Contract Schemas.

Defines the formal boundaries for Member 4:
1. Member 4 Input Schemas: Ingests raw Member 3 extractions without modifying Member 3.
2. Member 2 Context Reference Schemas: Resolves topic_reference -> topic_id bridging.
3. Member 4 Output Schemas: Proposed enriched contract for downstream intelligence.

Design Rules:
- Zero imports from Member 1, Member 2, or Member 3 implementation modules.
- Complete UI independence (usable in headless services, CLIs, or web backends).
- Strict separation between Input Contract (immutable source data) and Output Contract (enriched intelligence).
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator



# ============================================================================
# 0. CANONICAL SPEAKER IDENTITY (Dynamic Speaker Resolution)
# ============================================================================

class SpeakerIdentity(BaseModel):
    """
    Canonical speaker identity representing both the immutable diarization
    ID and the verified display name.
    """
    model_config = ConfigDict(extra="ignore")

    speaker_id: str = Field(
        ...,
        description="Canonical diarization speaker label (e.g. 'SPEAKER_01', 'SPEAKER_02')."
    )
    display_name: str = Field(
        ...,
        description="Verified real name if explicitly detected, else identical to speaker_id."
    )
    name_source: str = Field(
        ...,
        description="Origin of the name: 'explicit_transcript' or 'diarization_fallback'."
    )
    evidence_segment_id: Optional[int] = Field(
        default=None,
        description="Segment ID where the self-introduction occurred."
    )
    evidence_text: Optional[str] = Field(
        default=None,
        description="Verbatim self-introduction quote from transcript."
    )


# ============================================================================
# 1. MEMBER 4 INPUT CONTRACT (From Member 3)
# ============================================================================

class Member4ActionItemInput(BaseModel):
    """
    Action item data structure as emitted by Member 3.
    Captures raw extracted fields. Source priority/confidence are stored
    as upstream reference fields only and will not be used as calculated truth.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    task: str = Field(
        ...,
        description="Actionable task statement extracted by Member 3."
    )
    responsible_person: Optional[str] = Field(
        default=None,
        description="Assigned person or speaker ID (e.g. 'SPEAKER_00', 'SPEAKER_01')."
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Stated deadline or timeframe string (e.g. '30 minutes', 'by Friday')."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Foreign key linking to Member 2 topic_id."
    )
    # Upstream source fields from Member 3 (informational only)
    source_priority: Optional[str] = Field(
        default=None,
        alias="priority",
        description="Raw priority string emitted by Member 3 LLM (e.g. 'High', 'Medium')."
    )
    source_confidence_score: Optional[float] = Field(
        default=None,
        alias="confidence_score",
        description="Raw single-float confidence emitted by Member 3 LLM."
    )

    @field_validator("task")
    @classmethod
    def validate_task_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Task description cannot be empty or whitespace only.")
        return v.strip()


class Member4DecisionInput(BaseModel):
    """
    Key decision data structure as emitted by Member 3.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    decision: str = Field(
        ...,
        description="Agreed decision, project direction, or specification rule."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Foreign key linking to Member 2 topic_id."
    )

    @field_validator("decision")
    @classmethod
    def validate_decision_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Decision description cannot be empty or whitespace only.")
        return v.strip()


class Member4Input(BaseModel):
    """
    Top-level meeting intelligence payload ingested by Member 4.
    Matches the schema emitted by Member 3 (e.g. ES2002a_member3_results.json).
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    meeting_id: str = Field(
        ...,
        description="Unique identifier of the meeting (e.g. 'ES2002a')."
    )
    processing_stage: Optional[str] = Field(
        default="member_3_complete",
        description="Stage indicator from Member 3."
    )
    total_action_items: Optional[int] = Field(
        default=None,
        description="Total action item count reported by Member 3."
    )
    total_decisions: Optional[int] = Field(
        default=None,
        description="Total key decision count reported by Member 3."
    )
    action_items: List[Member4ActionItemInput] = Field(
        default_factory=list,
        description="List of raw action items extracted by Member 3."
    )
    key_decisions: List[Member4DecisionInput] = Field(
        default_factory=list,
        description="List of raw key decisions extracted by Member 3."
    )

    @field_validator("meeting_id")
    @classmethod
    def validate_meeting_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("meeting_id cannot be empty.")
        return v.strip()


# ============================================================================
# 2. MEMBER 2 CONTEXT BRIDGE SCHEMAS (Topic Reference Resolution)
# ============================================================================

class Member2TranscriptSegment(BaseModel):
    """
    Individual transcript utterance within a Member 2 topic.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    segment_id: int = Field(
        ...,
        description="Raw transcript segment identifier."
    )
    speaker: str = Field(
        default="UNKNOWN",
        description="Speaker label for this segment (e.g. 'SPEAKER_03')."
    )
    text: str = Field(
        default="",
        description="Segment transcript text."
    )
    start: Optional[float] = Field(
        default=None,
        description="Segment start timestamp in seconds."
    )
    end: Optional[float] = Field(
        default=None,
        description="Segment end timestamp in seconds."
    )


class Member2TopicContextInput(BaseModel):
    """
    Schema for topic context imported from Member 2 results JSON.
    Allows Member 4 to resolve Member 3 `topic_reference` -> Member 2 `topic_id`.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    topic_id: int = Field(
        ...,
        description="Identifier matching Member 3 topic_reference."
    )
    segment_count: Optional[int] = Field(
        default=None,
        description="Number of transcript segments in this topic."
    )
    speakers: List[str] = Field(
        default_factory=list,
        description="Active speakers in this topic."
    )
    start: Optional[float] = Field(
        default=None,
        description="Start timestamp in seconds."
    )
    end: Optional[float] = Field(
        default=None,
        description="End timestamp in seconds."
    )
    text: Optional[str] = Field(
        default=None,
        description="Full dialogue text of this topic."
    )
    summary: Optional[str] = Field(
        default=None,
        description="BART abstractive summary generated by Member 2."
    )
    source_segment_ids: List[int] = Field(
        default_factory=list,
        description="Raw segment IDs forming this topic."
    )
    segments: List[Member2TranscriptSegment] = Field(
        default_factory=list,
        description="Detailed transcript segments within this topic."
    )


# ============================================================================
# 3. MEMBER 4 NORMALIZED INTERNAL CONTRACT (Phase 2)
# ============================================================================

class TopicContextStatus(str, Enum):
    """Resolution status of an action item/decision's topic_reference."""
    RESOLVED = "RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    MISSING_REFERENCE = "MISSING_REFERENCE"


class SpeakerIdentity(BaseModel):
    """
    Canonical speaker identity representing both the immutable diarization
    ID and the verified display name.
    """
    model_config = ConfigDict(extra="ignore")

    speaker_id: str = Field(
        ...,
        description="Canonical diarization speaker label (e.g. 'SPEAKER_01', 'SPEAKER_02')."
    )
    display_name: str = Field(
        ...,
        description="Verified real name if explicitly self-identified, else identical to speaker_id."
    )
    name_source: str = Field(
        default="diarization_fallback",
        description="Source of display_name: 'explicit_transcript' or 'diarization_fallback'."
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence in name resolution (1.0 for explicit, 0.0 for fallback)."
    )
    evidence_text: Optional[str] = Field(
        default=None,
        description="Verbatim utterance where the speaker explicitly self-identified."
    )
    evidence_segment_id: Optional[int] = Field(
        default=None,
        description="Transcript segment ID containing the self-identification."
    )



class NormalizedActionItem(BaseModel):
    """
    Clean, normalized internal representation of an action item.
    Serves as the foundation for downstream Phase 3-7 intelligence layers.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(
        ...,
        description="Deterministic unique identifier (e.g. 'norm_act_001')."
    )
    raw_task: str = Field(
        ...,
        description="Original raw task description from Member 3."
    )
    task: str = Field(
        ...,
        description="Cleaned, whitespace-normalized actionable task description."
    )
    responsible_person: Optional[str] = Field(
        default=None,
        description="Normalized speaker ID or name, or None if unassigned/unknown."
    )
    speaker_id: Optional[str] = Field(
        default=None,
        description="Canonical diarization speaker label (e.g. 'SPEAKER_01')."
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Verified real name if explicitly detected, else identical to speaker_id."
    )
    name_source: Optional[str] = Field(
        default=None,
        description="'explicit_transcript' or 'diarization_fallback'."
    )
    is_unassigned: bool = Field(
        default=False,
        description="True if no valid person/speaker was assigned to this task."
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Normalized explicit timeframe string, or None if missing."
    )
    is_ambiguous_deadline: bool = Field(
        default=False,
        description="True if deadline uses vague temporal language (e.g. 'soon', 'later')."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Topic ID integer linking to Member 2 topics."
    )
    context_status: TopicContextStatus = Field(
        default=TopicContextStatus.MISSING_REFERENCE,
        description="Status of Member 2 topic context resolution."
    )
    topic_context: Optional[Member2TopicContextInput] = Field(
        default=None,
        description="Resolved topic metadata from Member 2 (if available)."
    )
    # Source metadata preserved strictly as reference
    source_priority: Optional[str] = Field(
        default=None,
        description="Raw priority from Member 3 (source metadata only)."
    )
    source_confidence_score: Optional[float] = Field(
        default=None,
        description="Raw confidence score from Member 3 (source metadata only)."
    )
    # Deduplication tracking
    is_duplicate: bool = Field(
        default=False,
        description="True if an identical action item was already registered."
    )
    duplicate_of: Optional[str] = Field(
        default=None,
        description="item_id of the canonical action item this item duplicates."
    )
    validation_diagnostics: List[str] = Field(
        default_factory=list,
        description="Diagnostics or warnings recorded during normalization."
    )


class NormalizedDecision(BaseModel):
    """
    Clean, normalized internal representation of a key decision.
    """
    model_config = ConfigDict(extra="ignore")

    decision_id: str = Field(
        ...,
        description="Deterministic unique identifier (e.g. 'norm_dec_001')."
    )
    raw_decision: str = Field(
        ...,
        description="Original raw decision description from Member 3."
    )
    decision: str = Field(
        ...,
        description="Cleaned, whitespace-normalized decision statement."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Topic ID integer linking to Member 2 topics."
    )
    context_status: TopicContextStatus = Field(
        default=TopicContextStatus.MISSING_REFERENCE,
        description="Status of Member 2 topic context resolution."
    )
    topic_context: Optional[Member2TopicContextInput] = Field(
        default=None,
        description="Resolved topic metadata from Member 2 (if available)."
    )
    validation_diagnostics: List[str] = Field(
        default_factory=list,
        description="Diagnostics or warnings recorded during normalization."
    )


class Member4NormalizedOutput(BaseModel):
    """
    Complete normalized internal representation produced by Phase 2.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(
        ...,
        description="Meeting identifier matching input."
    )
    processing_stage: str = Field(
        default="member_4_normalized",
        description="Stage indicator for Member 4 normalization."
    )
    total_action_items: int = Field(
        default=0,
        description="Count of valid normalized action items."
    )
    total_decisions: int = Field(
        default=0,
        description="Count of valid normalized key decisions."
    )
    duplicates_detected: int = Field(
        default=0,
        description="Count of detected duplicate action items."
    )
    unresolved_topics_count: int = Field(
        default=0,
        description="Count of items with unresolved or missing topic references."
    )
    member2_context_enriched: bool = Field(
        default=False,
        description="True if Member 2 topic context was supplied and used for resolution."
    )
    action_items: List[NormalizedActionItem] = Field(
        default_factory=list,
        description="Clean normalized action items."
    )
    speakers: Dict[str, SpeakerIdentity] = Field(
        default_factory=dict,
        description="Resolved speaker directory mapping speaker_id to SpeakerIdentity."
    )
    key_decisions: List[NormalizedDecision] = Field(
        default_factory=list,
        description="Clean normalized key decisions."
    )
    rejected_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Items rejected during validation (e.g. empty task text)."
    )
    diagnostics: List[str] = Field(
        default_factory=list,
        description="Meeting-level validation and normalization logs."
    )


# ============================================================================
# 4. MEMBER 4 CONTEXTUAL TASK INTELLIGENCE CONTRACT (Phase 3)
# ============================================================================

class LocalizedDialogueContext(BaseModel):
    """
    Localized dialogue window extracted from Member 2 transcript segments.
    Captures the triggering utterance and up to +/-2 neighboring turns.
    """
    model_config = ConfigDict(extra="ignore")

    window_text: str = Field(
        ...,
        description="Formatted verbatim dialogue turns within the localized window."
    )
    segment_ids: List[int] = Field(
        default_factory=list,
        description="IDs of the transcript segments included in this window."
    )
    trigger_segment_id: Optional[int] = Field(
        default=None,
        description="ID of the segment that triggered or matched this task/decision."
    )
    speakers: List[str] = Field(
        default_factory=list,
        description="Active speakers present within this localized window."
    )
    start: Optional[float] = Field(
        default=None,
        description="Start timestamp in seconds of the earliest segment in the window."
    )
    end: Optional[float] = Field(
        default=None,
        description="End timestamp in seconds of the latest segment in the window."
    )


class RelatedDecisionContext(BaseModel):
    """
    Deterministic cross-reference to a Key Decision established in the same topic.
    """
    model_config = ConfigDict(extra="ignore")

    decision_id: str = Field(
        ...,
        description="Identifier of the related decision (e.g. 'norm_dec_001')."
    )
    decision: str = Field(
        ...,
        description="Statement of the agreed decision."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Shared topic reference linking the task and decision."
    )


class ContextRichActionItem(BaseModel):
    """
    Phase 3 Context-Rich Action Item representation.
    Enriches the normalized action item with localized dialogue turns,
    topic summaries, speaker rosters, temporal anchors, and related decisions.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(
        ...,
        description="Deterministic unique identifier from normalization (e.g. 'norm_act_001')."
    )
    task: str = Field(
        ...,
        description="Original normalized actionable task description."
    )
    responsible_person: Optional[str] = Field(
        default=None,
        description="Normalized speaker ID or name, or None if unassigned."
    )
    speaker_id: Optional[str] = Field(
        default=None,
        description="Canonical diarization speaker label (e.g. 'SPEAKER_01')."
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Verified real name if explicitly detected, else identical to speaker_id."
    )
    name_source: Optional[str] = Field(
        default=None,
        description="'explicit_transcript' or 'diarization_fallback'."
    )
    is_unassigned: bool = Field(
        default=False,
        description="True if no person was assigned to this task."
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Normalized deadline string, or None if missing."
    )
    is_ambiguous_deadline: bool = Field(
        default=False,
        description="True if deadline uses vague temporal language (e.g. 'soon', 'later')."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Referenced Member 2 topic identifier."
    )
    context_status: TopicContextStatus = Field(
        default=TopicContextStatus.MISSING_REFERENCE,
        description="Status: RESOLVED, PARTIALLY_RESOLVED, UNRESOLVED, or MISSING_REFERENCE."
    )
    topic_summary: Optional[str] = Field(
        default=None,
        description="Member 2 BART abstractive summary for this topic."
    )
    topic_speakers: List[str] = Field(
        default_factory=list,
        description="List of all active speakers in the referenced topic."
    )
    localized_context: Optional[LocalizedDialogueContext] = Field(
        default=None,
        description="Localized +/-2 segment dialogue window around the task utterance."
    )
    context_start: Optional[float] = Field(
        default=None,
        description="Earliest timestamp associated with this task's context."
    )
    context_end: Optional[float] = Field(
        default=None,
        description="Latest timestamp associated with this task's context."
    )
    related_decisions: List[RelatedDecisionContext] = Field(
        default_factory=list,
        description="Key decisions sharing the same topic reference."
    )
    deadline_context_snippet: Optional[str] = Field(
        default=None,
        description="Verbatim excerpt from dialogue showing the deadline mention."
    )
    # Source metadata preserved strictly as reference
    source_priority: Optional[str] = Field(
        default=None,
        description="Raw priority from Member 3 (source metadata only)."
    )
    source_confidence_score: Optional[float] = Field(
        default=None,
        description="Raw confidence score from Member 3 (source metadata only)."
    )
    is_duplicate: bool = Field(
        default=False,
        description="True if flagged as a duplicate in normalization."
    )
    duplicate_of: Optional[str] = Field(
        default=None,
        description="item_id of the canonical action item."
    )
    context_diagnostics: List[str] = Field(
        default_factory=list,
        description="Diagnostics or warnings recorded during context construction."
    )


class ContextRichDecision(BaseModel):
    """
    Phase 3 Context-Rich Key Decision representation.
    """
    model_config = ConfigDict(extra="ignore")

    decision_id: str = Field(
        ...,
        description="Deterministic unique identifier from normalization (e.g. 'norm_dec_001')."
    )
    decision: str = Field(
        ...,
        description="Clean normalized decision statement."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Referenced Member 2 topic identifier."
    )
    context_status: TopicContextStatus = Field(
        default=TopicContextStatus.MISSING_REFERENCE,
        description="Status: RESOLVED, PARTIALLY_RESOLVED, UNRESOLVED, or MISSING_REFERENCE."
    )
    topic_summary: Optional[str] = Field(
        default=None,
        description="Member 2 BART abstractive summary for this topic."
    )
    topic_speakers: List[str] = Field(
        default_factory=list,
        description="List of all active speakers in the referenced topic."
    )
    localized_context: Optional[LocalizedDialogueContext] = Field(
        default=None,
        description="Localized +/-2 segment dialogue window around the decision utterance."
    )
    context_start: Optional[float] = Field(
        default=None,
        description="Earliest timestamp associated with this decision's context."
    )
    context_end: Optional[float] = Field(
        default=None,
        description="Latest timestamp associated with this decision's context."
    )
    context_diagnostics: List[str] = Field(
        default_factory=list,
        description="Diagnostics or warnings recorded during context construction."
    )


class Member4ContextOutput(BaseModel):
    """
    Complete context-enriched payload emitted by Phase 3 Context Engine.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(
        ...,
        description="Meeting identifier matching input."
    )
    processing_stage: str = Field(
        default="member_4_context_enriched",
        description="Stage indicator for Member 4 context enrichment."
    )
    total_action_items: int = Field(
        default=0,
        description="Count of context-rich action items."
    )
    total_decisions: int = Field(
        default=0,
        description="Count of context-rich key decisions."
    )
    resolved_topics_count: int = Field(
        default=0,
        description="Count of items whose topic and localized context were fully resolved."
    )
    partially_resolved_count: int = Field(
        default=0,
        description="Count of items with topic metadata but missing segment details."
    )
    unresolved_topics_count: int = Field(
        default=0,
        description="Count of items whose topic reference was not found."
    )
    missing_topics_count: int = Field(
        default=0,
        description="Count of items with null or absent topic references."
    )
    items_with_localized_context: int = Field(
        default=0,
        description="Count of action items with localized dialogue windows attached."
    )
    items_with_related_decisions: int = Field(
        default=0,
        description="Count of action items linked to related decisions via shared topics."
    )
    action_items: List[ContextRichActionItem] = Field(
        default_factory=list,
        description="List of context-enriched action items."
    )
    speakers: Dict[str, SpeakerIdentity] = Field(
        default_factory=dict,
        description="Resolved speaker directory mapping speaker_id to SpeakerIdentity."
    )
    key_decisions: List[ContextRichDecision] = Field(
        default_factory=list,
        description="List of context-enriched key decisions."
    )
    diagnostics: List[str] = Field(
        default_factory=list,
        description="Meeting-level context construction logs."
    )


# ============================================================================
# 5. MEMBER 4 PRIORITY INTELLIGENCE CONTRACT (Phase 4)
# ============================================================================

class PriorityLevel(str, Enum):
    """Calibrated operational priority tiers computed by Member 4."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriorityFactorContribution(BaseModel):
    """
    Structured, machine-readable evidence for a single priority factor.
    """
    model_config = ConfigDict(extra="ignore")

    factor_name: str = Field(
        ...,
        description="Name of the priority factor (e.g. 'deadline_urgency')."
    )
    raw_value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized factor score between 0.0 and 1.0."
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Configured weight of this factor in the model."
    )
    weighted_contribution: float = Field(
        ...,
        description="Contribution to final score: raw_value * weight."
    )
    has_evidence: bool = Field(
        default=False,
        description="True if concrete evidence was found in context to support this factor."
    )
    evidence_text: Optional[str] = Field(
        default=None,
        description="Verbatim excerpt or rationale documenting the evidence."
    )
    evidence_segment_ids: List[int] = Field(
        default_factory=list,
        description="Transcript segment IDs supporting this factor evidence."
    )


class PriorityAssessment(BaseModel):
    """
    Complete priority assessment result for an action item.
    """
    model_config = ConfigDict(extra="ignore")

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated continuous priority score (0.0 to 1.0)."
    )
    level: PriorityLevel = Field(
        ...,
        description="Categorical priority tier: HIGH, MEDIUM, or LOW."
    )
    factor_contributions: List[PriorityFactorContribution] = Field(
        default_factory=list,
        description="Detailed evidence and score contributions per factor."
    )
    scoring_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary mapping factor_name to weighted_contribution."
    )
    evidence_summary: List[str] = Field(
        default_factory=list,
        description="Structured list of human/machine-readable evidence statements."
    )


class PriorityEnrichedActionItem(BaseModel):
    """
    Action item enriched with Phase 4 priority inference.
    Preserves all provenance and context from Phases 1, 2, and 3.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(..., description="Unique deterministic identifier.")
    task: str = Field(..., description="Normalized task description.")
    responsible_person: Optional[str] = Field(default=None)
    speaker_id: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    name_source: Optional[str] = Field(default=None)
    is_unassigned: bool = Field(default=False)
    deadline: Optional[str] = Field(default=None)
    is_ambiguous_deadline: bool = Field(default=False)
    topic_reference: Optional[int] = Field(default=None)
    context_status: TopicContextStatus = Field(default=TopicContextStatus.MISSING_REFERENCE)
    topic_summary: Optional[str] = Field(default=None)
    topic_speakers: List[str] = Field(default_factory=list)
    localized_context: Optional[LocalizedDialogueContext] = Field(default=None)
    context_start: Optional[float] = Field(default=None)
    context_end: Optional[float] = Field(default=None)
    related_decisions: List[RelatedDecisionContext] = Field(default_factory=list)
    deadline_context_snippet: Optional[str] = Field(default=None)
    source_priority: Optional[str] = Field(default=None, description="Member 3 raw priority (source metadata only).")
    source_confidence_score: Optional[float] = Field(default=None, description="Member 3 raw confidence (source metadata only).")
    is_duplicate: bool = Field(default=False)
    duplicate_of: Optional[str] = Field(default=None)
    context_diagnostics: List[str] = Field(default_factory=list)
    priority_assessment: PriorityAssessment = Field(..., description="Inferred priority assessment and evidence.")


class Member4PriorityOutput(BaseModel):
    """
    Complete priority-enriched payload emitted by Phase 4 Priority Engine.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(..., description="Meeting identifier.")
    processing_stage: str = Field(default="member_4_priority_enriched")
    total_action_items: int = Field(default=0)
    high_priority_count: int = Field(default=0)
    medium_priority_count: int = Field(default=0)
    low_priority_count: int = Field(default=0)
    min_score: float = Field(default=0.0)
    max_score: float = Field(default=0.0)
    avg_score: float = Field(default=0.0)
    action_items: List[PriorityEnrichedActionItem] = Field(default_factory=list)
    speakers: Dict[str, SpeakerIdentity] = Field(default_factory=dict)
    key_decisions: List[ContextRichDecision] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)


# ============================================================================
# 6. MEMBER 4 CONFIDENCE INTELLIGENCE CONTRACT (Phase 5)
# ============================================================================

class ConfidenceLevel(str, Enum):
    """Categorical confidence tiers based on evidence reliability."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConfidenceFactorContribution(BaseModel):
    """
    Structured, machine-readable evidence for a single confidence factor.
    """
    model_config = ConfigDict(extra="ignore")

    factor_name: str = Field(
        ...,
        description="Name of the confidence factor (e.g. 'context_resolution')."
    )
    raw_value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized factor score between 0.0 and 1.0."
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Configured weight of this factor in the model."
    )
    weighted_contribution: float = Field(
        ...,
        description="Contribution to final score: raw_value * weight."
    )
    has_evidence: bool = Field(
        default=False,
        description="True if concrete evidence supported this factor."
    )
    evidence_text: Optional[str] = Field(
        default=None,
        description="Documentation of evidence quality or absence."
    )
    evidence_segment_ids: List[int] = Field(
        default_factory=list,
        description="Supporting transcript segment IDs."
    )


class ConfidenceAssessment(BaseModel):
    """
    Complete evidence reliability assessment result for an action item.
    """
    model_config = ConfigDict(extra="ignore")

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated continuous confidence score (0.0 to 1.0)."
    )
    level: ConfidenceLevel = Field(
        ...,
        description="Categorical tier: HIGH, MEDIUM, or LOW."
    )
    factor_contributions: List[ConfidenceFactorContribution] = Field(
        default_factory=list,
        description="Detailed evidence and score contributions per factor."
    )
    scoring_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary mapping factor_name to weighted_contribution."
    )
    evidence_quality_notes: List[str] = Field(
        default_factory=list,
        description="Structured list of notes detailing evidence grounding and quality."
    )


class ConfidenceEnrichedActionItem(BaseModel):
    """
    Action item enriched with Phase 5 confidence assessment.
    Preserves all provenance, context, and priority from Phases 1–4.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(..., description="Unique deterministic identifier.")
    task: str = Field(..., description="Normalized task description.")
    responsible_person: Optional[str] = Field(default=None)
    speaker_id: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    name_source: Optional[str] = Field(default=None)
    is_unassigned: bool = Field(default=False)
    deadline: Optional[str] = Field(default=None)
    is_ambiguous_deadline: bool = Field(default=False)
    topic_reference: Optional[int] = Field(default=None)
    context_status: TopicContextStatus = Field(default=TopicContextStatus.MISSING_REFERENCE)
    topic_summary: Optional[str] = Field(default=None)
    topic_speakers: List[str] = Field(default_factory=list)
    localized_context: Optional[LocalizedDialogueContext] = Field(default=None)
    context_start: Optional[float] = Field(default=None)
    context_end: Optional[float] = Field(default=None)
    related_decisions: List[RelatedDecisionContext] = Field(default_factory=list)
    deadline_context_snippet: Optional[str] = Field(default=None)
    source_priority: Optional[str] = Field(default=None, description="Member 3 raw priority (source metadata only).")
    source_confidence_score: Optional[float] = Field(default=None, description="Member 3 raw confidence (source metadata only).")
    is_duplicate: bool = Field(default=False)
    duplicate_of: Optional[str] = Field(default=None)
    context_diagnostics: List[str] = Field(default_factory=list)
    priority_assessment: PriorityAssessment = Field(..., description="Inferred priority assessment from Phase 4.")
    confidence_assessment: ConfidenceAssessment = Field(..., description="Inferred evidence confidence assessment from Phase 5.")


class Member4ConfidenceOutput(BaseModel):
    """
    Complete confidence-enriched payload emitted by Phase 5 Confidence Engine.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(..., description="Meeting identifier.")
    processing_stage: str = Field(default="member_4_confidence_enriched")
    total_action_items: int = Field(default=0)
    high_confidence_count: int = Field(default=0)
    medium_confidence_count: int = Field(default=0)
    low_confidence_count: int = Field(default=0)
    min_score: float = Field(default=0.0)
    max_score: float = Field(default=0.0)
    avg_score: float = Field(default=0.0)
    action_items: List[ConfidenceEnrichedActionItem] = Field(default_factory=list)
    speakers: Dict[str, SpeakerIdentity] = Field(default_factory=dict)
    key_decisions: List[ContextRichDecision] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)



# ============================================================================
# 7. MEMBER 4 HUMAN REVIEW / UNCERTAINTY CONTRACT (Phase 6)
# ============================================================================

class ReviewStatus(str, Enum):
    """Deterministic human review triage states."""
    AUTO_ACCEPT = "AUTO_ACCEPT"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ReviewReasonCode(str, Enum):
    """Structured, machine-readable uncertainty and triage reason codes."""
    # Critical uncertainty / high-risk combinations (Trigger REVIEW_REQUIRED)
    HIGH_PRIORITY_LOW_CONFIDENCE = "HIGH_PRIORITY_LOW_CONFIDENCE"
    HIGH_PRIORITY_AMBIGUOUS_DEADLINE = "HIGH_PRIORITY_AMBIGUOUS_DEADLINE"
    UNASSIGNED_HIGH_PRIORITY_TASK = "UNASSIGNED_HIGH_PRIORITY_TASK"
    UNRESOLVED_CONTEXT = "UNRESOLVED_CONTEXT"
    MISSING_TOPIC_REFERENCE = "MISSING_TOPIC_REFERENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"

    # Moderate uncertainty signals (Trigger REVIEW_RECOMMENDED)
    HIGH_PRIORITY_MEDIUM_CONFIDENCE = "HIGH_PRIORITY_MEDIUM_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    PARTIAL_CONTEXT = "PARTIAL_CONTEXT"
    UNASSIGNED_TASK = "UNASSIGNED_TASK"
    AMBIGUOUS_DEADLINE = "AMBIGUOUS_DEADLINE"
    WEAK_DIALOGUE_GROUNDING = "WEAK_DIALOGUE_GROUNDING"
    CONFLICTING_DECISIONS = "CONFLICTING_DECISIONS"


class ReviewDecision(BaseModel):
    """
    Complete human review triage decision for an action item.
    """
    model_config = ConfigDict(extra="ignore")

    status: ReviewStatus = Field(
        ...,
        description="Triage state: AUTO_ACCEPT, REVIEW_RECOMMENDED, or REVIEW_REQUIRED."
    )
    review_required: bool = Field(
        default=False,
        description="True if human intervention is mandatory prior to execution."
    )
    review_recommended: bool = Field(
        default=False,
        description="True if human verification is suggested due to moderate uncertainty."
    )
    reason_codes: List[ReviewReasonCode] = Field(
        default_factory=list,
        description="Machine-readable codes identifying exact uncertainty sources."
    )
    explanation: str = Field(
        ...,
        description="Human-readable synthesis explaining why this triage decision was made."
    )
    evidence_flags: Dict[str, Any] = Field(
        default_factory=dict,
        description="Deterministic boolean flags for uncertainty triggers."
    )


class TriageEnrichedActionItem(BaseModel):
    """
    Action item enriched with Phase 6 Human Review triage decision.
    Preserves all provenance, context, priority, and confidence from Phases 1–5.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(..., description="Unique deterministic identifier.")
    task: str = Field(..., description="Normalized task description.")
    responsible_person: Optional[str] = Field(default=None)
    speaker_id: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    name_source: Optional[str] = Field(default=None)
    is_unassigned: bool = Field(default=False)
    deadline: Optional[str] = Field(default=None)
    is_ambiguous_deadline: bool = Field(default=False)
    topic_reference: Optional[int] = Field(default=None)
    context_status: TopicContextStatus = Field(default=TopicContextStatus.MISSING_REFERENCE)
    topic_summary: Optional[str] = Field(default=None)
    topic_speakers: List[str] = Field(default_factory=list)
    localized_context: Optional[LocalizedDialogueContext] = Field(default=None)
    context_start: Optional[float] = Field(default=None)
    context_end: Optional[float] = Field(default=None)
    related_decisions: List[RelatedDecisionContext] = Field(default_factory=list)
    deadline_context_snippet: Optional[str] = Field(default=None)
    source_priority: Optional[str] = Field(default=None, description="Member 3 raw priority (source metadata only).")
    source_confidence_score: Optional[float] = Field(default=None, description="Member 3 raw confidence (source metadata only).")
    is_duplicate: bool = Field(default=False)
    duplicate_of: Optional[str] = Field(default=None)
    context_diagnostics: List[str] = Field(default_factory=list)
    priority_assessment: PriorityAssessment = Field(..., description="Inferred priority assessment from Phase 4.")
    confidence_assessment: ConfidenceAssessment = Field(..., description="Inferred confidence assessment from Phase 5.")
    review_decision: ReviewDecision = Field(..., description="Triage decision from Phase 6.")


class Member4TriageOutput(BaseModel):
    """
    Complete triage-enriched payload emitted by Phase 6 Human Review Engine.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(..., description="Meeting identifier.")
    processing_stage: str = Field(default="member_4_triage_enriched")
    total_action_items: int = Field(default=0)
    auto_accept_count: int = Field(default=0)
    review_recommended_count: int = Field(default=0)
    review_required_count: int = Field(default=0)
    reason_code_counts: Dict[str, int] = Field(default_factory=dict)
    action_items: List[TriageEnrichedActionItem] = Field(default_factory=list)
    speakers: Dict[str, SpeakerIdentity] = Field(default_factory=dict)
    key_decisions: List[ContextRichDecision] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)



# ============================================================================
# 8. MEMBER 4 EXPLAINABILITY CONTRACT (Phase 7)
# ============================================================================

class ExplanationFactor(BaseModel):
    """
    Detailed explanation of an individual factor's score contribution.
    """
    model_config = ConfigDict(extra="ignore")

    factor_name: str = Field(..., description="Name of the evaluated factor.")
    raw_value: float = Field(..., ge=0.0, le=1.0, description="Normalized factor score in [0.0, 1.0].")
    weight: float = Field(..., ge=0.0, le=1.0, description="Factor weight in multi-factor model.")
    weighted_contribution: float = Field(..., description="Mathematical contribution: raw_value * weight.")
    interpretation: str = Field(..., description="Human-readable assessment of this factor's evidence.")
    evidence_text: Optional[str] = Field(default=None, description="Verbatim evidence note or quote.")
    evidence_segment_ids: List[int] = Field(default_factory=list, description="Associated transcript segment IDs.")


class EvidenceReference(BaseModel):
    """
    Auditable pointer connecting an explanation directly to a source artifact.
    """
    model_config = ConfigDict(extra="ignore")

    source_type: str = Field(..., description="Type of source: 'topic', 'transcript_segment', 'decision', 'deadline'.")
    source_id: Optional[Union[int, str]] = Field(default=None, description="Identifier of the referenced artifact.")
    speaker: Optional[str] = Field(default=None, description="Speaker attributed to this evidence.")
    start_time: Optional[float] = Field(default=None, description="Start timestamp in seconds.")
    end_time: Optional[float] = Field(default=None, description="End timestamp in seconds.")
    text_excerpt: Optional[str] = Field(default=None, description="Verbatim short textual excerpt.")


class PriorityExplainability(BaseModel):
    """
    Read-only interpretation trail for the Phase 4 Priority score.
    """
    model_config = ConfigDict(extra="ignore")

    score: float = Field(..., description="Final continuous priority score from Phase 4.")
    level: PriorityLevel = Field(..., description="Categorical priority level from Phase 4.")
    factors: List[ExplanationFactor] = Field(default_factory=list, description="All evaluated priority factors.")
    top_contributors: List[ExplanationFactor] = Field(default_factory=list, description="Ranked strongest positive contributors.")
    supporting_evidence: List[str] = Field(default_factory=list, description="Key factors reinforcing high/medium priority.")
    limiting_factors: List[str] = Field(default_factory=list, description="Factors that attenuated priority (e.g. absent urgency/deadline).")
    explanation_text: str = Field(..., description="Concise human-readable rationale for the priority assignment.")


class ConfidenceExplainability(BaseModel):
    """
    Read-only interpretation trail for the Phase 5 Confidence score.
    """
    model_config = ConfigDict(extra="ignore")

    score: float = Field(..., description="Final continuous confidence score from Phase 5.")
    level: ConfidenceLevel = Field(..., description="Categorical confidence level from Phase 5.")
    factors: List[ExplanationFactor] = Field(default_factory=list, description="All evaluated confidence factors.")
    top_contributors: List[ExplanationFactor] = Field(default_factory=list, description="Ranked strongest evidence contributors.")
    supporting_evidence: List[str] = Field(default_factory=list, description="Positive evidence items verifying reliability.")
    limiting_evidence: List[str] = Field(default_factory=list, description="Uncertainty factors or evidence gaps.")
    explanation_text: str = Field(..., description="Concise human-readable rationale for the confidence score.")


class ReviewExplainability(BaseModel):
    """
    Read-only interpretation trail for the Phase 6 Human Review decision.
    """
    model_config = ConfigDict(extra="ignore")

    status: ReviewStatus = Field(..., description="Triage status from Phase 6.")
    review_required: bool = Field(default=False)
    review_recommended: bool = Field(default=False)
    reason_codes: List[ReviewReasonCode] = Field(default_factory=list)
    evidence_flags: Dict[str, Any] = Field(default_factory=dict)
    explanation_text: str = Field(..., description="Human-readable rationale for the review triage state.")


class ActionItemExplanation(BaseModel):
    """
    Unified multi-dimensional explainability object for an action item.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(..., description="Action item unique identifier.")
    task: str = Field(..., description="Action item normalized task.")
    priority_explanation: PriorityExplainability = Field(...)
    confidence_explanation: ConfidenceExplainability = Field(...)
    review_explanation: ReviewExplainability = Field(...)
    evidence_traces: List[EvidenceReference] = Field(default_factory=list)
    unified_explanation: str = Field(..., description="Comprehensive natural-language explanation.")


class ExplainedActionItem(BaseModel):
    """
    Action item enriched with Phase 7 Explainability.
    Preserves all Phase 1–6 intelligence models unmodified.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(...)
    task: str = Field(...)
    responsible_person: Optional[str] = Field(default=None)
    speaker_id: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    name_source: Optional[str] = Field(default=None)
    is_unassigned: bool = Field(default=False)
    deadline: Optional[str] = Field(default=None)
    is_ambiguous_deadline: bool = Field(default=False)
    topic_reference: Optional[int] = Field(default=None)
    context_status: TopicContextStatus = Field(default=TopicContextStatus.MISSING_REFERENCE)
    topic_summary: Optional[str] = Field(default=None)
    topic_speakers: List[str] = Field(default_factory=list)
    localized_context: Optional[LocalizedDialogueContext] = Field(default=None)
    context_start: Optional[float] = Field(default=None)
    context_end: Optional[float] = Field(default=None)
    related_decisions: List[RelatedDecisionContext] = Field(default_factory=list)
    deadline_context_snippet: Optional[str] = Field(default=None)
    source_priority: Optional[str] = Field(default=None)
    source_confidence_score: Optional[float] = Field(default=None)
    is_duplicate: bool = Field(default=False)
    duplicate_of: Optional[str] = Field(default=None)
    context_diagnostics: List[str] = Field(default_factory=list)
    priority_assessment: PriorityAssessment = Field(...)
    confidence_assessment: ConfidenceAssessment = Field(...)
    review_decision: ReviewDecision = Field(...)
    explanation: ActionItemExplanation = Field(...)


class Member4ExplainedOutput(BaseModel):
    """
    Complete explainability payload emitted by Phase 7 Explainability Engine.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(..., description="Meeting identifier.")
    processing_stage: str = Field(default="member_4_explained")
    total_action_items: int = Field(default=0)
    auto_accept_count: int = Field(default=0)
    review_recommended_count: int = Field(default=0)
    review_required_count: int = Field(default=0)
    explained_action_items_count: int = Field(default=0)
    action_items: List[ExplainedActionItem] = Field(default_factory=list)
    speakers: Dict[str, SpeakerIdentity] = Field(default_factory=dict)
    key_decisions: List[ContextRichDecision] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)



# ============================================================================
# 9. MEMBER 4 PERSONALIZATION CONTRACT (Phase 8)
# ============================================================================

class UserRole(str, Enum):
    """Supported personalization role profiles."""
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"
    INTERN = "INTERN"
    DEFAULT = "DEFAULT"


class RoleEmphasis(BaseModel):
    """
    Presentation-layer metadata tailoring emphasis and guidance for a role.
    Does NOT alter canonical intelligence values.
    """
    model_config = ConfigDict(extra="ignore")

    role: UserRole = Field(..., description="Role profile targeted.")
    highlighted_fields: List[str] = Field(default_factory=list, description="Fields emphasized in UI/views.")
    display_urgency_badge: bool = Field(default=False)
    display_review_badge: bool = Field(default=False)
    role_guidance: str = Field(..., description="Actionable recommendation for this role.")
    dependency_summary: Optional[str] = Field(default=None)


class PersonalizedActionItem(BaseModel):
    """
    Role-projected action item view.
    Guarantees 100% preservation of underlying canonical intelligence decisions.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(...)
    task: str = Field(...)
    responsible_person: Optional[str] = Field(default=None)
    speaker_id: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    name_source: Optional[str] = Field(default=None)
    is_unassigned: bool = Field(default=False)
    deadline: Optional[str] = Field(default=None)
    is_ambiguous_deadline: bool = Field(default=False)
    topic_reference: Optional[int] = Field(default=None)
    context_status: TopicContextStatus = Field(...)

    # Canonical intelligence values (MUST match upstream bit-for-bit)
    priority_score: float = Field(..., description="Canonical priority score.")
    priority_level: PriorityLevel = Field(..., description="Canonical priority level.")
    confidence_score: float = Field(..., description="Canonical confidence score.")
    confidence_level: ConfidenceLevel = Field(..., description="Canonical confidence level.")
    review_status: ReviewStatus = Field(..., description="Canonical review status.")
    review_reason_codes: List[ReviewReasonCode] = Field(default_factory=list)

    # Full canonical explanations & evidence traces
    explanation: ActionItemExplanation = Field(...)

    # Role-specific projection metadata
    role_emphasis: RoleEmphasis = Field(...)


class PersonalizedViewFilter(BaseModel):
    """
    Deterministic query filter for personalized views.
    Does not modify underlying items; only filters visibility.
    """
    model_config = ConfigDict(extra="ignore")

    role: Optional[UserRole] = Field(default=None)
    priority_level: Optional[PriorityLevel] = Field(default=None)
    confidence_level: Optional[ConfidenceLevel] = Field(default=None)
    review_status: Optional[ReviewStatus] = Field(default=None)
    assigned_only: Optional[bool] = Field(default=None)
    unassigned_only: Optional[bool] = Field(default=None)
    has_deadline_only: Optional[bool] = Field(default=None)
    topic_reference: Optional[int] = Field(default=None)


class PersonalizedMeetingView(BaseModel):
    """
    Complete role-tailored meeting view emitted by Phase 8 Personalization Engine.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(...)
    role: UserRole = Field(...)
    summary_headline: str = Field(..., description="Role-specific executive summary headline.")
    total_canonical_items: int = Field(default=0)
    displayed_items_count: int = Field(default=0)
    high_priority_count: int = Field(default=0)
    medium_priority_count: int = Field(default=0)
    low_priority_count: int = Field(default=0)
    auto_accept_count: int = Field(default=0)
    review_recommended_count: int = Field(default=0)
    review_required_count: int = Field(default=0)
    speakers: Dict[str, SpeakerIdentity] = Field(default_factory=dict)
    unassigned_count: int = Field(default=0)
    has_deadline_count: int = Field(default=0)
    action_items: List[PersonalizedActionItem] = Field(default_factory=list)
    key_decisions: List[ContextRichDecision] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)


# ============================================================================
# 10. PROPOSED MEMBER 4 OUTPUT CONTRACT (Enriched Intelligence)
# ============================================================================







class ReviewPriority(str, Enum):
    """Urgency of human review intervention."""
    CRITICAL = "CRITICAL"
    STANDARD = "STANDARD"
    LOW = "LOW"


class PriorityExplanation(BaseModel):
    """Multi-factor priority score and explanation trail."""
    model_config = ConfigDict(extra="ignore")

    level: PriorityLevel = Field(
        default=PriorityLevel.MEDIUM,
        description="Computed categorical priority."
    )
    score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Continuous priority score (0.0 to 1.0)."
    )
    factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Sub-factor weights (deadline_urgency, semantic_criticality, etc.)."
    )
    reason: str = Field(
        default="Standard priority task.",
        description="Human-readable rationale explaining the priority score."
    )


class ConfidenceBreakdown(BaseModel):
    """Granular sub-attribute confidence estimation."""
    model_config = ConfigDict(extra="ignore")

    overall: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Calibrated composite confidence score."
    )
    task_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Grammatical imperativeness & action validity confidence."
    )
    person_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Assignee grounding confidence in dialogue."
    )
    deadline_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Temporal explicitness confidence."
    )
    priority_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in the inferred priority classification."
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Verbatim dialogue citations and grounding evidence."
    )


class TriageStatus(BaseModel):
    """Human-in-the-loop review triage flags and triggers."""
    model_config = ConfigDict(extra="ignore")

    needs_human_review: bool = Field(
        default=False,
        description="True if confidence is low, ambiguous, or critical review triggered."
    )
    review_priority: Optional[ReviewPriority] = Field(
        default=None,
        description="Severity/urgency of required human verification."
    )
    review_reasons: List[str] = Field(
        default_factory=list,
        description="Explicit diagnostic reasons for flagging (e.g. 'Uncertain assignee')."
    )


class TaskContext(BaseModel):
    """Hydrated contextual background linked from Member 2."""
    model_config = ConfigDict(extra="ignore")

    topic_title: Optional[str] = Field(
        default=None,
        description="Synthesized topic label or header."
    )
    topic_summary: Optional[str] = Field(
        default=None,
        description="Member 2 BART summary for this topic reference."
    )
    dialogue_snippet: Optional[str] = Field(
        default=None,
        description="Relevant transcript segment text surrounding the task statement."
    )
    speaker_roster: List[str] = Field(
        default_factory=list,
        description="Active speakers in the referenced topic."
    )


class Member4ActionItemOutput(BaseModel):
    """
    Enriched Action Item emitted by Member 4.
    Transforms raw Member 3 items into priority-aware, confidence-aware,
    explainable, and review-triaged operational intelligence.
    """
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(
        ...,
        description="Unique deterministic ID (e.g. 'act_001')."
    )
    task: str = Field(
        ...,
        description="Normalized actionable task description."
    )
    responsible_person: Optional[str] = Field(
        default=None,
        description="Normalized speaker ID or resolved participant name."
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Stated deadline string."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Referenced Member 2 topic ID."
    )
    priority: PriorityExplanation = Field(
        default_factory=PriorityExplanation,
        description="Member 4 multi-factor priority inference."
    )
    confidence: ConfidenceBreakdown = Field(
        default_factory=ConfidenceBreakdown,
        description="Member 4 decomposed confidence estimation."
    )
    triage: TriageStatus = Field(
        default_factory=TriageStatus,
        description="Member 4 human review triage."
    )
    context: Optional[TaskContext] = Field(
        default=None,
        description="Hydrated topic context and dialogue citation."
    )


class Member4DecisionOutput(BaseModel):
    """
    Enriched Key Decision emitted by Member 4.
    """
    model_config = ConfigDict(extra="ignore")

    decision_id: str = Field(
        ...,
        description="Unique deterministic ID (e.g. 'dec_001')."
    )
    decision: str = Field(
        ...,
        description="Agreed decision statement."
    )
    topic_reference: Optional[int] = Field(
        default=None,
        description="Referenced Member 2 topic ID."
    )
    topic_summary: Optional[str] = Field(
        default=None,
        description="Summary of the topic where this decision occurred."
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Grounding confidence for this decision."
    )
    needs_human_review: bool = Field(
        default=False,
        description="Flag for uncertain or contentious decisions."
    )


class Member4PersonalizedViews(BaseModel):
    """
    Role-personalized projections derived deterministically from the master state.
    """
    model_config = ConfigDict(extra="ignore")

    manager_view: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated team allocation, milestones, and pending reviews."
    )
    developer_view: Dict[str, Any] = Field(
        default_factory=dict,
        description="Assigned technical tasks, architectural decisions, and immediate blockers."
    )
    intern_view: Dict[str, Any] = Field(
        default_factory=dict,
        description="Onboarding tasks enriched with extensive background context."
    )


class Member4Output(BaseModel):
    """
    Complete master output artifact emitted by Member 4.
    Headless and UI-agnostic.
    """
    model_config = ConfigDict(extra="ignore")

    meeting_id: str = Field(
        ...,
        description="Meeting identifier matching input."
    )
    processing_stage: str = Field(
        default="member_4_complete",
        description="Stage indicator for Member 4 completion."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Processing stats, timestamps, and item counts."
    )
    action_items: List[Member4ActionItemOutput] = Field(
        default_factory=list,
        description="Enriched, prioritized, and calibrated action items."
    )
    key_decisions: List[Member4DecisionOutput] = Field(
        default_factory=list,
        description="Enriched key decisions with contextual grounding."
    )
    personalized_views: Optional[Member4PersonalizedViews] = Field(
        default=None,
        description="Role-tailored projections (Manager, Developer, Intern)."
    )
