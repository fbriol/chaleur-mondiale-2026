#!/usr/bin/env python3
"""Construit la page interactive publiée sur GitHub Pages (site/index.html).

La figure est produite avec Plotly. Le fichier HTML est autonome (seule la
bibliothèque plotly.js est chargée depuis son CDN) et peut être servi par
n'importe quel hébergement statique.

Dans le navigateur, le visiteur peut zoomer, survoler chaque année, masquer
une courbe en cliquant sur la légende, et saisir son année de naissance et
celles de ses enfants : les repères de sa famille s'ajoutent alors à la
courbe. Aucune date n'est envoyée ni enregistrée.

Passé : température moyenne annuelle de la France métropolitaine (indicateur
thermique de 30 stations, Météo-France).
  - 1900-2017 : série diffusée par le ministère de la Transition écologique
    (SDES, indicateur 1.3), en écart à la moyenne 1961-1990 (11,8 °C) ;
  - 2018-2025 : indicateur thermique national exporté de
    https://dataclimat.fr/temperature/itn
    (Infoclimat / Data For Good, mesures Météo-France) le 17 novembre 2026.
Référence : moyenne 1900-1930, début des mesures homogènes.

Futur : trajectoire de réchauffement de référence pour l'adaptation au
changement climatique (TRACC), fixée par l'État en janvier 2026.

Usage : python build_page.py
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs_version

HERE = pathlib.Path(__file__).parent
OFFICIAL_CSV = HERE / "data" / "temperature_france_1900-2017_meteo-france.csv"
ITN_CSV = HERE / "data" / "itn_france_annuel_dataclimat.csv"
TEMPLATE = HERE / "page" / "index.html"
OUT = HERE / "site" / "index.html"

INK, MUTED, GRID, HOT, COOL, ANNUAL = (
    "#1f2328",
    "#6b7280",
    "#e5e7eb",
    "#eb6834",
    "#2a78d6",
    "#9aa1ab",
)
X_RANGE = (1897, 2103)
Y_RANGE = (-1.3, 4.7)

NORMAL_1961_1990 = 11.8  # °C, référence de la série officielle
BASELINE = (1900, 1930)
THIS_YEAR = 2026  # année en cours, incomplète dans l'export : exclue

#: TRACC (France hexagonale et Corse), par rapport à l'ère préindustrielle.
TRACC = {2050: 2.7, 2100: 4.0}

#: Scénario aligné sur l'Accord de Paris (+1,5 °C dans le monde en 2100) :
#: environ +2 °C en France hexagonale (ministère, consultation TRACC).
PARIS_2100 = 2.0

WINDOW = 11  # moyenne glissante centrée, en années, comme dans la série officielle


def load() -> pd.Series:
    """Écart annuel à la moyenne 1900-1930, de 1900 à la dernière année complète."""
    official = pd.read_csv(OFFICIAL_CSV, comment="#").set_index("annee")["ecart_1961_1990"]
    itn = pd.read_csv(ITN_CSV)
    itn = pd.Series(
        itn.iloc[:, 1].to_numpy(dtype=float) - NORMAL_1961_1990,
        index=pd.to_datetime(itn.iloc[:, 0]).dt.year,
    )
    overlap = (itn - official).dropna()
    print(
        f"Recouvrement {overlap.index.min()}-{overlap.index.max()} : écart moyen "
        f"{overlap.mean():+.3f} °C, écart-type {overlap.std():.3f} °C"
    )
    recent = itn[(itn.index > official.index.max()) & (itn.index < THIS_YEAR)]
    series = pd.concat([official, recent])
    return series - series.loc[BASELINE[0] : BASELINE[1]].mean()


def fr(value: float, digits: int = 1) -> str:
    """Écart signé à la française, par exemple « +2,7 » pour 2.71."""
    return f"+{value:.{digits}f}".replace(".", ",")


def interp(years: np.ndarray, points: list[tuple[float, float]]) -> np.ndarray:
    """Valeurs, arrondies au centième, de la ligne brisée `points` aux années `years`."""
    xs, ys = zip(*points, strict=True)
    return np.round(np.interp(years, xs, ys), 2)


def figure(
    series: pd.Series,
    smooth: pd.Series,
    *,
    today_x: float,
    today: float,
    record_year: int,
    record: float,
) -> go.Figure:
    """La courbe sans les repères de la famille, ajoutés ensuite dans le navigateur."""
    future_years = np.arange(int(np.ceil(today_x)), 2101)
    tracc_points = [(today_x, today), *TRACC.items()]
    paris_points = [(today_x, today), (2100, PARIS_2100)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=series.round(2),
            name="Chaque année",
            mode="lines",
            line=dict(color=ANNUAL, width=1.2),
            hovertemplate="%{y:+.2f} °C<extra>Année mesurée</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=smooth.index,
            y=smooth.round(2),
            name=f"Moyenne sur {WINDOW} ans",
            mode="lines",
            line=dict(color=INK, width=3),
            hovertemplate=f"%{{y:+.2f}} °C<extra>Moyenne sur {WINDOW} ans</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[today_x, *future_years],
            y=[round(today, 2), *interp(future_years, tracc_points)],
            name="Trajectoire actuelle (TRACC)",
            mode="lines",
            line=dict(color=HOT, width=3),
            hovertemplate="%{y:+.1f} °C<extra>Trajectoire actuelle</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[today_x, *future_years],
            y=[round(today, 2), *interp(future_years, paris_points)],
            name="Accord de Paris tenu",
            mode="lines",
            line=dict(color=COOL, width=3),
            hovertemplate="%{y:+.1f} °C<extra>Accord de Paris tenu</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[*TRACC, 2100],
            y=[*TRACC.values(), PARIS_2100],
            mode="markers",
            showlegend=False,
            hoverinfo="skip",
            marker=dict(
                size=10, color=[HOT] * len(TRACC) + [COOL], line=dict(color="white", width=2)
            ),
        )
    )

    fig.add_hline(y=record, line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_annotation(
        x=X_RANGE[0] + 3,
        y=record,
        xanchor="left",
        yanchor="bottom",
        showarrow=False,
        text=f"{record_year} ({fr(record)} °C) : année la plus chaude mesurée",
        font=dict(size=12, color=MUTED),
    )

    fig.update_layout(
        separators=", ",
        template="plotly_white",
        font=dict(
            family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif", size=14, color=INK
        ),
        margin=dict(l=8, r=8, t=8, b=8),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=13),
        legend=dict(
            orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom", font=dict(size=13)
        ),
        dragmode="zoom",
        xaxis=dict(
            range=X_RANGE,
            tickformat="d",
            hoverformat="d",
            showgrid=False,
            tickvals=[1900, 1950, 2000, 2050, 2100],
            fixedrange=False,
            showspikes=True,
            spikemode="across",
            spikecolor=MUTED,
            spikethickness=1,
            spikedash="dot",
        ),
        yaxis=dict(
            range=Y_RANGE,
            gridcolor=GRID,
            zeroline=False,
            ticksuffix=" °C",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["0", "+1 °C", "+2 °C", "+3 °C", "+4 °C"],
            tickfont=dict(color=MUTED),
        ),
    )
    return fig


def main() -> None:
    """Construit la figure et écrit la page dans site/index.html."""
    series = load()
    smooth = series.rolling(WINDOW, center=True).mean().dropna()
    last = int(series.index[-1])
    today = float(series.iloc[-10:].mean())
    today_x = last - 4.5
    record_year, record = int(series.idxmax()), float(series.max())

    fig = figure(
        series, smooth, today_x=today_x, today=today, record_year=record_year, record=record
    )
    data = {
        "smooth": {int(y): round(float(v), 2) for y, v in smooth.items()},
        "today": {"level": round(today, 2), "x": today_x, "from": last - 9, "to": last},
        "tracc": {str(y): v for y, v in TRACC.items()},
        "paris2100": PARIS_2100,
        "colors": {"ink": INK, "muted": MUTED, "band": "#eceef1"},
    }
    html = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{{PLOTLY_VERSION}}", get_plotlyjs_version())
        .replace("{{FIGURE}}", fig.to_json())
        .replace("{{DATA}}", json.dumps(data, ensure_ascii=False))
        .replace("{{LAST_YEAR}}", str(last))
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print("Page écrite :", OUT)


if __name__ == "__main__":
    main()
