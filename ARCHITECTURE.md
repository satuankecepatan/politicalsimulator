# ARCHITECTURE — polsim

> Agent-based political simulation sandbox. Python owns the truth, JavaScript owns the view.

## 1. Module map

```
polsim/                      # installable, zero-UI engine (usable from Jupyter)
├── cli.py                   # Typer CLI: run / export / calibrate / serve
├── config/
│   ├── schema.py            # Pydantic v2 models: axes, parties, cohorts, regions,
│   │                        #   institutions, events settings, tunables, ScenarioConfig
│   ├── loader.py            # YAML/JSON load + save
│   └── presets.py           # demographic + scenario presets, randomize_scenario()
├── core/
│   ├── rng.py               # RngStreams: SeedSequence -> named child Generators
│   ├── calendar.py          # SimDate (year, month) <-> tick
│   └── mathx.py             # softmax, sigmoid, clamp, decay helpers
├── population/
│   ├── generator.py         # cohort generation (Dirichlet + MVN, correlation tables)
│   └── drift.py             # cohort-component drift: aging, urbanization, education
├── territory/
│   └── regions.py           # region generation, NetworkX adjacency, Voronoi -> GeoJSON
├── economy/
│   └── model.py             # mean-reverting (OU/AR(1)) indicators + policy equilibria
├── opinion/
│   └── dynamics.py          # cohort ideology/salience drift with per-cause deltas
├── voting/
│   ├── model.py             # VotingModel protocol + SpatialLogitModel (utility parts)
│   ├── allocation.py        # d'Hondt, Sainte-Laguë, largest remainder, FPTP
│   ├── districts.py         # district apportionment + composition matrices
│   └── elections.py         # FPTP / PR / MMP / two-round orchestration
├── parties/
│   ├── ai.py                # repositioning (analytic vote gradient), funding, leaders
│   ├── relations.py         # trust / hostility / affinity matrices with memory
│   ├── coalition.py         # formateur-based coalition formation
│   ├── government.py        # confidence votes, collapse, legislation, reshuffles
│   └── lifecycle.py         # splits, mergers, dissolutions, new-party entry
├── events/
│   ├── schema.py            # EventDef + Effect models (Pydantic)
│   ├── expr.py              # safe AST expression evaluator (no eval)
│   ├── engine.py            # roll, apply, cascade, active-effect bookkeeping
│   └── library/*.yaml       # 60+ data-driven events
├── history/
│   ├── log.py               # HistoryEntry, HistoryLog (pandas-friendly)
│   ├── narrative.py         # Narrator protocol + TemplateNarrator
│   ├── store.py             # SQLite persistence (runs, history, snapshots)
│   └── export.py            # Markdown / JSON / CSV / Parquet
├── analytics/
│   └── metrics.py           # ENP, Gallagher, Pedersen, polarization, ...
├── engine/
│   ├── state.py             # SimState dataclasses (NumPy arrays)
│   ├── simulation.py        # Simulation: tick(), run(), interventions
│   ├── polling.py           # poll + exact telescoping cause attribution
│   └── snapshot.py          # pickle+zlib snapshot incl. RNG state, fork()
├── calibration/
│   └── harness.py           # parallel seeded runs -> pandas report vs real ranges
└── api/
    ├── app.py               # FastAPI REST + static prod serving
    ├── sessions.py          # in-memory session manager
    └── ws.py                # WebSocket tick streaming
frontend/                    # Vite + React (JSX) + D3 + Chart.js, Vectorheart theme
configs/                     # example scenarios
tests/                       # pytest + hypothesis
```

## 2. Data model (engine-internal)

| Entity | Representation |
|---|---|
| Ideology | `float64[D]` in `[-1, 1]` (config/UI uses `-100..100`) |
| Cohorts | struct-of-arrays: `size[N]`, `attrs[N,K]` (int categories), `region[N]`, `mean[N,D]`, `cov[N,D,D]`, `salience[N,D]`, `turnout[N]`, `loyalty[N,M]`, `media[N]` |
| Parties | list of `PartyState` dataclasses with stable integer index; inactive parties keep their slot |
| Relations | `trust[M,M]`, `hostility[M,M]`, `affinity[M,M]` (directed, bounded) |
| Regions | NetworkX graph + arrays (`wealth`, `unemployment_offset`, `regionalism`, ...) |
| Economy | dict of indicators driven by OU processes |
| History | list of `HistoryEntry` (typed records) -> DataFrame / SQLite |

## 3. Tick pipeline (1 tick = 1 month by default)

```mermaid
flowchart LR
  A[economy.step] --> B[events.roll+apply]
  B --> C[opinion.step]
  C --> D[demography yearly]
  D --> E[parties.adapt]
  E --> F[relations.update]
  F --> G[government.step]
  G --> H{election due?}
  H -- yes --> I[campaign -> vote -> seats -> coalition]
  H -- no --> J[poll + attribution]
  I --> J --> K[history.write]
```

## 4. Library choices

* **NumPy** for everything vectorized (utility tensor `N x M x D`), **SciPy** for Voronoi/Delaunay and distributions, **pandas** for history/analytics tables, **NetworkX** for adjacency and alliance graphs.
* **Pydantic v2** models are the single source of truth; `/api/schema` serves their JSON Schema and the frontend renders forms from it (with `json_schema_extra` UI hints).
* **FastAPI** + **uvicorn** (REST + WebSocket), plain **sqlite3** for persistence, **Typer** CLI.
* Frontend: **Vite + React (JSX)**, **D3** (graph, heatmap, map, compass), **Chart.js** (time series).

## 5. Determinism

`RngStreams(seed)` builds a root `SeedSequence` and derives a child per subsystem by **name hash** (`economy`, `events`, `elections`, `party_ai`, `demographics`, `opinion`, `generation`, `lifecycle`, `government`). Adding a new stream never shifts an existing one. Narrative variation uses a hash of the entry ID (no RNG). Snapshots pickle every `Generator.bit_generator.state`.

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Degenerate dominance / chaos | Thermostatic opinion, cost of ruling, mean-reversion to demographic baselines; calibration harness flags out-of-range outputs |
| Performance (100 yrs < seconds) | Struct-of-arrays, analytic gradients for party AI, district loops only on election ticks |
| Causality opacity | Telescoping attribution of poll changes by utility component; every event/decision logs `causes` |
| Schema drift between Python & JS | Forms generated from served JSON Schema |
| Python 3.14 wheel availability | Minimal deps; Parquet export optional (pyarrow) |
