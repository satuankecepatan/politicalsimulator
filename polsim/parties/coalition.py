"""Coalition formation algorithms, minimal winning coalitions, and portfolio bargaining."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
import numpy as np

from polsim.config.schema import GovernmentParams
from polsim.engine.state import GovernmentState, PartyState, RelationsState


@dataclass(slots=True)
class CoalitionProposal:
    formateur_party_id: str
    member_party_ids: list[str]
    total_seats: int
    majority_margin: int
    ideological_spread: float
    average_trust: float
    score: float
    cabinet_seats: dict[str, int]


def form_coalition(
    parties: list[PartyState],
    relations: RelationsState,
    total_parliament_seats: int,
    params: GovernmentParams,
) -> GovernmentState:
    """Execute post-election coalition formation bargaining.

    Heuristics:
    1. If a single party has an absolute majority (> 50% seats), it forms a single-party government.
    2. Otherwise, the largest party is appointed formateur and searches for viable coalitions.
    3. Prefers Minimal Winning Coalitions (MWC) with low ideological distance, high trust, and no cordon violations.
    4. Distributes cabinet portfolios proportionally (Gamson's Law).
    """
    active_parties = [p for p in parties if p.active and p.seats > 0]
    if not active_parties:
        return GovernmentState()

    majority_needed = (total_parliament_seats // 2) + 1
    party_by_id = {p.id: p for p in active_parties}
    party_indices = {p.id: i for i, p in enumerate(parties)}

    # Check for single-party absolute majority
    sorted_by_seats = sorted(active_parties, key=lambda p: p.seats, reverse=True)
    largest_party = sorted_by_seats[0]

    if largest_party.seats >= majority_needed:
        # Single party majority government
        for p in parties:
            p.in_government = (p.id == largest_party.id)
            p.is_leader = (p.id == largest_party.id)
            if p.in_government:
                p.months_in_gov = 0

        return GovernmentState(
            leader_party_id=largest_party.id,
            coalition_party_ids=[largest_party.id],
            cabinet_seats={largest_party.id: 15},
            months_in_office=0,
            stability=0.90,
        )

    # Formateur attempts: try largest party first, then 2nd largest if needed
    potential_formateurs = sorted_by_seats[:min(3, len(sorted_by_seats))]

    best_proposal: CoalitionProposal | None = None

    for formateur in potential_formateurs:
        f_idx = party_indices[formateur.id]
        other_parties = [p for p in active_parties if p.id != formateur.id]

        proposals_for_formateur: list[CoalitionProposal] = []

        # Search combinations up to max_coalition_size
        max_size = min(params.max_coalition_size, len(other_parties) + 1)
        for k in range(1, max_size):
            for combo in itertools.combinations(other_parties, k):
                coalition = [formateur] + list(combo)
                seats_sum = sum(p.seats for p in coalition)
                if seats_sum < majority_needed:
                    continue  # Not a majority

                # Check cordon sanitaire and taboo violations
                cordon_violated = False
                for p_a in coalition:
                    for p_b in coalition:
                        if p_a.id != p_b.id:
                            idx_a, idx_b = party_indices[p_a.id], party_indices[p_b.id]
                            if relations.trust[idx_a, idx_b] < 0.10 or relations.hostility[idx_a, idx_b] > 0.80:
                                cordon_violated = True
                                break
                    if cordon_violated:
                        break

                if cordon_violated:
                    continue

                # Compute ideological spread (max distance between any two members)
                positions = [p.position for p in coalition]
                max_dist = max(float(np.linalg.norm(pa - pb)) for pa, pb in itertools.combinations(positions, 2)) if len(positions) > 1 else 0.0

                # Compute average mutual trust
                trust_values = [
                    relations.trust[party_indices[pa.id], party_indices[pb.id]]
                    for pa, pb in itertools.permutations(coalition, 2)
                ]
                avg_trust = float(np.mean(trust_values)) if trust_values else 1.0

                # Minimal Winning Coalition score:
                # Surplus seats beyond majority penalty (MWC preference)
                surplus = seats_sum - majority_needed
                # Score combines high trust, small surplus (parsimony), and low ideological distance
                score = (2.0 * avg_trust) - (1.5 * max_dist) - (0.05 * surplus)

                # Allocate cabinet seats by Gamson's Law (proportional to seats contributed)
                total_c_seats = 18
                cab_alloc: dict[str, int] = {}
                for p in coalition:
                    share = p.seats / seats_sum
                    cab_alloc[p.id] = max(1, int(round(share * total_c_seats)))

                proposal = CoalitionProposal(
                    formateur_party_id=formateur.id,
                    member_party_ids=[p.id for p in coalition],
                    total_seats=seats_sum,
                    majority_margin=surplus,
                    ideological_spread=max_dist,
                    average_trust=avg_trust,
                    score=score,
                    cabinet_seats=cab_alloc,
                )
                proposals_for_formateur.append(proposal)

        if proposals_for_formateur:
            proposals_for_formateur.sort(key=lambda p: p.score, reverse=True)
            best_proposal = proposals_for_formateur[0]
            break

    if best_proposal:
        # Successful coalition agreement
        for p in parties:
            p.in_government = (p.id in best_proposal.member_party_ids)
            p.is_leader = (p.id == best_proposal.formateur_party_id)
            if p.in_government:
                p.months_in_gov = 0

        return GovernmentState(
            leader_party_id=best_proposal.formateur_party_id,
            coalition_party_ids=best_proposal.member_party_ids,
            cabinet_seats=best_proposal.cabinet_seats,
            months_in_office=0,
            stability=float(np.clip(best_proposal.average_trust, 0.4, 0.95)),
        )
    else:
        # Fallback: Minority government led by largest party
        for p in parties:
            p.in_government = (p.id == largest_party.id)
            p.is_leader = (p.id == largest_party.id)
            if p.in_government:
                p.months_in_gov = 0

        return GovernmentState(
            leader_party_id=largest_party.id,
            coalition_party_ids=[largest_party.id],
            cabinet_seats={largest_party.id: 12},
            months_in_office=0,
            stability=0.45,  # Inherently less stable
        )
