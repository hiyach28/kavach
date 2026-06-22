import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import ClassifierInput from '../components/fraudscope/ClassifierInput';
import ResultCard from '../components/fraudscope/ResultCard';
import EvidenceTrace from '../components/fraudscope/EvidenceTrace';

export default function FraudScopePage() {
  const { classifyCase, activeCase } = useCase();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleClassify = async (text) => {
    setLoading(true);
    setError(null);
    try {
      await classifyCase(text);
    } catch (err) {
      setError(
        err.message || 'An error occurred during classification. Graceful degradation triggered.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 select-none bg-bg-base">
      {/* Title Header */}
      <div className="border-b border-border-hairline pb-4 flex items-center justify-between">
        <div className="flex flex-col">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest font-bold">MODULE_01</span>
          <h2 className="font-condensed text-xl font-bold tracking-wider text-text-primary uppercase mt-0.5">FRAUDSCOPE // TEXT VERDICT CLASSIFIER</h2>
        </div>
        <span className="font-mono text-[9px] text-text-secondary uppercase">PII SCRUBBER RUNNING</span>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="border border-sev-critical bg-sev-critical/15 text-sev-critical p-4 rounded text-xs font-mono flex items-start space-x-2">
          <span className="font-bold flex-shrink-0">[FAIL]</span>
          <span>{error}</span>
        </div>
      )}

      {/* Input area */}
      <ClassifierInput onSubmit={handleClassify} isLoading={loading} />

      {/* Results area */}
      {!loading && activeCase && (
        <div className="space-y-6 animate-fade-in">
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
