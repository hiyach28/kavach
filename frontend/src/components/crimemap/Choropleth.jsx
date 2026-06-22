import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useCase } from '../../context/CaseContext';
import DistrictTooltip from './DistrictTooltip';

export default function Choropleth() {
  const svgRef = useRef(null);
  const { districts, selectDistrict, activeDistrict } = useCase();
  const [geoData, setGeoData] = useState(null);
  
  // Tooltip local state
  const [tooltip, setTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    data: null
  });

  // Fetch GeoJSON
  useEffect(() => {
    fetch('/india-districts.geojson')
      .then(res => res.json())
      .then(data => {
        setGeoData(data);
      })
      .catch(err => {
        console.error("Failed to load India GeoJSON data", err);
      });
  }, []);

  // Render D3 Map
  useEffect(() => {
    if (!svgRef.current || !geoData || !districts) return;

    const width = svgRef.current.clientWidth || 600;
    const height = svgRef.current.clientHeight || 500;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // D3 projection tailored for India boundaries
    const projection = d3.geoMercator()
      .center([78.9629, 22.5])
      .scale(width > 500 ? 900 : 700)
      .translate([width / 2, height / 2]);

    const pathGenerator = d3.geoPath().projection(projection);

    // Color interpolation function
    const getFillColor = (d) => {
      // Find matching district statistics by state name (since Gist maps states)
      const stateName = d.properties.state_name || d.properties.ST_NM;
      if (!stateName) return '#1C2229';

      const match = districts.find(dist => 
        dist.name.toLowerCase() === stateName.toLowerCase() ||
        (dist.state && dist.state.toLowerCase() === stateName.toLowerCase())
      );

      if (!match || match.complaint_count === 0) {
        return '#1C2229'; // Lighter surface color for zero stats
      }

      // Linear scale from light amber to critical red based on priority_score (0-100)
      const score = match.priority_score || 0;
      return d3.interpolateRgb('#BA7517', '#E24B4A')(score / 100);
    };

    // Draw Map Paths
    svg.append("g")
      .attr("class", "map-layer")
      .selectAll("path")
      .data(geoData.features)
      .enter()
      .append("path")
      .attr("d", pathGenerator)
      .attr("class", "map-district")
      .attr("fill", getFillColor)
      .attr("stroke", "#2A3038")
      .attr("stroke-width", 0.7)
      .on("mouseover", (event, d) => {
        const stateName = d.properties.state_name || d.properties.ST_NM;
        const match = districts.find(dist => 
          dist.name.toLowerCase() === stateName.toLowerCase() ||
          (dist.state && dist.state.toLowerCase() === stateName.toLowerCase())
        ) || { name: stateName, state: stateName, complaint_count: 0, estimated_loss: 0, priority_score: 0, campaigns_count: 0 };

        const [x, y] = d3.pointer(event, svgRef.current);

        setTooltip({
          show: true,
          x: x + 15,
          y: y - 10,
          data: match
        });
      })
      .on("mousemove", (event) => {
        const [x, y] = d3.pointer(event, svgRef.current);
        setTooltip(prev => ({
          ...prev,
          x: x + 15,
          y: y - 10
        }));
      })
      .on("mouseout", () => {
        setTooltip(prev => ({ ...prev, show: false }));
      })
      .on("click", (event, d) => {
        const stateName = d.properties.state_name || d.properties.ST_NM;
        selectDistrict(stateName);
      });

  }, [geoData, districts, activeDistrict]);

  return (
    <div className="relative w-full h-full bg-bg-base flex flex-col justify-end">
      {/* SVG Canvas */}
      <svg ref={svgRef} className="w-full h-full absolute inset-0"></svg>

      {/* Floating Tooltip overlay */}
      {tooltip.show && (
        <DistrictTooltip x={tooltip.x} y={tooltip.y} data={tooltip.data} />
      )}

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-bg-surface/90 border border-border-hairline p-4 rounded text-xs select-none space-y-2 z-10">
        <span className="font-condensed text-[10px] font-bold text-text-secondary tracking-wider block">PRIORITY_SCALING</span>
        <div className="flex items-center space-x-1">
          <span className="text-[9px] font-mono text-text-secondary">LOW</span>
          <div className="h-2 w-24 bg-gradient-to-r from-[#BA7517] to-[#E24B4A] border border-border-hairline rounded"></div>
          <span className="text-[9px] font-mono text-text-secondary">CRITICAL</span>
        </div>
        <div className="pt-2 border-t border-border-hairline font-mono text-[8px] text-text-secondary">
          Priority formula integrates volume, loss growth, and cluster count.
        </div>
      </div>
    </div>
  );
}
