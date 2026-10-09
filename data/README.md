# Experiment data

`burst_sweep_raw.csv` contains one row per main-experiment run.
`burst_sweep_summary.csv` contains results aggregated by experimental
condition.

Generate both files from the repository root:

    python -m src.experiments

The default sweep contains 36 conditions and 360 runs.

Waiting times are measured in simulation steps. Backlog counts searching
vehicles and vehicles waiting outside. Cumulative backlog is measured in
vehicle-steps.

`completion_fraction` measures successful parking, not departure.
Waiting-time averages exclude vehicles that have not successfully parked;
use completion and unfinished counts when interpreting them.

Optional entry-control results are generated with:

    python -m utils.run_threshold_sensitivity

These are saved as `burst_threshold_raw.csv` and
`burst_threshold_summary.csv`.
