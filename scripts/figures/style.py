from __future__ import annotations

from itertools import cycle, islice

from cycler import cycler
import matplotlib.pyplot as plt


def apply_style() -> None:
    default_colors = plt.rcParamsDefault["axes.prop_cycle"].by_key()["color"]
    markers = ["o", "s", "D", "^", "v", "P", "X"]
    marker_cycle = list(islice(cycle(markers), len(default_colors)))
    plt.rcParams.update(
        {
            "figure.figsize": (8, 6),
            "figure.dpi": 600,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Now Micro", "Helvetica"],
            "axes.prop_cycle": cycler("color", default_colors)
            + cycler("marker", marker_cycle),
        }
    )
