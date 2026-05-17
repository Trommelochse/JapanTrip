#!/usr/bin/env python3
"""
Geocode places for a day via Photon (OSM-based, no API key needed).
Falls back to Nominatim if Photon fails. Constrains results to a
city-region bounding box to filter out same-named places elsewhere.

Reads a "seed" file: places/<stem>.seed.json with shape:
{
  "region": "tokyo",   // see REGIONS below
  "places": [
    {"name": "Display Name", "query": "Search query", "time": "09:00",
     "category": "anchor", "notes": "..."}
  ]
}

Writes places/<stem>.json with lat/lng filled in. Entries that fail
get "lat": null, "lng": null, "geocode_error": "..." so you can fix them by hand.

Usage:
    python3 geocode.py day-03-tokyo
    python3 geocode.py --all
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
PLACES = ROOT / "places"

USER_AGENT = "JapanTripPlanner/0.1 (clemens.a.janes@gmail.com)"
PHOTON = "https://photon.komoot.io/api/"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
RATE_LIMIT_SECONDS = 1.1

# (min_lat, min_lon, max_lat, max_lon, bias_lat, bias_lon)
REGIONS = {
    "tokyo":    (35.50, 139.50, 35.85, 140.00, 35.68, 139.77),
    "kamakura": (35.27, 139.50, 35.40, 139.62, 35.32, 139.55),
    "hakone":   (35.18, 138.95, 35.30, 139.13, 35.23, 139.05),
    "takayama": (36.10, 137.20, 36.30, 137.35, 36.14, 137.25),
    "shirakawago": (36.20, 136.85, 36.32, 136.95, 36.26, 136.91),
    "kyoto":    (34.85, 135.55, 35.20, 135.90, 35.01, 135.77),
    "ohara":    (35.10, 135.78, 35.18, 135.86, 35.12, 135.83),
    "arashiyama": (34.99, 135.65, 35.05, 135.73, 35.01, 135.68),
}


def _in_box(lat: float, lon: float, box: tuple) -> bool:
    return box[0] <= lat <= box[2] and box[1] <= lon <= box[3]


def geocode_photon(query: str, region: tuple) -> tuple[float, float] | None:
    bias_lat, bias_lon = region[4], region[5]
    params = urllib.parse.urlencode({
        "q": query,
        "limit": "5",  # get more candidates so we can filter by bbox
        "lat": bias_lat,
        "lon": bias_lon,
    })
    req = urllib.request.Request(
        f"{PHOTON}?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"    photon error: {e}")
        return None
    for feat in data.get("features", []):
        lon, lat = feat["geometry"]["coordinates"]
        if _in_box(lat, lon, region):
            return lat, lon
    return None


def geocode_nominatim(query: str, region: tuple) -> tuple[float, float] | None:
    # viewbox is min_lon, max_lat, max_lon, min_lat
    viewbox = f"{region[1]},{region[2]},{region[3]},{region[0]}"
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": "5",
        "viewbox": viewbox,
        "bounded": "1",
    })
    req = urllib.request.Request(
        f"{NOMINATIM}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"    nominatim error: {e}")
        return None
    for entry in data:
        lat, lon = float(entry["lat"]), float(entry["lon"])
        if _in_box(lat, lon, region):
            return lat, lon
    return None


def geocode(query: str, region: tuple) -> tuple[tuple[float, float] | None, str]:
    """Return (coords or None, source name)."""
    coords = geocode_photon(query, region)
    if coords:
        return coords, "photon"
    time.sleep(RATE_LIMIT_SECONDS)
    coords = geocode_nominatim(query, region)
    if coords:
        return coords, "nominatim"
    return None, "none"


def process_seed(stem: str) -> None:
    seed_path = PLACES / f"{stem}.seed.json"
    if not seed_path.is_file():
        print(f"No seed file: {seed_path}")
        return
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    region_key = seed.get("region", "tokyo")
    if region_key not in REGIONS:
        sys.exit(f"Unknown region {region_key!r}; add it to REGIONS in geocode.py")
    region = REGIONS[region_key]

    print(f"\n=== {stem} (region: {region_key}) ===")
    out_places = []
    failures = 0
    for p in seed["places"]:
        name = p["name"]
        entry = {
            "name": name,
            "time": p.get("time"),
            "category": p.get("category"),
        }
        # Manual override: seed can supply lat/lng directly.
        if "lat" in p and "lng" in p:
            entry["lat"], entry["lng"] = p["lat"], p["lng"]
            print(f"  {name}  (manual: {p['lat']}, {p['lng']})")
            if p.get("notes"):
                entry["notes"] = p["notes"]
            out_places.append(entry)
            continue
        query = p.get("query") or name
        print(f"  {name}")
        coords, source = geocode(query, region)
        if coords:
            entry["lat"], entry["lng"] = round(coords[0], 5), round(coords[1], 5)
            print(f"    → {coords[0]:.4f}, {coords[1]:.4f}  via {source}")
        else:
            entry["lat"] = None
            entry["lng"] = None
            entry["geocode_error"] = f"No in-region match for: {query}"
            failures += 1
            print(f"    → FAIL")
        if p.get("notes"):
            entry["notes"] = p["notes"]
        out_places.append(entry)
        time.sleep(RATE_LIMIT_SECONDS)

    out = {
        "_note": f"Generated by geocode.py from {seed_path.name}. Pins are auto-geocoded; verify before relying on them. {failures} failure(s) need manual fix.",
        "region": region_key,
        "places": out_places,
    }
    out_path = PLACES / f"{stem}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {out_path}  ({failures} failure(s))")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stem", nargs="?")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        seeds = sorted(PLACES.glob("*.seed.json"))
        if not seeds:
            sys.exit("No *.seed.json files in places/")
        for s in seeds:
            process_seed(s.stem.removesuffix(".seed"))
    elif args.stem:
        process_seed(args.stem)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
