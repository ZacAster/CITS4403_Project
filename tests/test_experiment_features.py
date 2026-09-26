"""Tests for the experiment features added for Checkpoint """

from src.model import ParkingModel


def test_entry_control_keeps_car_outside_when_threshold_reached():
    """A new arrival should wait outside when occupancy reaches the threshold."""
    model = ParkingModel(
        road_length=6,
        n_spaces=2,
        initial_occupancy=1.0,
        arrival_prob=1.0,
        entry_control=True,
        entry_threshold=0.5,
        seed=1,
    )

    created = model._generate_arrival()

    assert created is True
    assert len(model.waiting_queue) == 1

    waiting_vid = model.waiting_queue[0]
    waiting_car = model.vehicles[waiting_vid]

    assert waiting_car.state == "WAITING"
    assert waiting_car.road_pos is None
    assert model.road[0] is None


def test_waiting_car_can_enter_later():
    """The first waiting car should enter after occupancy falls below the threshold."""
    model = ParkingModel(
        road_length=6,
        n_spaces=2,
        initial_occupancy=1.0,
        arrival_prob=1.0,
        entry_control=True,
        entry_threshold=1.0,
        seed=2,
    )

    model._generate_arrival()
    waiting_vid = model.waiting_queue[0]

    # Free one parking space so occupancy falls below the threshold.
    parked_vid = model.spots[0]
    model.spots[0] = None
    model.vehicles[parked_vid].state = "DONE"
    model.vehicles[parked_vid].spot_idx = None

    admitted = model._admit_waiting_car()

    assert admitted is True
    assert model.waiting_queue == []
    assert model.road[0] == waiting_vid
    assert model.vehicles[waiting_vid].state == "SEARCHING"
    assert model.vehicles[waiting_vid].road_pos == 0


def test_parked_car_leaving_frees_parking_space():
    """When a parked car's timer expires, its parking space should become free."""
    model = ParkingModel(
        road_length=6,
        n_spaces=1,
        initial_occupancy=1.0,
        arrival_prob=0.0,
        seed=3,
    )

    parked_vid = model.spots[0]
    parked_car = model.vehicles[parked_vid]
    parked_car.parked_timer = 1

    model._update_parked_cars()

    assert model.spots[0] is None
    assert parked_car.state == "DONE"
    assert parked_car.spot_idx is None


def test_recorded_waiting_and_search_times_are_not_negative():
    """Waiting-time measurements for successfully parked cars must be non-negative."""
    model = ParkingModel(
        road_length=6,
        n_spaces=3,
        initial_occupancy=0.0,
        parking_manoeuvre_steps=1,
        arrival_prob=0.0,
        seed=4,
    )

    assert model.add_car_at_entrance() is True
    model.run(steps=3)

    assert model.parking_results

    for result in model.parking_results:
        assert result["parking_search_time"] >= 0
        assert result["outside_waiting_time"] >= 0
        assert result["total_waiting_time"] >= 0


def test_one_car_never_appears_in_two_places_at_same_time():
    """A vehicle ID must not appear in the road, a space, and the queue simultaneously."""
    model = ParkingModel(
        road_length=12,
        n_spaces=6,
        initial_occupancy=0.5,
        parking_manoeuvre_steps=2,
        arrival_prob=0.7,
        mean_parking_duration=5,
        entry_control=True,
        entry_threshold=0.85,
        seed=5,
    )

    for _ in range(100):
        model.step()

        active_locations = (
            [vid for vid in model.road if vid is not None]
            + [vid for vid in model.spots if vid is not None]
            + list(model.waiting_queue)
        )

        assert len(active_locations) == len(set(active_locations))
