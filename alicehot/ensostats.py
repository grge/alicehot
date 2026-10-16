"""Checks on how much ENSO phase matters for summer heat in Alice Springs.

Run with: uv run python -m alicehot.ensostats
"""
import numpy as np
import pandas as pd

from . import data, enso
from .enso import PHASES

SPLITS = [1975, 2001]
MONTHS = {9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec", 1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr"}
METRICS = {
    "days40": ("Days ≥ 40 °C", "days", 1),
    "days35": ("Days ≥ 35 °C", "days", 1),
    "tmax": ("Nov–Mar mean max", "°C", 2),
}
N = 5000
RNG = np.random.default_rng(0)


def seasons(df, splits):
    df = data.complete_seasons(df)
    roni = data.load_roni()
    son = roni[roni.season == "SON"].set_index("year").anom
    s = pd.DataFrame({
        "days40": data.days_at_or_above(df, 40),
        "days35": data.days_at_or_above(df, 35),
        "tmax": enso.summer_tmax(df),
    }).join(data.summer_enso(), how="inner").astype({"days40": float, "days35": float})
    s["roni_son"] = son.reindex(s.index).values
    s["era"] = np.searchsorted(splits, s.index, side="right")
    return s


def monthly(df, index):
    df = data.complete_seasons(df)
    g = df.groupby([df.season, df.index.month]).tmax
    return g.mean().where(g.count() >= 25).unstack().reindex(index)


def _trend(index):
    t = (np.asarray(index) - 1985) / 30
    return np.column_stack([np.ones(len(t)), t, t ** 2])


def _fit(X, y):
    return np.linalg.lstsq(X, y, rcond=None)[0]


def effect(y, base, enso, contrast):
    """Effect of the ENSO columns on y after controlling for the base columns.

    Returns the estimate, a 95% bootstrap interval, a Freedman–Lane
    permutation p-value, and the smallest effect the sample could reliably
    detect (80% power, two-sided 5% test).
    """
    ok = ~np.isnan(y) & ~np.isnan(enso).any(axis=1)
    y, base, enso = y[ok], base[ok], enso[ok]
    X = np.column_stack([base, enso])
    k = base.shape[1]

    def est(X, y):
        return _fit(X, y)[k:] @ contrast

    obs = est(X, y)
    boot = np.array([est(X[i], y[i]) for i in RNG.integers(0, len(y), (N, len(y)))])
    reduced = base @ _fit(base, y)
    resid = y - reduced
    perm = np.array([est(X, reduced + RNG.permutation(resid)) for _ in range(N)])
    p = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (N + 1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return obs, lo, hi, p, 2.8 * boot.std()


def residuals(y, base):
    ok = ~np.isnan(y)
    out = np.full(len(y), np.nan)
    out[ok] = y[ok] - base[ok] @ _fit(base[ok], y[ok])
    return out


def partial_r(y, x, base):
    ry, rx = residuals(y, base), residuals(x, base)
    ok = ~np.isnan(ry) & ~np.isnan(rx)
    return np.corrcoef(ry[ok], rx[ok])[0, 1]


def _row(label, result, unit, digits):
    est, lo, hi, p, mde = result
    f = f"+.{digits}f"
    return (f"  {label:<24}{est:{f}} {unit}  [{lo:{f}}, {hi:{f}}]  "
            f"p = {p:.2f}  detectable ≈ {mde:.{digits}f}")


def _cells(series, labels):
    table = series.unstack().reindex(columns=PHASES)
    table.index = [labels[e] for e in table.index]
    return table.to_string(na_rep="–")


def report(df, splits):
    s = seasons(df, splits)
    starts = [s.index.min(), *splits]
    labels = [f"{a}–{b - 1}" for a, b in zip(starts, splits)] + [f"{splits[-1]}–now"]
    trend = _trend(s.index)
    phase = np.column_stack([s.phase == "El Niño", s.phase == "La Niña"]).astype(float)
    print(f"{len(s)} complete summers, {data.season_label(s.index.min())} to "
          f"{data.season_label(s.index.max())}. Bootstrap and permutation: {N} draws.")

    print("\n1. Summers in each cell of the eras chart")
    cells = s.assign(year=s.index).groupby(["era", "phase"]).year
    print(_cells(cells.count(), labels))
    print("\n   Average year of the summers in each cell (if a phase sits late in a")
    print("   period, warming alone raises its average)")
    print(_cells(cells.mean().round().astype(int), labels))

    print("\n2. El Niño minus La Niña, days ≥ 40 °C, within each period as charted")
    print("   (with so few summers per cell these intervals run narrow: in tests on")
    print("   data with no ENSO effect, up to 1 in 10 excluded zero rather than 1 in 20)")
    for era, label in enumerate(labels):
        sub = (s.era == era).values
        result = effect(s.days40.values[sub], np.ones((sub.sum(), 1)), phase[sub],
                        np.array([1, -1]))
        print(_row(label, result, "days", 1))

    print("\n3. Departure from the warming trend, by phase (smooth quadratic trend)")
    table = pd.DataFrame({
        METRICS[key][0]: pd.Series(residuals(s[key].values, trend), index=s.index)
        .groupby(s.phase).mean().reindex(PHASES).round(METRICS[key][2])
        for key in METRICS
    })
    print(table.to_string())

    print("\n4. El Niño minus La Niña, all summers pooled, three ways of handling warming")
    controls = {
        "no control": np.ones((len(s), 1)),
        "periods (as chart)": np.column_stack([s.era == e for e in range(len(labels))])
        .astype(float),
        "smooth trend": trend,
    }
    for key, (name, unit, digits) in METRICS.items():
        print(f"  {name}")
        for cname, base in controls.items():
            print(_row(cname, effect(s[key].values, base, phase, np.array([1, -1])),
                       unit, digits))

    print("\n5. Continuous index, after removing trend: change per +1.0 RONI")
    print("   (r is the partial correlation; Dec–Feb RONI as charted, and the")
    print("   preceding Sep–Nov RONI)")
    for key, (name, unit, digits) in METRICS.items():
        print(f"  {name}")
        for col, label in [("roni", "Dec–Feb RONI"), ("roni_son", "Sep–Nov RONI")]:
            y, x = s[key].values, s[[col]].values
            r = partial_r(y, x[:, 0], trend)
            print(_row(label, effect(y, trend, x, np.array([1])), unit, digits)
                  + f"  r = {r:+.2f}")

    print("\n6. Month by month: mean daily max vs Dec–Feb RONI, after removing trend")
    m = monthly(df, s.index)
    for month, name in MONTHS.items():
        y, x = m[month].values, s[["roni"]].values
        r = partial_r(y, x[:, 0], trend)
        print(_row(name, effect(y, trend, x, np.array([1])), "°C", 2) + f"  r = {r:+.2f}")

    print("\n7. Strongest events: departure from the warming trend")
    strong = s.assign(
        **{f"{key} vs trend": residuals(s[key].values, trend).round(METRICS[key][2])
           for key in METRICS}
    )
    strong = pd.concat([
        strong[strong.phase == "El Niño"].nlargest(6, "roni"),
        strong[strong.phase == "La Niña"].nsmallest(6, "roni"),
    ])
    strong.index = [data.season_label(i) for i in strong.index]
    strong["days40"] = strong.days40.astype(int)
    cols = ["phase", "roni", "days40", "days40 vs trend", "days35 vs trend", "tmax vs trend"]
    print(strong[cols].to_string())


if __name__ == "__main__":
    report(data.load_tmax(first_season=1942), SPLITS)
