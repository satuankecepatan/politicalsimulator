import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function PoliticalCompass({ compassData, onUpdatePartyPosition }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!compassData || !svgRef.current) return;

    const width = 440;
    const height = 400;
    const margin = { top: 25, right: 30, bottom: 35, left: 35 };

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Scales (-100 to 100)
    const xScale = d3.scaleLinear()
      .domain([-100, 100])
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
      .domain([-100, 100])
      .range([height - margin.bottom, margin.top]); // Social: progressive (-100) vs traditional (+100)

    // Center axes (0, 0)
    svg.append('line')
      .attr('x1', xScale(-100)).attr('y1', yScale(0))
      .attr('x2', xScale(100)).attr('y2', yScale(0))
      .attr('stroke', '#3D4856').attr('stroke-width', 1.5).attr('stroke-dasharray', '3,3');

    svg.append('line')
      .attr('x1', xScale(0)).attr('y1', yScale(-100))
      .attr('x2', xScale(0)).attr('y2', yScale(100))
      .attr('stroke', '#3D4856').attr('stroke-width', 1.5).attr('stroke-dasharray', '3,3');

    // Quadrant Labels
    const labels = [
      { text: 'STATE / TRADITIONAL', x: -80, y: 88, anchor: 'start' },
      { text: 'MARKET / TRADITIONAL', x: 80, y: 88, anchor: 'end' },
      { text: 'STATE / PROGRESSIVE', x: -80, y: -90, anchor: 'start' },
      { text: 'MARKET / PROGRESSIVE', x: 80, y: -90, anchor: 'end' },
    ];
    labels.forEach((l) => {
      svg.append('text')
        .attr('x', xScale(l.x)).attr('y', yScale(l.y))
        .attr('text-anchor', l.anchor)
        .attr('fill', '#484F58')
        .attr('font-size', '9px')
        .attr('font-family', 'JetBrains Mono')
        .attr('letter-spacing', '0.05em')
        .text(l.text);
    });

    // Axis labels
    svg.append('text')
      .attr('x', width - margin.right).attr('y', yScale(0) - 6)
      .attr('text-anchor', 'end')
      .attr('fill', '#8B949E')
      .attr('font-size', '10px')
      .text('FREE MARKET →');

    svg.append('text')
      .attr('x', margin.left).attr('y', yScale(0) - 6)
      .attr('text-anchor', 'start')
      .attr('fill', '#8B949E')
      .attr('font-size', '10px')
      .text('← STATE CONTROL');

    svg.append('text')
      .attr('x', xScale(0) + 6).attr('y', margin.top)
      .attr('text-anchor', 'start')
      .attr('fill', '#8B949E')
      .attr('font-size', '10px')
      .text('↑ TRADITIONAL');

    svg.append('text')
      .attr('x', xScale(0) + 6).attr('y', height - margin.bottom + 12)
      .attr('text-anchor', 'start')
      .attr('fill', '#8B949E')
      .attr('font-size', '10px')
      .text('↓ PROGRESSIVE');

    // Cohort population density circles
    if (compassData.cohorts) {
      svg.selectAll('.cohort-dot')
        .data(compassData.cohorts)
        .enter()
        .append('circle')
        .attr('cx', (d) => xScale(d.x))
        .attr('cy', (d) => yScale(d.y))
        .attr('r', (d) => Math.max(3, Math.sqrt(d.size || 50000) / 180))
        .attr('fill', '#00F0FF')
        .attr('fill-opacity', 0.18)
        .attr('stroke', '#00F0FF')
        .attr('stroke-width', 0.6)
        .attr('stroke-opacity', 0.4);
    }

    // Party points (interactive draggable)
    if (compassData.parties) {
      const drag = d3.drag()
        .on('drag', function (event, d) {
          const newX = Math.round(Math.max(-100, Math.min(100, xScale.invert(event.x))));
          const newY = Math.round(Math.max(-100, Math.min(100, yScale.invert(event.y))));
          d3.select(this)
            .attr('transform', `translate(${xScale(newX)}, ${yScale(newY)})`);
          d._newX = newX;
          d._newY = newY;
        })
        .on('end', function (event, d) {
          if (d._newX !== undefined && onUpdatePartyPosition) {
            onUpdatePartyPosition(d.id, { economic: d._newX, social: d._newY });
          }
        });

      const partyGroup = svg.selectAll('.party-node')
        .data(compassData.parties)
        .enter()
        .append('g')
        .attr('class', 'party-node')
        .attr('transform', (d) => `translate(${xScale(d.x)}, ${yScale(d.y)})`)
        .style('cursor', 'grab')
        .call(drag);

      // Party outer diamond
      partyGroup.append('rect')
        .attr('x', -7).attr('y', -7)
        .attr('width', 14).attr('height', 14)
        .attr('transform', 'rotate(45)')
        .attr('fill', (d) => d.color || '#FF4500')
        .attr('stroke', '#000')
        .attr('stroke-width', 1.5);

      // Party label tag
      partyGroup.append('rect')
        .attr('x', 10).attr('y', -10)
        .attr('width', (d) => (d.abbr.length * 7) + 8)
        .attr('height', 16)
        .attr('fill', '#111419')
        .attr('stroke', (d) => d.color || '#FF4500')
        .attr('stroke-width', 1);

      partyGroup.append('text')
        .attr('x', 14).attr('y', 2)
        .attr('fill', '#F4F4F0')
        .attr('font-size', '9px')
        .attr('font-weight', '700')
        .attr('font-family', 'JetBrains Mono')
        .text((d) => d.abbr);
    }
  }, [compassData, onUpdatePartyPosition]);

  return (
    <div className="vh-panel" style={{ height: '100%' }}>
      <div className="vh-corner-mark vh-tl" />
      <div className="vh-corner-mark vh-tr" />
      <div className="vh-corner-mark vh-bl" />
      <div className="vh-corner-mark vh-br" />
      
      <div className="vh-header-bar">
        <span className="vh-header-title">
          <span style={{ color: 'var(--accent-orange)' }}>◈</span> POLITICAL COMPASS // ELECTORAL DENSITY
        </span>
        <span className="badge badge-cyan">DRAG NODES TO REPOSITION</span>
      </div>

      <div style={{ padding: '12px', display: 'flex', justifyContent: 'center' }}>
        <svg ref={svgRef} width="440" height="400" viewBox="0 0 440 400" style={{ maxWidth: '100%', height: 'auto', background: '#0D0F12', border: '1px solid #252D38' }} />
      </div>
    </div>
  );
}
