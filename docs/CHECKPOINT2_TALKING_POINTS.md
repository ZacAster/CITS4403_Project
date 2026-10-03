# Checkpoint 2 talking points

## 1. Research question

**Primary:** Under what combinations of vehicle arrival rate, average parking duration, and entry-control threshold does a near-capacity car park develop persistent search congestion?

**Secondary:** Can entry control reduce or delay this congestion without mainly moving the waiting to the entrance?

## 2. What is implemented

The model is an agent-based model with a one-way loop road and finite parking spaces.

Cars can:
- arrive;
- wait outside if they cannot enter;
- search around the loop;
- start a two-step parking manoeuvre;
- temporarily block following cars while parking;
- stay parked for a stochastic duration;
- leave and free the space.

Main adjustable variables:
- `arrival_prob`
- `mean_parking_duration`
- `entry_control`
- `entry_threshold`

## 3. What the first experiment does

For Checkpoint 2 we use an exploratory grid:

- arrival probability: 0.10, 0.30, 0.50
- mean parking duration: 10, 20, 30 simulation steps
- entry control: off, or on at an occupancy threshold of 0.80
- 10 random seeds for each condition
- 400 simulation steps per run

This gives 18 conditions and 180 runs.

These are model parameters for an initial experiment. They are not claimed to be measured UWA values.

## 4. How we look for persistent congestion

We do not declare a tipping point in advance.

The main preliminary indicator is `late_mean_searching`: the mean number of cars still searching during the final 20% of a run.

We also look at:
- `search_clear_fraction`: how often the number of searching cars is zero;
- outside waiting;
- total waiting time among cars that successfully park;
- unfinished cars at the end of the run.

## 5. Preliminary pattern

The initial sweep produces both low-search and high-search conditions.

In the low-arrival / short-duration conditions, searching normally clears repeatedly.

As arrival probability and parking duration increase, late searching becomes much larger and the system clears less often.

In a demanding condition, entry control can reduce searching inside while increasing the outside queue. This is the trade-off behind the secondary research question.

Treat these as preliminary observations only. The final report should use a wider/sensitivity-focused experiment design before making strong claims.

## 6. Important limitations to mention if asked

- One simulation step is not calibrated to a real number of seconds/minutes.
- The car park is a simplified loop, not a copy of a particular UWA car park.
- Parking durations currently use an exponential distribution as a modelling assumption.
- At most one new arrival is generated per step.
- Departing parked cars leave the model immediately instead of merging back into the road.
- Outside waiting can occur because the entrance road cell is physically occupied as well as because entry control is active.
- Mean waiting time only includes cars that successfully parked before the simulation ended, so unfinished counts are shown separately.
- The current experiment shows a transition in behaviour across the tested parameter range, but we should not call it a sharp tipping point unless later analysis supports that wording.

## 7. Who did what

Maneesh:
- experiment parameters;
- stochastic parking duration;
- outside waiting queue;
- entry control;
- measurements;
- tests for those features.

Zac:
- initial parameter-sweep runner;
- additional late-congestion analysis metrics;
- result aggregation across random seeds;
- plots;
- Checkpoint 2 notebook and preliminary analysis.

Both:
- review each other's pull requests;
- explain the model and assumptions in the checkpoint.
