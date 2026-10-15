import ftplib
import io
import tarfile
import urllib.request
import zipfile
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
BOM_FTP = "ftp.bom.gov.au"
ACORN_URL = ("ftp://ftp.bom.gov.au/anon/home/ncc/www/change/ACORN_SAT_daily/"
             "acorn_sat_v2.6.0_daily_tmax.tar.gz")
ACORN_FILE = DATA / "acorn_sat_v2.6.0_daily_tmax.tar.gz"
ACORN_STATION = "tmax.015590.daily.csv"
ACORN_RAW_URL = ("ftp://ftp.bom.gov.au/anon/home/ncc/www/change/ACORN_SAT_daily/"
                 "v2.5-raw-data-and-supporting-information.zip")
ACORN_RAW_FILE = DATA / "v2.5-raw-data-and-supporting-information.zip"
RECENT_PATH = "/anon/gen/clim_data/IDCKWCDEA0/tables/nt/alice_springs_airport"
RECENT_DIR = DATA / "alice_springs_airport"
RECENT_STATION = "ALICE SPRINGS AIRPORT"
RONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
RONI_FILE = DATA / "RONI.ascii.txt"


def _download(url, path):
    if not path.exists():
        DATA.mkdir(exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


def load_acorn():
    with tarfile.open(_download(ACORN_URL, ACORN_FILE)) as t:
        with t.extractfile(ACORN_STATION) as f:
            df = pd.read_csv(f, skiprows=[1], index_col=0, parse_dates=True)
    return df.iloc[:, 0].rename("tmax")


def _load_unadjusted(station):
    with zipfile.ZipFile(_download(ACORN_RAW_URL, ACORN_RAW_FILE)) as z:
        name = next(n for n in z.namelist() if n.endswith(f"raw-data/hqnew{station}"))
        with z.open(name) as f:
            df = pd.read_fwf(f, widths=[6, 8, 6, 5], header=None,
                             names=["station", "date", "tmax", "tmin"],
                             dtype={"date": str})
    tmax = pd.Series(df.tmax.values / 10,
                     index=pd.to_datetime(df.date, format="%Y%m%d"), name="tmax")
    return tmax.where(tmax > -99)


def _fetch_recent():
    RECENT_DIR.mkdir(parents=True, exist_ok=True)
    with ftplib.FTP(BOM_FTP) as ftp:
        ftp.login()
        ftp.cwd(RECENT_PATH)
        names = sorted(n for n in ftp.nlst() if n.endswith(".csv"))
        for name in names:
            target = RECENT_DIR / name
            if name in names[-2:] or not target.exists():
                with open(target, "wb") as f:
                    ftp.retrbinary(f"RETR {name}", f.write)


@cache
def load_recent():
    _fetch_recent()
    months = []
    for path in sorted(RECENT_DIR.glob("*.csv")):
        rows = [line for line in path.read_text(encoding="latin-1").splitlines()
                if line.startswith(RECENT_STATION + ",")]
        df = pd.read_csv(io.StringIO("\n".join(rows)), header=None)
        months.append(pd.Series(pd.to_numeric(df[5], errors="coerce").values,
                                index=pd.to_datetime(df[1], format="%d/%m/%Y")))
    return pd.concat(months).rename("tmax")


def _append(series, recent):
    return pd.concat([series, recent[recent.index > series.index[-1]]])


def load_post_office():
    return _load_unadjusted("015540")


def load_airport():
    return _append(_load_unadjusted("015590"), load_recent())


def load_tmax(first_season):
    tmax = _append(load_acorn(), load_recent())
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
