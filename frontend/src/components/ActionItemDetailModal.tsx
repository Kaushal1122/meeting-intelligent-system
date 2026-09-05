import React from 'react';
import { ContextRichDecision, PersonalizedActionItem } from '../types/meeting';
import {
  cleanFactorName,
  formatScore,
  formatTimestamp,
  getConfidenceBadgeClass,
  getPriorityBadgeClass,
  getReviewBadgeClass,
  getReviewLabel,
} from '../utils/formatters';
import {
  AlertTriangle,
  Award,
  CheckCircle2,
  Clock,
  Flame,
  Lightbulb,
  MessageSquare,
  Sparkles,
  User,
  X,
} from 'lucide-react';


interface ActionItemDetailModalProps {
  item: PersonalizedActionItem | null;
  allDecisions: ContextRichDecision[];
  onClose: () => void;
}

export const ActionItemDetailModal: React.FC<ActionItemDetailModalProps> = ({
  item,
  allDecisions,
  onClose,
}) => {
  if (!item) return null;

  const { explanation, role_emphasis } = item;
  const pExp = explanation.priority_explanation;
  const cExp = explanation.confidence_explanation;
  const rExp = explanation.review_explanation;

  // Filter decisions related to this item's topic
  const relatedDecisions = allDecisions.filter(
    (d) => item.topic_reference !== null && d.topic_reference === item.topic_reference
  );

  const hasConflictingDecisions = item.review_reason_codes.includes('CONFLICTING_DECISIONS');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span className="topic-badge">{item.item_id}</span>
              {item.topic_reference !== null && (
                <span className="topic-badge">Topic {item.topic_reference}</span>
              )}
              <span className="topic-badge" style={{ color: '#a78bfa' }}>
                Context: {item.context_status}
              </span>
            </div>
            <h2 style={{ fontSize: '1.2rem', color: '#fff', lineHeight: 1.35 }}>{item.task}</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close inspection drawer">
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Executive Badges Bar */}
          <div
            style={{
              display: 'flex',
              gap: 10,
              flexWrap: 'wrap',
              alignItems: 'center',
              padding: '12px 16px',
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-card)',
            }}
          >
            <span className={getPriorityBadgeClass(item.priority_level)}>
              Priority: {item.priority_level} ({formatScore(item.priority_score)})
            </span>
            <span className={getConfidenceBadgeClass(item.confidence_level)}>
              Confidence: {item.confidence_level} ({formatScore(item.confidence_score)})
            </span>
            <span className={getReviewBadgeClass(item.review_status)}>
              {getReviewLabel(item.review_status)}
            </span>
            {item.priority_level?.toUpperCase() === 'HIGH' && (
              <span className="badge badge-priority-high">
                <Flame size={12} /> High Priority
              </span>
            )}
          </div>

          {/* Role-Specific Guidance Callout */}
          <div
            className="detail-section"
            style={{
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.05))',
              borderColor: 'rgba(99, 102, 241, 0.3)',
            }}
          >
            <div className="detail-section-title" style={{ color: '#c7d2fe' }}>
              <Sparkles size={16} color="var(--primary)" />
              <span>Persona Projection Guidance ({role_emphasis.role})</span>
            </div>
            <p style={{ fontSize: '0.9rem', color: '#e2e8f0', marginBottom: 8 }}>
              {role_emphasis.role_guidance}
            </p>
            {role_emphasis.dependency_summary && (
              <div style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
                <strong>Technical Dependency:</strong> {role_emphasis.dependency_summary}
              </div>
            )}
          </div>

          {/* Assignment & Deadline Metadata */}
          <div
            className="detail-section"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: 16,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <User size={13} /> Assigned Speaker / Owner
              </div>
              <div
                style={{
                  fontSize: '0.95rem',
                  color: '#fff',
                  fontWeight: 600,
                  marginTop: 4,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {item.display_name || item.responsible_person || item.speaker_id || '(Unassigned)'}
              </div>
              {item.speaker_id && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  <span>ID: {item.speaker_id}</span>
                  {item.name_source && (
                    <span
                      style={{
                        marginLeft: 6,
                        color: item.name_source === 'explicit_transcript' ? 'var(--accent-cyan)' : 'var(--text-muted)',
                      }}
                    >
                      ({item.name_source === 'explicit_transcript' ? 'Verified from transcript' : 'Diarization fallback'})
                    </span>
                  )}
                </div>
              )}
            </div>

            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <Clock size={13} /> Deadline Commitment
              </div>
              <div
                style={{
                  fontSize: '0.95rem',
                  color: item.deadline ? 'var(--priority-medium)' : 'var(--text-secondary)',
                  fontWeight: 600,
                  marginTop: 4,
                }}
              >
                {item.deadline || '(No explicit deadline specified)'}
              </div>
            </div>

            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <Award size={13} /> Review Action
              </div>
              <div style={{ fontSize: '0.95rem', color: '#fff', fontWeight: 600, marginTop: 4 }}>
                {item.review_status === 'AUTO_ACCEPT' ? 'Automatic Acceptance' : 'Requires Verification'}
              </div>
            </div>
          </div>

          {/* SECTION 1: Human Review Triage & Uncertainty */}
          <div className="detail-section">
            <div className="detail-section-title">
              {item.review_status === 'AUTO_ACCEPT' ? (
                <CheckCircle2 size={16} color="var(--review-auto)" />
              ) : (
                <AlertTriangle size={16} color="var(--review-rec)" />
              )}
              <span>Human Review Triage Assessment</span>
            </div>

            {hasConflictingDecisions && (
              <div className="conflict-alert">
                <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Conflicting Decisions Detected:</strong> Topic {item.topic_reference} contains
                  competing design proposals in dialogue context. Manual consensus verification is
                  recommended.
                </div>
              </div>
            )}

            <p style={{ fontSize: '0.88rem', color: '#e2e8f0', marginBottom: 12 }}>
              {rExp.explanation_text}
            </p>

            {item.review_reason_codes.length > 0 && (
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                  Triggered Reason Codes:
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {item.review_reason_codes.map((code) => (
                    <span key={code} className="badge badge-review-recommended">
                      {code}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* SECTION 2: Priority Explainability & Factor Decomposition */}
          <div className="detail-section">
            <div className="detail-section-title">
              <Flame size={16} color="var(--priority-high)" />
              <span>Priority Multi-Factor Decomposition (Score: {formatScore(pExp.score)})</span>
            </div>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginBottom: 12 }}>
              {pExp.explanation_text}
            </p>

            <table className="factor-table">
              <thead>
                <tr>
                  <th>Factor Name</th>
                  <th>Raw Value</th>
                  <th>Weight</th>
                  <th>Contribution</th>
                  <th>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {pExp.factors.map((f) => (
                  <tr key={f.factor_name}>
                    <td>
                      <strong>{cleanFactorName(f.factor_name)}</strong>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{f.raw_value.toFixed(2)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{f.weight.toFixed(2)}</td>
                    <td className="factor-contrib">+{formatScore(f.weighted_contribution)}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{f.interpretation}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {pExp.supporting_evidence.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--conf-high)', fontWeight: 600 }}>
                  Primary Priority Drivers:
                </div>
                <ul
                  style={{
                    fontSize: '0.82rem',
                    color: '#94a3b8',
                    paddingLeft: 18,
                    marginTop: 4,
                  }}
                >
                  {pExp.supporting_evidence.map((ev, idx) => (
                    <li key={idx}>{ev}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* SECTION 3: Confidence Reliability Assessment */}
          <div className="detail-section">
            <div className="detail-section-title">
              <CheckCircle2 size={16} color="var(--conf-high)" />
              <span>Confidence Reliability Calibration (Score: {formatScore(cExp.score)})</span>
            </div>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginBottom: 12 }}>
              {cExp.explanation_text}
            </p>

            <table className="factor-table">
              <thead>
                <tr>
                  <th>Factor Name</th>
                  <th>Raw Value</th>
                  <th>Weight</th>
                  <th>Contribution</th>
                  <th>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {cExp.factors.map((f) => (
                  <tr key={f.factor_name}>
                    <td>
                      <strong>{cleanFactorName(f.factor_name)}</strong>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{f.raw_value.toFixed(2)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{f.weight.toFixed(2)}</td>
                    <td className="factor-contrib" style={{ color: 'var(--conf-medium)' }}>
                      +{formatScore(f.weighted_contribution)}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{f.interpretation}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {cExp.limiting_evidence.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--review-rec)', fontWeight: 600 }}>
                  Limiting Uncertainty Factors:
                </div>
                <ul
                  style={{
                    fontSize: '0.82rem',
                    color: '#94a3b8',
                    paddingLeft: 18,
                    marginTop: 4,
                  }}
                >
                  {cExp.limiting_evidence.map((ev, idx) => (
                    <li key={idx}>{ev}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* SECTION 4: Dialogue Provenance & Verbatim Transcript Traces */}
          <div className="detail-section">
            <div className="detail-section-title">
              <MessageSquare size={16} color="var(--accent-cyan)" />
              <span>Verifiable Dialogue Provenance & Evidence Traces</span>
            </div>

            {explanation.evidence_traces.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No segment traces attached.
              </div>
            ) : (
              explanation.evidence_traces.map((trace, idx) => (
                <div key={idx} className="evidence-box">
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '0.78rem',
                      color: 'var(--text-muted)',
                    }}
                  >
                    <span>
                      <strong>Source:</strong> {trace.source_type} #{String(trace.source_id)}
                      {trace.speaker && ` | Speaker: ${trace.speaker}`}
                    </span>
                    {trace.start_time !== null && (
                      <span>Time: {formatTimestamp(trace.start_time)}</span>
                    )}
                  </div>
                  {trace.text_excerpt && (
                    <div className="verbatim-quote">"{trace.text_excerpt}"</div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* SECTION 5: Linked Decisions in Meeting Context */}
          <div className="detail-section">
            <div className="detail-section-title">
              <Lightbulb size={16} color="var(--accent-purple)" />
              <span>Linked Key Decisions ({relatedDecisions.length})</span>
            </div>

            {relatedDecisions.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No explicit key decisions linked directly to Topic {item.topic_reference}.
              </div>
            ) : (
              relatedDecisions.map((dec, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'var(--bg-card-subtle)',
                    border: '1px solid var(--border-card)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '12px',
                    marginBottom: 8,
                  }}
                >
                  <div
                    style={{
                      fontSize: '0.78rem',
                      color: 'var(--accent-purple)',
                      marginBottom: 4,
                      fontWeight: 600,
                    }}
                  >
                    Decision Statement:
                  </div>
                  <div style={{ color: '#fff', fontSize: '0.9rem', lineHeight: 1.4 }}>
                    {dec.decision}
                  </div>
                  {dec.topic_summary && (
                    <div
                      style={{
                        fontSize: '0.78rem',
                        color: 'var(--text-secondary)',
                        marginTop: 6,
                      }}
                    >
                      Context: {dec.topic_summary}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
