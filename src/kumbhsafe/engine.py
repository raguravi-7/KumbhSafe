"""Core system state: zones, simulated live feed, alerts, incidents."""
import csv
import random
import threading
from datetime import datetime
from pathlib import Path

from .crowd import ZoneReading, assess, ORDER
from .geo import nearest, eta_minutes
from .triage import Patient, SYMPTOM_WEIGHTS, triage

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data" / "sample"

# SOS type -> (priority, facility types that respond)
SOS_TYPES = {
    "crowd_crush": ("RED", ["police", "hospital"]),
    "fire": ("RED", ["fire", "hospital"]),
    "medical": ("ORANGE", ["first_aid", "hospital"]),
    "lost_child": ("YELLOW", ["police"]),
}
TRIAGE_FACILITY = {
    "RED": ["hospital"],
    "ORANGE": ["hospital", "first_aid"],
    "YELLOW": ["first_aid"],
    "GREEN": ["first_aid"],
}
SURGE_FACTOR = 1.9
SURGE_TICKS = 20


class System:
    def __init__(self, data_dir=DEFAULT_DATA, seed=None):
        self.rng = random.Random(seed)
        self.lock = threading.RLock()
        self.zones = {}
        with open(Path(data_dir) / "zones.csv", newline="") as f:
            for r in csv.DictReader(f):
                self.zones[r["zone"]] = {
                    "zone": r["zone"], "base": int(r["count"]), "count": int(r["count"]),
                    "prev": int(r["prev_count"]), "area": float(r["area_m2"]),
                    "lat": float(r["lat"]), "lon": float(r["lon"]), "surge": 0,
                }
        with open(Path(data_dir) / "facilities.csv", newline="") as f:
            self.facilities = [
                {"name": r["name"], "type": r["type"],
                 "lat": float(r["lat"]), "lon": float(r["lon"])}
                for r in csv.DictReader(f)
            ]
        self.incidents = []
        self._next_id = 1

    # ---- live feed simulation (replace with CCTV/sensor counts in production)
    def tick(self):
        with self.lock:
            for z in self.zones.values():
                target = z["base"] * (SURGE_FACTOR if z["surge"] > 0 else 1)
                if z["surge"] > 0:
                    z["surge"] -= 1
                z["prev"] = z["count"]
                noise = self.rng.gauss(0, z["base"] * 0.02)
                z["count"] = max(0, int(z["count"] + (target - z["count"]) * 0.25 + noise))

    def trigger_surge(self, zone):
        with self.lock:
            if zone not in self.zones:
                raise ValueError("unknown zone")
            self.zones[zone]["surge"] = SURGE_TICKS

    # ---- queries
    def snapshot(self):
        with self.lock:
            out = []
            for z in self.zones.values():
                r = assess(ZoneReading(z["zone"], z["count"], z["area"], z["prev"]))
                out.append({"zone": z["zone"], "count": z["count"], "area_m2": z["area"],
                            "density": r.density, "growth_pct": r.growth_pct,
                            "level": r.level, "action": r.action,
                            "lat": z["lat"], "lon": z["lon"]})
            return out

    def alerts(self):
        alerts = []
        for z in self.snapshot():
            if ORDER.index(z["level"]) >= ORDER.index("HIGH"):
                best = nearest(self.facilities, z["lat"], z["lon"], ["hospital", "first_aid"])
                alerts.append({
                    "zone": z["zone"], "level": z["level"], "density": z["density"],
                    "message": f"{z['level']} crowd density in {z['zone']} ({z['density']}/m2). {z['action']}",
                    "nearest_medical": best[0]["name"] if best else None,
                })
        alerts.sort(key=lambda a: ORDER.index(a["level"]), reverse=True)
        return alerts

    def meta(self):
        return {"symptoms": sorted(SYMPTOM_WEIGHTS), "sos_types": sorted(SOS_TYPES),
                "zones": list(self.zones)}

    def facilities_list(self):
        return self.facilities

    # ---- actions
    def _log(self, kind, zone, priority, detail, facility, km):
        with self.lock:
            inc = {
                "id": self._next_id, "kind": kind, "zone": zone, "priority": priority,
                "detail": detail, "facility": facility["name"] if facility else None,
                "distance_km": round(km, 2) if facility else None,
                "eta_min": eta_minutes(km) if facility else None,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
            self._next_id += 1
            self.incidents.insert(0, inc)
            del self.incidents[200:]
            return inc

    def _zone(self, name):
        if name not in self.zones:
            raise ValueError("unknown zone")
        return self.zones[name]

    def report_triage(self, payload):
        try:
            age = int(payload.get("age"))
        except (TypeError, ValueError):
            raise ValueError("age must be a number")
        if not 0 <= age <= 120:
            raise ValueError("age must be between 0 and 120")
        symptoms = payload.get("symptoms", [])
        if not isinstance(symptoms, list) or not all(isinstance(s, str) for s in symptoms):
            raise ValueError("symptoms must be a list of strings")
        zone = self._zone(payload.get("zone"))
        p = Patient(age, symptoms, bool(payload.get("pregnant")), bool(payload.get("chronic")))
        t = triage(p)
        best = nearest(self.facilities, zone["lat"], zone["lon"], TRIAGE_FACILITY[t.priority])
        fac, km = best if best else (None, 0)
        inc = self._log("triage", zone["zone"], t.priority,
                        f"age {age}: {', '.join(symptoms) or 'no symptoms'}", fac, km)
        return {"score": t.score, "priority": t.priority, "route": t.route, "incident": inc}

    def report_sos(self, payload):
        kind = payload.get("type")
        if kind not in SOS_TYPES:
            raise ValueError("unknown SOS type")
        zone = self._zone(payload.get("zone"))
        priority, types = SOS_TYPES[kind]
        best = nearest(self.facilities, zone["lat"], zone["lon"], types)
        fac, km = best if best else (None, 0)
        note = str(payload.get("note", ""))[:200]
        inc = self._log("sos", zone["zone"], priority, f"{kind}: {note}".strip(": "), fac, km)
        return {"priority": priority, "incident": inc}
