"""JabCross server: one FastAPI app for the phone page, the map viewer, and the perception API.

Run from the repo root: python server/app.py   then: cloudflared tunnel --url http://localhost:8000
"""

import time
from pathlib import Path

import cv2
import uvicorn
from fastapi import FastAPI, File, Form, Response, UploadFile
from fastapi.staticfiles import StaticFiles

import perception

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI()
last_line, last_line_t = None, 0.0


def obstacle_reply(p):
    """Stand-in for navigator.update(p, heading) until server/nav.py exists: obstacle warnings only."""
    global last_line, last_line_t
    if not p["view_ok"]:
        line, alert = "Camera blocked. Hold the phone flat against your chest.", "warn"
    elif p["obstacles"]["center"] < 1.0:
        side = "left" if p["obstacles"]["left"] > p["obstacles"]["right"] else "right"
        line, alert = f"Stop. Obstacle ahead. More space on your {side}.", "stop"
    else:
        return {"speak": None, "alert": "none"}
    if line == last_line and time.monotonic() - last_line_t < 3:  # never repeat a line within ~3 s
        line = None
    else:
        last_line, last_line_t = line, time.monotonic()
    return {"speak": line, "alert": alert}


# Plain def (not async): FastAPI runs it in a worker thread, so inference does not block other routes.
@app.post("/frame")
def frame(image: UploadFile = File(...), heading: float = Form(...)):
    p = perception.perceive(image.file.read())
    return {**obstacle_reply(p), "debug": p}


@app.post("/command")
def command(body: dict):
    return {"speak": f"Starting route to {body.get('text', '')}"}


@app.get("/state")
def state():
    return {"node": "entrance", "marker": 0, "destination": None}


@app.get("/depth.jpg")
def depth_jpg():
    if perception.latest_depth_image is None:
        return Response(status_code=204)
    jpeg = cv2.imencode(".jpg", perception.latest_depth_image)[1].tobytes()
    return Response(jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


app.mount("/map", StaticFiles(directory=ROOT / "demo", html=True), name="map")
app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
