"""Seat allocation algorithms: D'Hondt, Sainte-Laguë, Largest Remainder, and FPTP."""

from __future__ import annotations

import math
import numpy as np


def allocate_seats(
    votes: np.ndarray,          # (M,) vote counts per party
    total_seats: int,
    formula: str = "dhondt",
    threshold: float = 0.05,
) -> np.ndarray:
    """Allocate parliamentary seats according to specified electoral formula and threshold.

    Formulas:
    - 'dhondt': divisor (s_j + 1)
    - 'sainte_lague': divisor (2 * s_j + 1)
    - 'largest_remainder': Hare quota with largest remainders
    - 'fptp': Plurality (single seat award)
    """
    m = len(votes)
    seats = np.zeros(m, dtype=np.int64)
    total_votes = float(np.sum(votes))

    if total_votes <= 0.0 or total_seats <= 0 or m == 0:
        return seats

    if formula == "fptp":
        # Winner-take-all single district seat
        winner = int(np.argmax(votes))
        seats[winner] = total_seats
        return seats

    # Apply electoral threshold filter
    qualifies = (votes / total_votes) >= threshold
    if not np.any(qualifies):
        # Fallback if no party met threshold: allow top party
        qualifies[np.argmax(votes)] = True

    qualified_indices = np.where(qualifies)[0]
    qualified_votes = votes[qualified_indices].astype(np.float64)

    if formula == "dhondt":
        # D'Hondt divisor method: quotient Q = V / (s + 1)
        q_seats = np.zeros(len(qualified_indices), dtype=np.int64)
        for _ in range(total_seats):
            quotients = qualified_votes / (q_seats + 1.0)
            best_idx = int(np.argmax(quotients))
            q_seats[best_idx] += 1
        for i, party_idx in enumerate(qualified_indices):
            seats[party_idx] = q_seats[i]

    elif formula == "sainte_lague":
        # Sainte-Laguë divisor method: quotient Q = V / (2*s + 1)
        q_seats = np.zeros(len(qualified_indices), dtype=np.int64)
        for _ in range(total_seats):
            quotients = qualified_votes / (2.0 * q_seats + 1.0)
            best_idx = int(np.argmax(quotients))
            q_seats[best_idx] += 1
        for i, party_idx in enumerate(qualified_indices):
            seats[party_idx] = q_seats[i]

    elif formula == "largest_remainder":
        # Largest Remainder with Hare Quota
        sum_q_votes = np.sum(qualified_votes)
        if sum_q_votes <= 0:
            return seats
        quota = sum_q_votes / total_seats
        automatic_seats = np.floor(qualified_votes / quota).astype(np.int64)
        remainders = qualified_votes - (automatic_seats * quota)
        allocated = int(np.sum(automatic_seats))
        surplus = total_seats - allocated

        if surplus > 0:
            order = np.argsort(-remainders)
            for k in range(min(surplus, len(order))):
                automatic_seats[order[k]] += 1

        for i, party_idx in enumerate(qualified_indices):
            seats[party_idx] = automatic_seats[i]
    else:
        raise ValueError(f"Unknown PR formula: '{formula}'")

    return seats
