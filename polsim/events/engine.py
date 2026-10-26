"""Event management engine: YAML loader, safe rolls, effect application, and cascading follow-ups."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from polsim.config.schema import EventSettings
from polsim.engine.state import ActiveEffect, SimState
from polsim.events.expr import evaluate_precondition
from polsim.events.schema import EffectDef, EventDef

DEFAULT_LIBRARY_PATH = Path(__file__).parent / "library" / "events.yaml"


class EventEngine:
    """Loads event library, rolls for events per tick, applies effects, and tracks active effects."""

    def __init__(self, settings: EventSettings):
        self.settings = settings
        self.events: dict[str, EventDef] = {}
        self._load_library()

    def _load_library(self) -> None:
        paths = [DEFAULT_LIBRARY_PATH]
        for extra in self.settings.extra_library_paths:
            p = Path(extra)
            if p.is_file():
                paths.append(p)

        for p in paths:
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8")
            raw_data = yaml.safe_load(text)
            if isinstance(raw_data, list):
                for item in raw_data:
                    ev = EventDef.model_validate(item)
                    if ev.id not in self.settings.disabled_events:
                        self.events[ev.id] = ev

    def step(self, state: SimState, rng: Any) -> list[tuple[EventDef, str]]:
        """Roll for new events, apply their effects, and step existing active effects.

        Returns:
            List of (EventDef, outcome_description) for each triggered event.
        """
        triggered: list[tuple[EventDef, str]] = []

        # 1. Step existing active effects
        expired_effects: list[ActiveEffect] = []
        for eff in state.active_effects:
            eff.remaining_ticks -= 1
            if eff.remaining_ticks <= 0:
                expired_effects.append(eff)
                # Reverse effect if applicable
                self._revert_effect(eff, state)

        for exp in expired_effects:
            state.active_effects.remove(exp)

        # 2. Build context dictionary for safe precondition evaluation
        context = {
            "economy": state.economy,
            "government": state.government,
            "tick": state.tick,
            "n_parties": len(state.active_parties),
        }

        # 3. Roll for new events
        chaos = self.settings.chaos_level
        category_weights = self.settings.categories

        for ev_id, ev in self.events.items():
            cat_scale = category_weights.get(ev.category, 1.0)
            eff_prob = ev.base_prob * chaos * cat_scale

            if eff_prob <= 0.0:
                continue

            roll = float(rng.uniform(0.0, 1.0))
            if roll < eff_prob:
                # Check precondition
                if evaluate_precondition(ev.precondition, context):
                    self._apply_event(ev, state)
                    triggered.append((ev, ev.description))

        return triggered

    def _apply_event(self, ev: EventDef, state: SimState) -> None:
        """Apply all effects associated with an event."""
        for eff in ev.effects:
            # Apply to state
            self._apply_effect(eff, ev.id, ev.category, state)

    def _apply_effect(self, eff: EffectDef, event_id: str, category: str, state: SimState) -> None:
        # Economy target
        if eff.target == "economy":
            if hasattr(state.economy, eff.parameter):
                current_val = getattr(state.economy, eff.parameter)
                setattr(state.economy, eff.parameter, current_val + eff.delta)

        # Party target
        elif eff.target == "party":
            target_parties = (
                [p for p in state.parties if p.id == eff.target_id]
                if eff.target_id
                else [p for p in state.parties if p.is_leader] or state.active_parties
            )
            for p in target_parties:
                if hasattr(p, eff.parameter):
                    cur = getattr(p, eff.parameter)
                    setattr(p, eff.parameter, cur + eff.delta)

        # Government target
        elif eff.target == "government":
            if hasattr(state.government, eff.parameter):
                cur = getattr(state.government, eff.parameter)
                setattr(state.government, eff.parameter, cur + eff.delta)

        # If effect has duration > 1, register as ActiveEffect for decay/reversion
        if eff.duration_ticks > 1:
            state.active_effects.append(
                ActiveEffect(
                    source_event_id=event_id,
                    category=category,
                    target=eff.target,
                    target_id=eff.target_id,
                    parameter=eff.parameter,
                    delta=eff.delta,
                    remaining_ticks=eff.duration_ticks,
                )
            )

    def _revert_effect(self, eff: ActiveEffect, state: SimState) -> None:
        """Revert temporary parameter shifts when an active effect expires."""
        if eff.target == "party":
            target_parties = (
                [p for p in state.parties if p.id == eff.target_id]
                if eff.target_id
                else [p for p in state.parties if p.is_leader] or state.active_parties
            )
            for p in target_parties:
                if hasattr(p, eff.parameter):
                    cur = getattr(p, eff.parameter)
                    # Revert temporary delta
                    setattr(p, eff.parameter, cur - eff.delta)
