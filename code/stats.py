"""Table 1 and the significance tests quoted in the article.

Reads results/hotspot_eval.csv, writes results/table1.csv and results/stats.json:
  - mean hit rate over the 10 year pairs per method and area share (all injury crashes), PAI at 1 %, KSI hit rate at 1 %
  - Friedman test across the 8 ranked methods at 1 % of the area (10 pairs as blocks)
  - Wilcoxon signed-rank tests (exact, two-sided) of 3-year counts against every other method at 1 %,
    and of the МКДТП criterion against counts at the МКДТП area share
"""
import json
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RANKED = ["Counts (years t-2..t)", "KDE h=100 m", "Counts (year t)", "KDE h=200 m", "KDE h=400 m",
          "DBSCAN eps=100 m", "HDBSCAN", "Gi* r=400 m"]


def per_pair(res, method, target, share=None):
    r = res[(res.method == method) & (res.target == target)]
    if share is not None:
        r = r[(r.share - share).abs() < 1e-9]
    return r.set_index("train_year").hit_rate.sort_index()


def main():
    res = pd.read_csv(ROOT / "results" / "hotspot_eval.csv")
    rows = []
    for m in RANKED:
        row = {"method": m}
        for s in (0.0025, 0.005, 0.01, 0.02, 0.05):
            row[f"hr_{s}"] = per_pair(res, m, "all", s).mean()
        row["pai_0.01"] = row["hr_0.01"] / 0.01
        row["hr_ksi_0.01"] = per_pair(res, m, "KSI", 0.01).mean()
        rows.append(row)
    mk = per_pair(res, "МКДТП criterion", "all")
    mk_share = res[(res.method == "МКДТП criterion") & (res.target == "all")].share
    rows.append({"method": "МКДТП criterion", "share_mean": mk_share.mean(), "share_min": mk_share.min(),
                 "share_max": mk_share.max(), "hr_own": mk.mean(),
                 "pai_own": res[(res.method == "МКДТП criterion") & (res.target == "all")].pai.mean(),
                 "hr_ksi_own": per_pair(res, "МКДТП criterion", "KSI").mean()})
    t1 = pd.DataFrame(rows)
    t1.to_csv(ROOT / "results" / "table1.csv", index=False)

    out = {}
    mat = pd.concat([per_pair(res, m, "all", 0.01).rename(m) for m in RANKED], axis=1)
    out["friedman_1pct"] = stats.friedmanchisquare(*[mat[c] for c in RANKED]).pvalue
    out["wilcoxon_counts3_vs"] = {}
    for m in RANKED[1:]:
        d = mat["Counts (years t-2..t)"] - mat[m]
        out["wilcoxon_counts3_vs"][m] = {"wins": int((d > 0).sum()),
                                         "p": stats.wilcoxon(mat["Counts (years t-2..t)"], mat[m]).pvalue}
    out["mkdtp_vs"] = {}
    for tgt in ("all", "KSI"):
        base = per_pair(res, "МКДТП criterion", tgt)
        for m in ("Counts (years t-2..t)", "Counts (year t)", "KDE h=200 m"):
            other = per_pair(res, f"{m} @МКДТП share", tgt)
            out["mkdtp_vs"][f"{tgt}: {m}"] = {"mkdtp": base.mean(), "other": other.mean(),
                                              "rel_gain": other.mean() / base.mean() - 1,
                                              "wins": int((other > base).sum()),
                                              "p": stats.wilcoxon(other, base).pvalue}
    (ROOT / "results" / "stats.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 200)
    print(t1.round(4).to_string())
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
