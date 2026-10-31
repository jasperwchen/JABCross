# AcuPath build plan

| Role | Who | Owns |
|---|---|---|
| A: perception + server | Brian | `server/app.py`, `server/perception.py` |
| B: navigation + map | Jasper | `server/nav.py`, `demo/` (map data + 3D viewer) |
| C: phone + voice + video | Ayan | `web/index.html`, tunnel, staging, video edit |

## Do this now

Current video plan: record the real phone camera demo beside a separately scripted
hospital walkthrough. The website does not track the phone live. Its default café
route uses hospital scenery and first-person/3D/overhead views, with a countdown,
pace control and pause/reset for filming. The phone map and API stay unchanged.

- [x] Hospital walkthrough: first-person scene, filming controls, geometry checks and viewer reviews complete.
- [x] Hospital visual polish: lighting/shadows, materials, mounted signs and room details; geometry checks, browser route and both reviews passed.
- [x] Publish the updated viewer to GitHub Pages.

- **Jasper**: pause the viewer. Start `server/nav.py` (the navigator). Without it there is no product.
- **Brian**: `pip install -r server/requirements.txt`, then `python server/live_depth.py` to check depth
  and markers on the laptop webcam, then `python server/app.py` behind the tunnel.
- **Ayan**: `brew install cloudflared`, then the phone page.
- **Everyone, before 1:00**: walk the venue hallways together and pick the demo route.

## Already done

- 12 printed markers, IDs 0-11 (`markers/markers.pdf`)
- 3D Grady viewer with simulated walk (`demo/`, Jasper)

---

## How it fits

```
PHONE (worn on chest)                  LAPTOP (one FastAPI server, one tunnel)
  frame + heading  -- POST /frame ---->  perceive()  [Brian]  ->  navigator.update()  [Jasper]
  speak + tone     <------ reply ------
  voice text       -- POST /command -->  navigator.command()  [Jasper]
  speak            <------ reply ------

LAPTOP SCREEN (for the video)
  /map/ viewer  --> scripted hospital route, cued alongside phone footage
                   independent countdown, pace, pause and reset
```

## Endpoints (all on the one server)

| Route | Owner | What it does |
|---|---|---|
| `/` | Brian serves, Ayan builds | Phone page (`web/`) |
| `/map/` | Brian serves, Jasper builds | 3D viewer (`demo/`). Keep the trailing slash: the viewer loads files by relative path. |
| `POST /frame` | Brian | Form: `image` (JPEG, ~640 px wide), `heading` (float). Returns `{"speak": str or null, "alert": "none" or "warn" or "stop"}` |
| `POST /command` | Brian | JSON `{"text": "take me to the lab"}`. Returns `{"speak": "..."}` |
| `GET /state` | Brian | `{"node": "lobby", "marker": 1, "destination": "lab"}` from the navigator |
| `GET /depth.jpg` | Brian | Latest depth map as a color image |

FastAPI tip: register the API routes first, mount `/map` (from `demo/`), and mount `/` (from `web/`) last.

## Shared rules

- **Units**: distances in meters, angles in degrees.
- **Direction**: heading and bearing increase clockwise. Negative bearing = left of center.
- **Map axes**: the map's y axis points DOWN. Map heading of a hallway from a to b is
  `atan2(bx - ax, -(by - ay))` in degrees, clockwise from map-up. Get this wrong and every turn is mirrored.
- **Start**: the user starts at the entrance (marker 0), facing it. Any marker sighting overrides.
- **Re-anchoring the gyroscope**: when marker M is seen at bearing b, the user's map heading is
  `facing[M] - b`. Store the offset between that and the phone's gyro heading.
- **One user**: one global navigator in `app.py`. No accounts.

## The one map: `demo/grady-ground.json`

The default build is now the staged cafeteria map from the screenshot and `AGENT-HANDOFF.md`:
Entrance (0) -> Lobby (1) -> Pharmacy (2) -> X-ray (3), east then north then north.
Each leg currently uses 7 estimated steps (about 5 m); venue counts and real-phone validation remain outstanding.
Run `python demo/build_model.py` for the café, or `--hospital` to restore the original Grady reference.
Both the viewer and server use this same filename; restart the server after changing maps.

Both the viewer and the navigator read this file. Never edit it by hand; edit `demo/build_model.py`
and rerun it. Jasper adds three fields:

- **`aliases`** on each destination: what a person might say. `"lab": ["lab", "blood work", "lab waiting"]`
- **`facing`** on each node: the map heading you face when looking straight at that node's marker.
- **`steps`** as the third value of each edge, measured by walking the venue route. Placeholder 10
  until measured. The current third value is drawing units (one corridor is 1,160), useless for speech.
  The viewer's shortest-path code uses this value too; it still works.

## Data the code passes around

`perceive(jpeg_bytes)` returns:
```
{
  "view_ok": true,                                          # false = lens covered / pointing at floor
  "obstacles": {"left": 2.4, "center": 0.9, "right": 3.1},  # nearest meters per third of the frame
  "markers": [{"id": 3, "distance_m": 2.1, "bearing_deg": -12.0}],
  "place": {"node": "j2", "confidence": 0.8}                # optional, Jev only
}
```

`Navigator` (in `server/nav.py`):
- `command(text) -> str`: "take me to X", "where am I", "repeat", "stop", "cancel"
- `update(perception, heading) -> {"speak": str or None, "alert": str}`
- `state() -> dict`: what `GET /state` returns

---

## Brian (A): perception + server

- [x] **By 0:30**: FastAPI skeleton with all routes above. `/frame` and `/command` return a canned
      `speak`. Serves `web/` and `demo/`. This unblocks Ayan's first test.
- [x] **Depth**: Ultralytics YOLO26 depth (`yolo26n-depth.pt`, Mac GPU via MPS). Nearest meters in
      left / center / right thirds, above the bottom quarter (floor). Measure frames per second on the Mac.
      Frames keep their shape (stretching to a square read ~24% too far on NYU Depth V2). Check meters against
      a tape measure with `server/live_depth.py`, then set `DEPTH_SCALE` in `server/perception.py`.
- [x] **`view_ok`**: false when the frame is nearly uniform (lens covered). The depth model alone
      cannot tell: it predicts a smooth ~1 m wall for a covered lens.
- [x] **Markers**: OpenCV ArUco, dictionary `DICT_4X4_50`, printed side **0.15 m**. Return distance
      and bearing per marker.
- [x] **`/depth.jpg`**: save the latest depth frame as a color image.
- [ ] **Jev (only after the above works)**: confirm someone has an API key in the first 15 min, or
      drop it. Ask "which of these nearby junctions is this?" with the frame. Keep only if mostly
      right at the demo junctions. No key: ask Claude vision the same question.
- [ ] **After freeze**: one sourced statistic on blind patients and hospital wayfinding. Draft the
      written submission answers.

## Jasper (B): navigation + map

- [x] **Start position + routing**: start at entrance (marker 0); shortest path to the destination
      matched from `aliases`.
- [x] **Guidance, in this priority order** (highest wins when several apply):
  1. `view_ok` false: "Camera blocked. Hold the phone flat against your chest."
  2. Center obstacle under ~1 m: "Stop. Obstacle ahead. More space on your left."
  3. Facing more than ~15 degrees off the hallway: "Turn right about 30 degrees."
  4. Marker of the next node under ~1.2 m: next leg, or "You have arrived at the lab."
  5. Walking: "Walk forward about 12 steps", with small corrections from marker bearing.
- [x] **Pacing**: never repeat the same line within ~3 s. The user must not drown in audio.
- [x] **Test without Brian**: feed fake perception dicts until real perception lands.
- [x] **Map fields**: add `aliases`, `facing`, `steps` in `build_model.py`.
- [ ] **By 1:00, with Ayan**: adjust the chosen route's node positions so its turns match the venue's
      hallways. The navigator takes turn angles from the map, so a mismatch gives wrong directions on camera.
- [ ] **Viewer, live (deferred)**: live phone tracking is deferred; the video uses a
      separate scripted route viewer alongside real phone footage.

## Ayan (C): phone + voice + video

- [ ] **By 0:30**: phone page behind the tunnel (`cloudflared tunnel --url http://localhost:8000`).
      One full-screen "tap to start" (grants camera, mic, motion). Send a frame every ~300 ms to
      `/frame`, speak `speak` with browser speech. **Checkpoint: the phone speaks Brian's canned reply.**
- [x] **Screen awake**: Wake Lock API. A locked screen kills the camera.
- [x] **Heading**: device orientation events (iPhone needs a permission request on the start tap).
      Convert to clockwise degrees before sending.
- [x] **Voice, so the app runs itself**: on start say "Where would you like to go?", send the
      transcript to `/command`, guidance starts automatically. Pause listening while the app talks,
      or it hears itself. If continuous listening is flaky on iPhone, use "tap anywhere to talk".
- [x] **Alerts as tones** (Web Audio). iPhone Safari cannot vibrate.
- [ ] **By 1:00, with Jasper**: pick the venue route. Then print department signs that match it and
      tape markers at chest height (write the location on each sheet).
- [ ] **Video**: lead filming and the edit. Open with "Google Maps for hospitals."

---

## Timeline

| Time | Milestone |
|---|---|
| 0:30 | Phone speaks the server's canned reply through the tunnel |
| 1:00 | Venue route picked, map adjusted, markers taped up |
| 2:00 | Real perception + real navigator wired together |
| 2:30 | One full route works end to end |
| 3:45 | **Feature freeze** |
| 3:45-4:15 | Film: blindfolded walker + spotter, screen recording of `/map/` |
| 4:15-5:00 | Edit, written answers, final push |

