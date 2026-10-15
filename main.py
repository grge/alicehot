import sys

from alicehot import data, enso, hotdays, spiral, stripes, style

style.apply()
df = data.load_tmax(first_season=1910)

hotdays.plot(
    df, 35, "days-35",
    title="Days at or above 35 °C, Alice Springs",
    subtitle="Days per year (July–June), with decade averages",
)
hotdays.plot(
    df, 40, "days-40",
    title="Days at or above 40 °C, Alice Springs",
    subtitle="Days per year (July–June), with decade averages",
)

spiral_text = dict(
    title="Maximum temperature anomaly, Alice Springs",
    subtitle="12-month mean daily maximum relative to 1961–1990",
    note="Each point is the mean daily maximum over the\n"
         "previous 12 months. One loop per year.",
)
spiral.plot(df, **spiral_text)

enso.plot_bars(
    df, 40,
    title="Days at or above 40 °C by ENSO phase, Alice Springs",
    subtitle="Days per year (July–June), coloured by ENSO phase in December–February",
)
enso.plot_eras(
    df, 40, 1988,
    title="Days at or above 40 °C by ENSO phase, before and since 1988",
    subtitle="Days per year (July–June), by ENSO phase in December–February",
)

stripes.plot(
    df,
    title="Annual maximum temperature anomaly, Alice Springs",
    subtitle="Annual mean daily maximum relative to 1961–1990",
)

if "--animate" in sys.argv:
    spiral.animate(df, **spiral_text)
