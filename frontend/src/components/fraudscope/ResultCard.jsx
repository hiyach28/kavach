import React from 'react';

export default function ResultCard({ caseData }) {
  if (!caseData) return null;

  const { fraud_type, risk_score, confidence, verdict, red_flags, reporting_portal } = caseData;

  const getRiskColor = (score) => {
    if (score === null || score === undefined) return 'text-text-secondary border-text-secondary bg-text-secondary/10';
    if (score >= 70) return 'text-sev-critical border-sev-critical bg-sev-critical/10';
    if (score >= 40) return 'text-sev-high border-sev-high bg-sev-high/10';
    return 'text-sev-verified border-sev-verified bg-sev-verified/10';
  };

  const getSeverityDot = (category) => {
    switch (category) {
      case 'critical':
        return <span className="h-2 w-2 rounded-full bg-sev-critical flex-shrink-0"></span>;
      case 'high':
        return <span className="h-2 w-2 rounded-full bg-sev-high flex-shrink-0"></span>;
      default:
        return <span className="h-2 w-2 rounded-full bg-mod-network flex-shrink-0"></span>;
    }
  };

  const getFraudTypeLabel = (type) => {
    return type.replace(/_/g, ' ').toUpperCase();
  };

  return (
    <div className="border border-border-hairline rounded bg-bg-surface p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-hairline pb-3">
        <div className="flex flex-col">
          <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">CLASSIFICATION_VERDICT</span>
          <h3 className="font-mono text-sm font-semibold mt-0.5">{getFraudTypeLabel(fraud_type)}</h3>
        </div>
        {reporting_portal && (
          <a
            href={reporting_portal}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1 font-condensed font-bold text-[10px] tracking-wider bg-accent-signal/20 hover:bg-accent-signal/30 text-accent-signal border border-accent-signal/40 rounded transition-all duration-200"
          >
            REPORT TO GOVT PORTAL &rarr;
          </a>
        )}
      </div>

      {/* Score and Verdict Summary Layout */}
      <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-6 bg-bg-base/30 p-4 rounded border border-border-hairline">
        {risk_score !== null ? (
          <div className="flex flex-col items-center">
            {/* Risk Ring */}
            <div className={`h-20 w-20 rounded-full border-4 flex flex-col items-center justify-center relative ${getRiskColor(risk_score)}`}>
              <span className="font-mono text-[9px] text-text-secondary uppercase tracking-tight">RISK</span>
              <span className="font-mono text-xl font-bold leading-none">{risk_score}</span>
            </div>
            <span className="font-mono text-[8px] text-text-secondary uppercase mt-1.5">Confidence: {(confidence * 100).toFixed(0)}%</span>
          </div>
        ) : (
          <div className="h-20 w-20 rounded-full border-2 border-dashed border-sev-high bg-sev-high/10 text-sev-high flex flex-col items-center justify-center flex-shrink-0">
            <span className="font-mono text-[9px] font-bold tracking-tight text-center leading-tight">MANUAL<br/>REVIEW</span>
          </div>
        )}

        <div className="flex-1 text-center sm:text-left space-y-1.5">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-wider block">ANALYST_SUMMARY_VERDICT</span>
          <p className="text-sm font-medium text-text-primary leading-relaxed">{verdict}</p>
        </div>
      </div>

      {/* Red Flags Quick-List */}
      <div className="space-y-3">
        <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase block">SCAM_INDICATOR_FLAGS</span>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {red_flags && red_flags.length > 0 ? (
            red_flags.map((flag, idx) => (
              <div key={idx} className="p-3 bg-bg-base/20 border border-border-hairline rounded flex flex-col justify-between space-y-2">
                <div className="flex items-center space-x-2">
                  {getSeverityDot(flag.category)}
                  <span className="font-mono text-[10px] text-text-primary font-bold">{flag.flag_id}</span>
                  <span className="font-mono text-[8px] text-text-secondary uppercase">({flag.category})</span>
                </div>
                <div className="font-mono text-[10px] text-text-primary bg-bg-base/50 px-2 py-1 rounded border border-border-hairline truncate italic select-text">
                  "{flag.evidence}"
                </div>
                <p className="text-[11px] text-text-secondary leading-snug">
                  {flag.explanation}
                </p>
              </div>
            ))
          ) : (
            <div className="col-span-2 p-3 text-center border border-dashed border-border-hairline text-text-secondary text-xs rounded font-mono">
              NO_ALERT_FLAGS_TRIGGERED
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
