import csv
from pathlib import Path
import sys

# Make sure the project root is available for imports
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.experiments import run_condition


# Fixed demanding scenario from the Checkpoint 2 notebook
ARRIVAL_PROB = 0.50
MEAN_PARKING_DURATION = 30
STEPS = 400

# Compare no control against several entry-control thresholds
THRESHOLDS = [0.80, 0.85, 0.90, 0.95]

# Use the same number of seeds as the original experiment
SEEDS = range(10)

output_path = repo_root / "data" / "threshold_sensitivity_results.csv"

results = []


# Baseline: no entry control
for seed in SEEDS:
    result = run_condition(
        arrival_prob=ARRIVAL_PROB,
        mean_parking_duration=MEAN_PARKING_DURATION,
        entry_control=False,
        seed=seed,
        steps=STEPS,
    )

    result["scenario"] = "no_control"
    results.append(result)


# Entry-control threshold experiments
for threshold in THRESHOLDS:
    for seed in SEEDS:
        result = run_condition(
            arrival_prob=ARRIVAL_PROB,
            mean_parking_duration=MEAN_PARKING_DURATION,
            entry_control=True,
            entry_threshold=threshold,
            seed=seed,
            steps=STEPS,
        )

        result["scenario"] = f"threshold_{threshold:.2f}"
        results.append(result)


# Save all individual runs to CSV
output_path.parent.mkdir(parents=True, exist_ok=True)

fieldnames = ["scenario"] + [
    key for key in results[0].keys()
    if key != "scenario"
]

with output_path.open("w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for result in results:
        writer.writerow(result)


print(f"Completed {len(results)} simulation runs.")
print(f"Results saved to: {output_path}")


# Print a simple summary for each scenario
print("\nThreshold sensitivity summary")
print("-" * 70)

scenario_names = ["no_control"] + [
    f"threshold_{threshold:.2f}"
    for threshold in THRESHOLDS
]

for scenario in scenario_names:
    scenario_results = [
        row for row in results
        if row["scenario"] == scenario
    ]

    mean_search_time = sum(
        row["mean_search_time"] for row in scenario_results
    ) / len(scenario_results)

    mean_searching = sum(
        row["mean_searching_cars"] for row in scenario_results
    ) / len(scenario_results)

    late_mean_searching = sum(
        row["late_mean_searching"] for row in scenario_results
    ) / len(scenario_results)

    outside_waiting = sum(
        row["mean_outside_waiting_time"] for row in scenario_results
    ) / len(scenario_results)

    total_waiting = sum(
        row["mean_total_waiting_time"] for row in scenario_results
    ) / len(scenario_results)

    completion_fraction = sum(
        row["completion_fraction"] for row in scenario_results
    ) / len(scenario_results)

    print(f"\nScenario: {scenario}")
    print(f"  Mean search time:           {mean_search_time:.2f}")
    print(f"  Mean searching cars:        {mean_searching:.2f}")
    print(f"  Late mean searching:        {late_mean_searching:.2f}")
    print(f"  Mean outside waiting time:  {outside_waiting:.2f}")
    print(f"  Mean total waiting time:    {total_waiting:.2f}")
    print(f"  Completion fraction:        {completion_fraction:.3f}")
