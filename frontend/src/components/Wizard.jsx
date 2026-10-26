import React, { useState, useEffect } from 'react';

export default function Wizard({ presets, onLaunch, onClose }) {
  const [selectedPreset, setSelectedPreset] = useState('industrial_democracy');
  const [countryName, setCountryName] = useState('Republic of Veridia');
  const [population, setPopulation] = useState(12000000);
  const [regions, setRegions] = useState(8);
  const [electoralSystem, setElectoralSystem] = useState('pr');
  const [seats, setSeats] = useState(150);
  const [threshold, setThreshold] = useState(0.05);
  const [chaosLevel, setChaosLevel] = useState(1.0);
  const [seed, setSeed] = useState(42);

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
    });
  };

  const handleRandomize = () => {
    const randomPreset = presets[Math.floor(Math.random() * presets.length)] || 'industrial_democracy';
    setSelectedPreset(randomPreset);
    setSeed(Math.floor(Math.random() * 999999));
    setSeats(Math.floor(Math.random() * 150) + 50);
    setChaosLevel(Math.round((Math.random() * 2.0) * 10) / 10);
    const systems = ['pr', 'fptp', 'mixed', 'two_round'];
    setElectoralSystem(systems[Math.floor(Math.random() * systems.length)]);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(13, 15, 18, 0.90)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div className="vh-panel" style={{ width: '600px', maxWidth: '95vw', border: '2px solid var(--accent-cyan)' }}>
        <div className="vh-stripes" />
        <div className="vh-header-bar">
          <span className="vh-header-title">
            ⚙ SCENARIO INITIALIZATION WIZARD
          </span>
          <button onClick={onClose} style={{ padding: '2px 8px', fontSize: '10px' }}>✕ CLOSE</button>
        </div>

        <div style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '14px', maxHeight: '80vh', overflowY: 'auto' }}>
          
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
                <option key={p} value={p}>{p.replace('_', ' ').toUpperCase()}</option>
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
                CHAOS / EVENT LEVEL: {chaosLevel}x
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

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-dim)' }}>
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
    </div>
  );
}
