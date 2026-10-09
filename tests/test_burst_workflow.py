"""Checks for fixed demand, incomplete parking and animation consistency."""
import pytest
from copy import deepcopy
from src.experiments import (
    aggregate_results,
    build_arrival_times,
    run_condition,
)
from src.animate_model import (
    advance_to_step,
    create_comparison,
)

def test_reject_invalid_schedules():
    for total, width in [(0, 10), (24, 0), (24, 81)]:
        with pytest.raises(ValueError):
            build_arrival_times(total, width)


def test_horizon_must_include_all_arrivals():
    with pytest.raises(ValueError):
        run_condition(60, 24, 30, steps=69)


def test_parking_completion_is_not_departure():
    result, model = run_condition(
        1,
        1,
        1e9,
        seed=1,
        initial_occupancy=0,
        steps=70,
        return_model=True,
    )

    assert result["completion_fraction"] == 1
    assert result["departed_count"] == 0
    assert any(
        car.state == "PARKED"
        for car in model.vehicles.values()
    )


def test_incomplete_parking_is_reported():
    result = run_condition(
        10,
        24,
        1e9,
        seed=1,
        initial_occupancy=1,
        steps=70,
        entry_control=True,
        entry_threshold=1,
    )

    assert result["arrived_count"] == 24
    assert result["successful_parking_count"] == 0
    assert result["unfinished_parking_count"] == 24
    assert result["completion_fraction"] == 0
    assert result["final_total_backlog"] == 24


def test_different_controls_are_not_averaged_together():
    rows = [
        run_condition(
            10,
            12,
            15,
            entry_control=enabled,
        )
        for enabled in (False, True)
    ]

    assert len(aggregate_results(rows)) == 2


def test_repeated_animation_frame_does_not_step_twice():
    models, schedules = create_comparison()

    advance_to_step(models, schedules, 40)

    before = [
        list(model.step_results)
        for model in models
    ]

    advance_to_step(models, schedules, 40)

    assert [model.step_results for model in models] == before
    assert [model.time for model in models] == [40, 40]


def test_animation_matches_experiment():
    models, schedules = create_comparison(24, 30, 3)

    advance_to_step(models, schedules, 300)

    for width, model in zip((10, 60), models):
        result, expected = run_condition(
            width,
            24,
            30,
            seed=3,
            return_model=True,
        )

        assert model.step_results == expected.step_results
        assert model.parking_results == expected.parking_results
        assert model.vehicles == expected.vehicles
        assert result["arrived_count"] == 24

def test_earlier_target_leaves_model_state_unchanged():
    models, schedules = create_comparison()
    advance_to_step(models, schedules, 40)

    def snapshot(model):
        return deepcopy({
            "time": model.time,
            "road": model.road,
            "spots": model.spots,
            "waiting_queue": model.waiting_queue,
            "vehicles": model.vehicles,
            "next_vid": model.next_vid,
            "step_results": model.step_results,
            "parking_results": model.parking_results,
            "blocked_count": model.current_blocked_count,
            "rng_state": model.rng.bit_generator.state,
        })

    before = [snapshot(model) for model in models]

    # Request an earlier frame after both models have reached step 40.
    advance_to_step(models, schedules, 20)

    assert [model.time for model in models] == [40, 40]
    assert [snapshot(model) for model in models] == before
