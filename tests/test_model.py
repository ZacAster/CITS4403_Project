"""
Tests for the baseline movement and parking rules that are already implemented.

More tests should be added later when the partner features are implemented
(entry control, waiting queue, measurements, configurable parking duration).
"""

from src.model import ParkingModel


def empty_model():
    """Create a small empty model with no automatic arrivals."""
    return ParkingModel(
        road_length=12,
        n_spaces=4,
        initial_occupancy=0,
        parking_manoeuvre_steps=2,
        seed=1,
    )


def test_adjacent_searching_cars_can_move_together():
    """
    Adjacent searching cars should move together if nothing is blocking them.

    Before:
        position 4 = A
        position 5 = B

    After one movement update:
        position 5 = A
        position 6 = B
    """
    model = empty_model()

    car_a = model._new_vehicle()
    car_b = model._new_vehicle()

    car_a.state = "SEARCHING"
    car_b.state = "SEARCHING"
    car_a.road_pos = 4
    car_b.road_pos = 5

    model.road[4] = car_a.vid
    model.road[5] = car_b.vid

    model._move_searching_cars()

    assert model.road[5] == car_a.vid
    assert model.road[6] == car_b.vid


def test_parking_car_blocks_following_car():
    """
    A car that is PARKING stays still and blocks the searching car directly behind.
    """
    model = empty_model()

    follower = model._new_vehicle()
    parking_car = model._new_vehicle()

    follower.state = "SEARCHING"
    parking_car.state = "PARKING"

    follower.road_pos = 4
    parking_car.road_pos = 5
    parking_car.parking_timer = 2

    model.road[4] = follower.vid
    model.road[5] = parking_car.vid

    model._move_searching_cars()

    assert model.road[4] == follower.vid
    assert model.road[5] == parking_car.vid


def test_two_step_parking_manoeuvre():
    """
    With parking_manoeuvre_steps=2, the car stays on the road for two parking
    updates before moving into the parking space.
    """
    model = empty_model()

    road_pos = model.spot_road_pos[1]
    spot_idx = model.road_to_spot[road_pos]

    car = model._new_vehicle()
    car.state = "SEARCHING"
    car.road_pos = road_pos
    model.road[road_pos] = car.vid

    model._start_parking_manoeuvres()
    assert car.state == "PARKING"
    assert car.parking_timer == 2

    model._progress_parking_manoeuvres()
    assert car.state == "PARKING"
    assert model.road[road_pos] == car.vid

    model._progress_parking_manoeuvres()
    assert car.state == "PARKED"
    assert model.spots[spot_idx] == car.vid
    assert model.road[road_pos] is None
