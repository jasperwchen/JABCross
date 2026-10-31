# JabCross: Google Maps for hospitals

## Prompt (see PROMPT.md)

Accessibility tools for navigating the medical care system for disabled users.
Judged on: practicality/relevance, creativity/innovation, significance, technical complexity.

Format: 5-hour hackathon, 3 team members. Submission is a video + the codebase + a few written
questions. Judging happens through the video; the codebase only needs to be generally acceptable.

## Pitch

Google Maps for hospitals. A patient says where they need to go ("take me to Radiology") and the
app walks them there with spoken, real-time directions: "turn right about 30 degrees", "walk
forward about 12 steps", "stop", "obstacle ahead on your left", "you have arrived".

First focus: blind and low-vision patients. The phone is worn on the chest, camera facing forward.
A depth model watches the path ahead for obstacles and checks the camera has a usable view.

Decided:
- One core feature (hospital navigation), not a multi-feature hub
- No BetterBell code; accounts are hardcoded
- Security is out of scope (proof of concept)

## The hard problem: knowing where the user is

Indoors there is no GPS and no map, and depth detection alone does not say where you are.
Proposed approach:
- **Building map**: a hand-built graph of junctions and destinations. Each hallway edge stores a
  direction and an approximate step count.
- **Printed markers at each junction and destination** (ArUco codes: black-and-white squares that
  OpenCV can detect and measure). When the camera sees one, we know where the user is, how far
  away the marker is, and the angle to it, which drives "angle a bit left" corrections.
  Real-world precedent: NaviLens codes are already used in transit for blind riders.
- **Phone gyroscope** for turns between markers ("turn left 90 degrees" = change in heading).
- **Depth model** for obstacles and "bad view" warnings.

## Architecture

- **Phone (browser page, worn on chest)**: sends camera frames to the server, speaks
  instructions, vibrates on danger, reads the gyroscope, takes the destination by voice.
- **Laptop server (Python, FastAPI)**:
  - Depth model (Depth Anything V2 Metric Indoor, small) -> nearest obstacle in left / center / right
  - Marker detection (OpenCV ArUco) -> current position, distance and bearing to marker
  - Route planner + guidance logic -> next spoken instruction
- **HTTPS tunnel** (cloudflared or ngrok): phone browsers only allow camera access over HTTPS.

## Team split

- **A, perception**: depth model + marker detection, one endpoint that takes a frame and returns
  obstacles and markers seen.
- **B, navigation**: building map, routing, guidance logic, matching the spoken destination.
- **C, phone + demo**: phone page, tunnel, mapping the venue, printing markers and signs, video.

## Timeline

- 0:30 end-to-end spike: phone sends a frame, server replies, phone speaks it
- 2:30 one full route works (entrance -> one turn -> obstacle -> destination)
- 3:45 feature freeze
- 4:00-5:00 film and edit

## Demo plan

Stage the venue as a hospital: paper department signs, markers at junctions, one route with a turn
and a chair in the way. A blindfolded teammate wears the phone, with a spotter. In the edit, show
the depth map and a map view with the user's position next to the live footage.

## Not building (roadmap slide only)

Reviews, scheduling with a doctor, service requests, routing for other disabilities
(e.g. step-free routes for wheelchair users).
Stretch if ahead of schedule: destination suggested from a hardcoded appointment
("You have Radiology at 2pm. Go there?").
