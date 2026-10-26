"""Master Simulation orchestrator."""

from __future__ import annotations

from typing import Any, Callable
import numpy as np

from polsim.config.schema import ScenarioConfig
from polsim.core.calendar import SimDate
from polsim.core.rng import RngStreams
from polsim.economy.model import step_economy
from polsim.engine.polling import take_poll
from polsim.engine.snapshot import create_snapshot, fork_simulation
from polsim.engine.state import (
    EconomyState,
    GovernmentState,
    PartyState,
    SimState,
)
from polsim.events.engine import EventEngine
from polsim.history.log import HistoryEntry, HistoryLog
from polsim.history.narrative import TemplateNarrator
from polsim.opinion.dynamics import step_opinion_dynamics
from polsim.parties.ai import adapt_parties
from polsim.parties.coalition import form_coalition
from polsim.parties.government import step_government
from polsim.parties.lifecycle import step_party_lifecycle
from polsim.parties.relations import initialize_relations, update_relations
from polsim.population.drift import step_demographic_drift
from polsim.population.generator import generate_cohorts
from polsim.territory.regions import generate_territory
from polsim.voting.elections import ElectionResult, conduct_election


class Simulation:
    """Agent-based political simulation sandbox engine."""

    def __init__(self, config: ScenarioConfig, seed: int | None = None):
        self.config = config
        if seed is not None:
            self.config.settings.seed = seed

        self.rng = RngStreams(self.config.settings.seed)
        self.history = HistoryLog()
        self.narrator = TemplateNarrator()
        self.event_engine = EventEngine(self.config.events)

        # 1. Generate Territory & Map
        territory, self.map_data = generate_territory(
            self.config.country,
            self.config.institutions,
            self.rng["territory"],
        )

        # 2. Generate Cohorts
        cohorts = generate_cohorts(self.config, territory, self.rng["demographics"])

        # 3. Initialize Parties
        axis_ids = self.config.axis_ids
        parties: list[PartyState] = []
        party_indices: dict[str, int] = {}
        for i, p in enumerate(self.config.parties):
            pos = np.array([p.ideology.get(a, 0.0) / 100.0 for a in axis_ids], dtype=np.float64)
            sal = np.array([p.salience.get(a, 0.5) for a in axis_ids], dtype=np.float64)
            p_state = PartyState(
                id=p.id,
                name=p.name,
                abbreviation=p.abbreviation,
                color=p.color,
                position=pos,
                salience=sal,
                pragmatism=p.pragmatism,
                organization=p.organization,
                funding=p.funding,
                charisma=p.charisma,
                cohesion=p.cohesion,
                populism=p.populism,
                corruption=p.corruption,
                coalition_willingness=p.coalition_willingness,
                base_appeal=p.base_appeal,
                home_region=p.home_region,
                active=True,
            )
            parties.append(p_state)
            party_indices[p.id] = i

        # 4. Relations
        relations = initialize_relations(parties, axis_ids, self.config.institutions.cordon_rules)

        # 5. Economy & Government
        economy = EconomyState()
        government = GovernmentState()

        # Initial SimState
        start_date = SimDate(year=self.config.country.start_year, month=1)
        self.state = SimState(
            tick=0,
            date=start_date,
            axes=axis_ids,
            parties=parties,
            party_indices=party_indices,
            cohorts=cohorts,
            territory=territory,
            economy=economy,
            government=government,
            relations=relations,
            last_election_tick=0,
        )

        # Initial election to form starting parliament and government
        self._latest_poll: dict[str, float] = {}
        self._conduct_election_round(is_initial=True)

    def _conduct_election_round(self, is_initial: bool = False) -> ElectionResult:
        """Run election and subsequent coalition formation."""
        result = conduct_election(
            tick=self.state.tick,
            cohorts=self.state.cohorts,
            parties=self.state.parties,
            territory=self.state.territory,
            economy=self.state.economy,
            institutions=self.config.institutions,
            voting_params=self.config.parameters.voting,
            rng=self.rng["elections"],
        )
        self.state.last_election_tick = self.state.tick

        # Form government
        new_gov = form_coalition(
            parties=self.state.parties,
            relations=self.state.relations,
            total_parliament_seats=self.config.institutions.seats,
            params=self.config.parameters.government,
        )
        self.state.government = new_gov

        # Record to history log
        winner_party = next((p for p in self.state.parties if p.id == result.winner_party_id), None)
        winner_name = winner_party.name if winner_party else result.winner_party_id

        el_entry = self.history.append(
            tick=self.state.tick,
            date_str=self.state.date.format(),
            entry_type="election",
            title=f"General Election: {winner_name} wins plurality" if not result.majority_won else f"General Election: {winner_name} wins outright majority",
            actors=[p.id for p in self.state.parties if p.seats > 0],
            details={
                "winner": winner_name,
                "winner_id": result.winner_party_id,
                "turnout": result.turnout,
                "majority": result.majority_won,
                "seats": result.party_seats,
                "shares": result.party_vote_shares,
            },
        )
        el_entry.prose = self.narrator.narrate(el_entry)

        # Coalition entry
        c_parties = [p.name for p in self.state.parties if p.id in new_gov.coalition_party_ids]
        leader_p = next((p for p in self.state.parties if p.id == new_gov.leader_party_id), None)
        l_name = leader_p.name if leader_p else str(new_gov.leader_party_id)

        coal_entry = self.history.append(
            tick=self.state.tick,
            date_str=self.state.date.format(),
            entry_type="coalition",
            title=f"Government Formed: {l_name}",
            actors=new_gov.coalition_party_ids,
            details={
                "leader": l_name,
                "leader_id": new_gov.leader_party_id,
                "members": c_parties,
                "stability": new_gov.stability,
            },
        )
        coal_entry.prose = self.narrator.narrate(coal_entry)

        return result

    def tick(self) -> list[HistoryEntry]:
        """Execute one simulation month tick."""
        self.state.tick += 1
        dt_months = float(self.config.settings.tick_months)
        self.state.date = SimDate.from_tick(
            self.state.tick,
            start_year=self.config.country.start_year,
            tick_months=self.config.settings.tick_months,
        )

        entries_this_tick: list[HistoryEntry] = []

        # 1. Economy step
        governing = [p for p in self.state.parties if p.in_government]
        step_economy(self.state.economy, governing, self.config.parameters.economy, dt_months, self.rng["economy"])

        # 2. Event generator rolls & active effect step
        triggered_events = self.event_engine.step(self.state, self.rng["events"])
        for ev, desc in triggered_events:
            entry = self.history.append(
                tick=self.state.tick,
                date_str=self.state.date.format(),
                entry_type="event",
                title=ev.title,
                actors=[p.id for p in governing],
                details={"event_id": ev.id, "category": ev.category, "description": desc},
            )
            entry.prose = self.narrator.narrate(entry)
            entries_this_tick.append(entry)

        # 3. Public opinion dynamics
        causes = step_opinion_dynamics(
            self.state.cohorts,
            self.state.parties,
            self.state.economy,
            self.config.parameters.opinion,
            dt_months,
            self.rng["opinion"],
        )

        # 4. Demographic drift annually (every 12 months)
        if self.state.tick % 12 == 0:
            step_demographic_drift(self.state.cohorts, dt_months=12.0, rng=self.rng["demographics"])

        # 5. Party AI: strategic repositioning
        adapt_parties(
            self.state.parties,
            self.state.cohorts,
            self.state.relations,
            self.config.parameters.parties,
            tick=self.state.tick,
            rng=self.rng["party_ai"],
        )

        # 6. Inter-party relationships update
        if self.state.tick % self.config.settings.relations_every == 0:
            update_relations(
                self.state.relations,
                self.state.parties,
                dt_months=float(self.config.settings.relations_every),
                params=self.config.parameters.relations,
                cordon_rules=self.config.institutions.cordon_rules,
                axes=self.state.axes,
            )

        # 7. Government maintenance & confidence checks
        collapse_snap, gov_logs = step_government(
            self.state.government,
            self.state.parties,
            self.state.relations,
            self.config.parameters.government,
            dt_months,
            self.rng["government"],
        )
        for g_log in gov_logs:
            entry = self.history.append(
                tick=self.state.tick,
                date_str=self.state.date.format(),
                entry_type="collapse" if collapse_snap else "legislation",
                title="Government Update",
                details={"message": g_log},
                prose=g_log,
            )
            entries_this_tick.append(entry)

        # 8. Party Lifecycle (splits, mergers, dissolution, entry)
        changed, lc_logs = step_party_lifecycle(
            self.state.parties,
            self.state.relations,
            self.state.cohorts,
            self.config.parameters.parties,
            tick=self.state.tick,
            rng=self.rng["lifecycle"],
        )
        if changed:
            # Re-index parties
            self.state.party_indices = {p.id: i for i, p in enumerate(self.state.parties)}
            # Expand relations matrices to match new party count
            m = len(self.state.parties)
            new_rel = initialize_relations(self.state.parties, self.state.axes, self.config.institutions.cordon_rules)
            self.state.relations = new_rel

        for log_msg in lc_logs:
            entry = self.history.append(
                tick=self.state.tick,
                date_str=self.state.date.format(),
                entry_type="split" if "broke away" in log_msg else "merger" if "merge" in log_msg else "party_event",
                title="Party Realignment",
                details={"message": log_msg},
                prose=log_msg,
            )
            entries_this_tick.append(entry)

        # 9. Check if Election is due (regular cycle or snap election)
        election_due = False
        months_since_election = self.state.tick - self.state.last_election_tick
        if months_since_election >= self.config.institutions.cycle_months:
            election_due = True
        elif collapse_snap and self.config.institutions.snap_elections:
            election_due = True

        if election_due:
            res = self._conduct_election_round()
            entries_this_tick.append(self.history.entries[-2])  # election entry
            entries_this_tick.append(self.history.entries[-1])  # coalition entry

        # 10. Polling
        self._latest_poll = take_poll(
            self.state.cohorts,
            self.state.active_parties,
            self.state.economy,
            self.config.parameters.voting,
            n_effective=1500,
            rng=self.rng["polling"],
        )

        return entries_this_tick

    def run(self, years: int, progress_callback: Callable[[int, int], None] | None = None) -> None:
        """Run the simulation for a given number of simulated years."""
        target_ticks = self.state.tick + (years * 12) // self.config.settings.tick_months
        total_steps = target_ticks - self.state.tick

        for step in range(total_steps):
            self.tick()
            if progress_callback:
                progress_callback(step + 1, total_steps)

    def intervene_party_position(self, party_id: str, new_position: dict[str, float]) -> None:
        """User intervention: modify a party's ideological position in [-100..100] coordinates."""
        for p in self.state.parties:
            if p.id == party_id:
                for axis, val in new_position.items():
                    if axis in self.state.axes:
                        idx = self.state.axes.index(axis)
                        p.position[idx] = float(np.clip(val / 100.0, -1.0, 1.0))

    def intervene_trigger_event(self, event_id: str) -> bool:
        """User intervention: force trigger a specific event by ID."""
        if event_id in self.event_engine.events:
            ev = self.event_engine.events[event_id]
            self.event_engine._apply_event(ev, self.state)
            entry = self.history.append(
                tick=self.state.tick,
                date_str=self.state.date.format(),
                entry_type="event",
                title=f"[Intervention] {ev.title}",
                details={"event_id": ev.id, "category": ev.category, "description": ev.description},
            )
            entry.prose = self.narrator.narrate(entry)
            return True
        return False

    def fork(self, new_seed: int | None = None) -> Simulation:
        """Fork timeline into an alternate history from this exact save point."""
        return fork_simulation(self, new_seed=new_seed)

    def snapshot(self) -> bytes:
        """Capture full state snapshot byte string."""
        return create_snapshot(self)

    def get_compass_preview(self) -> dict[str, Any]:
        """Compute live 2D political compass data (Economic vs Social axes) for UI visualization."""
        econ_idx = self.state.axes.index("economic") if "economic" in self.state.axes else 0
        soc_idx = self.state.axes.index("social") if "social" in self.state.axes else min(1, len(self.state.axes) - 1)

        cohort_points = [
            {
                "x": round(float(self.state.cohorts.positions[i, econ_idx] * 100.0), 1),
                "y": round(float(self.state.cohorts.positions[i, soc_idx] * 100.0), 1),
                "size": round(float(self.state.cohorts.sizes[i]), 0),
            }
            for i in range(self.state.cohorts.n_cohorts)
        ]

        party_points = [
            {
                "id": p.id,
                "name": p.name,
                "abbr": p.abbreviation,
                "color": p.color,
                "x": round(float(p.position[econ_idx] * 100.0), 1),
                "y": round(float(p.position[soc_idx] * 100.0), 1),
                "seats": p.seats,
                "in_gov": p.in_government,
            }
            for p in self.state.active_parties
        ]

        return {
            "x_axis": self.state.axes[econ_idx],
            "y_axis": self.state.axes[soc_idx],
            "cohorts": cohort_points,
            "parties": party_points,
        }

    def get_status_summary(self) -> dict[str, Any]:
        """Return a lightweight state summary dict for live frontend polling/websockets."""
        gov = self.state.government
        return {
            "tick": self.state.tick,
            "date": self.state.date.format(),
            "year": self.state.date.year,
            "month": self.state.date.month,
            "economy": self.state.economy.to_dict(),
            "government": {
                "leader": gov.leader_party_id,
                "coalition": gov.coalition_party_ids,
                "stability": round(gov.stability, 2),
                "months_in_office": gov.months_in_office,
            },
            "poll": self._latest_poll,
            "parties": [
                {
                    "id": p.id,
                    "name": p.name,
                    "abbr": p.abbreviation,
                    "color": p.color,
                    "seats": p.seats,
                    "vote_share": round(p.vote_share, 4),
                    "in_gov": p.in_government,
                }
                for p in self.state.active_parties
            ],
        }
