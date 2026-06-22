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
  const pendingCount = cases.filter(c => c.status === 'needs_manual_review').length;

  const topDistrict = [...districts].sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0))[0];

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
    digital_arrest: '',
    upi_spoofing: '',
    investment_fraud: '',
    otp_sim_swap: '',
    needs_manual_review: '',
    legitimate: '',
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-bg-base">

      {/* ── Page Header ── */}
      <div className="flex items-start justify-between border-b border-border-hairline pb-4">
        <div>
          <h2 className="font-condensed text-2xl font-bold tracking-wider text-text-primary uppercase">
            Investigator's Terminal
          </h2>
          <p className="text-xs text-text-secondary mt-1 max-w-lg">
            Real-time cybercrime intelligence dashboard for Indian Police forces. Navigate to FraudScope to classify new cases, NetworkX to inspect fraud rings, or CrimeMap to view high-priority districts.
          </p>
        </div>
        <div className="hidden md:flex items-center gap-1.5 font-mono text-[9px] text-sev-verified bg-sev-verified/10 border border-sev-verified/20 px-3 py-1.5 rounded">
          <span className="h-1.5 w-1.5 rounded-full bg-sev-verified animate-pulse" />
          SYSTEM ONLINE
        </div>
      </div>

      {/* ── Metric Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Cybercrimes (NCRB 2023)', value: "86,420", sub: 'cases registered nationally', color: 'text-text-primary', accent: 'border-border-hairline' },
          { label: 'Total Digital Arrest Losses', value: "₹1,935 Cr", sub: 'MHA figures for 2024', color: 'text-sev-critical', accent: 'border-sev-critical/30' },
          { label: 'Indexed Campaigns', value: campaigns.length, sub: 'tracked fraud rings in local DB', color: 'text-mod-network', accent: 'border-mod-network/30' },
          { label: 'Manual Review', value: pendingCount, sub: 'awaiting analyst locally', color: 'text-sev-high', accent: 'border-sev-high/30' },
        ].map((m, i) => (
          <div key={i} className={`bg-bg-surface border ${m.accent} rounded p-4 space-y-2`}>
            <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest block">{m.label}</span>
            <div className="flex items-baseline gap-2">
              <span className={`font-mono text-3xl font-bold ${m.color}`}>{m.value}</span>
            </div>
            <span className="font-mono text-[9px] text-text-secondary">{m.sub}</span>
          </div>
        ))}
      </div>

      {/* ── Quick Actions ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[
          { tab: 'fraudscope', icon: '', title: 'Classify a Case', desc: 'Submit transcript or screenshot for fraud detection', color: 'hover:border-accent-signal/60 hover:bg-accent-signal/5' },
          { tab: 'network', icon: '', title: 'Inspect Network', desc: 'Explore infrastructure-linked fraud ring graphs', color: 'hover:border-mod-network/60 hover:bg-mod-network/5' },
          { tab: 'crimemap', icon: '', title: 'View Crime Map', desc: 'See priority districts on the choropleth heatmap', color: 'hover:border-mod-enforce/60 hover:bg-mod-enforce/5' },
        ].map(a => (
          <button
            key={a.tab}
            onClick={() => setActiveTab(a.tab)}
            className={`text-left p-4 bg-bg-surface border border-border-hairline rounded transition-all duration-200 ${a.color} group`}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{a.icon}</span>
              <div>
                <div className="font-condensed font-bold text-sm text-text-primary group-hover:text-text-primary tracking-wide mb-1">{a.title}</div>
                <p className="text-[11px] text-text-secondary leading-snug">{a.desc}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* ── Recent Cases + Campaign Summary ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Recent Cases List */}
        <div className="lg:col-span-2 bg-bg-surface border border-border-hairline rounded overflow-hidden flex flex-col">
          <div className="px-5 py-3 border-b border-border-hairline bg-bg-base/30 flex items-center justify-between">
            <span className="font-condensed text-xs font-bold tracking-wider text-text-primary uppercase">
              Recent Classified Cases
            </span>
            <button
              onClick={() => setActiveTab('fraudscope')}
              className="font-mono text-[9px] text-accent-signal hover:underline uppercase tracking-wider"
            >
              + New Case →
            </button>
          </div>
          <div className="divide-y divide-border-hairline flex-1 overflow-y-auto max-h-80">
            {recentCases.length === 0 ? (
              <div className="p-8 text-center">
                <p className="font-mono text-xs text-text-secondary">No cases yet. Submit one via FraudScope.</p>
              </div>
            ) : recentCases.map(c => {
              const badge = getRiskBadge(c.risk_score);
              const icon = FRAUD_ICONS[c.fraud_type] || '';
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

        {/* Campaign + Top District sidebar */}
        <div className="flex flex-col gap-4">
          {/* Top Priority District */}
          {topDistrict && (
            <div className="bg-bg-surface border border-sev-critical/30 rounded p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-sev-critical animate-pulse" />
                <span className="font-condensed text-[10px] font-bold text-sev-critical uppercase tracking-widest">
                  Highest Priority District
                </span>
              </div>
              <div className="font-condensed text-xl font-bold text-text-primary">{topDistrict.name}</div>
              <div className="grid grid-cols-2 gap-2 font-mono text-[9px]">
                <div>
                  <span className="text-text-secondary block">PRIORITY SCORE</span>
                  <span className="text-sev-critical font-bold text-sm">{topDistrict.priority_score}</span>
                </div>
                <div>
                  <span className="text-text-secondary block">COMPLAINTS</span>
                  <span className="text-text-primary font-bold text-sm">{topDistrict.complaint_count}</span>
                </div>
              </div>
              <button
                onClick={() => setActiveTab('crimemap')}
                className="w-full mt-1 py-1.5 font-mono text-[9px] text-text-secondary hover:text-text-primary border border-border-hairline hover:border-text-secondary rounded transition-all text-center"
              >
                View Full Map →
              </button>
            </div>
          )}

          {/* Active Campaigns */}
          <div className="bg-bg-surface border border-border-hairline rounded overflow-hidden flex flex-col flex-1">
            <div className="px-4 py-3 border-b border-border-hairline bg-bg-base/30">
              <span className="font-condensed text-xs font-bold tracking-wider text-text-primary uppercase">
                Active Fraud Rings
              </span>
            </div>
            <div className="p-3 space-y-2 flex-1 overflow-y-auto">
              {campaigns.map(camp => (
                <div key={camp.id} className="p-3 bg-bg-base/30 rounded border border-border-hairline">
                  <div className="font-condensed text-xs font-semibold text-text-primary mb-1 truncate">
                    {camp.label.split(' — ')[1]}
                  </div>
                  <div className="flex justify-between font-mono text-[9px] text-text-secondary">
                    <span>{camp.case_count} cases</span>
                    <span className="text-sev-critical">
                      ₹{(camp.total_estimated_loss / 10000000).toFixed(1)}Cr
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
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
      case 'network': return <NetworkXPage />;
      case 'crimemap': return <CrimeMapPage />;
      case 'overview':
      default: return <OverviewPage />;
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
