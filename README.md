# CITS4403 Research Project - Parking Search Congestion

## Project idea

We use an Agent-Based Model (ABM) to study parking-search congestion in a simplified campus-style car park.

Each car is one agent. Cars can arrive, wait outside, drive around the one-way loop, search for a parking space, perform a short parking manoeuvre, stay parked for a random duration, and later leave.

## Main phenomenon for Checkpoint 2

Our main focus is now **timetable-driven arrival burstiness / synchronisation**.

The key idea is simple:

- two scenarios can have the **same total number of arriving cars**;
- in one scenario, the cars arrive close together before class;
- in the other scenario, the same cars are spread over a longer time;
- we compare the parking-search congestion created by the two timing patterns.

### Main research question

**Can timetable-driven clustering of vehicle arrivals create much more parking-search congestion even when the total number of arriving cars is unchanged?**

We also check how this effect changes when:

1. the total number of arriving cars changes;
2. the average parking duration changes.

Entry control is already implemented in the model, but it is not the main Checkpoint 2 experiment. It can be studied later as a possible intervention.

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

## Checkpoint 2 burst experiment

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
