import React from 'react';
import { useCase } from '../context/CaseContext';
import Choropleth from '../components/crimemap/Choropleth';

// India flag as inline SVG (guaranteed visible, no external dependency)
function IndiaFlag({ size = 32 }) {
  return (
    <svg width={size * 1.5} height={size} viewBox="0 0 90 60" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0, borderRadius: 2 }}>
      {/* Saffron */}
      <rect width="90" height="20" fill="#FF9933" />
      {/* White */}
      <rect y="20" width="90" height="20" fill="#FFFFFF" />
      {/* Green */}
      <rect y="40" width="90" height="20" fill="#138808" />
      {/* Ashoka Chakra (Navy Blue) */}
      <circle cx="45" cy="30" r="8" fill="none" stroke="#000080" strokeWidth="1.2" />
      {/* 24 spokes — simplified */}
      {Array.from({ length: 24 }).map((_, i) => {
        const angle  = (i / 24) * Math.PI * 2;
        const x1 = 45 + 4 * Math.cos(angle);
        const y1 = 30 + 4 * Math.sin(angle);
        const x2 = 45 + 8 * Math.cos(angle);
        const y2 = 30 + 8 * Math.sin(angle);
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#000080" strokeWidth="0.6" />;
      })}
      <circle cx="45" cy="30" r="1.5" fill="#000080" />
    </svg>
  );
}

export default function CrimeMapPage() {
  const { districts, activeDistrict, selectDistrict } = useCase();

  // Sort districts by priority score for the threat list
  const sortedDistricts = [...districts].sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0));

  return (
    <div className="flex-1 flex flex-col h-full bg-bg-base overflow-hidden">

      {/* ── Title Header ── */}
      <div className="p-5 border-b border-border-hairline bg-bg-surface flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <IndiaFlag size={28} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest">MODULE_03</span>
              <span className="font-mono text-[9px] text-sev-verified">● LIVE</span>
            </div>
            <h2 className="text-base font-bold tracking-wide text-text-primary">
              CrimeMap — Priority District Choropleth
            </h2>
          </div>
        </div>
        <div className="flex items-center gap-3 font-mono text-[9px] text-text-secondary">
          <span>DISTRICTS_INDEXED:</span>
          <span className="text-mod-enforce font-bold text-sm">{districts.length}</span>
        </div>
      </div>

      {/* ── Map + District Panel ── */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0 relative">

        {/* Left: Choropleth Map */}
        <div className="flex-1 min-h-0 h-full relative border-r border-border-hairline">
          <Choropleth />
        </div>

        {/* Right: Cities with Most Threats List */}
        <div className="w-full lg:w-72 flex-shrink-0 bg-bg-surface/30 border-t lg:border-t-0 border-border-hairline flex flex-col overflow-hidden">

          {/* Section header */}
          <div className="px-4 pt-4 pb-3 border-b border-border-hairline flex-shrink-0">
            <div className="flex items-center gap-2 mb-1">
              <IndiaFlag size={16} />
              <span className="font-mono text-[9px] font-bold tracking-widest text-text-secondary uppercase">Cities with Most Threats</span>
            </div>
            <p className="text-[10px] text-text-secondary leading-snug">
              Ranked by complaint volume, financial impact, and campaign density.
            </p>
          </div>

          {/* Scrollable list */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {sortedDistricts.map((district, rank) => {
              const isActive = activeDistrict && activeDistrict.name === district.name;
              const priorityColor = (district.priority_score || 0) >= 70
                ? 'text-sev-critical border-sev-critical/30 bg-sev-critical/10'
                : (district.priority_score || 0) >= 40
                ? 'text-sev-high border-sev-high/30 bg-sev-high/10'
                : 'text-sev-verified border-sev-verified/30 bg-sev-verified/10';

              return (
                <button
                  key={district.name}
                  onClick={() => selectDistrict(district.name)}
                  className={`w-full text-left p-3 rounded-lg border transition-all duration-200 ${
                    isActive
                      ? 'bg-bg-base border-accent-signal'
                      : 'bg-bg-base/30 border-border-hairline hover:border-text-secondary'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="font-mono text-[9px] text-text-secondary flex-shrink-0">#{rank + 1}</span>
                      <span className="font-semibold text-sm text-text-primary truncate">{district.name}</span>
                    </div>
                    <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded border flex-shrink-0 ${priorityColor}`}>
                      P{district.priority_score || 0}
                    </span>
                  </div>
                  <div className="font-mono text-[9px] text-text-secondary mb-1.5">{district.state}</div>
                  <div className="flex items-center justify-between font-mono text-[9px] text-text-secondary">
                    <span>{district.complaint_count} complaints</span>
                    <span>₹{((district.estimated_loss || 0) / 10000000).toFixed(1)}Cr</span>
                  </div>
                  {/* Threat bar */}
                  <div className="mt-2 w-full bg-bg-base rounded-full h-1">
                    <div
                      className={`h-1 rounded-full ${
                        (district.priority_score || 0) >= 70 ? 'bg-sev-critical' :
                        (district.priority_score || 0) >= 40 ? 'bg-sev-high' : 'bg-sev-verified'
                      }`}
                      style={{ width: `${district.priority_score || 0}%` }}
                    />
                  </div>
                  {district.campaigns_count > 0 && (
                    <div className="mt-1.5 font-mono text-[9px] text-mod-network">
                      {district.campaigns_count} active campaign{district.campaigns_count > 1 ? 's' : ''}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
