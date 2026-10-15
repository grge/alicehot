import tarfile
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
STATION_ZIP = DATA / "IDCJAC0010_015590_1800.zip"
ACORN_URL = ("ftp://ftp.bom.gov.au/anon/home/ncc/www/change/ACORN_SAT_daily/"
             "acorn_sat_v2.6.0_daily_tmax.tar.gz")
ACORN_FILE = DATA / "acorn_sat_v2.6.0_daily_tmax.tar.gz"
ACORN_STATION = "tmax.015590.daily.csv"
RONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
RONI_FILE = DATA / "RONI.ascii.txt"



def _download(url, path):
    if not path.exists():
        DATA.mkdir(exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


def load_station():
    with zipfile.ZipFile(STATION_ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith("_Data.csv"))
        with z.open(name) as f:
            df = pd.read_csv(f)
    dates = pd.to_datetime(
        df[["Year", "Month", "Day"]].set_axis(["year", "month", "day"], axis=1))
    return pd.Series(df["Maximum temperature (Degree C)"].values, index=dates,
                     name="tmax")


def load_acorn():
    with tarfile.open(_download(ACORN_URL, ACORN_FILE)) as t:
        with t.extractfile(ACORN_STATION) as f:
            df = pd.read_csv(f, skiprows=[1], index_col=0, parse_dates=True)
    return df.iloc[:, 0].rename("tmax")


def load_tmax(first_season):
    acorn = load_acorn()
    station = load_station()
    tmax = pd.concat([acorn, station[station.index > acorn.index[-1]]])
    df = pd.DataFrame({"tmax": tmax, "season": tmax.index.year - (tmax.index.month < 7)})
    return df[df.season >= first_season]


def season_label(season):
    return f"{season}–{(season + 1) % 100:02d}"


def complete_seasons(df):
    last = df.index[-1]
    final = last.year - 1 if (last.month, last.day) >= (6, 30) else last.year - 2
    return df[df.season <= final]


def days_at_or_above(df, threshold):
    df = complete_seasons(df)
    return (df.tmax >= threshold).groupby(df.season).sum()


def annual_means(tmax, min_days=330):
    counts = tmax.groupby(tmax.index.year).count()
    return tmax.groupby(tmax.index.year).mean()[counts >= min_days]


def load_roni():
    roni = pd.read_csv(_download(RONI_URL, RONI_FILE), sep=r"\s+")
    return roni.rename(columns={"SEAS": "season", "YR": "year", "ANOM": "anom"})


def _runs(mask, length):
    out = np.zeros(len(mask), dtype=bool)
    start = None
    for i, m in enumerate(np.append(mask, False)):
        if m and start is None:
            start = i
        elif not m and start is not None:
            if i - start >= length:
                out[start:i] = True
            start = None
    return out


def summer_enso():
    roni = load_roni()
    el_nino = _runs(roni.anom.values >= 0.5, 5)
    la_nina = _runs(roni.anom.values <= -0.5, 5)
    roni["phase"] = np.select([el_nino, la_nina], ["El Niño", "La Niña"], "Neutral")
    djf = roni[roni.season == "DJF"]
    return pd.DataFrame(
        {"roni": djf.anom.values, "phase": djf.phase.values},
        index=pd.Index(djf.year.values - 1, name="season"),
    )
