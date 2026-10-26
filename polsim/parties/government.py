"""Government maintenance: confidence votes, legislative proxies, stability, and collapse."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import GovernmentParams
from polsim.engine.state import GovernmentState, PartyState, RelationsState


def step_government(
    government: GovernmentState,
    parties: list[PartyState],
    relations: RelationsState,
    params: GovernmentParams,
    dt_months: float,
    rng: np.random.Generator,
) -> tuple[bool, list[str]]:
    """Update government stability, legislative output, and resolve confidence votes.

    Returns:
        (snap_election_needed, list_of_log_events)
    """
    logs: list[str] = []
    if not government.leader_party_id:
        return False, logs

    government.months_in_office += int(dt_months)
    for p in parties:
        if p.in_government:
            p.months_in_gov += int(dt_months)

    party_indices = {p.id: i for i, p in enumerate(parties)}
    coalition = [p for p in parties if p.id in government.coalition_party_ids]

    # Calculate internal government tension from coalition hostility
    if len(coalition) > 1:
        pair_hostilities = [
            relations.hostility[party_indices[pa.id], party_indices[pb.id]]
            for pa in coalition
            for pb in coalition
            if pa.id != pb.id
        ]
        avg_hostility = float(np.mean(pair_hostilities)) if pair_hostilities else 0.0
    else:
        avg_hostility = 0.0

    # Adjust stability
    decay = 0.005 * dt_months
    government.stability = float(np.clip(government.stability - decay - (params.tension_weight * avg_hostility), 0.1, 0.95))

    # Legislative output proxy
    if rng.uniform(0.0, 1.0) < (params.legislation_rate * government.stability):
        government.legislation_passed += 1

    # Confidence vote / Collapse hazard
    # Hazard rises when stability is very low
    collapse_risk = params.collapse_hazard * dt_months + (0.05 * max(0.0, 0.40 - government.stability))
    if rng.uniform(0.0, 1.0) < collapse_risk:
        logs.append(
            f"Government led by {government.leader_party_id} collapsed following a vote of no confidence."
        )
        # Clear government status
        for p in parties:
            p.in_government = False
            p.is_leader = False
        government.leader_party_id = None
        government.coalition_party_ids.clear()
        government.cabinet_seats.clear()
        government.stability = 0.0
        return True, logs

    # Occasional cabinet reshuffle
    if rng.uniform(0.0, 1.0) < (params.reshuffle_rate * dt_months):
        logs.append(f"Cabinet reshuffle announced by Prime Minister from {government.leader_party_id}.")

    return False, logs
