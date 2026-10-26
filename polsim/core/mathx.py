"""Numerical helpers and statistical functions for political simulation math.

Adheres strictly to .agent/SKILL/MATHEMATICIAN.md and .agent/RULES/AGENT.md:
- Numerically stable softmax with row-max subtraction
- Vectorized weighted Euclidean distances
- Ornstein-Uhlenbeck updates
- Half-life exponential decay
"""

from __future__ import annotations

import math
import numpy as np


def softmax(x: np.ndarray, axis: int = -1, temperature: float = 1.0) -> np.ndarray:
    """Numerically stable softmax with temperature scaling."""
    t = max(1e-6, float(temperature))
    scaled = x / t
    max_val = np.max(scaled, axis=axis, keepdims=True)
    exp_shifted = np.exp(scaled - max_val)
    sum_exp = np.sum(exp_shifted, axis=axis, keepdims=True)
    sum_exp = np.where(sum_exp == 0.0, 1e-12, sum_exp)
    return exp_shifted / sum_exp


def sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    """Standard logistic function."""
    if isinstance(x, (float, int)):
        if x < -40.0:
            return 0.0
        if x > 40.0:
            return 1.0
        return 1.0 / (1.0 + math.exp(-x))
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def clamp(arr: np.ndarray, low: float = -1.0, high: float = 1.0) -> np.ndarray:
    """Clamp array values strictly to [low, high]."""
    return np.clip(arr, low, high)


def decay_factor(half_life_months: float, dt_months: float = 1.0) -> float:
    """Calculate exponential decay multiplier E(t+1) = E(t) * decay_factor."""
    if half_life_months <= 0.0:
        return 0.0
    lam = math.log(2.0) / half_life_months
    return math.exp(-lam * dt_months)


def ornstein_uhlenbeck_step(
    x: float,
    mu: float,
    theta: float,
    sigma: float,
    dt: float,
    rng: np.random.Generator,
) -> float:
    """Step an Ornstein-Uhlenbeck mean-reverting process:
    X_{t+1} = X_t + theta * (mu - X_t) * dt + sigma * sqrt(dt) * N(0, 1)
    """
    drift = theta * (mu - x) * dt
    diffusion = sigma * math.sqrt(max(0.0, dt)) * float(rng.normal(0.0, 1.0))
    return x + drift + diffusion


def weighted_euclidean_distance(
    voter_positions: np.ndarray,  # Shape (N, D)
    party_positions: np.ndarray,  # Shape (M, D)
    voter_salience: np.ndarray,   # Shape (N, D)
) -> np.ndarray:
    """Calculate weighted ideological distance between N voter blocs and M parties.

    Formula from MATHEMATICIAN.md 2.1:
        d_ij = sqrt( sum_{k=1}^D w_ik * (v_ik - p_jk)^2 )

    Returns:
        Array of shape (N, M)
    """
    # voter_positions[:, None, :] -> (N, 1, D)
    # party_positions[None, :, :] -> (1, M, D)
    # diff -> (N, M, D)
    diff = voter_positions[:, None, :] - party_positions[None, :, :]
    squared_diff = diff * diff
    # salience -> (N, 1, D)
    weighted = squared_diff * voter_salience[:, None, :]
    summed = np.sum(weighted, axis=-1)  # (N, M)
    return np.sqrt(np.maximum(0.0, summed))
