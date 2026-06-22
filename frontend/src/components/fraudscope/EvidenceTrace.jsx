import React from 'react';

export default function EvidenceTrace({ rawText, redFlags }) {
  if (!rawText) return null;

  // Render raw text with highlighted red flags
  // In a full implementation, we'd find the index of each redFlag.evidence in the text 
  // and wrap it in a span. For this MVP, we will just render the text as a block.

  const renderTextWithHighlights = () => {
    if (!redFlags || redFlags.length === 0) {
      return <span className="text-text-secondary">{rawText}</span>;
    }

    // Very simplistic highlighting approach:
    // Split the text using evidence substrings.
    let highlightedText = [{ type: 'text', content: rawText }];

    redFlags.forEach(flag => {
      if (!flag.evidence) return;
      const newHighlighted = [];
      highlightedText.forEach(segment => {
        if (segment.type !== 'text') {
          newHighlighted.push(segment);
          return;
        }

        const parts = segment.content.split(flag.evidence);
        parts.forEach((part, idx) => {
          if (part) {
            newHighlighted.push({ type: 'text', content: part });
          }
          if (idx < parts.length - 1) {
            newHighlighted.push({
              type: 'highlight',
              content: flag.evidence,
              category: flag.category
            });
          }
        });
      });
      highlightedText = newHighlighted;
    });

    return highlightedText.map((segment, idx) => {
      if (segment.type === 'highlight') {
        const color = segment.category === 'critical' ? 'text-sev-critical bg-sev-critical/10 underline decoration-sev-critical' :
                      segment.category === 'high' ? 'text-sev-high bg-sev-high/10 underline decoration-sev-high' :
                      'text-mod-network bg-mod-network/10 underline decoration-mod-network';
        return <span key={idx} className={`font-mono text-sm px-1 py-0.5 rounded mx-0.5 ${color}`}>{segment.content}</span>;
      }
      return <span key={idx} className="text-text-secondary">{segment.content}</span>;
    });
  };

  return (
    <div className="bg-bg-surface border border-border-hairline rounded-lg overflow-hidden">
      <div className="px-5 py-3 border-b border-border-hairline bg-bg-base/30">
        <span className="font-sans text-[10px] font-bold tracking-widest text-text-secondary uppercase">
          EVIDENCE TRACE (DE-IDENTIFIED)
        </span>
      </div>
      <div className="p-5 font-mono text-sm leading-relaxed whitespace-pre-wrap">
        {renderTextWithHighlights()}
      </div>
    </div>
  );
}
