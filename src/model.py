"""
Baseline parking-search agent-based model.

Already implemented here:
- one-way loop road
- parking spaces
- searching-car movement
- two-step parking manoeuvres
- temporary blocking behind a parking car
- parked cars leaving after a fixed placeholder duration

Not implemented yet on purpose:
- random/configurable arrival rate
- configurable/stochastic parking duration
- outside waiting queue
- entry control
- measurements and experiment summaries

Those are separate GitHub tasks for the next development stage.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


BASELINE_PARKING_DURATION = 12


@dataclass
class Vehicle:
    """Information needed for one car in the baseline model."""

    vid: int
    state: str = "SEARCHING"   # SEARCHING -> PARKING -> PARKED -> DONE
    road_pos: Optional[int] = None
    spot_idx: Optional[int] = None
    parking_timer: int = 0
    parked_timer: int = 0


class ParkingModel:
    """Simple one-way-loop parking model."""

    def __init__(
        self,
        road_length=30,
        n_spaces=12,
        initial_occupancy=0.75,
        parking_manoeuvre_steps=2,
        seed=None,
    ):
        if not (0 < n_spaces <= road_length):
            raise ValueError("n_spaces must be between 1 and road_length")
        if not (0 <= initial_occupancy <= 1):
            raise ValueError("initial_occupancy must be between 0 and 1")
        if parking_manoeuvre_steps < 1:
            raise ValueError("parking_manoeuvre_steps must be at least 1")

        self.road_length = road_length
        self.n_spaces = n_spaces
        self.parking_manoeuvre_steps = parking_manoeuvre_steps
        self.rng = np.random.default_rng(seed)

        # Put parking spaces at roughly even positions around the loop.
        positions = np.linspace(0, road_length - 1, n_spaces, dtype=int)
        self.spot_road_pos = list(map(int, positions))
        self.road_to_spot = {
            road_pos: i for i, road_pos in enumerate(self.spot_road_pos)
        }

        # road[pos] stores a car ID or None.
        self.road = [None] * road_length

        # spots[i] stores a parked car ID or None.
        self.spots = [None] * n_spaces

        self.vehicles = {}
        self.next_vid = 0
        self.time = 0

        # Start partly occupied so the demo does not need a long warm-up.
        n_initial = round(initial_occupancy * n_spaces)
        if n_initial:
            chosen_spots = self.rng.choice(
                n_spaces, size=n_initial, replace=False
            )
            for spot_idx in chosen_spots:
                car = self._new_vehicle()
                car.state = "PARKED"
                car.spot_idx = int(spot_idx)
                car.parked_timer = BASELINE_PARKING_DURATION
                self.spots[int(spot_idx)] = car.vid

    def _new_vehicle(self):
        """Create one car with a unique ID."""
        car = Vehicle(self.next_vid)
        self.vehicles[car.vid] = car
        self.next_vid += 1
        return car

    def add_car_at_entrance(self):
        """
        Add one new searching car at road position 0.

        This is only a simple baseline arrival method.
        If the entrance is occupied, no car is added.

        A later GitHub task will replace this with a configurable random arrival
        process and an outside waiting queue.
        """
        if self.road[0] is not None:
            return False

        car = self._new_vehicle()
        car.state = "SEARCHING"
        car.road_pos = 0
        self.road[0] = car.vid
        return True

    def _update_parked_cars(self):
        """
        Count down parked cars and free spaces when the timer reaches zero.

        The fixed timer is only a placeholder for the baseline model.
        Later it will be replaced with a configurable/stochastic parking duration.
        """
        for spot_idx, vid in enumerate(list(self.spots)):
            if vid is None:
                continue

            car = self.vehicles[vid]
            car.parked_timer -= 1

            if car.parked_timer <= 0:
                self.spots[spot_idx] = None
                car.state = "DONE"
                car.spot_idx = None

    def _progress_parking_manoeuvres(self):
        """
        Continue cars that are already parking.

        A PARKING car stays on its road position while the timer counts down.
        When the timer reaches zero, the car moves into the parking space.
        """
        finished = []

        for road_pos, vid in enumerate(self.road):
            if vid is None:
                continue

            car = self.vehicles[vid]

            if car.state == "PARKING":
                car.parking_timer -= 1
                if car.parking_timer <= 0:
                    finished.append((road_pos, vid, car.spot_idx))

        for road_pos, vid, spot_idx in finished:
            if self.spots[spot_idx] is not None:
                raise RuntimeError("Parking spot conflict")

            car = self.vehicles[vid]
            self.road[road_pos] = None
            self.spots[spot_idx] = vid

            car.state = "PARKED"
            car.road_pos = None
            car.parked_timer = BASELINE_PARKING_DURATION

    def _start_parking_manoeuvres(self):
        """
        Let a SEARCHING car start parking if the adjacent parking space is empty.
        """
        starters = []

        for road_pos, vid in enumerate(self.road):
            if vid is None:
                continue

            car = self.vehicles[vid]
            if car.state != "SEARCHING":
                continue

            spot_idx = self.road_to_spot.get(road_pos)
            if spot_idx is not None and self.spots[spot_idx] is None:
                starters.append((vid, spot_idx))

        for vid, spot_idx in starters:
            car = self.vehicles[vid]
            car.state = "PARKING"
            car.spot_idx = spot_idx
            car.parking_timer = self.parking_manoeuvre_steps

    def _move_searching_cars(self):
        """
        Move searching cars one road position using a simultaneous update.

        Adjacent cars are allowed to move together:

            Before: [A][B][C][ ]
            After:  [ ][A][B][C]

        A PARKING car does not move. Searching cars directly behind it are
        blocked, and that blockage propagates backward through an adjacent line.
        """
        occupied = {
            pos: vid for pos, vid in enumerate(self.road) if vid is not None
        }

        # Parking cars are the initial stationary blockers.
        blocked_positions = {
            pos
            for pos, vid in occupied.items()
            if self.vehicles[vid].state == "PARKING"
        }

        # Propagate the blockage backward through adjacent searching cars.
        changed = True
        while changed:
            changed = False

            for pos, vid in occupied.items():
                car = self.vehicles[vid]

                if car.state != "SEARCHING" or pos in blocked_positions:
                    continue

                next_pos = (pos + 1) % self.road_length

                if next_pos in blocked_positions:
                    blocked_positions.add(pos)
                    changed = True

        # Build the next road state separately so update order does not matter.
        new_road = [None] * self.road_length

        # Parking cars stay where they are.
        for pos, vid in occupied.items():
            if self.vehicles[vid].state == "PARKING":
                new_road[pos] = vid

        # Move or hold searching cars.
        for pos, vid in occupied.items():
            car = self.vehicles[vid]

            if car.state != "SEARCHING":
                continue

            if pos in blocked_positions:
                new_road[pos] = vid
                car.road_pos = pos
            else:
                next_pos = (pos + 1) % self.road_length

                if new_road[next_pos] is not None:
                    raise RuntimeError("Movement collision")

                new_road[next_pos] = vid
                car.road_pos = next_pos

        self.road = new_road

    def step(self):
        """
        Advance the baseline model by one simulation step.

        Update order:
        1. parked cars count down and may leave;
        2. cars already parking continue/finish parking;
        3. searching cars beside empty spaces start parking;
        4. the remaining searching cars move.

        New arrivals are currently added manually with add_car_at_entrance().
        """
        self._update_parked_cars()
        self._progress_parking_manoeuvres()
        self._start_parking_manoeuvres()
        self._move_searching_cars()
        self.time += 1

    def run(self, steps=100, add_car_every=None):
        """
        Run several baseline steps.

        add_car_every is only a demo helper.
        Example: add_car_every=4 attempts to add one car every 4 steps.

        It is NOT the final arrival-rate experiment variable.
        """
        for _ in range(steps):
            if add_car_every and self.time % add_car_every == 0:
                self.add_car_at_entrance()

            self.step()

    def road_as_text(self):
        """
        Return a compact text view of the road.

        '.' = empty road position
        'S' = searching car
        'P' = car currently parking
        """
        symbols = []

        for vid in self.road:
            if vid is None:
                symbols.append(".")
                continue

            car = self.vehicles[vid]

            if car.state == "SEARCHING":
                symbols.append("S")
            elif car.state == "PARKING":
                symbols.append("P")
            else:
                symbols.append("?")

        return "".join(symbols)
