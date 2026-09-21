# CITS4403 Research Project

## Project idea

We are interested in parking congestion in busy campus car parks.

During busy periods, a car park can stay close to full capacity for a long time. Cars keep arriving while only some parked cars leave and free up spaces.

At some point, the car park may go from being busy but still manageable to having many cars continuously driving around looking for parking.

We want to use a computational model to explore when this happens and whether entry control can change it.

## System

Vehicle movement and parking in a near-capacity campus car park.

## Research question

**Under what conditions does a near-capacity campus car park develop persistent search congestion, and how does entry control affect this?**

By "persistent search congestion", we mean a situation where the number of cars searching for parking stays high or continues to build up instead of returning to a normal level.

We are interested in whether there is a point where a relatively small change in traffic conditions causes a much larger increase in congestion.

For example, a car park might handle 8 arriving cars in a certain time period without much trouble, but increasing this to 10 cars might cause searching vehicles to start building up continuously.

We also want to see whether entry control can delay or reduce this problem, and whether very strict entry control simply moves the waiting from inside the car park to the entrance.

## Main variables

We currently plan to change three main variables in the experiments.

### 1. Vehicle arrival rate

This is how quickly new vehicles arrive at the car park.

For example, we could compare low, medium and high arrival rates.

A low arrival rate may be easy for the car park to handle, while a high arrival rate may cause cars to arrive faster than parking spaces become available.

### 2. Parking turnover rate

This describes how quickly occupied parking spaces become available again.

A high turnover rate means parked cars leave more often, so spaces become available quickly.

A low turnover rate means cars stay parked for longer, so fewer spaces become available.

We want to see how the balance between arriving vehicles and newly available spaces affects congestion.

### 3. Entry-control threshold

This is the point where new vehicles are temporarily stopped from entering the car park.

For example, a stricter rule may start controlling entry when the car park reaches a lower occupancy level, while a looser rule may only start when the car park is almost completely full.

We will also have a baseline with no entry control.

We want to see whether different control levels work differently depending on the arrival rate and parking turnover rate.

## Current modelling idea

We are planning to use an Agent-Based Model (ABM).

Each vehicle will be represented as an agent moving through a simplified car park.

Vehicles will:

- arrive at the car park
- enter if they are allowed to
- search for an available parking space
- park when they find one
- leave after some time and free the parking space

The first version of the model will be kept simple and will not try to copy one specific UWA car park exactly.

## What we want to observe

We are not only trying to show that entry control reduces the number of cars inside the car park, because that result would be quite obvious.

The more interesting part is to see how the three variables interact.

For example:

- When arrival rate is low, entry control may make very little difference.
- When cars arrive faster than parking spaces become available, congestion may suddenly become much worse.
- Faster parking turnover may allow the car park to handle a higher arrival rate before this happens.
- Entry control may move this congestion point, but very strict control may create long queues outside instead.

We want to find out whether there is a clear congestion threshold or transition in the model, and what conditions cause it.

## Measurements

Some of the main results we currently plan to measure are:

- average parking search time
- average number of vehicles searching inside the car park
- total waiting time, including waiting outside the entrance
- possibly the maximum number of searching vehicles

These measurements may be adjusted once the model and experiment design are more developed.

## Current hypothesis

We expect congestion to depend on the balance between how quickly vehicles arrive and how quickly parking spaces become available.

When arrival demand becomes too high compared with parking turnover, the number of searching vehicles may increase sharply.

Entry control may help delay this transition, but if the control is too strict it may reduce congestion inside while increasing waiting outside.

## Current status

This is our updated project direction after Checkpoint 1 feedback.

The exact parameter values, model rules, entry-control thresholds and experiment design are still being developed.
