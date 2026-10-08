"""Fixed-demand arrival experiments for the parking-search model."""

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev

from src.model import ParkingModel

ROAD_LENGTH = 30
N_SPACES = 12
INITIAL_OCCUPANCY = 0.75
PARKING_MANOEUVRE_STEPS = 2
ENTRY_CONTROL = False
ARRIVAL_CENTER = 40
TOTAL_ARRIVALS_CASES = (12, 18, 24)
BURST_WIDTHS = (10, 20, 40, 60)
MEAN_PARKING_DURATIONS = (15, 30, 60)
SIMULATION_STEPS = 300
DEFAULT_SEEDS = tuple(range(10))

CONDITION_FIELDS = (
    "burst_width", "total_arrivals", "mean_parking_duration",
    "initial_occupancy", "steps", "entry_control", "entry_threshold",
)

METRICS = (
    "mean_total_waiting_time", "max_total_waiting_time",
    "peak_searching_inside", "peak_waiting_outside",
    "peak_total_backlog", "cumulative_backlog",
    "mean_blocked_by_parking", "mean_occupancy",
    "successful_parking_count", "completion_fraction",
    "arrived_count", "unfinished_parking_count",
    "departed_count", "final_total_backlog",
)


def build_arrival_times(total_arrivals, burst_width):
    """Place an exact number of arrivals within a centred, discrete window."""
    if not isinstance(total_arrivals, int) or total_arrivals < 1:
        raise ValueError("total_arrivals must be a positive integer")

    if not isinstance(burst_width, int) or not 1 <= burst_width <= 80:
        raise ValueError("burst_width must be an integer from 1 to 80")

    if total_arrivals == 1:
        return [ARRIVAL_CENTER]

    start = ARRIVAL_CENTER - burst_width // 2

    return [
        start + round(i * (burst_width - 1) / (total_arrivals - 1))
        for i in range(total_arrivals)
    ]


def build_arrival_counts(total_arrivals, burst_width):
    return dict(Counter(build_arrival_times(total_arrivals, burst_width)))


def add_scheduled_arrival(model):
    """Queue an outside arrival before the existing model update."""
    car = model._new_vehicle()
    car.arrival_time = model.time
    car.state = "WAITING"
    car.road_pos = None
    model.waiting_queue.append(car.vid)
    return car.vid


def create_burst_model(
    mean_parking_duration=30,
    seed=0,
    *,
    initial_occupancy=INITIAL_OCCUPANCY,
    entry_control=ENTRY_CONTROL,
    entry_threshold=0.9,
):
    """Shared model configuration for experiments and animation."""
    return ParkingModel(
        road_length=ROAD_LENGTH,
        n_spaces=N_SPACES,
        initial_occupancy=initial_occupancy,
        parking_manoeuvre_steps=PARKING_MANOEUVRE_STEPS,
        arrival_prob=0.0,
        mean_parking_duration=mean_parking_duration,
        entry_control=entry_control,
        entry_threshold=entry_threshold,
        seed=seed,
    )


def step_scheduled_model(model, arrival_counts):
    """Apply scheduled arrivals and then advance exactly one model step."""
    if model.arrival_prob != 0:
        raise ValueError("Scheduled experiments require arrival_prob=0")

    for _ in range(arrival_counts.get(model.time, 0)):
        add_scheduled_arrival(model)

    model.step()


def safe_mean(values):
    values = list(values)
    return mean(values) if values else math.nan


def run_condition(
    burst_width,
    total_arrivals,
    mean_parking_duration,
    seed=0,
    return_model=False,
    *,
    initial_occupancy=INITIAL_OCCUPANCY,
    steps=SIMULATION_STEPS,
    entry_control=ENTRY_CONTROL,
    entry_threshold=0.9,
):
    """Run one condition; parking completion does not require departure."""
    arrivals = build_arrival_counts(total_arrivals, burst_width)

    if not isinstance(steps, int) or steps <= max(arrivals):
        raise ValueError("steps must include every scheduled arrival")

    model = create_burst_model(
        mean_parking_duration,
        seed,
        initial_occupancy=initial_occupancy,
        entry_control=entry_control,
        entry_threshold=entry_threshold,
    )

    first_new_id = model.next_vid

    for _ in range(steps):
        step_scheduled_model(model, arrivals)

    cars = [
        car for car in model.vehicles.values()
        if car.vid >= first_new_id
    ]

    if len(cars) != total_arrivals:
        raise RuntimeError("Actual arrivals do not match scheduled demand")

    parked = [car for car in cars if car.parked_time is not None]
    waits = [car.parked_time - car.arrival_time for car in parked]

    history = model.step_results
    searching = [row["searching_inside"] for row in history]
    outside = [row["waiting_outside"] for row in history]
    backlog = [s + q for s, q in zip(searching, outside)]

    result = {
        "seed": seed,
        "burst_width": burst_width,
        "total_arrivals": total_arrivals,
        "mean_parking_duration": mean_parking_duration,
        "initial_occupancy": initial_occupancy,
        "steps": steps,
        "entry_control": entry_control,
        "entry_threshold": entry_threshold,
        "mean_total_waiting_time": safe_mean(waits),
        "max_total_waiting_time": max(waits) if waits else math.nan,
        "peak_searching_inside": max(searching),
        "peak_waiting_outside": max(outside),
        "peak_total_backlog": max(backlog),
        "cumulative_backlog": sum(backlog),
        "mean_blocked_by_parking": mean(
            row["blocked_by_parking"] for row in history
        ),
        "mean_occupancy": mean(
            row["parking_occupancy"] for row in history
        ),
        "successful_parking_count": len(parked),
        "completion_fraction": len(parked) / total_arrivals,
        "arrived_count": len(cars),
        "unfinished_parking_count": len(cars) - len(parked),
        "departed_count": sum(car.state == "DONE" for car in cars),
        "final_total_backlog": backlog[-1],
    }

    return (result, model) if return_model else result


def aggregate_results(raw_rows):
    """Summarise repetitions without merging different experimental settings."""
    groups = defaultdict(list)

    for row in raw_rows:
        key = tuple(row[field] for field in CONDITION_FIELDS)
        groups[key].append(row)

    summaries = []

    for key, group in sorted(groups.items()):
        summary = dict(zip(CONDITION_FIELDS, key))
        summary["n_seeds"] = len(group)

        for metric in METRICS:
            values = [
                float(row[metric])
                for row in group
                if math.isfinite(row[metric])
            ]

            summary[f"{metric}_mean"] = safe_mean(values)
            summary[f"{metric}_sd"] = (
                pstdev(values) if values else math.nan
            )
            summary[f"{metric}_n_valid"] = len(values)

        summaries.append(summary)

    return summaries


def write_csv(rows, path):
    if not rows:
        raise ValueError("No rows to write")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_burst_sweep(
    output_dir="data",
    seeds=DEFAULT_SEEDS,
    *,
    initial_occupancy=INITIAL_OCCUPANCY,
    steps=SIMULATION_STEPS,
):
    seeds = tuple(seeds)

    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Provide at least one seed, with no duplicates")

    raw = [
        run_condition(
            width,
            total,
            duration,
            seed=seed,
            initial_occupancy=initial_occupancy,
            steps=steps,
        )
        for width in BURST_WIDTHS
        for total in TOTAL_ARRIVALS_CASES
        for duration in MEAN_PARKING_DURATIONS
        for seed in seeds
    ]

    summary = aggregate_results(raw)

    write_csv(raw, Path(output_dir) / "burst_sweep_raw.csv")
    write_csv(summary, Path(output_dir) / "burst_sweep_summary.csv")

    return raw, summary


def print_checkpoint_examples(summary_rows):
    """Print waiting times together with parking-completion diagnostics."""
    print(
        "width  arrivals  duration  mean-wait  "
        "peak-backlog  completion  unfinished"
    )

    for row in summary_rows:
        if row["total_arrivals"] == 24 and row["burst_width"] in (10, 60):
            print(
                f"{row['burst_width']:5}"
                f"{row['total_arrivals']:10}"
                f"{row['mean_parking_duration']:10}"
                f"{row['mean_total_waiting_time_mean']:11.2f}"
                f"{row['peak_total_backlog_mean']:14.2f}"
                f"{row['completion_fraction_mean']:12.3f}"
                f"{row['unfinished_parking_count_mean']:12.2f}"
            )

    print(
        "\nValues are averages across seeds. Waiting-time means include "
        "only vehicles that successfully parked."
    )
    print(
        "Completion means successful parking, not departure. "
        "Interpret waiting times alongside completion and unfinished counts."
    )


def main():
    raw, summary = run_burst_sweep()
    print(f"Completed {len(raw)} runs across {len(summary)} conditions.")
    print_checkpoint_examples(summary)


if __name__ == "__main__":
    main()