# JabCross: Google Maps for hospitals

## Prompt (see PROMPT.md)

Accessibility tools for navigating the medical care system for disabled users.
Judged on: practicality/relevance, creativity/innovation, significance, technical complexity.

Format: 5-hour hackathon, 3 team members. Submission is a video + the codebase + a few written
questions. Judging happens through the video; the codebase only needs to be generally acceptable.

## Pitch

Google Maps for hospitals, built first for blind and low-vision patients. The patient says where
they need to go ("take me to Radiology") and the app walks them there with spoken, real-time
directions: "turn right about 30 degrees", "walk forward about 12 steps", "stop", "obstacle ahead
on your left", "you have arrived".

The phone is worn on the chest, camera facing forward. A depth model watches the path ahead for
obstacles and checks the camera has a usable view.

The app is fully voice-operated. After one tap to start (the phone requires a tap before it allows
camera, microphone and motion access), the user never has to find a button: they say where they
want to go and the app sets up and starts the route itself.

Decided:
- One core feature: hospital navigation for blind patients
- Voice-only operation is the one extension in scope
- No BetterBell code; accounts are hardcoded
- Map source: Grady Memorial Hospital base plans (GRADY-HOSPITAL-BASE-PLANS-02.17.22.pdf).
  If tracing it takes too long, use a mock floor plan; this is a proof of concept.
- Security is out of scope

## The hard problem: knowing where the user is

Indoors there is no GPS, and depth detection alone does not say where you are.

- **Building map**: a hand-traced graph of junctions and destinations from the Grady ground floor.
- **Printed markers at each junction and destination** (ArUco codes: black-and-white squares that
  OpenCV can detect and measure). Seeing one tells us where the user is, how far away the marker
  is, and the angle to it, which drives "angle a bit left" corrections and "stop" on arrival.
  Real-world precedent: NaviLens codes are already used in transit for blind riders.
- **Phone gyroscope** for turns between markers ("turn left 90 degrees" = change in heading).
- **Depth model** for obstacles and "bad view" warnings.
- **Markerless experiment (Jev)**: Jev is TypeSafe AI's decision model. It answers typed questions
  (pick one of N options, a score, yes/no) instead of writing text, and it has experimental image
  input. Ask it "which of these map locations is this camera looking at?" with the camera frame and
  the nearby junctions as options. If it is reliable at our demo junctions, we pitch "no stickers
  needed". Markers stay as the reliable path for the demo either way.

## Demo plan

Pick one short route on the Grady ground floor (main entrance, one or two turns, a department).
Recreate its turns at the venue with matching paper department signs and markers, so the map view
and the footage agree. A blindfolded teammate wears the phone, with a spotter. In the edit, show
the depth map and a live dot on the Grady plan next to the footage.

## Not building (roadmap slide only)

Reviews, scheduling with a doctor, service requests, routing for other disabilities
(e.g. step-free routes for wheelchair users).

Who does what, interfaces, and the timeline: see PLAN.md.
