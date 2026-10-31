"""Perception: one phone JPEG in, obstacles + view check + ArUco markers out (contract in PLAN.md).

Benchmark on the laptop (first run downloads the depth model, ~100 MB):
    .venv/bin/python server/perception.py some_frame.jpg
"""
import math
import sys
import time

import cv2
import numpy as np
import torch
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

# ---- Depth: Depth Anything V2 Metric Indoor Small, output in meters ----
DEPTH_MODEL = "depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf"
device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
processor = model = None  # loaded on the first frame
_latest_depth_jpg = None


def estimate_depth(rgb):
    """RGB uint8 HxWx3 -> float32 HxW depth in meters, same size as the input."""
    global processor, model
    if model is None:
        processor = AutoImageProcessor.from_pretrained(DEPTH_MODEL)
        model = AutoModelForDepthEstimation.from_pretrained(DEPTH_MODEL).to(device).eval()
    inputs = processor(images=rgb, return_tensors="pt").to(device)
    with torch.inference_mode():
        out = model(**inputs)
    depth = processor.post_process_depth_estimation(out, target_sizes=[rgb.shape[:2]])[0]["predicted_depth"]
    return depth.float().cpu().numpy()


# Camera on the chest at ~1.3 m. Level, the bottom quarter of a portrait frame sees floor 2-4 m away, but
# tilted down 30 deg it sees floor at 1.2-1.7 m, which reads as an obstacle. Skip those rows.
FLOOR_ROWS = 0.25


def summarize(depth_m, gray):
    """-> (view_ok, {"left","center","right": nearest meters}), using the 5th percentile to ignore noisy pixels."""
    view = depth_m[: int(depth_m.shape[0] * (1 - FLOOR_ROWS))]
    near = [round(float(np.percentile(part, 5)), 2) for part in np.array_split(view, 3, axis=1)]
    # Covered lens: nearly everything closer than 0.3 m, or a black frame (the model may not call black "near").
    view_ok = bool((depth_m < 0.3).mean() < 0.85 and gray.mean() >= 20)
    return view_ok, dict(zip(("left", "center", "right"), near))


def colorize(depth_m):
    """Depth -> JPEG bytes. Fixed 0-5 m scale so colors are stable; near is bright yellow, far is black."""
    near = ((1 - np.clip(depth_m, 0, 5) / 5) * 255).astype(np.uint8)
    return cv2.imencode(".jpg", cv2.applyColorMap(near, cv2.COLORMAP_INFERNO))[1].tobytes()


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
    depth = estimate_depth(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    view_ok, obstacles = summarize(depth, gray)
    _latest_depth_jpg = colorize(depth)
    return {"view_ok": view_ok, "obstacles": obstacles, "markers": detect_markers(gray)}


def latest_depth_jpg():
    return _latest_depth_jpg


if __name__ == "__main__":
    jpeg = open(sys.argv[1], "rb").read()
    print(f"device: {device}")
    perceive(jpeg)  # warm-up (and first-run model download)
    t = time.perf_counter()
    for _ in range(10):
        result = perceive(jpeg)
    print(result)
    print(f"{(time.perf_counter() - t) / 10 * 1000:.0f} ms/frame, {10 / (time.perf_counter() - t):.1f} fps")
