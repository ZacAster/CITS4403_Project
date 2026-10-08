# CITS4403 Research Project - Parking Search Congestion

## Project idea

We use an Agent-Based Model (ABM) to study parking-search congestion in a simplified campus-style car park.

Each car is one agent. Cars can arrive, wait outside, drive around the one-way loop, search for a parking space, perform a short parking manoeuvre, stay parked for a random duration, and later leave.

## Main phenomenon

Our main focus is now **timetable-driven arrival burstiness / synchronisation**.

The key idea is:

- two scenarios can have the **same total number of arriving cars**;
- in one scenario, the cars arrive close together before class;
- in the other scenario, the same cars are spread over a longer time;
- we compare the parking-search congestion created by the two timing patterns.

### Main research question

**How does the concentration of vehicle arrivals affect parking congestion when total demand is unchanged?**

### Project aim and hypothesis

The aim of this project is to determine whether concentrating the same parking demand into a shorter arrival period produces substantially greater parking-search congestion than spreading those arrivals over time.

Our hypothesis is that, for the same total number of arriving vehicles, narrower arrival windows will produce higher peak congestion, larger backlogs, and longer waiting times because more vehicles compete for limited parking capacity at the same time.

## Original contribution

The main contribution of this project is the controlled comparison of different arrival-time concentration patterns while holding total vehicle demand constant.

Rather than only increasing the number of vehicles to create congestion, the experiments investigate whether congestion can emerge because the same demand arrives in a more synchronised pattern. This allows the effect of arrival timing to be separated from the effect of total demand.

The model also records both internal searching and external waiting, allowing congestion to be evaluated as a system-wide backlog rather than only as the number of vehicles circulating inside the car park.

We also check how this effect changes when:

1. the total number of arriving cars changes;
2. the average parking duration changes.

The model also includes occupancy-based entry control, which can be used as a secondary intervention after establishing how arrival burstiness affects congestion.

## Model structure

The current model has:

- a one-way loop road;
- 12 parking spaces in the main experiment;
- cars searching for empty spaces;
- a two-step parking manoeuvre;
- temporary blocking behind a parking car;
- stochastic parking duration;
- an outside FIFO waiting queue;
- occupancy-based entry control;
- per-step and per-car measurements.

The model is deliberately simplified and is not a copy of a specific UWA car park.

## Burst experiment

The main sweep uses three experimental variables:

- **arrival window width:** 10, 20, 40, 60 simulation steps;
- **total arriving cars:** 12, 18, 24;
- **mean parking duration:** 15, 30, 60 simulation steps.

A smaller arrival window means the arrivals are more synchronised.

For example, with 24 total arrivals:

```text
width = 10  -> 24 cars arrive in a short burst
width = 60  -> the same 24 cars are spread over a much longer period
```

Every condition is repeated with 10 random seeds.
Repeated random seeds are used to reduce the influence of individual stochastic outcomes and assess whether observed differences are consistent across runs.

This gives:

```text
4 burst widths x 3 arrival totals x 3 parking durations x 10 seeds
= 360 simulation runs
```

The main measurements are:

- mean total waiting time;
- peak searching cars;
- peak outside queue;
- peak total backlog;
- cumulative backlog;
- completion fraction.

`cumulative_backlog` is the sum of `searching_inside + waiting_outside` across all simulation steps. It gives one simple measure of both the size and duration of congestion.
`completion_fraction` is the proportion of scheduled vehicles that complete their parking visit within the simulation horizon. It helps identify conditions where severe congestion prevents the system from clearing before the simulation ends.

## Preliminary Checkpoint 2 result

For 24 total arrivals, the total demand is identical between the bursty and spread cases.

With mean parking duration = 30:

```text
Arrival width 10:
mean waiting time about 46.0 steps
peak backlog about 22.0 cars

Arrival width 60:
mean waiting time about 18.8 steps
peak backlog about 8.2 cars
```
These preliminary results suggest that arrival timing has a substantial effect even when total demand is unchanged. Concentrating the 24 arrivals into a 10-step window produced both a much larger peak backlog and a considerably higher mean waiting time than spreading the same 24 arrivals across 60 steps.

This supports the hypothesis that synchronised arrivals can create short periods of demand that exceed the car park's ability to absorb vehicles, producing persistent searching and queueing. Final conclusions will be based on the complete parameter sweep and repeated runs rather than this single comparison.

These are preliminary model results, not real UWA measurements.

## Repository structure

```text
project-root/
├── src/
│   ├── model.py
│   ├── experiments.py
│   └── run_demo.py
├── tests/
├── utils/
│   └── plots.py
├── data/
├── figures/
├── notebooks/
├── docs/
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bash
.venv\Scripts\activate
```

## Run the tests

```bash
python -m pytest -q
```

## Run a single model demonstration

```bash
python -m src.run_demo
```

## Run the burst experiment

```bash
python -m src.experiments
```

This creates:

```text
data/burst_sweep_raw.csv
data/burst_sweep_summary.csv
```

## Open the Checkpoint 2 notebook

```bash
jupyter notebook
```

Then open:

```text
notebooks/checkpoint2.ipynb
```

## Current limitations

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

