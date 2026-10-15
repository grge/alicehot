import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation
from matplotlib.cm import ScalarMappable
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patheffects import withStroke

from . import data, style

CMAP = LinearSegmentedColormap.from_list(
    "heat", ["#f3e3c3", "#f0a050", "#d9482b", "#7f1414"])
BASELINE_YEARS = ("1961", "1990")
OFFSET = 3.0
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def rolling_anomaly(df):
    tmax = df.tmax[df.tmax.first_valid_index():]
    counts = tmax.resample("MS").count()
    monthly = tmax.resample("MS").mean()
    monthly = monthly.where(counts >= counts.index.days_in_month * 0.8)
    monthly = monthly[monthly.index.year >= data.FIRST_SEASON]
    base = monthly[slice(*BASELINE_YEARS)]
    clim = base.groupby(base.index.month).mean()
    anomaly = monthly - clim.reindex(monthly.index.month).values
    return anomaly.rolling(12).mean().dropna()


class Spiral:
    def __init__(self, df, **fig_kwargs):
        self.roll = rolling_anomaly(df)
        self.theta = np.unwrap(2 * np.pi * (self.roll.index.month - 1) / 12)
        self.r = self.roll.values + OFFSET
        years = self.roll.index.year + (self.roll.index.month - 1) / 12
        norm = Normalize(years.min(), years.max())
        points = np.column_stack([self.theta, self.r]).reshape(-1, 1, 2)
        self.segments = np.concatenate([points[:-1], points[1:]], axis=1)
        self.colours = CMAP(norm(years[:-1]))

        self.fig = fig = style.slide(**fig_kwargs)
        self.ax = ax = fig.add_axes([0.5, 0.09, 0.46, 0.7], projection="polar")
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)

        self.lines = LineCollection([], linewidths=1.5, capstyle="round",
                                    joinstyle="round")
        ax.add_collection(self.lines)

        rmax = np.ceil(self.r.max() + 0.3)
        ax.set_ylim(0, rmax)
        ax.set_xticks(np.linspace(0, 2 * np.pi, 12, endpoint=False), MONTHS)
        ax.tick_params(axis="x", pad=6, labelsize=14)
        rings = np.arange(-2, rmax - OFFSET + 0.01, 1)
        ax.set_yticks(rings + OFFSET, [])
        ax.yaxis.grid(True, color=style.GRID, lw=1)
        ax.xaxis.grid(True, color=style.GRID, lw=1)
        ax.spines["polar"].set_visible(False)
        ax.plot(np.linspace(0, 2 * np.pi, 200), np.full(200, OFFSET),
                color=style.INK_2, lw=1.2, zorder=1)
        for ring in rings:
            txt = "average" if ring == 0 else f"{ring:+.0f} °C"
            ax.text(0, ring + OFFSET, txt, fontsize=12, ha="center", va="center",
                    color=style.INK if ring == 0 else style.INK_2, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", fc=style.SURFACE,
                              ec="none", alpha=0.85))

        (self.head,) = ax.plot([], [], "o", ms=9, color=CMAP(1.0),
                               mec=style.SURFACE, mew=2, zorder=6)
        self.label = ax.annotate(
            "", xy=(0, 0), xytext=(10, -4), textcoords="offset points",
            fontsize=13, fontweight="semibold", va="top", zorder=6,
            path_effects=[withStroke(linewidth=4, foreground=style.SURFACE)])

        cax = fig.add_axes([0.05, 0.4, 0.34, 0.03])
        cb = fig.colorbar(ScalarMappable(norm, CMAP), cax=cax,
                          orientation="horizontal")
        cb.outline.set_visible(False)
        cb.set_ticks([int(years.min()), 1960, 1980, 2000, int(years.max())])
        cax.tick_params(length=0, labelsize=14, pad=6)

        fig.text(0.05, 0.66,
                 "Each point is the average maximum temperature\n"
                 "over the previous 12 months, compared with the\n"
                 f"{BASELINE_YEARS[0]}–{BASELINE_YEARS[1]} average. "
                 "One loop is one year.",
                 fontsize=15, color=style.INK_2, va="top", linespacing=1.4)

        style.headline(fig, "Alice Springs is spiralling hotter",
                       "Average daily maximum temperature, 1942 to today")

    def draw(self, n):
        self.lines.set_segments(self.segments[:n - 1])
        self.lines.set_color(self.colours[:n - 1])
        i = n - 1
        self.head.set_data([self.theta[i]], [self.r[i]])
        self.head.set_color(self.colours[max(i - 1, 0)])
        self.label.xy = (self.theta[i], self.r[i])
        self.label.set_text(f"{self.roll.index[i]:%b %Y}")
        return self.lines, self.head, self.label


def plot(df):
    s = Spiral(df)
    s.draw(len(s.roll))
    style.save(s.fig, "spiral")


def animate(df, fps=30, months_per_frame=2, hold_seconds=4):
    s = Spiral(df)
    n = len(s.roll)
    frames = list(range(2, n, months_per_frame)) + [n] * (fps * hold_seconds)
    anim = FuncAnimation(s.fig, s.draw, frames=frames, blit=False)
    style.OUT.mkdir(exist_ok=True)
    writer = FFMpegWriter(fps=fps, codec="libx264",
                          extra_args=["-pix_fmt", "yuv420p", "-crf", "18"])
    anim.save(style.OUT / "spiral.mp4", writer=writer, dpi=144)
