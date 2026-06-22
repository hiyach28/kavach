import React from 'react';

export default function DistrictTooltip({ x, y, data }) {
  if (!data) return null;

  return (
    <div
      className="absolute z-50 pointer-events-none bg-bg-surface border border-border-hairline rounded shadow-lg p-3 min-w-[180px]"
      style={{ left: x, top: y }}
    >
      <div className="font-sans text-sm font-bold text-text-primary mb-1.5">{data.name}</div>
      <div className="font-mono text-[9px] text-text-secondary mb-2">{data.state}</div>
      <div className="space-y-1">
        <div className="flex justify-between font-mono text-[10px]">
          <span className="text-text-secondary">COMPLAINTS</span>
          <span className="text-text-primary font-semibold">{data.complaint_count || 0}</span>
        </div>
        <div className="flex justify-between font-mono text-[10px]">
          <span className="text-text-secondary">EST. LOSS</span>
          <span className="text-sev-critical font-semibold">
            ₹{((data.estimated_loss || 0) / 10000000).toFixed(1)}Cr
          </span>
        </div>
        <div className="flex justify-between font-mono text-[10px]">
          <span className="text-text-secondary">PRIORITY</span>
          <span className={`font-semibold ${
            (data.priority_score || 0) >= 70 ? 'text-sev-critical' :
            (data.priority_score || 0) >= 40 ? 'text-sev-high' :
            'text-sev-verified'
          }`}>
            {data.priority_score || 0}
          </span>
        </div>
        {data.campaigns_count > 0 && (
          <div className="flex justify-between font-mono text-[10px]">
            <span className="text-text-secondary">CAMPAIGNS</span>
            <span className="text-mod-network font-semibold">{data.campaigns_count}</span>
          </div>
        )}
      </div>
    </div>
  );
}
