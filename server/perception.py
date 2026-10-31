"""Perception for JabCross: obstacle distances from the YOLO26 depth model and ArUco marker sightings.

perceive(jpeg_bytes) returns the dict defined in PLAN.md. latest_depth_image holds the last colorized
depth map (BGR) for GET /depth.jpg and the live test window.
"""

import math

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from ultralytics.utils.plotting import colorize_depth

DEVICE = "mps" if torch.backends.mps.is_available() else 0 if torch.cuda.is_available() else "cpu"
MODEL = YOLO("yolo26n-depth.pt")  # downloads on first use; predicts at its trained 768 px. s/m/l/x: slower, more accurate

BLOCKED_M = 0.3  # view_ok is false when most of the frame is closer than this (lens covered)
BLOCKED_FRACTION = 0.8
DARK_LEVEL = 15  # mean gray level below this also counts as a covered lens
NEAR_PERCENTILE = 5  # "nearest" distance per third, ignoring the closest few percent as noise

MARKER_SIDE_M = 0.15  # printed black square, markers/markers.pdf
FOCAL_PER_LONG_SIDE = 0.75  # focal length in pixels / long frame side; iPhone main camera (~67 deg across)
ARUCO = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50))

latest_depth_image = None


def perceive(jpeg_bytes):
    """Return view_ok, nearest obstacle meters per third (left, center, right), and visible markers."""
    global latest_depth_image
    frame = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    result = MODEL.predict(frame, device=DEVICE, verbose=False)[0]
    depth = result.depth.data.cpu().numpy()  # (H, W) meters, same size as the frame

    thirds = np.array_split(depth, 3, axis=1)
    obstacles = {
        side: round(float(np.percentile(third, NEAR_PERCENTILE)), 2)
        for side, third in zip(("left", "center", "right"), thirds)
    }
    view_ok = bool(gray.mean() > DARK_LEVEL and (depth < BLOCKED_M).mean() < BLOCKED_FRACTION)

    latest_depth_image = draw_depth(depth, obstacles)
    return {"view_ok": view_ok, "obstacles": obstacles, "markers": find_markers(gray)}


def find_markers(gray):
    """Distance and bearing of each ArUco marker, from its pixel size with a pinhole camera model."""
    h, w = gray.shape
    focal = FOCAL_PER_LONG_SIDE * max(h, w)
    corners, ids, _ = ARUCO.detectMarkers(gray)
    markers = []
    for quad, marker_id in zip(corners, [] if ids is None else ids.flatten()):
        quad = quad.reshape(4, 2)
        side_px = max(np.linalg.norm(quad - np.roll(quad, 1, axis=0), axis=1))  # longest edge resists tilt
        markers.append(
            {
                "id": int(marker_id),
                "distance_m": round(focal * MARKER_SIDE_M / side_px, 2),
                "bearing_deg": round(math.degrees(math.atan((quad[:, 0].mean() - w / 2) / focal)), 1),
            }
        )
    return markers


def draw_depth(depth, obstacles):
    """Colorized depth (near = warm) with the three obstacle zones and their nearest distances."""
    image = colorize_depth(depth)
    h, w = depth.shape
    for i, side in enumerate(("left", "center", "right")):
        x = w * i // 3
        if i:
            cv2.line(image, (x, 0), (x, h), (255, 255, 255), 2)
        cv2.putText(image, f"{obstacles[side]:.1f} m", (x + 10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
    return image
