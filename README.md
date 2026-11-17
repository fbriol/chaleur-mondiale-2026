# 2026 talonne le record de chaleur de 2024

![Température mondiale annuelle](temperature-mondiale-2026.png)

Ce dépôt contient le script qui produit cette figure, pour que chacun puisse
la vérifier et la refaire.

## D'où viennent les données

Le script ne contient aucune température saisie à la main. Il télécharge le fichier
publié par le **Copernicus Climate Change Service** (C3S, opéré par l'ECMWF
pour la Commission européenne) avec son bulletin d'octobre 2026 :

- Bulletin : <https://climate.copernicus.eu/copernicus-warmest-october-record-2026-virtually-certain-exceed-15degc>
- Données (CSV) : <https://climate.copernicus.eu/sites/default/files/2026-11/C3S_Bulletin_PR_202610_timeseries_annual_global_surface_temperature_anomalies_ref1850-1900_prediction_DATA.csv>

Les températures sont des moyennes mondiales annuelles de l'air en surface
(réanalyse ERA5), exprimées en écart à la période préindustrielle 1850-1900.
La valeur 2026 est une estimation de C3S établie à fin octobre : l'année
n'est pas terminée.

## Ce que dit Copernicus

- 2024 reste l'année la plus chaude mesurée : +1,60 °C.
- 2026 devrait finir entre +1,56 et +1,61 °C, très probablement au deuxième
  rang, avec environ 20 % de chances d'égaler ou de dépasser 2024.
- Ce serait la deuxième année civile au-dessus de +1,5 °C.

## La page interactive : la courbe avec vos dates

<https://fbriol.github.io/chaleur-mondiale-2026/>

`build_page.py` produit avec [Plotly](https://plotly.com/python/) une version
interactive de la courbe France : on peut survoler chaque année, zoomer, masquer
une courbe en cliquant sur la légende et exporter l'image. Le visiteur saisit
son année de naissance et celles de ses enfants, et les repères de sa famille
s'ajoutent à la courbe. Tout se calcule dans le navigateur : aucune date n'est
envoyée ni enregistrée. Les dates peuvent être passées dans l'adresse
(`?n=1969&e=2000-2006`) pour partager sa propre courbe.

Le texte et le script de la page sont dans `page/index.html`, dans lequel
`build_page.py` insère la figure ; le résultat est écrit dans `site/` (non
versionné). Le workflow `.github/workflows/pages.yml` reconstruit la page et la
publie sur GitHub Pages à chaque modification de `main`.

### Le passé : deux fichiers Météo-France, déposés dans `data/`

- `temperature_france_1900-2017_meteo-france.csv` : série annuelle 1900-2017
  de l'indicateur thermique (30 stations), en écart à la moyenne 1961-1990
  (11,8 °C). Source : Météo-France, diffusée par le ministère de la Transition
  écologique (SDES, indicateur 1.3),
  <https://www.donnees.statistiques.developpement-durable.gouv.fr/lesessentiels/indicateurs/e13.html>.
  Fichier Excel converti en CSV sans modification des valeurs.
- `itn_france_annuel_dataclimat.csv` : indicateur thermique national annuel
  1947-2026, exporté de <https://dataclimat.fr/temperature/itn>
  (Infoclimat / Data For Good, mesures Météo-France) le 17 novembre 2026. Seules les années 2018 à
  2025 en sont utilisées ; 2026, incomplète, est exclue.

Sur leurs 71 années communes (1947-2017), les deux séries diffèrent de
0,04 °C en moyenne (écart-type 0,03 °C) : le script affiche ce contrôle à
chaque exécution. Les écarts sont exprimés par rapport à la moyenne 1900-1930,
calculée sur la série elle-même.

Ces deux fichiers ne sont pas téléchargés par le script : je n'ai pas trouvé
d'adresse stable pour le faire. Chacun peut les réexporter depuis les deux
sites ci-dessus et comparer.

### Le futur : uniquement des chiffres officiels

Toutes les valeurs sont exprimées par rapport à l'ère préindustrielle. Pour la
France hexagonale, Météo-France utilise 1900-1930, comparable à 1850-1900
pour le réchauffement mondial : c'est la référence de la courbe observée
([rapport TRACC, partie 1](https://drias-climat.fr/document/Rapport-TRACC-Partie1-V8-web-72DPI.pdf)).

**Point de départ : le réchauffement d'origine humaine en 2025.** Selon
[Météo-France](https://meteofrance.com/presse/25-degc-en-france-en-2025-comment-la-science-ameliore-la-prevision-des-risques-meteo)
(communiqué du 23 mars 2026), la France a été à +2,5 °C en 2025, dont
+1,8 °C dus aux activités humaines ; le reste relève de la variabilité
naturelle. La série de `data/` donne +2,53 °C pour 2025. Les trajectoires
partent de ce +1,8 °C, car elles décrivent le climat et non une année donnée :
c'est pourquoi les années récentes (et la moyenne 2016-2025, +2,2 °C) sont
au-dessus.

**Trajectoire actuelle (TRACC).** Inscrite dans le code de l'environnement en
janvier 2026, elle retient pour la France hexagonale +2 °C en 2030, +2,7 °C
en 2050 et +4 °C en 2100, ce qui correspond à +1,5, +2 et +3 °C dans le monde.
Source : <https://www.ecologie.gouv.fr/trajectoire-rechauffement-reference-ladaptation-au-changement-climatique-tracc-0>.

**Accord de Paris (GIEC).** La bande bleue couvre les deux scénarios du GIEC
qui respectent l'accord (AR6, groupe I, tableau SPM.1, meilleures estimations
du réchauffement mondial) :

| Scénario | 2021-2040 | 2041-2060 | 2081-2100 |
|---|---|---|---|
| SSP1-1.9, « 1,5 °C » | +1,5 °C | +1,6 °C | +1,4 °C |
| SSP1-2.6, « bien en dessous de 2 °C » | +1,5 °C | +1,7 °C | +1,8 °C |

Elles sont converties pour la France avec la correspondance officielle de la
TRACC (rapport TRACC, figure 1 et tableau 2) :

| Monde | +1,2 °C | +1,5 °C | +2 °C | +3 °C |
|---|---|---|---|---|
| France hexagonale | +1,7 °C | +2 °C | +2,7 °C | +4 °C |

Ce qui donne, en France, +2 °C en 2030 dans les deux cas, puis +2,1 à
+2,3 °C en 2050 et +1,9 à +2,4 °C en 2090. La légère baisse de SSP1-1.9 après
2050 suppose des émissions nettes négatives. Le script affiche ces valeurs à
chaque exécution.

### Limites

- Les valeurs du GIEC sont placées au milieu de chaque période de 20 ans
  (2030, 2050, 2090), et celle de 2090 est maintenue jusqu'en 2100.
- La conversion monde / France est interpolée linéairement entre les points
  officiels de la TRACC, qui ne couvrent que +1,2 à +3 °C dans le monde.
- Entre les repères, les valeurs sont interpolées : ce sont des ordres de
  grandeur.

### Voir la page en local

```bash
python build_page.py
open site/index.html
```

## Refaire la figure et la page

```bash
pip install -r requirements.txt
python plot_temperature.py
python build_page.py   # page interactive, dans site/
```

Une copie du fichier Copernicus téléchargé est conservée dans `data/`. La
figure est régénérée automatiquement par GitHub Actions à chaque
modification, et la page republiée sur GitHub Pages.

## Maintenance du code

Le code Python est vérifié et formaté par [Ruff](https://docs.astral.sh/ruff/)
(réglages dans `pyproject.toml`), lancé avant chaque commit par
[pre-commit](https://pre-commit.com) (`.pre-commit-config.yaml`). Les fichiers
de `data/` et les images ne sont jamais modifiés par ces vérifications.

```bash
pip install pre-commit
pre-commit install          # une fois : active la vérification avant chaque commit
pre-commit run --all-files  # vérifie tout le dépôt
```

## Licence

Code : MIT. Données : © Copernicus Climate Change Service / ECMWF.
