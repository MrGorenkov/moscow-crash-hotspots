"""Clean the dtp-stat Moscow GeoJSON into a crash table with metric coordinates.

- keeps crashes 2015-2025 with valid coordinates inside a Moscow bounding box
  (drops the 783 records with null, placeholder, swapped or out-of-box points, all from 2015-2018)
- projects WGS-84 to UTM zone 37N (EPSG:32637), metres
- builds a consistent severity flag KSI = at least one killed or one in-patient,
  from participant health status (the dtp-stat `severity` field breaks in 2020)
Writes results/crashes.parquet and results/prepare_log.json.
"""
import json
from pathlib import Path

import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "moskva.geojson"


def persons(props):
    for v in props.get("vehicles") or []:
        yield from v.get("participants") or []
    yield from props.get("participants") or []


def main():
    gj = json.loads(SRC.read_text(encoding="utf-8"))
    rows, dropped = [], {"null_geometry": 0, "out_of_box": 0, "outside_years": 0}
    for f in gj["features"]:
        p = f["properties"]
        year = int(p["datetime"][:4])
        if not 2015 <= year <= 2025:
            dropped["outside_years"] += 1
            continue
        g = f.get("geometry")
        if not g or not g.get("coordinates"):
            dropped["null_geometry"] += 1
            continue
        lon, lat = g["coordinates"][:2]
        if not (36.7 <= lon <= 38.0 and 55.0 <= lat <= 56.1) or (lon == 37 and lat == 55):
            dropped["out_of_box"] += 1
            continue
        hs = [str(x.get("health_status") or "") for x in persons(p)]
        killed = (p.get("dead_count") or 0) > 0 or any("скончал" in h.lower() or "погиб" in h.lower() for h in hs)
        inpatient = any("стационарном лечении" in h.lower() for h in hs)
        rows.append({"id": p["id"], "gibdd": p.get("gibdd_number"), "datetime": p["datetime"], "year": year,
                     "lon": lon, "lat": lat, "category": p.get("category"), "light": p.get("light"),
                     "dead": p.get("dead_count") or 0, "injured": p.get("injured_count") or 0,
                     "ksi": int(killed or inpatient), "killed": int(killed),
                     "pedestrian": int("Пешеходы" in (p.get("participant_categories") or []))})
    df = pd.DataFrame(rows)
    x, y = Transformer.from_crs(4326, 32637, always_xy=True).transform(df["lon"].values, df["lat"].values)
    df["x"], df["y"] = x, y
    df.to_parquet(ROOT / "results" / "crashes.parquet", index=False)
    log = {"kept": len(df), "dropped": dropped, "per_year": df.groupby("year").size().to_dict(),
           "ksi_share_per_year": df.groupby("year")["ksi"].mean().round(3).to_dict()}
    (ROOT / "results" / "prepare_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
