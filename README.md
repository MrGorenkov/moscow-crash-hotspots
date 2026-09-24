# Predictive accuracy of identifying road crash concentration sites in Moscow

Code, derived results and figures for the article
«Прогнозная точность выявления мест концентрации дорожно-транспортных происшествий в Москве»
(A. A. Gorenkov, Plekhanov Russian University of Economics, 2026).

## What is done
- 93,614 injury crashes in Moscow, 2015–2025, from the open data of the Road Crash Map project
  (dtp-stat.ru; original source: the State Traffic Inspectorate, stat.gibdd.ru).
- The city (OSM relation 102269) is split into 64,045 cells of 200 × 200 m.
- For 10 pairs (year t → year t + 1) each method ranks cells from year-t data only; the share of year-(t + 1)
  crashes in the top 0.25–5 % of the area (hit rate) and the predictive accuracy index PAI are computed.
  Methods: 1-year and 3-year counts, kernel density (h = 100/200/400 m), Getis–Ord Gi*, DBSCAN, HDBSCAN,
  and the official Russian criterion for crash concentration sites (Federal Law 196-FZ, art. 2),
  which is evaluated at the area it selects itself.
- Temporal stability of the top 1 % of cells (Jaccard index, years in the top).

## Layout
```
code/
  download.py   raw data: dtp-stat Moscow GeoJSON and the OSM boundary -> data/
  prepare.py    cleaning, UTM 37N projection, consistent KSI flag -> results/crashes.parquet
  hotspots.py   grid, methods, out-of-sample evaluation -> results/hotspot_eval.csv, persistence.json
  stats.py      Table 1, Friedman and Wilcoxon tests -> results/table1.csv, stats.json
  figures.py    figures 1–4 -> paper/figures/
data/data_notes.md   description of the source data and its caveats
results/             derived results (the crash table is rebuilt by prepare.py)
paper/figures/       figures of the article
```

## Reproduce
```
pip install numpy pandas pyarrow scipy scikit-learn pyproj matplotlib
python code/download.py
python code/prepare.py
python code/hotspots.py
python code/stats.py
python code/figures.py
```
Random tie-breaking uses a fixed seed (20260924). The dtp-stat file is updated from time to time;
`download.py` reports whether the downloaded file is the one used in the article.

## Data and licenses
- Road Crash Map (dtp-stat.ru) open data; attribution: «Карта ДТП», original source — Госавтоинспекция.
  The raw file is not redistributed here.
- Moscow boundary: © OpenStreetMap contributors, ODbL.
- Code in this repository: MIT.
