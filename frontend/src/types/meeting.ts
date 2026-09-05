export type UserRole = 'MANAGER' | 'DEVELOPER' | 'INTERN' | 'DEFAULT';

export type PriorityLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type ReviewStatus = 'AUTO_ACCEPT' | 'REVIEW_RECOMMENDED' | 'REVIEW_REQUIRED';

export interface ExplanationFactor {
  factor_name: string;
  raw_value: number;
  weight: number;
  weighted_contribution: number;
  interpretation: string;
  evidence_text: string | null;
  evidence_segment_ids: number[];
}

export interface PriorityExplainability {
  score: number;
  level: PriorityLevel;
  factors: ExplanationFactor[];
  top_contributors: ExplanationFactor[];
  supporting_evidence: string[];
  limiting_factors: string[];
  explanation_text: string;
}

export interface ConfidenceExplainability {
  score: number;
  level: ConfidenceLevel;
  factors: ExplanationFactor[];
  top_contributors: ExplanationFactor[];
  supporting_evidence: string[];
  limiting_evidence: string[];
  explanation_text: string;
}

export interface ReviewExplainability {
  status: ReviewStatus;
  review_required: boolean;
  review_recommended: boolean;
  reason_codes: string[];
  evidence_flags: Record<string, any>;
  explanation_text: string;
}

export interface EvidenceReference {
  source_type: string;
  source_id: number | string | null;
  speaker: string | null;
  start_time: number | null;
  end_time: number | null;
  text_excerpt: string | null;
}

export interface ActionItemExplanation {
  item_id: string;
  task: string;
  priority_explanation: PriorityExplainability;
  confidence_explanation: ConfidenceExplainability;
  review_explanation: ReviewExplainability;
  evidence_traces: EvidenceReference[];
  unified_explanation: string;
}

export interface RoleEmphasis {
  role: UserRole;
  highlighted_fields: string[];
  display_urgency_badge: boolean;
  display_review_badge: boolean;
  role_guidance: string;
  dependency_summary: string | null;
}

export interface SpeakerIdentity {
  speaker_id: string;
  display_name: string;
  name_source: string;
  evidence_segment_id?: number | null;
  evidence_text?: string | null;
}

export interface PersonalizedActionItem {
  item_id: string;
  task: string;
  responsible_person: string | null;
  speaker_id?: string | null;
  display_name?: string | null;
  name_source?: string | null;
  is_unassigned: boolean;
  deadline: string | null;
  is_ambiguous_deadline: boolean;
  topic_reference: number | null;
  context_status: string;
  priority_score: number;
  priority_level: PriorityLevel;
  confidence_score: number;
  confidence_level: ConfidenceLevel;
  review_status: ReviewStatus;
  review_reason_codes: string[];
  explanation: ActionItemExplanation;
  role_emphasis: RoleEmphasis;
}

export interface ContextRichDecision {
  decision: string;
  topic_reference: number | null;
  topic_summary: string | null;
  topic_speakers: string[];
  context_status: string;
}

export interface PersonalizedMeetingView {
  meeting_id: string;
  role: UserRole;
  summary_headline: string;
  total_canonical_items: number;
  displayed_items_count: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
  auto_accept_count: number;
  review_recommended_count: number;
  review_required_count: number;
  unassigned_count: number;
  has_deadline_count: number;
  speakers?: Record<string, SpeakerIdentity>;
  action_items: PersonalizedActionItem[];
  key_decisions: ContextRichDecision[];
  diagnostics: string[];
}

export interface DashboardPayload {
  meeting_id: string;
  processing_stage: string;
  total_canonical_items: number;
  speakers?: Record<string, SpeakerIdentity>;
  views: Record<UserRole, PersonalizedMeetingView>;
  key_decisions: ContextRichDecision[];
  diagnostics: string[];
}

export interface FilterState {
  role: UserRole;
  priorityLevel: 'ALL' | PriorityLevel;
  confidenceLevel: 'ALL' | ConfidenceLevel;
  reviewStatus: 'ALL' | ReviewStatus;
  assignment: 'ALL' | 'ASSIGNED' | 'UNASSIGNED';
  deadline: 'ALL' | 'HAS_DEADLINE' | 'NO_DEADLINE';
  searchQuery: string;
}
