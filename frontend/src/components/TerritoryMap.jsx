import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

export default function TerritoryMap({ mapData, parties }) {
  const svgRef = useRef(null);
  const [selectedRegion, setSelectedRegion] = useState(null);

  useEffect(() => {
    if (!mapData || !mapData.features || !svgRef.current) return;

    const width = 420;
    const height = 360;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const features = mapData.features;

    // Scale region coordinates from [0..100] to canvas
    const xScale = d3.scaleLinear().domain([0, 100]).range([30, width - 30]);
    const yScale = d3.scaleLinear().domain([0, 100]).range([30, height - 30]);

    // Draw connection web between regions
    for (let i = 0; i < features.length; i++) {
      for (let j = i + 1; j < features.length; j++) {
        const p1 = features[i].properties.center;
        const p2 = features[j].properties.center;
        if (p1 && p2) {
          const dist = Math.hypot(p1[0] - p2[0], p1[1] - p2[1]);
          if (dist < 45) {
            svg.append('line')
              .attr('x1', xScale(p1[0])).attr('y1', yScale(p1[1]))
              .attr('x2', xScale(p2[0])).attr('y2', yScale(p2[1]))
              .attr('stroke', '#252D38')
              .attr('stroke-width', 1);
          }
        }
      }
    }

    // Region nodes
    const nodeGroup = svg.selectAll('.region-node')
      .data(features)
      .enter()
      .append('g')
      .attr('class', 'region-node')
      .attr('transform', (d) => `translate(${xScale(d.properties.center[0])}, ${yScale(d.properties.center[1])})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        setSelectedRegion(d.properties);
      });

    // Outer target circle
    nodeGroup.append('circle')
      .attr('r', (d) => Math.max(10, Math.sqrt(d.properties.population / 100000) * 2.2))
      .attr('fill', '#161B22')
      .attr('stroke', '#00F0FF')
      .attr('stroke-width', 1.5);

    // Center registration cross (+)
    nodeGroup.append('line')
      .attr('x1', -4).attr('y1', 0).attr('x2', 4).attr('y2', 0)
      .attr('stroke', '#FF4500').attr('stroke-width', 1.5);
    nodeGroup.append('line')
      .attr('x1', 0).attr('y1', -4).attr('x2', 0).attr('y2', 4)
      .attr('stroke', '#FF4500').attr('stroke-width', 1.5);

    // Label
    nodeGroup.append('text')
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .attr('fill', '#8B949E')
      .attr('font-size', '9px')
      .attr('font-family', 'JetBrains Mono')
      .text((d) => d.properties.name.split(' ')[0]);

  }, [mapData]);

  return (
    <div className="vh-panel" style={{ height: '100%' }}>
      <div className="vh-corner-mark vh-tl" />
      <div className="vh-corner-mark vh-tr" />
      <div className="vh-corner-mark vh-bl" />
      <div className="vh-corner-mark vh-br" />

      <div className="vh-header-bar">
        <span className="vh-header-title">
          <span style={{ color: 'var(--accent-cyan)' }}>⬡</span> TERRITORY TOPOLOGY // REGIONS
        </span>
        <span className="badge badge-cyan">{mapData?.features?.length || 0} PROVINCES</span>
      </div>

      <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <svg ref={svgRef} width="420" height="360" viewBox="0 0 420 360" style={{ maxWidth: '100%', height: 'auto', background: '#0D0F12', border: '1px solid #252D38' }} />

        {selectedRegion && (
          <div style={{ marginTop: '10px', width: '100%', background: '#161B22', border: '1px solid #3D4856', padding: '8px 12px', fontSize: '11px' }}>
            <div style={{ color: 'var(--accent-orange)', fontWeight: 700 }}>{selectedRegion.name.toUpperCase()}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginTop: '4px', color: 'var(--text-dim)' }}>
              <div>POP: <strong style={{ color: '#fff' }}>{selectedRegion.population?.toLocaleString()}</strong></div>
              <div>SEATS: <strong style={{ color: '#fff' }}>{selectedRegion.seats}</strong></div>
              <div>URBAN: <strong style={{ color: '#fff' }}>{(selectedRegion.urbanization * 100).toFixed(0)}%</strong></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
