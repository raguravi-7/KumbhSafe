"""HTTP server (standard library only): JSON API + static dashboard."""
import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .engine import System

WEB = Path(__file__).resolve().parent / "web"
TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}


def make_server(system, host="127.0.0.1", port=8000):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            api = {
                "/api/zones": system.snapshot, "/api/alerts": system.alerts,
                "/api/facilities": system.facilities_list, "/api/meta": system.meta,
                "/api/incidents": lambda: system.incidents,
            }
            if path in api:
                return self._send(200, api[path]())
            name = "index.html" if path == "/" else path.lstrip("/")
            f = (WEB / name).resolve()
            if WEB.resolve() in f.parents and f.is_file() and f.suffix in TYPES:
                return self._send(200, f.read_bytes(), TYPES[f.suffix])
            self._send(404, {"error": "not found"})

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > 10_000:
                    return self._send(413, {"error": "payload too large"})
                payload = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(payload, dict):
                    raise ValueError("JSON object expected")
                if path == "/api/triage":
                    return self._send(200, system.report_triage(payload))
                if path == "/api/sos":
                    return self._send(200, system.report_sos(payload))
                if path == "/api/surge":
                    system.trigger_surge(payload.get("zone"))
                    return self._send(200, {"ok": True})
                self._send(404, {"error": "not found"})
            except (ValueError, json.JSONDecodeError) as e:
                self._send(400, {"error": str(e)})

    return ThreadingHTTPServer((host, port), Handler)


def main():
    ap = argparse.ArgumentParser(description="KumbhSafe dashboard server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=None, help="fixed seed for repeatable demo")
    args = ap.parse_args()
    system = System(seed=args.seed)

    def loop():
        while True:
            time.sleep(2)
            system.tick()

    threading.Thread(target=loop, daemon=True).start()
    httpd = make_server(system, args.host, args.port)
    print(f"KumbhSafe running at http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
