"""JabCross laptop server: phone frames in, spoken guidance out.

Run:  .venv/bin/python server/app.py      (http://localhost:8000, any cwd)
Then: cloudflared tunnel --url http://localhost:8000   (open the https URL on the phone)
Map:  http://localhost:8000/map/ on the laptop (keep the trailing slash)
"""
import threading
import time
from pathlib import Path

import uvicorn
from fastapi import Body, FastAPI, Form, HTTPException, Response, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from perception import latest_depth_jpg, perceive

try:
    from nav import Navigator
    print("navigator: server/nav.py", flush=True)
except ModuleNotFoundError as e:
    if e.name != "nav":
        raise

    class Navigator:  # canned stand-in until server/nav.py exists
        def __init__(self):
            self.last_speak = 0.0

        def command(self, text):
            return f"Starting route to {text}"

        def update(self, perception, heading):
            if time.monotonic() - self.last_speak < 5:
                return {"speak": None, "alert": "none"}
            self.last_speak = time.monotonic()
            return {"speak": "Hello from the server", "alert": "none"}

        def state(self):
            return {"node": "entrance", "marker": 0, "destination": None}

    print("navigator: canned fallback (server/nav.py not found)", flush=True)

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI()
navigator = Navigator()
lock = threading.Lock()  # one frame or command at a time; keeps the GPU model single-threaded
frames, busy_s, window_t0 = 0, 0.0, time.perf_counter()


@app.post("/frame")
def frame(image: UploadFile, heading: float = Form()):
    global frames, busy_s, window_t0
    jpeg = image.file.read()
    with lock:
        t = time.perf_counter()
        out = navigator.update(perceive(jpeg), heading)
        busy_s += time.perf_counter() - t
        frames += 1
        if frames == 20:
            now = time.perf_counter()
            print(f"{frames / (now - window_t0):.1f} fps, {busy_s / frames * 1000:.0f} ms/frame perceive+nav", flush=True)
            frames, busy_s, window_t0 = 0, 0.0, now
    return {"speak": out["speak"], "alert": out["alert"]}


@app.post("/command")
def command(text: str = Body(embed=True)):  # JSON {"text": "..."}
    print(f"command: {text!r}", flush=True)
    with lock:
        return {"speak": navigator.command(text)}


@app.get("/state")
def state():
    return navigator.state()


@app.get("/depth.jpg")
def depth():
    jpg = latest_depth_jpg()
    if jpg is None:
        raise HTTPException(404, "no frame yet")
    return Response(jpg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.get("/map", include_in_schema=False)
def map_slash():
    return RedirectResponse("/map/")  # the viewer loads ./app.js etc. relative to /map/


class NoStore(StaticFiles):  # phone page: always fetch the latest index.html, like web/dev_server.py
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-store"
        return response


app.mount("/map", StaticFiles(directory=ROOT / "demo", html=True), name="map")
app.mount("/", NoStore(directory=ROOT / "web", html=True), name="web")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)  # no access log: frames arrive every ~300 ms
