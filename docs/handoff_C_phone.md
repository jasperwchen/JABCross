# Handoff: Person C (Ayan) - phone page

You are building Ayan's part of AcuPath, a 5-hour hackathon project. Start immediately; the
team is already building. Read `PLAN.md` (the build plan and the contract between the three
pieces) and `IDEA.md` (the pitch) first. If this doc and `PLAN.md` disagree, `PLAN.md` wins.

## The product in one paragraph

"Google Maps for hospitals" for blind patients. The patient wears a phone on their chest, camera
facing forward, and says where they want to go. A laptop server runs a depth model (obstacles)
and detects printed markers taped at hallway junctions (position), then replies with spoken
directions: "turn right about 30 degrees", "walk forward about 12 steps", "stop, obstacle ahead".
Judging is by video, so it must work reliably on camera; code quality only needs to be acceptable.
Security is out of scope.

## Your scope

You own `web/` only. The phone page is `web/index.html`: one file, plain HTML + JS, no build step,
no frameworks. The server serves it at `/`.

Do not edit `server/` (Brian) or `demo/` (Jasper). Do not change the endpoints or data shapes in
`PLAN.md` without telling Ayan, because two other people code against them.

## The contract you call

- `POST /frame`: multipart form, `image` (JPEG, ~640 px wide) and `heading` (float, degrees,
  clockwise). Returns `{"speak": str or null, "alert": "none" | "warn" | "stop"}`.
- `POST /command`: JSON `{"text": "<what the user said>"}`. Returns `{"speak": "..."}`.

Use relative URLs (`/frame`, `/command`). The page is served by the same server, so no CORS.

## Build order

1. **Mock server, so you are not blocked on Brian.** `web/dev_server.py`, Python standard library
   only (`http.server`). Serve files from `web/` on port 8000. `POST /frame` returns a canned
   `{"speak": "Hello from the mock server", "alert": "none"}` (but only every ~5 s, `null`
   otherwise, so you can hear pacing). `POST /command` echoes `{"speak": "Starting route to <text>"}`.
   Swap to Brian's real server later by pointing the tunnel at it. Nothing else changes.
2. **Tunnel**: `cloudflared tunnel --url http://localhost:8000` (Ayan may need
   `brew install cloudflared`). Phone browsers only allow the camera over HTTPS; the tunnel URL is HTTPS.
3. **Start screen**: one full-screen button, "Tap to start". It must work with VoiceOver on
   (double-tap activates a focused button, so a real `<button>` with a clear label works). In that
   ONE tap handler, unlock everything iPhone gates behind a user gesture:
   - camera: `getUserMedia({video: {facingMode: "environment"}})`
   - motion: `DeviceOrientationEvent.requestPermission()` (exists on iPhone only; skip if undefined)
   - speech output: speak a short utterance ("Starting") inside the handler
   - tones: create and `resume()` an `AudioContext`
   - screen: `navigator.wakeLock.request("screen")`, and re-request on `visibilitychange`.
     A locked screen kills the camera.
4. **Frame loop**: draw the video to a canvas 640 px wide, `toBlob("image/jpeg", 0.7)`, POST to
   `/frame` with the current heading. Send the next frame only after the previous reply returns,
   and no more often than every ~300 ms, so requests never pile up behind a slow server.
5. **Speech out**: speak `speak` when non-null with `speechSynthesis`.
   - `alert == "stop"`: cancel whatever is playing and speak immediately.
   - otherwise: if already speaking, hold the new line in one pending slot (newest replaces older);
     speak it when the current line ends. The server handles repeat-pacing; don't add more.
6. **Tones** (Web Audio oscillator): `warn` = one short beep, `stop` = three fast high beeps.
   iPhone Safari has no vibration API, so tones are the only non-speech alert.
7. **Heading**: from `deviceorientation`. Use `event.webkitCompassHeading` when present (iPhone,
   already clockwise), else `(360 - event.alpha) % 360` (alpha runs counterclockwise).
   **Test it with the phone held upright on the chest**: turn your body 90 degrees right and check
   the value rises by ~90. Orientation readings can go unstable on an upright phone. If they do,
   integrate `devicemotion` `rotationRate.gamma` (rotation around the phone's long axis) over time
   instead, and check the sign. The server re-anchors heading whenever a marker is seen, so a
   consistent relative heading is enough; absolute north does not matter.
8. **Voice control, so the app runs itself**: after start, speak "Where would you like to go?",
   then listen with `webkitSpeechRecognition`. Send the final transcript to `POST /command` and
   speak the reply. Keep listening during navigation for "where am I", "repeat", "stop", "cancel"
   (just forward every final transcript to `/command`; the server parses it).
   - Stop recognition while the app is speaking and restart after, or it transcribes itself.
   - If continuous listening is flaky on iPhone, switch to: tap anywhere on the screen to talk.
9. **Debug strip**: small text at the bottom with last `speak`, heading, and round-trip ms. Useful
   while building and in the video's screen recording.

## Done means

- On Ayan's phone (assume iPhone Safari; confirm with Ayan), through the tunnel, against the mock:
  tap once, hear "Where would you like to go?", say "the lab", hear "Starting route to the lab",
  then hear the mock's line every ~5 s while frames flow, with heading in the debug strip
  changing correctly as you turn.
- Against Brian's real server: the same flow with real directions. This is the 0:30 checkpoint in
  `PLAN.md`; report to Ayan as soon as the phone speaks a reply from the real server.

## Things that will bite

- Test on the real phone early. iPhone audio (speech recognition + speech synthesis + Web Audio
  at once) is where this breaks, and desktop Chrome hides it.
- `getUserMedia`, motion permission, speech and audio all fail silently without the user gesture.
- Teammates push often. `git pull` before editing. Commit only your `web/` files.
- Plain `git push` fails on this machine (no stored GitHub login). Push with:
  `git -c credential.helper= -c credential.helper='!gh auth git-credential' push origin main`
- Append a short plain-English entry to `docs/jabcross_a5logs.txt` (local, gitignored) when each
  checklist item in `PLAN.md` under "Ayan (C)" is done, and tick it in `PLAN.md`.

## After the phone page works (from PLAN.md, Ayan's own tasks, not yours)

Picking the venue route with Jasper, printing signs, taping markers, filming and editing. Help if
asked (e.g. a sign-printing PDF), but don't start these on your own.
