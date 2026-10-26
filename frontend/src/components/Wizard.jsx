import React, { useState, useEffect } from 'react';

const AXES_DEFINITIONS = [
  { id: 'economic', name: 'ECONOMIC', low: 'STATE CONTROL', high: 'FREE MARKET' },
  { id: 'social', name: 'SOCIAL', low: 'PROGRESSIVE', high: 'TRADITIONAL' },
  { id: 'authority', name: 'AUTHORITY', low: 'LIBERTARIAN', high: 'AUTHORITARIAN' },
  { id: 'identity', name: 'IDENTITY', low: 'COSMOPOLITAN', high: 'NATIONALIST' },
  { id: 'secularism', name: 'SECULARISM', low: 'SECULAR', high: 'CLERICAL' },
  { id: 'environment', name: 'ENVIRONMENT', low: 'ECOLOGY FIRST', high: 'GROWTH FIRST' },
  { id: 'trust', name: 'TRUST', low: 'ANTI-SYSTEM', high: 'INSTITUTIONALIST' },
];

const PALETTE = ['#FF4500', '#00F0FF', '#CCFF00', '#FFD700', '#E63946', '#1D3557', '#9D4EDD', '#2A9D8F'];

export default function Wizard({ presets, onLaunch, onClose }) {
  const [tab, setTab] = useState('INSTITUTIONS'); // 'INSTITUTIONS' | 'PARTIES'
  const [selectedPreset, setSelectedPreset] = useState(presets[0] || 'industrial_democracy');
  const [countryName, setCountryName] = useState('Republic of Veridia');
  const [population, setPopulation] = useState(12000000);
  const [regions, setRegions] = useState(8);
  const [electoralSystem, setElectoralSystem] = useState('pr');
  const [seats, setSeats] = useState(150);
  const [threshold, setThreshold] = useState(0.05);
  const [chaosLevel, setChaosLevel] = useState(1.0);
  const [seed, setSeed] = useState(42);

  const [parties, setParties] = useState([]);
  const [selectedPartyIndex, setSelectedPartyIndex] = useState(0);

  // Load preset scenario configuration on mount or preset change
  useEffect(() => {
    fetch(`/api/presets/${selectedPreset}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.country) {
          setCountryName(data.country.name || 'Republic of Veridia');
          setPopulation(data.country.population || 12000000);
          setRegions(data.country.n_regions || 8);
        }
        if (data.institutions) {
          setElectoralSystem(data.institutions.electoral_system || 'pr');
          setSeats(data.institutions.seats || 150);
          setThreshold(data.institutions.threshold || 0.05);
        }
        if (data.events) {
          setChaosLevel(data.events.chaos_level || 1.0);
        }
        if (data.parties && Array.isArray(data.parties)) {
          setParties(
            data.parties.map((p) => ({
              id: p.id,
              name: p.name,
              abbreviation: p.abbreviation || p.abbr,
              color: p.color || '#FF4500',
              ideology: {
                economic: p.ideology?.economic ?? 0,
                social: p.ideology?.social ?? 0,
                authority: p.ideology?.authority ?? 0,
                identity: p.ideology?.identity ?? 0,
                secularism: p.ideology?.secularism ?? 0,
                environment: p.ideology?.environment ?? 0,
                trust: p.ideology?.trust ?? 0,
              },
              pragmatism: p.pragmatism ?? 0.5,
              populism: p.populism ?? 0.2,
              cohesion: p.cohesion ?? 0.7,
            }))
          );
          setSelectedPartyIndex(0);
        }
      })
      .catch((err) => console.error('Failed to load preset:', err));
  }, [selectedPreset]);

  const activeParty = parties[selectedPartyIndex] || null;

  const updateActiveParty = (key, value) => {
    setParties((prev) => {
      const updated = [...prev];
      updated[selectedPartyIndex] = {
        ...updated[selectedPartyIndex],
        [key]: value,
      };
      return updated;
    });
  };

  const updateActivePartyIdeology = (axisId, value) => {
    setParties((prev) => {
      const updated = [...prev];
      const cur = updated[selectedPartyIndex];
      updated[selectedPartyIndex] = {
        ...cur,
        ideology: {
          ...cur.ideology,
          [axisId]: Number(value),
        },
      };
      return updated;
    });
  };

  const handleAddParty = () => {
    const idNum = parties.length + 1;
    const color = PALETTE[(parties.length) % PALETTE.length];
    const newP = {
      id: `party_${Date.now().toString().slice(-5)}`,
      name: `New Democratic Front ${idNum}`,
      abbreviation: `NDF${idNum}`,
      color: color,
      ideology: {
        economic: 0,
        social: 0,
        authority: 0,
        identity: 0,
        secularism: 0,
        environment: 0,
        trust: 0,
      },
      pragmatism: 0.5,
      populism: 0.2,
      cohesion: 0.7,
    };
    setParties((prev) => [...prev, newP]);
    setSelectedPartyIndex(parties.length);
  };

  const handleRemoveParty = (indexToRemove) => {
    if (parties.length <= 2) {
      alert('Simulation requires at least 2 contesting parties.');
      return;
    }
    setParties((prev) => prev.filter((_, i) => i !== indexToRemove));
    setSelectedPartyIndex((prev) => (prev >= indexToRemove ? Math.max(0, prev - 1) : prev));
  };

  const handleLaunch = () => {
    onLaunch({
      preset: selectedPreset,
      seed: Number(seed),
      country: {
        name: countryName,
        population: Number(population),
        n_regions: Number(regions),
      },
      institutions: {
        electoral_system: electoralSystem,
        seats: Number(seats),
        threshold: Number(threshold),
      },
      events: {
        chaos_level: Number(chaosLevel),
      },
      parties: parties,
    });
  };

  const handleRandomize = () => {
    const randomPreset = presets[Math.floor(Math.random() * presets.length)] || 'industrial_democracy';
    setSelectedPreset(randomPreset);
    setSeed(Math.floor(Math.random() * 999999));
    setSeats(Math.floor(Math.random() * 150) + 60);
    setChaosLevel(Math.round(Math.random() * 2.0 * 10) / 10);
    const systems = ['pr', 'fptp', 'mixed', 'two_round'];
    setElectoralSystem(systems[Math.floor(Math.random() * systems.length)]);

    // Jitter party positions
    setParties((prev) =>
      prev.map((p) => ({
        ...p,
        ideology: {
          economic: Math.round((Math.random() * 160 - 80)),
          social: Math.round((Math.random() * 160 - 80)),
          authority: Math.round((Math.random() * 160 - 80)),
          identity: Math.round((Math.random() * 160 - 80)),
          secularism: Math.round((Math.random() * 160 - 80)),
          environment: Math.round((Math.random() * 160 - 80)),
          trust: Math.round((Math.random() * 160 - 80)),
        },
      }))
    );
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(13, 15, 18, 0.92)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <div
        className="vh-panel"
        style={{
          width: '780px',
          maxWidth: '96vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          border: '2px solid var(--accent-cyan)',
        }}
      >
        <div className="vh-stripes" />
        <div className="vh-header-bar">
          <span className="vh-header-title">
            <span style={{ color: 'var(--accent-cyan)' }}>⚙</span> SCENARIO & PARTY INITIALIZATION WIZARD
          </span>
          <button onClick={onClose} style={{ padding: '2px 8px', fontSize: '10px' }}>✕ CLOSE</button>
        </div>

        {/* Wizard Navigation Sub-tabs */}
        <div style={{ display: 'flex', background: 'var(--bg-slate)', borderBottom: '1px solid var(--border-dim)', padding: '0 12px' }}>
          <button
            onClick={() => setTab('INSTITUTIONS')}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderBottom: tab === 'INSTITUTIONS' ? '2px solid var(--accent-orange)' : '2px solid transparent',
              background: 'transparent',
              color: tab === 'INSTITUTIONS' ? 'var(--accent-orange)' : 'var(--text-dim)',
              fontWeight: tab === 'INSTITUTIONS' ? 700 : 500,
              fontSize: '11px',
            }}
          >
            01 // NATION & INSTITUTIONS
          </button>
          <button
            onClick={() => setTab('PARTIES')}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderBottom: tab === 'PARTIES' ? '2px solid var(--accent-cyan)' : '2px solid transparent',
              background: 'transparent',
              color: tab === 'PARTIES' ? 'var(--accent-cyan)' : 'var(--text-dim)',
              fontWeight: tab === 'PARTIES' ? 700 : 500,
              fontSize: '11px',
            }}
          >
            02 // PARTIES & IDEOLOGY ({parties.length})
          </button>
        </div>

        {/* Tab 1: Institutions & Nation */}
        {tab === 'INSTITUTIONS' && (
          <div style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto' }}>
            {/* Preset Picker */}
            <div>
              <label style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                DEMOGRAPHIC & REGIONAL PRESET:
              </label>
              <select
                value={selectedPreset}
                onChange={(e) => setSelectedPreset(e.target.value)}
                style={{ width: '100%' }}
              >
                {presets.map((p) => (
                  <option key={p} value={p}>{p.replace(/_/g, ' ').toUpperCase()}</option>
                ))}
              </select>
            </div>

            {/* Country Setup */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                  COUNTRY NAME:
                </label>
                <input
                  type="text"
                  value={countryName}
                  onChange={(e) => setCountryName(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                  POPULATION:
                </label>
                <input
                  type="number"
                  value={population}
                  onChange={(e) => setPopulation(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            {/* Institutions */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                  ELECTORAL SYSTEM:
                </label>
                <select
                  value={electoralSystem}
                  onChange={(e) => setElectoralSystem(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <option value="pr">Proportional Representation (PR)</option>
                  <option value="fptp">First-Past-The-Post (FPTP)</option>
                  <option value="mixed">Mixed-Member Proportional</option>
                  <option value="two_round">Two-Round Runoff</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                  PARLIAMENTARY SEATS:
                </label>
                <input
                  type="number"
                  value={seats}
                  onChange={(e) => setSeats(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            {/* Seed and Chaos */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                  RANDOM SEED (DETERMINISTIC):
                </label>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                  CHAOS / EVENT FREQUENCY: {chaosLevel}x
                </label>
                <input
                  type="range"
                  min="0"
                  max="3"
                  step="0.1"
                  value={chaosLevel}
                  onChange={(e) => setChaosLevel(Number(e.target.value))}
                />
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Parties & Ideologies Configuration */}
        {tab === 'PARTIES' && (
          <div style={{ padding: '14px', display: 'grid', gridTemplateColumns: '220px 1fr', gap: '14px', flex: 1, minHeight: '380px', overflowY: 'auto' }}>
            {/* Party Selector List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', borderRight: '1px solid var(--border-dim)', paddingRight: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-dim)', fontWeight: 700 }}>PARTIES ({parties.length})</span>
                <button onClick={handleAddParty} style={{ padding: '2px 6px', fontSize: '10px', color: 'var(--accent-lime)', borderColor: 'var(--accent-lime)' }}>
                  + NEW
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto', maxHeight: '340px' }}>
                {parties.map((p, idx) => (
                  <div
                    key={p.id || idx}
                    onClick={() => setSelectedPartyIndex(idx)}
                    style={{
                      padding: '6px 8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: selectedPartyIndex === idx ? 'var(--bg-slate)' : 'transparent',
                      border: selectedPartyIndex === idx ? `1px solid ${p.color}` : '1px solid transparent',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ width: '10px', height: '10px', backgroundColor: p.color, flexShrink: 0 }} />
                    <div style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <span style={{ fontWeight: 700, fontSize: '11px', color: '#FFF' }}>{p.abbreviation || 'PTY'}</span>
                      <div style={{ fontSize: '9px', color: 'var(--text-dim)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {p.name}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Party Editor */}
            {activeParty ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-dim)', paddingBottom: '6px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: activeParty.color }}>
                    EDITING: {activeParty.name.toUpperCase()} [{activeParty.abbreviation}]
                  </span>
                  <button
                    onClick={() => handleRemoveParty(selectedPartyIndex)}
                    style={{ padding: '2px 8px', fontSize: '9px', color: 'var(--accent-orange)', borderColor: 'var(--accent-orange)' }}
                  >
                    ✕ REMOVE
                  </button>
                </div>

                {/* Identity fields */}
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '8px' }}>
                  <div>
                    <label style={{ fontSize: '10px', color: 'var(--text-dim)', display: 'block', marginBottom: '2px' }}>
                      PARTY FULL NAME:
                    </label>
                    <input
                      type="text"
                      value={activeParty.name}
                      onChange={(e) => updateActiveParty('name', e.target.value)}
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
                      value={activeParty.abbreviation}
                      onChange={(e) => updateActiveParty('abbreviation', e.target.value.toUpperCase())}
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>

                {/* Color Chooser */}
                <div>
                  <label style={{ fontSize: '10px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                    THEMATIC COLOR:
                  </label>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <input
                      type="color"
                      value={activeParty.color.startsWith('#') ? activeParty.color : `#${activeParty.color}`}
                      onChange={(e) => updateActiveParty('color', e.target.value)}
                      style={{ width: '32px', height: '26px', border: 'none', background: 'transparent', cursor: 'pointer' }}
                    />
                    <input
                      type="text"
                      value={activeParty.color}
                      onChange={(e) => updateActiveParty('color', e.target.value)}
                      style={{ width: '80px', fontSize: '11px' }}
                    />
                    <div style={{ display: 'flex', gap: '4px', marginLeft: '6px' }}>
                      {PALETTE.map((c) => (
                        <div
                          key={c}
                          onClick={() => updateActiveParty('color', c)}
                          style={{
                            width: '16px',
                            height: '16px',
                            backgroundColor: c,
                            cursor: 'pointer',
                            border: activeParty.color === c ? '2px solid #FFF' : '1px solid #000',
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* 7-Axis Ideological Platform Configuration */}
                <div style={{ background: 'var(--bg-slate)', padding: '10px', border: '1px solid var(--border-dim)' }}>
                  <span style={{ fontSize: '10px', color: 'var(--accent-cyan)', fontWeight: 700, display: 'block', marginBottom: '8px' }}>
                    7-AXIS IDEOLOGICAL VECTOR [-100..+100]:
                  </span>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {AXES_DEFINITIONS.map((axis) => {
                      const val = activeParty.ideology?.[axis.id] ?? 0;
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
                            onChange={(e) => updateActivePartyIdeology(axis.id, e.target.value)}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: '11px' }}>
                SELECT OR ADD A PARTY TO CONFIGURE
              </div>
            )}
          </div>
        )}

        {/* Action Buttons Footer */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 18px',
            borderTop: '1px solid var(--border-dim)',
            background: 'var(--bg-panel)',
          }}
        >
          <button onClick={handleRandomize} style={{ borderColor: 'var(--accent-yellow)', color: 'var(--accent-yellow)' }}>
            🎲 RANDOMIZE EVERYTHING
          </button>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={onClose}>CANCEL</button>
            <button className="btn-primary" onClick={handleLaunch}>
              LAUNCH SIMULATION ►
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
