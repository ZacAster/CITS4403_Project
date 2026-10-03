"""
Plotting helpers for the timetable-driven arrival-burst experiment.

The plots are deliberately simple because they are mainly used in the
Checkpoint 2 notebook and demo.
"""

# csv reads the summary file made by src/experiments.py.
import csv

# Path makes file paths easier to handle on Mac, Windows, and Linux.
from pathlib import Path

# matplotlib is used for all project figures.
import matplotlib.pyplot as plt

# Reuse the arrival-schedule function so the plot shows the exact schedule
# that the simulation actually uses.
from src.experiments import build_arrival_counts


# -----------------------------
# Reading result CSV files
# -----------------------------

def read_csv_rows(path):
    """Read a result CSV and convert numbers back from strings."""

    # This list will hold one dictionary per CSV row.
    rows = []

    # Open the CSV file in read mode.
    with Path(path).open(newline="", encoding="utf-8") as file:
        # DictReader uses the first CSV line as the column names.
        reader = csv.DictReader(file)

        # Read every row one by one.
        for row in reader:
            # Store the converted values in a new dictionary.
            converted = {}

            # Go through every column in the row.
            for key, value in row.items():
                # Try to convert normal numeric values to floats.
                try:
                    converted[key] = float(value)
                # If conversion fails, keep the original text.
                except ValueError:
                    converted[key] = value

            # Add the finished row to the result list.
            rows.append(converted)

    # Return all rows.
    return rows


def finish_plot(fig, output_path=None):
    """Apply simple spacing and optionally save the figure."""

    # Reduce unnecessary overlap around labels and titles.
    fig.tight_layout()

    # Only save the figure when a path was supplied.
    if output_path is not None:
        # Convert the supplied value to a Path object.
        path = Path(output_path)

        # Create the parent folder if it does not exist yet.
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save a clear PNG that is suitable for the notebook/report.
        fig.savefig(path, dpi=160, bbox_inches="tight")

    # Return the figure so Jupyter can display it.
    return fig


# -----------------------------
# Figure 1: arrival schedules
# -----------------------------

def plot_arrival_patterns(
    total_arrivals=24,
    bursty_width=10,
    spread_width=60,
    output_path=None,
):
    """
    Show that both scenarios contain the same number of cars.

    The only difference is how tightly the arrivals are grouped in time.
    """

    # Build the concentrated arrival schedule.
    bursty_counts = build_arrival_counts(total_arrivals, bursty_width)

    # Build the more spread-out arrival schedule.
    spread_counts = build_arrival_counts(total_arrivals, spread_width)

    # Find the full time range covered by either schedule.
    all_times = list(bursty_counts.keys()) + list(spread_counts.keys())

    # Start one step before the first arrival so the graph begins at zero.
    first_time = min(all_times) - 1

    # End one step after the final arrival for the same reason.
    last_time = max(all_times) + 1

    # Make one value for every simulation step on the x-axis.
    times = list(range(first_time, last_time + 1))

    # Convert the dictionaries to y-values for the concentrated schedule.
    bursty_values = [bursty_counts.get(time, 0) for time in times]

    # Convert the dictionaries to y-values for the spread schedule.
    spread_values = [spread_counts.get(time, 0) for time in times]

    # Create one normal matplotlib figure and axis.
    fig, ax = plt.subplots(figsize=(8, 4.5))

    # Draw the concentrated pattern.
    ax.plot(
        times,
        bursty_values,
        marker="o",
        label=f"Bursty: {total_arrivals} cars in {bursty_width} steps",
    )

    # Draw the spread pattern.
    ax.plot(
        times,
        spread_values,
        marker="o",
        label=f"Spread: {total_arrivals} cars in {spread_width} steps",
    )

    # Label the horizontal axis.
    ax.set_xlabel("Simulation step")

    # Label the vertical axis.
    ax.set_ylabel("Cars arriving at this step")

    # Explain the comparison in the title.
    ax.set_title("Same total arrivals, different timetable concentration")

    # Show which line is which.
    ax.legend()

    # Finish and optionally save the plot.
    return finish_plot(fig, output_path)


# -----------------------------
# Figure 2: backlog over time
# -----------------------------

def plot_backlog_comparison(
    bursty_model,
    spread_model,
    output_path=None,
):
    """
    Compare the congestion created by two models with the same total arrivals.

    Backlog = cars searching inside + cars waiting outside.
    """

    # Read the simulation time from the bursty model.
    times = [row["time"] for row in bursty_model.step_results]

    # Calculate total backlog for the bursty arrival pattern.
    bursty_backlog = [
        row["searching_inside"] + row["waiting_outside"]
        for row in bursty_model.step_results
    ]

    # Calculate total backlog for the spread arrival pattern.
    spread_backlog = [
        row["searching_inside"] + row["waiting_outside"]
        for row in spread_model.step_results
    ]

    # Create one figure for the time-series comparison.
    fig, ax = plt.subplots(figsize=(8, 4.5))

    # Plot the concentrated-arrival result.
    ax.plot(times, bursty_backlog, label="Bursty arrivals (width 10)")

    # Plot the spread-arrival result.
    ax.plot(times, spread_backlog, label="Spread arrivals (width 60)")

    # Label the simulation time axis.
    ax.set_xlabel("Simulation step")

    # Explain what the y-value counts.
    ax.set_ylabel("Searching + waiting cars")

    # State the main point of the comparison.
    ax.set_title("Same number of cars, different congestion over time")

    # Display a legend for the two scenarios.
    ax.legend()

    # Finish and optionally save the figure.
    return finish_plot(fig, output_path)


# -----------------------------
# Figure 3: heatmap
# -----------------------------

def plot_burst_heatmap(
    summary_rows,
    mean_parking_duration=30,
    output_path=None,
):
    """
    Heatmap of mean waiting time for different burst widths and demand levels.

    Each cell is already averaged across repeated random seeds.
    """

    # Keep only the rows for the requested parking duration.
    selected = [
        row
        for row in summary_rows
        if int(row["mean_parking_duration"]) == mean_parking_duration
    ]

    # Get the burst-width values in increasing order.
    widths = sorted({int(row["burst_width"]) for row in selected})

    # Get the total-arrival values in increasing order.
    arrival_levels = sorted({int(row["total_arrivals"]) for row in selected})

    # This list of lists becomes the heatmap matrix.
    matrix = []

    # Build one heatmap row for every total-arrival level.
    for total_arrivals in arrival_levels:
        # Store all burst-width results for this demand level.
        matrix_row = []

        # Read the mean waiting time for every burst width.
        for width in widths:
            # Find the one summary row matching this cell.
            row = next(
                row
                for row in selected
                if int(row["total_arrivals"]) == total_arrivals
                and int(row["burst_width"]) == width
            )

            # Add the averaged waiting time to the heatmap row.
            matrix_row.append(row["mean_total_waiting_time_mean"])

        # Add the completed row to the matrix.
        matrix.append(matrix_row)

    # Create the heatmap figure.
    fig, ax = plt.subplots(figsize=(7.5, 4.8))

    # imshow converts the numeric matrix into a colour intensity map.
    image = ax.imshow(matrix, aspect="auto")

    # Put one x-axis tick under every burst-width column.
    ax.set_xticks(range(len(widths)))

    # Label those ticks with the actual width values.
    ax.set_xticklabels(widths)

    # Put one y-axis tick beside every total-arrival row.
    ax.set_yticks(range(len(arrival_levels)))

    # Label those ticks with the actual number of arriving cars.
    ax.set_yticklabels(arrival_levels)

    # Explain that small widths mean stronger synchronisation.
    ax.set_xlabel("Arrival window width (smaller = more bursty)")

    # Label the fixed total number of arrivals in each scenario.
    ax.set_ylabel("Total arriving cars")

    # Put the fixed parking-duration condition in the title.
    ax.set_title(
        f"Mean waiting time under different arrival patterns\n"
        f"Mean parking duration = {mean_parking_duration} steps"
    )

    # Add a colour bar so the heatmap values have a visible scale.
    colour_bar = fig.colorbar(image, ax=ax)

    # Label the colour-bar units.
    colour_bar.set_label("Mean waiting time (simulation steps)")

    # Write the numeric value inside every heatmap cell.
    for row_index, matrix_row in enumerate(matrix):
        # Go through every column in this row.
        for column_index, value in enumerate(matrix_row):
            # Show one decimal place so the plot is easy to read.
            ax.text(
                column_index,
                row_index,
                f"{value:.1f}",
                ha="center",
                va="center",
            )

    # Finish and optionally save the figure.
    return finish_plot(fig, output_path)


# -----------------------------
# Figure 4: interaction plot
# -----------------------------

def plot_burst_interaction(
    summary_rows,
    total_arrivals=24,
    output_path=None,
):
    """
    Show how parking duration changes the effect of arrival burstiness.

    The total number of arriving cars is fixed for every line on this plot.
    """

    # Keep only one fixed total-arrival level.
    selected = [
        row
        for row in summary_rows
        if int(row["total_arrivals"]) == total_arrivals
    ]

    # Find every parking-duration value used in the sweep.
    durations = sorted(
        {int(row["mean_parking_duration"]) for row in selected}
    )

    # Create one figure for the line comparison.
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    # Draw one line for each parking-duration condition.
    for duration in durations:
        # Select this duration and sort points by burst width.
        rows = sorted(
            [
                row
                for row in selected
                if int(row["mean_parking_duration"]) == duration
            ],
            key=lambda row: row["burst_width"],
        )

        # Plot mean waiting time against the arrival-window width.
        ax.plot(
            [row["burst_width"] for row in rows],
            [row["mean_total_waiting_time_mean"] for row in rows],
            marker="o",
            label=f"Parking duration = {duration}",
        )

    # Label the arrival-concentration axis.
    ax.set_xlabel("Arrival window width (smaller = more bursty)")

    # Label the waiting-time axis.
    ax.set_ylabel("Mean waiting time (simulation steps)")

    # State that the total number of cars is fixed.
    ax.set_title(
        f"Effect of arrival synchronisation with {total_arrivals} total arrivals"
    )

    # Show which line belongs to which parking duration.
    ax.legend()

    # Finish and optionally save the figure.
    return finish_plot(fig, output_path)
