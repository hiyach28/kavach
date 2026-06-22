import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import Choropleth from '../components/crimemap/Choropleth';

export default function CrimeMapPage() {
  const { districts, activeDistrict, selectDistrict, fetchDistricts, cases } = useCase();
  const [filterFraudType, setFilterFraudType] = useState('');
  const [expandedCaseId, setExpandedCaseId] = useState(null);

  const handleFilterChange = (e) => {
    const val = e.target.value;
    setFilterFraudType(val);
    fetchDistricts(val);
  };

  const exportBrief = () => {
    if (!activeDistrict) return;
    const districtCases = cases.filter(c => c.district && c.district.toLowerCase() === activeDistrict.name.toLowerCase());
    const briefContent = `
ENFORCEMENT BRIEF: ${activeDistrict.name}
-----------------------------------------
Priority Score: ${activeDistrict.priority_score || 0}
Complaint Count: ${activeDistrict.complaint_count}
Estimated Financial Loss: ₹${((activeDistrict.estimated_loss || 0) / 10000000).toFixed(1)}Cr
Indexed Cases: ${districtCases.length}

FRAUD TYPE BREAKDOWN:
${[...new Set(districtCases.map(c => c.fraud_type))].map(ft => `  - ${ft}: ${districtCases.filter(c => c.fraud_type === ft).length} cases`).join('\n')}

RECOMMENDED ACTION: 
Review top campaign nodes and initiate inter-state coordination if cross-jurisdictional infra is found.
    `.trim();
    const newWindow = window.open();
    newWindow.document.write(`<pre>${briefContent}</pre>`);
    newWindow.print();
  };

  // Cases for the selected district
  const districtCases = activeDistrict
    ? [...cases]
        .filter(c => c.district && c.district.toLowerCase() === activeDistrict.name.toLowerCase())
        .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
    : [];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'confirmed': return <span className="text-[8px] font-mono font-bold text-sev-critical border border-sev-critical/30 bg-sev-critical/10 px-1 rounded">CONFIRMED</span>;
      case 'false_positive': return <span className="text-[8px] font-mono font-bold text-sev-verified border border-sev-verified/30 bg-sev-verified/10 px-1 rounded">CLEARED</span>;
      case 'needs_manual_review': return <span className="text-[8px] font-mono font-bold text-sev-high border border-sev-high/30 bg-sev-high/10 px-1 rounded">PENDING</span>;
      default: return <span className="text-[8px] font-mono font-bold text-accent-signal border border-accent-signal/30 bg-accent-signal/10 px-1 rounded">CLASSIFIED</span>;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-bg-base overflow-hidden">
      {/* Title Header */}
      <div className="p-6 border-b border-border-hairline bg-bg-surface flex items-center justify-between flex-shrink-0">
        <div className="flex flex-col">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest font-bold">MODULE_03</span>
          <h2 className="font-condensed text-xl font-bold tracking-wider text-text-primary uppercase mt-0.5">CRIMEMAP // PRIORITY DISTRICT CHOROPLETH</h2>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={filterFraudType}
            onChange={handleFilterChange}
            className="bg-bg-base border border-border-hairline rounded px-2 py-1 text-xs font-mono text-text-primary"
          >
            <option value="">ALL FRAUD TYPES</option>
            <option value="digital_arrest">DIGITAL ARREST</option>
            <option value="investment_fraud">INVESTMENT FRAUD</option>
            <option value="otp_sim_swap">OTP SIM SWAP</option>
            <option value="courier_parcel">COURIER / PARCEL</option>
            <option value="job_loan_scam">JOB / LOAN SCAM</option>
          </select>
          <div className="flex items-center space-x-2 font-mono text-[9px] text-text-secondary">
            <span>DISTRICTS_INDEXED:</span>
            <span className="text-mod-enforce font-semibold">{districts.length}</span>
          </div>
        </div>
      </div>

      {/* Map + District Panel */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0 relative">
        {/* Left: Map */}
        <div className="flex-1 min-h-0 h-full relative border-r border-border-hairline">
          <Choropleth />
        </div>

        {/* Right Panel */}
        <div className="w-full lg:w-80 flex-shrink-0 bg-bg-surface/30 border-t lg:border-t-0 border-border-hairline flex flex-col overflow-hidden">

          {/* District List */}
          <div className="p-4 border-b border-border-hairline space-y-3 overflow-y-auto" style={{ maxHeight: activeDistrict ? '40%' : '100%' }}>
            <div className="flex flex-col space-y-1 flex-shrink-0">
              <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">PRIORITY_DISTRICTS</span>
              <p className="text-[10px] text-text-secondary leading-snug">Ranked by complaint volume, financial impact, and campaign density.</p>
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
                        isActive ? 'bg-bg-base border-accent-signal' : 'bg-bg-base/30 border-border-hairline hover:border-text-secondary'
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
                    </button>
                  );
                })}
            </div>
          </div>

          {/* District Case Details (shown when district selected) */}
          {activeDistrict && (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-3 border-b border-border-hairline bg-bg-base/40 flex items-center justify-between flex-shrink-0">
                <div>
                  <span className="font-condensed text-xs font-bold text-text-primary uppercase">{activeDistrict.name}</span>
                  <span className="font-mono text-[9px] text-text-secondary ml-2">{districtCases.length} indexed cases</span>
                </div>
                <button
                  onClick={exportBrief}
                  className="text-[9px] font-mono font-bold text-mod-enforce border border-mod-enforce/40 bg-mod-enforce/10 hover:bg-mod-enforce/20 px-2 py-0.5 rounded transition-colors"
                >
                  EXPORT
                </button>
              </div>

              {districtCases.length === 0 ? (
                <div className="p-4 text-center text-text-secondary text-[10px] font-mono">
                  No local indexed cases for {activeDistrict.name}.
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
                  {districtCases.map((c) => {
                    const isExpanded = expandedCaseId === c.id;
                    return (
                      <div key={c.id} className="border border-border-hairline rounded bg-bg-base/30 overflow-hidden">
                        <button
                          onClick={() => setExpandedCaseId(isExpanded ? null : c.id)}
                          className="w-full text-left px-3 py-2 flex items-center justify-between hover:bg-bg-base/50 transition-colors"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="font-mono text-[9px] text-text-secondary shrink-0">#{c.id}</span>
                            <span className="font-mono text-[10px] text-text-primary truncate uppercase">
                              {(c.fraud_type || 'unclassified').replace(/_/g, ' ')}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {getStatusBadge(c.status)}
                            {c.risk_score != null && (
                              <span className={`text-[9px] font-mono font-bold ${
                                c.risk_score >= 70 ? 'text-sev-critical' : c.risk_score >= 40 ? 'text-sev-high' : 'text-sev-verified'
                              }`}>R{c.risk_score}</span>
                            )}
                            <span className="text-text-secondary text-[10px]">{isExpanded ? '▲' : '▼'}</span>
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="px-3 pb-3 border-t border-border-hairline space-y-2 bg-bg-base/20">
                            {c.verdict && (
                              <p className="text-[10px] text-text-secondary italic mt-2 leading-snug">{c.verdict}</p>
                            )}
                            {c.raw_text_deidentified && (
                              <div className="font-mono text-[9px] text-text-secondary bg-bg-base border border-border-hairline rounded p-2 leading-relaxed max-h-28 overflow-y-auto whitespace-pre-wrap">
                                {c.raw_text_deidentified}
                              </div>
                            )}
                            {c.created_at && (
                              <div className="font-mono text-[9px] text-text-secondary">
                                Filed: {new Date(c.created_at).toLocaleDateString('en-IN')}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
