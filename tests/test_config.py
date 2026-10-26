import pytest
from polsim.config.loader import get_json_schema, load_scenario, save_scenario
from polsim.config.presets import PRESETS, build_scenario
from polsim.config.schema import ScenarioConfig


def test_default_scenario_valid():
    sc = build_scenario("industrial_democracy")
    assert isinstance(sc, ScenarioConfig)
    assert len(sc.axes) == 7
    assert len(sc.parties) == 5
    assert sc.country.n_regions == 8


def test_all_presets_valid():
    for name in PRESETS:
        sc = build_scenario(name)
        assert sc.demographics.preset == name
        assert len(sc.parties) >= 2


def test_yaml_roundtrip(tmp_path):
    sc = build_scenario("industrial_democracy", seed=99, years=30)
    file_path = tmp_path / "scenario.yaml"
    save_scenario(sc, file_path)
    loaded = load_scenario(file_path)
    assert loaded.name == sc.name
    assert loaded.settings.seed == sc.settings.seed
    assert len(loaded.parties) == len(sc.parties)


def test_schema_generation():
    schema = get_json_schema()
    assert "properties" in schema
    assert "axes" in schema["properties"]
    assert "parties" in schema["properties"]


def test_invalid_party_axis():
    sc = build_scenario()
    # Add party with unknown axis
    sc.parties[0].ideology["unknown_axis_xyz"] = 50.0
    with pytest.raises(ValueError, match="unknown axes"):
        sc.model_validate(sc.model_dump())
