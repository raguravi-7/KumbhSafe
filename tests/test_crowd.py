import unittest
from kumbhsafe.crowd import ZoneReading, assess, classify_density, density


class CrowdTests(unittest.TestCase):
    def test_density(self):
        self.assertEqual(density(100, 50), 2.0)

    def test_invalid_area(self):
        with self.assertRaises(ValueError):
            density(10, 0)

    def test_levels(self):
        for d, lvl in [(1, "SAFE"), (3, "MODERATE"), (4.5, "HIGH"), (6, "CRITICAL")]:
            self.assertEqual(classify_density(d), lvl)

    def test_growth_escalates(self):
        self.assertEqual(assess(ZoneReading("Z", 3000, 1000, 2000)).level, "HIGH")

    def test_stable_no_escalation(self):
        self.assertEqual(assess(ZoneReading("Z", 3000, 1000, 2900)).level, "MODERATE")


if __name__ == "__main__":
    unittest.main()
