"""Geo helpers: distance and nearest-facility lookup."""
import math


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest(facilities, lat, lon, types):
    """Return (facility, km) of the closest facility whose type is in `types`."""
    best = None
    for f in facilities:
        if f["type"] not in types:
            continue
        d = haversine_km(lat, lon, f["lat"], f["lon"])
        if best is None or d < best[1]:
            best = (f, d)
    return best


def eta_minutes(km, speed_kmph=15.0):
    """Crowded-area response speed (default 15 km/h)."""
    return max(1, round(km / speed_kmph * 60))
