import React, { useState } from 'react';

const QUICK_EVENTS = [
  { id: 'econ_stock_crash', name: 'Stock Market Crash' },
  { id: 'econ_mineral_boom', name: 'Strategic Mineral Boom' },
  { id: 'scn_offshore_leak', name: 'Offshore Wealth Leak' },
  { id: 'scn_defense_kickback', name: 'Defense Procurement Probe' },
  { id: 'soc_general_strike', name: 'Nationwide General Strike' },
  { id: 'sec_capital_attack', name: 'Capital Security Incident' },
  { id: 'dis_earthquake', name: 'Major Richter Earthquake' },
  { id: 'int_trade_pact', name: 'International Free Trade Pact' },
  { id: 'inst_emergency_powers', name: 'Emergency Decree Invoked' },
  { id: 'ldr_pm_resignation', name: 'Prime Minister Resignation' },
];

export default function InterventionModal({ parties, onClose, onTriggerEvent, onUpdatePartyPosition, onFork }) {
  const [selectedEvent, setSelectedEvent] = useState(QUICK_EVENTS[0].id);
  const [selectedParty, setSelectedParty] = useState(parties[0]?.id || '');
  const [econShift, setEconShift] = useState(0);
  const [socShift, setSocShift] = useState(0);

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(13, 15, 18, 0.85)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div className="vh-panel" style={{ width: '480px', maxWidth: '95vw', border: '2px solid var(--accent-orange)' }}>
        <div className="vh-stripes" />
        <div className="vh-header-bar">
          <span className="vh-header-title" style={{ color: 'var(--accent-orange)' }}>
            ⚡ EXECUTIVE INTERVENTION PROTOCOL
          </span>
          <button onClick={onClose} style={{ padding: '2px 8px', fontSize: '10px' }}>✕ CLOSE</button>
        </div>

        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* 1. Force Event */}
          <div style={{ background: 'var(--bg-slate)', padding: '12px', border: '1px solid var(--border-dim)' }}>
            <div style={{ color: 'var(--accent-yellow)', fontWeight: 700, fontSize: '12px', marginBottom: '8px' }}>
              1. INJECT HISTORICAL EVENT
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <select
                value={selectedEvent}
                onChange={(e) => setSelectedEvent(e.target.value)}
                style={{ flex: 1 }}
              >
                {QUICK_EVENTS.map((ev) => (
                  <option key={ev.id} value={ev.id}>{ev.name}</option>
                ))}
              </select>
              <button
                className="btn-primary"
                onClick={() => {
                  onTriggerEvent(selectedEvent);
                  onClose();
                }}
              >
                TRIGGER
              </button>
            </div>
          </div>

          {/* 2. Reposition Party */}
          <div style={{ background: 'var(--bg-slate)', padding: '12px', border: '1px solid var(--border-dim)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '12px', marginBottom: '8px' }}>
              2. SHIFT PARTY IDEOLOGICAL PLATFORM
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <select
                value={selectedParty}
                onChange={(e) => setSelectedParty(e.target.value)}
              >
                {parties.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.abbr})</option>
                ))}
              </select>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-dim)' }}>
                  <span>ECONOMIC AXIS:</span>
                  <span>{econShift > 0 ? `+${econShift}` : econShift}</span>
                </div>
                <input
                  type="range"
                  min="-100"
                  max="100"
                  value={econShift}
                  onChange={(e) => setEconShift(Number(e.target.value))}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-dim)' }}>
                  <span>SOCIAL AXIS:</span>
                  <span>{socShift > 0 ? `+${socShift}` : socShift}</span>
                </div>
                <input
                  type="range"
                  min="-100"
                  max="100"
                  value={socShift}
                  onChange={(e) => setSocShift(Number(e.target.value))}
                />
              </div>

              <button
                className="btn-cyan"
                onClick={() => {
                  onUpdatePartyPosition(selectedParty, { economic: econShift, social: socShift });
                  onClose();
                }}
              >
                APPLY PLATFORM SHIFT
              </button>
            </div>
          </div>

          {/* 3. Fork Alternate Timeline */}
          <div style={{ background: 'var(--bg-slate)', padding: '12px', border: '1px solid var(--border-dim)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ color: 'var(--accent-lime)', fontWeight: 700, fontSize: '12px' }}>
                3. FORK TIMELINE
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                Branch alternate history from current simulation tick.
              </div>
            </div>
            <button
              onClick={() => {
                onFork();
                onClose();
              }}
              style={{ borderColor: 'var(--accent-lime)', color: 'var(--accent-lime)' }}
            >
              ⑂ FORK
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
