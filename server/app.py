"""JabCross server: one FastAPI app for the phone page, the map viewer, and the perception API.

Run from the repo root: python server/app.py   then: cloudflared tunnel --url http://localhost:8000
"""

from pathlib import Path

import cv2
import uvicorn
from fastapi import FastAPI, File, Form, Response, UploadFile
from fastapi.staticfiles import StaticFiles

import perception
from nav import Navigator

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI()
navigator = Navigator()  # one user, one global navigator


# Plain def (not async): FastAPI runs it in a worker thread, so inference does not block other routes.
@app.post("/frame")
def frame(image: UploadFile = File(...), heading: float = Form(...)):
    p = perception.perceive(image.file.read())
    return {**navigator.update(p, heading), "debug": p}


@app.post("/command")
def command(body: dict):
    return {"speak": navigator.command(body.get("text", ""))}


@app.get("/state")
def state():
    return navigator.state()


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
