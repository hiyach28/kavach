import React from 'react';
import { CaseProvider, useCase } from './context/CaseContext';
import StatusBar from './components/shell/StatusBar';
import ModuleRail from './components/shell/ModuleRail';
import DossierPanel from './components/shell/DossierPanel';

// Pages
import FraudScopePage from './pages/FraudScopePage';
import NetworkXPage from './pages/NetworkXPage';
import CrimeMapPage from './pages/CrimeMapPage';

// ─── Overview Dashboard ───────────────────────────────────────────────────────
function OverviewPage() {
  const { cases, campaigns, districts, selectCase, setActiveTab } = useCase();

  const recentCases = [...cases]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 6);

  const criticalCount = cases.filter(c => c.risk_score >= 70).length;
  const pendingCount  = cases.filter(c => c.status === 'needs_manual_review').length;
  const topDistrict   = [...districts].sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0))[0];

  const getRiskBadge = (score) => {
    if (score === null || score === undefined)
      return { cls: 'text-sev-high bg-sev-high/10 border-sev-high/20', label: 'REVIEW' };
    if (score >= 70)
      return { cls: 'text-sev-critical bg-sev-critical/10 border-sev-critical/20', label: `RISK ${score}` };
    if (score >= 40)
      return { cls: 'text-sev-high bg-sev-high/10 border-sev-high/20', label: `RISK ${score}` };
    return { cls: 'text-sev-verified bg-sev-verified/10 border-sev-verified/20', label: `RISK ${score}` };
  };

  const FRAUD_ICONS = {
    digital_arrest:     '🚨',
    upi_spoofing:       '💳',
    investment_fraud:   '📈',
    otp_sim_swap:       '📱',
    needs_manual_review:'⚠️',
    legitimate:         '✅',
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-5 bg-bg-base">

      {/* ── Page Header ── */}
      <div className="flex items-center justify-between border-b border-border-hairline pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-text-primary">
            Investigator's Terminal
          </h2>
          <p className="text-xs text-text-secondary mt-1 max-w-lg leading-relaxed">
            Real-time cybercrime intelligence dashboard for Indian Police forces.
          </p>
        </div>
        <div className="hidden md:flex items-center gap-1.5 font-mono text-[9px] text-sev-verified bg-sev-verified/10 border border-sev-verified/20 px-3 py-1.5 rounded">
          <span className="h-1.5 w-1.5 rounded-full bg-sev-verified animate-pulse" />
          SYSTEM ONLINE
        </div>
      </div>

      {/* ── Highest Priority District Banner (AT TOP) ── */}
      {topDistrict && (
        <div className="flex items-center justify-between bg-bg-surface border border-sev-critical/30 rounded-lg px-5 py-3.5 gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <span className="h-2.5 w-2.5 rounded-full bg-sev-critical animate-pulse flex-shrink-0" />
            <div className="min-w-0">
              <span className="font-mono text-[9px] text-sev-critical/80 uppercase tracking-widest block mb-0.5">
                ⚠ Highest Priority District
              </span>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-base font-bold text-text-primary">{topDistrict.name}</span>
                <span className="font-mono text-[10px] text-text-secondary">{topDistrict.state}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-5 flex-shrink-0">
            <div className="text-right">
              <span className="font-mono text-[9px] text-text-secondary block">PRIORITY</span>
              <span className="font-mono text-xl font-bold text-sev-critical">{topDistrict.priority_score}</span>
            </div>
            <div className="text-right">
              <span className="font-mono text-[9px] text-text-secondary block">COMPLAINTS</span>
              <span className="font-mono text-xl font-bold text-text-primary">{topDistrict.complaint_count}</span>
            </div>
            <button
              onClick={() => setActiveTab('crimemap')}
              className="py-1.5 px-3 font-mono text-[9px] text-sev-critical border border-sev-critical/30 hover:bg-sev-critical/10 rounded transition-all whitespace-nowrap"
            >
              View Map →
            </button>
          </div>
        </div>
      )}

      {/* ── Metric Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Total Cases',      value: cases.length,     sub: 'indexed complaints', color: 'text-text-primary', accent: 'border-border-hairline' },
          { label: 'Critical Threats', value: criticalCount,    sub: 'risk score ≥ 70',    color: 'text-sev-critical', accent: 'border-sev-critical/30' },
          { label: 'Active Campaigns', value: campaigns.length, sub: 'fraud ring clusters', color: 'text-mod-network',  accent: 'border-mod-network/30' },
          { label: 'Manual Review',    value: pendingCount,     sub: 'awaiting analyst',   color: 'text-sev-high',     accent: 'border-sev-high/30' },
        ].map((m, i) => (
          <div key={i} className={`bg-bg-surface border ${m.accent} rounded-lg p-4 space-y-1.5`}>
            <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest block">{m.label}</span>
            <span className={`font-mono text-3xl font-bold ${m.color} block leading-none`}>{m.value}</span>
            <span className="font-mono text-[9px] text-text-secondary">{m.sub}</span>
          </div>
        ))}
      </div>

      {/* ── Quick Actions ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[
          { tab: 'fraudscope', icon: '📝', title: 'Classify a Case',  desc: 'Submit transcript or screenshot for fraud detection',   color: 'hover:border-accent-signal/60 hover:bg-accent-signal/5' },
          { tab: 'network',    icon: '🔗', title: 'Inspect Network',  desc: 'Explore infrastructure-linked fraud ring graphs',       color: 'hover:border-mod-network/60 hover:bg-mod-network/5'     },
          { tab: 'crimemap',   icon: '🗺️', title: 'View Crime Map',  desc: 'See priority districts on the choropleth heatmap',     color: 'hover:border-mod-enforce/60 hover:bg-mod-enforce/5'     },
        ].map(a => (
          <button
            key={a.tab}
            onClick={() => setActiveTab(a.tab)}
            className={`text-left p-4 bg-bg-surface border border-border-hairline rounded-lg transition-all duration-200 ${a.color}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl flex-shrink-0">{a.icon}</span>
              <div>
                <div className="font-semibold text-sm text-text-primary mb-0.5">{a.title}</div>
                <p className="text-[11px] text-text-secondary leading-snug">{a.desc}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* ── Recent Cases (full-width) ── */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg overflow-hidden">
        <div className="px-5 py-3 border-b border-border-hairline bg-bg-base/30 flex items-center justify-between">
          <span className="font-mono text-[10px] font-bold tracking-widest text-text-secondary uppercase">
            Recent Classified Cases
          </span>
          <button
            onClick={() => setActiveTab('fraudscope')}
            className="font-mono text-[9px] text-accent-signal hover:underline uppercase tracking-wider"
          >
            + New Case →
          </button>
        </div>
        <div className="divide-y divide-border-hairline">
          {recentCases.length === 0 ? (
            <div className="p-8 text-center">
              <p className="font-mono text-xs text-text-secondary">No cases yet. Submit one via FraudScope.</p>
            </div>
          ) : recentCases.map(c => {
            const badge = getRiskBadge(c.risk_score);
            const icon  = FRAUD_ICONS[c.fraud_type] || '🔎';
            return (
              <div
                key={c.id}
                onClick={() => selectCase(c)}
                className="px-5 py-3 hover:bg-bg-base/40 cursor-pointer flex items-center gap-4 transition-colors"
              >
                <span className="text-base flex-shrink-0">{icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-mono text-xs text-text-primary font-semibold">Case #{c.id}</span>
                    <span className="font-mono text-[9px] text-text-secondary">{c.district || 'Unknown'}</span>
                  </div>
                  <p className="text-[11px] text-text-secondary truncate">{c.raw_text_deidentified}</p>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className={`font-mono text-[9px] px-1.5 py-0.5 rounded border ${badge.cls}`}>
                    {badge.label}
                  </span>
                  <span className="font-mono text-[8px] text-text-secondary">
                    {new Date(c.created_at).toLocaleDateString('en-IN')}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Active Fraud Ring Campaigns (BELOW cases — scrollable) ── */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg overflow-hidden">
        <div className="px-5 py-3 border-b border-border-hairline bg-bg-base/30 flex items-center justify-between">
          <span className="font-mono text-[10px] font-bold tracking-widest text-text-secondary uppercase">
            Active Fraud Ring Campaigns
          </span>
          <button
            onClick={() => setActiveTab('network')}
            className="font-mono text-[9px] text-mod-network hover:underline uppercase tracking-wider"
          >
            Inspect Graph →
          </button>
        </div>
        <div className="divide-y divide-border-hairline">
          {campaigns.map(camp => (
            <div key={camp.id} className="px-5 py-4 flex items-center gap-6">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[9px] text-mod-network bg-mod-network/10 border border-mod-network/20 px-1.5 py-0.5 rounded uppercase tracking-widest">
                    Campaign #{camp.id}
                  </span>
                </div>
                <div className="font-semibold text-sm text-text-primary leading-snug">
                  {camp.label.split(' — ')[1]}
                </div>
              </div>
              <div className="flex items-center gap-5 flex-shrink-0 font-mono text-xs">
                <div className="text-right">
                  <span className="text-[9px] text-text-secondary block">CASES</span>
                  <span className="text-text-primary font-bold">{camp.case_count}</span>
                </div>
                <div className="text-right">
                  <span className="text-[9px] text-text-secondary block">EST. LOSS</span>
                  <span className="text-sev-critical font-bold">₹{(camp.total_estimated_loss / 10000000).toFixed(1)}Cr</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

// ─── Shell content switcher ───────────────────────────────────────────────────
function AppContent() {
  const { activeTab } = useCase();

  const renderContent = () => {
    switch (activeTab) {
      case 'fraudscope': return <FraudScopePage />;
      case 'network':    return <NetworkXPage />;
      case 'crimemap':   return <CrimeMapPage />;
      case 'overview':
      default:           return <OverviewPage />;
    }
  };

  return (
    <div className="flex-1 flex flex-row overflow-hidden w-full bg-bg-base">
      <ModuleRail />
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {renderContent()}
      </div>
      <DossierPanel />
    </div>
  );
}

// ─── Root App ─────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <CaseProvider>
      <StatusBar />
      <AppContent />
    </CaseProvider>
  );
}
