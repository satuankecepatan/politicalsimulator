# ASSUMPTIONS

Ambiguities in the spec and the decisions taken. Each is a reasonable default and can be revisited.

## Modeling

1. **Ideology scale.** Config and UI use `-100..+100` per axis (spec). The engine divides by 100 and works in `[-1, 1]` (MATHEMATICIAN.md). Conversion happens only at the config/API boundary.
2. **Cohort generation.** A full cross-product of 7 demographic dimensions (~1,150 cells per region) is far beyond "~100 cohorts". Instead each region gets `cohorts_per_region` *archetype cohorts* whose attributes are sampled sequentially from region marginals with configurable log-odds correlations (e.g. urban -> tertiary education). Cohort sizes are Dirichlet-distributed.
3. **Cohort ideology covariance** is stored (`N x D x D`) and used through **sigma points** (unscented transform, `2D+1` points per cohort) in the voting model, so a dispersed cohort genuinely splits its vote. Under quadratic utility the covariance would otherwise cancel out of the logit.
4. **Individual-agents mode** = the same engine with many cohorts of near-zero covariance, each representing `population / n_agents` people. No separate code path.
5. **Strategic voting (FPTP)** is computed per district at cohort level: a configurable share of each cohort's probability mass on non-top-two parties is re-cast between the top two using that cohort's own utilities.
6. **Two-round runoff** applies to single-member districts (legislative) and to the presidency in presidential regimes. Round two recomputes cohort choice restricted to the two finalists.
7. **Mixed-member** is implemented as the additional-member (compensatory, modified d'Hondt) method, so total seats stay fixed (no overhang).
8. **Districts.** Seats are apportioned to regions by population (largest remainder). Each district has a Dirichlet-perturbed composition over its region's cohorts, making districts within a region differ.
9. **Economy** indicators are national OU processes; regions get persistent offsets. Government economic positioning shifts the long-run equilibria **symmetrically** (growth vs. inequality tradeoff), so no ideology is privileged.
10. **Party repositioning** uses the analytic gradient of expected vote share (vote-seeking), a pull back to the party's factions (policy-seeking) and toward likely partners (office-seeking), step-bounded by pragmatism. Evaluated quarterly.
11. **Factions.** Each party is generated with 2–3 internal factions; cohesion falls when the leadership position drifts away from them. Splits spawn a new party at the disgruntled faction's position.
12. **Relationship scales.** `trust`, `hostility` in `[0, 1]`; `affinity` in `[-1, 1]`. Grudge half-life (default 96 months) > goodwill half-life (default 24 months).
13. **Cordon sanitaire** is a configurable rule list (`axis`, `beyond`), not a hardcoded ideology. Any axis/side can be made taboo.
14. **Presidential regime:** the president's party leads the cabinet; no confidence votes; divided government lowers legislative success.
15. **Poll attribution.** Monthly poll changes are decomposed with an exact telescoping sequence over utility components (voter drift, party moves, valence, economy, incumbency, scandals, loyalty, demographics, turnout). Deltas sum exactly to the total change.

## Engineering

16. **Python 3.14** is the installed interpreter; code targets 3.11+ syntax.
17. **Dependency management:** `uv` with `pyproject.toml`; `requirements.txt` kept for pip users.
18. **Snapshots** use `pickle + zlib` of the full state (including RNG bit-generator states). They are local, trusted files; JSON export exists for interchange.
19. **SQLite** via the standard `sqlite3` module (no SQLAlchemy) to keep dependencies minimal.
20. **Parallel calibration** uses `concurrent.futures.ProcessPoolExecutor` (stdlib) instead of joblib.
21. **History IDs** are `"{run_id}:{tick}:{seq}"`-style deterministic strings (`e{tick:05d}-{seq:03d}`), stable for identical seed + config.
22. **Narrative variation** is selected by hashing the entry ID, so prose never consumes simulation RNG.
23. **Frontend** follows the repository Vectorheart aesthetic (AGENT.md): obsidian/slate/white backgrounds, signal-orange/lime/cyan/yellow accents, zero border radius, chamfers, monospace data readouts.
24. **Charts** use Chart.js (spec allows Chart.js or Recharts).
25. **Sessions** live in server memory; persistence to SQLite happens on explicit save.
26. **Dates:** simulation starts in a configurable year (default 2000), month 1.
