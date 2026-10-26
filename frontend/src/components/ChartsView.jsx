import React, { useState, useEffect, useRef } from 'react';
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

export default function ChartsView({ historyEntries = [], parties = [], status = null }) {
  const [metricTab, setMetricTab] = useState('POLLING'); // 'POLLING' | 'MACRO' | 'ELECTIONS'
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  const timeSeries = status?.time_series || [];
  const elections = (historyEntries || []).filter((e) => e.entry_type === 'election');
  const analytics = status?.analytics || {};
  const economy = status?.economy || {};

  useEffect(() => {
    if (!chartRef.current) return;

    let labels = [];
    let datasets = [];
    let yTitle = '% SHARE';
    let yMax = undefined;

    const partyColorMap = new Map((parties || []).map((p) => [p.id, p.color || '#FF4500']));

    if (metricTab === 'POLLING') {
      if (timeSeries.length > 0) {
        labels = timeSeries.map((t) => t.date);
        datasets = (parties || []).map((p) => {
          const color = p.color || '#00F0FF';
          return {
            label: `${p.abbr || p.abbreviation || p.id} (%)`,
            data: timeSeries.map((t) => Math.round((t.poll?.[p.id] || 0) * 1000) / 10),
            borderColor: color,
            backgroundColor: color,
            tension: 0.25,
            pointRadius: timeSeries.length > 24 ? 1 : 3,
            borderWidth: 2,
          };
        });
        yMax = 60;
        yTitle = 'POLLING INTENT (%)';
      }
    } else if (metricTab === 'MACRO') {
      if (timeSeries.length > 0) {
        labels = timeSeries.map((t) => t.date);
        datasets = [
          {
            label: 'GDP GROWTH (%)',
            data: timeSeries.map((t) => {
              const val = t.economy?.growth ?? t.economy?.gdp_growth ?? 0;
              return Math.round((Math.abs(val) < 1 ? val * 100 : val) * 10) / 10;
            }),
            borderColor: '#00F0FF',
            backgroundColor: '#00F0FF',
            tension: 0.25,
            pointRadius: timeSeries.length > 24 ? 1 : 3,
            borderWidth: 2,
          },
          {
            label: 'INFLATION (%)',
            data: timeSeries.map((t) => {
              const val = t.economy?.inflation ?? 0;
              return Math.round((Math.abs(val) < 1 ? val * 100 : val) * 10) / 10;
            }),
            borderColor: '#FF4500',
            backgroundColor: '#FF4500',
            tension: 0.25,
            pointRadius: timeSeries.length > 24 ? 1 : 3,
            borderWidth: 2,
          },
          {
            label: 'UNEMPLOYMENT (%)',
            data: timeSeries.map((t) => {
              const val = t.economy?.unemployment ?? 0;
              return Math.round((Math.abs(val) < 1 ? val * 100 : val) * 10) / 10;
            }),
            borderColor: '#FFD700',
            backgroundColor: '#FFD700',
            tension: 0.25,
            pointRadius: timeSeries.length > 24 ? 1 : 3,
            borderWidth: 2,
          },
        ];
        yTitle = 'MACROECONOMIC RATE (%)';
      }
    } else if (metricTab === 'ELECTIONS') {
      if (elections.length > 0) {
        labels = elections.map((e) => e.date);
        const partyIds = Array.from(new Set(elections.flatMap((e) => Object.keys(e.details?.shares || {}))));
        datasets = partyIds.map((pId) => {
          const color = partyColorMap.get(pId) || '#CCFF00';
          return {
            label: pId.toUpperCase(),
            data: elections.map((e) => Math.round((e.details?.shares?.[pId] || 0) * 1000) / 10),
            borderColor: color,
            backgroundColor: color,
            tension: 0.2,
            pointRadius: 5,
            borderWidth: 2.5,
          };
        });
        yMax = 60;
        yTitle = 'ELECTION VOTE SHARE (%)';
      }
    }

    if (chartInstance.current) {
      chartInstance.current.destroy();
      chartInstance.current = null;
    }

    // Only instantiate chart if we have labels and datasets
    if (labels.length > 0 && datasets.length > 0) {
      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new ChartJS(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 300 },
          plugins: {
            legend: {
              position: 'top',
              labels: {
                color: '#F4F4F0',
                font: { family: 'JetBrains Mono', size: 10, weight: '700' },
                boxWidth: 10,
                padding: 12,
              },
            },
            tooltip: {
              backgroundColor: '#111419',
              titleColor: '#00F0FF',
              bodyColor: '#F4F4F0',
              borderColor: '#3D4856',
              borderWidth: 1,
              titleFont: { family: 'JetBrains Mono', size: 11 },
              bodyFont: { family: 'JetBrains Mono', size: 10 },
            },
          },
          scales: {
            x: {
              grid: { color: '#202630' },
              ticks: { color: '#8B949E', font: { family: 'JetBrains Mono', size: 9 }, maxRotation: 45 },
            },
            y: {
              max: yMax,
              grid: { color: '#202630' },
              ticks: {
                color: '#8B949E',
                font: { family: 'JetBrains Mono', size: 9 },
                callback: (v) => `${v}%`,
              },
              title: {
                display: true,
                text: yTitle,
                color: '#6E7681',
                font: { family: 'JetBrains Mono', size: 9 },
              },
            },
          },
        },
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
        chartInstance.current = null;
      }
    };
  }, [metricTab, timeSeries, elections, parties]);

  const hasChartData =
    (metricTab === 'POLLING' && timeSeries.length > 0) ||
    (metricTab === 'MACRO' && timeSeries.length > 0) ||
    (metricTab === 'ELECTIONS' && elections.length > 0);

  return (
    <div className="vh-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '0' }}>
      <div className="vh-corner-mark vh-tl" />
      <div className="vh-corner-mark vh-tr" />
      <div className="vh-corner-mark vh-bl" />
      <div className="vh-corner-mark vh-br" />

      {/* Header bar with Tab switcher */}
      <div className="vh-header-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="vh-header-title">
          <span style={{ color: 'var(--accent-cyan)' }}>∿</span> ANALYTICS // TIME-SERIES & INSTITUTIONAL INDICES
        </span>

        {/* View Mode Tabs */}
        <div style={{ display: 'flex', gap: '4px' }}>
          {[
            { id: 'POLLING', label: 'POLLING TRENDS' },
            { id: 'MACRO', label: 'MACROECONOMY' },
            { id: 'ELECTIONS', label: 'ELECTION RETURNS' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setMetricTab(tab.id)}
              style={{
                padding: '3px 8px',
                fontSize: '9px',
                border: metricTab === tab.id ? '1px solid var(--accent-orange)' : '1px solid var(--border-dim)',
                background: metricTab === tab.id ? 'var(--bg-slate)' : 'transparent',
                color: metricTab === tab.id ? 'var(--accent-orange)' : 'var(--text-dim)',
                fontWeight: 700,
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Political Science & Macroeconomic KPI Telemetry Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '8px',
          padding: '10px 14px',
          background: 'var(--bg-slate)',
          borderBottom: '1px solid var(--border-dim)',
        }}
      >
        <div style={{ borderLeft: '2px solid var(--accent-cyan)', paddingLeft: '8px' }}>
          <div style={{ fontSize: '9px', color: 'var(--text-dim)' }}>EFFECTIVE PARTIES (ENP)</div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
            V: {analytics.enp_v ?? '—'} / S: {analytics.enp_s ?? '—'}
          </div>
          <div style={{ fontSize: '8px', color: 'var(--text-dim)' }}>Laakso-Taagepera</div>
        </div>

        <div style={{ borderLeft: '2px solid var(--accent-orange)', paddingLeft: '8px' }}>
          <div style={{ fontSize: '9px', color: 'var(--text-dim)' }}>GALLAGHER INDEX</div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-orange)' }}>
            {analytics.gallagher !== undefined ? `${analytics.gallagher}%` : '—'}
          </div>
          <div style={{ fontSize: '8px', color: 'var(--text-dim)' }}>Disproportionality</div>
        </div>

        <div style={{ borderLeft: '2px solid var(--accent-lime)', paddingLeft: '8px' }}>
          <div style={{ fontSize: '9px', color: 'var(--text-dim)' }}>DALTON POLARIZATION</div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-lime)' }}>
            {analytics.polarization !== undefined ? analytics.polarization : '—'}
          </div>
          <div style={{ fontSize: '8px', color: 'var(--text-dim)' }}>Ideological Spread</div>
        </div>

        <div style={{ borderLeft: '2px solid var(--accent-yellow)', paddingLeft: '8px' }}>
          <div style={{ fontSize: '9px', color: 'var(--text-dim)' }}>GOV STABILITY</div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-yellow)' }}>
            {analytics.stability !== undefined ? `${analytics.stability}%` : '—'}
          </div>
          <div style={{ fontSize: '8px', color: 'var(--text-dim)' }}>Coalition Security</div>
        </div>

        <div style={{ borderLeft: '2px solid #FFF', paddingLeft: '8px' }}>
          <div style={{ fontSize: '9px', color: 'var(--text-dim)' }}>GDP / INFLATION</div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#FFF' }}>
            {economy.gdp_growth !== undefined ? `${(economy.gdp_growth * 100).toFixed(1)}%` : '—'} / {economy.inflation !== undefined ? `${(economy.inflation * 100).toFixed(1)}%` : '—'}
          </div>
          <div style={{ fontSize: '8px', color: 'var(--text-dim)' }}>Macro Climate</div>
        </div>
      </div>

      {/* Main Chart Area */}
      <div style={{ flex: 1, padding: '14px', position: 'relative', display: 'flex', flexDirection: 'column' }}>
        {hasChartData ? (
          <div style={{ flex: 1, position: 'relative' }}>
            <canvas ref={chartRef} />
          </div>
        ) : (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#0D0F12',
              border: '1px dashed var(--border-dim)',
              padding: '24px',
              textAlign: 'center',
            }}
          >
            <div style={{ color: 'var(--accent-yellow)', fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>
              ⚠ NO TELEMETRY DATA AVAILABLE FOR {metricTab}
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: '11px', maxWidth: '420px', lineHeight: 1.5 }}>
              {metricTab === 'ELECTIONS'
                ? 'No quadrennial elections have concluded yet in this timeline. Elections occur every 48 months or upon coalition collapse / vote of no confidence. Step the simulation forward to reach the next election cycle.'
                : 'Monthly polling samples are recorded upon each simulation tick. Press STEP or PLAY in the control header to commence data generation.'}
            </div>
          </div>
        )}
      </div>

      {/* Party Status Standing Footer */}
      <div
        style={{
          borderTop: '1px solid var(--border-dim)',
          background: 'var(--bg-slate)',
          padding: '8px 14px',
          display: 'flex',
          gap: '12px',
          overflowX: 'auto',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '9px', color: 'var(--text-dim)', fontWeight: 700, flexShrink: 0 }}>
          CONTESTING PARTIES:
        </span>
        {parties.map((p) => {
          const pollShare = status?.poll?.[p.id] ? Math.round(status.poll[p.id] * 1000) / 10 : 0;
          return (
            <div
              key={p.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '10px',
                background: 'var(--bg-dark)',
                padding: '3px 8px',
                border: `1px solid ${p.color || '#333'}`,
                flexShrink: 0,
              }}
            >
              <div style={{ width: '8px', height: '8px', backgroundColor: p.color }} />
              <span style={{ fontWeight: 700, color: '#FFF' }}>{p.abbr || p.abbreviation}</span>
              <span style={{ color: 'var(--accent-cyan)' }}>{pollShare}%</span>
              <span style={{ color: 'var(--text-dim)', fontSize: '9px' }}>({p.seats} seats)</span>
              {p.in_gov && (
                <span className="badge badge-orange" style={{ padding: '0 4px', fontSize: '8px' }}>
                  {p.is_leader ? 'LEADER' : 'GOV'}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
