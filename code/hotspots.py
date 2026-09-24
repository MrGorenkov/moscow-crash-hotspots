"""Out-of-sample evaluation of crash-hotspot methods for Moscow, 2015-2025.

For each of the 10 pairs (train year t, test year t+1) every method scores the cells of a
200 m grid covering the city (OSM relation 102269) from year-t crashes only; cells are
ranked by score and the top share s of the city area is flagged. Metrics:
  hit rate HR(s) = share of year-(t+1) crashes that fall in flagged cells
  PAI(s)         = HR(s) / s   (Predictive Accuracy Index, Chainey et al. 2008)
for s in {0.25, 0.5, 1, 2, 5} % of the city area, for all injury crashes and for
killed-or-seriously-injured (KSI) crashes. The official Russian criterion for places of
concentration of crashes (МКДТП: >= 5 crashes, or >= 3 of the same type, within a 200 m
stretch in 12 months) is evaluated at the area share it selects by itself.
Writes results/hotspot_eval.csv and results/persistence.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.path import Path as MPath
from pyproj import Transformer
from scipy import ndimage
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN, HDBSCAN

ROOT = Path(__file__).resolve().parents[1]
CELL = 200.0
SHARES = [0.0025, 0.005, 0.01, 0.02, 0.05]
RNG = np.random.default_rng(20260924)


def city_grid():
    gj = json.loads((ROOT / "data" / "moscow_boundary.geojson").read_text(encoding="utf-8"))
    tr = Transformer.from_crs(4326, 32637, always_xy=True)
    polys = []
    for poly in gj["features"][0]["geometry"]["coordinates"]:
        ring = np.array(poly[0])
        x, y = tr.transform(ring[:, 0], ring[:, 1])
        polys.append(MPath(np.c_[x, y]))
    xs = np.concatenate([p.vertices[:, 0] for p in polys])
    ys = np.concatenate([p.vertices[:, 1] for p in polys])
    x0, y0 = np.floor(xs.min() / CELL) * CELL, np.floor(ys.min() / CELL) * CELL
    nx, ny = int(np.ceil((xs.max() - x0) / CELL)), int(np.ceil((ys.max() - y0) / CELL))
    cx, cy = np.meshgrid(x0 + (np.arange(nx) + 0.5) * CELL, y0 + (np.arange(ny) + 0.5) * CELL)
    pts = np.c_[cx.ravel(), cy.ravel()]
    inside = np.zeros(len(pts), bool)
    for p in polys:
        inside |= p.contains_points(pts)
    return x0, y0, nx, ny, inside.reshape(ny, nx)


def cell_index(df, x0, y0, nx, ny):
    ix = np.clip(((df["x"].values - x0) // CELL).astype(int), 0, nx - 1)
    iy = np.clip(((df["y"].values - y0) // CELL).astype(int), 0, ny - 1)
    return iy, ix


def counts(df, g):
    x0, y0, nx, ny, _ = g
    iy, ix = cell_index(df, x0, y0, nx, ny)
    c = np.zeros((ny, nx))
    np.add.at(c, (iy, ix), 1)
    return c


# ---------- methods: each returns a score grid from training crashes ----------
def m_counts(train, g, **_):
    return counts(train, g)


def m_counts3(train, g, hist=None, **_):
    return counts(hist, g) if hist is not None else counts(train, g)


def m_kde(train, g, h=200.0, **_):
    return ndimage.gaussian_filter(counts(train, g), sigma=h / CELL, mode="constant")


def m_gistar(train, g, radius=400.0, **_):
    """Getis-Ord Gi* with binary weights inside a square window of the given radius."""
    c = counts(train, g)
    inside = g[4]
    k = 2 * int(round(radius / CELL)) + 1
    n = inside.sum()
    xbar = c[inside].mean()
    s = np.sqrt((c[inside] ** 2).mean() - xbar ** 2)
    w = ndimage.uniform_filter(inside.astype(float), size=k, mode="constant") * k * k  # neighbours in city
    local = ndimage.uniform_filter(c, size=k, mode="constant") * k * k
    num = local - xbar * w
    den = s * np.sqrt((n * w - w ** 2) / (n - 1))
    return np.where(den > 0, num / np.maximum(den, 1e-12), 0.0)


def cluster_score(train, g, labels):
    x0, y0, nx, ny, _ = g
    iy, ix = cell_index(train, x0, y0, nx, ny)
    sc = np.zeros((ny, nx))
    lab = pd.Series(labels)
    size = lab[lab >= 0].value_counts()
    for i, l in enumerate(labels):
        if l >= 0:
            sc[iy[i], ix[i]] = max(sc[iy[i], ix[i]], size[l])
    return sc


def m_dbscan(train, g, eps=100.0, min_samples=5, **_):
    lab = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(train[["x", "y"]].values)
    return cluster_score(train, g, lab)


def m_hdbscan(train, g, min_cluster_size=10, **_):
    lab = HDBSCAN(min_cluster_size=min_cluster_size).fit_predict(train[["x", "y"]].values)
    return cluster_score(train, g, lab)


def mkdtp_flags(train, radius=100.0):
    """Crashes that sit in a 200 m stretch (radius 100 m) with >= 5 crashes, or >= 3 of the same type."""
    xy = train[["x", "y"]].values
    tree = cKDTree(xy)
    nb = tree.query_ball_point(xy, r=radius)
    cat = train["category"].values
    flag = np.zeros(len(train), bool)
    for i, idx in enumerate(nb):
        if len(idx) >= 5 or sum(cat[j] == cat[i] for j in idx) >= 3:
            flag[i] = True
    return flag


def m_mkdtp(train, g, **_):
    f = mkdtp_flags(train)
    return counts(train[f], g)


METHODS = {
    "Counts (year t)": (m_counts, {}),
    "Counts (years t-2..t)": (m_counts3, {}),
    "KDE h=100 m": (m_kde, {"h": 100.0}),
    "KDE h=200 m": (m_kde, {"h": 200.0}),
    "KDE h=400 m": (m_kde, {"h": 400.0}),
    "Gi* r=400 m": (m_gistar, {"radius": 400.0}),
    "DBSCAN eps=100 m": (m_dbscan, {}),
    "HDBSCAN": (m_hdbscan, {}),
}


def rank_cells(score, inside):
    s = score[inside] + RNG.random(inside.sum()) * 1e-9  # random tie-breaking
    return np.argsort(-s)


def evaluate(score, test, g, shares):
    inside = g[4]
    tc = counts(test, g)[inside]
    order = rank_cells(score, inside)
    total = tc.sum()
    n = inside.sum()
    out = {}
    for s in shares:
        k = int(round(s * n))
        hr = tc[order[:k]].sum() / total
        out[s] = (hr, hr / s)
    return out


def main():
    df = pd.read_parquet(ROOT / "results" / "crashes.parquet")
    g = city_grid()
    inside = g[4]
    n_cells = int(inside.sum())
    print("grid cells inside Moscow:", n_cells, "area km2:", n_cells * CELL * CELL / 1e6)
    rows = []
    for t in range(2015, 2025):
        train = df[df.year == t]
        hist = df[(df.year >= t - 2) & (df.year <= t)]
        for target, test in (("all", df[df.year == t + 1]), ("KSI", df[(df.year == t + 1) & (df.ksi == 1)])):
            for name, (fn, kw) in METHODS.items():
                sc = fn(train, g, hist=hist, **kw)
                for s, (hr, pai) in evaluate(sc, test, g, SHARES).items():
                    rows.append({"train_year": t, "target": target, "method": name, "share": s, "hit_rate": hr, "pai": pai})
            # official МКДТП criterion at its own area share
            sc = m_mkdtp(train, g)
            flagged = (sc[inside] > 0).sum()
            s = flagged / n_cells
            tc = counts(test, g)[inside]
            hr = tc[sc[inside] > 0].sum() / tc.sum()
            rows.append({"train_year": t, "target": target, "method": "МКДТП criterion", "share": s, "hit_rate": hr,
                         "pai": hr / s if s > 0 else np.nan})
            # the best-performing smooth method at exactly the МКДТП area share, for a like-for-like comparison
            for name in ("Counts (year t)", "KDE h=200 m", "Counts (years t-2..t)"):
                fn, kw = METHODS[name]
                hr2, pai2 = evaluate(fn(train, g, hist=hist, **kw), test, g, [s])[s]
                rows.append({"train_year": t, "target": target, "method": f"{name} @МКДТП share", "share": s,
                             "hit_rate": hr2, "pai": pai2})
        print("done", t, flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(ROOT / "results" / "hotspot_eval.csv", index=False)

    # persistence: how often a cell is in the top 1 % of the city area by yearly count
    k = int(round(0.01 * n_cells))
    top = {}
    for t in range(2015, 2026):
        order = rank_cells(counts(df[df.year == t], g), inside)
        top[t] = set(order[:k].tolist())
    jacc = {f"{t}-{t + 1}": len(top[t] & top[t + 1]) / len(top[t] | top[t + 1]) for t in range(2015, 2025)}
    freq = pd.Series([sum(c in top[t] for t in top) for c in set().union(*top.values())]).value_counts().sort_index()
    pers = {"n_cells": n_cells, "top1pct_cells": k, "jaccard_consecutive": jacc,
            "years_in_top1pct_hist": {int(a): int(b) for a, b in freq.items()}}
    (ROOT / "results" / "persistence.json").write_text(json.dumps(pers, indent=1), encoding="utf-8")
    print(json.dumps(pers, indent=1))


if __name__ == "__main__":
    main()
