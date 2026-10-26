import hypothesis.strategies as st
from hypothesis import given, settings
import numpy as np

from polsim.config.presets import build_scenario
from polsim.core.mathx import clamp
from polsim.voting.allocation import allocate_seats


@given(
    v1=st.floats(min_value=1.0, max_value=100000.0),
    v2=st.floats(min_value=1.0, max_value=100000.0),
    v3=st.floats(min_value=1.0, max_value=100000.0),
    seats=st.integers(min_value=5, max_value=250),
)
@settings(max_examples=30)
def test_property_seats_sum_to_total(v1, v2, v3, seats):
    votes = np.array([v1, v2, v3], dtype=np.float64)
    allocated = allocate_seats(votes, total_seats=seats, formula="dhondt", threshold=0.0)
    assert int(np.sum(allocated)) == seats
    assert np.all(allocated >= 0)


@given(
    coords=st.lists(st.floats(min_value=-500.0, max_value=500.0), min_size=5, max_size=20),
)
@settings(max_examples=30)
def test_property_ideology_coordinates_bounded(coords):
    arr = np.array(coords, dtype=np.float64)
    clamped = clamp(arr, -1.0, 1.0)
    assert np.all(clamped >= -1.0)
    assert np.all(clamped <= 1.0)
