import React from 'react';
import { useCase } from '../../context/CaseContext';

export default function StatusBar() {
  const { cases, campaigns, districts } = useCase();

  // Find top priority district
  let topDistrict = 'N/A';
  let topScore = -1;

  if (districts && districts.length > 0) {
    districts.forEach(d => {
      if (d.priority_score > topScore) {
        topScore = d.priority_score;
        topDistrict = d.name;
      }
    });
  }

  // Active cases count (non-legitimate, non-false positive)
  const activeCasesCount = cases.filter(c => c.fraud_type !== 'legitimate' && c.status !== 'false_positive').length;

  return (
    <div className="h-12 w-full bg-bg-surface border-b border-border-hairline flex items-center justify-between px-6 select-none z-10">
      {/* Title / Logo */}
      <div className="flex items-center space-x-3">
        <span className="font-sans text-lg font-bold tracking-widest text-accent-signal">KAVACH</span>
        <span className="h-4 w-px bg-border-hairline"></span>
        <span className="font-mono text-xs text-text-secondary uppercase tracking-wider">Investigator's Terminal</span>
      </div>

      {/* Live System Metrics */}
      <div className="flex items-center space-x-8">
        {/* Metric 1 */}
        <div className="flex items-center space-x-2">
          <span className="font-mono text-[10px] text-text-secondary uppercase tracking-wider">ACTIVE_CASES:</span>
          <span className="font-mono text-sm font-semibold text-text-primary px-1.5 py-0.5 bg-bg-base border border-border-hairline rounded">
            {cases.length}
          </span>
        </div>

        {/* Metric 2 */}
        <div className="flex items-center space-x-2">
          <span className="font-mono text-[10px] text-text-secondary uppercase tracking-wider">CAMPAIGNS:</span>
          <span className="font-mono text-sm font-semibold text-mod-network px-1.5 py-0.5 bg-bg-base border border-border-hairline rounded">
            {campaigns.length}
          </span>
        </div>

        {/* Metric 3 */}
        <div className="flex items-center space-x-2">
          <span className="font-mono text-[10px] text-text-secondary uppercase tracking-wider">TOP_PRIORITY:</span>
          <span className="font-mono text-sm font-semibold text-sev-critical px-1.5 py-0.5 bg-bg-base border border-border-hairline rounded flex items-center space-x-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-sev-critical animate-pulse"></span>
            <span>{topDistrict.toUpperCase()}</span>
            {topScore > 0 && <span className="text-[10px] text-text-secondary">({topScore})</span>}
          </span>
        </div>
      </div>

      {/* Timestamp */}
      <div className="hidden md:flex items-center space-x-2 font-mono text-[10px] text-text-secondary">
        <span className="h-2 w-2 rounded-full bg-sev-verified"></span>
        <span>SECURE_CONN_ESTABLISHED</span>
      </div>
    </div>
  );
}
