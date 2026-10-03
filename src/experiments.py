"""
Initial parameter experiments for the parking-search ABM.

This file is the main implementation for Issue 4.

The model itself is defined in src/model.py.  Here we:
1. run one parameter condition;
2. calculate extra analysis metrics for persistent search congestion;
3. repeat conditions across several random seeds;
4. save raw and aggregated CSV files.

The parameter values below are exploratory model values for Checkpoint 2.
They are not claimed to be measured UWA traffic or parking data.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable

from src.model import ParkingModel


# Fixed model structure used for the first Checkpoint 2 experiment.
ROAD_LENGTH = 30
N_SPACES = 12
INITIAL_OCCUPANCY = 0.75
PARKING_MANOEUVRE_STEPS = 2

# First exploratory parameter grid.
ARRIVAL_PROBS = (0.10, 0.30, 0.50)
MEAN_PARKING_DURATIONS = (10, 20, 30)

# Compare no policy with one simple occupancy-based threshold.
ENTRY_CONTROL_CASES = (
    (False, 0.80),
    (True, 0.80),
)

DEFAULT_STEPS = 400
DEFAULT_SEEDS = tuple(range(10))
LATE_FRACTION = 0.20


def _safe_mean(values):
    """Return the mean, or NaN if the list is empty."""
    values = list(values)
    return mean(values) if values else math.nan


def analyse_model(model: ParkingModel, steps: int) -> dict:
    """
    Calculate experiment outcomes from one completed model run.

    The most useful extra metric is late_mean_searching: the average number of
    SEARCHING cars during the final 20% of the run.  This helps distinguish a
    short temporary build-up from congestion that remains late in the run.

    We deliberately keep it as a continuous indicator instead of declaring an
    arbitrary binary 'tipping point'.
    """
    records = model.step_results

    if not records:
        raise ValueError("The model has no recorded steps.")

    late_start = max(0, int(len(records) * (1.0 - LATE_FRACTION)))
    late_records = records[late_start:]

    searching = [r["searching_inside"] for r in records]
    late_searching = [r["searching_inside"] for r in late_records]
    waiting = [r["waiting_outside"] for r in records]
    late_waiting = [r["waiting_outside"] for r in late_records]
    occupancies = [r["parking_occupancy"] for r in records]
    blocked = [r["blocked_by_parking"] for r in records]

    parked_results = model.parking_results

    # These means only use cars that successfully parked before the run ended.
    # We therefore also report unfinished_vehicle_count and final queue sizes.
    mean_search_time = _safe_mean(
        r["parking_search_time"] for r in parked_results
    )
    mean_outside_waiting_time = _safe_mean(
        r["outside_waiting_time"] for r in parked_results
    )
    mean_total_waiting_time = _safe_mean(
        r["total_waiting_time"] for r in parked_results
    )

    state_counts = {
        state: sum(1 for car in model.vehicles.values() if car.state == state)
        for state in ("WAITING", "SEARCHING", "PARKING", "PARKED", "DONE")
    }

    initial_vehicle_count = round(INITIAL_OCCUPANCY * N_SPACES)
    generated_arrivals = max(0, len(model.vehicles) - initial_vehicle_count)
    successful = len(parked_results)

    completion_fraction = (
        successful / generated_arrivals if generated_arrivals else math.nan
    )

    return {
        "steps": steps,
        "mean_searching_cars": mean(searching),
        "max_searching_cars": max(searching),
        "late_mean_searching": mean(late_searching),
        "search_clear_fraction": sum(x == 0 for x in searching) / len(searching),
        "mean_waiting_outside": mean(waiting),
        "late_mean_waiting_outside": mean(late_waiting),
        "final_waiting_outside": records[-1]["waiting_outside"],
        "mean_occupancy": mean(occupancies),
        "mean_blocked_by_parking": mean(blocked),
        "mean_search_time": mean_search_time,
        "mean_outside_waiting_time": mean_outside_waiting_time,
        "mean_total_waiting_time": mean_total_waiting_time,
        "successful_parking_count": successful,
        "generated_arrivals": generated_arrivals,
        "completion_fraction": completion_fraction,
        "unfinished_vehicle_count": (
            state_counts["WAITING"]
            + state_counts["SEARCHING"]
            + state_counts["PARKING"]
        ),
        "final_searching": state_counts["SEARCHING"],
        "final_parking_manoeuvre": state_counts["PARKING"],
    }


def run_condition(
    arrival_prob: float,
    mean_parking_duration: float,
    entry_control: bool,
    entry_threshold: float = 0.80,
    seed: int = 0,
    steps: int = DEFAULT_STEPS,
    return_model: bool = False,
):
    """Run one experimental condition and return its measurements."""
    model = ParkingModel(
        road_length=ROAD_LENGTH,
        n_spaces=N_SPACES,
        initial_occupancy=INITIAL_OCCUPANCY,
        parking_manoeuvre_steps=PARKING_MANOEUVRE_STEPS,
        arrival_prob=arrival_prob,
        mean_parking_duration=mean_parking_duration,
        entry_control=entry_control,
        entry_threshold=entry_threshold,
        seed=seed,
    )

    model.run(steps=steps)

    result = {
        "seed": seed,
        "arrival_prob": arrival_prob,
        "mean_parking_duration": mean_parking_duration,
        "entry_control": entry_control,
        "entry_threshold": entry_threshold,
    }
    result.update(analyse_model(model, steps))

    if return_model:
        return result, model

    return result


def _csv_value(value):
    """Write NaN as a blank cell so the CSV is easier to read."""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return value


def write_csv(rows: list[dict], path: Path):
    """Write a list of dictionaries to CSV."""
    if not rows:
        raise ValueError("No rows to write.")

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()

        for row in rows:
            writer.writerow({k: _csv_value(v) for k, v in row.items()})


def aggregate_results(raw_rows: list[dict]) -> list[dict]:
    """Average repeated seeds for each parameter condition."""
    metric_names = [
        "mean_searching_cars",
        "max_searching_cars",
        "late_mean_searching",
        "search_clear_fraction",
        "mean_waiting_outside",
        "late_mean_waiting_outside",
        "final_waiting_outside",
        "mean_occupancy",
        "mean_blocked_by_parking",
        "mean_search_time",
        "mean_outside_waiting_time",
        "mean_total_waiting_time",
        "successful_parking_count",
        "generated_arrivals",
        "completion_fraction",
        "unfinished_vehicle_count",
        "final_searching",
        "final_parking_manoeuvre",
    ]

    groups = {}

    for row in raw_rows:
        key = (
            row["arrival_prob"],
            row["mean_parking_duration"],
            row["entry_control"],
            row["entry_threshold"],
        )
        groups.setdefault(key, []).append(row)

    summary_rows = []

    for key in sorted(groups, key=lambda x: (x[0], x[1], x[2])):
        arrival_prob, duration, control, threshold = key
        group = groups[key]

        summary = {
            "arrival_prob": arrival_prob,
            "mean_parking_duration": duration,
            "entry_control": control,
            "entry_threshold": threshold,
            "n_seeds": len(group),
        }

        for metric in metric_names:
            values = [
                float(r[metric])
                for r in group
                if not (
                    isinstance(r[metric], float)
                    and math.isnan(r[metric])
                )
            ]

            summary[f"{metric}_mean"] = _safe_mean(values)
            summary[f"{metric}_sd"] = (
                pstdev(values) if len(values) >= 2 else 0.0
            )

        summary_rows.append(summary)

    return summary_rows


def run_initial_sweep(
    output_dir: str | Path = "data",
    seeds: Iterable[int] = DEFAULT_SEEDS,
    steps: int = DEFAULT_STEPS,
):
    """
    Run the first Checkpoint 2 parameter sweep.

    Grid:
    - arrival probability: 0.10, 0.30, 0.50
    - mean parking duration: 10, 20, 30 steps
    - entry control: off / on at threshold 0.80
    - 10 random seeds by default

    This gives 18 parameter conditions and 180 runs.
    """
    rows = []

    for arrival_prob in ARRIVAL_PROBS:
        for duration in MEAN_PARKING_DURATIONS:
            for entry_control, threshold in ENTRY_CONTROL_CASES:
                for seed in seeds:
                    rows.append(
                        run_condition(
                            arrival_prob=arrival_prob,
                            mean_parking_duration=duration,
                            entry_control=entry_control,
                            entry_threshold=threshold,
                            seed=seed,
                            steps=steps,
                        )
                    )

    summary_rows = aggregate_results(rows)

    output_dir = Path(output_dir)
    raw_path = output_dir / "initial_sweep_raw.csv"
    summary_path = output_dir / "initial_sweep_summary.csv"

    write_csv(rows, raw_path)
    write_csv(summary_rows, summary_path)

    return rows, summary_rows


def _print_checkpoint_examples(summary_rows: list[dict]):
    """Print a few easy-to-explain preliminary conditions."""
    wanted = [
        (0.10, 10, False),
        (0.30, 20, False),
        (0.50, 30, False),
        (0.50, 30, True),
    ]

    print("\nSelected preliminary conditions")
    print("-" * 76)
    print(
        "arrival  duration  control   late-search   late-outside   total-wait"
    )

    for arrival, duration, control in wanted:
        row = next(
            r
            for r in summary_rows
            if r["arrival_prob"] == arrival
            and r["mean_parking_duration"] == duration
            and r["entry_control"] == control
        )

        print(
            f"{arrival:>7.2f}"
            f"{duration:>10}"
            f"{str(control):>9}"
            f"{row['late_mean_searching_mean']:>14.2f}"
            f"{row['late_mean_waiting_outside_mean']:>15.2f}"
            f"{row['mean_total_waiting_time_mean']:>13.2f}"
        )


def main():
    _, summary_rows = run_initial_sweep()
    print(
        "Initial sweep complete: 18 conditions x 10 seeds = 180 runs.\n"
        "Saved data/initial_sweep_raw.csv and data/initial_sweep_summary.csv."
    )
    _print_checkpoint_examples(summary_rows)


if __name__ == "__main__":
    main()
