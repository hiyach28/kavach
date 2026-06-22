import React from 'react';

export default function EvidenceTrace({ rawText, redFlags }) {
  if (!rawText) return null;

  // If there are no flags, just render the text
  if (!redFlags || redFlags.length === 0) {
    return (
      <div className="border border-border-hairline rounded bg-bg-surface p-5 space-y-3 font-mono text-sm leading-relaxed whitespace-pre-wrap select-text">
        {rawText}
      </div>
    );
  }

  // Helper to split text by multiple evidence phrases to apply custom highlights
  // Sort evidence by length descending to avoid matching substrings of other highlights first
  const sortedFlags = [...redFlags]
    .filter(f => f.evidence && f.evidence !== 'N/A' && f.evidence.length > 2)
    .sort((a, b) => b.evidence.length - a.evidence.length);

  if (sortedFlags.length === 0) {
    return (
      <div className="border border-border-hairline rounded bg-bg-surface p-5 space-y-3 font-mono text-sm leading-relaxed whitespace-pre-wrap select-text">
        {rawText}
      </div>
    );
  }

  const getSeverityStyle = (category) => {
    switch (category) {
      case 'critical':
        return 'border-b-2 border-sev-critical bg-sev-critical/10 text-text-primary hover:bg-sev-critical/20 cursor-pointer';
      case 'high':
        return 'border-b-2 border-sev-high bg-sev-high/10 text-text-primary hover:bg-sev-high/20 cursor-pointer';
      default:
        return 'border-b-2 border-mod-network bg-mod-network/10 text-text-primary hover:bg-mod-network/20 cursor-pointer';
    }
  };

  // Construct inline highlights
  // We can search-and-replace or build a regex structure
  // To avoid HTML injection or tag matching issues, we do a token-based replacement
  let processedText = rawText;
  const matchesMap = {};
  
  sortedFlags.forEach((flag, idx) => {
    const token = `__FLAG_TOKEN_${idx}__`;
    // Escape regex characters
    const escapedEvidence = flag.evidence.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    const regex = new RegExp(`(${escapedEvidence})`, 'gi');
    
    // Replace first occurrence only to keep trace exact
    processedText = processedText.replace(regex, (match) => {
      matchesMap[token] = { match, flag };
      return token;
    });
  });

  // Split processedText by tokens and render parts
  const tokensRegex = /(__FLAG_TOKEN_\d+__)/;
  const parts = processedText.split(tokensRegex);

  return (
    <div className="border border-border-hairline rounded bg-bg-surface p-5 space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">EVIDENCE_HIGHLIGHTS_TRACE</span>
        <span className="font-mono text-[9px] text-text-secondary uppercase tracking-tight">Hover highlights to inspect flag classifications</span>
      </div>

      <div className="font-mono text-xs leading-relaxed whitespace-pre-wrap select-text p-4 bg-bg-base/40 rounded border border-border-hairline max-h-64 overflow-y-auto">
        {parts.map((part, index) => {
          if (matchesMap[part]) {
            const { match, flag } = matchesMap[part];
            return (
              <span
                key={index}
                title={`[${flag.flag_id}] - ${flag.explanation}`}
                className={`relative px-0.5 py-0.5 rounded-t transition-colors inline-block ${getSeverityStyle(flag.category)}`}
              >
                {match}
                <span className="text-[8px] font-bold ml-1 font-mono uppercase tracking-tighter opacity-80 select-none">
                  ({flag.flag_id})
                </span>
              </span>
            );
          }
          return <span key={index}>{part}</span>;
        })}
      </div>
    </div>
  );
}
