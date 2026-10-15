import numpy as np
from matplotlib.patheffects import withStroke
from matplotlib.ticker import MaxNLocator

from . import data, style

DECADE_INK = "#a3271b"


def plot(df, threshold, name, title, subtitle):
    counts = data.days_at_or_above(df, threshold)
    seasons = counts.index.values

    fig = style.slide()
    ax = fig.add_axes([0.05, 0.13, 0.9, 0.66])
    ax.bar(seasons, counts.values, width=0.72, color=style.HEAT_LIGHT, zorder=2)

    decades = counts.groupby(seasons // 10 * 10)
    for decade, group in decades:
        x0, x1 = group.index.min() - 0.45, group.index.max() + 0.45
        mean = group.mean()
        ax.plot([x0, x1], [mean, mean], color=DECADE_INK, lw=3.5,
                solid_capstyle="butt", zorder=3)
        ax.text((x0 + x1) / 2, mean + counts.max() * 0.025, f"{mean:.0f}",
                ha="center", va="bottom", fontsize=17, fontweight="semibold",
                color=DECADE_INK, zorder=4,
                path_effects=[withStroke(linewidth=5, foreground=style.SURFACE)])

    record = counts.idxmax()
    ax.annotate(
        f"{data.season_label(record)}\n{counts[record]} days",
        xy=(record, counts[record]), xytext=(record - 5.5, counts[record] * 1.03),
        ha="right", va="center", fontsize=14, color=style.INK_2,
        arrowprops=dict(arrowstyle="-", color=style.MUTED, lw=1,
                        shrinkA=4, shrinkB=4),
    )

    starts = np.arange(seasons.min() // 10 * 10, seasons.max() + 10, 10)
    centres = [g.index.values.mean() for _, g in decades]
    ax.set_xticks(starts - 0.5, minor=False, labels=[])
    ax.set_xticks(centres, minor=True,
                  labels=[f"{d}s" for d, _ in decades])
    ax.tick_params(axis="x", which="minor", length=0, pad=8)
    ax.set_xlim(seasons.min() - 1, seasons.max() + 1)
    ax.set_ylim(0, counts.max() * 1.12)
    ax.yaxis.set_major_locator(MaxNLocator(6, steps=[1, 2, 5, 10], integer=True))

    style.headline(fig, title, subtitle)
    style.save(fig, name)
