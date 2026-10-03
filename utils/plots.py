"""
Plotting helpers for the Checkpoint 2 parking-search experiments.

The functions return the matplotlib Figure object and optionally save it.
They do not call plt.show(), so they work both in notebooks and scripts.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


def read_csv_rows(path):
    """Read a CSV file and convert obvious numeric/boolean values."""
    rows = []

    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            converted = {}

            for key, value in row.items():
                if value == "":
                    converted[key] = float("nan")
                elif value in ("True", "False"):
                    converted[key] = value == "True"
                else:
                    try:
                        converted[key] = float(value)
                    except ValueError:
                        converted[key] = value

            rows.append(converted)

    return rows


def _finish(fig, output_path):
    fig.tight_layout()

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160, bbox_inches="tight")

    return fig


def plot_search_and_waiting_timeseries(model, title=None, output_path=None):
    """
    Plot searching cars inside and cars waiting outside over simulation time.
    """
    times = [r["time"] for r in model.step_results]
    searching = [r["searching_inside"] for r in model.step_results]
    outside = [r["waiting_outside"] for r in model.step_results]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(times, searching, label="Searching inside")
    ax.plot(times, outside, label="Waiting outside")
    ax.set_xlabel("Simulation step")
    ax.set_ylabel("Number of cars")
    ax.set_title(title or "Parking-search model")
    ax.legend()

    return _finish(fig, output_path)


def plot_late_searching_by_arrival(
    summary_rows,
    entry_control,
    output_path=None,
):
    """
    Plot late-run searching against arrival probability.

    One line is shown for each average parking duration.
    """
    selected = [
        r for r in summary_rows if bool(r["entry_control"]) == entry_control
    ]

    durations = sorted(
        {int(r["mean_parking_duration"]) for r in selected}
    )

    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    for duration in durations:
        rows = sorted(
            [
                r
                for r in selected
                if int(r["mean_parking_duration"]) == duration
            ],
            key=lambda r: r["arrival_prob"],
        )

        ax.plot(
            [r["arrival_prob"] for r in rows],
            [r["late_mean_searching_mean"] for r in rows],
            marker="o",
            label=f"Mean parking duration = {duration}",
        )

    ax.set_xlabel("Arrival probability per simulation step")
    ax.set_ylabel("Mean searching cars in final 20%")
    ax.set_title(
        "Late search congestion "
        + ("with entry control" if entry_control else "without entry control")
    )
    ax.legend()

    return _finish(fig, output_path)


def plot_entry_control_tradeoff(
    summary_rows,
    arrival_prob=0.50,
    mean_parking_duration=30,
    output_path=None,
):
    """
    Show the inside/outside trade-off for one demanding condition.

    The x-axis is late outside waiting and the y-axis is late searching inside.
    """
    rows = [
        r
        for r in summary_rows
        if r["arrival_prob"] == arrival_prob
        and int(r["mean_parking_duration"]) == mean_parking_duration
    ]

    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    for row in rows:
        label = "Control on" if row["entry_control"] else "Control off"
        x = row["late_mean_waiting_outside_mean"]
        y = row["late_mean_searching_mean"]

        ax.scatter([x], [y], s=70)
        ax.annotate(label, (x, y), xytext=(6, 6), textcoords="offset points")

    ax.set_xlabel("Mean cars waiting outside in final 20%")
    ax.set_ylabel("Mean cars searching inside in final 20%")
    ax.set_title(
        f"Entry-control trade-off: arrival={arrival_prob}, "
        f"parking duration={mean_parking_duration}"
    )

    return _finish(fig, output_path)
