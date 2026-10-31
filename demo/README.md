# Hospital and GSMST cafeteria viewer

Public viewer: https://jabcross-gsmst-cafeteria.purplegull36.chatgpt.site

Use the Hospital walkthrough and Grady reference tabs to switch maps. The hospital-styled café route is now the default; `?map=hospital` opens the Grady reference. Both support destination selection and simulated walking. The viewer is a scripted simulation, separate from the real phone camera demo. The existing public URL has NOT yet received the first-person update: this account has no Sites editor access. The latest prepared assets are in `sites/gsmst-viewer/dist` after packaging.

Build both viewer maps with `python demo/build_viewer.py`. The phone server still reads the active café map at `demo/grady-ground.json`; regenerate that separately with `python demo/build_model.py` when calibrating. `python demo/package_viewer.py` always rebuilds both viewer maps and copies only public runtime assets into `sites/gsmst-viewer/dist` for Sites deployment. Site identity is saved in `sites/gsmst-viewer/.openai/hosting.json`.

# Cafeteria route demo

Run from the repository root:

    python -m http.server 8766 --bind 127.0.0.1 --directory demo

Open http://127.0.0.1:8766 in a modern browser. Dependencies are vendored, so no npm installation or internet is required.

The hospital walkthrough recreates the four pillars in `cafe-route-sketch.png`, using the final printed signs in `AGENT-HANDOFF.md`: **Entrance (0), Lobby (1), Pharmacy (2), X-ray (3)**. X-ray is selected initially; Pharmacy is the shorter destination. The handoff's X-ray name replaces the sketch's handwritten Lab; voice commands for lab still work.

Start south of marker 0 facing map north. Turn right 90 degrees toward marker 1, left 90 degrees toward marker 2, then continue north toward marker 3. The markers are on pillar faces south / west / south / south. The route stays beside the pillars; it does not pass through their centers. Both viewer and navigator use the same graph. Three roughly 5 m legs currently have **7 estimated steps each**; measure and update these values in `demo/cafe_geometry.py` before filming. Pillar sizes, clearances and drawing scale are illustrative. Confirm real marker visibility and turns on the phone with a spotter.

Rebuild the active café JSON and matching GLB with `python demo/build_model.py`. Keep the existing `grady-ground.json` and `.glb` filenames for server compatibility. The café generator is `demo/cafe_geometry.py`. The original hospital generator and geometry remain available with `python demo/build_model.py --hospital`; this replaces the active map, so restart the server and reload the viewer afterward. Run the default build again to return to the café. Use `--output-dir PATH` to generate either map elsewhere without changing the active map.

The viewer offers first-person/overhead/3D views, scripted playback/pause/reset, optional speech, route progress and labeled pillars. The café viewer adds enclosing hospital walls, a ceiling, lights, doors, waiting chairs, reception and department signage. This interior is illustrative; it is not a reconstruction of the real café or Grady. `hospital_interior.py` decorates only the viewer export; the phone map and navigation remain unchanged. It starts facing marker 0, rotates before walking and announces turns and estimated steps. The hospital SVG overlay is hidden for café staging. Vendored Three.js r170 is retained without an upgrade; no new packages are required. Latest upstream is r187; r170 remains installed to avoid an unnecessary upgrade. Its renderer/camera/geometry and CanvasTexture APIs were checked against the [official documentation](https://threejs.org/docs/).

Run `python demo/test_interior.py` for viewer route clearance, unchanged phone contract and exported model parity. Run `python demo/test_cafe.py`, `python demo/test_model.py`, and `python -m unittest discover -s server -p test_nav.py`. These cover café marker faces, route clearance, aliases and the complete spoken route using fake perception; GLB parity; and existing hospital navigator regressions using a temporary generated hospital map. They do not validate the physical route, actual phone compass or live perception.

## Original hospital reference

Source: ground-floor GMH-G, PDF page 3; cropped entrance/lab area. The 75 room/area entries cover the entire displayed crop, including exam/consult rooms, toilets, staff rooms, north and west edge spaces, elevator cores and stairs. Outlines are simplified hand traces; furniture and heights are illustrative. The original SVG floor plan is cropped to the modeled area and enabled beneath the geometry by default. Room/facility labels reveal detail as you zoom; overlapping labels are suppressed and the selected destination takes priority. This is the displayed entrance/lab section, not the entire hospital ground floor. Routes have not been validated for public access or against current hospital conditions. Coordinates are uncalibrated drawing units, not meters or steps. GLB geometry matches every object in the browser model but does not embed the floor-plan image or interactive labels.

The amber beam is the walker's line of sight: rays at chest height, 70 degrees wide, stop at the first object tall enough to block them. Blue dots are the printed markers, placed on the first wall along each node's `facing` direction and shown through walls so they stay readable. A dot brightens and grows while it is inside the beam. Beam range is illustrative, not a measured detection range.

Integration: `window.jabCross.setMarker(markerId)` updates the position and facing to a known marker and pauses simulation. This is an adapter only; no camera, server polling, or live localization is connected.

Run `python demo/test_model.py` for active-map coverage, GLB/viewer parity and route-wall intersection checks. Geometry is authored in `demo/model_geometry.py`; the build script preserves the existing marker IDs and navigation export.

## Film beside the phone footage

Open the standalone viewer or `/map/` and choose First person or 3D view. Choose X-ray and a walking pace, then press Start scripted walk. A three-second countdown cues the recording; the elapsed timer starts when movement starts. Normal pace takes about seven seconds per leg, plus turns. Pause/resume to align with the phone performance; Reset route returns to the start and resets the timer. Switching away from the page pauses playback.

Record the real phone view separately and place it alongside this website view in the video. The website is a hardcoded route visualization: it neither reads the phone camera nor follows its markers live. Keep the visible Scripted route label in the footage. Camera demo: the phone page at `/` on the laptop server over HTTPS. Route demo: this standalone viewer or `/map/`.

To prepare the latest website for the existing Sites owner, run `python3 demo/package_viewer.py`. This rebuilds the viewer environments from source before copying the public runtime assets. Deployment must use the existing site's identity and requires editor access; packaging alone does not update the public link.

## Hospital visual pass

The scripted set uses six ceiling spotlights, two static soft-shadow maps, neutral ambient lighting, and distinct matte wall, satin floor, wood and brushed-metal finishes. Small canvas textures keep it offline with no added dependencies. Department signs have physical backing and fit within the pillars; room numbers, handrails, ceiling seams and sanitizer dispensers add hospital detail without changing the walking route. Ceiling pieces hide in overhead and 3D views. The GLB includes authored geometry and base colors; browser lighting, canvas textures and sign lettering are viewer-only.
