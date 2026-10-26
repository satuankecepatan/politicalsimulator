# POLSIM // Political Simulation Sandbox

> Agent-based political simulation sandbox modeling the long-term political history of a fictional nation.
> Built with a high-performance **Python engine** and a **Vectorheart aesthetic web UI**.

---

## ◈ Core Architecture

- **Engine (Python 3.11+):**
  - **Probabilistic Spatial Voting Model:** Downsian ideological proximity with non-policy valence, historical partisan brand loyalty, retrospective economic voting, alienation & indifference abstention.
  - **Multi-Dimensional Ideology Space:** 7 configurable axes (`economic`, `social`, `authority`, `identity`, `secularism`, `environment`, `trust`) in `[-1.0, 1.0]`.
  - **Deterministic Multi-Stream RNG:** `SeedSequence` deriving independent child streams for economy, events, elections, party AI, demographics, and polling.
  - **Electoral Systems:** Proportional Representation (D'Hondt, Sainte-Laguë, Largest Remainder Hare/Droop), First-Past-The-Post (FPTP) with strategic voting, Mixed-Member Proportional (MMP), and Two-Round Runoff.
  - **Party Strategic AI:** Multi-force repositioning (vote-seeking, policy-seeking, office-seeking) bounded by pragmatism; internal factions, cohesion tracking, splits, and mergers.
  - **Coalition Bargaining:** Minimal Winning Coalitions (MWC), Gamson's Law portfolio allocation, confidence votes, and cordon sanitaire rules.
  - **Data-Driven Event System:** 60+ YAML events spanning 9 categories with safe AST precondition evaluation (no raw `eval`).
  - **Structured History & Narrative Layer:** Typed records persisted to SQLite, deterministic template prose, and exports (Markdown, JSON, CSV).
  - **Empirical Calibration Harness:** Parallel batch runs comparing turnout, ENP, and Gallagher disproportionality against documented political science benchmarks.

- **Frontend (Vectorheart Web App):**
  - Late 1990s / early 2000s neo-modernist vector design inspired by *The Designers Republic* and Y2K telemetry.
  - Razor-sharp geometry (45-degree chamfers, hazard stripes, zero border radius, monospace readouts).
  - D3.js interactive Political Compass (with draggable party repositioning), Territorial Map, and Parliamentary Alliance Network.
  - Chart.js electoral vote share trajectories.
  - Full scenario initialization wizard and executive intervention controls.

---

## ◈ Quickstart

### 1. Python Environment Setup
```bash
# Using uv or pip
uv pip install -e .
```

### 2. CLI Usage
```bash
# Run a simulation directly from the terminal
python -m polsim run --config configs/example.yaml --seed 123 --years 50

# Run parallel empirical calibration harness
python -m polsim calibrate --preset industrial_democracy --runs 5 --years 20

# Export OpenAPI JSON Schema
python -m polsim schema --out schema.json
```

### 3. Running the Web Application
```bash
# Start FastAPI backend (serving API, WebSocket, and built frontend)
python -m polsim serve --port 8000
```
Then navigate to `http://127.0.0.1:8000`.

To run Vite in hot-reloading development mode:
```bash
cd frontend
npm run dev
```

---

## ◈ Testing
```bash
# Run complete test suite (unit tests, property tests, snapshot determinism)
pytest -v
```
