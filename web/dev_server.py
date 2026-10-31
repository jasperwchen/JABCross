"""Mock JabCross server for phone-page development. Stdlib only.

Run: python3 web/dev_server.py   (serves web/ on http://localhost:8000)
Then: cloudflared tunnel --url http://localhost:8000
"""
import json
import re
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent
PORT = 8000
SPEAK_EVERY_S = 5.0
_last_speak = 0.0


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if not self.path.startswith("/frame"):  # frames arrive every ~300 ms; don't spam
            super().log_message(fmt, *args)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global _last_speak
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))

        if self.path == "/frame":
            m = re.search(rb'name="heading"\r\n\r\n([^\r]*)', body)
            heading = m.group(1).decode(errors="replace") if m else "?"
            print(f"frame {len(body):>7} B  heading={heading}", flush=True)
            now = time.monotonic()
            if now - _last_speak >= SPEAK_EVERY_S:
                _last_speak = now
                return self.send_json({"speak": "Hello from the mock server", "alert": "none"})
            return self.send_json({"speak": None, "alert": "none"})

        if self.path == "/command":
            try:
                text = json.loads(body or b"{}").get("text", "")
            except ValueError:
                text = ""
            print(f"command: {text!r}", flush=True)
            return self.send_json({"speak": f"Starting route to {text}"})

        self.send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    print(f"Serving {WEB_DIR} on http://localhost:{PORT}", flush=True)
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
