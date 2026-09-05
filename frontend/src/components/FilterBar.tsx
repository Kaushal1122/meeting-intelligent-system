import React from 'react';
import { ConfidenceLevel, FilterState, PriorityLevel, ReviewStatus } from '../types/meeting';
import { RotateCcw, Search } from 'lucide-react';

interface FilterBarProps {
  filter: FilterState;
  onChangeFilter: (newFilter: FilterState) => void;
  displayedCount: number;
  totalCount: number;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filter,
  onChangeFilter,
  displayedCount,
  totalCount,
}) => {
  const handleReset = () => {
    onChangeFilter({
      role: filter.role,
      priorityLevel: 'ALL',
      confidenceLevel: 'ALL',
      reviewStatus: 'ALL',
      assignment: 'ALL',
      deadline: 'ALL',
      searchQuery: '',
    });
  };

  const isFiltered =
    filter.priorityLevel !== 'ALL' ||
    filter.confidenceLevel !== 'ALL' ||
    filter.reviewStatus !== 'ALL' ||
    filter.assignment !== 'ALL' ||
    filter.deadline !== 'ALL' ||
    filter.searchQuery.trim() !== '';

  return (
    <div className="filter-bar">
      {/* Search Input */}
      <div className="search-box">
        <Search className="search-icon" size={16} />
        <input
          type="text"
          className="search-input"
          placeholder="Search task, owner, or topic..."
          value={filter.searchQuery}
          onChange={(e) => onChangeFilter({ ...filter, searchQuery: e.target.value })}
        />
      </div>

      {/* Priority Filter */}
      <select
        className="filter-select"
        value={filter.priorityLevel}
        onChange={(e) =>
          onChangeFilter({ ...filter, priorityLevel: e.target.value as 'ALL' | PriorityLevel })
        }
        aria-label="Filter by Priority"
      >
        <option value="ALL">Priority: All</option>
        <option value="HIGH">Priority: HIGH</option>
        <option value="MEDIUM">Priority: MEDIUM</option>
        <option value="LOW">Priority: LOW</option>
      </select>

      {/* Confidence Filter */}
      <select
        className="filter-select"
        value={filter.confidenceLevel}
        onChange={(e) =>
          onChangeFilter({ ...filter, confidenceLevel: e.target.value as 'ALL' | ConfidenceLevel })
        }
        aria-label="Filter by Confidence"
      >
        <option value="ALL">Confidence: All</option>
        <option value="HIGH">Confidence: HIGH</option>
        <option value="MEDIUM">Confidence: MEDIUM</option>
        <option value="LOW">Confidence: LOW</option>
      </select>

      {/* Review Status Filter */}
      <select
        className="filter-select"
        value={filter.reviewStatus}
        onChange={(e) =>
          onChangeFilter({ ...filter, reviewStatus: e.target.value as 'ALL' | ReviewStatus })
        }
        aria-label="Filter by Review Status"
      >
        <option value="ALL">Review: All</option>
        <option value="AUTO_ACCEPT">Auto Accept</option>
        <option value="REVIEW_RECOMMENDED">Review Recommended</option>
        <option value="REVIEW_REQUIRED">Review Required</option>
      </select>

      {/* Assignment Filter */}
      <select
        className="filter-select"
        value={filter.assignment}
        onChange={(e) =>
          onChangeFilter({
            ...filter,
            assignment: e.target.value as 'ALL' | 'ASSIGNED' | 'UNASSIGNED',
          })
        }
        aria-label="Filter by Assignment"
      >
        <option value="ALL">Assignment: All</option>
        <option value="ASSIGNED">Assigned Only</option>
        <option value="UNASSIGNED">Unassigned Only</option>
      </select>

      {/* Deadline Filter */}
      <select
        className="filter-select"
        value={filter.deadline}
        onChange={(e) =>
          onChangeFilter({
            ...filter,
            deadline: e.target.value as 'ALL' | 'HAS_DEADLINE' | 'NO_DEADLINE',
          })
        }
        aria-label="Filter by Deadline"
      >
        <option value="ALL">Deadline: All</option>
        <option value="HAS_DEADLINE">With Deadline</option>
        <option value="NO_DEADLINE">No Deadline</option>
      </select>

      {/* Reset Filter Button */}
      {isFiltered && (
        <button className="filter-reset-btn" onClick={handleReset} title="Clear all filters">
          <RotateCcw size={12} style={{ display: 'inline', marginRight: 4 }} />
          Reset ({displayedCount}/{totalCount})
        </button>
      )}
    </div>
  );
};
