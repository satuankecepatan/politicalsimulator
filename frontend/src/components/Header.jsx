import React from 'react';

export default function Header({
  session,
  status,
  isPlaying,
  onPlay,
  onPause,
  onStep,
  onRunYears,
  speedMs,
  onSetSpeed,
  onOpenIntervention,
  onOpenWizard,
  onSave,
  onExport,
}) {
  const dateStr = status?.date || 'PRE-INIT';
  const tick = status?.tick ?? 0;
  const gov = status?.government;
  const econ = status?.economy;

  return (
    <header className="vh-panel" style={{ borderBottom: '2px solid var(--accent-orange)' }}>
      <div className="vh-stripes" />
      <div style={{ padding: '10px 18px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
        
        {/* Title & Telemetry */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: 'var(--accent-orange)', fontWeight: 900, fontSize: '15px', letterSpacing: '0.12em' }}>POLSIM</span>
              <span className="badge badge-cyan">SYS.VER.0.1</span>
              {session?.name && (
                <span style={{ color: 'var(--text-white)', fontWeight: 600, fontSize: '13px' }}>
                  // {session.name}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: '12px', color: 'var(--text-dim)', fontSize: '11px', marginTop: '2px' }}>
              <span>DATE: <strong style={{ color: 'var(--accent-yellow)' }}>{dateStr}</strong></span>
              <span>TICK: <strong style={{ color: 'var(--text-white)' }}>{tick}</strong></span>
              {gov?.leader && (
                <span>GOV: <strong style={{ color: 'var(--accent-lime)' }}>{gov.leader.toUpperCase()}</strong> ({gov.coalition?.join('+') || 'SOLO'})</span>
              )}
              {econ && (
                <span>GDP: <strong style={{ color: econ.growth >= 0 ? 'var(--accent-lime)' : 'var(--accent-orange)' }}>{econ.growth}%</strong> | UNEMP: <strong>{econ.unemployment}%</strong></span>
              )}
            </div>
          </div>
        </div>

        {/* Run Controls */}
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          {isPlaying ? (
            <button onClick={onPause} className="btn-primary" style={{ backgroundColor: 'var(--accent-yellow)', borderColor: 'var(--accent-yellow)' }}>
              ❚❚ PAUSE
            </button>
          ) : (
            <button onClick={onPlay} className="btn-primary">
              ► PLAY
            </button>
          )}

          <button onClick={onStep} disabled={isPlaying} title="Advance 1 Month">
            ►| STEP
          </button>

          <button onClick={() => onRunYears(1)} disabled={isPlaying} title="Simulate 1 Year Instantly">
            +1 YR
          </button>

          <button onClick={() => onRunYears(5)} disabled={isPlaying} title="Simulate 5 Years Instantly">
            +5 YRS
          </button>

          {/* Speed Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', borderLeft: '1px solid var(--border-bright)', paddingLeft: '8px' }}>
            <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>SPD:</span>
            {[
              { label: '1x', ms: 500 },
              { label: '2x', ms: 250 },
              { label: '5x', ms: 100 },
              { label: 'MAX', ms: 25 },
            ].map((s) => (
              <button
                key={s.label}
                onClick={() => onSetSpeed(s.ms)}
                style={{
                  padding: '4px 8px',
                  fontSize: '10px',
                  backgroundColor: speedMs === s.ms ? 'var(--accent-cyan)' : 'transparent',
                  color: speedMs === s.ms ? '#000' : 'var(--text-white)',
                  borderColor: speedMs === s.ms ? 'var(--accent-cyan)' : 'var(--border-dim)',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* Action Modals & Tools */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', borderLeft: '1px solid var(--border-bright)', paddingLeft: '8px' }}>
            <button onClick={onOpenIntervention} className="btn-cyan">
              ⚡ INTERVENE
            </button>
            <button onClick={onSave} title="Save to SQLite">
              💾 SAVE
            </button>
            <button onClick={() => onExport('markdown')} title="Download Markdown Chronicle">
              ↓ CHRONICLE
            </button>
            <button onClick={onOpenWizard} style={{ borderColor: 'var(--border-bright)' }}>
              ⚙ CONFIG
            </button>
          </div>

        </div>

      </div>
    </header>
  );
}
