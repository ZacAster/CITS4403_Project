"""
Parking-search agent-based model.

Implemented here:
 one-way loop road
 parking spaces
 searching-car movement
 two-step parking manoeuvres
 temporary blocking behind a parking car
 parked cars leaving after a configurable stochastic duration
 random/configurable arrival rate
 outside waiting queue
 entry control
 per-step measurements
 per-vehicle waiting-time measurements
 end-of-run result summary
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


BASELINE_PARKING_DURATION = 12


@dataclass
class Vehicle:
    """Information needed for one car in the parking model."""

    vid: int
    state: str = "SEARCHING"   # WAITING -> SEARCHING -> PARKING -> PARKED -> DONE
    road_pos: Optional[int] = None
    spot_idx: Optional[int] = None
    parking_timer: int = 0
    parked_timer: int = 0

    # Timestamps used for experiment measurements.
    arrival_time: Optional[int] = None
    entry_time: Optional[int] = None
    parked_time: Optional[int] = None


class ParkingModel:
    """Simple one-way-loop parking model."""

    def __init__(
        self,
        road_length=30,
        n_spaces=12,
        initial_occupancy=0.75,
        parking_manoeuvre_steps=2,
        arrival_prob=0.0,
        mean_parking_duration=BASELINE_PARKING_DURATION,
        entry_control=False,
        entry_threshold=0.9,
        seed=None,
    ):
        if not (0 < n_spaces <= road_length):
            raise ValueError("n_spaces must be between 1 and road_length")
        if not (0 <= initial_occupancy <= 1):
            raise ValueError("initial_occupancy must be between 0 and 1")
        if parking_manoeuvre_steps < 1:
            raise ValueError("parking_manoeuvre_steps must be at least 1")
        if not (0 <= arrival_prob <= 1):
            raise ValueError("arrival_prob must be between 0 and 1")
        if mean_parking_duration <= 0:
            raise ValueError("mean_parking_duration must be greater than 0")
        if not (0 <= entry_threshold <= 1):
            raise ValueError("entry_threshold must be between 0 and 1")

        self.road_length = road_length
        self.n_spaces = n_spaces
        self.parking_manoeuvre_steps = parking_manoeuvre_steps

        # Experiment settings. These can be changed when the model is created
        # without changing any of the movement code below.
        self.arrival_prob = arrival_prob
        self.mean_parking_duration = mean_parking_duration
        self.entry_control = entry_control
        self.entry_threshold = entry_threshold

        # Cars that arrive but cannot currently enter wait here in FIFO order.
        self.waiting_queue = []

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

        # Measurements for Issue #11.
        # step_results stores one model-state record for each completed step.
        self.step_results = []

        # parking_results stores waiting-time results for cars that successfully
        # complete parking during the simulation.
        self.parking_results = []

        # Number of searching cars blocked during the most recent movement step.
        self.current_blocked_count = 0

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
                car.parked_timer = self._sample_parking_duration()

                # These cars are already parked when the simulation begins.
                car.arrival_time = 0
                car.entry_time = 0
                car.parked_time = 0

                self.spots[int(spot_idx)] = car.vid

    def _sample_parking_duration(self):
        """Return a random positive parking duration with the configured mean."""
        return max(
            1,
            int(round(self.rng.exponential(self.mean_parking_duration)))
        )

    def _new_vehicle(self):
        """Create one car with a unique ID."""
        car = Vehicle(self.next_vid)
        self.vehicles[car.vid] = car
        self.next_vid += 1
        return car

    def _parking_occupancy(self):
        """Return the fraction of parking spaces that are currently occupied."""
        occupied_spaces = sum(vid is not None for vid in self.spots)
        return occupied_spaces / self.n_spaces

    def _entry_allowed(self):
        """
        Return True when the entry-control rule allows a car to enter.

        When entry control is off, occupancy does not restrict entry.
        When it is on, entry is stopped once parking occupancy reaches the
        configured threshold.
        """
        if not self.entry_control:
            return True

        return self._parking_occupancy() < self.entry_threshold

    def _can_enter_now(self):
        """Return True when both the entrance and entry-control rule allow entry."""
        return self.road[0] is None and self._entry_allowed()

    def _place_car_at_entrance(self, car):
        """Place an existing vehicle at road position 0 as a searching car."""
        car.state = "SEARCHING"
        car.road_pos = 0
        car.entry_time = self.time
        self.road[0] = car.vid

    def add_car_at_entrance(self):
        """
        Manually add one new searching car at road position 0.

        This helper is kept for the baseline demo and existing tests. It also
        respects entry control. If the entrance or entry-control rule blocks
        entry, no manual car is created and False is returned.

        Experiment arrivals are handled separately by _generate_arrival(),
        which stores blocked arrivals in the outside waiting queue.
        """
        if not self._can_enter_now():
            return False

        car = self._new_vehicle()
        car.arrival_time = self.time
        self._place_car_at_entrance(car)
        return True

    def _generate_arrival(self):
        """
        Generate a new outside arrival using arrival_prob.

        A successful arrival enters immediately when possible. Otherwise the
        vehicle is stored in the outside waiting queue and can enter later.
        """
        if self.rng.random() >= self.arrival_prob:
            return False

        car = self._new_vehicle()
        car.arrival_time = self.time

        if self._can_enter_now() and not self.waiting_queue:
            self._place_car_at_entrance(car)
        else:
            car.state = "WAITING"
            car.road_pos = None
            self.waiting_queue.append(car.vid)

        return True

    def _admit_waiting_car(self):
        """
        Let the first waiting car enter when the entrance and control rule allow.

        Only one car can enter per simulation step because there is one entrance.
        """
        if not self.waiting_queue:
            return False

        if not self._can_enter_now():
            return False

        vid = self.waiting_queue.pop(0)
        car = self.vehicles[vid]
        self._place_car_at_entrance(car)
        return True

    def _update_parked_cars(self):
        """
        Count down parked cars and free spaces when the timer reaches zero.

        Each car receives a stochastic duration sampled from
        mean_parking_duration when it becomes parked.
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

    def _record_successful_parking(self, car):
        """Store waiting-time measurements for a car that has successfully parked."""
        if car.arrival_time is None or car.entry_time is None or car.parked_time is None:
            return

        outside_waiting_time = car.entry_time - car.arrival_time
        parking_search_time = car.parked_time - car.entry_time
        total_waiting_time = car.parked_time - car.arrival_time

        self.parking_results.append(
            {
                "vid": car.vid,
                "arrival_time": car.arrival_time,
                "entry_time": car.entry_time,
                "parked_time": car.parked_time,
                "parking_search_time": parking_search_time,
                "outside_waiting_time": outside_waiting_time,
                "total_waiting_time": total_waiting_time,
            }
        )

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
            car.parked_time = self.time
            car.parked_timer = self._sample_parking_duration()

            self._record_successful_parking(car)

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

        # Record how many SEARCHING cars were held up by parking manoeuvres.
        self.current_blocked_count = sum(
            1
            for pos, vid in occupied.items()
            if self.vehicles[vid].state == "SEARCHING"
            and pos in blocked_positions
        )

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

    def _record_step_result(self):
        """Record the model measurements required at the end of each step."""
        searching_inside = sum(
            1 for car in self.vehicles.values() if car.state == "SEARCHING"
        )

        self.step_results.append(
            {
                "time": self.time,
                "parking_occupancy": self._parking_occupancy(),
                "searching_inside": searching_inside,
                "waiting_outside": len(self.waiting_queue),
                "blocked_by_parking": self.current_blocked_count,
            }
        )

    def step(self):
        """
        Advance the model by one simulation step.

        Update order:
        1. parked cars count down and may leave;
        2. cars already parking continue/finish parking;
        3. searching cars beside empty spaces start parking;
        4. the remaining searching cars move;
        5. the first outside waiting car may enter;
        6. a new arrival may be generated using arrival_prob;
        7. record the model state for this completed step.

        Waiting cars are given priority over a brand-new arrival.
        """
        self._update_parked_cars()
        self._progress_parking_manoeuvres()
        self._start_parking_manoeuvres()
        self._move_searching_cars()

        # Existing waiting cars get the first chance to use the entrance.
        self._admit_waiting_car()

        # Then generate this step's possible new outside arrival.
        self._generate_arrival()

        self.time += 1
        self._record_step_result()

    def summary(self):
        """Return a readable summary of the main experiment results."""
        if self.parking_results:
            mean_search_time = sum(
                result["parking_search_time"] for result in self.parking_results
            ) / len(self.parking_results)

            mean_total_waiting_time = sum(
                result["total_waiting_time"] for result in self.parking_results
            ) / len(self.parking_results)
        else:
            mean_search_time = 0.0
            mean_total_waiting_time = 0.0

        if self.step_results:
            searching_counts = [
                result["searching_inside"] for result in self.step_results
            ]
            mean_searching_cars = sum(searching_counts) / len(searching_counts)
            max_searching_cars = max(searching_counts)
        else:
            mean_searching_cars = 0.0
            max_searching_cars = 0

        return {
            "mean_search_time": mean_search_time,
            "mean_total_waiting_time": mean_total_waiting_time,
            "mean_searching_cars": mean_searching_cars,
            "max_searching_cars": max_searching_cars,
            "successful_parking_count": len(self.parking_results),
        }

    def run(self, steps=100, add_car_every=None):
        """
        Run several model steps and return the main result summary.

        arrival_prob is the experiment variable used for random arrivals.

        add_car_every is kept only as a backwards-compatible demo helper.
        Example: add_car_every=4 also attempts a manual car every 4 steps.
        For experiments, normally leave add_car_every as None and set
        arrival_prob instead.
        """
        for _ in range(steps):
            if add_car_every and self.time % add_car_every == 0:
                self.add_car_at_entrance()

            self.step()

        return self.summary()

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
