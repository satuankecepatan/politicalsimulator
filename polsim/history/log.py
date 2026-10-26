"""Structured simulation history logging, pandas export, and query filtering."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import pandas as pd


@dataclass(slots=True)
class HistoryEntry:
    id: str
    tick: int
    date: str
    entry_type: str  # 'election', 'coalition', 'event', 'collapse', 'split', 'merger', 'legislation', 'monthly'
    title: str
    actors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    causes: dict[str, float] = field(default_factory=dict)
    prose: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HistoryLog:
    """In-memory collection of all structured history records with pandas and export methods."""

    def __init__(self):
        self.entries: list[HistoryEntry] = []
        self._seq_by_tick: dict[int, int] = {}

    def append(
        self,
        tick: int,
        date_str: str,
        entry_type: str,
        title: str,
        actors: list[str] | None = None,
        details: dict[str, Any] | None = None,
        causes: dict[str, float] | None = None,
        prose: str = "",
    ) -> HistoryEntry:
        seq = self._seq_by_tick.get(tick, 0) + 1
        self._seq_by_tick[tick] = seq
        entry_id = f"e{tick:05d}-{seq:03d}"

        entry = HistoryEntry(
            id=entry_id,
            tick=tick,
            date=date_str,
            entry_type=entry_type,
            title=title,
            actors=actors or [],
            details=details or {},
            causes=causes or {},
            prose=prose,
        )
        self.entries.append(entry)
        return entry

    def filter(
        self,
        entry_type: str | None = None,
        actor: str | None = None,
        start_tick: int | None = None,
        end_tick: int | None = None,
    ) -> list[HistoryEntry]:
        results = self.entries
        if entry_type:
            results = [e for e in results if e.entry_type == entry_type]
        if actor:
            results = [e for e in results if actor in e.actors]
        if start_tick is not None:
            results = [e for e in results if e.tick >= start_tick]
        if end_tick is not None:
            results = [e for e in results if e.tick <= end_tick]
        return results

    def to_frame(self) -> pd.DataFrame:
        """Export history entries as a pandas DataFrame."""
        if not self.entries:
            return pd.DataFrame(
                columns=["id", "tick", "date", "entry_type", "title", "actors", "details", "causes", "prose"]
            )
        records = [e.to_dict() for e in self.entries]
        return pd.DataFrame.from_records(records)

    def export(self, path: str | Path) -> None:
        """Export history to JSON, CSV, or Parquet."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        suffix = p.suffix.lower()

        df = self.to_frame()
        if suffix == ".csv":
            df.to_csv(p, index=False)
        elif suffix in {".parquet", ".pq"}:
            df.to_parquet(p, index=False)
        else:
            # Default JSON
            import json
            data = [e.to_dict() for e in self.entries]
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
