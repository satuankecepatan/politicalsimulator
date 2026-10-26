"""Directed pairwise relationship matrices: trust, hostility, and affinity."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import CordonRule, RelationParams
from polsim.core.mathx import clamp, decay_factor
from polsim.engine.state import PartyState, RelationsState


def initialize_relations(
    parties: list[PartyState],
    axes: list[str],
    cordon_rules: list[CordonRule],
) -> RelationsState:
    """Initialize relationship matrices from ideological proximity and cordon taboos."""
    m = len(parties)
    trust = np.full((m, m), 0.5, dtype=np.float64)
    hostility = np.full((m, m), 0.1, dtype=np.float64)
    affinity = np.zeros((m, m), dtype=np.float64)

    axis_idx = {axis: i for i, axis in enumerate(axes)}

    for i in range(m):
        for j in range(m):
            if i == j:
                trust[i, j] = 1.0
                hostility[i, j] = 0.0
                affinity[i, j] = 1.0
                continue

            # Ideological distance in [-1, 1] space
            diff = parties[i].position - parties[j].position
            dist = float(np.linalg.norm(diff))
            # Proximity maps to initial affinity
            aff = float(np.clip(1.0 - dist, -1.0, 1.0))
            affinity[i, j] = aff
            trust[i, j] = float(np.clip(0.5 + 0.3 * aff, 0.0, 1.0))
            hostility[i, j] = float(np.clip(0.3 - 0.3 * aff, 0.0, 1.0))

            # Apply cordon sanitaire taboo if party j violates any rule
            for rule in cordon_rules:
                if rule.axis in axis_idx:
                    k = axis_idx[rule.axis]
                    rule_pos = rule.beyond / 100.0
                    party_val = parties[j].position[k]
                    # If party j exceeds the taboo boundary on that side
                    if (rule_pos > 0 and party_val >= rule_pos) or (rule_pos < 0 and party_val <= rule_pos):
                        trust[i, j] = 0.0
                        hostility[i, j] = 0.90
                        affinity[i, j] = -0.90

    return RelationsState(trust=trust, hostility=hostility, affinity=affinity)


def update_relations(
    relations: RelationsState,
    parties: list[PartyState],
    dt_months: float,
    params: RelationParams,
    cordon_rules: list[CordonRule],
    axes: list[str],
) -> None:
    """Step relationship decay, shared cooperation, and competition."""
    m = len(parties)
    if m <= 1:
        return

    goodwill_decay = decay_factor(params.goodwill_half_life, dt_months)
    grudge_decay = decay_factor(params.grudge_half_life, dt_months)
    axis_idx = {axis: i for i, axis in enumerate(axes)}

    for i in range(m):
        for j in range(m):
            if i == j or not parties[i].active or not parties[j].active:
                continue

            # Decay goodwill toward baseline
            relations.trust[i, j] = 0.3 + (relations.trust[i, j] - 0.3) * goodwill_decay
            # Grudges decay much slower
            relations.hostility[i, j] = 0.1 + (relations.hostility[i, j] - 0.1) * grudge_decay
            relations.affinity[i, j] = 0.0 + (relations.affinity[i, j] - 0.0) * goodwill_decay

            # If both parties are governing together, mutual trust and affinity rise
            if parties[i].in_government and parties[j].in_government:
                relations.trust[i, j] += params.cooperation_gain * dt_months
                relations.affinity[i, j] += params.cooperation_gain * dt_months
                relations.hostility[i, j] -= params.cooperation_gain * dt_months

            # Shared enemies: if both i and j are hostile to another party k
            for k in range(m):
                if k != i and k != j and parties[k].active:
                    if relations.hostility[i, k] > 0.6 and relations.hostility[j, k] > 0.6:
                        relations.affinity[i, j] += params.shared_enemy_gain * dt_months
                        relations.trust[i, j] += params.shared_enemy_gain * 0.5 * dt_months

            # Re-apply cordon sanitaire boundaries strictly
            for rule in cordon_rules:
                if rule.axis in axis_idx:
                    idx = axis_idx[rule.axis]
                    rule_pos = rule.beyond / 100.0
                    party_val = parties[j].position[idx]
                    if (rule_pos > 0 and party_val >= rule_pos) or (rule_pos < 0 and party_val <= rule_pos):
                        relations.trust[i, j] = 0.0
                        relations.hostility[i, j] = max(relations.hostility[i, j], 0.85)
                        relations.affinity[i, j] = min(relations.affinity[i, j], -0.85)

    # Strict parameter bounds
    relations.trust = clamp(relations.trust, 0.0, 1.0)
    relations.hostility = clamp(relations.hostility, 0.0, 1.0)
    relations.affinity = clamp(relations.affinity, -1.0, 1.0)
