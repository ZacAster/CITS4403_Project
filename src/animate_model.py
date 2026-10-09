"""Compare fixed-demand bursty and spread arrivals on the same clock."""
import argparse
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from src.experiments import (
    build_arrival_counts,
    create_burst_model,
    step_scheduled_model,
)
from utils.visualisation import draw_model

def create_comparison(total_arrivals=24, duration=30, seed=3):
    widths = (10, 60)

    models = [
        create_burst_model(duration, seed)
        for _ in widths
    ]

    schedules = [
        build_arrival_counts(total_arrivals, width)
        for width in widths
    ]

    return models, schedules


def advance_to_step(models, schedules, target):
    """Advance each model forward to the requested step.
    A target at or before a model's current time leaves that model
    unchanged. This function does not rewind or reset the simulation.
    """
    for model, schedule in zip(models, schedules):
        while model.time < target:
            step_scheduled_model(model, schedule)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arrivals", type=int, default=24)
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--interval", type=int, default=100)
    args = parser.parse_args()

    models, schedules = create_comparison(
        args.arrivals,
        args.duration,
        args.seed,
    )

    if args.steps <= max(max(s) for s in schedules) or args.interval < 1:
        parser.error(
            "Include all arrivals"
        )

    initial_counts = [len(model.vehicles) for model in models]

    fig = plt.figure(figsize=(14, 9))
    grid = fig.add_gridspec(2, 2, height_ratios=(2, 1))

    views = [fig.add_subplot(grid[0, i]) for i in range(2)]
    chart = fig.add_subplot(grid[1, :])

    labels = ("Bursty: width 10", "Spread: width 60")

    def draw():
        for model, ax, label, initial in zip(
            models, views, labels, initial_counts
        ):
            arrived = len(model.vehicles) - initial

            draw_model(
                model,
                ax=ax,
                title=(
                    f"{label} | "
                    f"Arrived: {arrived}/{args.arrivals}"
                ),
            )

        chart.clear()

        for model, label in zip(models, labels):
            history = model.step_results

            chart.plot(
                [0] + [row["time"] for row in history],
                [0] + [
                    row["searching_inside"] + row["waiting_outside"]
                    for row in history
                ],
                label=label,
            )

        chart.set_xlim(0, args.steps)
        chart.set_ylim(0, args.arrivals + 1)
        chart.set_xlabel("Simulation step")
        chart.set_ylabel("Searching + waiting vehicles")
        chart.legend(loc="upper right")
        chart.grid(alpha=0.25)
        chart.set_title("Same total demand | Space: pause/resume")

        return []

    def update(target):
        advance_to_step(models, schedules, target)
        return draw()

    animation = FuncAnimation(
        fig,
        update,
        init_func=draw,
        frames=range(1, args.steps + 1),
        interval=args.interval,
        repeat=False,
        blit=False,
        cache_frame_data=False,
    )

    paused = False

    def on_key(event):
        nonlocal paused

        # Ignore other keys and space presses after playback has finished.
        if event.key != " " or animation.event_source is None:
            return

        paused = not paused

        if paused:
            animation.pause()
        else:
            animation.resume()

    fig.canvas.mpl_connect("key_press_event", on_key)
    plt.show()


if __name__ == "__main__":
    main()
