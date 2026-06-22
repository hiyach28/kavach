import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useCase } from '../../context/CaseContext';
import { apiClient } from '../../api/client';

export default function ForceGraph({ graphData }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const { activeCase, cases, selectCase } = useCase();
  const [error, setError] = useState(null);

  // Load full case from API and set as active
  const handleNodeClick = async (nodeId) => {
    try {
      // nodeId is "case_12" — extract numeric id
      const numId = parseInt(nodeId.replace('case_', ''), 10);
      const res = await fetch(`/api/cases/${numId}`);
      const json = await res.json();
      if (json.success && json.data) {
        // Merge with cases list to get raw_text
        const base = cases.find(c => c.id === numId) || {};
        selectCase({ ...base, ...json.data, id: numId });
      }
    } catch (e) {
      console.error('Failed to load case node', e);
    }
  };

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return;

    setError(null);

    try {
      const width = containerRef.current.clientWidth || 800;
      const height = containerRef.current.clientHeight || 600;

      const svg = d3.select(svgRef.current)
        .attr('width', width)
        .attr('height', height);
      svg.selectAll('*').remove();

      // Zoom layer
      const g = svg.append('g');
      svg.call(
        d3.zoom()
          .scaleExtent([0.3, 3])
          .on('zoom', (event) => g.attr('transform', event.transform))
      );

      // Color mapper from group string e.g. "campaign_2"
      const PALETTE = ['#E24B4A', '#3FB6C7', '#E8A33D', '#7B61FF', '#4ADE80', '#F97316'];
      const getCampaignColor = (group) => {
        if (!group || group === 'unclustered') return '#8B939E';
        const id = parseInt(group.replace('campaign_', ''), 10);
        if (isNaN(id)) return '#8B939E';
        return PALETTE[id % PALETTE.length];
      };

      const nodes = graphData.nodes.map(d => ({ ...d }));

      // Extract string IDs defensively — D3 mutates source/target to node objects after first render
      const nodeIds = new Set(nodes.map(n => n.id));
      const safeLinks = (graphData.links || [])
        .map(d => ({
          source: typeof d.source === 'object' && d.source !== null ? d.source.id : d.source,
          target: typeof d.target === 'object' && d.target !== null ? d.target.id : d.target,
          type: d.type,
        }))
        .filter(d => d.source && d.target && nodeIds.has(d.source) && nodeIds.has(d.target));

      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(safeLinks).id(d => d.id).distance(90))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.degree || 1) * 3 + 14));

      const link = g.append('g')
        .selectAll('line')
        .data(safeLinks)
        .enter().append('line')
        .attr('stroke', d => d.type === 'semantic' ? '#57606a' : '#3A4048')
        .attr('stroke-width', d => d.type === 'semantic' ? 1 : 1.5)
        .attr('stroke-opacity', d => d.type === 'semantic' ? 0.5 : 0.7)
        .attr('stroke-dasharray', d => d.type === 'semantic' ? '4,4' : 'none');

      const nodeGroup = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .style('cursor', 'pointer')
        .call(d3.drag()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
          })
        )
        .on('click', (event, d) => {
          event.stopPropagation();
          handleNodeClick(d.id);
        });

      const circle = nodeGroup.append('circle')
        .attr('fill', d => getCampaignColor(d.group))
        .attr('stroke', d => activeCase && `case_${activeCase.id}` === d.id ? '#E8EAED' : '#14181D')
        .attr('stroke-width', d => activeCase && `case_${activeCase.id}` === d.id ? 2.5 : 1)
        .attr('r', 0);

      circle.transition().duration(600).delay((d, i) => i * 20)
        .attr('r', d => (d.degree || 1) * 2.5 + 8);

      nodeGroup.append('text')
        .attr('dx', d => (d.degree || 1) * 2.5 + 12)
        .attr('dy', '.35em')
        .attr('font-family', 'IBM Plex Mono, monospace')
        .attr('font-size', '8px')
        .attr('fill', '#8B939E')
        .text(d => `#${d.id.replace('case_', '')}`)
        .attr('pointer-events', 'none');

      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        nodeGroup.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });

      return () => simulation.stop();
    } catch (err) {
      console.error('ForceGraph render error:', err);
      setError(err.message);
    }
  }, [graphData, activeCase]);

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-bg-base">
        <div className="font-mono text-xs text-sev-critical border border-sev-critical/30 bg-sev-critical/10 p-4 rounded max-w-sm text-center">
          <div className="font-bold mb-1">[GRAPH_RENDER_ERROR]</div>
          <div className="text-text-secondary">{error}</div>
        </div>
      </div>
    );
  }

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-bg-base">
        <span className="font-mono text-xs text-text-secondary animate-pulse">NO_GRAPH_DATA</span>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative w-full h-full bg-bg-base overflow-hidden">
      <svg ref={svgRef} className="w-full h-full" />

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-bg-surface/90 border border-border-hairline p-3 rounded text-xs select-none space-y-2 z-10 pointer-events-none">
        <span className="font-condensed text-[10px] font-bold text-text-secondary tracking-wider block">CAMPAIGN_CLUSTERS</span>
        <div className="space-y-1.5 font-mono text-[9px] text-text-primary">
          {(graphData.campaigns || []).map((camp, i) => (
            <div key={camp.id} className="flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: ['#E24B4A','#3FB6C7','#E8A33D','#7B61FF','#4ADE80','#F97316'][camp.id % 6] }} />
              <span className="truncate max-w-[140px]">{camp.label?.split(' — ')[1] || camp.label} ({camp.case_count})</span>
            </div>
          ))}
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-text-secondary flex-shrink-0" />
            <span>Unclustered</span>
          </div>
        </div>
        <div className="pt-2 border-t border-border-hairline font-mono text-[8px] text-text-secondary">
          Scroll to zoom · Drag to pan · Click node to inspect
        </div>
      </div>

      {/* Node count badge */}
      <div className="absolute top-4 right-4 font-mono text-[9px] text-text-secondary bg-bg-surface/80 border border-border-hairline px-2 py-1 rounded">
        {graphData.nodes.length} nodes · {graphData.links?.length || 0} edges
      </div>
    </div>
  );
}
