from __future__ import annotations

from itertools import cycle, islice

from cycler import cycler
import matplotlib.pyplot as plt


def apply_style() -> None:
    # Okabe & Ito (2008) colorblind-safe qualitative palette.
    palette = [
        "#000000",
        "#E69F00",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
        "#D55E00",
        "#CC79A7",
    ]
    markers = ["o", "s", "D", "^", "v", "P", "X", "p"]
    marker_cycle = list(islice(cycle(markers), len(palette)))
    plt.rcParams.update(
        {
            "figure.figsize": (8, 6),
            "figure.dpi": 900,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Now Micro", "Helvetica"],
            "axes.prop_cycle": cycler("color", palette)
            + cycler("marker", marker_cycle),
        }
    )
