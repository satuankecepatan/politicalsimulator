import math
import numpy as np
from polsim.core.mathx import (
    clamp,
    decay_factor,
    ornstein_uhlenbeck_step,
    sigmoid,
    softmax,
    weighted_euclidean_distance,
)


def test_softmax_stability():
    # Huge logits that would overflow naive exp()
    x = np.array([[1000.0, 1001.0, 999.0]])
    probs = softmax(x, axis=-1, temperature=1.0)
    assert not np.isnan(probs).any()
    assert np.isclose(np.sum(probs), 1.0)
    assert probs[0, 1] > probs[0, 0] > probs[0, 2]


def test_sigmoid():
    assert math.isclose(sigmoid(0.0), 0.5)
    assert sigmoid(100.0) == 1.0
    assert sigmoid(-100.0) == 0.0


def test_decay_factor():
    # Half-life of 12 months with dt=12 should halve
    factor = decay_factor(12.0, dt_months=12.0)
    assert math.isclose(factor, 0.5, rel_tol=1e-5)


def test_weighted_euclidean_distance():
    # 1 voter bloc, 2 parties, 2 dimensions
    voters = np.array([[0.0, 0.0]])
    parties = np.array([
        [1.0, 0.0],
        [0.0, 2.0],
    ])
    salience = np.array([[1.0, 0.25]])

    d = weighted_euclidean_distance(voters, parties, salience)
    # Party 0: sqrt(1.0 * (1-0)^2 + 0.25 * (0-0)^2) = 1.0
    # Party 1: sqrt(1.0 * (0-0)^2 + 0.25 * (2-0)^2) = sqrt(0.25 * 4) = 1.0
    assert d.shape == (1, 2)
    assert math.isclose(d[0, 0], 1.0)
    assert math.isclose(d[0, 1], 1.0)


def test_ornstein_uhlenbeck():
    rng = np.random.default_rng(42)
    x = 10.0
    mu = 2.0
    # Strong reversion, zero noise
    stepped = ornstein_uhlenbeck_step(x, mu=mu, theta=0.5, sigma=0.0, dt=1.0, rng=rng)
    assert stepped < x
    assert stepped == 10.0 + 0.5 * (2.0 - 10.0) * 1.0  # 6.0
