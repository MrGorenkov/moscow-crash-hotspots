"""Figures for the article (Vestnik SibADI): grayscale-legible, bilingual labels, Arial.

Fig. 1  map: 3-year hotspot cells (top 1 % of city area, trained on 2022-2024) vs cells flagged by the
        official criterion in 2024, with 2025 injury crashes
Fig. 2  hit rate vs flagged share of city area (mean over 10 year pairs), all injury crashes and KSI
Fig. 3  per-pair hit rate: official criterion vs 3-year counts at the same area share
Fig. 4  stability of the top 1 % cells: Jaccard index of consecutive years and years-in-top histogram
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import hotspots as H  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
MM = 1 / 25.4
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.5, "legend.frameon": False})
STYLE = {  # grayscale-safe: line style + marker carry identity
    "Counts (years t-2..t)": ("#000000", "-", "o", "Счёт за 3 года / 3-year counts"),
    "Counts (year t)": ("#000000", "--", "s", "Счёт за год / 1-year counts"),
    "KDE h=100 m": ("#555555", "-", "^", "ЯОП / KDE, h = 100 м"),
    "KDE h=400 m": ("#555555", ":", "v", "ЯОП / KDE, h = 400 м"),
    "Gi* r=400 m": ("#888888", "-.", "D", "Gi*, r = 400 м"),
    "HDBSCAN": ("#888888", "--", "x", "HDBSCAN"),
    "DBSCAN eps=100 m": ("#888888", ":", "+", "DBSCAN, eps = 100 м"),
}


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=600, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.jpg", dpi=400, bbox_inches="tight")
    plt.close(fig)


def fig_map(df):
    g = H.city_grid()
    x0, y0, nx, ny, inside = g
    hist = df[(df.year >= 2022) & (df.year <= 2024)]
    sc = H.counts(hist, g)
    k = int(round(0.01 * inside.sum()))
    order = H.rank_cells(sc, inside)
    idx = np.flatnonzero(inside.ravel())[order[:k]]
    top = np.zeros(ny * nx, bool)
    top[idx] = True
    top = top.reshape(ny, nx)
    mk = H.m_mkdtp(df[df.year == 2024], g) > 0
    test = df[df.year == 2025]
    fig, ax = plt.subplots(figsize=(165 * MM, 105 * MM))
    fig.subplots_adjust(left=0, right=0.62, top=1, bottom=0)
    ax.imshow(np.where(inside, 0.93, 1.0), origin="lower", cmap="gray", vmin=0, vmax=1,
              extent=[x0, x0 + nx * H.CELL, y0, y0 + ny * H.CELL])
    ax.scatter(test.x, test.y, s=0.35, c="#8a8a8a", linewidths=0, rasterized=True,
               label="ДТП 2025 г.\nInjury crashes, 2025")
    yy, xx = np.nonzero(top)
    ax.scatter(x0 + (xx + 0.5) * H.CELL, y0 + (yy + 0.5) * H.CELL, s=2.2, marker="s", c="#000000", linewidths=0,
               label="Число ДТП за 2022–2024 гг.,\n1 % площади города\n3-year counts, top 1 % of area")
    yy, xx = np.nonzero(mk & inside)
    ax.scatter(x0 + (xx + 0.5) * H.CELL, y0 + (yy + 0.5) * H.CELL, s=9, marker="o", facecolors="none",
               edgecolors="#000000", linewidths=0.4, label="Критерий МКДТП, 2024 г.\nOfficial criterion, 2024")
    # zoom to old Moscow and the nearest new territories
    ax.set_xlim(390000, 435000)
    ax.set_ylim(6155000, 6200000)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=7, markerscale=2.5, ncol=1, labelspacing=1.2)
    ax.plot([422000, 432000], [6157000, 6157000], color="k", lw=1.5)
    ax.text(427000, 6157600, "10 км / 10 km", ha="center", fontsize=7)
    save(fig, "fig1_map")


def fig_hitrate(res):
    fig, axes = plt.subplots(1, 2, figsize=(165 * MM, 70 * MM), sharey=True)
    for ax, tgt, title in ((axes[0], "all", "а) все ДТП с пострадавшими / all injury crashes"),
                           (axes[1], "KSI", "б) погибшие и тяжело раненые / KSI crashes")):
        for m, (c, ls, mk, lab) in STYLE.items():
            s = res[(res.target == tgt) & (res.method == m)].groupby("share").hit_rate
            ax.plot(100 * s.mean().index, 100 * s.mean().values, color=c, ls=ls, marker=mk, ms=3.5, lw=1, label=lab)
        mk_ = res[(res.target == tgt) & (res.method == "МКДТП criterion")]
        ax.errorbar(100 * mk_.share.mean(), 100 * mk_.hit_rate.mean(), yerr=100 * mk_.hit_rate.std(),
                    marker="*", ms=9, color="k", ls="", capsize=2, label="Критерий МКДТП / official criterion")
        ax.set_xscale("log")
        ax.set_xticks([0.25, 0.5, 1, 2, 5])
        ax.set_xticklabels(["0,25", "0,5", "1", "2", "5"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_xlabel("Доля площади города, % / Share of city area, %")
        ax.set_title(title, fontsize=8, loc="left")
    axes[0].set_ylabel("Доля ДТП следующего года, %\nShare of next-year crashes, %")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, 0.0), fontsize=6.5, ncol=3)
    fig.subplots_adjust(wspace=0.08)
    save(fig, "fig2_hitrate")


def fig_pairs(res):
    fig, ax = plt.subplots(figsize=(165 * MM, 60 * MM))
    yrs = list(range(2015, 2025))
    for m, lab, hatch, off in (("МКДТП criterion", "Критерий МКДТП / official criterion", "", -0.2),
                               ("Counts (years t-2..t) @МКДТП share", "Счёт за 3 года на той же площади / 3-year counts, same area", "///", 0.2)):
        v = res[(res.target == "all") & (res.method == m)].set_index("train_year").hit_rate.reindex(yrs)
        ax.bar(np.arange(10) + off, 100 * v.values, width=0.4, color="white" if hatch else "#777777",
               edgecolor="k", hatch=hatch, lw=0.6, label=lab)
    ax.set_xticks(np.arange(10))
    ax.set_xticklabels([f"{y}→{str(y + 1)[2:]}" for y in yrs], fontsize=7)
    ax.set_ylabel("Доля ДТП следующего года, %\nShare of next-year crashes, %")
    ax.set_xlabel("Год обучения → год проверки / training year → test year")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=7, ncol=2)
    ax.set_ylim(0, 16)
    save(fig, "fig3_pairs")


def fig_stability(pers):
    fig, axes = plt.subplots(1, 2, figsize=(165 * MM, 55 * MM))
    j = pers["jaccard_consecutive"]
    axes[0].plot(range(len(j)), [100 * v for v in j.values()], "k-o", ms=3.5, lw=1)
    axes[0].set_xticks(range(len(j)))
    axes[0].set_xticklabels([k.replace("-", "→")[2:] .replace("→20", "→") for k in j], fontsize=6.5, rotation=45)
    axes[0].set_ylabel("Индекс Жаккара, %\nJaccard index, %")
    axes[0].set_xlabel("Пара лет / pair of years")
    axes[0].set_ylim(0, 25)
    h = pers["years_in_top1pct_hist"]
    axes[1].bar([int(k) for k in h], list(h.values()), color="#777777", edgecolor="k", lw=0.6)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Число лет в 1 % лучших ячеек\nYears in the top 1 % of cells")
    axes[1].set_ylabel("Число ячеек / number of cells")
    axes[1].set_xticks(range(1, 12))
    for ax, t in zip(axes, ("а)", "б)")):
        ax.set_title(t, fontsize=8, loc="left")
    fig.subplots_adjust(wspace=0.35)
    save(fig, "fig4_stability")


def main():
    df = pd.read_parquet(ROOT / "results" / "crashes.parquet")
    res = pd.read_csv(ROOT / "results" / "hotspot_eval.csv")
    pers = json.loads((ROOT / "results" / "persistence.json").read_text())
    fig_hitrate(res)
    fig_pairs(res)
    fig_stability(pers)
    fig_map(df)


if __name__ == "__main__":
    main()
