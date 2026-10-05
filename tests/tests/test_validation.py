"""Additional validation and edge-case tests for the parking model."""

from src.model import ParkingModel


def test_zero_arrival_probability_creates_no_new_vehicles():
    """With arrival_prob=0, the model should not generate automatic arrivals."""
    model = ParkingModel(
        road_length=12,
        n_spaces=6,
        initial_occupancy=0.0,
        arrival_prob=0.0,
        mean_parking_duration=5,
        seed=10,
    )

    initial_vehicle_count = len(model.vehicles)

    model.run(steps=100)

    assert len(model.vehicles) == initial_vehicle_count
    assert len(model.waiting_queue) == 0


def test_parking_occupancy_never_exceeds_capacity():
    """The number of occupied parking spaces must never exceed n_spaces."""
    model = ParkingModel(
        road_length=12,
        n_spaces=6,
        initial_occupancy=0.5,
        arrival_prob=1.0,
        mean_parking_duration=20,
        entry_control=False,
        seed=11,
    )

    for _ in range(200):
        model.step()

        occupied_spaces = sum(
            1 for vid in model.spots
            if vid is not None
        )

        assert occupied_spaces <= model.n_spaces


def test_same_seed_produces_reproducible_state_history():
    """Identical parameters and seeds should produce identical model behaviour."""
    kwargs = dict(
        road_length=12,
        n_spaces=6,
        initial_occupancy=0.5,
        arrival_prob=0.7,
        mean_parking_duration=10,
        entry_control=True,
        entry_threshold=0.85,
        seed=12,
    )

    model_a = ParkingModel(**kwargs)
    model_b = ParkingModel(**kwargs)

    for _ in range(100):
        model_a.step()
        model_b.step()

    assert model_a.road == model_b.road
    assert model_a.spots == model_b.spots
    assert list(model_a.waiting_queue) == list(model_b.waiting_queue)


def test_vehicle_counts_remain_consistent_under_high_demand():
    """High demand should not duplicate or lose active vehicle IDs."""
    model = ParkingModel(
        road_length=12,
        n_spaces=6,
        initial_occupancy=0.5,
        arrival_prob=1.0,
        mean_parking_duration=30,
        entry_control=True,
        entry_threshold=0.85,
        seed=13,
    )

    for _ in range(200):
        model.step()

        active_ids = (
            [vid for vid in model.road if vid is not None]
            + [vid for vid in model.spots if vid is not None]
            + list(model.waiting_queue)
        )

        assert len(active_ids) == len(set(active_ids))


def test_full_car_park_does_not_exceed_capacity_under_continued_arrivals():
    """Continued arrivals must not create more occupied spaces than capacity."""
    model = ParkingModel(
        road_length=12,
        n_spaces=6,
        initial_occupancy=1.0,
        arrival_prob=1.0,
        mean_parking_duration=50,
        entry_control=True,
        entry_threshold=1.0,
        seed=14,
    )

    for _ in range(50):
        model.step()

        occupied_spaces = sum(
            1 for vid in model.spots
            if vid is not None
        )

        assert occupied_spaces <= 6
