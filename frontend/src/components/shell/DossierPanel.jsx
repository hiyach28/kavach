import React, { useState, useEffect } from 'react';
import { useCase } from '../../context/CaseContext';
import { apiClient } from '../../api/client';

export default function DossierPanel() {
  const { activeCase, submitFeedback } = useCase();
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [showInput, setShowInput] = useState(false);

  useEffect(() => {
    setAuditLogs([]);
    setShowInput(false);
    if (!activeCase?.audit_id) return;
    setLoadingLogs(true);
    apiClient.getAuditLogs(activeCase.audit_id)
      .then(logs => setAuditLogs(Array.isArray(logs) ? logs : []))
      .catch(() => setAuditLogs([]))
      .finally(() => setLoadingLogs(false));
  }, [activeCase?.audit_id]);

  if (!activeCase) {
    return (
      <div className="w-80 bg-bg-surface border-l border-border-hairline h-full flex flex-col items-center justify-center p-6 text-center select-none">
        <span className="font-mono text-[10px] text-text-secondary uppercase tracking-widest mb-2 font-bold animate-pulse">NO_ACTIVE_DOSSIER</span>
        <p className="text-xs text-text-secondary">
          Submit a case in FraudScope or select a node in NetworkX to view active investigator files.
        </p>
      </div>
    );
  }

  const getRiskColor = (score) => {
    if (score === null || score === undefined) return 'text-text-secondary border-text-secondary bg-text-secondary/10';
    if (score >= 70) return 'text-sev-critical border-sev-critical bg-sev-critical/10';
    if (score >= 40) return 'text-sev-high border-sev-high bg-sev-high/10';
    return 'text-sev-verified border-sev-verified bg-sev-verified/10';
  };

  const getSeverityBadge = (category) => {
    switch (category) {
      case 'critical': return <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-sev-critical/20 text-sev-critical border border-sev-critical/30">CRITICAL</span>;
      case 'high': return <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-sev-high/20 text-sev-high border border-sev-high/30">HIGH</span>;
      default: return <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-mod-network/20 text-mod-network border border-mod-network/30">MEDIUM</span>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'confirmed': return <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-sev-critical/20 text-sev-critical border border-sev-critical/30 uppercase rounded-full">CONFIRMED</span>;
      case 'false_positive': return <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-sev-verified/20 text-sev-verified border border-sev-verified/30 uppercase rounded-full">CLEARED</span>;
      case 'needs_manual_review': return <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-sev-high/20 text-sev-high border border-sev-high/30 uppercase rounded-full">PENDING</span>;
      default: return <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-accent-signal/20 text-accent-signal border border-accent-signal/30 uppercase rounded-full">CLASSIFIED</span>;
    }
  };

  const fraudType = activeCase.fraud_type ? activeCase.fraud_type.replace(/_/g, ' ') : 'UNCLASSIFIED';
  const confidence = activeCase.confidence != null ? (activeCase.confidence * 100).toFixed(0) : 'N/A';

  return (
    <div className="w-96 bg-bg-surface border-l border-border-hairline h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border-hairline bg-bg-base/30 flex items-center justify-between flex-shrink-0">
        <div className="flex flex-col">
          <span className="font-condensed text-xs font-bold text-accent-signal tracking-widest">DOSSIER_FILE</span>
          <span className="font-mono text-sm font-semibold tracking-wider">CASE #{activeCase.id || '—'}</span>
        </div>
        {getStatusBadge(activeCase.status)}
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">

        {/* Core Metadata */}
        <div className="bg-bg-base/30 p-3 rounded border border-border-hairline font-mono text-[10px] text-text-secondary space-y-1.5">
          <div><span className="text-text-primary">AUDIT_ID:</span> {activeCase.audit_id || '—'}</div>
          <div><span className="text-text-primary">CLASSIFIED_AT:</span> {activeCase.created_at ? new Date(activeCase.created_at).toLocaleString() : '—'}</div>
          <div><span className="text-text-primary">LOC_DISTRICT:</span> {activeCase.district || 'UNKNOWN'}</div>
          {activeCase.campaign_id && (
            <div><span className="text-text-primary">CLUSTER_GROUP:</span> <span className="text-mod-network">Campaign #{activeCase.campaign_id}</span></div>
          )}
        </div>

        {/* INPUT TEXT — collapsible */}
        {activeCase.raw_text_deidentified && (
          <div className="space-y-1.5">
            <button
              onClick={() => setShowInput(v => !v)}
              className="w-full flex items-center justify-between font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase hover:text-text-primary transition-colors"
            >
              <span>INPUT_TRANSCRIPT</span>
              <span className="font-mono text-[10px]">{showInput ? '▲ HIDE' : '▼ SHOW'}</span>
            </button>
            {showInput && (
              <div className="bg-bg-base border border-border-hairline rounded p-3 font-mono text-[10px] text-text-secondary leading-relaxed select-text whitespace-pre-wrap max-h-48 overflow-y-auto">
                {activeCase.raw_text_deidentified}
              </div>
            )}
          </div>
        )}

        {/* Verdict + Risk Score */}
        <div className="flex items-center space-x-4 bg-bg-base/20 p-3 rounded border border-border-hairline">
          {activeCase.risk_score !== null && activeCase.risk_score !== undefined ? (
            <div className={`h-16 w-16 rounded-full border-2 flex flex-col items-center justify-center flex-shrink-0 ${getRiskColor(activeCase.risk_score)}`}>
              <span className="font-mono text-xs text-text-secondary font-medium tracking-tighter leading-none">RISK</span>
              <span className="font-mono text-lg font-bold leading-none mt-0.5">{activeCase.risk_score}</span>
            </div>
          ) : (
            <div className="h-16 w-16 rounded-full border border-dashed border-sev-high bg-sev-high/10 text-sev-high flex flex-col items-center justify-center flex-shrink-0">
              <span className="font-mono text-[10px] text-center leading-tight font-bold">MANUAL<br/>REVIEW</span>
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="font-mono text-[9px] text-text-secondary uppercase">LLM_CONFIDENCE: {confidence}%</div>
            <h4 className="font-condensed text-xs font-bold text-text-primary uppercase tracking-wider mt-0.5">{fraudType}</h4>
            {activeCase.verdict && (
              <p className="text-xs text-text-primary leading-snug mt-1 italic">{activeCase.verdict}</p>
            )}
          </div>
        </div>

        {/* Red Flags */}
        <div className="space-y-2">
          <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">
            EVIDENCE_RED_FLAGS ({activeCase.red_flags?.length || 0})
          </span>
          {activeCase.red_flags && activeCase.red_flags.length > 0 ? (
            <div className="space-y-2">
              {activeCase.red_flags.map((flag, idx) => (
                <div key={idx} className="p-3 bg-bg-base/30 rounded border border-border-hairline space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-text-primary font-bold">{flag.flag_id}</span>
                    {getSeverityBadge(flag.category)}
                  </div>
                  <div className="font-mono text-[10px] text-text-primary bg-bg-base px-2 py-1 border border-border-hairline rounded leading-relaxed select-text italic">
                    "{flag.evidence}"
                  </div>
                  <p className="text-[11px] text-text-secondary leading-snug">{flag.explanation}</p>
                  {flag.mha_ncrb_citation && (
                    <div className="font-mono text-[9px] text-mod-network border-t border-border-hairline pt-1">
                      REF: {flag.mha_ncrb_citation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 text-center border border-dashed border-border-hairline text-text-secondary text-xs rounded">
              No red flags — seeded case (run FraudScope to generate LLM evidence).
            </div>
          )}
        </div>

        {/* Reporting Portal */}
        {activeCase.reporting_portal && (
          <div className="space-y-1.5">
            <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">REPORTING_PORTAL</span>
            <a
              href={activeCase.reporting_portal}
              target="_blank"
              rel="noreferrer"
              className="block font-mono text-[10px] text-accent-signal underline underline-offset-2 hover:text-text-primary transition-colors"
            >
              {activeCase.reporting_portal}
            </a>
          </div>
        )}

        {/* Audit Log */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">AUDIT_LOG</span>
            {loadingLogs && <span className="font-mono text-[8px] text-text-secondary uppercase animate-pulse">FETCHING...</span>}
          </div>
          {auditLogs.length > 0 ? (
            <div className="border border-border-hairline rounded overflow-hidden">
              <table className="w-full font-mono text-[9px] text-left">
                <thead className="bg-bg-base/50 text-text-secondary border-b border-border-hairline">
                  <tr><th className="p-2">EVENT</th><th className="p-2">TIME</th></tr>
                </thead>
                <tbody className="divide-y divide-border-hairline bg-bg-base/20">
                  {auditLogs.map((log, i) => (
                    <tr key={i} className="hover:bg-bg-base/40">
                      <td className={`p-2 font-bold ${log.event?.includes('success') ? 'text-sev-verified' : log.event?.includes('fail') ? 'text-sev-critical' : 'text-accent-signal'}`}>
                        {log.event?.replace('classify_', '').toUpperCase()}
                      </td>
                      <td className="p-2 text-text-secondary">{log.created_at ? new Date(log.created_at).toLocaleTimeString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-2 text-center text-text-secondary text-[10px] font-mono border border-border-hairline rounded bg-bg-base/10">
              {loadingLogs ? 'LOADING...' : 'NO_AUDIT_RECORDS (seeded case)'}
            </div>
          )}
        </div>
      </div>

      {/* Investigator Actions */}
      <div className="p-4 border-t border-border-hairline bg-bg-base/50 space-y-3 flex-shrink-0">
        <span className="font-mono text-[10px] text-text-secondary uppercase tracking-wider block font-semibold text-center">INVESTIGATOR_DECISION</span>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => submitFeedback(activeCase.id, 'confirmed')}
            disabled={activeCase.status === 'confirmed'}
            className={`py-2 px-3 rounded font-condensed font-bold text-xs tracking-wider border transition-all duration-200 ${
              activeCase.status === 'confirmed'
                ? 'bg-sev-critical/10 text-sev-critical/60 border-sev-critical/30 cursor-not-allowed'
                : 'bg-sev-critical/20 hover:bg-sev-critical/30 text-sev-critical border-sev-critical/40'
            }`}
          >
            CONFIRM SCAM
          </button>
          <button
            onClick={() => submitFeedback(activeCase.id, 'false_positive')}
            disabled={activeCase.status === 'false_positive'}
            className={`py-2 px-3 rounded font-condensed font-bold text-xs tracking-wider border transition-all duration-200 ${
              activeCase.status === 'false_positive'
                ? 'bg-sev-verified/10 text-sev-verified/60 border-sev-verified/30 cursor-not-allowed'
                : 'bg-sev-verified/20 hover:bg-sev-verified/30 text-sev-verified border-sev-verified/40'
            }`}
          >
            FALSE POSITIVE
          </button>
        </div>
      </div>
    </div>
  );
}
