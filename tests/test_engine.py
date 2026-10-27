import unittest
from kumbhsafe.engine import System
from kumbhsafe.geo import haversine_km, nearest


class GeoTests(unittest.TestCase):
    def test_zero_distance(self):
        self.assertAlmostEqual(haversine_km(25.4, 81.8, 25.4, 81.8), 0.0)

    def test_known_distance(self):
        # 0.01 degree latitude is about 1.11 km
        self.assertAlmostEqual(haversine_km(25.0, 81.0, 25.01, 81.0), 1.11, places=1)

    def test_nearest_filters_type(self):
        fac = [{"name": "A", "type": "police", "lat": 0, "lon": 0},
               {"name": "B", "type": "hospital", "lat": 1, "lon": 1}]
        self.assertEqual(nearest(fac, 0, 0, ["hospital"])[0]["name"], "B")
        self.assertIsNone(nearest(fac, 0, 0, ["fire"]))


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.s = System(seed=1)

    def test_surge_raises_level(self):
        self.s.trigger_surge("Sangam Entry")
        for _ in range(8):
            self.s.tick()
        z = [x for x in self.s.snapshot() if x["zone"] == "Sangam Entry"][0]
        self.assertIn(z["level"], ("HIGH", "CRITICAL"))
        self.assertTrue(any(a["zone"] == "Sangam Entry" for a in self.s.alerts()))

    def test_triage_routes_red_to_hospital(self):
        r = self.s.report_triage({"zone": "Ram Ghat", "age": 40, "symptoms": ["unconscious"]})
        self.assertEqual(r["priority"], "RED")
        self.assertIn("Hospital", r["incident"]["facility"])
        self.assertEqual(len(self.s.incidents), 1)

    def test_sos_lost_child_goes_to_police(self):
        r = self.s.report_sos({"zone": "Akhara Marg", "type": "lost_child", "note": "boy, 6"})
        self.assertIn("Police", r["incident"]["facility"])

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.s.report_triage({"zone": "Ram Ghat", "age": "abc", "symptoms": []})
        with self.assertRaises(ValueError):
            self.s.report_triage({"zone": "Nowhere", "age": 20, "symptoms": []})
        with self.assertRaises(ValueError):
            self.s.report_sos({"zone": "Ram Ghat", "type": "bogus"})


if __name__ == "__main__":
    unittest.main()
