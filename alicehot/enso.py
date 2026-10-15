import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from . import data, style

PHASES = ["El Niño", "Neutral", "La Niña"]
COLOURS = {"El Niño": style.HEAT, "Neutral": style.NEUTRAL, "La Niña": style.COOL}
SOURCE = style.SOURCE + "; ENSO: NOAA Relative Oceanic Niño Index (Dec–Feb)"


def summers(df, threshold):
    counts = data.days_at_or_above(df, threshold).rename("days")
    return pd.concat([counts, data.summer_enso()], axis=1, join="inner")


def plot_bars(df, threshold, title, subtitle):
    s = summers(df, threshold)
    fig = style.slide()
    ax = fig.add_axes([0.05, 0.13, 0.9, 0.6])
    ax.bar(s.index, s.days, width=0.72, color=s.phase.map(COLOURS), zorder=2)

    record = s.days.idxmax()
    ax.annotate(
        f"{data.season_label(record)}: {s.days[record]} days\n"
        f"{s.phase[record]} summer",
        xy=(record, s.days[record]), xytext=(record - 5.5, s.days[record] * 0.98),
        ha="right", va="center", fontsize=14, color=style.INK_2,
        arrowprops=dict(arrowstyle="-", color=style.MUTED, lw=1,
                        shrinkA=4, shrinkB=4),
    )

    ax.set_xlim(s.index.min() - 1, s.index.max() + 1)
    ax.set_ylim(0, s.days.max() * 1.08)
    ax.yaxis.set_major_locator(MaxNLocator(6, steps=[1, 2, 5, 10], integer=True))
    ticks = np.arange(1950, s.index.max() + 1, 10)
    ax.set_xticks(ticks, [data.season_label(t) for t in ticks])

    handles = [Patch(color=COLOURS[p], label=p) for p in PHASES]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncols=3, handlelength=1, handleheight=1, columnspacing=1.5,
              fontsize=16, borderaxespad=0.4)

    style.headline(fig, title, subtitle, source=SOURCE)
    style.save(fig, "enso-bars")


def _swarm(values, width):
    order = np.argsort(values.values)
    offsets = np.zeros(len(values))
    seen = {}
    for i in order:
        v = round(values.iloc[i] / 1.5)
        k = seen.get(v, 0)
        seen[v] = k + 1
        offsets[i] = ((k + 1) // 2) * (1 if k % 2 else -1) * width
    return offsets


def plot_eras(df, threshold, split, title, subtitle):
    s = summers(df, threshold)
    s["recent"] = s.index >= split
    eras = [(False, f"{s.index.min()} to {split - 1}"), (True, f"{split} to now")]

    fig = style.slide()
    ax = fig.add_axes([0.05, 0.2, 0.9, 0.53])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)

    xticks, xlabels = [], []
    for g, phase in enumerate(PHASES):
        for j, (recent, label) in enumerate(eras):
            x = g * 3 + j * 1.15
            sub = s[(s.phase == phase) & (s.recent == recent)].days
            colour = COLOURS[phase]
            ax.scatter(x + _swarm(sub, 0.1), sub, s=70, zorder=3,
                       color=colour if recent else style.SURFACE,
                       edgecolor=colour, linewidth=2)
            mean = sub.mean()
            ax.plot([x - 0.38, x + 0.38], [mean, mean], color=style.INK, lw=3,
                    solid_capstyle="butt", zorder=4)
            ax.text(x + 0.42, mean, f"{mean:.0f}", va="center", ha="left",
                    fontsize=17, fontweight="semibold", zorder=4)
            xticks.append(x)
            xlabels.append(label)
        ax.text(g * 3 + 0.575, -0.12, phase, transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=19, fontweight="semibold")

    ax.set_xticks(xticks, xlabels, fontsize=14)
    ax.set_xlim(-0.8, 2 * 3 + 1.15 + 0.9)
    ax.set_ylim(0, s.days.max() * 1.05)
    ax.yaxis.set_major_locator(MaxNLocator(6, steps=[1, 2, 5, 10], integer=True))
    ax.yaxis.grid(True)

    handles = [
        Line2D([], [], color=style.INK, lw=3, label="Average"),
        Line2D([], [], ls="", marker="o", ms=9, mfc=style.INK_2, mec=style.INK_2,
               mew=2, label="One summer"),
    ]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncols=2, fontsize=15, columnspacing=2, borderaxespad=0.4)

    style.headline(fig, title, subtitle, source=SOURCE)
    style.save(fig, "enso-eras")
