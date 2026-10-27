"""Demo CLI: python -m kumbhsafe.cli"""
import csv
import sys
from pathlib import Path

from .crowd import ZoneReading, assess
from .triage import Patient, triage

DATA = Path(__file__).resolve().parents[2] / "data" / "sample"


def run_crowd(path: Path) -> None:
    print("=== Crowd risk by zone ===")
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            r = assess(ZoneReading(row["zone"], int(row["count"]),
                                   float(row["area_m2"]), int(row["prev_count"])))
            print(f"{r.zone:<18} density={r.density:>5}/m2 growth={r.growth_pct:>6}% "
                  f"-> {r.level:<8} | {r.action}")


def run_triage(path: Path) -> None:
    print("\n=== Health triage ===")
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            syms = [s for s in row["symptoms"].split(";") if s]
            p = Patient(int(row["age"]), syms,
                        row["pregnant"] == "1", row["chronic"] == "1")
            t = triage(p)
            print(f"{row['id']:<4} age={p.age:<3} {t.priority:<7} score={t.score:<4} {t.route}")


def main() -> int:
    run_crowd(DATA / "zones.csv")
    run_triage(DATA / "patients.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
