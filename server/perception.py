"""Perception: one phone JPEG in, obstacles + view check + ArUco markers out (contract in PLAN.md).

Depth comes from the Ultralytics YOLO26 depth model. Live check on the laptop webcam: python server/live_depth.py
"""

import math

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from ultralytics.utils.plotting import colorize_depth

# ---- Depth: YOLO26 depth, output in meters, same size as the frame ----
DEVICE = "mps" if torch.backends.mps.is_available() else 0 if torch.cuda.is_available() else "cpu"
MODEL = YOLO("yolo26n-depth.pt")  # downloads on first use. yolo26m-depth.pt: ~20% less error, ~5x slower
# The model's default stretches every frame to a 768 px square, which made NYU Depth V2 indoor scenes read ~24% too
# far. Keeping the frame's own shape at 640 px on the long side cut that to ~9% and runs faster.
LONG_SIDE = 640
# Multiplies every depth reading: (tape-measured meters) / (reported meters), from facing a wall at 1, 2 and 3 m.
DEPTH_SCALE = 1.0
_latest_depth_jpg = None

# Camera on the chest at ~1.3 m. Level, the bottom quarter of a portrait frame sees floor 2-4 m away, but
# tilted down 30 deg it sees floor at 1.2-1.7 m, which reads as an obstacle. Skip those rows.
FLOOR_ROWS = 0.25
NEAR_PERCENTILE = 5  # "nearest" distance per third, ignoring the closest few percent as noise
MIN_CONTRAST = 10  # view_ok is false below this gray-level std: lens covered or pressed against something


def summarize(depth_m, gray):
    """-> (view_ok, {"left","center","right": nearest meters})."""
    view = depth_m[: int(depth_m.shape[0] * (1 - FLOOR_ROWS))]
    near = [round(float(np.percentile(part, NEAR_PERCENTILE)), 2) for part in np.array_split(view, 3, axis=1)]
    view_ok = bool(gray.std() > MIN_CONTRAST)  # the model still predicts a smooth ~1 m wall for a covered lens
    return view_ok, dict(zip(("left", "center", "right"), near))


def draw_depth(depth_m, obstacles):
    """Colorized depth (near = red, scaled per frame; the printed meters are absolute), zones above the floor band."""
    image = colorize_depth(depth_m)
    h, w = depth_m.shape
    floor_y = int(h * (1 - FLOOR_ROWS))
    cv2.line(image, (0, floor_y), (w, floor_y), (255, 255, 255), 2)
    for i, side in enumerate(("left", "center", "right")):
        x = w * i // 3
        if i:
            cv2.line(image, (x, 0), (x, floor_y), (255, 255, 255), 2)
        cv2.putText(image, f"{obstacles[side]:.1f} m", (x + 10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
    return image


# ---- Markers: ArUco DICT_4X4_50, IDs 0-11, printed 0.15 m (markers/make_markers.py) ----
MARKER_M = 0.15
# Field of view across the LONG image side (vertical, frames are portrait). iPhone main camera (26 mm equivalent)
# on a 4:3 frame is about 67 deg. Calibrate: stand a measured 2 m from a marker, read distance_m = d, then set
# FOV_LONG_DEG = 2 * degrees(atan(tan(radians(FOV_LONG_DEG) / 2) * d / 2)), repeat until d reads 2.0.
FOV_LONG_DEG = 67.0
# Corner order IPPE_SQUARE requires; ArUco returns corners TL, TR, BR, BL, which matches.
MARKER_OBJ = np.array([[-1, 1, 0], [1, 1, 0], [1, -1, 0], [-1, -1, 0]], np.float32) * (MARKER_M / 2)
_params = cv2.aruco.DetectorParameters()
_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX  # halves the range overestimate on small markers
_params.perspectiveRemovePixelPerCell = 8  # default 4; reads more far-away (small) markers
ARUCO = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), _params)


def detect_markers(gray):
    corners, ids, _ = ARUCO.detectMarkers(gray)
    if ids is None:
        return []
    h, w = gray.shape
    f = (max(w, h) / 2) / math.tan(math.radians(FOV_LONG_DEG) / 2)
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]], np.float64)
    out = []
    for c, i in zip(corners, ids.flatten()):
        if i > 11:
            continue
        _, _, t = cv2.solvePnP(MARKER_OBJ, c.reshape(4, 2).astype(np.float64), K, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
        tx, _, tz = t.flatten()
        # Straight-line range: does not assume the chest phone is held level (tilt mixes ty into tz).
        # Bearing: positive = right of center, negative = left.
        out.append({"id": int(i), "distance_m": round(float(np.linalg.norm(t)), 2),
                    "bearing_deg": round(math.degrees(math.atan2(tx, tz)), 1)})
    return out


def perceive(jpeg_bytes):
    global _latest_depth_jpg
    bgr = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    s = LONG_SIDE / max(bgr.shape[:2])
    imgsz = [round(bgr.shape[0] * s / 32) * 32, round(bgr.shape[1] * s / 32) * 32]  # model needs multiples of 32
    depth = MODEL.predict(bgr, imgsz=imgsz, device=DEVICE, verbose=False)[0].depth.data.cpu().numpy() * DEPTH_SCALE
    view_ok, obstacles = summarize(depth, gray)
    _latest_depth_jpg = cv2.imencode(".jpg", draw_depth(depth, obstacles))[1].tobytes()
    return {"view_ok": view_ok, "obstacles": obstacles, "markers": detect_markers(gray)}


def latest_depth_jpg():
    return _latest_depth_jpg
