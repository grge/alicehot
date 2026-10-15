import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
BOM_ZIP = DATA / "IDCJAC0010_015590_1800.zip"
RONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
RONI_FILE = DATA / "RONI.ascii.txt"

FIRST_SEASON = 1942


def load_tmax():
    with zipfile.ZipFile(BOM_ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith("_Data.csv"))
        with z.open(name) as f:
            df = pd.read_csv(f)
    df = df.rename(
        columns={
            "Year": "year",
            "Month": "month",
            "Day": "day",
            "Maximum temperature (Degree C)": "tmax",
        }
    )
    df.index = pd.to_datetime(df[["year", "month", "day"]])
    df["season"] = df.year - (df.month < 7)
    return df[["year", "month", "day", "season", "tmax"]]


def season_label(season):
    return f"{season}–{(season + 1) % 100:02d}"


def complete_seasons(df):
    last = df.index[-1]
    final = last.year - 1 if (last.month, last.day) >= (6, 30) else last.year - 2
    return df[(df.season >= FIRST_SEASON) & (df.season <= final)]


def days_at_or_above(df, threshold):
    df = complete_seasons(df)
    return (df.tmax >= threshold).groupby(df.season).sum()


def load_roni():
    if not RONI_FILE.exists():
        DATA.mkdir(exist_ok=True)
        urllib.request.urlretrieve(RONI_URL, RONI_FILE)
    roni = pd.read_csv(RONI_FILE, sep=r"\s+")
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
