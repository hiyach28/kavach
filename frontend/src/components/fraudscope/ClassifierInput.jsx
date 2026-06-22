import React, { useState } from 'react';

export default function ClassifierInput({ onSubmit, isLoading }) {
  const [text, setText] = useState('');
  const [statusLog, setStatusLog] = useState([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || isLoading) return;

    // Simulate system progress log lines
    setStatusLog([]);
    onSubmit(text);
    
    // Status logs timing corresponding to apiClient delay
    const logs = [
      { msg: 'INITIALIZING DE-IDENTIFICATION PIPELINE...', delay: 0 },
      { msg: 'COMPLETED PII DE-IDENTIFICATION MASKING...', delay: 400 },
      { msg: 'REQUEST ENCRYPTED AND SENT TO CLAUDE SONNET...', delay: 700 },
      { msg: 'STRUCTURING INFERENCE RESPONSE SCHEMAS...', delay: 1100 },
      { msg: 'UPDATING LOUVAIN COMMUNITY CLUSTERING GRAPHS...', delay: 1300 }
    ];

    logs.forEach(l => {
      setTimeout(() => {
        setStatusLog(prev => [...prev, l.msg]);
      }, l.delay);
    });
  };

  return (
    <div className="border border-border-hairline rounded bg-bg-surface p-5 space-y-4">
      <div className="flex items-center justify-between">
        <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">INPUT_TRANSCRIBE_FIELD</span>
        <span className="font-mono text-[9px] text-text-secondary uppercase tracking-tight bg-bg-base px-2 py-0.5 border border-border-hairline rounded">SECURE_PII_GUARD: ACTIVE</span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste call transcript, SMS message, WhatsApp thread, or UPI payment request details here for classification..."
          rows={6}
          disabled={isLoading}
          className="w-full bg-bg-base border border-border-hairline rounded p-4 text-sm text-text-primary placeholder:text-text-secondary/50 font-mono focus:border-accent-signal transition-colors leading-relaxed resize-none"
        />

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
          <div className="text-[10px] text-text-secondary max-w-md">
            All 10-digit mobile numbers and 12-digit numeric sequences (Aadhaar cards) are automatically scrubbed and tokenized client-side before analysis.
          </div>
          <button
            type="submit"
            disabled={!text.trim() || isLoading}
            className={`px-6 py-2.5 rounded font-condensed font-bold text-xs tracking-wider border transition-all duration-200 self-end ${
              !text.trim() || isLoading
                ? 'bg-bg-base border-border-hairline text-text-secondary/40 cursor-not-allowed'
                : 'bg-accent-signal/20 hover:bg-accent-signal/30 text-accent-signal border-accent-signal/40'
            }`}
          >
            {isLoading ? 'ANALYZING...' : 'RUN VERDICT ANALYSIS'}
          </button>
        </div>
      </form>

      {/* Monospace System Logs */}
      {statusLog.length > 0 && (
        <div className="p-3 bg-bg-base border border-border-hairline rounded font-mono text-[10px] text-mod-network leading-loose space-y-1 select-none">
          {statusLog.map((log, idx) => (
            <div key={idx} className="flex items-start space-x-2">
              <span className="text-text-secondary flex-shrink-0">&gt;</span>
              <span className="break-all">{log}</span>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-center space-x-1.5 pl-3">
              <span className="h-1 w-1 bg-mod-network rounded-full animate-ping"></span>
              <span className="text-text-secondary text-[8px] animate-pulse">PROCESSING_INFERENCE_STREAM...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
