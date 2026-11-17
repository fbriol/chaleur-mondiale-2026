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
Référence : moyenne 1900-1930, la période « préindustrielle » retenue par
Météo-France pour la France hexagonale (rapport TRACC, partie 1).

Futur : uniquement des chiffres officiels, tous par rapport à l'ère
préindustrielle.
  - Point de départ : réchauffement dû aux activités humaines en France en
    2025, +1,8 °C (Météo-France, communiqué du 23 mars 2026). Les années
    observées au-dessus relèvent de la variabilité naturelle.
  - Trajectoire actuelle : TRACC (+2 °C en 2030, +2,7 °C en 2050, +4 °C en
    2100 en France).
  - Accord de Paris : bande entre les scénarios SSP1-1.9 et SSP1-2.6 du GIEC
    (AR6, groupe I, tableau SPM.1), convertis du monde à la France par la
    correspondance officielle de la TRACC (rapport TRACC, figure 1 et
    tableau 2), interpolée linéairement entre ses points.

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
COOL_FILL = "rgba(42, 120, 214, 0.18)"
X_RANGE = (1897, 2103)
Y_RANGE = (-1.3, 4.7)

NORMAL_1961_1990 = 11.8  # °C, référence de la série officielle
BASELINE = (1900, 1930)
THIS_YEAR = 2026  # année en cours, incomplète dans l'export : exclue
WINDOW = 11  # moyenne glissante centrée, en années, comme dans la série officielle
END_YEAR = 2100  # horizon des projections

#: Réchauffement dû aux activités humaines en France, Météo-France, communiqué
#: du 23 mars 2026 (« + 2,5 °C en France en 2025 ») : +2,5 °C observés en 2025,
#: dont +1,8 °C d'origine humaine.
HUMAN_YEAR, HUMAN_LEVEL = 2025, 1.8

#: TRACC, France hexagonale, par rapport à l'ère préindustrielle.
TRACC = {2030: 2.0, 2050: 2.7, 2100: 4.0}

#: Correspondance officielle entre réchauffement mondial et France hexagonale,
#: par rapport à l'ère préindustrielle (rapport TRACC, Météo-France, partie 1,
#: figure 1 et tableau 2).
WORLD_TO_FRANCE = ((1.2, 1.7), (1.5, 2.0), (2.0, 2.7), (3.0, 4.0))

#: GIEC AR6, groupe I, tableau SPM.1 : réchauffement mondial (meilleure
#: estimation, par rapport à 1850-1900) sur 2021-2040, 2041-2060 et 2081-2100,
#: placé au milieu de chaque période. La valeur de 2090 est maintenue jusqu'en 2100.
SSP1_19 = {2030: 1.5, 2050: 1.6, 2090: 1.4}
SSP1_26 = {2030: 1.5, 2050: 1.7, 2090: 1.8}


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


def to_france(world: float) -> float:
    """Réchauffement en France correspondant à un réchauffement mondial (TRACC)."""
    xs, ys = zip(*WORLD_TO_FRANCE, strict=True)
    if not xs[0] <= world <= xs[-1]:
        msg = f"{world} °C hors de la correspondance officielle ({xs[0]} à {xs[-1]} °C)"
        raise ValueError(msg)
    return float(np.interp(world, xs, ys))


def trajectory(levels: dict[int, float]) -> list[tuple[float, float]]:
    """Trajectoire France partant du réchauffement d'origine humaine actuel, jusqu'en 2100."""
    points = [(HUMAN_YEAR, HUMAN_LEVEL), *levels.items()]
    if points[-1][0] < END_YEAR:
        points.append((END_YEAR, points[-1][1]))
    return points


def interp(years: np.ndarray, points: list[tuple[float, float]]) -> np.ndarray:
    """Valeurs, arrondies au centième, de la ligne brisée `points` aux années `years`."""
    xs, ys = zip(*points, strict=True)
    return np.round(np.interp(years, xs, ys), 2)


def figure(
    series: pd.Series,
    smooth: pd.Series,
    *,
    record_year: int,
    record: float,
    paris_low: list[tuple[float, float]],
    paris_high: list[tuple[float, float]],
) -> go.Figure:
    """La courbe sans les repères de la famille, ajoutés ensuite dans le navigateur."""
    years = np.arange(HUMAN_YEAR, END_YEAR + 1)
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
            x=years,
            y=interp(years, trajectory(TRACC)),
            name="Trajectoire actuelle (TRACC)",
            mode="lines",
            line=dict(color=HOT, width=3),
            hovertemplate="%{y:+.1f} °C<extra>Trajectoire actuelle (TRACC)</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=interp(years, paris_high),
            name="Accord de Paris (GIEC)",
            legendgroup="paris",
            mode="lines",
            line=dict(color=COOL, width=2),
            hovertemplate="%{y:+.1f} °C<extra>Paris, SSP1-2.6</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=interp(years, paris_low),
            name="Accord de Paris, SSP1-1.9",
            legendgroup="paris",
            showlegend=False,
            mode="lines",
            line=dict(color=COOL, width=2),
            fill="tonexty",
            fillcolor=COOL_FILL,
            hovertemplate="%{y:+.1f} °C<extra>Paris, SSP1-1.9</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[HUMAN_YEAR, *TRACC],
            y=[HUMAN_LEVEL, *TRACC.values()],
            mode="markers",
            showlegend=False,
            hoverinfo="skip",
            marker=dict(
                size=10,
                color=[MUTED] + [HOT] * len(TRACC),
                line=dict(color="white", width=2),
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
    fig.add_annotation(
        x=HUMAN_YEAR,
        y=HUMAN_LEVEL,
        ax=120,
        ay=60,
        arrowcolor=MUTED,
        text=f"{HUMAN_YEAR} : {fr(HUMAN_LEVEL)} °C dus<br>aux activités humaines",
        font=dict(size=12, color=MUTED),
        bgcolor="rgba(255,255,255,.8)",
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
    record_year, record = int(series.idxmax()), float(series.max())
    paris_low = trajectory({year: to_france(v) for year, v in SSP1_19.items()})
    paris_high = trajectory({year: to_france(v) for year, v in SSP1_26.items()})
    print(f"{last} observé : {fr(series[last], 2)} °C ; moyenne {last - 9}-{last} : {fr(today, 2)}")
    for name, points in (("SSP1-1.9", paris_low), ("SSP1-2.6", paris_high)):
        print(f"Paris {name} :", ", ".join(f"{y} {fr(v, 2)} °C" for y, v in points))

    fig = figure(
        series,
        smooth,
        record_year=record_year,
        record=record,
        paris_low=paris_low,
        paris_high=paris_high,
    )
    data = {
        "smooth": {int(y): round(float(v), 2) for y, v in smooth.items()},
        "today": {"level": round(today, 2), "x": last - 4.5, "from": last - 9, "to": last},
        "start": {"x": HUMAN_YEAR, "level": HUMAN_LEVEL},
        "tracc": {str(y): v for y, v in TRACC.items()},
        "paris2100": [round(paris_low[-1][1], 1), round(paris_high[-1][1], 1)],
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
