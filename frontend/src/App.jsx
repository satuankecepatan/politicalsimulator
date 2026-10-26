import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header.jsx';
import PoliticalCompass from './components/PoliticalCompass.jsx';
import TerritoryMap from './components/TerritoryMap.jsx';
import AllianceGraph from './components/AllianceGraph.jsx';
import ChronicleView from './components/ChronicleView.jsx';
import ChartsView from './components/ChartsView.jsx';
import InterventionModal from './components/InterventionModal.jsx';
import Wizard from './components/Wizard.jsx';

export default function App() {
  const [session, setSession] = useState(null);
  const [status, setStatus] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [compassData, setCompassData] = useState(null);
  const [historyEntries, setHistoryEntries] = useState([]);
  const [presets, setPresets] = useState([]);

  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedMs, setSpeedMs] = useState(250);

  const [showIntervention, setShowIntervention] = useState(false);
  const [showWizard, setShowWizard] = useState(false);

  const wsRef = useRef(null);

  // 1. Load presets and initialize default session
  useEffect(() => {
    fetch('/api/presets')
      .then((r) => r.json())
      .then((p) => setPresets(p))
      .catch(() => {});

    initSession('industrial_democracy', 42);
  }, []);

  const initSession = (presetName, seed) => {
    fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preset: presetName, seed }),
    })
      .then((r) => r.json())
      .then((data) => {
        setSession({ id: data.session_id, name: data.name });
        setStatus(data.summary);
        setMapData(data.map);
        setCompassData(data.compass);

        // Fetch initial history entries
        fetch(`/api/sessions/${data.session_id}/history`)
          .then((r) => r.json())
          .then((entries) => setHistoryEntries(entries));

        // Connect WebSocket
        connectWs(data.session_id);
      })
      .catch((err) => console.error('Failed to init session:', err));
  };

  // 2. WebSocket streaming connection
  const connectWs = (sessionId) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'tick') {
        setStatus(msg.summary);
        if (msg.compass) setCompassData(msg.compass);
        if (msg.entries && msg.entries.length > 0) {
          setHistoryEntries((prev) => [...prev, ...msg.entries]);
        }
      } else if (msg.type === 'batch_complete') {
        setStatus(msg.summary);
        if (msg.compass) setCompassData(msg.compass);
        if (msg.recent_entries) {
          setHistoryEntries((prev) => {
            const existingIds = new Set(prev.map((e) => e.id));
            const newOnes = msg.recent_entries.filter((e) => !existingIds.has(e.id));
            return [...prev, ...newOnes];
          });
        }
      }
    };
  };

  // 3. Control Handlers
  const handlePlay = () => {
    setIsPlaying(true);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'play', speed_ms: speedMs }));
    }
  };

  const handlePause = () => {
    setIsPlaying(false);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'pause' }));
    }
  };

  const handleStep = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'step' }));
    } else if (session) {
      fetch(`/api/sessions/${session.id}/tick`, { method: 'POST' })
        .then((r) => r.json())
        .then((d) => {
          setStatus(d.summary);
          setCompassData(d.compass);
          if (d.entries) setHistoryEntries((prev) => [...prev, ...d.entries]);
        });
    }
  };

  const handleRunYears = (years) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'run_years', years }));
    } else if (session) {
      fetch(`/api/sessions/${session.id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ years }),
      })
        .then((r) => r.json())
        .then((d) => {
          setStatus(d.summary);
          setCompassData(d.compass);
          if (d.recent_entries) setHistoryEntries(d.recent_entries);
        });
    }
  };

  const handleSetSpeed = (ms) => {
    setSpeedMs(ms);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'speed', speed_ms: ms }));
    }
  };

  const handleTriggerEvent = (eventId) => {
    if (!session) return;
    fetch(`/api/sessions/${session.id}/intervene`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'event', event_id: eventId }),
    })
      .then((r) => r.json())
      .then((d) => {
        setStatus(d.summary);
        // Refresh history
        fetch(`/api/sessions/${session.id}/history`)
          .then((res) => res.json())
          .then((ents) => setHistoryEntries(ents));
      });
  };

  const handleUpdatePartyPosition = (partyId, position) => {
    if (!session) return;
    fetch(`/api/sessions/${session.id}/intervene`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'party_position', party_id: partyId, position }),
    })
      .then((r) => r.json())
      .then((d) => {
        setStatus(d.summary);
        // Refresh compass
        fetch(`/api/sessions/${session.id}/compass`)
          .then((res) => res.json())
          .then((cmp) => setCompassData(cmp));
      });
  };

  const handleFork = () => {
    if (!session) return;
    fetch(`/api/sessions/${session.id}/fork`, { method: 'POST' })
      .then((r) => r.json())
      .then((d) => {
        setSession({ id: d.session_id, name: `${session.name} [ALT]` });
        setStatus(d.summary);
        setCompassData(d.compass);
        connectWs(d.session_id);
      });
  };

  const handleSave = () => {
    if (!session) return;
    fetch(`/api/sessions/${session.id}/save`, { method: 'POST' })
      .then((r) => r.json())
      .then((d) => alert(`Run successfully saved to SQLite database (ID: ${d.run_id})`));
  };

  const handleExport = (fmt) => {
    if (!session) return;
    window.open(`/api/sessions/${session.id}/export/${fmt}`, '_blank');
  };

  const handleWizardLaunch = (scenarioPayload) => {
    setShowWizard(false);
    initSession(scenarioPayload.preset, scenarioPayload.seed);
  };

  const parties = status?.parties || [];
  const gov = status?.government;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-dark)' }}>
      {/* Top Telemetry & Control Header */}
      <Header
        session={session}
        status={status}
        isPlaying={isPlaying}
        onPlay={handlePlay}
        onPause={handlePause}
        onStep={handleStep}
        onRunYears={handleRunYears}
        speedMs={speedMs}
        onSetSpeed={handleSetSpeed}
        onOpenIntervention={() => setShowIntervention(true)}
        onOpenWizard={() => setShowWizard(true)}
        onSave={handleSave}
        onExport={handleExport}
      />

      {/* Navigation Tab Bar */}
      <nav style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--border-dim)', padding: '0 18px', display: 'flex', gap: '8px' }}>
        {[
          { id: 'OVERVIEW', label: 'OVERVIEW // CHRONICLE & COMPASS' },
          { id: 'MAP_PARLIAMENT', label: 'TERRITORY // MAP & ALLIANCES' },
          { id: 'TRENDS', label: 'ANALYTICS // TIME-SERIES CHARTS' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 16px',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid var(--accent-orange)' : '2px solid transparent',
              backgroundColor: 'transparent',
              color: activeTab === tab.id ? 'var(--accent-orange)' : 'var(--text-dim)',
              fontWeight: activeTab === tab.id ? 700 : 500,
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Main Content Workspace */}
      <main style={{ flex: 1, padding: '16px', display: 'flex', gap: '16px', overflow: 'hidden' }}>
        {activeTab === 'OVERVIEW' && (
          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '16px', height: 'calc(100vh - 140px)' }}>
            <ChronicleView entries={historyEntries} />
            <PoliticalCompass
              compassData={compassData}
              onUpdatePartyPosition={handleUpdatePartyPosition}
            />
          </div>
        )}

        {activeTab === 'MAP_PARLIAMENT' && (
          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', height: 'calc(100vh - 140px)' }}>
            <TerritoryMap mapData={mapData} parties={parties} />
            <AllianceGraph parties={parties} government={gov} />
          </div>
        )}

        {activeTab === 'TRENDS' && (
          <div style={{ flex: 1, height: 'calc(100vh - 140px)' }}>
            <ChartsView historyEntries={historyEntries} parties={parties} />
          </div>
        )}
      </main>

      {/* Intervention Modal */}
      {showIntervention && (
        <InterventionModal
          parties={parties}
          onClose={() => setShowIntervention(false)}
          onTriggerEvent={handleTriggerEvent}
          onUpdatePartyPosition={handleUpdatePartyPosition}
          onFork={handleFork}
        />
      )}

      {/* Wizard Modal */}
      {showWizard && (
        <Wizard
          presets={presets}
          onClose={() => setShowWizard(false)}
          onLaunch={handleWizardLaunch}
        />
      )}
    </div>
  );
}
