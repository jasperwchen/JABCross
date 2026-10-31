# JabCross build plan

Three people, three pieces that meet at a small set of agreed interfaces. Agree on the interfaces
below in the first 10 minutes, then everyone can work against fakes until integration.

## How the pieces fit

```
Phone (web page, worn on chest)            Laptop (Python, FastAPI)
  camera frame + heading  --- POST /frame --->  perception.perceive(frame)   [A]
                                                nav.Navigator.update(...)    [B]
  speak text, play alert  <-- JSON reply ----
  voice transcript        --- POST /command ->  nav.Navigator.command(text)  [B]
  speak reply             <-- JSON reply ----
```

The phone reaches the laptop through an HTTPS tunnel (`cloudflared tunnel --url http://localhost:8000`);
phone browsers only allow camera access over HTTPS. FastAPI also serves the phone page.

## Repo layout

```
server/app.py        FastAPI routes, glue, serves web/              [A]
server/perception.py depth model, marker detection, Jev experiment  [A]
server/nav.py        routing + guidance logic                       [B]
server/map.json      traced map of the Grady route                  [B]
web/index.html       the phone page                                 [C]
requirements.txt
```

## Interfaces (the contract)

Conventions: distances in meters. Angles in degrees. Bearing and heading increase clockwise
(turning right increases them). Negative bearing = left of center.

**POST /frame**: multipart form, `image` (JPEG, ~640px wide) and `heading` (float, clockwise
degrees from the phone's gyroscope).
Returns `{"speak": str | null, "alert": "none" | "warn" | "stop", "debug": {...}}`

**POST /command**: JSON `{"text": "take me to radiology"}`
Returns `{"speak": "Starting route to Radiology. Turn right about 90 degrees."}`

**perception.perceive(jpeg_bytes) -> dict**
```
{
  "view_ok": true,                                        # false if lens covered or pointing at floor
  "obstacles": {"left": 2.4, "center": 0.9, "right": 3.1},  # nearest distance per third of the frame
  "markers": [{"id": 3, "distance_m": 2.1, "bearing_deg": -12.0}],
  "place": {"node": "j2", "confidence": 0.8}              # optional, Jev experiment only
}
```

**nav.Navigator**
- `command(text) -> str`: handles "take me to X", "where am I", "repeat", "stop", "cancel"
- `update(perception, heading) -> {"speak": str | None, "alert": str}`

**map.json**
```
{
  "nodes": {
    "entrance": {"name": "Main Entrance", "aliases": ["front door", "lobby"],
                 "marker": 0, "facing": 0, "x": 0, "y": 0},
    "j1":       {"name": "Hallway junction", "aliases": [], "marker": 1, "facing": 90, "x": 0, "y": 12}
  },
  "edges": [["entrance", "j1", 12]]
}
```
`x`, `y` in steps on the traced plan (map up = 0 degrees). Edge = [from, to, steps]. `facing` is
the map heading you face when looking straight at that node's marker; it lets nav re-anchor the
gyroscope every time a marker is seen.

## Person A: perception + server

- [ ] 0:00-0:30 FastAPI skeleton: `/frame` and `/command` return a canned `speak`, `web/` served
      statically. This unblocks C's end-to-end test.
- [ ] Depth: Depth Anything V2 Metric Indoor Small (Hugging Face transformers, Mac GPU via MPS).
      Nearest distance in left/center/right thirds, `view_ok` check. Measure frames per second.
- [ ] Markers: OpenCV ArUco detection, distance and bearing per marker. Generate and print one
      marker per map node.
- [ ] Jev experiment (only once the above works): confirm someone has an API key in the first 15
      minutes, or drop it. Choice question with the frame + nearby nodes as options. Test at the
      demo junctions; keep it only if it is right most of the time. Fallback if no key: the same
      question to Claude vision.
- [ ] Debug image of the depth map for the video.
- [ ] After freeze: one sourced statistic for the harm (blind patients and hospital wayfinding),
      draft the written submission answers.

## Person B: navigation

- [ ] 0:00-0:45 Pick a short route on the Grady ground floor (main entrance off Jesse Hill Jr.
      Drive, one or two turns, a department). Trace it into `map.json`. Room labels in the PDF are
      not machine-readable, so read them by eye. Hard stop at 45 minutes: switch to a mock plan.
- [ ] Navigator: route with shortest path, then guidance states:
      orient ("turn right about 30 degrees" until within ~15 degrees of the hallway direction),
      walk ("walk forward about N steps", corrections from marker bearing when one is visible),
      stop for obstacles (center < ~1 m: "stop, obstacle ahead, more space on your left"),
      arrive at node (marker < ~1.2 m: next leg or "you have arrived").
- [ ] Speech pacing: priority stop > obstacle > turn > info, and never repeat the same line within
      ~3 seconds, or the user drowns in audio.
- [ ] Test against fake perception dicts before A's real perception is ready.
- [ ] With C: lay out the venue route so its turns and distances match the traced slice.
- [ ] Stretch: map view page with a live dot on the Grady plan, for the video.

## Person C: phone + voice + video

- [ ] 0:00-0:30 Phone page behind the tunnel: one full-screen "tap to start" (grants camera,
      microphone, motion), sends a frame every ~300 ms to `/frame`, speaks `speak` with the
      browser's built-in speech. Checkpoint: phone speaks A's canned reply.
- [ ] Keep the screen awake (Wake Lock API); a locked screen kills the camera.
- [ ] Heading: device orientation events (iPhone needs a permission request on the start tap).
      Convert to clockwise degrees before sending.
- [ ] Voice control, so the app runs itself: on start, ask "Where would you like to go?", send the
      transcript to `/command`, start guidance automatically. Browser speech recognition
      (webkitSpeechRecognition); pause listening while the app is talking or it hears itself.
      If continuous listening is flaky on iPhone, fall back to "tap anywhere to talk".
- [ ] Alerts as audio tones (Web Audio). iPhone Safari does not support vibration.
- [ ] Staging: print department signs matching the Grady route, tape up markers from A.
- [ ] Lead filming and editing. Hook line first: "Google Maps for hospitals."

## Timeline

- 0:30 checkpoint: phone sends a frame through the tunnel and speaks the server's reply
- 2:00 integrate: real perception + real nav on the venue route
- 2:30 one full route works end to end
- 3:45 feature freeze
- 3:45-4:15 film (blindfolded walker, spotter, screen recordings of depth map and map view)
- 4:15-5:00 edit, written answers, final push
