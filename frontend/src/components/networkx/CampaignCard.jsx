import React from 'react';

export default function CampaignCard({ campaign, isActive, onSelect }) {
  if (!campaign) return null;

  const { id, label, case_count, total_estimated_loss } = campaign;

  // Convert paise to rupees
  const lossInRupees = (total_estimated_loss / 100).toLocaleString('en-IN');

  const getCampaignBorder = (campId) => {
    switch (campId) {
      case 1: return isActive ? 'border-sev-critical bg-sev-critical/5' : 'border-border-hairline hover:border-sev-critical/50';
      case 2: return isActive ? 'border-mod-network bg-mod-network/5' : 'border-border-hairline hover:border-mod-network/50';
      case 3: return isActive ? 'border-accent-signal bg-accent-signal/5' : 'border-border-hairline hover:border-accent-signal/50';
      default: return isActive ? 'border-text-primary bg-text-primary/5' : 'border-border-hairline hover:border-text-secondary';
    }
  };

  const getCampaignBadgeColor = (campId) => {
    switch (campId) {
      case 1: return 'text-sev-critical bg-sev-critical/10 border-sev-critical/20';
      case 2: return 'text-mod-network bg-mod-network/10 border-mod-network/20';
      case 3: return 'text-accent-signal bg-accent-signal/10 border-accent-signal/20';
      default: return 'text-text-secondary bg-text-secondary/10 border-border-hairline';
    }
  };

  return (
    <div
      onClick={() => onSelect(id)}
      className={`border rounded p-4 cursor-pointer transition-all duration-200 space-y-3 bg-bg-surface ${getCampaignBorder(id)}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-condensed text-xs font-bold text-text-primary truncate pr-2">
          {label.split(' — ')[1]}
        </span>
        <span className={`font-mono text-[8px] font-bold tracking-wider px-1.5 py-0.5 border rounded uppercase flex-shrink-0 ${getCampaignBadgeColor(id)}`}>
          CAMPAIGN_{id}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-left border-t border-border-hairline/50 pt-2 font-mono">
        <div className="space-y-0.5">
          <span className="text-[8px] text-text-secondary uppercase block">MEMBER_CASES</span>
          <span className="text-xs font-bold text-text-primary">{case_count} cases</span>
        </div>
        <div className="space-y-0.5">
          <span className="text-[8px] text-text-secondary uppercase block">EST_FIN_LOSS</span>
          <span className="text-xs font-bold text-sev-critical">₹{lossInRupees}</span>
        </div>
      </div>
    </div>
  );
}
