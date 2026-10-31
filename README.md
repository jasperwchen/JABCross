# AcuPath

Indoor voice navigation for blind and low-vision hospital patients. A chest-worn phone
detects obstacles, reads printed location markers, and gives spoken turn-by-turn directions.

[Demo video](https://youtu.be/GIWPhk8ZWZ0) | [Web demo](https://jasperwchen.github.io/JABCross/) | [Devpost](https://devpost.com/software/acupath)

The web demo is a scripted simulation of the route. It does not connect to a phone.

## How it works

The patient taps once to start, taps the mic, and says a destination such as "take me to
radiology." AcuPath then speaks each step:

- **Directions:** "Turn right about 90 degrees," then "Walk forward about 7 steps."
- **Obstacles:** Within about 1 meter, a tone plays and the app says stop and which side is clearer.
- **Blocked camera:** The app asks the patient to adjust the phone.
- **Location:** Printed ArUco markers fix the patient's position and correct the compass.
- **Arrival:** The app announces each stop and the destination.

Patients can also say "where am I," "repeat," "stop," or "cancel."

```
PHONE (worn on chest)                  LAPTOP (FastAPI server behind an HTTPS tunnel)
  frame + heading  -- POST /frame ---->  perceive()  ->  navigator.update()
  speech + tone    <------ reply ------
  voice text       -- POST /command -->  navigator.command()
  speech           <------ reply ------
```

The phone sends a camera frame and compass heading about every 300 ms. The laptop uses the
Ultralytics YOLO26 depth model to measure the nearest obstacle on the left, center, and right,
and OpenCV to read markers. The navigator plans the shortest route on a map graph and chooses
one instruction, in this order: blocked camera, obstacle, turn, next marker, walk.

## Run it

Requires Python 3.13, `cloudflared`, and a phone. The first server start downloads the 12 MB
depth model.

```sh
python3 -m venv .venv
.venv/bin/pip install -r server/requirements.txt
.venv/bin/python server/app.py
```

In a second terminal, create the HTTPS address that the phone camera requires:

```sh
cloudflared tunnel --url http://localhost:8000
```

Open that address on the phone. The viewer is at `/map/` on the same address.

For the demo route, print `markers/markers.pdf` at actual size, so each black square measures
0.15 m. Place markers 0 to 3 at the Entrance, Lobby, Pharmacy, and X-ray stops.

Other commands:

```sh
.venv/bin/python server/live_depth.py   # Check depth and markers on the webcam
python3 web/dev_server.py               # Run the phone page with canned replies
python3 demo/build_model.py             # Rebuild the map from its generator
```

## Tests

```sh
python3 -m unittest discover -s server -p "test_*.py"
python3 -m unittest discover -s demo -p "test_*.py"
```

The tests use simulated camera readings to cover navigation, plus map and viewer geometry.
They do not cover a real phone, live perception, or a physical route.

## Repository

| Path | Contents |
| --- | --- |
| `server/` | FastAPI server, perception, and navigator |
| `web/` | Phone page in plain HTML and JavaScript |
| `demo/` | Map generators and Three.js viewer |
| `markers/` | Printable ArUco markers, IDs 0 to 11 |
| `floor-plan/` | Grady Memorial Hospital source plans |
| `docs/` | Build plan, project notes, and route sketch |

## Limitations

AcuPath is a six-hour hackathon prototype, not a medical or safety device.

- It has not been tested with blind or low-vision users.
- The demo is a staged four-stop route with estimated step counts.
- Depth distances are not calibrated against measured distances.
- The Grady map is illustrative and has not been validated for navigation.

## License

The code is available under the [MIT License](LICENSE). Three.js keeps its own license in
`demo/vendor/`. The MIT License does not cover the Grady floor plans or maps traced from them.

## Team

Team Jab+ (JabCross) from GSMST:

- Wei "Jasper" Chen
- Ayan Sandybayev
- Brian Li
