"""Optional entry-control comparison under fixed, scheduled demand."""
from pathlib import Path
from src.experiments import (
    aggregate_results,
    run_condition,
    write_csv,
)

def main():
    scenarios = [
        (False, 0.9),
        (True, 0.80),
        (True, 0.90),
        (True, 0.95),
    ]

    rows = [
        run_condition(
            burst_width=10,
            total_arrivals=24,
            mean_parking_duration=30,
            seed=seed,
            entry_control=enabled,
            entry_threshold=threshold,
        )
        for enabled, threshold in scenarios
        for seed in range(10)
    ]

    output = Path(__file__).resolve().parents[1] / "data"

    write_csv(
        rows,
        output / "burst_threshold_raw.csv",
    )

    write_csv(
        aggregate_results(rows),
        output / "burst_threshold_summary.csv",
    )

    print(
        f"Completed {len(rows)} runs; "
        "saved burst_threshold CSVs."
    )


if __name__ == "__main__":
    main()