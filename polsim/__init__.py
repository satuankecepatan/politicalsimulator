"""polsim — agent-based political simulation sandbox.

The engine is fully usable without the API or UI::

    from polsim import Simulation, load_scenario
    sim = Simulation(load_scenario("configs/example.yaml"), seed=123)
    sim.run(years=50)
    print(sim.history.to_frame().tail())
"""

from polsim.config.loader import load_scenario, save_scenario
from polsim.config.schema import ScenarioConfig

__all__ = ["ScenarioConfig", "Simulation", "load_scenario", "save_scenario"]
__version__ = "0.1.0"


def __getattr__(name: str) -> object:
    # Lazy import keeps `import polsim.config` light and avoids import cycles.
    if name == "Simulation":
        from polsim.engine.simulation import Simulation

        return Simulation
    raise AttributeError(name)
