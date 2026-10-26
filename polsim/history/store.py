"""SQLite storage backend for simulation runs, history records, and state snapshots."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from polsim.config.schema import ScenarioConfig
from polsim.history.log import HistoryEntry, HistoryLog

def _numpy_default(o: Any) -> Any:
    if hasattr(o, "item"):
        return o.item()
    if hasattr(o, "tolist"):
        return o.tolist()
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def _safe_json(obj: Any) -> str:
    return json.dumps(obj, default=_numpy_default)


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    seed INTEGER NOT NULL,
    config_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS history_entries (
    run_id TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    date TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    title TEXT NOT NULL,
    actors_json TEXT NOT NULL,
    details_json TEXT NOT NULL,
    causes_json TEXT NOT NULL,
    prose TEXT NOT NULL,
    PRIMARY KEY (run_id, entry_id),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS snapshots (
    run_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    snapshot_bytes BLOB NOT NULL,
    PRIMARY KEY (run_id, tick),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_history_run_tick ON history_entries(run_id, tick);
"""


class HistoryStore:
    """Manages SQLite persistence for political simulation sessions."""

    def __init__(self, db_path: str | Path = "polsim.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(SCHEMA)

    def save_run(
        self,
        run_id: str,
        config: ScenarioConfig,
        history: HistoryLog,
        snapshot_bytes: bytes | None = None,
        tick: int = 0,
    ) -> None:
        """Save or update simulation run and insert all history entries."""
        config_json = json.dumps(config.model_dump(mode="json"))
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs (id, name, seed, config_json) VALUES (?, ?, ?, ?)",
                (run_id, config.name, config.settings.seed, config_json),
            )

            # Insert history entries
            entry_rows = [
                (
                    run_id,
                    e.id,
                    e.tick,
                    e.date,
                    e.entry_type,
                    e.title,
                    _safe_json(e.actors),
                    _safe_json(e.details),
                    _safe_json(e.causes),
                    e.prose,
                )
                for e in history.entries
            ]
            conn.executemany(
                """
                INSERT OR REPLACE INTO history_entries
                (run_id, entry_id, tick, date, entry_type, title, actors_json, details_json, causes_json, prose)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                entry_rows,
            )

            if snapshot_bytes is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO snapshots (run_id, tick, snapshot_bytes) VALUES (?, ?, ?)",
                    (run_id, tick, snapshot_bytes),
                )

    def load_run(self, run_id: str) -> tuple[ScenarioConfig, HistoryLog] | None:
        """Load a saved run's configuration and full history log."""
        with self._get_conn() as conn:
            run_row = conn.execute("SELECT config_json FROM runs WHERE id = ?", (run_id,)).fetchone()
            if not run_row:
                return None
            config = ScenarioConfig.model_validate_json(run_row["config_json"])

            history = HistoryLog()
            cur = conn.execute(
                "SELECT * FROM history_entries WHERE run_id = ? ORDER BY tick ASC, entry_id ASC",
                (run_id,),
            )
            for row in cur:
                entry = HistoryEntry(
                    id=row["entry_id"],
                    tick=row["tick"],
                    date=row["date"],
                    entry_type=row["entry_type"],
                    title=row["title"],
                    actors=json.loads(row["actors_json"]),
                    details=json.loads(row["details_json"]),
                    causes=json.loads(row["causes_json"]),
                    prose=row["prose"],
                )
                history.entries.append(entry)
            return config, history

    def list_runs(self) -> list[dict[str, Any]]:
        """List all saved simulation runs."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT id, name, seed, created_at FROM runs ORDER BY created_at DESC")
            return [dict(row) for row in cur]
