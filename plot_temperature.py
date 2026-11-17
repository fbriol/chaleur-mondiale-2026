#!/usr/bin/env python3
"""Température mondiale annuelle : 2026 face au record de 2024.

Le script télécharge le fichier officiel publié par le Copernicus Climate
Change Service (C3S / ECMWF, réanalyse ERA5) avec son bulletin d'octobre 2026,
puis trace la figure. Aucune température n'est saisie à la main.

Usage : python plot_temperature.py
"""

from __future__ import annotations

import io
import pathlib
import sys
import urllib.request

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

#: Fichier de données de la figure « anomalies annuelles + prévision 2026 »
#: du bulletin C3S d'octobre 2026 (publié le 5 novembre 2026).
DATA_URL = (
    "https://climate.copernicus.eu/sites/default/files/2026-11/"
    "C3S_Bulletin_PR_202610_timeseries_annual_global_surface_temperature_"
    "anomalies_ref1850-1900_prediction_DATA.csv"
)
BULLETIN_URL = (
    "https://climate.copernicus.eu/"
    "copernicus-warmest-october-record-2026-virtually-certain-exceed-15degc"
)
HERE = pathlib.Path(__file__).parent
CSV_PATH = HERE / "data" / "c3s_annual_anomalies_ref1850-1900.csv"
PNG_PATH = HERE / "temperature-mondiale-2026.png"


def download() -> str:
    """Télécharge le CSV officiel et en garde une copie dans data/."""
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
    # DATA_URL est une constante https : pas de schéma file: ou arbitraire possible.
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        raw = response.read()
    CSV_PATH.parent.mkdir(exist_ok=True)
    CSV_PATH.write_bytes(raw)
    return raw.decode("utf-8-sig")


def parse(text: str) -> tuple[pd.Series, float | None, float | None]:
    """Retourne (anomalies annuelles, borne basse 2026, borne haute 2026)."""
    frame = pd.read_csv(io.StringIO(text), comment="#", skip_blank_lines=True)
    frame.columns = [str(c).strip().lower() for c in frame.columns]
    print("Colonnes du fichier C3S :", list(frame.columns))
    print(frame.tail(5).to_string())

    year_col = frame.columns[0]
    frame["year"] = frame[year_col].astype(str).str[:4].astype(int)
    numeric = [
        c
        for c in frame.columns
        if c not in (year_col, "year") and pd.api.types.is_numeric_dtype(frame[c])
    ]
    if not numeric:
        sys.exit("Format inattendu : aucune colonne numérique.")

    def find(*keys: str) -> str | None:
        return next((c for c in numeric if any(k in c for k in keys)), None)

    low_col = find("lower", "min", "low")
    high_col = find("upper", "max", "high")
    main_col = next(c for c in numeric if c not in (low_col, high_col))
    series = frame.set_index("year")[main_col]

    last = frame.iloc[-1]
    low = float(last[low_col]) if low_col and pd.notna(last[low_col]) else None
    high = float(last[high_col]) if high_col and pd.notna(last[high_col]) else None
    if pd.isna(series.iloc[-1]):
        if low is None or high is None:
            sys.exit("Format inattendu : pas de valeur ni de fourchette pour 2026.")
        series.iloc[-1] = (low + high) / 2
    return series, low, high


def plot(series: pd.Series, low: float | None, high: float | None) -> None:
    """Trace les quatre dernières années, la dernière étant une estimation."""
    ink, muted, grid, hue = "#1f2328", "#6b7280", "#e5e7eb", "#c9502e"
    record_year = int(series.iloc[:-1].idxmax())
    recent = series.iloc[-4:]
    last_year = int(recent.index[-1])

    def fr(x: float) -> str:
        return f"+{x:.2f}".replace(".", ",")

    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    for i, (year, value) in enumerate(recent.items()):
        estimate = year == last_year
        ax.bar(
            i,
            value,
            width=0.56,
            zorder=3,
            linewidth=2,
            edgecolor=hue,
            color="white" if estimate else hue,
            hatch="///" if estimate else None,
        )
        top, label = value, f"{fr(value)} °C"
        if year == record_year:
            label += "\nrecord actuel"
        if estimate and low is not None and high is not None:
            ax.plot(
                [i, i],
                [low, high],
                color=ink,
                lw=2.5,
                zorder=5,
                solid_capstyle="butt",
            )
            for bound in (low, high):
                ax.plot(
                    [i - 0.1, i + 0.1],
                    [bound, bound],
                    color=ink,
                    lw=2.5,
                    zorder=5,
                )
            top, label = high, f"{fr(low)} à {fr(high)} °C\nestimation"
        ax.text(
            i,
            top + 0.03,
            label,
            ha="center",
            va="bottom",
            fontsize=13,
            color=ink,
            fontweight="bold",
            linespacing=1.3,
        )

    ax.axhline(1.5, color=ink, lw=1.5, ls=(0, (5, 4)), zorder=4)
    ax.plot([-0.45, -0.2], [1.93, 1.93], color=ink, lw=1.5, ls=(0, (5, 4)))
    ax.text(
        -0.14,
        1.93,
        "Seuil de l'Accord de Paris : +1,5 °C",
        color=ink,
        fontsize=12,
        va="center",
    )

    ax.set_ylim(0, 2.0)
    ax.set_xlim(-0.55, 3.55)
    ax.set_xticks(range(4))
    ax.set_xticklabels(
        [str(y) for y in recent.index[:-1]] + [f"{last_year}*"],
        fontsize=15,
        color=ink,
    )
    ax.set_yticks([0, 0.5, 1.0, 1.5])
    ax.set_yticklabels(["0", "+0,5", "+1,0", "+1,5"], fontsize=12, color=muted)
    ax.yaxis.grid(True, color=grid, lw=1, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(grid)

    fig.suptitle(
        f"{last_year} talonne le record de chaleur de {record_year}",
        x=0.06,
        y=0.965,
        ha="left",
        fontsize=21,
        fontweight="bold",
        color=ink,
    )
    fig.text(
        0.06,
        0.895,
        "Température moyenne mondiale, écart par rapport à l'ère préindustrielle (1850-1900)",
        fontsize=12,
        color=muted,
    )
    fig.text(
        0.06,
        0.03,
        f"* Estimation Copernicus (C3S) à fin octobre {last_year} "
        f": environ 20 % de chances d'égaler ou de battre {record_year}.\n"
        "Source : Copernicus Climate Change Service / ECMWF, données ERA5.\n"
        "Code et données : github.com/fbriol/chaleur-mondiale-2026",
        fontsize=10,
        color=muted,
        linespacing=1.5,
    )
    fig.subplots_adjust(left=0.1, right=0.96, top=0.86, bottom=0.16)
    fig.savefig(PNG_PATH, facecolor="white")
    print("Figure écrite :", PNG_PATH)


if __name__ == "__main__":
    plot(*parse(download()))
