
# Parking Model Validation

## Overview

This document describes the automated validation tests
added for Issue #33. The purpose is to verify that the
parking-search simulation maintains correct vehicle
movement, blocking, queue order and update behaviour.

## Test 1: Circular Road Movement

A searching car starts at road position 5 on a road
of length 6. After one movement update, it should
move to position 0.

The test also confirms that the vehicle is not
duplicated or lost.

## Test 2: Blocking Across the Boundary

A parking vehicle is positioned at road position 1.
Searching vehicles occupy positions 0, 5 and 3.

Expected results:
- The parking vehicle remains at position 1.
- Vehicles at positions 0 and 5 stay blocked.
- The vehicle at position 3 moves to position 4.
- The blocked searching count equals 2.

## Test 3: FIFO Queue Admission

Three cars are placed in a known waiting queue.

Expected results:
- Vehicles enter in FIFO order.
- A maximum of one vehicle enters per step.
- Admitted vehicles are removed from the queue.
- The remaining queue order is preserved.
- All three vehicles eventually enter.

## Test 4: Departure Before Admission

The model starts with an occupied parking space,
entry control enabled and one waiting car.

The parked vehicle has one step remaining.

Expected results:
- The parked vehicle departs.
- The parking space becomes available.
- The waiting car enters during the same step.

## Vehicle Conservation

The tests also check that each vehicle is accounted
for in exactly one valid location or completed state.

The supported states are:
- WAITING
- SEARCHING
- PARKING
- PARKED
- DONE

This helps detect lost vehicles, duplicate vehicles
and inconsistent vehicle positions.

## Running the Tests

Run the validation tests:

    python -m pytest tests/test_model_rules.py -v

Run all project tests:

    python -m pytest -v
