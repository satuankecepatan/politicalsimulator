"""Deterministic multi-stream random number generation using SeedSequence."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np


class RngStreams:
    """Manages independent NumPy random.Generator instances per subsystem.

    Subsystems:
    - economy
    - events
    - elections
    - party_ai
    - demographics
    - opinion
    - territory
    - lifecycle
    - government
    - polling

    Spawning uses a deterministic integer derived from hashing the subsystem name,
    ensuring that child generators receive independent, uncorrelated bit-generator
    sequences that do not shift when additional subsystems are created.
    """

    SUBSYSTEMS = (
        "economy",
        "events",
        "elections",
        "party_ai",
        "demographics",
        "opinion",
        "territory",
        "lifecycle",
        "government",
        "polling",
    )

    def __init__(self, seed: int):
        self.seed = seed
        self._root_seq = np.random.SeedSequence(seed)
        self._streams: dict[str, np.random.Generator] = {}
        for name in self.SUBSYSTEMS:
            self._streams[name] = self._create_stream(name)

    def _create_stream(self, name: str) -> np.random.Generator:
        # Use name-derived seed sequence spawn key
        name_int = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16)
        child_seq = self._root_seq.spawn(1)[0]
        # Re-mix with subsystem integer
        sub_seq = np.random.SeedSequence(child_seq.entropy, spawn_key=(name_int,))
        return np.random.default_rng(sub_seq)

    def get(self, name: str) -> np.random.Generator:
        """Get or lazily initialize the generator for a named subsystem."""
        if name not in self._streams:
            self._streams[name] = self._create_stream(name)
        return self._streams[name]

    def __getitem__(self, name: str) -> np.random.Generator:
        return self.get(name)

    def get_state(self) -> dict[str, Any]:
        """Capture bit generator states for exact snapshotting."""
        return {name: gen.bit_generator.state for name, gen in self._streams.items()}

    def set_state(self, state_dict: dict[str, Any]) -> None:
        """Restore bit generator states from snapshot."""
        for name, state in state_dict.items():
            if name in self._streams:
                self._streams[name].bit_generator.state = state
            else:
                gen = np.random.default_rng()
                gen.bit_generator.state = state
                self._streams[name] = gen
