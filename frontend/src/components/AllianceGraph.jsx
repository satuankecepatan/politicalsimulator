import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function AllianceGraph({ parties, government }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!parties || parties.length === 0 || !svgRef.current) return;

    const width = 420;
    const height = 360;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const activeParties = parties.filter((p) => p.seats > 0 || p.in_gov);
    const n = activeParties.length;
    if (n === 0) return;

    // Arrange nodes on a circular layout for clean telemetry visualization
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - 55;

    const nodes = activeParties.map((p, i) => {
      const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
      return {
        ...p,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        angle,
      };
    });

    const nodeMap = new Map(nodes.map((d) => [d.id, d]));

    // Draw coalition alliance links
    const coalitionIds = government?.coalition || [];
    if (coalitionIds.length > 1) {
      for (let i = 0; i < coalitionIds.length; i++) {
        for (let j = i + 1; j < coalitionIds.length; j++) {
          const u = nodeMap.get(coalitionIds[i]);
          const v = nodeMap.get(coalitionIds[j]);
          if (u && v) {
            svg.append('line')
              .attr('x1', u.x).attr('y1', u.y)
              .attr('x2', v.x).attr('y2', v.y)
              .attr('stroke', '#00F0FF')
              .attr('stroke-width', 2.5)
              .attr('stroke-opacity', 0.8)
              .attr('stroke-dasharray', '4,2');
          }
        }
      }
    }

    // Nodes
    const nodeGroup = svg.selectAll('.node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', (d) => `translate(${d.x}, ${d.y})`);

    // Circle sized by parliamentary seats
    nodeGroup.append('circle')
      .attr('r', (d) => Math.max(14, Math.sqrt(d.seats || 5) * 3.5))
      .attr('fill', (d) => d.color || '#FF4500')
      .attr('stroke', (d) => (d.in_gov ? '#CCFF00' : '#252D38'))
      .attr('stroke-width', (d) => (d.in_gov ? 2.5 : 1.5));

    // Abbreviation inside circle
    nodeGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#000')
      .attr('font-size', '10px')
      .attr('font-weight', '700')
      .attr('font-family', 'JetBrains Mono')
      .text((d) => d.abbr);

    // Seats badge below
    nodeGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('y', (d) => Math.max(14, Math.sqrt(d.seats || 5) * 3.5) + 14)
      .attr('fill', '#8B949E')
      .attr('font-size', '10px')
      .attr('font-family', 'JetBrains Mono')
      .text((d) => `${d.seats} SEATS`);

  }, [parties, government]);

  return (
    <div className="vh-panel" style={{ height: '100%' }}>
      <div className="vh-corner-mark vh-tl" />
      <div className="vh-corner-mark vh-tr" />
      <div className="vh-corner-mark vh-bl" />
      <div className="vh-corner-mark vh-br" />

      <div className="vh-header-bar">
        <span className="vh-header-title">
          <span style={{ color: 'var(--accent-lime)' }}>☍</span> PARLIAMENTARY ALLIANCE NETWORK
        </span>
        <span className="badge badge-lime">
          {government?.leader ? `GOV: ${government.leader.toUpperCase()}` : 'HUNG PARLIAMENT'}
        </span>
      </div>

      <div style={{ padding: '12px', display: 'flex', justifyContent: 'center' }}>
        <svg ref={svgRef} width="420" height="360" viewBox="0 0 420 360" style={{ maxWidth: '100%', height: 'auto', background: '#0D0F12', border: '1px solid #252D38' }} />
      </div>
    </div>
  );
}
