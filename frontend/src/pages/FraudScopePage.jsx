import React, { useState, useEffect } from 'react';
import { useCase } from '../context/CaseContext';
import ClassifierInput from '../components/fraudscope/ClassifierInput';
import ResultCard from '../components/fraudscope/ResultCard';
import EvidenceTrace from '../components/fraudscope/EvidenceTrace';

export default function FraudScopePage() {
  const { classifyCase, activeCase, cases } = useCase();
  const [loading, setLoading]               = useState(false);
  const [error, setError]                   = useState(null);
  // classifiedResult: only populated after an explicit "Run Verdict Analysis" click
  const [classifiedResult, setClassifiedResult] = useState(null);

  // When activeCase is cleared (e.g. after Confirm Scam), also clear our local result
  useEffect(() => {
    if (!activeCase) {
      setClassifiedResult(null);
    }
  }, [activeCase]);

  const handleClassify = async (text) => {
    setLoading(true);
    setError(null);
    setClassifiedResult(null); // clear any previous result while loading
    try {
      await classifyCase(text);
      // After classifyCase, activeCase in context is updated; we mark results as ready
      setClassifiedResult(true); // sentinel: results are ready to display
    } catch (err) {
      setError(err.message || 'Classification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Determine whether to show results: only if an explicit analysis was run this session
  const showResults = !loading && classifiedResult && activeCase;

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
          <h2 className="text-2xl font-bold tracking-wide text-text-primary">
            FraudScope
          </h2>
          <p className="text-xs text-text-secondary mt-1 max-w-lg leading-relaxed">
            Submit a complaint transcript, SMS, WhatsApp message, or screenshot — the system will classify the cybercrime type, extract evidence indicators, and cluster it into known fraud campaigns.
          </p>
        </div>
        <div className="hidden md:flex flex-col items-end gap-1 font-mono text-[9px] text-text-secondary">
          <span>TOTAL CASES: <span className="text-text-primary font-bold">{cases.length}</span></span>
          <span>ENGINE: <span className="text-accent-signal">MOCK v1.0</span></span>
        </div>
      </div>

      {/* How it works — only shown when no result has been submitted yet */}
      {!classifiedResult && !loading && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            {
              step: '01',
              icon: '📝',
              title: 'Submit Evidence',
              desc: 'Paste a complaint transcript or upload a WhatsApp / SMS screenshot.',
            },
            {
              step: '02',
              icon: '🔍',
              title: 'Auto-Classification',
              desc: 'The system scrubs PII, then classifies fraud type and computes a risk score.',
            },
            {
              step: '03',
              icon: '🔗',
              title: 'Campaign Clustering',
              desc: 'Cases sharing infrastructure (UPI handles, phone numbers) are linked into ring campaigns.',
            },
          ].map(item => (
            <div key={item.step} className="flex gap-3 p-4 bg-bg-surface border border-border-hairline rounded-lg">
              <div className="text-2xl flex-shrink-0">{item.icon}</div>
              <div>
                <div className="font-mono text-[9px] text-text-secondary mb-0.5">STEP {item.step}</div>
                <div className="font-semibold text-sm text-text-primary mb-1">{item.title}</div>
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
          <div className="h-40 bg-bg-surface border border-border-hairline rounded-lg" />
          <div className="h-24 bg-bg-surface border border-border-hairline rounded-lg" />
        </div>
      )}

      {/* Results — only shown after explicit button click */}
      {showResults && (
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
