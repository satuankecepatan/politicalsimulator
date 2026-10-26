"""FastAPI REST and WebSocket application."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Literal
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from polsim.api.sessions import manager
from polsim.api.ws import router as ws_router
from polsim.config.loader import get_json_schema
from polsim.config.presets import PRESETS, build_scenario
from polsim.config.schema import ScenarioConfig
from polsim.history.export import export_markdown_chronicle
from polsim.history.store import HistoryStore

app = FastAPI(
    title="polsim API",
    description="Agent-based political simulation sandbox backend.",
    version="0.1.0",
)

# CORS middleware for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
store = HistoryStore()


# ---------------------------------------------------------------------------
# Schema & Presets
# ---------------------------------------------------------------------------


@app.get("/api/schema")
def get_schema() -> dict[str, Any]:
    """Return JSON Schema for ScenarioConfig with UI metadata annotations."""
    return get_json_schema()


@app.get("/api/presets")
def list_presets() -> list[str]:
    """Return names of built-in demographic presets."""
    return list(PRESETS.keys())


@app.get("/api/presets/{name}")
def get_preset_scenario(name: str) -> dict[str, Any]:
    """Return a complete ScenarioConfig generated from preset."""
    if name not in PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    sc = build_scenario(name)
    return sc.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Simulation Sessions
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    config: ScenarioConfig | None = None
    preset: str = "industrial_democracy"
    seed: int = 42
    country: dict[str, Any] | None = None
    institutions: dict[str, Any] | None = None
    parties: list[dict[str, Any]] | None = None
    events: dict[str, Any] | None = None


@app.post("/api/sessions")
def create_session(req: CreateSessionRequest) -> dict[str, Any]:
    """Initialize a new simulation session."""
    if req.config:
        sc = req.config
    else:
        sc = build_scenario(req.preset, seed=req.seed)
        sc.settings.seed = req.seed
        if req.country:
            if "name" in req.country:
                sc.country.name = req.country["name"]
            if "population" in req.country:
                sc.country.population = int(req.country["population"])
            if "n_regions" in req.country:
                sc.country.n_regions = int(req.country["n_regions"])
        if req.institutions:
            if "electoral_system" in req.institutions:
                sc.institutions.electoral_system = req.institutions["electoral_system"]
            if "seats" in req.institutions:
                sc.institutions.seats = int(req.institutions["seats"])
            if "threshold" in req.institutions:
                sc.institutions.threshold = float(req.institutions["threshold"])
        if req.events and "chaos_level" in req.events:
            sc.events.chaos_level = float(req.events["chaos_level"])
        if req.parties:
            from polsim.config.schema import PartyConfig
            party_field_names = set(PartyConfig.model_fields.keys())
            clean_parties = []
            for p in req.parties:
                p_copy = dict(p)
                if "abbr" in p_copy and "abbreviation" not in p_copy:
                    p_copy["abbreviation"] = p_copy["abbr"]
                if "id" not in p_copy or not p_copy["id"]:
                    p_copy["id"] = p_copy.get("abbreviation", "pty").lower().replace(" ", "_")
                if "color" in p_copy and p_copy["color"] and not str(p_copy["color"]).startswith("#"):
                    p_copy["color"] = f"#{p_copy['color']}"
                filtered = {k: v for k, v in p_copy.items() if k in party_field_names}
                clean_parties.append(PartyConfig.model_validate(filtered))
            if clean_parties:
                sc.parties = clean_parties

    session_id, sim = manager.create(sc, seed=sc.settings.seed)
    return {
        "session_id": session_id,
        "name": sc.name,
        "summary": sim.get_status_summary(),
        "map": sim.map_data,
        "compass": sim.get_compass_preview(),
    }


@app.get("/api/sessions/{session_id}")
def get_session_status(session_id: str) -> dict[str, Any]:
    """Get current status summary for session."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    return sim.get_status_summary()


@app.post("/api/sessions/{session_id}/tick")
def step_simulation_tick(session_id: str) -> dict[str, Any]:
    """Step simulation by 1 tick."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    entries = sim.tick()
    return {
        "summary": sim.get_status_summary(),
        "compass": sim.get_compass_preview(),
        "entries": [e.to_dict() for e in entries],
    }


class RunRequest(BaseModel):
    years: int = 5


@app.post("/api/sessions/{session_id}/run")
def run_simulation(session_id: str, req: RunRequest) -> dict[str, Any]:
    """Advance simulation by N years."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    sim.run(years=req.years)
    return {
        "summary": sim.get_status_summary(),
        "compass": sim.get_compass_preview(),
        "recent_entries": [e.to_dict() for e in sim.history.entries[-30:]],
    }


@app.get("/api/sessions/{session_id}/compass")
def get_compass_data(session_id: str) -> dict[str, Any]:
    """Live 2D political compass coordinates."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    return sim.get_compass_preview()


@app.get("/api/sessions/{session_id}/map")
def get_territory_map(session_id: str) -> dict[str, Any]:
    """Territory GeoJSON polygonal / point map."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    return sim.map_data


@app.get("/api/sessions/{session_id}/history")
def get_history(
    session_id: str,
    entry_type: str | None = Query(None),
    actor: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    """Query and filter structured history entries."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    filtered = sim.history.filter(entry_type=entry_type, actor=actor)
    return [e.to_dict() for e in filtered[-limit:]]


class InterveneRequest(BaseModel):
    type: Literal["event", "party_position", "party_update"]
    event_id: str | None = None
    party_id: str | None = None
    name: str | None = None
    abbreviation: str | None = None
    color: str | None = None
    position: dict[str, float] | None = None


@app.post("/api/sessions/{session_id}/intervene")
def intervene(session_id: str, req: InterveneRequest) -> dict[str, Any]:
    """Trigger mid-run user intervention."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")

    if req.type == "event" and req.event_id:
        success = sim.intervene_trigger_event(req.event_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Event '{req.event_id}' not found")
    elif req.type in {"party_position", "party_update"} and req.party_id:
        sim.intervene_party(
            party_id=req.party_id,
            name=req.name,
            abbreviation=req.abbreviation,
            color=req.color,
            position=req.position,
        )

    return {"status": "ok", "summary": sim.get_status_summary()}


@app.post("/api/sessions/{session_id}/fork")
def fork_session(session_id: str, new_seed: int | None = None) -> dict[str, Any]:
    """Fork timeline into an alternate history session."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    forked = sim.fork(new_seed=new_seed)
    new_sid = manager.store_sim(forked)
    return {
        "session_id": new_sid,
        "summary": forked.get_status_summary(),
        "compass": forked.get_compass_preview(),
    }


@app.get("/api/sessions/{session_id}/export/{fmt}")
def export_history(session_id: str, fmt: Literal["markdown", "json", "csv"]) -> Response:
    """Export history in Markdown, JSON, or CSV."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")

    if fmt == "markdown":
        text = export_markdown_chronicle(sim.history, title=sim.config.name)
        return Response(content=text, media_type="text/markdown")
    elif fmt == "csv":
        df = sim.history.to_frame()
        out = io.StringIO()
        df.to_csv(out, index=False)
        return Response(content=out.getvalue(), media_type="text/csv")
    else:
        import json
        records = [e.to_dict() for e in sim.history.entries]
        return Response(content=json.dumps(records, indent=2), media_type="application/json")


@app.post("/api/sessions/{session_id}/save")
def save_session_to_db(session_id: str) -> dict[str, Any]:
    """Persist session and history records to SQLite."""
    sim = manager.get(session_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")
    store.save_run(
        run_id=session_id,
        config=sim.config,
        history=sim.history,
        snapshot_bytes=sim.snapshot(),
        tick=sim.state.tick,
    )
    return {"status": "saved", "run_id": session_id}


@app.get("/api/runs")
def list_saved_runs() -> list[dict[str, Any]]:
    """List all saved runs in SQLite database."""
    return store.list_runs()


# Static file serving for production single-process mode
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
