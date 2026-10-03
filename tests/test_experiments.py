"""Small tests for the Issue 4 experiment runner."""

from src.experiments import aggregate_results, run_condition


def test_run_condition_returns_analysis_metrics():
    result = run_condition(
        arrival_prob=0.1,
        mean_parking_duration=10,
        entry_control=False,
        seed=1,
        steps=30,
    )

    assert result["late_mean_searching"] >= 0
    assert result["final_waiting_outside"] >= 0
    assert 0 <= result["search_clear_fraction"] <= 1
    assert result["unfinished_vehicle_count"] >= 0


def test_aggregate_results_combines_repeated_seeds():
    rows = [
        run_condition(0.1, 10, False, seed=0, steps=20),
        run_condition(0.1, 10, False, seed=1, steps=20),
    ]

    summary = aggregate_results(rows)

    assert len(summary) == 1
    assert summary[0]["n_seeds"] == 2
    assert summary[0]["arrival_prob"] == 0.1
    assert summary[0]["mean_parking_duration"] == 10
