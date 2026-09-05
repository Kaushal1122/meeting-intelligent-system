import React, { useMemo, useState } from 'react';
import { DashboardPayload, FilterState, PersonalizedActionItem, UserRole } from './types/meeting';
import { dataService } from './data/dataService';
import { Header } from './components/Header';
import { MeetingInputWidget } from './components/MeetingInputWidget';
import { SummaryCards } from './components/SummaryCards';
import { DistributionCharts } from './components/DistributionCharts';
import { FilterBar } from './components/FilterBar';
import { ActionItemTable } from './components/ActionItemTable';
import { ActionItemDetailModal } from './components/ActionItemDetailModal';
import { DecisionsList } from './components/DecisionsList';
import { Loader2, Radio, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [selectedRole, setSelectedRole] = useState<UserRole>('MANAGER');
  const [selectedItem, setSelectedItem] = useState<PersonalizedActionItem | null>(null);

  // Active meeting payload is initially null so previous audio/results are not shown automatically
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [isLiveApiData, setIsLiveApiData] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const [filter, setFilter] = useState<FilterState>({
    role: selectedRole,
    priorityLevel: 'ALL',
    confidenceLevel: 'ALL',
    reviewStatus: 'ALL',
    assignment: 'ALL',
    deadline: 'ALL',
    searchQuery: '',
  });

  // Handle role change
  const handleRoleChange = (role: UserRole) => {
    setSelectedRole(role);
    setFilter((prev) => ({ ...prev, role }));
  };

  // Handle processing lifecycle from MeetingInputWidget
  const handleProcessingStart = () => {
    setIsProcessing(true);
  };

  const handleProcessingSuccess = (newPayload: DashboardPayload) => {
    setPayload(newPayload);
    setIsLiveApiData(true);
    setIsProcessing(false);
    setSelectedItem(null);
  };

  const handleProcessingError = () => {
    setIsProcessing(false);
  };

  // Get current role's view from active payload
  const view = useMemo(() => {
    if (!payload) return null;
    const roleView = payload.views[selectedRole];
    if (roleView) return roleView;
    return payload.views['DEFAULT'] || Object.values(payload.views)[0] || null;
  }, [payload, selectedRole]);

  // Key decisions
  const decisions = useMemo(() => {
    if (!payload) return [];
    return payload.key_decisions || [];
  }, [payload]);

  // Filtered action items
  const filteredItems = useMemo(() => {
    if (!view) return [];
    return dataService.filterItems(view.action_items, filter);
  }, [view, filter]);

  return (
    <div className="app-container">
      {/* Header with Meeting ID & Role Switcher */}
      <Header
        meetingId={view?.meeting_id || ''}
        selectedRole={selectedRole}
        onSelectRole={handleRoleChange}
      />

      {/* Meeting Input Area (Upload Audio / Transcript / Pasted Text) */}
      <MeetingInputWidget
        onProcessingStart={handleProcessingStart}
        onProcessingSuccess={handleProcessingSuccess}
        onProcessingError={handleProcessingError}
      />

      {/* Initial Empty State (No meeting loaded and not currently processing) */}
      {!payload && !isProcessing && (
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px dashed var(--border-card)',
            borderRadius: 'var(--radius-lg)',
            padding: '56px 24px',
            textAlign: 'center',
            marginTop: '8px',
            boxShadow: 'var(--shadow-card)',
          }}
        >
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: 'rgba(99, 102, 241, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}
          >
            <Sparkles size={24} color="var(--primary)" />
          </div>
          <h3
            style={{
              fontSize: '1.25rem',
              color: '#fff',
              marginBottom: '10px',
              fontWeight: 700,
            }}
          >
            No Meeting Results Loaded
          </h3>
          <p
            style={{
              color: 'var(--text-secondary)',
              fontSize: '0.92rem',
              maxWidth: '560px',
              margin: '0 auto',
              lineHeight: 1.6,
            }}
          >
            Select an audio file, upload a transcript file, or paste transcript dialogue above and
            click <strong>Process Meeting</strong> to run post-extraction intelligence and explore
            role-tailored views.
          </p>
        </div>
      )}

      {/* Processing State Indicator */}
      {isProcessing && !payload && (
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-card)',
            borderRadius: 'var(--radius-lg)',
            padding: '56px 24px',
            textAlign: 'center',
            marginTop: '8px',
            boxShadow: 'var(--shadow-card)',
          }}
        >
          <Loader2
            size={40}
            className="spinner"
            style={{
              margin: '0 auto 16px',
              animation: 'spin 1s linear infinite',
              color: 'var(--primary)',
            }}
          />
          <h3
            style={{
              fontSize: '1.2rem',
              color: '#fff',
              marginBottom: '8px',
              fontWeight: 700,
            }}
          >
            Analyzing Meeting Intelligence...
          </h3>
          <p
            style={{
              color: 'var(--text-secondary)',
              fontSize: '0.9rem',
              maxWidth: '520px',
              margin: '0 auto',
            }}
          >
            Evaluating dialogue windows, scoring operational priorities, calibrating evidence
            reliability, and structuring key decisions...
          </p>
        </div>
      )}

      {/* Results View: rendered only when meeting intelligence payload is available */}
      {payload && view && (
        <>
          {/* Executive Role-Calibrated Headline Banner */}
          <div className="executive-banner">
            <div className="banner-content">
              <Sparkles className="banner-icon" size={20} />
              <div className="banner-text">
                <strong>Executive Focus ({selectedRole}):</strong> {view.summary_headline}
              </div>
            </div>
            <div className="banner-tag" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {isLiveApiData ? (
                <>
                  <Radio size={12} color="#10b981" /> Live API Result
                </>
              ) : (
                'Loaded Result'
              )}
            </div>
          </div>

          {/* Summary Metric Cards (Derived from Active Canonical Intelligence) */}
          <SummaryCards
            view={view}
            totalDecisions={decisions.length}
            onSelectPriorityFilter={(p) => setFilter((prev) => ({ ...prev, priorityLevel: p }))}
          />

          {/* Visual Distribution Charts (Priority, Confidence, Review) */}
          <DistributionCharts items={view.action_items} />

          {/* Key Decisions Collapsible Section */}
          <DecisionsList decisions={decisions} />

          {/* Filter Controls */}
          <FilterBar
            filter={filter}
            onChangeFilter={setFilter}
            displayedCount={filteredItems.length}
            totalCount={view.total_canonical_items}
          />

          {/* Action Items Table / List */}
          <ActionItemTable items={filteredItems} onSelectItem={(item) => setSelectedItem(item)} />

          {/* Slide-over Deep Inspection Drawer */}
          <ActionItemDetailModal
            item={selectedItem}
            allDecisions={decisions}
            onClose={() => setSelectedItem(null)}
          />
        </>
      )}
    </div>
  );
};

export default App;

