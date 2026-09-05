import React from 'react';
import { PersonalizedMeetingView } from '../types/meeting';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileSpreadsheet,
  Flame,
  Lightbulb,
  ShieldAlert,
} from 'lucide-react';


interface SummaryCardsProps {
  view: PersonalizedMeetingView;
  totalDecisions: number;
  onSelectPriorityFilter?: (priority: 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW') => void;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({
  view,
  totalDecisions,
  onSelectPriorityFilter,
}) => {
  const highCount =
    view.high_priority_count ??
    view.action_items.filter((i) => i.priority_level?.toUpperCase() === 'HIGH').length;
  const medCount =
    view.medium_priority_count ??
    view.action_items.filter((i) => i.priority_level?.toUpperCase() === 'MEDIUM').length;
  const lowCount =
    view.low_priority_count ??
    view.action_items.filter((i) => i.priority_level?.toUpperCase() === 'LOW').length;

  return (
    <div className="summary-grid">
      {/* 1. Total Action Items */}
      <div
        className="metric-card"
        onClick={() => onSelectPriorityFilter && onSelectPriorityFilter('ALL')}
        style={{ cursor: onSelectPriorityFilter ? 'pointer' : 'default' }}
        title="Show all tasks"
      >
        <div className="metric-header">
          <span>Total Tasks</span>
          <FileSpreadsheet size={16} color="var(--primary)" />
        </div>
        <div className="metric-value">{view.total_canonical_items}</div>
        <div className="metric-sub">Ingested & Normalized</div>
      </div>

      {/* 2. High Priority */}
      <div
        className="metric-card"
        style={{
          borderColor: 'rgba(244, 63, 94, 0.3)',
          cursor: onSelectPriorityFilter ? 'pointer' : 'default',
        }}
        onClick={() => onSelectPriorityFilter && onSelectPriorityFilter('HIGH')}
        title="Click to filter by High Priority"
      >
        <div className="metric-header">
          <span style={{ color: 'var(--priority-high)' }}>High Priority</span>
          <Flame size={16} color="var(--priority-high)" />
        </div>
        <div className="metric-value" style={{ color: 'var(--priority-high)' }}>
          {highCount}
        </div>
        <div className="metric-sub">Critical Milestones</div>
      </div>

      {/* 3. Medium Priority */}
      <div
        className="metric-card"
        style={{ cursor: onSelectPriorityFilter ? 'pointer' : 'default' }}
        onClick={() => onSelectPriorityFilter && onSelectPriorityFilter('MEDIUM')}
        title="Click to filter by Medium Priority"
      >
        <div className="metric-header">
          <span style={{ color: 'var(--priority-medium)' }}>Med Priority</span>
          <Clock size={16} color="var(--priority-medium)" />
        </div>
        <div className="metric-value" style={{ color: 'var(--priority-medium)' }}>
          {medCount}
        </div>
        <div className="metric-sub">Standard Workflows</div>
      </div>

      {/* 4. Low Priority */}
      <div
        className="metric-card"
        style={{ cursor: onSelectPriorityFilter ? 'pointer' : 'default' }}
        onClick={() => onSelectPriorityFilter && onSelectPriorityFilter('LOW')}
        title="Click to filter by Low Priority"
      >
        <div className="metric-header">
          <span style={{ color: 'var(--priority-low)' }}>Low Priority</span>
          <CheckCircle2 size={16} color="var(--priority-low)" />
        </div>
        <div className="metric-value" style={{ color: 'var(--priority-low)' }}>
          {lowCount}
        </div>
        <div className="metric-sub">Routine Discussions</div>
      </div>

      {/* 5. Auto Accepted */}
      <div className="metric-card">
        <div className="metric-header">
          <span style={{ color: 'var(--review-auto)' }}>Auto Accepted</span>
          <CheckCircle2 size={16} color="var(--review-auto)" />
        </div>
        <div className="metric-value" style={{ color: 'var(--review-auto)' }}>
          {view.auto_accept_count}
        </div>
        <div className="metric-sub">High Confidence / Clear</div>
      </div>

      {/* 6. Review Recommended */}
      <div className="metric-card" style={{ borderColor: 'rgba(245, 158, 11, 0.3)' }}>
        <div className="metric-header">
          <span style={{ color: 'var(--review-rec)' }}>Needs Review</span>
          <AlertTriangle size={16} color="var(--review-rec)" />
        </div>
        <div className="metric-value" style={{ color: 'var(--review-rec)' }}>
          {view.review_recommended_count}
        </div>
        <div className="metric-sub">Flagged For Triage</div>
      </div>

      {/* 7. Review Required */}
      <div className="metric-card">
        <div className="metric-header">
          <span style={{ color: 'var(--review-req)' }}>Review Req.</span>
          <ShieldAlert size={16} color="var(--review-req)" />
        </div>
        <div className="metric-value" style={{ color: 'var(--review-req)' }}>
          {view.review_required_count}
        </div>
        <div className="metric-sub">Blockers / Low Conf.</div>
      </div>

      {/* 8. Decisions */}
      <div className="metric-card">
        <div className="metric-header">
          <span>Decisions</span>
          <Lightbulb size={16} color="var(--accent-cyan)" />
        </div>
        <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
          {totalDecisions}
        </div>
        <div className="metric-sub">Linked Contextual Decisions</div>
      </div>
    </div>
  );
};
