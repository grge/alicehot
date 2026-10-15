import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize

from . import data, style

CMAP = LinearSegmentedColormap.from_list(
    "stripes",
    ["#08306b", "#2171b5", "#6baed6", "#c6dbef", "#f7f7f7",
     "#fcbba1", "#fb6a4a", "#cb181d", "#67000d"],
)


def annual_anomaly(df):
    tmax = df.tmax[df.tmax.first_valid_index():]
    counts = tmax.groupby(tmax.index.year).count()
    annual = tmax.groupby(tmax.index.year).mean()[counts >= 330]
    annual = annual[annual.index >= data.FIRST_SEASON]
    return annual - annual.loc[1961:1990].mean()


def plot(df, title, subtitle):
    anom = annual_anomaly(df)
    years = anom.index.values
    limit = np.abs(anom).max()

    fig = style.slide()
    ax = fig.add_axes([0, 0.16, 1, 0.6])
    ax.bar(years, np.ones(len(years)), width=1.0,
           color=CMAP(Normalize(-limit, limit)(anom.values)))
    ax.set_xlim(years.min() - 0.5, years.max() + 0.5)
    ax.set_ylim(0, 1)
    ax.axis("off")

    for year, ha in ((years.min(), "left"), (years.max(), "right")):
        x = 0.012 if ha == "left" else 0.988
        fig.text(x, 0.12, str(year), ha=ha, va="top", fontsize=17,
                 color=style.INK_2)

    style.headline(fig, title, subtitle)
    style.save(fig, "stripes")
