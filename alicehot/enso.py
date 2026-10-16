import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from . import data, style

PHASES = ["El Niño", "Neutral", "La Niña"]
COLOURS = {"El Niño": style.HEAT, "Neutral": style.NEUTRAL, "La Niña": style.COOL}
SOURCE = style.SOURCE + "; ENSO: NOAA Relative Oceanic Niño Index (Dec–Feb)"
SUMMER = [11, 12, 1, 2, 3]


def summers(df, threshold):
    counts = data.days_at_or_above(df, threshold).rename("days")
    return pd.concat([counts, data.summer_enso()], axis=1, join="inner")


def summer_tmax(df):
    df = data.complete_seasons(df)
    summer = df[df.index.month.isin(SUMMER)].groupby("season").tmax
    return summer.mean().where(summer.count() >= 140)


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


def _tint(colour, amount):
    return tuple(np.array(to_rgb(style.SURFACE)) * (1 - amount)
                 + np.array(to_rgb(colour)) * amount)


def plot_eras(df, threshold, splits, title, subtitle):
    s = summers(df, threshold)
    s["era"] = np.searchsorted(splits, s.index, side="right")
    starts = [s.index.min(), *splits]
    labels = [f"{a}–{b - 1}" for a, b in zip(starts, splits)] + [f"{splits[-1]}–now"]
    n = len(labels)
    step, group = 1.2, len(labels) * 1.2 + 0.9

    fig = style.slide()
    ax = fig.add_axes([0.05, 0.2, 0.92, 0.53])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)

    xticks, xlabels = [], []
    for g, phase in enumerate(PHASES):
        for era, label in enumerate(labels):
            x = g * group + era * step
            sub = s[(s.phase == phase) & (s.era == era)].days
            colour = COLOURS[phase]
            ax.scatter(x + _swarm(sub, 0.1), sub, s=70, zorder=3,
                       color=_tint(colour, era / (n - 1)), edgecolor=colour,
                       linewidth=2)
            mean = sub.mean()
            ax.plot([x - 0.35, x + 0.35], [mean, mean], color=style.INK, lw=3,
                    solid_capstyle="butt", zorder=4)
            ax.text(x + 0.4, mean, f"{mean:.0f}", va="center", ha="left",
                    fontsize=17, fontweight="semibold", zorder=4)
            xticks.append(x)
            xlabels.append(label)
        ax.text(g * group + (n - 1) * step / 2, -0.12, phase,
                transform=ax.get_xaxis_transform(), ha="center", va="top",
                fontsize=19, fontweight="semibold")

    ax.set_xticks(xticks, xlabels, fontsize=13)
    ax.set_xlim(-0.7, 2 * group + (n - 1) * step + 0.9)
    ax.set_ylim(-1.5, s.days.max() * 1.05)
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


def plot_scatter(df, title, subtitle):
    s = pd.concat([summer_tmax(df).rename("tmax"), data.summer_enso()],
                  axis=1, join="inner").dropna()
    t = s.index.values
    s["anom"] = s.tmax - np.polyval(np.polyfit(t, s.tmax, 2), t)
    slope, intercept = np.polyfit(s.roni, s.anom, 1)

    fig = style.slide()
    ax = fig.add_axes([0.07, 0.19, 0.86, 0.54])
    ax.grid(True, axis="both")
    ax.axhline(0, color=style.BASELINE, lw=1.5, zorder=1)
    ax.scatter(s.roni, s.anom, s=80, zorder=3, color=s.phase.map(COLOURS),
               edgecolor=style.SURFACE, linewidth=1.5)

    xs = np.array([s.roni.min() - 0.1, s.roni.max() + 0.1])
    ax.plot(xs, intercept + slope * xs, color=style.INK, lw=2.5, zorder=4)
    ax.text(xs[1] + 0.1, intercept + slope * xs[1],
            f"+{slope:.1f} °C per\nunit of index", ha="left", va="center",
            fontsize=15, fontweight="semibold", zorder=4)

    labelled = pd.concat([s.nsmallest(2, "anom"), s.nlargest(2, "anom")])
    for season, row in labelled.iterrows():
        right = row.roni < 1.5
        ax.annotate(data.season_label(season), xy=(row.roni, row.anom),
                    xytext=(12 if right else -12, 0), textcoords="offset points",
                    ha="left" if right else "right", va="center",
                    fontsize=14, color=style.INK_2)

    ax.set_xlim(xs[0] - 0.15, xs[1] + 0.95)
    ax.xaxis.set_major_locator(MaxNLocator(8, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_locator(MaxNLocator(6, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:+.0f} °C".replace("-", "−") if v else "0")
    ax.set_xlabel("← La Niña      Relative Oceanic Niño Index, Dec–Feb      El Niño →",
                  fontsize=15, labelpad=8)
    ax.tick_params(axis="x", length=0)

    handles = [Line2D([], [], ls="", marker="o", ms=10, mfc=COLOURS[p], mec=COLOURS[p],
                      label=p) for p in PHASES]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncols=3, fontsize=16, columnspacing=1.5, handletextpad=0.3,
              borderaxespad=0.4)

    style.headline(fig, title, subtitle, source=SOURCE)
    style.save(fig, "enso-scatter")
