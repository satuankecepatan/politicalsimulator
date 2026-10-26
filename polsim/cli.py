"""Command-line interface for polsim using Typer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from polsim.config.loader import get_json_schema, load_scenario, save_scenario
from polsim.config.presets import PRESETS, build_scenario

app = typer.Typer(
    name="polsim",
    help="Agent-based political simulation sandbox.",
    no_args_is_help=True,
)


@app.command()
def schema(
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="File path to write JSON schema to"),
) -> None:
    """Export the ScenarioConfig OpenAPI / JSON Schema."""
    sc = get_json_schema()
    dumped = json.dumps(sc, indent=2)
    if out:
        out.write_text(dumped, encoding="utf-8")
        typer.echo(f"Wrote JSON schema to {out}")
    else:
        typer.echo(dumped)


@app.command()
def preset(
    name: str = typer.Argument("industrial_democracy", help="Preset name"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output YAML/JSON file path"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all available presets"),
) -> None:
    """Generate or inspect scenario presets."""
    if list_all:
        typer.echo("Available presets:")
        for k in PRESETS:
            typer.echo(f"  - {k}")
        return

    sc = build_scenario(name)
    if out:
        save_scenario(sc, out)
        typer.echo(f"Saved preset '{name}' to {out}")
    else:
        typer.echo(f"Built preset '{name}': {sc.name} ({len(sc.parties)} parties, {sc.country.population} pop)")


@app.command()
def run(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to scenario YAML/JSON"),
    preset_name: str = typer.Option("industrial_democracy", "--preset", "-p", help="Preset if no config given"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for deterministic run"),
    years: int = typer.Option(20, "--years", "-y", help="Years to simulate"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Export history CSV/JSON path"),
) -> None:
    """Run a political simulation."""
    from polsim.engine.simulation import Simulation

    if config and config.is_file():
        sc = load_scenario(config)
    else:
        sc = build_scenario(preset_name, seed=seed, years=years)

    sc.settings.seed = seed
    sc.settings.years = years

    typer.echo(f"Initializing simulation: {sc.name} (Seed: {seed}, {years} years)...")
    sim = Simulation(sc)
    sim.run(years=years)
    typer.echo(f"Simulation completed: {sim.state.tick} ticks ({sim.state.date.format()}).")

    if out:
        sim.history.export(out)
        typer.echo(f"Exported history to {out}")


@app.command()
def calibrate(
    preset_name: str = typer.Option("industrial_democracy", "--preset", "-p"),
    runs: int = typer.Option(5, "--runs", "-n", help="Number of seeded runs to evaluate"),
    years: int = typer.Option(15, "--years", "-y", help="Years per run"),
    workers: int = typer.Option(2, "--workers", "-w", help="Parallel worker processes"),
) -> None:
    """Run calibration batch and evaluate against documented empirical ranges."""
    from polsim.calibration.harness import CalibrationHarness

    sc = build_scenario(preset_name)
    harness = CalibrationHarness(sc)
    typer.echo(f"Running calibration harness ({runs} parallel runs of {years} years)...")
    df = harness.run_batch(n_runs=runs, years=years, max_workers=workers)
    report = harness.evaluate_calibration(df)

    typer.echo("\n--- CALIBRATION REPORT ---")
    typer.echo(f"Mean National Turnout: {report['mean_turnout']:.1%}")
    typer.echo(f"Effective Parties (ENP): {report['mean_enp']}")
    typer.echo(f"Disproportionality (Gallagher): {report['mean_gallagher']}")
    if report["flags"]:
        typer.echo("\n[!] Warnings:")
        for flag in report["flags"]:
            typer.echo(f"  * {flag}")
    else:
        typer.echo("\n[OK] All simulation indicators fall within empirical bounds.")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the FastAPI backend server."""
    import uvicorn
    uvicorn.run("polsim.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
