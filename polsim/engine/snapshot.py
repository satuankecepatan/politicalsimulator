"""Simulation state snapshotting, timeline forking, and full RNG bit-generator serialization."""

from __future__ import annotations

import copy
import pickle
from typing import TYPE_CHECKING
import zlib

if TYPE_CHECKING:
    from polsim.engine.simulation import Simulation


def create_snapshot(sim: Simulation) -> bytes:
    """Serialize full simulation state including RNG bit-generator states with pickle and zlib."""
    payload = {
        "config": sim.config,
        "state": sim.state,
        "history": sim.history,
        "map_data": sim.map_data,
        "rng_states": sim.rng.get_state(),
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    return zlib.compress(raw, level=6)


def restore_snapshot(data: bytes) -> Simulation:
    """Restore simulation object from compressed snapshot bytes."""
    from polsim.engine.simulation import Simulation

    decompressed = zlib.decompress(data)
    payload = pickle.loads(decompressed)

    sim = Simulation.__new__(Simulation)
    sim.config = payload["config"]
    sim.state = payload["state"]
    sim.history = payload["history"]
    sim.map_data = payload["map_data"]

    # Re-initialize RNG and set saved bit generator states
    from polsim.core.rng import RngStreams

    sim.rng = RngStreams(sim.config.settings.seed)
    sim.rng.set_state(payload["rng_states"])

    # Re-instantiate event engine and narrator
    from polsim.events.engine import EventEngine
    from polsim.history.narrative import TemplateNarrator

    sim.event_engine = EventEngine(sim.config.events)
    sim.narrator = TemplateNarrator()
    sim._latest_poll = {}
    return sim


def fork_simulation(sim: Simulation, new_seed: int | None = None) -> Simulation:
    """Fork timeline into an alternate history from current simulation point."""
    snapshot_bytes = create_snapshot(sim)
    forked = restore_snapshot(snapshot_bytes)
    if new_seed is not None:
        forked.config.settings.seed = new_seed
        from polsim.core.rng import RngStreams

        forked.rng = RngStreams(new_seed)
    return forked
