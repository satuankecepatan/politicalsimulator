"""Electoral systems execution: PR, FPTP with strategic voting, Mixed-Member, Two-Round."""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from polsim.config.schema import InstitutionsConfig, VotingParams
from polsim.engine.state import CohortState, EconomyState, PartyState, TerritoryState
from polsim.voting.allocation import allocate_seats
from polsim.voting.model import resolve_probabilistic_votes


@dataclass(slots=True)
class RegionalResult:
    region_id: str
    region_name: str
    seats_allocated: int
    party_votes: dict[str, float]
    party_seats: dict[str, int]
    turnout: float


@dataclass(slots=True)
class ElectionResult:
    tick: int
    electoral_system: str
    total_seats: int
    total_votes: float
    turnout: float
    party_votes: dict[str, float]
    party_vote_shares: dict[str, float]
    party_seats: dict[str, int]
    party_seat_shares: dict[str, float]
    regional_results: list[RegionalResult] = field(default_factory=list)
    winner_party_id: str | None = None
    majority_won: bool = False


def conduct_election(
    tick: int,
    cohorts: CohortState,
    parties: list[PartyState],
    territory: TerritoryState,
    economy: EconomyState,
    institutions: InstitutionsConfig,
    voting_params: VotingParams,
    rng: np.random.Generator,
) -> ElectionResult:
    """Run an election according to the configured electoral system."""
    m = len(parties)
    party_ids = [p.id for p in parties]

    # First resolve base voter choices across the electorate
    outcome = resolve_probabilistic_votes(cohorts, parties, economy, voting_params)
    total_valid_votes = outcome.total_valid_votes
    nat_turnout = outcome.national_turnout_rate

    party_votes_dict = {p.id: float(outcome.party_total_votes[i]) for i, p in enumerate(parties)}
    party_shares_dict = {p.id: float(outcome.party_vote_shares[i]) for i, p in enumerate(parties)}

    system = institutions.electoral_system
    total_seats = institutions.seats
    allocated_seats = np.zeros(m, dtype=np.int64)
    reg_results: list[RegionalResult] = []

    if system == "pr" and institutions.pr_scope == "national":
        # National PR
        allocated_seats = allocate_seats(
            outcome.party_total_votes,
            total_seats=total_seats,
            formula=institutions.pr_formula,
            threshold=institutions.threshold,
        )
        # Compute regional vote counts for reporting
        for reg_id, reg in territory.regions.items():
            reg_cohort_idx = [i for i, r in enumerate(cohorts.region_ids) if r == reg_id]
            if reg_cohort_idx:
                reg_votes = np.sum(outcome.cohort_votes[reg_cohort_idx], axis=0)
                rv_dict = {p.id: float(reg_votes[i]) for i, p in enumerate(parties)}
                t_rate = float(np.sum(reg_votes) / reg.population) if reg.population > 0 else 0.0
            else:
                rv_dict = {p.id: 0.0 for p in parties}
                t_rate = 0.0
            reg_results.append(
                RegionalResult(
                    region_id=reg_id,
                    region_name=reg.name,
                    seats_allocated=reg.seats,
                    party_votes=rv_dict,
                    party_seats={p.id: 0 for p in parties},
                    turnout=t_rate,
                )
            )

    elif system == "pr" and institutions.pr_scope == "regional":
        # Regional PR (seats apportioned to regions, allocated per region)
        for reg_id, reg in territory.regions.items():
            reg_cohort_idx = [i for i, r in enumerate(cohorts.region_ids) if r == reg_id]
            if reg_cohort_idx:
                reg_votes = np.sum(outcome.cohort_votes[reg_cohort_idx], axis=0)
                rv_dict = {p.id: float(reg_votes[i]) for i, p in enumerate(parties)}
                t_rate = float(np.sum(reg_votes) / reg.population) if reg.population > 0 else 0.0
            else:
                reg_votes = np.zeros(m, dtype=np.float64)
                rv_dict = {p.id: 0.0 for p in parties}
                t_rate = 0.0

            r_seats = allocate_seats(
                reg_votes,
                total_seats=reg.seats,
                formula=institutions.pr_formula,
                threshold=institutions.threshold,
            )
            allocated_seats += r_seats
            reg_results.append(
                RegionalResult(
                    region_id=reg_id,
                    region_name=reg.name,
                    seats_allocated=reg.seats,
                    party_votes=rv_dict,
                    party_seats={p.id: int(r_seats[i]) for i, p in enumerate(parties)},
                    turnout=t_rate,
                )
            )

    elif system == "fptp":
        # Single-member plurality districts apportioned across regions
        # With strategic voting: voters recognize top 2 in district and tactical voters switch
        for reg_id, reg in territory.regions.items():
            n_districts = reg.seats
            reg_cohort_idx = [i for i, r in enumerate(cohorts.region_ids) if r == reg_id]
            r_seats = np.zeros(m, dtype=np.int64)

            if reg_cohort_idx:
                base_reg_votes = np.sum(outcome.cohort_votes[reg_cohort_idx], axis=0)
                # District simulation with Dirichlet variance across districts
                for _ in range(n_districts):
                    dist_noise = rng.dirichlet(np.maximum(0.5, base_reg_votes / (np.sum(base_reg_votes) + 1e-6) * 20.0))
                    dist_votes = dist_noise * (np.sum(base_reg_votes) / max(1, n_districts))

                    # Strategic voting: find top 2 parties
                    top2 = np.argsort(-dist_votes)[:2]
                    tactical_share = voting_params.tactical_rate
                    # Non-top-2 voters transfer share of votes to closer of the top 2
                    for p_other in range(m):
                        if p_other not in top2 and dist_votes[p_other] > 0:
                            transfer = dist_votes[p_other] * tactical_share
                            dist_votes[p_other] -= transfer
                            # Distribute transfer based on relative proximity between top2
                            dist_votes[top2[0]] += transfer * 0.6
                            dist_votes[top2[1]] += transfer * 0.4

                    winner_idx = int(np.argmax(dist_votes))
                    r_seats[winner_idx] += 1

                rv_dict = {p.id: float(base_reg_votes[i]) for i, p in enumerate(parties)}
                t_rate = float(np.sum(base_reg_votes) / reg.population) if reg.population > 0 else 0.0
            else:
                rv_dict = {p.id: 0.0 for p in parties}
                t_rate = 0.0

            allocated_seats += r_seats
            reg_results.append(
                RegionalResult(
                    region_id=reg_id,
                    region_name=reg.name,
                    seats_allocated=reg.seats,
                    party_votes=rv_dict,
                    party_seats={p.id: int(r_seats[i]) for i, p in enumerate(parties)},
                    turnout=t_rate,
                )
            )

    elif system == "mixed":
        # Mixed-Member Proportional (MMP) compensatory system
        # Part constituency FPTP, remainder compensatory list seats
        constituency_share = 1.0 - institutions.mixed_list_share
        const_seats_total = max(1, int(round(total_seats * constituency_share)))
        list_seats_total = total_seats - const_seats_total

        # 1. Local FPTP seats
        fptp_seats = np.zeros(m, dtype=np.int64)
        for reg_id, reg in territory.regions.items():
            r_const_seats = max(1, int(round(reg.seats * constituency_share)))
            reg_cohort_idx = [i for i, r in enumerate(cohorts.region_ids) if r == reg_id]
            if reg_cohort_idx:
                base_reg_votes = np.sum(outcome.cohort_votes[reg_cohort_idx], axis=0)
                for _ in range(r_const_seats):
                    winner_idx = int(np.argmax(base_reg_votes + rng.normal(0, np.std(base_reg_votes) + 1.0, size=m)))
                    fptp_seats[winner_idx] += 1

        # 2. Compensatory list seats
        list_seats = allocate_seats(
            outcome.party_total_votes,
            total_seats=list_seats_total,
            formula=institutions.pr_formula,
            threshold=institutions.threshold,
        )
        allocated_seats = fptp_seats + list_seats

    elif system == "two_round":
        # Two-round runoff: if top party has <= 50%, run round 2 between top 2
        top2 = np.argsort(-outcome.party_total_votes)[:2]
        shares = outcome.party_vote_shares
        if shares[top2[0]] > 0.50:
            # Won outright
            winner = top2[0]
        else:
            # Round 2: recalculate choice between top 2 only
            r2_parties = [parties[top2[0]], parties[top2[1]]]
            r2_outcome = resolve_probabilistic_votes(cohorts, r2_parties, economy, voting_params)
            winner = top2[0] if r2_outcome.party_total_votes[0] >= r2_outcome.party_total_votes[1] else top2[1]

        allocated_seats[winner] = total_seats

    # Calculate seat shares and check absolute majority
    party_seats_dict = {p.id: int(allocated_seats[i]) for i, p in enumerate(parties)}
    party_seat_shares_dict = {
        p.id: (float(allocated_seats[i]) / total_seats) if total_seats > 0 else 0.0
        for i, p in enumerate(parties)
    }

    winner_idx = int(np.argmax(allocated_seats))
    winner_id = party_ids[winner_idx]
    majority = (allocated_seats[winner_idx] > (total_seats / 2.0))

    # Update party objects with election results
    for i, p in enumerate(parties):
        p.seats = int(allocated_seats[i])
        p.vote_share = float(party_shares_dict[p.id])

    return ElectionResult(
        tick=tick,
        electoral_system=system,
        total_seats=total_seats,
        total_votes=total_valid_votes,
        turnout=nat_turnout,
        party_votes=party_votes_dict,
        party_vote_shares=party_shares_dict,
        party_seats=party_seats_dict,
        party_seat_shares=party_seat_shares_dict,
        regional_results=reg_results,
        winner_party_id=winner_id,
        majority_won=majority,
    )
