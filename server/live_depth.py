"""Live test of perception on the laptop webcam, before the phone is wired up.

Run from the repo root: python server/live_depth.py   (or pass a camera index / video file)
Each frame is resized to 640 px wide and JPEG-encoded like the phone page does, then passed to the
same perceive() the server uses. Left: camera with marker sightings. Right: depth map. Press q to quit.
"""

import sys
import time

import cv2
import numpy as np

import perception

FRAME_WIDTH = 640  # matches web/index.html

source = sys.argv[1] if len(sys.argv) > 1 else "0"
cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.resize(frame, (FRAME_WIDTH, round(frame.shape[0] * FRAME_WIDTH / frame.shape[1])))
    jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes()

    t0 = time.perf_counter()
    p = perception.perceive(jpeg)
    ms = (time.perf_counter() - t0) * 1000

    o = p["obstacles"]
    status = f"{ms:.0f} ms ({1000 / ms:.1f} fps)  L {o['left']:.2f}  C {o['center']:.2f}  R {o['right']:.2f} m"
    if not p["view_ok"]:
        status += "  VIEW BLOCKED"
    for m in p["markers"]:
        status += f"  marker {m['id']}: {m['distance_m']} m at {m['bearing_deg']} deg"
    print(status, flush=True)

    cv2.putText(frame, status[:60], (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    depth = cv2.imdecode(np.frombuffer(perception.latest_depth_jpg(), np.uint8), cv2.IMREAD_COLOR)
    cv2.imshow("JabCross perception (q to quit)", np.hstack([frame, depth]))
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
