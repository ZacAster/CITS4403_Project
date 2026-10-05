"""Tests for the timetable-driven arrival-burst experiment."""

# Import the experiment helpers that we want to check.
from src.experiments import (
    aggregate_results,
    build_arrival_times,
    run_condition,
)


def test_arrival_schedule_keeps_same_number_of_cars():
    """Changing burst width must not change the total number of arrivals."""

    # Build a very concentrated schedule.
    bursty_times = build_arrival_times(total_arrivals=24, burst_width=10)

    # Build a much more spread-out schedule.
    spread_times = build_arrival_times(total_arrivals=24, burst_width=60)

    # Both schedules must still contain exactly 24 cars.
    assert len(bursty_times) == 24
    assert len(spread_times) == 24

    # All arrival times should be valid non-negative simulation steps.
    assert min(bursty_times) >= 0
    assert min(spread_times) >= 0


def test_run_condition_returns_burst_metrics():
    """One simulation should return the main measurements used in the notebook."""

    # Use a small demand level so this test runs quickly and reliably.
    result = run_condition(
        burst_width=20,
        total_arrivals=12,
        mean_parking_duration=15,
        seed=1,
    )

    # The experiment should never create a negative wait or backlog.
    assert result["mean_total_waiting_time"] >= 0
    assert result["peak_total_backlog"] >= 0
    assert result["cumulative_backlog"] >= 0

    # The completion fraction is always a normal probability-like value.
    assert 0 <= result["completion_fraction"] <= 1

    # The fixed demand setting should really contain 12 scheduled cars.
    assert result["successful_parking_count"] <= 12


def test_aggregate_results_combines_repeated_seeds():
    """Two runs of the same condition should become one averaged summary row."""

    # Run exactly the same condition with two random seeds.
    rows = [
        run_condition(20, 12, 15, seed=0),
        run_condition(20, 12, 15, seed=1),
    ]

    # Average the two raw rows.
    summary = aggregate_results(rows)

    # There should now be one condition row.
    assert len(summary) == 1

    # The summary should remember that two seeds were used.
    assert summary[0]["n_seeds"] == 2

    # The condition settings should not change during aggregation.
    assert summary[0]["burst_width"] == 20
    assert summary[0]["total_arrivals"] == 12
    assert summary[0]["mean_parking_duration"] == 15
