"""Rule-based health triage. Prototype only; NOT a medical device.

Symptoms carry weights; age and vulnerability add risk. Output is a
colour-coded priority (RED > ORANGE > YELLOW > GREEN) with a route.
An ML model can replace `score()` later behind the same interface.
"""
from dataclasses import dataclass, field
from typing import List

SYMPTOM_WEIGHTS = {
    "unconscious": 100, "not_breathing": 100, "severe_bleeding": 90,
    "chest_pain": 70, "seizure": 70, "difficulty_breathing": 65,
    "stampede_injury": 60, "fracture": 40, "heat_stroke": 60,
    "high_fever": 30, "dehydration": 30, "vomiting": 15,
    "dizziness": 15, "minor_cut": 5, "headache": 5,
}


@dataclass
class Patient:
    age: int
    symptoms: List[str] = field(default_factory=list)
    pregnant: bool = False
    chronic_condition: bool = False


@dataclass
class TriageResult:
    score: int
    priority: str
    route: str


def score(p: Patient) -> int:
    s = sum(SYMPTOM_WEIGHTS.get(x.strip().lower(), 0) for x in p.symptoms)
    if p.age < 5 or p.age >= 60:
        s += 15
    if p.pregnant:
        s += 15
    if p.chronic_condition:
        s += 10
    return s


def triage(p: Patient) -> TriageResult:
    s = score(p)
    if s >= 90:
        return TriageResult(s, "RED", "Immediate: ambulance + nearest ICU-capable hospital")
    if s >= 60:
        return TriageResult(s, "ORANGE", "Urgent: field hospital doctor within 10 min")
    if s >= 25:
        return TriageResult(s, "YELLOW", "Delayed: first-aid post, observe")
    return TriageResult(s, "GREEN", "Minor: first-aid and advice")
