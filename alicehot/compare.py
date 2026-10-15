from matplotlib.ticker import FuncFormatter

from . import data, style

SCREEN_CHANGE = 1998 + 8 / 12
SOURCE = ("Data: Bureau of Meteorology, ACORN-SAT v2.6 and Alice Springs Airport "
          "(015590) observations")


def plot(acorn, station, title, subtitle):
    a = data.annual_means(acorn)
    s = data.annual_means(station)

    fig = style.slide()
    ax = fig.add_axes([0.08, 0.13, 0.87, 0.6])
    ax.plot(a.index, a.values, color=style.HEAT, lw=3.5, zorder=2,
            solid_capstyle="round", label="ACORN-SAT (homogenised)")
    ax.plot(s.index, s.values, color=style.INK, lw=1.5, zorder=3,
            solid_capstyle="round", label="Station observations (unadjusted)")

    ax.axvline(SCREEN_CHANGE, color=style.BASELINE, lw=1, zorder=1)
    ax.text(SCREEN_CHANGE + 0.6, 0.98, "Screen change\nAugust 1998",
            transform=ax.get_xaxis_transform(), va="top", fontsize=13,
            color=style.INK_2)

    ax.set_xlim(a.index.min() - 1, max(a.index.max(), s.index.max()) + 1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} °C"))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2,
              handlelength=1.6, columnspacing=2, fontsize=16, borderaxespad=0.4)

    style.headline(fig, title, subtitle, source=SOURCE)
    style.save(fig, "acorn-vs-station")
