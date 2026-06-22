import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import ClassifierInput from '../components/fraudscope/ClassifierInput';
import ResultCard from '../components/fraudscope/ResultCard';
import EvidenceTrace from '../components/fraudscope/EvidenceTrace';

export default function FraudScopePage() {
  const { classifyCase, activeCase, cases } = useCase();
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
          <span>ENGINE: <span className="text-accent-signal">MOCK v1.0</span></span>
        </div>
      </div>

      {/* How it works — only shown when no submission yet */}
      {!hasSubmitted && !activeCase && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            {
              step: '01',
              icon: '',
              title: 'Submit Evidence',
              desc: 'Paste a complaint transcript or upload a WhatsApp / SMS screenshot.',
            },
            {
              step: '02',
              icon: '',
              title: 'Auto-Classification',
              desc: 'The system scrubs PII, then classifies fraud type and computes a risk score.',
            },
            {
              step: '03',
              icon: '',
              title: 'Campaign Clustering',
              desc: 'Cases sharing infrastructure (UPI handles, phone numbers) are linked into ring campaigns.',
            },
          ].map(item => (
            <div key={item.step} className="flex gap-3 p-4 bg-bg-surface border border-border-hairline rounded">
              <div className="text-2xl flex-shrink-0">{item.icon}</div>
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
    </div>
  );
}
