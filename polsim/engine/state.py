"""Simulation state dataclasses and memory structures.

Designed for vectorized NumPy operations and minimal memory allocations.
All internal ideological coordinates are normalized to [-1.0, 1.0].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import numpy as np

from polsim.core.calendar import SimDate


@dataclass(slots=True)
class FactionState:
    name: str
    offset: np.ndarray  # Shape (D,) in [-1, 1]
    weight: float = 0.33


@dataclass(slots=True)
class PartyState:
    id: str
    name: str
    abbreviation: str
    color: str
    position: np.ndarray  # Shape (D,) in [-1, 1]
    salience: np.ndarray   # Shape (D,) in [0, 1]
    pragmatism: float = 0.5
    organization: float = 0.5
    funding: float = 0.5
    charisma: float = 0.5
    cohesion: float = 0.75
    populism: float = 0.2
    corruption: float = 0.3
    coalition_willingness: float = 0.6
    base_appeal: dict[str, float] = field(default_factory=dict)
    factions: list[FactionState] = field(default_factory=list)
    home_region: str | None = None
    founded_tick: int = 0
    active: bool = True
    seats: int = 0
    vote_share: float = 0.0
    in_government: bool = False
    is_leader: bool = False
    months_in_gov: int = 0
    consecutive_terms: int = 0
    scandal_accum: float = 0.0
    valence_boost: float = 0.0  # Temporary boost from events/honeymoons


@dataclass(slots=True)
class CohortState:
    """Struct-of-arrays storing vectorized cohort demographic data."""

    sizes: np.ndarray           # (N,) float
    positions: np.ndarray       # (N, D) float in [-1, 1]
    baselines: np.ndarray       # (N, D) float in [-1, 1]
    salience: np.ndarray        # (N, D) float in [0, 1]
    covariances: np.ndarray     # (N, D, D) float
    turnout: np.ndarray         # (N,) float in [0, 1]
    loyalty: np.ndarray         # (N, M) float in [0, 1]
    media: np.ndarray           # (N,) float in [0, 1]
    region_ids: list[str]       # Length N
    attrs: list[dict[str, str]] # Length N

    @property
    def n_cohorts(self) -> int:
        return len(self.sizes)


@dataclass(slots=True)
class RegionState:
    id: str
    name: str
    population: float
    urbanization: float
    wealth: float
    unemployment_offset: float
    regionalism: float
    religiosity: float
    minority_share: float
    education: float
    aging: float
    resources: float
    seats: int = 1


@dataclass(slots=True)
class TerritoryState:
    regions: dict[str, RegionState] = field(default_factory=dict)
    graph: nx.Graph = field(default_factory=nx.Graph)


@dataclass(slots=True)
class EconomyState:
    growth: float = 2.2         # Real GDP growth rate (%)
    inflation: float = 2.5      # Annual CPI (%)
    unemployment: float = 6.5   # Unemployment rate (%)
    inequality: float = 0.32    # Gini coefficient
    security: float = 0.85      # Public safety / stability [0, 1]
    corruption: float = 0.25    # Perceived corruption [0, 1]

    def to_dict(self) -> dict[str, float]:
        return {
            "growth": round(self.growth, 3),
            "inflation": round(self.inflation, 3),
            "unemployment": round(self.unemployment, 3),
            "inequality": round(self.inequality, 4),
            "security": round(self.security, 3),
            "corruption": round(self.corruption, 3),
        }


@dataclass(slots=True)
class GovernmentState:
    leader_party_id: str | None = None
    coalition_party_ids: list[str] = field(default_factory=list)
    cabinet_seats: dict[str, int] = field(default_factory=dict)
    months_in_office: int = 0
    stability: float = 0.80
    legislation_passed: int = 0


@dataclass(slots=True)
class RelationsState:
    """Pairwise relationship matrices indexed by party index."""

    trust: np.ndarray      # (M, M) float in [0, 1]
    hostility: np.ndarray  # (M, M) float in [0, 1]
    affinity: np.ndarray   # (M, M) float in [-1, 1]


@dataclass(slots=True)
class ActiveEffect:
    source_event_id: str
    category: str
    target: str          # 'economy', 'party', 'cohort', etc.
    target_id: str | None
    parameter: str
    delta: float
    remaining_ticks: int


@dataclass(slots=True)
class SimState:
    """Complete snapshot of simulation at a given tick."""

    tick: int
    date: SimDate
    axes: list[str]
    parties: list[PartyState]
    party_indices: dict[str, int]
    cohorts: CohortState
    territory: TerritoryState
    economy: EconomyState
    government: GovernmentState
    relations: RelationsState
    active_effects: list[ActiveEffect] = field(default_factory=list)
    last_election_tick: int = 0

    @property
    def active_parties(self) -> list[PartyState]:
        return [p for p in self.parties if p.active]
