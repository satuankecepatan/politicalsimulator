import React, { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function ChartsView({ historyEntries, parties }) {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // Filter election records to build vote share trajectories
    const elections = historyEntries.filter((e) => e.entry_type === 'election');
    if (elections.length === 0) return;

    const labels = elections.map((e) => e.date);
    const partyColorMap = new Map((parties || []).map((p) => [p.id, p.color || '#FF4500']));

    const partyIds = Array.from(new Set(elections.flatMap((e) => Object.keys(e.details?.shares || {}))));

    const datasets = partyIds.map((pId) => {
      const color = partyColorMap.get(pId) || '#CCFF00';
      return {
        label: pId.toUpperCase(),
        data: elections.map((e) => Math.round((e.details?.shares?.[pId] || 0) * 1000) / 10),
        borderColor: color,
        backgroundColor: color,
        tension: 0.2,
        pointRadius: 4,
        pointHoverRadius: 6,
      };
    });

    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    chartInstance.current = new ChartJS(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#F4F4F0',
              font: { family: 'JetBrains Mono', size: 10 },
              boxWidth: 12,
            },
          },
          tooltip: {
            backgroundColor: '#111419',
            titleColor: '#00F0FF',
            bodyColor: '#F4F4F0',
            borderColor: '#3D4856',
            borderWidth: 1,
            titleFont: { family: 'JetBrains Mono' },
            bodyFont: { family: 'JetBrains Mono' },
          },
        },
        scales: {
          x: {
            grid: { color: '#252D38' },
            ticks: { color: '#8B949E', font: { family: 'JetBrains Mono', size: 9 } },
          },
          y: {
            min: 0,
            max: 60,
            grid: { color: '#252D38' },
            ticks: {
              color: '#8B949E',
              font: { family: 'JetBrains Mono', size: 9 },
              callback: (v) => `${v}%`,
            },
          },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [historyEntries, parties]);

  return (
    <div className="vh-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="vh-corner-mark vh-tl" />
      <div className="vh-corner-mark vh-tr" />
      <div className="vh-corner-mark vh-bl" />
      <div className="vh-corner-mark vh-br" />

      <div className="vh-header-bar">
        <span className="vh-header-title">
          <span style={{ color: 'var(--accent-cyan)' }}>∿</span> ELECTORAL TRENDS // VOTE SHARE TRAJECTORY
        </span>
        <span className="badge badge-cyan">TIME-SERIES</span>
      </div>

      <div style={{ flex: 1, padding: '14px', position: 'relative' }}>
        <canvas ref={chartRef} />
      </div>
    </div>
  );
}
