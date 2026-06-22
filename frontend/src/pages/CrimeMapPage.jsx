import React from 'react';
import { useCase } from '../context/CaseContext';
import Choropleth from '../components/crimemap/Choropleth';

export default function CrimeMapPage() {
  const { districts, activeDistrict, selectDistrict } = useCase();

  return (
    <div className="flex-1 flex flex-col h-full bg-bg-base overflow-hidden">
      {/* Title Header */}
      <div className="p-6 border-b border-border-hairline bg-bg-surface flex items-center justify-between flex-shrink-0">
        <div className="flex flex-col">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest font-bold">MODULE_03</span>
          <h2 className="font-condensed text-xl font-bold tracking-wider text-text-primary uppercase mt-0.5">CRIMEMAP // PRIORITY DISTRICT CHOROPLETH</h2>
        </div>
        <div className="flex items-center space-x-2 font-mono text-[9px] text-text-secondary">
          <span>DISTRICTS_INDEXED:</span>
          <span className="text-mod-enforce font-semibold">{districts.length}</span>
        </div>
      </div>

      {/* Map + District Panel */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0 relative">
        {/* Left: Choropleth Map */}
        <div className="flex-1 min-h-0 h-full relative border-r border-border-hairline">
          <Choropleth />
        </div>

        {/* Right: District List */}
        <div className="w-full lg:w-72 flex-shrink-0 bg-bg-surface/30 border-t lg:border-t-0 border-border-hairline p-4 overflow-y-auto flex flex-col space-y-3">
          <div className="flex flex-col space-y-1 flex-shrink-0">
            <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">PRIORITY_DISTRICTS</span>
            <p className="text-[10px] text-text-secondary leading-snug">
              Ranked by complaint volume, financial impact, and campaign density.
            </p>
          </div>

          <div className="flex flex-col gap-2">
            {[...districts]
              .sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0))
              .map((district) => {
                const isActive = activeDistrict && activeDistrict.name === district.name;
                return (
                  <button
                    key={district.name}
                    onClick={() => selectDistrict(district.name)}
                    className={`w-full text-left p-3 rounded border transition-all duration-200 ${
                      isActive
                        ? 'bg-bg-base border-accent-signal'
                        : 'bg-bg-base/30 border-border-hairline hover:border-text-secondary'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-condensed text-sm font-semibold text-text-primary">{district.name}</span>
                      <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded border ${
                        (district.priority_score || 0) >= 70
                          ? 'text-sev-critical border-sev-critical/30 bg-sev-critical/10'
                          : (district.priority_score || 0) >= 40
                          ? 'text-sev-high border-sev-high/30 bg-sev-high/10'
                          : 'text-sev-verified border-sev-verified/30 bg-sev-verified/10'
                      }`}>
                        P{district.priority_score || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between font-mono text-[9px] text-text-secondary">
                      <span>{district.complaint_count} complaints</span>
                      <span>₹{((district.estimated_loss || 0) / 10000000).toFixed(1)}Cr</span>
                    </div>
                    {district.campaigns_count > 0 && (
                      <div className="mt-1 font-mono text-[9px] text-mod-network">
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
