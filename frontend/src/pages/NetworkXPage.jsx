import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { apiClient } from '../api/client';
import ForceGraph from '../components/networkx/ForceGraph';
import CampaignCard from '../components/networkx/CampaignCard';

export default function NetworkXPage() {
  const { activeCampaign, selectCampaign } = useCase();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);

  // Fetch graph details
  const fetchGraphData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getGraph();
      setGraphData(data);
    } catch (err) {
      console.error("Failed to load graph data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full bg-bg-base overflow-hidden">
      {/* Title Header */}
      <div className="p-6 border-b border-border-hairline bg-bg-surface flex items-center justify-between flex-shrink-0">
        <div className="flex flex-col">
          <span className="font-mono text-[9px] text-text-secondary uppercase tracking-widest font-bold">MODULE_02</span>
          <h2 className="font-condensed text-xl font-bold tracking-wider text-text-primary uppercase mt-0.5">NETWORKX // INFRASTRUCTURE GRAPH CLUSTERING</h2>
        </div>
        <div className="flex items-center space-x-2 font-mono text-[9px] text-text-secondary">
          <span>ALGORITHM:</span>
          <span className="text-mod-network font-semibold uppercase">LOUVAIN_COMMUNITY_DETECT</span>
        </div>
      </div>

      {/* Main Canvas and Campaign Panel */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0 relative">
        {/* Left: Force-directed Graph Canvas */}
        <div className="flex-1 min-h-0 h-full relative border-r border-border-hairline">
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center font-mono text-xs text-text-secondary">
              <span className="animate-pulse">RUNNING_COMMUNITY_CLUSTERING_SIM...</span>
            </div>
          ) : (
            <ForceGraph graphData={graphData} />
          )}
        </div>

        {/* Right (In-Page): Campaign Lists */}
        <div className="w-full lg:w-72 flex-shrink-0 bg-bg-surface/30 border-t lg:border-t-0 border-border-hairline p-4 overflow-y-auto flex flex-col space-y-4">
          <div className="flex flex-col space-y-1">
            <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">DETECTED_RING_CAMPAIGNS</span>
            <p className="text-[10px] text-text-secondary leading-snug">
              Communities automatically aggregated based on shared telecom endpoints, bank codes, or UPI payment handles.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            {graphData.campaigns && graphData.campaigns.map((camp) => (
              <CampaignCard
                key={camp.id}
                campaign={camp}
                isActive={activeCampaign && activeCampaign.id === camp.id}
                onSelect={selectCampaign}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
