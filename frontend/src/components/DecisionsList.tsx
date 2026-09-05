import React, { useState } from 'react';
import { ContextRichDecision } from '../types/meeting';
import { ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';

interface DecisionsListProps {
  decisions: ContextRichDecision[];
}

export const DecisionsList: React.FC<DecisionsListProps> = ({ decisions }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '20px',
        marginBottom: '28px',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Lightbulb size={20} color="var(--accent-purple)" />
          <h3 style={{ fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
            Meeting Key Decisions ({decisions.length})
          </h3>
          <span className="topic-badge">Grounding Context</span>
        </div>
        <button
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: '0.82rem',
          }}
        >
          {isExpanded ? (
            <>
              Hide Decisions <ChevronUp size={16} />
            </>
          ) : (
            <>
              Show Decisions <ChevronDown size={16} />
            </>
          )}
        </button>
      </div>

      {isExpanded && (
        <div
          style={{
            marginTop: 16,
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 12,
          }}
        >
          {decisions.map((d, idx) => (
            <div
              key={idx}
              style={{
                background: 'var(--bg-card-subtle)',
                border: '1px solid var(--border-card)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: 6,
                  fontSize: '0.78rem',
                }}
              >
                <span className="topic-badge">
                  {d.topic_reference !== null ? `Topic ${d.topic_reference}` : 'General'}
                </span>
                {d.topic_speakers.length > 0 && (
                  <span style={{ color: 'var(--text-muted)' }}>
                    Speakers: {d.topic_speakers.join(', ')}
                  </span>
                )}
              </div>
              <p style={{ color: '#fff', fontSize: '0.88rem', fontWeight: 500, lineHeight: 1.4 }}>
                {d.decision}
              </p>
              {d.topic_summary && (
                <p
                  style={{
                    color: 'var(--text-muted)',
                    fontSize: '0.78rem',
                    marginTop: 6,
                    lineHeight: 1.3,
                  }}
                >
                  Context: {d.topic_summary}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
