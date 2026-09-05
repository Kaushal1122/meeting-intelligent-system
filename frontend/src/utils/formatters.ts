import { ConfidenceLevel, PriorityLevel, ReviewStatus } from '../types/meeting';

export function formatScore(score: number): string {
  return score.toFixed(4);
}

export function formatPercent(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

export function getPriorityBadgeClass(level: PriorityLevel): string {
  switch (level) {
    case 'HIGH':
      return 'badge badge-priority-high';
    case 'MEDIUM':
      return 'badge badge-priority-medium';
    case 'LOW':
      return 'badge badge-priority-low';
    default:
      return 'badge';
  }
}

export function getConfidenceBadgeClass(level: ConfidenceLevel): string {
  switch (level) {
    case 'HIGH':
      return 'badge badge-confidence-high';
    case 'MEDIUM':
      return 'badge badge-confidence-medium';
    case 'LOW':
      return 'badge badge-confidence-low';
    default:
      return 'badge';
  }
}

export function getReviewBadgeClass(status: ReviewStatus): string {
  switch (status) {
    case 'AUTO_ACCEPT':
      return 'badge badge-review-auto';
    case 'REVIEW_RECOMMENDED':
      return 'badge badge-review-recommended';
    case 'REVIEW_REQUIRED':
      return 'badge badge-review-required';
    default:
      return 'badge';
  }
}

export function getReviewLabel(status: ReviewStatus): string {
  switch (status) {
    case 'AUTO_ACCEPT':
      return 'Auto Accepted';
    case 'REVIEW_RECOMMENDED':
      return 'Review Recommended';
    case 'REVIEW_REQUIRED':
      return 'Review Required';
    default:
      return status;
  }
}

export function cleanFactorName(name: string): string {
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function formatTimestamp(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return 'N/A';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')} (${seconds.toFixed(1)}s)`;
}
