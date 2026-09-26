"""
Small baseline demo.

This only demonstrates the movement/parking code that is already implemented.
It does not contain the final experiment parameters or measurements.
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

    # Baseline demo only: try to add one car every 3 steps.
    # Later this will be replaced by the real arrival-rate code.
    for _ in range(30):
        if model.time % 3 == 0:
            model.add_car_at_entrance()

        print(f"step {model.time:02d}: {model.road_as_text()}")
        model.step()


if __name__ == "__main__":
    main()
