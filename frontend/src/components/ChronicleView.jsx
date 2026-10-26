import React, { useState } from 'react';

export default function ChronicleView({ entries }) {
  const [filterType, setFilterType] = useState('ALL');

  const filtered = entries.filter((e) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'ELECTIONS') return e.entry_type === 'election' || e.entry_type === 'coalition';
    if (filterType === 'SCANDALS') return e.details?.category === 'scandal';
    if (filterType === 'CRISIS') return e.details?.category === 'security' || e.details?.category === 'disaster';
    if (filterType === 'PARTY') return e.entry_type === 'split' || e.entry_type === 'merger';
    return true;
  });

  return (
    <div className="vh-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="vh-corner-mark vh-tl" />
      <div className="vh-corner-mark vh-tr" />
      <div className="vh-corner-mark vh-bl" />
      <div className="vh-corner-mark vh-br" />

      <div className="vh-header-bar">
        <span className="vh-header-title">
          <span style={{ color: 'var(--accent-orange)' }}>■</span> HISTORICAL CHRONICLE // DISPATCH LOG
        </span>
        <div style={{ display: 'flex', gap: '4px' }}>
          {['ALL', 'ELECTIONS', 'SCANDALS', 'CRISIS', 'PARTY'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterType(cat)}
              style={{
                padding: '2px 8px',
                fontSize: '9px',
                backgroundColor: filterType === cat ? 'var(--accent-orange)' : 'transparent',
                color: filterType === cat ? '#000' : 'var(--text-dim)',
                borderColor: filterType === cat ? 'var(--accent-orange)' : 'var(--border-dim)',
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {filtered.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '40px' }}>
            NO DISPATCHES RECORDED FOR SELECTION.
          </div>
        ) : (
          filtered.slice().reverse().map((entry) => {
            const isElection = entry.entry_type === 'election';
            const isCoalition = entry.entry_type === 'coalition';
            const isCollapse = entry.entry_type === 'collapse';

            let badgeColor = 'badge-cyan';
            if (isElection) badgeColor = 'badge-lime';
            if (isCollapse) badgeColor = 'badge-orange';
            if (entry.details?.category === 'scandal') badgeColor = 'badge-yellow';

            return (
              <div
                key={entry.id}
                style={{
                  background: 'var(--bg-slate)',
                  border: '1px solid var(--border-dim)',
                  borderLeft: isElection ? '3px solid var(--accent-lime)' : isCollapse ? '3px solid var(--accent-orange)' : '3px solid var(--border-bright)',
                  padding: '10px 14px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--accent-yellow)', fontWeight: 700 }}>
                    {entry.date} // {entry.id}
                  </span>
                  <span className={`badge ${badgeColor}`}>{entry.entry_type.toUpperCase()}</span>
                </div>

                <div style={{ fontFamily: 'var(--font-header)', fontSize: '13px', color: 'var(--text-white)', fontWeight: 700, marginBottom: '6px' }}>
                  {entry.title}
                </div>

                {entry.prose && (
                  <div style={{ fontSize: '12px', color: 'var(--text-white)', lineHeight: 1.4, marginBottom: '8px' }}>
                    {entry.prose}
                  </div>
                )}

                {/* Structured Election Results Table */}
                {isElection && entry.details?.seats && (
                  <div style={{ marginTop: '8px', background: 'var(--bg-dark)', padding: '6px 10px', border: '1px solid var(--border-dim)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-dim)', marginBottom: '4px' }}>
                      <span>PARLIAMENTARY SEATS</span>
                      <span>TURNOUT: {(entry.details.turnout * 100).toFixed(1)}%</span>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {Object.entries(entry.details.seats).map(([pId, seats]) => (
                        <div key={pId} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}>
                          <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{pId.toUpperCase()}:</span>
                          <span>{seats} seats</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
