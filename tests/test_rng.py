import numpy as np
from polsim.core.rng import RngStreams


def test_rng_determinism():
    rng1 = RngStreams(seed=12345)
    rng2 = RngStreams(seed=12345)

    v1 = rng1["elections"].normal(size=10)
    v2 = rng2["elections"].normal(size=10)
    assert np.allclose(v1, v2)


def test_subsystem_stream_independence():
    """Drawing from subsystem A does NOT advance subsystem B."""
    rng_a = RngStreams(seed=42)
    rng_b = RngStreams(seed=42)

    # In rng_b, draw 1000 numbers from economy
    _ = rng_b["economy"].normal(size=1000)

    # The elections stream in both should be identical
    draw_a = rng_a["elections"].uniform(size=5)
    draw_b = rng_b["elections"].uniform(size=5)
    assert np.allclose(draw_a, draw_b)


def test_rng_state_snapshot_restore():
    rng = RngStreams(seed=999)
    _ = rng["events"].integers(0, 100, size=10)

    snapshot = rng.get_state()
    val_after_draw = rng["events"].uniform(size=5)

    # Restore snapshot and verify identical next draw
    rng.set_state(snapshot)
    val_restored = rng["events"].uniform(size=5)
    assert np.allclose(val_after_draw, val_restored)
