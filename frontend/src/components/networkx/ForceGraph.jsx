import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useCase } from '../../context/CaseContext';

export default function ForceGraph({ graphData }) {
  const svgRef = useRef(null);
  const { selectCase, activeCase } = useCase();

  useEffect(() => {
    if (!svgRef.current || !graphData || !graphData.nodes) return;

    const width = svgRef.current.clientWidth || 600;
    const height = svgRef.current.clientHeight || 500;

    // Clear previous SVG contents
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Color mapper for Campaign clusters
    const getCampaignColor = (campId) => {
      switch (campId) {
        case 1: return '#E24B4A'; // Campaign A - red
        case 2: return '#3FB6C7'; // Campaign B - cyan
        case 3: return '#E8A33D'; // Campaign C - amber
        default: return '#8B939E'; // Unclustered - grey
      }
    };

    // Deep copy data to prevent D3 from mutating React props directly
    const nodes = graphData.nodes.map(d => ({ ...d }));
    const links = graphData.links.map(d => ({ ...d }));

    // Define simulation forces
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-150))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(d => (d.degree || 1) * 3 + 12));

    // Render connecting links
    const link = svg.append("g")
      .attr("class", "links-layer")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("stroke", "#2A3038")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.6);

    // Create container for nodes
    const nodeGroup = svg.append("g")
      .attr("class", "nodes-layer")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node-group")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended)
      )
      .on("click", (event, d) => {
        selectCase(d);
      });

    // Append circular nodes
    const node = nodeGroup.append("circle")
      .attr("class", "node")
      .attr("fill", d => getCampaignColor(d.campaign_id))
      .attr("stroke", d => activeCase && d.id === activeCase.id ? "#E8EAED" : "#14181D")
      .attr("stroke-width", d => activeCase && d.id === activeCase.id ? 2.5 : 1)
      // Node sizing based on degree connectivity
      .attr("r", 0); // start at 0 for enter animation

    // Enter animation: nodes scale up and transition in color
    node.transition()
      .duration(800)
      .delay((d, i) => i * 30)
      .attr("r", d => (d.degree || 1) * 2.5 + 8);

    // Append text tags inside/beside nodes for terminal identifier look
    nodeGroup.append("text")
      .attr("dx", d => (d.degree || 1) * 2.5 + 12)
      .attr("dy", ".35em")
      .attr("font-family", "IBM Plex Mono, monospace")
      .attr("font-size", "8px")
      .attr("fill", "#8B939E")
      .text(d => `c_${d.id}`)
      .attr("pointer-events", "none");

    // Simulation tick callback
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      nodeGroup.attr("transform", d => `translate(${d.x}, ${d.y})`);
    });

    // Drag helper callbacks
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Cleanup simulation on unmount
    return () => simulation.stop();
  }, [graphData, activeCase]);

  return (
    <div className="relative w-full h-full bg-bg-base flex flex-col justify-end">
      {/* SVG Canvas */}
      <svg ref={svgRef} className="w-full h-full absolute inset-0"></svg>

      {/* Floating Graph Legend */}
      <div className="absolute top-4 left-4 bg-bg-surface/90 border border-border-hairline p-4 rounded text-xs select-none space-y-2 z-10">
        <span className="font-sans text-[10px] font-bold text-text-secondary tracking-wider block">CAMPAIGN_CLUSTERS</span>
        <div className="space-y-1.5 font-mono text-[9px] text-text-primary">
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-sev-critical"></span>
            <span>Pune Arrest Ring (C1)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-mod-network"></span>
            <span>Jamtara UPI Spoofing (C2)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-accent-signal"></span>
            <span>Mumbai Investment (C3)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-text-secondary"></span>
            <span>Unclustered Node</span>
          </div>
        </div>
        <div className="pt-2 border-t border-border-hairline font-mono text-[8px] text-text-secondary">
          Node radius correlates with case connectivity degree.
        </div>
      </div>
    </div>
  );
}
