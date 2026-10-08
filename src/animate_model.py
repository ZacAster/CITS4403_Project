"""simple animation for the parking model"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from src.model import ParkingModel
from utils.visualisation import draw_model


def main():
    # same basic model as before
    model = ParkingModel(
        road_length=30,
        n_spaces=12,
        initial_occupancy=0.75,
        arrival_prob=0.45,
        mean_parking_duration=30,
        entry_control=False,
        seed=4,
    )

    fig, ax = plt.subplots(figsize=(8, 8))

    # first frame
    draw_model(
        model,
        ax=ax,
        title="Live parking simulation",
    )

    def update(frame):
        # one model step each frame
        model.step()

        draw_model(
            model,
            ax=ax,
            title="Live parking simulation",
        )

        return []

    # keep this variable or matplotlib may stop it
    animation = FuncAnimation(
        fig,
        update,
        frames=100,
        interval=350,
        repeat=False,
        blit=False,
    )

    plt.show()


if __name__ == "__main__":
    main()