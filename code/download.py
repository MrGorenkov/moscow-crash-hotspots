"""Download the raw inputs into data/.

- dtp-stat.ru open data for Moscow (the file used in the article: Last-Modified 26.02.2026,
  SHA-256 of the zip 430FB00B76BFC0BEA4240C4DDB1C4CBC1F1089884591FA3AFE2135BF093BBAEF;
  later uploads of the same URL may differ)
- the Moscow boundary (OSM relation 102269) from Nominatim, © OpenStreetMap contributors, ODbL
"""
import hashlib
import urllib.request
import zipfile
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data"
DTP = "https://dtp-stat.ru/media/opendata/moskva.geojson.zip"
BOUNDARY = ("https://nominatim.openstreetmap.org/search?q=%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0&countrycodes=ru"
            "&featureType=state&polygon_geojson=1&format=geojson&limit=1")
SHA = "430FB00B76BFC0BEA4240C4DDB1C4CBC1F1089884591FA3AFE2135BF093BBAEF"


def get(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "moscow-crash-hotspots research script"})
    with urllib.request.urlopen(req) as r:
        path.write_bytes(r.read())


def main():
    D.mkdir(exist_ok=True)
    z = D / "moskva.geojson.zip"
    get(DTP, z)
    sha = hashlib.sha256(z.read_bytes()).hexdigest().upper()
    print("dtp-stat zip sha256:", sha, "(same as in the article)" if sha == SHA else "(DIFFERS from the article's file)")
    zipfile.ZipFile(z).extractall(D)
    get(BOUNDARY, D / "moscow_boundary.geojson")
    print("done:", sorted(p.name for p in D.iterdir()))


if __name__ == "__main__":
    main()
