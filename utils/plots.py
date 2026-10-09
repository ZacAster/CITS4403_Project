import csv
from pathlib import Path
import matplotlib.pyplot as plt
from src.experiments import build_arrival_counts


def read_csv_rows(path):
    """Read a result CSV and convert numbers back from strings."""
    rows = []

    # Open the CSV
    with Path(path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Store the converted values
            converted = {}

            for key, value in row.items():
                try:
                    converted[key] = float(value)
                # If conversion fails, keep the original text
                except ValueError:
                    converted[key] = value
            rows.append(converted)
    return rows


def finish_plot(fig, output_path=None):
    """Apply simple spacing and optionally save the figure."""

    fig.tight_layout()

    # Only save the figure when a path was supplied
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160, bbox_inches="tight")
    return fig


def plot_arrival_patterns(
    total_arrivals=24,
    bursty_width=10,
    spread_width=60,
    output_path=None,
):

    # Build the concentrated arrival
    bursty_counts = build_arrival_counts(total_arrivals, bursty_width)

    # Build the more spread-out arrival
    spread_counts = build_arrival_counts(total_arrivals, spread_width)


    all_times = list(bursty_counts.keys()) + list(spread_counts.keys())
    first_time = min(all_times) - 1
    last_time = max(all_times) + 1
    times = list(range(first_time, last_time + 1))
    bursty_values = [bursty_counts.get(time, 0) for time in times]
    spread_values = [spread_counts.get(time, 0) for time in times]
    fig, ax = plt.subplots(figsize=(8, 4.5))

    # Draw the concentrated pattern
    ax.plot(
        times,
        bursty_values,
        marker="o",
        label=f"Bursty: {total_arrivals} cars in {bursty_width} steps",
    )

    # Draw the spread pattern
    ax.plot(
        times,
        spread_values,
        marker="o",
        label=f"Spread: {total_arrivals} cars in {spread_width} steps",
    )


    ax.set_xlabel("Simulation step")
    ax.set_ylabel("Cars arriving at this step")
    ax.set_title("Same total arrivals, different timetable concentration")
    ax.legend()
    return finish_plot(fig, output_path)


def plot_backlog_comparison(
    bursty_model,
    spread_model,
    output_path=None,
):

    # Read the simulation time
    times = [row["time"] for row in bursty_model.step_results]

    # Calculate total backlog
    bursty_backlog = [
        row["searching_inside"] + row["waiting_outside"]
        for row in bursty_model.step_results
    ]

    spread_backlog = [
        row["searching_inside"] + row["waiting_outside"]
        for row in spread_model.step_results
    ]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(times, bursty_backlog, label="Bursty arrivals (width 10)")
    ax.plot(times, spread_backlog, label="Spread arrivals (width 60)")
    ax.set_xlabel("Simulation step")
    ax.set_ylabel("Searching + waiting cars")
    ax.set_title("Same number of cars, different congestion over time")

    ax.legend()
    return finish_plot(fig, output_path)


def plot_burst_heatmap(
    summary_rows,
    mean_parking_duration=30,
    output_path=None,
):

    # Keep only the rows for the requested parking duration
    selected = [
        row
        for row in summary_rows
        if int(row["mean_parking_duration"]) == mean_parking_duration
    ]

    widths = sorted({int(row["burst_width"]) for row in selected})
    arrival_levels = sorted({int(row["total_arrivals"]) for row in selected})

    matrix = []

    for total_arrivals in arrival_levels:
        matrix_row = []
        for width in widths:
            row = next(
                row
                for row in selected
                if int(row["total_arrivals"]) == total_arrivals
                and int(row["burst_width"]) == width
            )
            matrix_row.append(row["mean_total_waiting_time_mean"])
        matrix.append(matrix_row)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    image = ax.imshow(matrix, aspect="auto")
    ax.set_xticks(range(len(widths)))
    ax.set_xticklabels(widths)
    ax.set_yticks(range(len(arrival_levels)))
    ax.set_yticklabels(arrival_levels)
    ax.set_xlabel("Arrival window width (smaller = more bursty)")
    ax.set_ylabel("Total arriving cars")
    ax.set_title(
        f"Mean waiting time under different arrival patterns\n"
        f"Mean parking duration = {mean_parking_duration} steps"
    )

    # Add a colour bar
    colour_bar = fig.colorbar(image, ax=ax)
    colour_bar.set_label("Mean waiting time (simulation steps)")

    # Write the numeric value
    for row_index, matrix_row in enumerate(matrix):
        for column_index, value in enumerate(matrix_row):
            ax.text(
                column_index,
                row_index,
                f"{value:.1f}",
                ha="center",
                va="center",
            )
    return finish_plot(fig, output_path)


def plot_burst_interaction(
    summary_rows,
    total_arrivals=24,
    output_path=None,
):

    selected = [
        row
        for row in summary_rows
        if int(row["total_arrivals"]) == total_arrivals
    ]

    # Find every parking-duration value
    durations = sorted(
        {int(row["mean_parking_duration"]) for row in selected}
    )

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for duration in durations:
        rows = sorted(
            [
                row
                for row in selected
                if int(row["mean_parking_duration"]) == duration
            ],
            key=lambda row: row["burst_width"],
        )
        ax.errorbar(
            [row["burst_width"] for row in rows],
            [row["mean_total_waiting_time_mean"] for row in rows],
            yerr=[
                row["mean_total_waiting_time_sd"]
                for row in rows
            ],
            marker="o",
            capsize=4,
            label=f"Parking duration = {duration}",
        )       

    ax.set_xlabel("Arrival window width (smaller = more bursty)")
    ax.set_ylabel("Mean waiting time (simulation steps)")
    ax.set_title(
        f"Effect of arrival synchronisation with {total_arrivals} total arrivals"
    )
    ax.legend()
    return finish_plot(fig, output_path)
