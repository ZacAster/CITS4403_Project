"""Simple visualisation helpers for the parking-search model.
"""
import math
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# The road is drawn as a circle with parking spaces slightly outside it.
ROAD_RADIUS = 1.0
PARKING_RADIUS = 1.28

def _position_on_circle(index, total, radius):
    """Return the x/y position for one model position on a circle."""

    # Convert the road index into an angle around the circle.
    angle = 2 * math.pi * index / total

    # Convert the angle into normal x/y coordinates for matplotlib.
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)

    return x, y

def draw_model(model, ax=None, title=None):
    """Draw one static snapshot of the current ParkingModel state.

    The function just read the info from the model.
    It shows:
    - the one-way loop road
    - empty and occupied parking spaces
    - searching and parking cars on the road
    - the entrance
    - a small summary of the current model state
    """

    # If no matplotlib axes were supplied, create a new figure
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.figure

    # Remove anything that was already drawn
    # This will also be useful later when we animate the model
    ax.clear()

    # Draw the road
    # Give every road position an x/y coordinate
    road_xy = [
        _position_on_circle(
            pos,
            model.road_length,
            ROAD_RADIUS,
        )
        for pos in range(model.road_length)
    ]

    # Add the first point again so the line becomes a closed loop
    closed_road = road_xy + [road_xy[0]]

    # Draw the circular road
    ax.plot(
        [x for x, _ in closed_road],
        [y for _, y in closed_road],
        linewidth=1.5,
        color="0.45",
        zorder=1,
    )

    # Draw small dots for the discrete road positions
    ax.scatter(
        [x for x, _ in road_xy],
        [y for _, y in road_xy],
        s=18,
        color="0.75",
        zorder=2,
    )

    # Draw parking spaces

    for spot_idx, road_pos in enumerate(model.spot_road_pos):

        # Parking space is outside the road at the same angle
        road_x, road_y = road_xy[road_pos]

        spot_x, spot_y = _position_on_circle(
            road_pos,
            model.road_length,
            PARKING_RADIUS,
        )

        # Connect the parking space to its road position
        ax.plot(
            [road_x, spot_x],
            [road_y, spot_y],
            linewidth=1.0,
            color="0.65",
            zorder=1,
        )

        # model.spots contains a vehicle ID if the space is occupied
        occupied = model.spots[spot_idx] is not None

        # Filled square = occupied
        # Empty square = available
        ax.scatter(
            [spot_x],
            [spot_y],
            marker="s",
            s=140,
            facecolors="tab:green" if occupied else "none",
            edgecolors="black",
            linewidths=1.5,
            zorder=3,
        )

    # Draw cars currently on the road

    for road_pos, vehicle_id in enumerate(model.road):

        # None means this road position is empty
        if vehicle_id is None:
            continue

        # Find the Vehicle object for this ID
        car = model.vehicles[vehicle_id]

        # Get the x/y position of this road position
        x, y = road_xy[road_pos]

        # Searching cars use a circle
        if car.state == "SEARCHING":
            marker = "o"
            marker_colour = "tab:blue"

        # A car currently parking uses an X
        elif car.state == "PARKING":
            marker = "X"
            marker_colour = "tab:orange"

        # should normally not happen
 
        else:
            marker = "o"
            marker_colour = "black"

        ax.scatter(
            [x],
            [y],
            marker=marker,
            s=115,
            color=marker_colour,
            edgecolors="black",
            linewidths=0.7,
            zorder=4,
        )

    # Mark the entrance

    # Road position 0 is the entrance
    entrance_x, entrance_y = road_xy[0]

    ax.annotate(
        "Entrance",
        xy=(entrance_x, entrance_y),
        xytext=(1.45, 0.15),
        arrowprops={"arrowstyle": "->"},
        ha="left",
        va="center",
    )

    # Calculate simple information about the model

    searching_count = sum(
        car.state == "SEARCHING"
        for car in model.vehicles.values()
    )

    parking_count = sum(
        car.state == "PARKING"
        for car in model.vehicles.values()
    )

    occupied_count = sum(
        vehicle_id is not None
        for vehicle_id in model.spots
    )

    waiting_count = len(model.waiting_queue)

    # Text shown in the top-left corner
    info_text = (
        f"Step: {model.time}\n"
        f"Searching inside: {searching_count}\n"
        f"Parking manoeuvre: {parking_count}\n"
        f"Occupied spaces: {occupied_count}/{model.n_spaces}\n"
        f"Waiting outside: {waiting_count}"
    )

    ax.text(
        0.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        bbox={
            "boxstyle": "round",
            "facecolor": "white",
            "alpha": 0.9,
        },
    )

    # Legend

    legend_items = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor="tab:blue",
            markeredgecolor="black",
            markersize=9,
            label="Searching car",
        ),
        Line2D(
            [0],
            [0],
            marker="X",
            linestyle="none",
            markerfacecolor="tab:orange",
            markeredgecolor="black",
            markersize=9,
            label="Parking car",
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            linestyle="none",
            markerfacecolor="tab:green",
            markeredgecolor="black",
            markersize=9,
            label="Occupied space",
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            linestyle="none",
            markerfacecolor="none",
            markeredgecolor="black",
            markersize=9,
            label="Empty space",
        ),
    ]

    ax.legend(
        handles=legend_items,
        loc="lower left",
    )

    # Make the road stay circular
    ax.set_aspect("equal")

    # Give some extra room around the parking spaces
    ax.set_xlim(-1.65, 1.75)
    ax.set_ylim(-1.55, 1.55)

    # Normal graph axes are not useful for this visualisation
    ax.axis("off")

    # Use a default title
    ax.set_title(
        title or "Parking model state"
    )

    fig.tight_layout()

    return fig, ax