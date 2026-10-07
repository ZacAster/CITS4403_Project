"""Show one static snapshot of the parking model
"""
import matplotlib.pyplot as plt
from src.model import ParkingModel
from utils.visualisation import draw_model

def main():
    # Create a normal copy of the existing parking model
    model = ParkingModel(
        road_length=30,
        n_spaces=12,
        initial_occupancy=0.75,
        arrival_prob=0.5,
        mean_parking_duration=30,
        entry_control=False,
        seed=4,
    )

    # Run a few steps so the picture contains some cars
    model.run(steps=25)

    draw_model(
        model,
        title="Example parking model state",
    )
    plt.show()


if __name__ == "__main__":
    main()