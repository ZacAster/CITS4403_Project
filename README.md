# Parking Search Congestion under Synchronised Arrivals

## Project overview

This project uses an agent-based model to investigate parking-search
congestion in a simplified campus-style car park.

Vehicles arrive, wait outside when necessary, search along a one-way loop,
perform a parking manoeuvre, occupy a space, and eventually leave.

The main phenomenon is the build-up and clearance of congestion when the
same total parking demand arrives over different time windows.

## Research question

Under fixed total vehicle demand, how does arrival synchronisation affect
waiting times and backlog in a parking system, and how does this effect
vary with parking turnover?

Within each comparison, total arrivals and other model settings are held
constant while the arrival-window width changes.

## Aim and hypothesis

We investigate the size and conditions of the arrival-timing effect.

Our hypothesis is that narrower arrival windows produce higher peak
backlogs and longer waiting times, and that slower parking turnover can
increase this effect.

This is a hypothesis to test rather than an assumption built into the
reported conclusions.

## Project contribution

The investigation combines finite parking capacity, temporary blocking
during parking manoeuvres, and an outside waiting queue.

It compares arrival concentration at fixed total demand and examines its
interaction with parking duration. Measuring both internal searching and
external waiting helps distinguish overall congestion from a redistribution
of vehicles between the road and the outside queue.

The project is inspired by campus arrival patterns, but it does not use
measured university timetable or parking data.

## Model rules

The main experiment uses:

- 30 road positions arranged in a one-way loop;
- 12 parking spaces;
- 75% initial parking occupancy;
- a two-step parking manoeuvre;
- an outside FIFO waiting queue;
- at most one vehicle admitted through the entrance per step;
- stochastic parking durations;
- no occupancy-based entry control in the main sweep.

Searching vehicles move simultaneously when the movement rule allows.
A vehicle performing a parking manoeuvre can block vehicles behind it.
Parked vehicles leave directly when their parking timer expires.

Parking durations are sampled from an exponential distribution, rounded
to integer steps, and bounded below by one step. Therefore,
`mean_parking_duration` is the exponential scale parameter; rounding means
the realised discrete mean need not equal it exactly.

For scheduled experiments, arrivals join the queue before each model step.
The model then updates parked vehicles, progresses parking manoeuvres,
starts new manoeuvres, moves searching vehicles, admits a waiting vehicle,
and records the resulting state.

## Experimental design

The main parameter sweep uses:

| Parameter | Values |
| --- | --- |
| Arrival-window width | 10, 20, 40, 60 steps |
| Total arriving vehicles | 12, 18, 24 |
| Parking-duration parameter | 15, 30, 60 steps |
| Random seeds | 0–9 |
| Simulation horizon | 300 steps |

This gives 36 conditions and 360 simulation runs.

Arrival schedules are approximately centred around step 40. Narrower
windows concentrate the same number of arrivals into fewer steps.

Comparisons of arrival-window width hold total demand, parking duration,
initial occupancy, layout and entry-control settings constant.

Repeated seeds characterise variability. Using the same seed across
different scenarios does not guarantee identical parking durations for
each corresponding vehicle.

## Outcome measures

- `mean_total_waiting_time`: mean arrival-to-parking time among vehicles
  that successfully park. It includes outside waiting, searching and the
  parking manoeuvre.
- `peak_total_backlog`: maximum searching-inside plus waiting-outside count.
- `cumulative_backlog`: sum of that backlog across recorded steps, measured
  in vehicle-steps.
- `completion_fraction`: fraction of scheduled vehicles that successfully
  park before the simulation ends. It does not require them to depart.
- `unfinished_parking_count`: arrivals that have not successfully parked
  by the end of the run.
- `departed_count`: scheduled vehicles that have already departed.
- `final_total_backlog`: searching plus waiting vehicles at the final step.

Backlog excludes vehicles currently performing a parking manoeuvre.
Consequently, it is not identical to the number of all vehicles that have
not yet completed parking.

Waiting-time averages must be interpreted alongside completion and
unfinished counts because they exclude vehicles that have not parked.

## Baseline result

For 24 arrivals and a parking-duration parameter of 30, the existing
10-seed baseline gives:

| Arrival width | Mean waiting time, mean ± SD | Peak backlog, mean ± SD |
| --- | --- | --- |
| 10 | 46.04 ± 7.17 steps | 22.00 ± 0.63 vehicles |
| 60 | 18.83 ± 3.75 steps | 8.20 ± 1.25 vehicles |

The standard deviations describe variation across the ten runs; they are
not confidence intervals.

All scheduled vehicles successfully parked within 300 steps in the
baseline 360-run sweep. This does not guarantee completion for other
parameters or seeds.

These results describe the model and are not calibrated predictions for
a real car park.

## Setup

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Tests

```bash
python -m pytest -q
```

## Text demonstration

```bash
python -m src.run_demo
```

## Live comparison

```bash
python -m src.animate_model
```

The animation compares width 10 with width 60 using 24 arrivals in each
scenario. Both simulations advance on the same clock.

Press Space to pause or resume. Close the window and rerun the command
to restart.

Example settings:

```bash
python -m src.animate_model --arrivals 24 --duration 60 --seed 3
```

Run this on a machine with a graphical Matplotlib backend.
Frame interval controls playback speed, not simulated vehicle speed.

## Main experiment

```bash
python -m src.experiments
```

This regenerates:

- `data/burst_sweep_raw.csv`
- `data/burst_sweep_summary.csv`

The summary includes per-metric means, descriptive standard deviations
and valid-run counts.

## Optional entry-control experiment

```bash
python -m utils.run_threshold_sensitivity
```

This compares entry-control settings for a fixed burst scenario and writes
separate `burst_threshold_raw.csv` and `burst_threshold_summary.csv` files.

It is a secondary analysis, not part of the main 360-run sweep.

## Notebook

```bash
jupyter notebook
```

Open `notebooks/checkpoint2.ipynb` to inspect arrival schedules, example
trajectories, heatmaps and parking-duration comparisons.

After regenerating experiment data or changing plotting functions,
restart the notebook kernel and run all cells.

## Limitations

The road geometry, movement rules and parking behaviour are simplified.
Simulation steps are not calibrated to real minutes.

The entrance admits at most one vehicle per step. A concentrated arrival
schedule can therefore create an outside queue even before parking-space
availability becomes the limiting factor.

Initial occupants can depart before or during the arrival window. The
results describe a transient arrival event rather than a stationary system.

Backlog excludes parking manoeuvres, whereas arrival-to-parking waiting
time includes them.

Departing vehicles disappear from their spaces without rejoining the road.
There are no alternative parking destinations or driver route choices.

- Simulation steps are not calibrated to real minutes.
- The car park layout is simplified.
- Parking duration uses an exponential distribution as a modelling assumption.
- The burst schedules are exploratory and are not measured UWA timetable traffic data.
- Departing parked cars leave the model immediately instead of merging back into the road.
- The main experiment uses scheduled arrivals so that every compared condition can have exactly the same number of arriving cars.



## Reproducing the experiment results

This project investigates whether concentrating the same number
of arriving cars into shorter time windows increases parking-search
congestion.

### 1. Set up the environment

Create a Python virtual environment and install the dependencies
using the Setup instructions above.

### 2. Verify the implementation

Run the complete automated test suite:

```bash
python -m pytest -v
```

The tests check parking movement, queue admission, parking
capacity, vehicle conservation, and experiment behaviour.

### 3. Run the baseline demonstration

```bash
python -m src.run_demo
```

This demonstrates the basic parking-search model.

### 4. Run the burst-arrival experiments

```bash
python -m src.experiments
```

These experiments compare different arrival concentration
scenarios while keeping total scheduled demand fixed.

### 5. Examine experiment results

Inspect the generated CSV files in the `data/` folder.

Relevant measures include:

- Mean total waiting time
- Parking completion fraction
- Unfinished parking count
- Vehicle backlog
- Parking occupancy

When comparing mean waiting times, consider the completion
fraction and unfinished parking count as well. Waiting-time
averages based only on successfully parked cars may understate
congestion when many cars remain unfinished.

### 6. Reproducibility considerations

For meaningful comparisons:

- Keep total scheduled arrivals equal between scenarios.
- Use the same model parameters across comparisons.
- Use controlled random seeds.
- Record arrival-window widths and simulation duration.
- Include repeated runs to capture variability.
- Report both completed and unfinished parking attempts.

### 7. Current limitations

The car park layout is simplified, and simulation steps are
not calibrated to real-world minutes. Parking duration is
modelled using an exponential distribution. The results
should therefore be interpreted as comparisons within
the simulated system rather than direct predictions for
a real campus car park.

