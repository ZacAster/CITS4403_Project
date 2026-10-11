"""
Small baseline demo.
Formal parameter experiments are run from src/experiments.py.
"""

from src.model import ParkingModel


def main():
    model = ParkingModel(
        road_length=24,
        n_spaces=8,
        initial_occupancy=0.75,
        seed=4,
    )

    print("Legend: S=searching, P=parking, .=empty road position")
    print()

    # Try a direct arrival every three steps.
    # The main experiments use fixed arrival schedules.
    for _ in range(30):
        if model.time % 3 == 0:
            model.add_car_at_entrance()

        print(f"step {model.time:02d}: {model.road_as_text()}")
        model.step()


if __name__ == "__main__":
    main()
