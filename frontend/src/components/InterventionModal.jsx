import React, { useState, useEffect } from 'react';

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

const AXES_INFO = [
  { id: 'economic', name: 'ECONOMIC', low: 'State Control', high: 'Free Market' },
  { id: 'social', name: 'SOCIAL', low: 'Progressive', high: 'Traditional' },
  { id: 'authority', name: 'AUTHORITY', low: 'Libertarian', high: 'Authoritarian' },
  { id: 'identity', name: 'IDENTITY', low: 'Cosmopolitan', high: 'Nationalist' },
  { id: 'secularism', name: 'SECULARISM', low: 'Secular', high: 'Clerical' },
  { id: 'environment', name: 'ENVIRONMENT', low: 'Ecology First', high: 'Growth First' },
  { id: 'trust', name: 'TRUST', low: 'Anti-System', high: 'Institutionalist' },
];

const PALETTE = ['#FF4500', '#00F0FF', '#CCFF00', '#FFD700', '#E63946', '#1D3557', '#9D4EDD', '#2A9D8F'];

export default function InterventionModal({ parties, onClose, onTriggerEvent, onUpdateParty, onFork }) {
  const [selectedEvent, setSelectedEvent] = useState(QUICK_EVENTS[0].id);
  const [selectedPartyId, setSelectedPartyId] = useState(parties[0]?.id || '');

  // Party editing state
  const [partyName, setPartyName] = useState('');
  const [partyAbbr, setPartyAbbr] = useState('');
  const [partyColor, setPartyColor] = useState('#FF4500');
  const [partyIdeology, setPartyIdeology] = useState({});

  useEffect(() => {
    const p = parties.find((item) => item.id === selectedPartyId) || parties[0];
    if (p) {
      setSelectedPartyId(p.id);
      setPartyName(p.name || '');
      setPartyAbbr(p.abbr || p.abbreviation || '');
      setPartyColor(p.color || '#FF4500');
      setPartyIdeology({
        economic: p.ideology?.economic ?? 0,
        social: p.ideology?.social ?? 0,
        authority: p.ideology?.authority ?? 0,
        identity: p.ideology?.identity ?? 0,
        secularism: p.ideology?.secularism ?? 0,
        environment: p.ideology?.environment ?? 0,
        trust: p.ideology?.trust ?? 0,
      });
    }
  }, [selectedPartyId, parties]);

  const handleAxisChange = (axisId, val) => {
    setPartyIdeology((prev) => ({
      ...prev,
      [axisId]: Number(val),
    }));
  };

  const handleApplyPartyChanges = () => {
    if (!selectedPartyId) return;
    onUpdateParty(selectedPartyId, {
      name: partyName,
      abbreviation: partyAbbr,
      color: partyColor,
      position: partyIdeology,
    });
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(13, 15, 18, 0.88)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <div
        className="vh-panel"
        style={{
          width: '580px',
          maxWidth: '96vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          border: '2px solid var(--accent-orange)',
        }}
      >
        <div className="vh-stripes" />
        <div className="vh-header-bar">
          <span className="vh-header-title" style={{ color: 'var(--accent-orange)' }}>
            ⚡ EXECUTIVE INTERVENTION & PLATFORM REVISION
          </span>
          <button onClick={onClose} style={{ padding: '2px 8px', fontSize: '10px' }}>✕ CLOSE</button>
        </div>

        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto' }}>
          
          {/* 1. Force Event Injection */}
          <div style={{ background: 'var(--bg-slate)', padding: '12px', border: '1px solid var(--border-dim)' }}>
            <div style={{ color: 'var(--accent-yellow)', fontWeight: 700, fontSize: '11px', marginBottom: '8px' }}>
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

          {/* 2. Full Party & Ideological Repositioning */}
          <div style={{ background: 'var(--bg-slate)', padding: '12px', border: '1px solid var(--border-dim)' }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '11px', marginBottom: '8px' }}>
              2. EDIT PARTY IDENTITY & 7-AXIS IDEOLOGICAL PLATFORM
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '10px', color: 'var(--text-dim)', display: 'block', marginBottom: '3px' }}>
                  TARGET PARTY:
                </label>
                <select
                  value={selectedPartyId}
                  onChange={(e) => setSelectedPartyId(e.target.value)}
                  style={{ width: '100%' }}
                >
                  {parties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.abbr || p.abbreviation})
                    </option>
                  ))}
                </select>
              </div>

              {/* Name & Abbreviation fields */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '10px', color: 'var(--text-dim)', display: 'block', marginBottom: '2px' }}>
                    PARTY NAME:
                  </label>
                  <input
                    type="text"
                    value={partyName}
                    onChange={(e) => setPartyName(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '10px', color: 'var(--text-dim)', display: 'block', marginBottom: '2px' }}>
                    ABBREVIATION:
                  </label>
                  <input
                    type="text"
                    maxLength={8}
                    value={partyAbbr}
                    onChange={(e) => setPartyAbbr(e.target.value.toUpperCase())}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              {/* Color Chooser */}
              <div>
                <label style={{ fontSize: '10px', color: 'var(--text-dim)', display: 'block', marginBottom: '3px' }}>
                  PARTY COLOR:
                </label>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <input
                    type="color"
                    value={partyColor.startsWith('#') ? partyColor : `#${partyColor}`}
                    onChange={(e) => setPartyColor(e.target.value)}
                    style={{ width: '32px', height: '26px', border: 'none', background: 'transparent', cursor: 'pointer' }}
                  />
                  <input
                    type="text"
                    value={partyColor}
                    onChange={(e) => setPartyColor(e.target.value)}
                    style={{ width: '80px', fontSize: '11px' }}
                  />
                  <div style={{ display: 'flex', gap: '4px', marginLeft: '6px' }}>
                    {PALETTE.map((c) => (
                      <div
                        key={c}
                        onClick={() => setPartyColor(c)}
                        style={{
                          width: '16px',
                          height: '16px',
                          backgroundColor: c,
                          cursor: 'pointer',
                          border: partyColor === c ? '2px solid #FFF' : '1px solid #000',
                        }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Ideology Sliders across all axes */}
              <div style={{ borderTop: '1px solid var(--border-dim)', paddingTop: '8px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-dim)', fontWeight: 700, display: 'block', marginBottom: '6px' }}>
                  IDEOLOGICAL PLATFORM COORDINATES [-100..+100]:
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto', paddingRight: '4px' }}>
                  {AXES_INFO.map((axis) => {
                    const val = partyIdeology[axis.id] ?? 0;
                    return (
                      <div key={axis.id}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-dim)' }}>
                          <span>{axis.name} ({axis.low})</span>
                          <span style={{ color: val > 0 ? 'var(--accent-orange)' : val < 0 ? 'var(--accent-cyan)' : '#FFF', fontWeight: 700 }}>
                            {val > 0 ? `+${val}` : val}
                          </span>
                          <span>({axis.high})</span>
                        </div>
                        <input
                          type="range"
                          min="-100"
                          max="100"
                          value={val}
                          onChange={(e) => handleAxisChange(axis.id, e.target.value)}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>

              <button
                className="btn-cyan"
                onClick={handleApplyPartyChanges}
                style={{ marginTop: '4px' }}
              >
                APPLY PARTY REVISIONS
              </button>
            </div>
          </div>

          {/* 3. Fork Alternate Timeline */}
          <div style={{ background: 'var(--bg-slate)', padding: '12px', border: '1px solid var(--border-dim)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ color: 'var(--accent-lime)', fontWeight: 700, fontSize: '11px' }}>
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
