import React, { useMemo, useState } from 'react';
import { PersonalizedActionItem } from '../types/meeting';
import {
  formatScore,
  getConfidenceBadgeClass,
  getPriorityBadgeClass,
  getReviewBadgeClass,
  getReviewLabel,
} from '../utils/formatters';
import {
  AlertCircle,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  Flame,
  ShieldAlert,
} from 'lucide-react';

interface ActionItemTableProps {
  items: PersonalizedActionItem[];
  onSelectItem: (item: PersonalizedActionItem) => void;
}

type PrioritySortOrder = 'DESC' | 'ASC' | 'DEFAULT';

const PRIORITY_ORDER_RANK: Record<string, number> = {
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
};

export const ActionItemTable: React.FC<ActionItemTableProps> = ({ items, onSelectItem }) => {
  const [prioritySort, setPrioritySort] = useState<PrioritySortOrder>('DESC');

  const handleTogglePrioritySort = () => {
    setPrioritySort((prev) => {
      if (prev === 'DESC') return 'ASC';
      if (prev === 'ASC') return 'DEFAULT';
      return 'DESC';
    });
  };

  const sortedItems = useMemo(() => {
    if (prioritySort === 'DEFAULT') {
      return items;
    }
    const cloned = [...items];
    return cloned.sort((a, b) => {
      const rankA = PRIORITY_ORDER_RANK[a.priority_level?.toUpperCase()] || 0;
      const rankB = PRIORITY_ORDER_RANK[b.priority_level?.toUpperCase()] || 0;
      if (prioritySort === 'DESC') {
        if (rankA !== rankB) return rankB - rankA;
        return b.priority_score - a.priority_score;
      } else {
        if (rankA !== rankB) return rankA - rankB;
        return a.priority_score - b.priority_score;
      }
    });
  }, [items, prioritySort]);

  if (items.length === 0) {
    return (
      <div className="table-container">
        <div className="empty-state">
          <AlertCircle size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
          <h3>No action items match the current filters</h3>
          <p>Try broadening your filter criteria or resetting filters.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="items-table">
        <thead>
          <tr>
            <th>Action Item & Guidance</th>
            <th>Owner</th>
            <th>Deadline</th>
            <th>Topic</th>
            <th
              onClick={handleTogglePrioritySort}
              style={{ cursor: 'pointer', userSelect: 'none' }}
              title="Click to sort by Priority (High to Low / Low to High)"
            >
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span>Priority</span>
                {prioritySort === 'DESC' && <ArrowDown size={14} color="var(--primary)" />}
                {prioritySort === 'ASC' && <ArrowUp size={14} color="var(--primary)" />}
                {prioritySort === 'DEFAULT' && (
                  <ArrowUpDown size={14} style={{ opacity: 0.4 }} />
                )}
              </div>
            </th>
            <th>Confidence</th>
            <th>Review Status</th>
            <th style={{ width: 40 }}></th>
          </tr>
        </thead>
        <tbody>
          {sortedItems.map((item) => {
            const isHighPriority = item.priority_level?.toUpperCase() === 'HIGH';
            const hasReviewWarning = item.role_emphasis.display_review_badge;

            return (
              <tr
                key={item.item_id}
                className="clickable-row"
                onClick={() => onSelectItem(item)}
                title="Click to inspect full explainability, factor contributions, and evidence traces"
              >
                {/* Task & Guidance */}
                <td className="task-cell">
                  <div className="task-text">{item.task}</div>
                  {item.role_emphasis.role_guidance && (
                    <div className="task-guidance">
                      {isHighPriority && <Flame size={12} color="var(--priority-high)" />}
                      {hasReviewWarning && <AlertTriangle size={12} color="var(--review-rec)" />}
                      <span>{item.role_emphasis.role_guidance}</span>
                    </div>
                  )}
                  {item.role_emphasis.dependency_summary && (
                    <div
                      className="task-guidance"
                      style={{ color: 'var(--accent-cyan)', marginTop: 2 }}
                    >
                      <span>Prereq: {item.role_emphasis.dependency_summary}</span>
                    </div>
                  )}
                </td>

                {/* Owner */}
                <td>
                  <span
                    className="owner-text"
                    title={item.speaker_id ? `Speaker ID: ${item.speaker_id} (${item.name_source || 'diarization'})` : 'Unassigned'}
                  >
                    {item.display_name || item.responsible_person || item.speaker_id || (
                      <span style={{ color: 'var(--text-muted)' }}>(Unassigned)</span>
                    )}
                  </span>
                </td>

                {/* Deadline */}
                <td>
                  {item.deadline ? (
                    <span className="deadline-text deadline-highlight">{item.deadline}</span>
                  ) : (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>(None)</span>
                  )}
                </td>

                {/* Topic */}
                <td>
                  {item.topic_reference !== null ? (
                    <span className="topic-badge">Topic {item.topic_reference}</span>
                  ) : (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>N/A</span>
                  )}
                </td>

                {/* Priority */}
                <td>
                  <span className={getPriorityBadgeClass(item.priority_level)}>
                    {item.priority_level}{' '}
                    <span className="badge-score">{formatScore(item.priority_score)}</span>
                  </span>
                </td>

                {/* Confidence */}
                <td>
                  <span className={getConfidenceBadgeClass(item.confidence_level)}>
                    {item.confidence_level}{' '}
                    <span className="badge-score">{formatScore(item.confidence_score)}</span>
                  </span>
                </td>

                {/* Review Status */}
                <td>
                  <span className={getReviewBadgeClass(item.review_status)}>
                    {item.review_status === 'REVIEW_REQUIRED' && <ShieldAlert size={12} />}
                    {item.review_status === 'REVIEW_RECOMMENDED' && <AlertTriangle size={12} />}
                    {getReviewLabel(item.review_status)}
                  </span>
                </td>

                {/* Action Arrow */}
                <td>
                  <ChevronRight size={16} color="var(--text-muted)" />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
