
"""Tests for parking model rules and vehicle conservation."""

from src.model import ParkingModel


def make_model(**kwargs):
    settings = dict(
        road_length=6,
        n_spaces=1,
        initial_occupancy=0,
        arrival_prob=0,
        parking_manoeuvre_steps=2,
        seed=1,
    )
    settings.update(kwargs)
    return ParkingModel(**settings)


def place_searching(model, position):
    car = model._new_vehicle()
    car.state = "SEARCHING"
    car.road_pos = position
    model.road[position] = car.vid
    return car


def check_conservation(model):
    """Check that every car has exactly one valid location."""
    found = []

    for pos, vid in enumerate(model.road):
        if vid is not None:
            car = model.vehicles[vid]
            assert car.state in ("SEARCHING", "PARKING")
            assert car.road_pos == pos
            found.append(vid)

    for index, vid in enumerate(model.spots):
        if vid is not None:
            car = model.vehicles[vid]
            assert car.state == "PARKED"
            assert car.spot_idx == index
            found.append(vid)

    for vid in model.waiting_queue:
        car = model.vehicles[vid]
        assert car.state == "WAITING"
        assert car.road_pos is None
        found.append(vid)

    for vid, car in model.vehicles.items():
        if car.state == "DONE":
            found.append(vid)

    assert len(found) == len(set(found))
    assert set(found) == set(model.vehicles)


def test_movement_wraps_around_loop():
    model = make_model()
    car = place_searching(model, 5)

    model._move_searching_cars()

    assert model.road[5] is None
    assert model.road[0] == car.vid
    assert car.road_pos == 0
    assert model.current_blocked_count == 0
    check_conservation(model)


def test_blocking_propagates_across_boundary():
    model = make_model(n_spaces=6)

    parking = model._new_vehicle()
    parking.state = "PARKING"
    parking.road_pos = 1
    parking.spot_idx = 1
    parking.parking_timer = 2
    model.road[1] = parking.vid

    car0 = place_searching(model, 0)
    car5 = place_searching(model, 5)
    car3 = place_searching(model, 3)

    model._move_searching_cars()

    assert model.road[1] == parking.vid
    assert model.road[0] == car0.vid
    assert model.road[5] == car5.vid
    assert model.road[4] == car3.vid
    assert car3.road_pos == 4
    assert model.current_blocked_count == 2

    check_conservation(model)


def test_fifo_queue_and_one_admission_per_step():
    model = make_model(mean_parking_duration=2)

    waiting = []
    for _ in range(3):
        car = model._new_vehicle()
        car.state = "WAITING"
        car.arrival_time = 0
        model.waiting_queue.append(car.vid)
        waiting.append(car.vid)

    admitted = []

    for _ in range(200):
        before = list(model.waiting_queue)

        model.step()

        after = list(model.waiting_queue)
        newly_admitted = [
            vid for vid in before if vid not in after
        ]

        assert len(newly_admitted) <= 1
        assert after == before[len(newly_admitted):]

        if newly_admitted:
            vid = newly_admitted[0]
            assert vid == waiting[len(admitted)]
            assert model.vehicles[vid].entry_time is not None
            admitted.append(vid)

        check_conservation(model)

        if len(admitted) == 3:
            break

    assert admitted == waiting
    assert model.waiting_queue == []


def test_departure_precedes_queue_admission():
    model = make_model(
        initial_occupancy=1,
        entry_control=True,
        entry_threshold=1.0,
    )

    parked_id = model.spots[0]
    parked = model.vehicles[parked_id]
    parked.parked_timer = 1

    waiting = model._new_vehicle()
    waiting.state = "WAITING"
    waiting.arrival_time = 0
    model.waiting_queue.append(waiting.vid)

    assert model.road[0] is None
    assert not model._entry_allowed()

    model.step()

    assert parked.state == "DONE"
    assert model.spots[0] is None
    assert waiting.vid not in model.waiting_queue
    assert model.road[0] == waiting.vid
    assert waiting.state == "SEARCHING"
    assert waiting.entry_time == 0

    check_conservation(model)
