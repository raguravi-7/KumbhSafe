import unittest
from kumbhsafe.triage import Patient, triage


class TriageTests(unittest.TestCase):
    def test_red(self):
        self.assertEqual(triage(Patient(40, ["unconscious"])).priority, "RED")

    def test_orange(self):
        self.assertEqual(triage(Patient(30, ["chest_pain"])).priority, "ORANGE")

    def test_yellow_elderly(self):
        self.assertEqual(triage(Patient(70, ["dehydration"])).priority, "YELLOW")

    def test_green(self):
        self.assertEqual(triage(Patient(25, ["minor_cut"])).priority, "GREEN")

    def test_unknown_symptom_ignored(self):
        self.assertEqual(triage(Patient(25, ["xyz"])).score, 0)


if __name__ == "__main__":
    unittest.main()
