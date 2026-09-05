import rawPayload from './es2002a_data.json';
import {
  DashboardPayload,
  FilterState,
  PersonalizedActionItem,
  PersonalizedMeetingView,
  UserRole,
} from '../types/meeting';

const payload = rawPayload as unknown as DashboardPayload;

export const dataService = {
  getPayload(): DashboardPayload {
    return payload;
  },

  getMeetingView(role: UserRole): PersonalizedMeetingView {
    const view = payload.views[role];
    if (!view) {
      return payload.views['DEFAULT'];
    }
    return view;
  },

  filterItems(items: PersonalizedActionItem[], filter: FilterState): PersonalizedActionItem[] {
    return items.filter((item) => {
      // 1. Priority filter
      if (
        filter.priorityLevel !== 'ALL' &&
        item.priority_level?.toUpperCase() !== filter.priorityLevel.toUpperCase()
      ) {
        return false;
      }

      // 2. Confidence filter
      if (filter.confidenceLevel !== 'ALL' && item.confidence_level !== filter.confidenceLevel) {
        return false;
      }

      // 3. Review status filter
      if (filter.reviewStatus !== 'ALL' && item.review_status !== filter.reviewStatus) {
        return false;
      }

      // 4. Assignment filter
      if (filter.assignment === 'ASSIGNED' && item.is_unassigned) {
        return false;
      }
      if (filter.assignment === 'UNASSIGNED' && !item.is_unassigned) {
        return false;
      }

      // 5. Deadline filter
      const hasDeadline = Boolean(item.deadline && item.deadline.trim());
      if (filter.deadline === 'HAS_DEADLINE' && !hasDeadline) {
        return false;
      }
      if (filter.deadline === 'NO_DEADLINE' && hasDeadline) {
        return false;
      }

      // 6. Search query
      if (filter.searchQuery.trim()) {
        const q = filter.searchQuery.toLowerCase().trim();
        const matchTask = item.task.toLowerCase().includes(q);
        const matchOwner = (item.responsible_person || '').toLowerCase().includes(q);
        const matchTopic = item.topic_reference !== null && String(item.topic_reference).includes(q);
        const matchId = item.item_id.toLowerCase().includes(q);
        if (!matchTask && !matchOwner && !matchTopic && !matchId) {
          return false;
        }
      }

      return true;
    });
  },

  getKeyDecisions() {
    return payload.key_decisions || [];
  },

  getItemById(itemId: string, role: UserRole): PersonalizedActionItem | undefined {
    const view = this.getMeetingView(role);
    return view.action_items.find((a) => a.item_id === itemId);
  },
};
