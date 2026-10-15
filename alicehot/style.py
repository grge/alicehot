from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent.parent / "figures"

SURFACE = "#ffffff"
INK = "#1a1a19"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e6e5df"
BASELINE = "#c3c2b7"

HEAT = "#e0542e"
HEAT_LIGHT = "#f2b8a0"
COOL = "#2a78d6"
NEUTRAL = "#a8a69e"

SLIDE = (40 / 3, 7.5)
SOURCE = ("Data: Bureau of Meteorology, ACORN-SAT v2.6 to 2024 and Alice Springs "
          "Airport (015590) observations from 2025")


def apply():
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Noto Sans", "DejaVu Sans"],
            "font.size": 15,
            "text.color": INK,
            "axes.labelcolor": INK_2,
            "axes.edgecolor": BASELINE,
            "axes.facecolor": SURFACE,
            "axes.linewidth": 1,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 1,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelcolor": INK_2,
            "ytick.labelcolor": INK_2,
            "xtick.labelsize": 15,
            "ytick.labelsize": 15,
            "ytick.major.size": 0,
            "xtick.major.size": 6,
            "legend.frameon": False,
            "legend.fontsize": 15,
            "figure.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "svg.fonttype": "none",
        }
    )


def slide(**kwargs):
    return plt.figure(figsize=SLIDE, **kwargs)


def headline(fig, title, subtitle=None, source=SOURCE):
    fig.text(0.05, 0.93, title, fontsize=28, fontweight="semibold", va="top")
    if subtitle:
        fig.text(0.05, 0.855, subtitle, fontsize=17, color=INK_2, va="top")
    if source:
        fig.text(0.05, 0.035, source, fontsize=11, color=MUTED, va="bottom")


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=200)
    plt.close(fig)
