"""Party lifecycle dynamics: splits, mergers, dissolutions, and new-party entries."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import PartyParams
from polsim.core.mathx import clamp
from polsim.engine.state import CohortState, FactionState, PartyState, RelationsState


def step_party_lifecycle(
    parties: list[PartyState],
    relations: RelationsState,
    cohorts: CohortState,
    params: PartyParams,
    tick: int,
    rng: np.random.Generator,
) -> tuple[bool, list[str]]:
    """Process splits, mergers, dissolutions, and new party emergence.

    Returns:
        (parties_structure_changed, log_messages)
    """
    logs: list[str] = []
    structure_changed = False
    m = len(parties)
    active_parties = [p for p in parties if p.active]

    # 1. Party Splits (Cohesion failure)
    for p in active_parties:
        if p.cohesion < params.split_cohesion and len(p.factions) > 1 and len(active_parties) < params.max_parties:
            if rng.uniform(0.0, 1.0) < params.split_hazard:
                # Disgruntled faction breaks away
                disgruntled_idx = int(np.argmax([float(np.linalg.norm(f.offset)) for f in p.factions]))
                faction = p.factions.pop(disgruntled_idx)

                new_id = f"{p.id}_split_{tick}"
                new_name = f"{faction.name} Movement"
                new_abbr = f"{p.abbreviation}-R"[:6]
                new_pos = clamp(p.position + faction.offset, -1.0, 1.0)

                new_party = PartyState(
                    id=new_id,
                    name=new_name,
                    abbreviation=new_abbr,
                    color="#DDA15E",
                    position=new_pos,
                    salience=p.salience.copy(),
                    pragmatism=max(0.2, p.pragmatism - 0.2),
                    organization=0.35,
                    funding=0.30,
                    charisma=0.55,
                    cohesion=0.85,
                    populism=min(0.9, p.populism + 0.2),
                    corruption=0.1,
                    coalition_willingness=0.5,
                    base_appeal=p.base_appeal.copy(),
                    founded_tick=tick,
                    active=True,
                )
                parties.append(new_party)
                structure_changed = True
                p.cohesion = 0.80  # Cohesion restores after dissident faction exits
                p.organization = max(0.2, p.organization * 0.75)
                logs.append(f"Faction '{faction.name}' broke away from {p.name} to form {new_name}.")
                break  # Limit 1 structural change per tick

    # 2. Party Mergers
    if not structure_changed and len(active_parties) > 4:
        for i, pa in enumerate(active_parties):
            for pb in active_parties[i + 1 :]:
                if pa.vote_share < 0.08 and pb.vote_share < 0.08 and not pa.in_government and not pb.in_government:
                    dist = float(np.linalg.norm(pa.position - pb.position))
                    if dist < 0.25 and rng.uniform(0.0, 1.0) < params.merger_rate:
                        # Merge pb into pa
                        pa.name = f"{pa.abbreviation}-{pb.abbreviation} United"
                        pa.abbreviation = f"{pa.abbreviation}{pb.abbreviation}"[:6]
                        pa.position = clamp(0.5 * (pa.position + pb.position), -1.0, 1.0)
                        pa.funding = min(0.9, pa.funding + pb.funding * 0.7)
                        pa.organization = min(0.9, pa.organization + pb.organization * 0.6)
                        pb.active = False
                        structure_changed = True
                        logs.append(f"{pa.name} and {pb.name} agreed to merge into a single parliamentary party.")
                        break
            if structure_changed:
                break

    # 3. Party Dissolution
    if not structure_changed and len(active_parties) > 3:
        for p in active_parties:
            if not p.in_government and p.seats == 0 and p.vote_share < params.dissolve_share:
                months_active = tick - p.founded_tick
                if months_active > params.dissolve_after_months:
                    p.active = False
                    structure_changed = True
                    logs.append(f"Minor party {p.name} ({p.abbreviation}) dissolved following sustained electoral decline.")
                    break

    # 4. New Party Entry from Unrepresented Public Mood
    if not structure_changed and len(active_parties) < params.max_parties:
        if rng.uniform(0.0, 1.0) < params.entry_rate:
            # Pick a cohort whose distance to all existing active parties is largest
            cohort_positions = cohorts.positions
            active_positions = np.array([p.position for p in active_parties])
            min_dists = np.min(
                np.linalg.norm(cohort_positions[:, None, :] - active_positions[None, :, :], axis=-1),
                axis=1,
            )
            alienated_cohort_idx = int(np.argmax(min_dists))

            if min_dists[alienated_cohort_idx] > 0.40:
                new_pos = clamp(cohort_positions[alienated_cohort_idx] + rng.normal(0, 0.05, size=cohort_positions.shape[1]), -1.0, 1.0)
                new_id = f"entry_p_{tick}"
                new_party = PartyState(
                    id=new_id,
                    name=f"New Citizen Alliance {tick}",
                    abbreviation=f"NCA{tick % 100}"[:5],
                    color="#588157",
                    position=new_pos,
                    salience=cohorts.salience[alienated_cohort_idx].copy(),
                    pragmatism=0.45,
                    organization=0.35,
                    funding=0.30,
                    charisma=0.60,
                    cohesion=0.80,
                    populism=0.55,
                    corruption=0.05,
                    coalition_willingness=0.6,
                    founded_tick=tick,
                    active=True,
                )
                parties.append(new_party)
                structure_changed = True
                logs.append(f"New political movement founded: {new_party.name} ({new_party.abbreviation}).")

    return structure_changed, logs
