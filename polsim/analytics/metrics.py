"""Political science and electoral system analytics metrics."""

from __future__ import annotations

import math
import numpy as np


def effective_number_of_parties(shares: list[float] | np.ndarray) -> float:
    """Calculate Laakso-Taagepera Effective Number of Parties (ENP).

    Formula: N = 1 / sum(s_i^2)
    Applicable to vote shares (ENPv) or parliamentary seat shares (ENPs).
    """
    arr = np.array(shares, dtype=np.float64)
    arr = arr[arr > 0]
    total = np.sum(arr)
    if total <= 0:
        return 0.0
    props = arr / total
    herfindahl = float(np.sum(props**2))
    return (1.0 / herfindahl) if herfindahl > 0 else 0.0


def gallagher_index(vote_shares: list[float] | np.ndarray, seat_shares: list[float] | np.ndarray) -> float:
    """Calculate Gallagher Index of Electoral Disproportionality (Least Squares Index).

    Formula: G = sqrt( 0.5 * sum( (v_i - s_i)^2 ) ) * 100
    Lower values mean higher proportionality.
    """
    v = np.array(vote_shares, dtype=np.float64)
    s = np.array(seat_shares, dtype=np.float64)
    v_norm = v / np.sum(v) if np.sum(v) > 0 else v
    s_norm = s / np.sum(s) if np.sum(s) > 0 else s

    diff_sq = (v_norm - s_norm) ** 2
    return float(math.sqrt(0.5 * np.sum(diff_sq)) * 100.0)


def pedersen_volatility(
    past_vote_shares: dict[str, float],
    current_vote_shares: dict[str, float],
) -> float:
    """Calculate Pedersen Electoral Volatility Index.

    Formula: V = 0.5 * sum( |v_{i, t} - v_{i, t-1}| ) * 100
    Measures net change in party support between consecutive elections.
    """
    all_parties = set(past_vote_shares.keys()) | set(current_vote_shares.keys())
    total_diff = sum(
        abs(current_vote_shares.get(p, 0.0) - past_vote_shares.get(p, 0.0))
        for p in all_parties
    )
    return float(0.5 * total_diff * 100.0)


def dalton_polarization(
    party_shares: list[float] | np.ndarray,
    party_positions: np.ndarray,  # (M, D)
) -> float:
    """Calculate Dalton's Polarization Index across multi-dimensional ideology.

    Formula: DP = sqrt( sum( s_i * ||p_i - mean_p||^2 ) )
    """
    shares = np.array(party_shares, dtype=np.float64)
    if np.sum(shares) <= 0:
        return 0.0
    shares = shares / np.sum(shares)

    # Weighted mean party position
    mean_pos = np.sum(shares[:, None] * party_positions, axis=0)  # (D,)
    diff = party_positions - mean_pos[None, :]
    sq_dist = np.sum(diff * diff, axis=-1)  # (M,)
    weighted_variance = np.sum(shares * sq_dist)
    return float(math.sqrt(max(0.0, weighted_variance)) * 100.0)
