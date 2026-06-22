import React from 'react';
import { CaseProvider, useCase } from './context/CaseContext';
import StatusBar from './components/shell/StatusBar';
import ModuleRail from './components/shell/ModuleRail';
import DossierPanel from './components/shell/DossierPanel';

// Pages
import FraudScopePage from './pages/FraudScopePage';
import NetworkXPage from './pages/NetworkXPage';
import CrimeMapPage from './pages/CrimeMapPage';

// Simple dashboard overview page
function OverviewPage() {
  const { cases, campaigns, districts, selectCase, setActiveTab } = useCase();

  // Sort cases to find recent ones
  const recentCases = [...cases].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5);

  // High risk count (score >= 70)
  const criticalCount = cases.filter(c => c.risk_score >= 70).length;

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6 select-none bg-bg-base">
      {/* Welcome Banner */}
      <div className="border border-border-hairline p-5 rounded bg-bg-surface flex items-center justify-between">
        <div>
          <h2 className="font-condensed text-xl font-bold tracking-wider text-text-primary">INVESTIGATOR INTERPOLATION TERMINAL</h2>
          <p className="text-xs text-text-secondary mt-1 max-w-xl">
            Real-time cybercrime intelligence aggregator for Indian Police forces. Use the side rail to run text classification (FraudScope), inspect infrastructure nodes (NetworkX), or view priority districts (CrimeMap).
          </p>
        </div>
        <div className="text-right font-mono text-xs text-text-secondary space-y-1">
          <div>NODE_STATUS: <span className="text-sev-verified font-bold">ONLINE</span></div>
          <div>MOCK_DATABASE: <span className="text-mod-network font-bold">SEED_VER_1.0</span></div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="border border-border-hairline p-4 rounded bg-bg-surface space-y-1">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest block">TOTAL_RECORDS</span>
          <div className="flex items-baseline space-x-2">
            <span className="font-mono text-2xl font-bold text-text-primary">{cases.length}</span>
            <span className="text-[10px] text-text-secondary font-mono">cases</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="border border-border-hairline p-4 rounded bg-bg-surface space-y-1">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest block">CRITICAL_THREATS</span>
          <div className="flex items-baseline space-x-2">
            <span className="font-mono text-2xl font-bold text-sev-critical">{criticalCount}</span>
            <span className="text-[10px] text-text-secondary font-mono">score &ge; 70</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="border border-border-hairline p-4 rounded bg-bg-surface space-y-1">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest block">ACTIVE_CAMPAIGNS</span>
          <div className="flex items-baseline space-x-2">
            <span className="font-mono text-2xl font-bold text-mod-network">{campaigns.length}</span>
            <span className="text-[10px] text-text-secondary font-mono">clusters</span>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="border border-border-hairline p-4 rounded bg-bg-surface space-y-1">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest block">MAPPED_REGIONS</span>
          <div className="flex items-baseline space-x-2">
            <span className="font-mono text-2xl font-bold text-mod-enforce">{districts.length}</span>
            <span className="text-[10px] text-text-secondary font-mono">districts</span>
          </div>
        </div>
      </div>

      {/* Recent Alerts & Campaign Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recent Classified Cases */}
        <div className="lg:col-span-2 border border-border-hairline rounded bg-bg-surface flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border-hairline bg-bg-base/30 flex items-center justify-between">
            <span className="font-condensed text-xs font-bold tracking-wider text-text-primary uppercase">RECENTLY_CLASSIFIED_TRANSCRIPTS</span>
            <button onClick={() => setActiveTab('fraudscope')} className="font-mono text-[10px] text-accent-signal hover:underline">NEW_CLASSIFICATION_RUN &rarr;</button>
          </div>
          <div className="divide-y divide-border-hairline max-h-80 overflow-y-auto">
            {recentCases.map((c) => (
              <div
                key={c.id}
                onClick={() => selectCase(c)}
                className="p-3 hover:bg-bg-base/40 cursor-pointer flex items-center justify-between transition-colors"
              >
                <div className="flex flex-col min-w-0 pr-4 space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs text-text-primary font-semibold">Case #{c.id}</span>
                    <span className="font-mono text-[9px] text-text-secondary">[{c.district || 'Pune'}]</span>
                  </div>
                  <p className="text-xs text-text-secondary truncate leading-tight select-text">
                    {c.raw_text_deidentified}
                  </p>
                </div>
                <div className="flex items-center space-x-3 flex-shrink-0">
                  <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded border ${
                    c.risk_score >= 70 ? 'text-sev-critical bg-sev-critical/10 border-sev-critical/20' :
                    c.risk_score >= 40 ? 'text-sev-high bg-sev-high/10 border-sev-high/20' :
                    c.risk_score !== null ? 'text-sev-verified bg-sev-verified/10 border-sev-verified/20' :
                    'text-text-secondary bg-text-secondary/10 border-border-hairline'
                  }`}>
                    {c.risk_score !== null ? `RISK_${c.risk_score}` : 'PENDING'}
                  </span>
                  <span className="font-mono text-[9px] text-text-secondary hidden sm:inline">{new Date(c.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Active Campaigns Summary */}
        <div className="border border-border-hairline rounded bg-bg-surface flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border-hairline bg-bg-base/30">
            <span className="font-condensed text-xs font-bold tracking-wider text-text-primary uppercase">ACTIVE_CAMPAIGN_SUMMARY</span>
          </div>
          <div className="p-4 flex-1 space-y-4">
            {campaigns.map((camp) => (
              <div key={camp.id} className="p-3 bg-bg-base/30 rounded border border-border-hairline space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-condensed text-xs font-semibold text-text-primary">{camp.label.split(' — ')[1]}</span>
                  <span className="font-mono text-[9px] text-mod-network tracking-wider px-1 bg-mod-network/10 border border-mod-network/20 rounded uppercase">Campaign #{camp.id}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-left pt-1">
                  <div>
                    <span className="font-mono text-[8px] text-text-secondary block">MEMBER_CASES</span>
                    <span className="font-mono text-sm font-semibold text-text-primary">{camp.case_count} cases</span>
                  </div>
                  <div>
                    <span className="font-mono text-[8px] text-text-secondary block">ESTIMATED_FINANCIAL_LOSS</span>
                    <span className="font-mono text-sm font-semibold text-sev-critical">
                      ₹{(camp.total_estimated_loss / 100).toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Shell content switcher
function AppContent() {
  const { activeTab } = useCase();

  const renderContent = () => {
    switch (activeTab) {
      case 'fraudscope':
        return <FraudScopePage />;
      case 'network':
        return <NetworkXPage />;
      case 'crimemap':
        return <CrimeMapPage />;
      case 'overview':
      default:
        return <OverviewPage />;
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

export default function App() {
  return (
    <CaseProvider>
      <StatusBar />
      <AppContent />
    </CaseProvider>
  );
}
