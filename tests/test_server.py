import json
import threading
import unittest
import urllib.error
import urllib.request

from kumbhsafe.engine import System
from kumbhsafe.server import make_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = make_server(System(seed=1), "127.0.0.1", 0)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, r.read()

    def post(self, path, body):
        req = urllib.request.Request(self.base + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_zones(self):
        code, body = self.get("/api/zones")
        self.assertEqual(code, 200)
        self.assertEqual(len(json.loads(body)), 5)

    def test_dashboard_served(self):
        code, body = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn(b"KumbhSafe", body)

    def test_triage_endpoint(self):
        code, r = self.post("/api/triage", {"zone": "Ram Ghat", "age": 30, "symptoms": ["chest_pain"]})
        self.assertEqual((code, r["priority"]), (200, "ORANGE"))

    def test_bad_request(self):
        code, r = self.post("/api/triage", {"zone": "Ram Ghat", "age": "x"})
        self.assertEqual(code, 400)

    def test_path_traversal_blocked(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get("/../engine.py")
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
