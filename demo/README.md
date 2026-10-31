# Grady ground-floor demo

Run from the repository root:

    python -m http.server 8766 --bind 127.0.0.1 --directory demo

Open http://127.0.0.1:8766 in a modern browser. Dependencies are vendored, so no npm installation or internet is required.

Select Cashier (the demo route, two turns), Cafe or Lab waiting; simulate/pause/reset a walk, switch overhead/3D views, and toggle the original floor-plan overlay. Optional speech uses browser speech synthesis.

Outputs: grady-ground.glb (777 objects: walls, floors, doors, stairs, elevators and fixtures), grady-ground.json (geometry and the routing graph with aliases, marker facing and estimated steps, shared by the viewer and server/nav.py). Rebuild both with `python demo/build_model.py`; set `STEPS_PER_UNIT` there from the measured venue route.

Source: ground-floor GMH-G, PDF page 3; cropped entrance/lab area. The 75 room/area entries cover the entire displayed crop, including exam/consult rooms, toilets, staff rooms, north and west edge spaces, elevator cores and stairs. Outlines are simplified hand traces; furniture and heights are illustrative. The original SVG floor plan is cropped to the modeled area and enabled beneath the geometry by default. Room/facility labels reveal detail as you zoom; overlapping labels are suppressed and the selected destination takes priority. This is the displayed entrance/lab section, not the entire hospital ground floor. Routes have not been validated for public access or against current hospital conditions. Coordinates are uncalibrated drawing units, not meters or steps. GLB geometry matches every object in the browser model but does not embed the floor-plan image or interactive labels.

The amber beam is the walker's line of sight: rays at chest height, 70 degrees wide, stop at the first object tall enough to block them. Blue dots are the printed markers, placed on the first wall along each node's `facing` direction and shown through walls so they stay readable. A dot brightens and grows while it is inside the beam. Beam range is illustrative, not a measured detection range.

Integration: `window.jabCross.setMarker(markerId)` updates the position and facing to a known marker and pauses simulation. This is an adapter only; no camera, server polling, or live localization is connected.

Run `python demo/test_model.py` for coverage, GLB/viewer parity and route-wall intersection checks. Geometry is authored in `demo/model_geometry.py`; the build script preserves the existing marker IDs and navigation export.
