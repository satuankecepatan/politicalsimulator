"""In-memory session manager for simulation instances."""

from __future__ import annotations

import time
import uuid
from typing import Any

from polsim.config.schema import ScenarioConfig
from polsim.engine.simulation import Simulation


class SessionManager:
    def __init__(self, ttl_seconds: int = 7200):
        self._sessions: dict[str, tuple[Simulation, float]] = {}
        self.ttl = ttl_seconds

    def create(self, config: ScenarioConfig, seed: int | None = None) -> tuple[str, Simulation]:
        session_id = str(uuid.uuid4())[:8]
        sim = Simulation(config, seed=seed)
        self._sessions[session_id] = (sim, time.time())
        return session_id, sim

    def get(self, session_id: str) -> Simulation | None:
        self._cleanup()
        item = self._sessions.get(session_id)
        if not item:
            return None
        sim, _ = item
        self._sessions[session_id] = (sim, time.time())
        return sim

    def store_sim(self, sim: Simulation) -> str:
        session_id = str(uuid.uuid4())[:8]
        self._sessions[session_id] = (sim, time.time())
        return session_id

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _cleanup(self) -> None:
        now = time.time()
        expired = [sid for sid, (_, last) in self._sessions.items() if now - last > self.ttl]
        for sid in expired:
            del self._sessions[sid]


manager = SessionManager()
