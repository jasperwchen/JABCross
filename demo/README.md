# Grady ground-floor demo

Run from the repository root:

    python -m http.server 8766 --bind 127.0.0.1 --directory demo

Open http://127.0.0.1:8766 in a modern browser. Dependencies are vendored, so no npm installation or internet is required.

Select Lab waiting, Cafe or Cashier; simulate/pause/reset a walk, switch overhead/3D views, and toggle the original floor-plan overlay. Optional speech uses browser speech synthesis.

Outputs: grady-ground.glb (70 simplified walls and floor), grady-ground.json (geometry and illustrative routing graph). Rebuild both with `python demo/build_model.py`.

Source: ground-floor GMH-G, PDF page 3; cropped entrance/lab area. Rooms are simplified rectangular traces. The image retains architectural detail beyond the modeled walls. Routes have not been validated for public access or against current hospital conditions. Coordinates are uncalibrated drawing units, not meters or steps. GLB geometry matches the simplified walls but does not embed the floor-plan image or interactive labels.

Integration: `window.jabCross.setMarker(markerId)` updates the position to a known marker and pauses simulation. This is an adapter only; no camera, server polling, or live localization is connected. Convert coordinates and validate the graph before using the team's server/map.json contract.

Validation: JavaScript syntax, graph connectivity and GLB header/scene checks passed. Browser rendering and simulation progress checked in the Codex browser.
