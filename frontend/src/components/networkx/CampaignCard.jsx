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

  const handleExport = (e) => {
    e.stopPropagation();
    const brief = `TAKEDOWN BRIEF - CAMPAIGN_${id}
=============================
Name: ${label}
Total Cases: ${case_count}
Estimated Loss: ₹${lossInRupees}
Cross Jurisdiction: ${campaign.cross_jurisdiction ? 'YES (ESCALATE)' : 'NO'}

PRIMARY TARGET
--------------
Target Node ID: I_${campaign.primary_target_infra_id}
Betweenness Score: ${campaign.primary_target_betweenness?.toFixed(2) || 'N/A'}
Action: IMMEDIATE TAKEDOWN RECOMMENDED

COLLAPSE IMPACT
---------------
Fractures Network: ${campaign.fractures_network ? 'YES' : 'NO'}
Connectivity Lost: ${campaign.pct_connectivity_lost ? (campaign.pct_connectivity_lost * 100).toFixed(0) : 0}%`;

    const blob = new Blob([brief], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `takedown_brief_camp_${id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      onClick={() => onSelect(id)}
      className={`border rounded p-4 cursor-pointer transition-all duration-200 space-y-3 bg-bg-surface ${getCampaignBorder(id)}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-sans text-xs font-bold text-text-primary truncate pr-2">
          {label.split(' — ')[1] || label}
        </span>
        <span className={`font-mono text-xs font-bold tracking-wider px-1.5 py-0.5 border rounded uppercase flex-shrink-0 ${getCampaignBadgeColor(id)}`}>
          CAMPAIGN_{id}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-left border-t border-border-hairline/50 pt-2 font-mono">
        <div className="space-y-0.5">
          <span className="text-xs text-text-secondary uppercase block">MEMBER_CASES</span>
          <span className="text-xs font-bold text-text-primary">{case_count} cases</span>
        </div>
        <div className="space-y-0.5">
          <span className="text-xs text-text-secondary uppercase block">EST_FIN_LOSS</span>
          <span className="text-xs font-bold text-sev-critical">₹{lossInRupees}</span>
        </div>
      </div>

      {isActive && campaign.primary_target_infra_id && (
        <div className="mt-4 pt-4 border-t border-border-hairline/50 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-primary uppercase tracking-wider">Takedown Brief</span>
            {campaign.cross_jurisdiction && (
              <span className="text-[10px] bg-sev-critical text-bg-surface px-1 font-bold rounded uppercase">
                Escalation Reqd
              </span>
            )}
          </div>
          
          <div className="bg-bg-base border border-border-hairline rounded p-2 text-xs font-mono space-y-2">
            <div className="flex justify-between">
              <span className="text-text-secondary">TARGET_NODE</span>
              <span className="text-accent-signal font-bold">I_{campaign.primary_target_infra_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">FRACTURES_NET</span>
              <span className={campaign.fractures_network ? "text-sev-critical font-bold" : "text-text-primary"}>
                {campaign.fractures_network ? "YES" : "NO"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">CONN_LOST</span>
              <span className="text-text-primary font-bold">
                {campaign.pct_connectivity_lost ? (campaign.pct_connectivity_lost * 100).toFixed(0) : 0}%
              </span>
            </div>
          </div>
          
          <button 
            onClick={handleExport}
            className="w-full py-1 border border-text-secondary text-text-primary text-xs font-mono uppercase hover:bg-text-secondary/10 transition-colors"
          >
            Export Brief
          </button>
        </div>
      )}
    </div>
  );
}
