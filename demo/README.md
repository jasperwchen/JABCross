# AcuPath viewer

A Three.js viewer that simulates a walk along the demo route. It does not read the phone
camera or track the phone. Live version: https://jasperwchen.github.io/JABCross/

The viewer has two maps:

- **Hospital walkthrough** is the default: Entrance (marker 0), Lobby (1), Pharmacy (2), X-ray (3).
  Its hospital interior is illustrative.
- **Grady reference** (`?map=hospital`) is a simplified trace of the entrance and lab area on
  ground floor GMH-G. It is illustrative, and its distances are not meters or steps.

Each map offers 1st POV, 3D, and overhead views, with a walk you can pause and reset.

## Run

No install is needed. From the repository root:

```sh
python -m http.server 8766 --bind 127.0.0.1 --directory demo
```

Open http://127.0.0.1:8766. The server also serves the viewer at `/map/`.

## Build the maps

Edit the generators, not the generated JSON or GLB files.

| Command | Result |
| --- | --- |
| `python demo/build_viewer.py` | Rebuilds both maps in `demo/maps/` |
| `python demo/build_model.py` | Rebuilds the active café map that the server reads |
| `python demo/build_model.py --hospital` | Makes the Grady map active |

Restart the server after changing the active map. Route steps are set in
`demo/cafe_geometry.py`. Each of the three legs is about 5 m, estimated at 7 steps.

## Test

```sh
python -m unittest discover -s demo -p "test_*.py"
```

The tests check marker placement, route clearance, the spoken route with simulated camera
readings, and that the JSON and GLB models match.

## Deploy

Pushing a change under `demo/` to `main` publishes the viewer to GitHub Pages.

## Dependencies

Three.js r170 is included in `demo/vendor/`, so npm is not required.
