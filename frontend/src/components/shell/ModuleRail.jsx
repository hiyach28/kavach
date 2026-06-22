import React from 'react';
import { useCase } from '../../context/CaseContext';

export default function ModuleRail() {
  const { activeTab, setActiveTab } = useCase();

  const navItems = [
    { id: 'overview', number: '00', label: 'OVERVIEW', desc: 'System dashboard' },
    { id: 'fraudscope', number: '01', label: 'FRAUDSCOPE', desc: 'Case classification' },
    { id: 'network', number: '02', label: 'NETWORKX', desc: 'Infrastructure graph' },
    { id: 'crimemap', number: '03', label: 'CRIMEMAP', desc: 'Priority choropleth' }
  ];

  return (
    <div className="w-64 bg-bg-surface border-r border-border-hairline flex flex-col h-full select-none justify-between">
      {/* Navigation Links */}
      <div className="flex flex-col pt-6 px-3 space-y-2">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-stretch text-left rounded border transition-all duration-200 ${
                isActive
                  ? 'bg-bg-base border-accent-signal text-text-primary'
                  : 'bg-transparent border-transparent text-text-secondary hover:text-text-primary hover:bg-bg-base/30'
              }`}
            >
              {/* Vertical Indicator Indicator Bar */}
              <div className={`w-1 rounded-l ${isActive ? 'bg-accent-signal' : 'bg-transparent'}`}></div>
              
              <div className="flex-1 py-3 px-4 flex items-center space-x-4">
                <span className="font-mono text-sm font-bold tracking-wider opacity-60">
                  {item.number}
                </span>
                <div className="flex flex-col">
                  <span className="font-sans text-sm font-semibold tracking-wider">
                    {item.label}
                  </span>
                  <span className="font-mono text-[13px] text-text-secondary uppercase tracking-tight">
                    {item.desc}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Terminal Branding Footer */}
      <div className="p-6 border-t border-border-hairline font-mono text-xs text-text-secondary space-y-1.5 bg-bg-base/20">
        <div>SYSTEM: <span className="text-text-primary">ONLINE</span></div>
        <div>SEC_GRADE: <span className="text-mod-network font-semibold">CONFIDENTIAL</span></div>
        <div className="text-[13px] opacity-75">POLICE ANALYST TERMINAL v0.1</div>
      </div>
    </div>
  );
}
