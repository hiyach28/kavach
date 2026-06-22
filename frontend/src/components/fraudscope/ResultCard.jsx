import React from 'react';

const FRAUD_TYPE_META = {
  digital_arrest: {
    label: 'Digital Arrest',
    icon: '🚨',
    description: 'Impersonation of law enforcement to coerce victims into camera surveillance and financial transfer.',
    color: 'text-sev-critical',
  },
  upi_spoofing: {
    label: 'UPI Spoofing',
    icon: '💳',
    description: 'Fake UPI payment confirmations or reverse-request scams using spoofed merchant interfaces.',
    color: 'text-sev-high',
  },
  investment_fraud: {
    label: 'Investment Fraud',
    icon: '📈',
    description: 'Fake trading platforms, crypto pumps, or task-based schemes funneling money into mule accounts.',
    color: 'text-sev-critical',
  },
  otp_sim_swap: {
    label: 'OTP / SIM Swap',
    icon: '📱',
    description: 'Phishing for OTP codes or SIM swap attacks to take over banking and UPI accounts.',
    color: 'text-sev-high',
  },
  needs_manual_review: {
    label: 'Manual Review Required',
    icon: '⚠️',
    description: 'Insufficient signals for automated classification. Routed for analyst review.',
    color: 'text-sev-high',
  },
  legitimate: {
    label: 'Legitimate — No Fraud Detected',
    icon: '✅',
    description: 'No known fraud indicators detected in this submission.',
    color: 'text-sev-verified',
  },
};

const getRiskStyle = (score) => {
  if (score === null || score === undefined) return { ring: 'border-sev-high text-sev-high bg-sev-high/10', bar: 'bg-sev-high', label: 'REVIEW' };
  if (score >= 70) return { ring: 'border-sev-critical text-sev-critical bg-sev-critical/10', bar: 'bg-sev-critical', label: 'CRITICAL' };
  if (score >= 40) return { ring: 'border-sev-high text-sev-high bg-sev-high/10', bar: 'bg-sev-high', label: 'HIGH' };
  return { ring: 'border-sev-verified text-sev-verified bg-sev-verified/10', bar: 'bg-sev-verified', label: 'LOW' };
};

const getSeverityDot = (category) => {
  const classes = {
    critical: 'bg-sev-critical',
    high: 'bg-sev-high',
  };
  return <span className={`h-2 w-2 rounded-full flex-shrink-0 ${classes[category] || 'bg-mod-network'}`} />;
};

export default function ResultCard({ caseData }) {
  if (!caseData) return null;

  const { fraud_type, risk_score, confidence, verdict, red_flags, reporting_portal, district, campaign_id, infra } = caseData;
  const meta = FRAUD_TYPE_META[fraud_type] || { label: fraud_type?.replace(/_/g, ' ').toUpperCase(), icon: '🔎', color: 'text-text-primary' };
  const riskStyle = getRiskStyle(risk_score);

  return (
    <div className="border border-border-hairline rounded bg-bg-surface overflow-hidden">
      {/* ── Card Header ── */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border-hairline bg-bg-base/30">
        <div className="flex items-center gap-2">
          <span className="text-lg">{meta.icon}</span>
          <div>
            <span className="font-mono text-[13px] text-text-secondary uppercase tracking-widest block">CLASSIFICATION VERDICT</span>
            <h3 className={`font-sans text-sm font-bold tracking-wider ${meta.color}`}>{meta.label}</h3>
          </div>
        </div>
        {reporting_portal && (
          <a
            href={reporting_portal}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 font-sans font-bold text-xs tracking-wider bg-accent-signal/20 hover:bg-accent-signal/30 text-accent-signal border border-accent-signal/40 rounded transition-all duration-200 hover:scale-[1.02] whitespace-nowrap"
          >
            Report to Govt Portal →
          </a>
        )}
      </div>

      <div className="p-5 space-y-5">
        {/* ── Risk Score + Verdict ── */}
        <div className="flex gap-5 items-start bg-bg-base/40 p-4 rounded border border-border-hairline">
          {/* Ring */}
          <div className="flex flex-col items-center gap-1.5 flex-shrink-0">
            {risk_score !== null && risk_score !== undefined ? (
              <>
                <div className={`h-20 w-20 rounded-full border-4 flex flex-col items-center justify-center ${riskStyle.ring}`}>
                  <span className="font-mono text-xs text-text-secondary uppercase tracking-tight">RISK</span>
                  <span className="font-mono text-2xl font-bold leading-none">{risk_score}</span>
                  <span className="font-mono text-xs tracking-widest">{riskStyle.label}</span>
                </div>
                {/* Confidence bar */}
                <div className="w-20 space-y-1">
                  <div className="flex justify-between font-mono text-xs text-text-secondary">
                    <span>CONF.</span>
                    <span>{(confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1 bg-bg-base border border-border-hairline rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-500 ${riskStyle.bar}`} style={{ width: `${confidence * 100}%` }} />
                  </div>
                </div>
              </>
            ) : (
              <div className="h-20 w-20 rounded-full border-2 border-dashed border-sev-high bg-sev-high/10 text-sev-high flex flex-col items-center justify-center flex-shrink-0">
                <span className="font-mono text-[13px] font-bold text-center leading-tight">MANUAL{'\n'}REVIEW</span>
              </div>
            )}
          </div>

          {/* Verdict + Meta */}
          <div className="flex-1 min-w-0 space-y-2">
            <p className="text-sm text-text-primary leading-relaxed">{verdict}</p>
            <p className="text-[13px] text-text-secondary italic leading-snug">{meta.description}</p>
            <div className="flex flex-wrap gap-2 pt-1">
              {district && (
                <span className="font-mono text-[13px] px-2 py-0.5 bg-bg-base border border-border-hairline rounded text-text-secondary">
                  📍 {district}
                </span>
              )}
              {campaign_id && (
                <span className="font-mono text-[13px] px-2 py-0.5 bg-mod-network/10 border border-mod-network/20 rounded text-mod-network">
                  🔗 Campaign #{campaign_id}
                </span>
              )}
              {infra && infra.length > 0 && (
                <span className="font-mono text-[13px] px-2 py-0.5 bg-sev-critical/10 border border-sev-critical/20 rounded text-sev-critical">
                  ⚡ {infra.length} infra node{infra.length > 1 ? 's' : ''}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* ── Red Flags ── */}
        {red_flags && red_flags.length > 0 && (
          <div className="space-y-2">
            <span className="font-sans text-xs font-bold tracking-widest text-text-secondary uppercase block">
              ⚑ Scam Indicator Flags ({red_flags.length})
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {red_flags.map((flag, idx) => (
                <div key={idx} className="p-3 bg-bg-base/30 border border-border-hairline rounded space-y-2">
                  <div className="flex items-center gap-2">
                    {getSeverityDot(flag.category)}
                    <span className="font-mono text-xs text-text-primary font-bold">{flag.flag_id}</span>
                    <span className={`font-mono text-xs uppercase px-1 rounded ${flag.category === 'critical' ? 'text-sev-critical bg-sev-critical/10' :
                        flag.category === 'high' ? 'text-sev-high bg-sev-high/10' :
                          'text-mod-network bg-mod-network/10'
                      }`}>
                      {flag.category}
                    </span>
                  </div>
                  <div className="font-mono text-xs text-accent-signal bg-bg-base/60 px-2 py-1 rounded border border-border-hairline italic truncate">
                    "{flag.evidence}"
                  </div>
                  <p className="text-[13px] text-text-secondary leading-snug">{flag.explanation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── No Flags State ── */}
        {(!red_flags || red_flags.length === 0) && (
          <div className="p-4 border border-dashed border-sev-verified/40 bg-sev-verified/5 rounded text-center">
            <span className="text-sev-verified font-mono text-xs">✓ No fraud indicator flags triggered</span>
          </div>
        )}
      </div>
    </div>
  );
}
