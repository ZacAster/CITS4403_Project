"""
Checkpoint 2 experiment for the parking-search ABM.

Main idea:
The total number of arriving cars can stay the same, but the cars can arrive
in different time patterns. A small arrival window means the cars are more
synchronised (many cars arrive close together). A large arrival window means
the same cars are spread out more evenly.

This lets us study timetable-driven arrival burstiness without changing the
basic parking model in src/model.py.

The values in this file are exploratory model values. They are not claimed to
be measured UWA parking data.
"""

# We use Path so the CSV files can be saved with simple folder paths.
from pathlib import Path

# csv is used to write the raw results and the averaged results.
import csv

# math is only used for NaN when a mean cannot be calculated.
import math

# mean and pstdev make it easy to average repeated random seeds.
from statistics import mean, pstdev

# ParkingModel is the model written in src/model.py.
from src.model import ParkingModel


# -----------------------------
# Basic car-park settings
# -----------------------------

# The loop road has 30 road positions.
ROAD_LENGTH = 30

# The car park has 12 parking spaces.
N_SPACES = 12

# The car park starts at 75% occupancy for the main experiment.
INITIAL_OCCUPANCY = 0.75

# A parking manoeuvre blocks the road for two simulation steps.
PARKING_MANOEUVRE_STEPS = 2

# Entry control is not used in the main burstiness experiment.
# We keep it off so the arrival timing effect is easier to see.
ENTRY_CONTROL = False

# -----------------------------
# Arrival-burst experiment settings
# -----------------------------

# All arrival patterns are centred around the same simulation time.
# This represents cars arriving around one class-start period.
ARRIVAL_CENTER = 40

# These are the numbers of new cars used in the experiment.
# Within each comparison, the total number of cars is kept the same.
TOTAL_ARRIVALS_CASES = (12, 18, 24)

# A smaller width means the same cars are packed into a shorter time window.
# Width 10 is very bursty. Width 60 is much more spread out.
BURST_WIDTHS = (10, 20, 40, 60)

# This changes how quickly parked cars normally leave and free a space.
MEAN_PARKING_DURATIONS = (15, 30, 60)

# Every simulation runs long enough for the scheduled cars to finish parking.
SIMULATION_STEPS = 300

# We repeat every condition with 10 random seeds.
# The randomness comes mainly from the stochastic parking durations.
DEFAULT_SEEDS = tuple(range(10))


# -----------------------------
# Small helper functions
# -----------------------------

def build_arrival_times(total_arrivals, burst_width):
    """
    Create the exact arrival times for one scenario.

    Example:
    - total_arrivals = 24
    - burst_width = 10

    Then the 24 cars are squeezed into a 10-step window around ARRIVAL_CENTER.
    Some simulation steps can therefore receive more than one outside arrival.

    The total number of cars never changes when burst_width changes.
    """

    # The start time keeps every arrival pattern centred at ARRIVAL_CENTER.
    start_time = ARRIVAL_CENTER - burst_width // 2

    # This list will store one simulation time for each arriving car.
    arrival_times = []

    # If there is only one car, put it directly at the centre.
    if total_arrivals == 1:
        return [ARRIVAL_CENTER]

    # Go through every arriving car.
    for car_number in range(total_arrivals):
        # Spread the car positions across the chosen arrival window.
        # round() allows several cars to share the same step in a narrow burst.
        position_in_window = round(
            car_number * (burst_width - 1) / (total_arrivals - 1)
        )

        # Convert the position inside the window to an actual simulation time.
        arrival_time = start_time + position_in_window

        # Store this car's arrival time.
        arrival_times.append(arrival_time)

    # Return one time value for every scheduled car.
    return arrival_times


def build_arrival_counts(total_arrivals, burst_width):
    """
    Convert the arrival-time list into a dictionary.

    Example output:
    {35: 2, 36: 3, 37: 2, ...}

    This means two cars arrive at step 35, three cars at step 36, and so on.
    """

    # Start with an empty dictionary.
    counts = {}

    # Reuse the arrival schedule made by build_arrival_times().
    arrival_times = build_arrival_times(total_arrivals, burst_width)

    # Count how many cars are scheduled for every simulation step.
    for arrival_time in arrival_times:
        counts[arrival_time] = counts.get(arrival_time, 0) + 1

    # Return the finished step -> number-of-cars dictionary.
    return counts


def add_scheduled_arrival(model):
    """
    Add one externally scheduled car to the existing model.

    The normal model uses a Bernoulli arrival probability. For this experiment
    we need an exact number of cars, so we create the car ourselves.

    The new car first joins the outside FIFO queue. The original model then
    decides when the first waiting car can enter the road. This keeps the
    existing one-entrance rule instead of bypassing it.
    """

    # Create a new Vehicle object using the model's existing helper.
    car = model._new_vehicle()

    # Record the time at which this car reached the car park.
    car.arrival_time = model.time

    # The car starts outside the car park.
    car.state = "WAITING"

    # A waiting car has no road position yet.
    car.road_pos = None

    # Put the car at the end of the existing FIFO waiting queue.
    model.waiting_queue.append(car.vid)

    # Return the vehicle ID in case we want it later.
    return car.vid


def safe_mean(values):
    """Return the mean, or NaN when the list is empty."""

    # Convert the input to a list so it can be checked more than once.
    values = list(values)

    # Return the normal mean when at least one value exists.
    if values:
        return mean(values)

    # NaN is clearer than pretending an empty mean is zero.
    return math.nan


# -----------------------------
# One simulation condition
# -----------------------------

def run_condition(
    burst_width,
    total_arrivals,
    mean_parking_duration,
    seed=0,
    return_model=False,
):
    """
    Run one timetable-burst condition.

    The important comparison is that burst_width can change while
    total_arrivals stays exactly the same.
    """

    # Create one copy of the existing parking model.
    model = ParkingModel(
        road_length=ROAD_LENGTH,
        n_spaces=N_SPACES,
        initial_occupancy=INITIAL_OCCUPANCY,
        parking_manoeuvre_steps=PARKING_MANOEUVRE_STEPS,
        # Automatic random arrivals are disabled because this experiment uses
        # an exact arrival schedule instead.
        arrival_prob=0.0,
        mean_parking_duration=mean_parking_duration,
        entry_control=ENTRY_CONTROL,
        seed=seed,
    )

    # Remember how many vehicles existed before the scheduled arrivals start.
    # These are the cars that were already parked at time zero.
    initial_vehicle_count = len(model.vehicles)

    # Make the timetable-driven arrival schedule for this condition.
    arrival_counts = build_arrival_counts(total_arrivals, burst_width)

    # Run the model one simulation step at a time.
    for _ in range(SIMULATION_STEPS):
        # Check how many outside arrivals should appear at the current time.
        cars_arriving_now = arrival_counts.get(model.time, 0)

        # Add every car scheduled for this time to the outside queue.
        for _ in range(cars_arriving_now):
            add_scheduled_arrival(model)

        # Advance the original parking model by one step.
        model.step()

    # Select only the new cars created by this experiment.
    # This avoids mixing them with the cars that were parked at time zero.
    scheduled_cars = [
        car
        for car in model.vehicles.values()
        if car.vid >= initial_vehicle_count
    ]

    # A successful car has reached a parking space at least once.
    successful_cars = [
        car for car in scheduled_cars if car.parked_time is not None
    ]

    # Calculate each successful car's total wait from arrival to parking.
    waiting_times = [
        car.parked_time - car.arrival_time
        for car in successful_cars
    ]

    # Pull the recorded searching count from every simulation step.
    searching_by_step = [
        row["searching_inside"] for row in model.step_results
    ]

    # Pull the outside queue length from every simulation step.
    outside_by_step = [
        row["waiting_outside"] for row in model.step_results
    ]

    # Total backlog means cars searching inside plus cars waiting outside.
    backlog_by_step = [
        searching + outside
        for searching, outside in zip(searching_by_step, outside_by_step)
    ]

    # Record how often cars are blocked by a parking manoeuvre.
    blocked_by_step = [
        row["blocked_by_parking"] for row in model.step_results
    ]

    # Record parking occupancy over time as an extra diagnostic value.
    occupancy_by_step = [
        row["parking_occupancy"] for row in model.step_results
    ]

    # Build one result row for this simulation run.
    result = {
        # Store the input settings first so every result can be reproduced.
        "seed": seed,
        "burst_width": burst_width,
        "total_arrivals": total_arrivals,
        "mean_parking_duration": mean_parking_duration,
        # Store the main outcomes used in the analysis.
        "mean_total_waiting_time": safe_mean(waiting_times),
        "max_total_waiting_time": max(waiting_times) if waiting_times else math.nan,
        "peak_searching_inside": max(searching_by_step),
        "peak_waiting_outside": max(outside_by_step),
        "peak_total_backlog": max(backlog_by_step),
        # This is the area under the backlog curve in car-steps.
        # It captures both how high and how long the congestion lasts.
        "cumulative_backlog": sum(backlog_by_step),
        "mean_blocked_by_parking": mean(blocked_by_step),
        "mean_occupancy": mean(occupancy_by_step),
        # Check that the fixed number of scheduled cars actually parked.
        "successful_parking_count": len(successful_cars),
        "completion_fraction": len(successful_cars) / total_arrivals,
    }

    # The notebook sometimes needs the full model for a time-series plot.
    if return_model:
        return result, model

    # Normal experiment runs only need the result dictionary.
    return result


# -----------------------------
# Repeated runs and CSV output
# -----------------------------

def aggregate_results(raw_rows):
    """Average the repeated random seeds for every parameter condition."""

    # Each dictionary key represents one unique experiment condition.
    groups = {}

    # Put every raw run into its matching condition group.
    for row in raw_rows:
        key = (
            row["burst_width"],
            row["total_arrivals"],
            row["mean_parking_duration"],
        )

        # Create the group when we see the condition for the first time.
        groups.setdefault(key, []).append(row)

    # These are the measurements that will get a mean and standard deviation.
    metric_names = [
        "mean_total_waiting_time",
        "max_total_waiting_time",
        "peak_searching_inside",
        "peak_waiting_outside",
        "peak_total_backlog",
        "cumulative_backlog",
        "mean_blocked_by_parking",
        "mean_occupancy",
        "successful_parking_count",
        "completion_fraction",
    ]

    # This will hold one averaged row per condition.
    summary_rows = []

    # Sort the conditions so the CSV is easy to read.
    for key in sorted(groups):
        # Unpack the three experiment variables.
        burst_width, total_arrivals, duration = key

        # Get all repeated seeds for this condition.
        group = groups[key]

        # Start the summary row with the condition settings.
        summary = {
            "burst_width": burst_width,
            "total_arrivals": total_arrivals,
            "mean_parking_duration": duration,
            "n_seeds": len(group),
        }

        # Calculate a mean and standard deviation for every output metric.
        for metric in metric_names:
            # Keep only real numeric values and ignore NaN values.
            values = [
                float(row[metric])
                for row in group
                if not (
                    isinstance(row[metric], float)
                    and math.isnan(row[metric])
                )
            ]

            # Save the average result across seeds.
            summary[f"{metric}_mean"] = safe_mean(values)

            # Use population standard deviation because these are repeated
            # simulation runs of the same condition.
            if len(values) >= 2:
                summary[f"{metric}_sd"] = pstdev(values)
            else:
                summary[f"{metric}_sd"] = 0.0

        # Add the finished condition row to the summary table.
        summary_rows.append(summary)

    # Return all averaged conditions.
    return summary_rows


def write_csv(rows, path):
    """Write a list of result dictionaries to a CSV file."""

    # Do not create an empty CSV by mistake.
    if not rows:
        raise ValueError("No rows to write.")

    # Convert the supplied path to a Path object.
    path = Path(path)

    # Create the data folder if it does not already exist.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Open the CSV file for writing.
    with path.open("w", newline="", encoding="utf-8") as file:
        # Use the first dictionary's keys as the CSV column names.
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))

        # Write the header row.
        writer.writeheader()

        # Write every experiment row underneath the header.
        for row in rows:
            writer.writerow(row)


def run_burst_sweep(output_dir="data", seeds=DEFAULT_SEEDS):
    """
    Run the main Checkpoint 2 burstiness experiment.

    Grid:
    - 4 burst widths
    - 3 total-arrival levels
    - 3 mean parking durations
    - 10 random seeds

    This gives 36 conditions and 360 runs by default.
    """

    # Store every individual simulation run here.
    raw_rows = []

    # Try every arrival concentration.
    for burst_width in BURST_WIDTHS:
        # Try three total-demand levels.
        for total_arrivals in TOTAL_ARRIVALS_CASES:
            # Try three parking-turnover speeds.
            for duration in MEAN_PARKING_DURATIONS:
                # Repeat the same condition with several random seeds.
                for seed in seeds:
                    # Run the model once and save its result row.
                    result = run_condition(
                        burst_width=burst_width,
                        total_arrivals=total_arrivals,
                        mean_parking_duration=duration,
                        seed=seed,
                    )

                    # Add the run to the full raw-results list.
                    raw_rows.append(result)

    # Average the repeated seeds for easier plotting and interpretation.
    summary_rows = aggregate_results(raw_rows)

    # Convert the output folder to a Path object.
    output_dir = Path(output_dir)

    # Save one row per simulation run.
    write_csv(raw_rows, output_dir / "burst_sweep_raw.csv")

    # Save one averaged row per parameter condition.
    write_csv(summary_rows, output_dir / "burst_sweep_summary.csv")

    # Return both tables so a notebook can use them immediately.
    return raw_rows, summary_rows


def print_checkpoint_examples(summary_rows):
    """Print a few simple comparisons that are useful in a meeting."""

    # Compare the most bursty and most spread arrival patterns.
    wanted_widths = (10, 60)

    # Use the highest arrival count because the difference is easy to see.
    wanted_arrivals = 24

    # Show all three parking-duration cases.
    wanted_durations = (15, 30, 60)

    # Print a small heading.
    print("\nSame number of cars, different arrival concentration")
    print("-" * 72)
    print("width  arrivals  duration  mean-wait  peak-backlog  backlog-area")

    # Print one line for every selected example condition.
    for duration in wanted_durations:
        for width in wanted_widths:
            # Find the matching averaged row.
            row = next(
                row
                for row in summary_rows
                if row["burst_width"] == width
                and row["total_arrivals"] == wanted_arrivals
                and row["mean_parking_duration"] == duration
            )

            # Print the main measurements in an easy-to-read format.
            print(
                f"{width:>5}"
                f"{wanted_arrivals:>10}"
                f"{duration:>10}"
                f"{row['mean_total_waiting_time_mean']:>11.2f}"
                f"{row['peak_total_backlog_mean']:>14.2f}"
                f"{row['cumulative_backlog_mean']:>14.2f}"
            )


def main():
    """Run the full experiment when this file is executed as a module."""

    # Run the 360 simulations and get the averaged results.
    _, summary_rows = run_burst_sweep()

    # Tell the user where the output files were written.
    print(
        "Burst experiment complete: 36 conditions x 10 seeds = 360 runs.\n"
        "Saved data/burst_sweep_raw.csv and data/burst_sweep_summary.csv."
    )

    # Print a few easy-to-explain preliminary comparisons.
    print_checkpoint_examples(summary_rows)


# Only run main() when the file is executed directly with python -m.
if __name__ == "__main__":
    main()
