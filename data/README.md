# CITS4403 Research Project

## Project idea

We are studying parking-search congestion in a busy campus-style car park.

The model is intentionally simple. The parts that matter for our research question: cars arriving, driving around looking for a space, temporarily blocking cars behind while parking, staying parked for some time, and eventually leaving.

## Research questions

### Main question

**Under what combinations of vehicle arrival rate, average parking duration, and entry-control threshold does a near-capacity car park develop persistent search congestion?**

In simpler words, we want to change three things later:

1. how quickly new cars arrive;
2. how long parked cars stay before a space becomes free again;
3. how full the car park can become before entry control starts holding new cars outside.

We then look at whether searching cars clear after a short time, or whether many searching cars remain inside for a long period.

### Secondary question

**Can entry control reduce or delay this congestion without simply moving most of the waiting to the entrance?**

A strict entry rule will obviously reduce the number of cars allowed inside. That alone is not enough to answer our question. Later we also need to measure outside waiting and total waiting time.

## What the car park looks like

We use an Agent-Based Model (ABM).

Each car is one agent. The environment is a simple one-way loop with parking spaces attached to some road positions.

```text
                    parking spaces
                 P     P     P     P
                 |     |     |     |
Entrance ---> [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ] ...
                 ^                       |
                 |_______________________|
                       one-way loop
```

## How cars move

A searching car normally moves one road position per simulation step.

Cars can drive directly behind one another. They do **not** need an empty road position between them.

```text
Before:   [A][B][C][ ]
After:    [ ][A][B][C]
```

The main temporary blockage in the current model happens when a car starts parking.

## How parking works

If a searching car reaches a road position next to an empty parking space, it starts a parking manoeuvre.

For the first version, parking takes **two simulation steps**.

During those two steps the car stays on its road position, so cars directly behind it have to wait.

After two steps, the parking car leaves the road and occupies the parking space. The road position becomes free and the cars behind can move again.

The two-step parking rule is a modelling assumption. It does not mean two real seconds or two real minutes. Later we can test whether changing it to 1 or 3 steps changes the result.

## What happens after a car parks

The current baseline model keeps each parked car for a fixed placeholder number of simulation steps.

When that time finishes, the car leaves the model and the parking space becomes free again.

This fixed duration is temporary. One of the next tasks is to replace it with a configurable and stochastic parking-duration setting for the experiments.

## What is already implemented

This repository currently contains the **baseline model only**.

Implemented:

- one-way loop road;
- parking spaces beside the road;
- initial occupied parking spaces;
- cars can be added at the entrance;
- adjacent searching cars can move together;
- cars can find an empty parking space;
- parking takes two simulation steps;
- a parking car temporarily blocks cars directly behind;
- parked cars leave after a fixed placeholder duration;
- three basic tests for the movement and parking rules.

## What is intentionally NOT implemented yet

These parts are left for the next development tasks:

- random/configurable vehicle arrival rate;
- configurable average parking duration;
- outside waiting queue;
- occupancy-based entry control;
- entry-control threshold;
- experiment measurements such as search time and total waiting time;
- CSV result output;
- full parameter sweep;
- final Checkpoint 2 plots.


## Planned experimental variables

These are part of the research design, but they are **not all implemented in the current code yet**.

### 1. Vehicle arrival rate

How quickly new cars arrive.

### 2. Average parking duration

How long parked cars stay before they leave and free a space.

### 3. Entry-control threshold

How full the car park can become before new cars are temporarily held outside.

## Behaviour we want to investigate

We are looking for a possible change from temporary searching to persistent search congestion.

Example of searching that clears:

```text
0 -> 2 -> 5 -> 3 -> 1 -> 0
```

Example of searching that stays high:

```text
2 -> 5 -> 8 -> 11 -> 13 -> 12 -> 15 ...
```


## Current Checkpoint 2 goal

Before Checkpoint 2, we want to add the missing experiment features, record useful measurements, run a small set of trial conditions, and produce at least one clear plot.

## Repository structure

```text
project-root/
├── src/
├── tests/
├── notebooks/
├── utils/
├── data/
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

## Run the baseline demo

```bash
python -m src.run_demo
```

## Run the current tests

```bash
python -m pytest -q
```

## Notebook

```bash
jupyter notebook
```

Then open:

```text
notebooks/checkpoint2.ipynb
```
