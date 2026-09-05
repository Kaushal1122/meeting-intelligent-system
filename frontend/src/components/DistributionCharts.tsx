import React from 'react';
import { PersonalizedActionItem } from '../types/meeting';

interface DistributionChartsProps {
  items: PersonalizedActionItem[];
}

export const DistributionCharts: React.FC<DistributionChartsProps> = ({ items }) => {
  const total = items.length || 1;

  // Priority counts
  const pHigh = items.filter((i) => i.priority_level === 'HIGH').length;
  const pMed = items.filter((i) => i.priority_level === 'MEDIUM').length;
  const pLow = items.filter((i) => i.priority_level === 'LOW').length;

  // Confidence counts
  const cHigh = items.filter((i) => i.confidence_level === 'HIGH').length;
  const cMed = items.filter((i) => i.confidence_level === 'MEDIUM').length;
  const cLow = items.filter((i) => i.confidence_level === 'LOW').length;

  // Review counts
  const rAuto = items.filter((i) => i.review_status === 'AUTO_ACCEPT').length;
  const rRec = items.filter((i) => i.review_status === 'REVIEW_RECOMMENDED').length;
  const rReq = items.filter((i) => i.review_status === 'REVIEW_REQUIRED').length;

  return (
    <div className="distribution-panel">
      <div className="distribution-panel-header">
        <span>Intelligence Distribution Analysis ({items.length} items evaluated)</span>
      </div>

      <div className="distribution-columns">
        {/* Priority Distribution */}
        <div className="dist-bar-group">
          <div className="dist-bar-label">
            <strong>Priority Distribution</strong>
            <span>
              H: {pHigh} | M: {pMed} | L: {pLow}
            </span>
          </div>
          <div className="progress-track" title={`High: ${pHigh}, Medium: ${pMed}, Low: ${pLow}`}>
            <div
              className="progress-fill"
              style={{
                width: `${(pHigh / total) * 100}%`,
                backgroundColor: 'var(--priority-high)',
              }}
            />
            <div
              className="progress-fill"
              style={{
                width: `${(pMed / total) * 100}%`,
                backgroundColor: 'var(--priority-medium)',
              }}
            />
            <div
              className="progress-fill"
              style={{
                width: `${(pLow / total) * 100}%`,
                backgroundColor: 'var(--priority-low)',
              }}
            />
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="dist-bar-group">
          <div className="dist-bar-label">
            <strong>Confidence Calibration</strong>
            <span>
              H: {cHigh} | M: {cMed} | L: {cLow}
            </span>
          </div>
          <div className="progress-track" title={`High: ${cHigh}, Medium: ${cMed}, Low: ${cLow}`}>
            <div
              className="progress-fill"
              style={{
                width: `${(cHigh / total) * 100}%`,
                backgroundColor: 'var(--conf-high)',
              }}
            />
            <div
              className="progress-fill"
              style={{
                width: `${(cMed / total) * 100}%`,
                backgroundColor: 'var(--conf-medium)',
              }}
            />
            <div
              className="progress-fill"
              style={{
                width: `${(cLow / total) * 100}%`,
                backgroundColor: 'var(--conf-low)',
              }}
            />
          </div>
        </div>

        {/* Review Status Distribution */}
        <div className="dist-bar-group">
          <div className="dist-bar-label">
            <strong>Human Review Triage</strong>
            <span>
              Auto: {rAuto} | Rec: {rRec} | Req: {rReq}
            </span>
          </div>
          <div className="progress-track" title={`Auto: ${rAuto}, Recommended: ${rRec}, Required: ${rReq}`}>
            <div
              className="progress-fill"
              style={{
                width: `${(rAuto / total) * 100}%`,
                backgroundColor: 'var(--review-auto)',
              }}
            />
            <div
              className="progress-fill"
              style={{
                width: `${(rRec / total) * 100}%`,
                backgroundColor: 'var(--review-rec)',
              }}
            />
            <div
              className="progress-fill"
              style={{
                width: `${(rReq / total) * 100}%`,
                backgroundColor: 'var(--review-req)',
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
