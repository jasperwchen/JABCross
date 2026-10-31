# AcuPath agent context

## Goal and pace

AcuPath is a six-hour, three-person hackathon project: "Google Maps for hospitals,"
starting with blind and low-vision patients. A phone worn on the chest sends camera
frames and heading to a laptop. The laptop detects obstacles and printed location
markers, calculates a route, and returns spoken directions. After one start tap,
the patient should be able to choose a destination and navigate by voice.

The submission is a video, this codebase, and written answers. Judging emphasizes
practicality, creativity, significance, and technical complexity. Prioritize a
reliable, demonstrable route and clear footage. Coding will be fast: use the
smallest working implementation, test the integration early, and avoid speculative
features, frameworks, broad refactors, and production infrastructure. Prefer Python
where practical; the phone page stays plain HTML/JavaScript.

## Read first and check the latest version

1. Read `docs/PLAN.md`: current owners, shared contracts, checklists, and timeline.
2. Read `docs/IDEA.md` for the agreed pitch and scope, and `docs/HG-PROMPT.md` for judging.
3. Read the handoff or README for the area you are changing. For the phone, use
   `docs/handoff_C_phone.md`; for the viewer, use `demo/README.md`.
4. Check `git status`, the branch, and recent commits before editing. Fetch the
   remote and compare with the upstream branch: teammates push frequently. On a
   clean, behind-only branch, use a fast-forward update. Preserve local/untracked
   work; do not reset, stash, overwrite, or resolve conflicting teammate changes
   blindly. Recheck before committing and pushing.
5. Before using or installing a dependency, model, SDK, or browser API, check the
   latest stable version and current official documentation. Compare with what is
   installed, pinned, or vendored here. Verify compatibility with the actual Python
   version and target phone. Do not rely on remembered API signatures or blindly
   upgrade working dependencies during the hackathon. Record any necessary version
   choice in the existing dependency file or relevant README. Do not install
   packages unless needed.

`docs/PLAN.md` is the source of truth for shared interfaces if another project document
disagrees. Files describe both plans and implemented work: inspect the current code
and test results before claiming something works. Keep this file aligned when the
architecture changes. `CLAUDE.md` points here to avoid two competing sets of rules.

## Scope, ownership, and repository map

| Owner | Area | Responsibility |
| --- | --- | --- |
| Brian (A) | `server/app.py`, `server/perception.py` | FastAPI server, depth, marker detection |
| Jasper (B) | `server/nav.py`, `demo/` | Navigation, map generation, viewer |
| Ayan (C) | `web/index.html`, `web/dev_server.py` | Phone, voice, tunnel, staging, video |

Respect the assigned area. Coordinate changes to another owner's files or any
shared endpoint/data shape with the user before implementing them.

- `docs/PLAN.md` contains the active per-person checklists; use those as milestones.
- `demo/` contains a working standalone Three.js viewer and simulated route, with
  vendored dependencies. `demo/build_model.py` generates `grady-ground.json` and
  `grady-ground.glb`. Edit the generator, not generated map data by hand.
- `markers/markers.pdf` contains ArUco IDs 0–11, dictionary `DICT_4X4_50`. Print at
  actual size; the black square must measure 0.15 m. `markers/make_markers.py`
  regenerates it using OpenCV and Pillow.
- `floor-plan/GRADY-HOSPITAL-BASE-PLANS-02.17.22.pdf` is the source floor plan. The viewer uses
  the entrance/lab crop of ground-floor GMH-G, PDF page 3.
- `docs/plans/grady-viewer.md` is the earlier viewer plan.
  `docs/brainstorm.md` is brainstorming.
  Consult these for background without overriding the current shared build plan.
- `web/` may contain in-progress local work. Inspect it without overwriting it.
  The phone mock server is independent of the planned real server.
- `server/` holds the real server (`app.py`), perception (`perception.py`: Ultralytics
  YOLO26 depth and ArUco markers), a webcam check of perception (`live_depth.py`), the
  navigator (`nav.py`), and dependencies in `requirements.txt`. Mac speed and distance
  accuracy still need checking on the laptop; do not assume live viewer integration
  exists merely because it appears in `docs/PLAN.md`.

No accounts, scheduling, reviews, caregiver requests, or additional disability
features are in scope. Jev markerless localization is optional, only after the
marker/depth route works; drop it if credentials or reliability are blockers.

## Shared integration contract

One laptop FastAPI server and one HTTPS tunnel serve everything. Register API
routes first, mount the viewer at `/map`, and mount the phone at `/` last. Keep
`/map/`'s trailing slash for relative asset URLs. Phone requests use relative URLs.

| Endpoint | Request / response |
| --- | --- |
| `GET /` | Phone page from `web/` |
| `GET /map/` | Viewer from `demo/` |
| `POST /frame` | Multipart `image` (JPEG, about 640 px wide), `heading` (clockwise degrees); returns `{"speak": null, "alert": "none"}` with speech text when needed and alert `none`, `warn`, or `stop` |
| `POST /command` | JSON `{"text": "take me to the lab"}`; returns `{"speak": "..."}` |
| `GET /state` | Navigator state, e.g. `{"node": "lobby", "marker": 1, "destination": "lab"}` |
| `GET /depth.jpg` | Latest depth frame as a color image |

`perceive(jpeg_bytes)` produces `view_ok` (boolean), `obstacles` (nearest meters in
`left`, `center`, `right`), and `markers` (list of `id`, `distance_m`, `bearing_deg`).
Optional Jev output is `place: {node, confidence}`. The planned `Navigator` exposes
`command(text) -> str`, `update(perception, heading) -> {speak, alert}`, and
`state() -> dict`. There is one global navigator for one user.

Geometry and guidance rules:

- Distances exchanged by perception are meters; angles are degrees, clockwise.
  Negative marker bearing means left of center.
- Map x points right and y points down. Hallway heading from a to b is
  `degrees(atan2(bx - ax, -(by - ay)))`, clockwise from map-up.
- Start at entrance, marker 0. A marker sighting overrides position. On seeing
  marker M at bearing b, map heading is `facing[M] - b`; store its offset from
  phone heading.
- `demo/grady-ground.json` is the shared map. The plan calls for destination
  `aliases`, node `facing`, and edge step counts. The initial generator still uses
  uncalibrated drawing distances as edge weights. Inspect its current format;
  never speak those values as meters or steps. Measure the staged venue route.
- Guidance priority: blocked camera, center obstacle under about 1 m, turn error
  over about 15 degrees, next marker under about 1.2 m/arrival, then forward steps.
  Do not repeat the same line within about 3 seconds.
- The viewer exposes `window.jabCross.setMarker(markerId)` as an adapter. The current
  video uses a scripted hospital walkthrough alongside separate real phone footage;
  live state/depth polling is deferred. The café viewer defaults to first person,
  with countdown, pace, pause/reset and overhead/3D controls. Hospital scenery is
  generated only into `demo/maps/cafe/`; the phone's active map stays unchanged.

## Phone constraints and demo validation

Test on the real phone early, initially assuming iPhone Safari. Camera access
requires HTTPS on the phone. A single real start button must unlock camera,
motion permission where required, speech, and Web Audio in its tap handler.
Use screen wake lock and reacquire it when returning to the page.

Send one frame at a time, no faster than about 300 ms; do not queue requests behind
slow inference. Use `webkitCompassHeading` where available, otherwise convert
alpha to clockwise heading. Test while the phone is upright against the chest;
if unstable, follow the motion fallback in the phone handoff and check its sign.
Pause recognition while speaking so the app does not transcribe itself. Fall back
to tap-to-talk if continuous recognition fails. Stop alerts interrupt speech;
ordinary guidance keeps at most one pending line. Use audio tones for alerts;
iPhone Safari does not provide vibration.

Run from the repository root (commands assume the relevant files are present):

```sh
# Standalone viewer; no npm install required.
python3 -m http.server 8766 --bind 127.0.0.1 --directory demo
# Real server on port 8000 (first start downloads the 12 MB yolo26n-depth.pt).
python3 -m venv .venv && .venv/bin/pip install -r server/requirements.txt
.venv/bin/python server/app.py
# Depth + marker check on the laptop webcam (or a video file path), with ms per frame.
.venv/bin/python server/live_depth.py
# Phone mock, when the real server is not needed.
python3 web/dev_server.py
# Expose whichever server is listening on port 8000 to the phone over HTTPS.
cloudflared tunnel --url http://localhost:8000
# Rebuild map/GLB only when intentionally changing the generator.
python3 demo/build_model.py
```

The mock implements canned `/frame` and `/command` replies, not perception. Use
fake perception dictionaries to test navigation independently. No shared dependency
manifest or automated test suite was present when this file was written; inspect
the latest checkout for additions. Run checks suited to the changed code, then
test the actual interaction. Report mocked, desktop-only, or untested behavior.

Milestones: phone speaks a server reply at 0:30; venue route and markers at 1:00;
real perception/navigation integrated at 2:00; full route at 2:30; feature freeze
at 3:45; film until 4:15; edit, written answers, final push by 5:00. These are
elapsed hackathon times. Follow current team priorities if they have changed.
Film a staged route with a spotter. Grady geometry is illustrative and has not
been validated for real hospital navigation.

## Working rules and finishing work

- Be concise and factual. State assumptions. Ask only when required information,
  authority, or a consequential decision is missing; proceed on routine work.
- Before substantial or high-risk implementation, summarize the approach and
  get confirmation. Keep edits surgical and preserve concurrent teammate changes.
- Never include secrets, modify `.env` files, change production configuration,
  delete major files, or restructure the project without authorization. Production
  security hardening is outside the hackathon scope; keep basic input handling and
  secret protection.
- If an unrelated issue appears outside the active checklist item, surface it and
  ask before fixing it or expanding the checklist.
- For larger, bug-sensitive changes, run relevant tests and use both code-critic
  and pentest-reviewer agents. Use pentest-reviewer for security-sensitive changes.
  Simple documentation changes do not require reviewer agents.
- Mark a checklist item done only after its required implementation, checks, and
  reviews pass. Append a brief plain-English entry to `docs/jabcross_a5logs.txt`,
  which is local and already gitignored. Do not add that log to commits.
- Commit only the intended files. Do not automatically commit or push: an explicit
  request authorizes the requested action; close-item authorizes a local commit,
  not a push. Never force-push to work around concurrent commits.
- If normal Git authentication fails here, the phone handoff documents this
  alternative: `git -c credential.helper= -c credential.helper='!gh auth git-credential' push origin main`.
