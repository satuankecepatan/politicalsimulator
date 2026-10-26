"""Pydantic v2 configuration schema — the single source of truth.

Every model here is served as JSON Schema by the API (`/api/schema`) and the
frontend renders its setup forms from it. UI hints live in ``json_schema_extra``
under the ``"ui"`` key so adding a field in Python surfaces it in the UI.

Units: ideology is ``-100..+100`` at this boundary (engine uses ``[-1, 1]``);
"Unit" fields are ``0..1``; all rates are *per month* and scaled by tick length.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Unit = Annotated[float, Field(ge=0.0, le=1.0, json_schema_extra={"ui": {"widget": "slider", "step": 0.01}})]
Score = Annotated[float, Field(ge=-100.0, le=100.0)]
Slug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_\-]*$", max_length=40)]

ElectoralSystem = Literal["fptp", "pr", "mixed", "two_round"]
PRFormula = Literal["dhondt", "sainte_lague", "largest_remainder"]
Regime = Literal["parliamentary", "presidential"]
EventCategory = Literal[
    "economic", "scandal", "social", "security", "disaster",
    "international", "technological", "institutional", "leadership",
]
EVENT_CATEGORIES: tuple[str, ...] = (
    "economic", "scandal", "social", "security", "disaster",
    "international", "technological", "institutional", "leadership",
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


# ---------------------------------------------------------------------------
# Ideology & demographics
# ---------------------------------------------------------------------------


class IdeologyAxis(StrictModel):
    id: Slug
    name: str
    low_label: str
    high_label: str


DEFAULT_AXES: list[IdeologyAxis] = [
    IdeologyAxis(id="economic", name="Economic", low_label="State control", high_label="Free market"),
    IdeologyAxis(id="social", name="Social", low_label="Progressive", high_label="Traditional"),
    IdeologyAxis(id="authority", name="Authority", low_label="Libertarian", high_label="Authoritarian"),
    IdeologyAxis(id="identity", name="Identity", low_label="Cosmopolitan", high_label="Nationalist"),
    IdeologyAxis(id="secularism", name="Secularism", low_label="Secular", high_label="Religious"),
    IdeologyAxis(id="environment", name="Environment", low_label="Growth-first", high_label="Ecology-first"),
    IdeologyAxis(id="trust", name="Institutional trust", low_label="Anti-establishment", high_label="Establishment"),
]


class DemographicDimension(StrictModel):
    id: Slug
    name: str
    values: list[str] = Field(min_length=2)


DEFAULT_DIMENSIONS: list[DemographicDimension] = [
    DemographicDimension(id="age", name="Age band", values=["18-29", "30-44", "45-64", "65+"]),
    DemographicDimension(id="income", name="Income class", values=["low", "middle", "high"]),
    DemographicDimension(id="education", name="Education", values=["primary", "secondary", "tertiary"]),
    DemographicDimension(id="settlement", name="Settlement", values=["urban", "rural"]),
    DemographicDimension(id="religion", name="Religion", values=["secular", "religious"]),
    DemographicDimension(id="identity", name="Identity group", values=["majority", "minority"]),
    DemographicDimension(id="sector", name="Occupation sector", values=["industry", "services", "public", "agriculture"]),
]


class CohortConfig(StrictModel):
    """A hand-specified (or exported) cohort. Overrides generation when supplied."""

    region: Slug
    attrs: dict[str, str] = Field(description="dimension id -> value")
    size: float = Field(gt=0, description="Number of people represented")
    ideology: dict[str, Score] = Field(default_factory=dict, json_schema_extra={"ui": {"widget": "axis-sliders"}})
    spread: float = Field(default=18.0, ge=0, le=60, description="Ideological std-dev (same units as ideology)")
    salience: dict[str, Unit] = Field(default_factory=dict, json_schema_extra={"ui": {"widget": "axis-sliders", "min": 0, "max": 1}})
    turnout: Unit = 0.65
    media: Unit = Field(default=0.5, description="Media / information susceptibility")
    loyalty: dict[str, Unit] = Field(default_factory=dict, description="party id -> party identification")


class DemographicsConfig(StrictModel):
    preset: str = Field(default="industrial_democracy", json_schema_extra={"ui": {"widget": "preset-select"}})
    mode: Literal["cohort", "agents"] = "cohort"
    cohorts_per_region: int = Field(default=6, ge=1, le=60)
    n_agents: int = Field(default=400, ge=20, le=5000, description="Used only in agents mode")
    dimensions: list[DemographicDimension] = Field(default_factory=lambda: list(DEFAULT_DIMENSIONS))
    base_ideology: dict[str, Score] = Field(default_factory=dict, json_schema_extra={"ui": {"widget": "axis-sliders"}})
    ideology_spread: float = Field(default=22.0, ge=1, le=60, description="Between-cohort std-dev of ideology")
    within_spread: float = Field(default=18.0, ge=0, le=60, description="Within-cohort std-dev of ideology")
    axis_correlation: list[list[float]] | None = Field(default=None, description="D x D correlation between axes")
    marginals: dict[str, dict[str, float]] = Field(default_factory=dict, description="national attribute shares")
    attribute_correlations: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="'dim:value' -> {'dim:value': log-odds boost}"
    )
    loadings: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="'dim:value' -> {axis: ideology shift (-100..100 units)}"
    )
    cohorts: list[CohortConfig] | None = Field(default=None, description="Explicit cohorts (skip generation)")


# ---------------------------------------------------------------------------
# Territory
# ---------------------------------------------------------------------------


class RegionConfig(StrictModel):
    id: Slug
    name: str
    population_share: float = Field(default=1.0, gt=0)
    urbanization: Unit = 0.6
    wealth: Unit = 0.5
    unemployment_offset: float = Field(default=0.0, ge=-6, le=6)
    regionalism: Unit = 0.1
    religiosity: Unit = 0.4
    minority_share: Unit = 0.15
    education: Unit = 0.5
    aging: Unit = 0.5
    resources: Unit = 0.3
    neighbors: list[Slug] = Field(default_factory=list)


class CountryConfig(StrictModel):
    name: str = "Republic of Veridia"
    population: int = Field(default=12_000_000, ge=10_000, le=2_000_000_000)
    start_year: int = Field(default=2000, ge=1800, le=2400)
    n_regions: int = Field(default=12, ge=1, le=60)
    regions: list[RegionConfig] = Field(default_factory=list, description="Leave empty to generate")


# ---------------------------------------------------------------------------
# Parties
# ---------------------------------------------------------------------------


class FactionConfig(StrictModel):
    name: str
    offset: dict[str, Score] = Field(default_factory=dict, description="Offset from the party position")
    weight: Unit = 0.33


class PartyConfig(StrictModel):
    id: Slug
    name: str
    abbreviation: str = Field(max_length=8)
    color: str = Field(default="#FF4500", pattern=r"^#[0-9A-Fa-f]{6}$", json_schema_extra={"ui": {"widget": "color"}})
    icon: str | None = None
    ideology: dict[str, Score] = Field(default_factory=dict, json_schema_extra={"ui": {"widget": "axis-sliders"}})
    salience: dict[str, Unit] = Field(default_factory=dict, json_schema_extra={"ui": {"widget": "axis-sliders", "min": 0, "max": 1}})
    pragmatism: Unit = 0.5
    organization: Unit = 0.5
    funding: Unit = 0.5
    charisma: Unit = 0.5
    cohesion: Unit = 0.75
    populism: Unit = 0.2
    corruption: Unit = 0.3
    coalition_willingness: Unit = 0.6
    base_appeal: dict[str, float] = Field(
        default_factory=dict,
        description="'dim:value' -> appeal weight (-1..1)",
        json_schema_extra={"ui": {"widget": "demographic-weights"}},
    )
    founded_year: int | None = Field(default=None, description="Null = exists at start")
    home_region: Slug | None = Field(default=None, description="Regional party: contests only here")
    factions: list[FactionConfig] = Field(default_factory=list)

    @field_validator("base_appeal")
    @classmethod
    def _appeal_bounds(cls, v: dict[str, float]) -> dict[str, float]:
        for key, w in v.items():
            if ":" not in key:
                raise ValueError(f"base_appeal key '{key}' must look like 'dimension:value'")
            if not -1.0 <= w <= 1.0:
                raise ValueError(f"base_appeal '{key}' must be within [-1, 1]")
        return v


# ---------------------------------------------------------------------------
# Institutions
# ---------------------------------------------------------------------------


class CordonRule(StrictModel):
    """Parties beyond ``beyond`` on ``axis`` (sign gives side) are taboo partners."""

    axis: str
    beyond: Score = 75.0
    label: str = "cordon sanitaire"


class InstitutionsConfig(StrictModel):
    electoral_system: ElectoralSystem = "pr"
    pr_formula: PRFormula = "dhondt"
    threshold: float = Field(default=0.05, ge=0.0, le=0.2)
    pr_scope: Literal["national", "regional"] = "national"
    mixed_list_share: Unit = 0.5
    regime: Regime = "parliamentary"
    seats: int = Field(default=150, ge=11, le=1000)
    cycle_months: int = Field(default=48, ge=12, le=96)
    presidential_term_months: int = Field(default=60, ge=24, le=120)
    term_limit: int = Field(default=0, ge=0, le=6, description="Max consecutive leader terms; 0 = none")
    confidence_votes: bool = True
    snap_elections: bool = True
    cordon_rules: list[CordonRule] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class EventSettings(StrictModel):
    chaos_level: float = Field(default=1.0, ge=0.0, le=3.0, json_schema_extra={"ui": {"widget": "slider", "step": 0.05}})
    categories: dict[str, float] = Field(
        default_factory=lambda: dict.fromkeys(EVENT_CATEGORIES, 1.0),
        json_schema_extra={"ui": {"widget": "category-sliders", "min": 0, "max": 3}},
    )
    disabled_events: list[str] = Field(default_factory=list)
    extra_library_paths: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Tunable parameters (documented defaults; per-month rates)
# ---------------------------------------------------------------------------


class VotingParams(StrictModel):
    beta: float = Field(default=2.2, gt=0, description="Ideological sensitivity")
    temperature: float = Field(default=0.9, gt=0, description="Logit noise (volatility)")
    valence_weight: float = Field(default=1.1, ge=0)
    loyalty_weight: float = Field(default=1.4, ge=0)
    cleavage_weight: float = Field(default=0.9, ge=0)
    econ_weight: float = Field(default=0.10, ge=0, description="Economic voting per index point")
    incumbency_bonus: float = Field(default=0.15, ge=0)
    fatigue_per_year: float = Field(default=0.06, ge=0, description="Cost of ruling")
    protest_weight: float = Field(default=0.8, ge=0)
    tactical_rate: float = Field(default=0.45, ge=0, le=1, description="FPTP tactical re-casting share")
    pact_transfer: float = Field(default=0.6, ge=0, le=1)
    turnout_k: float = Field(default=1.6, gt=0, description="Turnout curve steepness")
    alienation_threshold: float = Field(default=-1.2, description="Utility below which voters abstain")
    indifference_weight: float = Field(default=0.6, ge=0)
    sigma_points: bool = Field(default=True, description="Use cohort covariance via sigma points")


class OpinionParams(StrictModel):
    baseline_reversion: float = Field(default=0.010, ge=0, description="Pull back to demographic baseline")
    thermostatic_rate: float = Field(default=0.0035, ge=0)
    persuasion_rate: float = Field(default=0.0040, ge=0, description="Cue-taking toward supported parties")
    noise: float = Field(default=0.006, ge=0, description="Monthly ideological noise (engine units)")
    hardship_left_shift: float = Field(default=0.0025, ge=0, description="Economic axis response to hardship")
    insecurity_shift: float = Field(default=0.0030, ge=0)
    salience_reversion: float = Field(default=0.05, ge=0)
    loyalty_decay: float = Field(default=0.004, ge=0)
    loyalty_gain: float = Field(default=0.12, ge=0, description="Loyalty gained toward voted party per election")


class EconomyParams(StrictModel):
    growth_mu: float = 2.2
    growth_theta: float = 0.08
    growth_sigma: float = 0.55
    inflation_mu: float = 2.5
    inflation_theta: float = 0.06
    inflation_sigma: float = 0.35
    unemployment_mu: float = 6.5
    unemployment_theta: float = 0.05
    okun: float = Field(default=0.05, description="Unemployment response to growth gap")
    inequality_mu: float = 0.32
    inequality_theta: float = 0.01
    inequality_sigma: float = 0.003
    security_theta: float = 0.06
    corruption_theta: float = 0.03
    policy_effect: float = Field(default=0.5, ge=0, description="Gov economic position -> equilibria (symmetric)")


class PartyParams(StrictModel):
    reposition_every: int = Field(default=3, ge=1)
    max_step: float = Field(default=0.035, ge=0, description="Max move per decision (engine units)")
    vote_seeking: float = 1.0
    policy_seeking: float = 0.6
    office_seeking: float = 0.3
    split_cohesion: float = Field(default=0.28, ge=0, le=1)
    split_hazard: float = Field(default=0.04, ge=0, le=1)
    dissolve_share: float = Field(default=0.012, ge=0, le=0.2)
    dissolve_after_months: int = Field(default=60, ge=6)
    entry_rate: float = Field(default=0.010, ge=0, description="Monthly hazard scale for new parties")
    merger_rate: float = Field(default=0.010, ge=0)
    max_parties: int = Field(default=14, ge=2, le=40)
    leader_change_after_loss: float = Field(default=0.45, ge=0, le=1)


class RelationParams(StrictModel):
    goodwill_half_life: float = Field(default=24.0, gt=0, description="months")
    grudge_half_life: float = Field(default=96.0, gt=0, description="months")
    affinity_rate: float = Field(default=0.05, ge=0)
    competition_weight: float = Field(default=0.020, ge=0)
    cooperation_gain: float = Field(default=0.015, ge=0)
    betrayal_hostility: float = Field(default=0.35, ge=0, le=1)
    shared_enemy_gain: float = Field(default=0.004, ge=0)


class GovernmentParams(StrictModel):
    collapse_hazard: float = Field(default=0.004, ge=0)
    tension_weight: float = Field(default=0.03, ge=0)
    reshuffle_rate: float = Field(default=0.02, ge=0)
    legislation_rate: float = Field(default=0.6, ge=0)
    max_coalition_size: int = Field(default=5, ge=1, le=8)
    formation_attempts: int = Field(default=6, ge=1)
    policy_drift_rate: float = Field(default=0.02, ge=0)


class SimParameters(StrictModel):
    voting: VotingParams = Field(default_factory=VotingParams)
    opinion: OpinionParams = Field(default_factory=OpinionParams)
    economy: EconomyParams = Field(default_factory=EconomyParams)
    parties: PartyParams = Field(default_factory=PartyParams)
    relations: RelationParams = Field(default_factory=RelationParams)
    government: GovernmentParams = Field(default_factory=GovernmentParams)


class SimSettings(StrictModel):
    seed: int = Field(default=42, ge=0)
    years: int = Field(default=100, ge=1, le=1000)
    tick_months: Literal[1, 2, 3, 6, 12] = 1
    relations_every: int = Field(default=3, ge=1, description="Store relation matrices every N ticks")
    poll_shift_threshold: float = Field(default=0.02, ge=0, description="Log poll shifts above this share")


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------


class ScenarioConfig(StrictModel):
    name: str = "Untitled scenario"
    description: str = ""
    axes: list[IdeologyAxis] = Field(default_factory=lambda: list(DEFAULT_AXES), min_length=1)
    country: CountryConfig = Field(default_factory=CountryConfig)
    demographics: DemographicsConfig = Field(default_factory=DemographicsConfig)
    parties: list[PartyConfig] = Field(default_factory=list)
    institutions: InstitutionsConfig = Field(default_factory=InstitutionsConfig)
    events: EventSettings = Field(default_factory=EventSettings)
    parameters: SimParameters = Field(default_factory=SimParameters)
    settings: SimSettings = Field(default_factory=SimSettings)

    @property
    def axis_ids(self) -> list[str]:
        return [a.id for a in self.axes]

    @model_validator(mode="after")
    def _cross_validate(self) -> ScenarioConfig:
        axis_ids = set(self.axis_ids)
        if len(axis_ids) != len(self.axes):
            raise ValueError("axis ids must be unique")
        party_ids = [p.id for p in self.parties]
        if len(set(party_ids)) != len(party_ids):
            raise ValueError("party ids must be unique")
        for party in self.parties:
            unknown = set(party.ideology) - axis_ids
            if unknown:
                raise ValueError(f"party '{party.id}' uses unknown axes: {sorted(unknown)}")
        region_ids = {r.id for r in self.country.regions}
        if region_ids:
            for party in self.parties:
                if party.home_region and party.home_region not in region_ids:
                    raise ValueError(f"party '{party.id}' home_region '{party.home_region}' not found")
        for rule in self.institutions.cordon_rules:
            if rule.axis not in axis_ids:
                raise ValueError(f"cordon rule uses unknown axis '{rule.axis}'")
        return self
