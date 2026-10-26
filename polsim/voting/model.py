"""Probabilistic spatial voting model with valence, loyalty, economics, and turnout."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from polsim.config.schema import VotingParams
from polsim.core.mathx import clamp, sigmoid, softmax, weighted_euclidean_distance
from polsim.engine.state import CohortState, EconomyState, PartyState


@dataclass(slots=True)
class VotingOutcome:
    """Per-cohort and aggregate voting outputs."""

    cohort_turnout: np.ndarray          # (N,) in [0, 1]
    cohort_choice_prob: np.ndarray      # (N, M) probabilities summing to 1 per row
    cohort_votes: np.ndarray            # (N, M) actual voter counts
    party_total_votes: np.ndarray       # (M,)
    party_vote_shares: np.ndarray       # (M,) summing to 1.0
    total_valid_votes: float
    national_turnout_rate: float
    raw_utilities: np.ndarray           # (N, M) deterministic utilities


def compute_voter_utilities(
    cohorts: CohortState,
    parties: list[PartyState],
    economy: EconomyState,
    params: VotingParams,
) -> np.ndarray:
    """Calculate deterministic utility U_ij for each cohort i and party j.

    Formulation adheres to .agent/SKILL/MATHEMATICIAN.md and .agent/RULES/AGENT.md.
    """
    n_cohorts = cohorts.n_cohorts
    m_parties = len(parties)
    if n_cohorts == 0 or m_parties == 0:
        return np.zeros((n_cohorts, m_parties), dtype=np.float64)

    party_positions = np.array([p.position for p in parties], dtype=np.float64)  # (M, D)

    # 1. Weighted Ideological Distance
    # Standard or unscented sigma points
    if params.sigma_points and np.any(cohorts.covariances > 0.0):
        # Sample +/- 1 sigma per dimension to capture cohort spread
        d = weighted_euclidean_distance(cohorts.positions, party_positions, cohorts.salience)
        # Add variance penalty representing dispersion
        var_trace = np.trace(cohorts.covariances, axis1=1, axis2=2)[:, None]  # (N, 1)
        d_squared = (d * d) + 0.5 * var_trace
    else:
        d = weighted_euclidean_distance(cohorts.positions, party_positions, cohorts.salience)
        d_squared = d * d

    # Base spatial loss: -beta * d_ij^2
    utilities = -params.beta * d_squared  # (N, M)

    # Economic shock score (positive = good economy, negative = poor)
    econ_performance = (economy.growth - 2.0) - 0.5 * (economy.unemployment - 6.0) - 0.3 * (economy.inflation - 2.5)

    for j, party in enumerate(parties):
        if not party.active:
            utilities[:, j] = -1e9
            continue

        # 2. Valence alpha_j: charisma + organization + funding - scandals + boost
        valence = (
            0.4 * party.charisma
            + 0.3 * party.organization
            + 0.2 * party.funding
            - 0.5 * party.scandal_accum
            + party.valence_boost
        )
        utilities[:, j] += params.valence_weight * valence

        # 3. Incumbency and Cost of Ruling (incumbency fatigue)
        if party.in_government:
            # Incumbent bonus
            utilities[:, j] += params.incumbency_bonus
            # Fatigue penalty proportional to years in power
            years_in_power = party.months_in_gov / 12.0
            utilities[:, j] -= params.fatigue_per_year * years_in_power
            # Economic retrospective voting: reward or punish governing parties
            utilities[:, j] += params.econ_weight * econ_performance

        # 4. Protest voting bonus for anti-establishment / populist parties under high corruption
        if party.populism > 0.4 and economy.corruption > 0.35:
            utilities[:, j] += params.protest_weight * party.populism * (economy.corruption - 0.30)

    # 5. Historical Partisan Brand Loyalty: gamma_ij
    utilities += params.loyalty_weight * cohorts.loyalty[:, :m_parties]

    return utilities


def compute_turnout(
    utilities: np.ndarray,      # (N, M)
    cohorts: CohortState,
    params: VotingParams,
) -> np.ndarray:
    """Calculate turnout probability T_i for each cohort i."""
    # Best available option utility (Alienation test)
    max_utility = np.max(utilities, axis=1)  # (N,)

    # Indifference test: difference between top 1 and top 2 choices
    if utilities.shape[1] > 1:
        sorted_u = np.sort(utilities, axis=1)
        spread = sorted_u[:, -1] - sorted_u[:, -2]  # (N,)
        indifference_penalty = np.exp(-spread / 0.5) * params.indifference_weight
    else:
        indifference_penalty = 0.0

    # Turnout sigmoid: 1 / (1 + exp(-k * (U* - theta + baseline)))
    # baseline is cohorts.turnout (converted to log-odds shift)
    base_logits = (cohorts.turnout - 0.5) * 4.0
    turnout_score = params.turnout_k * (max_utility - params.alienation_threshold - indifference_penalty) + base_logits
    return np.asarray(sigmoid(turnout_score), dtype=np.float64)


def resolve_probabilistic_votes(
    cohorts: CohortState,
    parties: list[PartyState],
    economy: EconomyState,
    params: VotingParams,
) -> VotingOutcome:
    """Run full spatial voting model over cohorts and aggregate votes."""
    utilities = compute_voter_utilities(cohorts, parties, economy, params)
    turnout_rates = compute_turnout(utilities, cohorts, params)

    # Choice probabilities via temperature-scaled Softmax
    choice_probs = softmax(utilities, axis=-1, temperature=params.temperature)

    # Effective voters per cohort
    voters_per_cohort = cohorts.sizes * turnout_rates  # (N,)

    # Cohort votes matrix (N, M)
    cohort_votes = voters_per_cohort[:, None] * choice_probs

    party_total_votes = np.sum(cohort_votes, axis=0)  # (M,)
    total_valid_votes = float(np.sum(party_total_votes))

    if total_valid_votes > 0.0:
        party_vote_shares = party_total_votes / total_valid_votes
    else:
        party_vote_shares = np.zeros(len(parties), dtype=np.float64)

    total_pop = float(np.sum(cohorts.sizes))
    national_turnout = total_valid_votes / total_pop if total_pop > 0 else 0.0

    return VotingOutcome(
        cohort_turnout=turnout_rates,
        cohort_choice_prob=choice_probs,
        cohort_votes=cohort_votes,
        party_total_votes=party_total_votes,
        party_vote_shares=party_vote_shares,
        total_valid_votes=total_valid_votes,
        national_turnout_rate=national_turnout,
        raw_utilities=utilities,
    )
