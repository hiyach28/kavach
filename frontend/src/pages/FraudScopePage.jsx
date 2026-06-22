import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import ClassifierInput from '../components/fraudscope/ClassifierInput';
import ResultCard from '../components/fraudscope/ResultCard';
import EvidenceTrace from '../components/fraudscope/EvidenceTrace';

export default function FraudScopePage() {
  const { classifyCase, activeCase, cases, selectCase } = useCase();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const handleClassify = async (text) => {
    setLoading(true);
    setError(null);
    setHasSubmitted(true);
    try {
      await classifyCase(text);
    } catch (err) {
      setError(err.message || 'Classification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Load full case detail from API when clicking a case in the log
  const handleCaseSelect = async (c) => {
    try {
      const res = await fetch(`/api/cases/${c.id}`);
      const json = await res.json();
      if (json.success && json.data) {
        selectCase({ ...c, ...json.data, id: c.id });
        setHasSubmitted(true);
      } else {
        selectCase(c);
      }
    } catch {
      selectCase(c);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'confirmed':        return <span className="text-[8px] font-mono font-bold text-sev-critical border border-sev-critical/30 bg-sev-critical/10 px-1.5 py-0.5 rounded">CONFIRMED</span>;
      case 'false_positive':   return <span className="text-[8px] font-mono font-bold text-sev-verified border border-sev-verified/30 bg-sev-verified/10 px-1.5 py-0.5 rounded">CLEARED</span>;
      case 'needs_manual_review': return <span className="text-[8px] font-mono font-bold text-sev-high border border-sev-high/30 bg-sev-high/10 px-1.5 py-0.5 rounded">PENDING</span>;
      default:                 return <span className="text-[8px] font-mono font-bold text-accent-signal border border-accent-signal/30 bg-accent-signal/10 px-1.5 py-0.5 rounded">CLASSIFIED</span>;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-bg-base">

      {/* Page Header */}
      <div className="flex items-start justify-between border-b border-border-hairline pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest bg-bg-surface border border-border-hairline px-2 py-0.5 rounded">
              MODULE 01
            </span>
            <span className="font-mono text-[9px] text-sev-verified">● ONLINE</span>
          </div>
          <h2 className="font-condensed text-2xl font-bold tracking-wider text-text-primary uppercase">
            FraudScope
          </h2>
          <p className="text-xs text-text-secondary mt-1 max-w-lg">
            Submit a complaint transcript, SMS, WhatsApp message, or screenshot — the system will classify the cybercrime type, extract evidence indicators, and cluster it into known fraud campaigns.
          </p>
        </div>
        <div className="hidden md:flex flex-col items-end gap-1 font-mono text-[9px] text-text-secondary">
          <span>TOTAL CASES: <span className="text-text-primary font-bold">{cases.length}</span></span>
          <span>ENGINE: <span className="text-accent-signal">GEMINI v1.0</span></span>
        </div>
      </div>

      {/* How it works — only shown before first submission */}
      {!hasSubmitted && !activeCase && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { step: '01', title: 'Submit Evidence', desc: 'Paste a complaint transcript or upload a WhatsApp / SMS screenshot.' },
            { step: '02', title: 'Auto-Classification', desc: 'The system scrubs PII, then classifies fraud type and computes a risk score.' },
            { step: '03', title: 'Campaign Clustering', desc: 'Cases sharing infrastructure (UPI handles, phone numbers) are linked into ring campaigns.' },
          ].map(item => (
            <div key={item.step} className="flex gap-3 p-4 bg-bg-surface border border-border-hairline rounded">
              <div>
                <div className="font-mono text-[9px] text-text-secondary mb-0.5">STEP {item.step}</div>
                <div className="font-condensed font-bold text-sm text-text-primary mb-1">{item.title}</div>
                <p className="text-[11px] text-text-secondary leading-snug">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="border border-sev-critical/40 bg-sev-critical/10 text-sev-critical p-4 rounded font-mono text-xs flex items-start gap-2">
          <span className="font-bold flex-shrink-0">[FAIL]</span>
          <span>{error}</span>
        </div>
      )}

      {/* Input Panel */}
      <ClassifierInput onSubmit={handleClassify} isLoading={loading} />

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="h-40 bg-bg-surface border border-border-hairline rounded" />
          <div className="h-24 bg-bg-surface border border-border-hairline rounded" />
        </div>
      )}

      {/* Results */}
      {!loading && activeCase && (
        <div className="space-y-4" style={{ animation: 'fadeInUp 0.35s ease both' }}>
          <ResultCard caseData={activeCase} />
          {activeCase.raw_text_deidentified && (
            <EvidenceTrace
              rawText={activeCase.raw_text_deidentified}
              redFlags={activeCase.red_flags}
            />
          )}
        </div>
      )}

      {/* Indexed Case Log */}
      {cases.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between border-b border-border-hairline pb-2">
            <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">Indexed Case Log</span>
            <span className="font-mono text-[9px] text-text-secondary">{cases.length} records</span>
          </div>
          <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
            {[...cases]
              .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
              .map((c) => {
                const isActive = activeCase && activeCase.id === c.id;
                const riskColor = (c.risk_score || 0) >= 80
                  ? 'text-sev-critical border-sev-critical/30 bg-sev-critical/10'
                  : (c.risk_score || 0) >= 60
                  ? 'text-sev-high border-sev-high/30 bg-sev-high/10'
                  : 'text-sev-verified border-sev-verified/30 bg-sev-verified/10';

                return (
                  <button
                    key={c.id}
                    onClick={() => handleCaseSelect(c)}
                    className={`w-full text-left px-3 py-2 rounded border font-mono text-[10px] flex items-center justify-between gap-4 transition-colors ${
                      isActive ? 'bg-bg-surface border-accent-signal' : 'bg-bg-surface/40 border-border-hairline hover:border-text-secondary'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-text-secondary shrink-0">#{c.id}</span>
                      <span className="text-text-primary truncate uppercase">{(c.fraud_type || 'unclassified').replace(/_/g, ' ')}</span>
                      {c.district && <span className="text-text-secondary shrink-0 hidden sm:inline">{c.district}</span>}
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {getStatusBadge(c.status)}
                      {c.risk_score != null && (
                        <span className={`px-1.5 py-0.5 rounded border text-[9px] ${riskColor}`}>R{c.risk_score}</span>
                      )}
                      <span className="text-text-secondary text-[9px]">
                        {c.created_at ? new Date(c.created_at).toLocaleDateString('en-IN') : '—'}
                      </span>
                    </div>
                  </button>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
