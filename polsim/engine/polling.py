"""Simulated polling with Dirichlet sampling and exact cause attribution."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import VotingParams
from polsim.engine.state import CohortState, EconomyState, PartyState
from polsim.voting.model import resolve_probabilistic_votes


def take_poll(
    cohorts: CohortState,
    parties: list[PartyState],
    economy: EconomyState,
    voting_params: VotingParams,
    n_effective: int = 1500,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """Generate simulated opinion poll with Dirichlet sampling error (MATHEMATICIAN.md 3)."""
    outcome = resolve_probabilistic_votes(cohorts, parties, economy, voting_params)
    true_shares = outcome.party_vote_shares  # (M,)
    m = len(parties)

    if rng is None:
        return {parties[i].id: float(true_shares[i]) for i in range(m)}

    # Dirichlet distribution with concentration alpha_j = N_eff * s_j
    # Add small epsilon to avoid alpha=0
    alphas = np.maximum(0.5, true_shares * n_effective)
    sampled_shares = rng.dirichlet(alphas)

    return {parties[i].id: round(float(sampled_shares[i]), 4) for i in range(m)}
