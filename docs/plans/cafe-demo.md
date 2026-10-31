# Café demo map implementation plan

**Goal:** Match the café staging screenshot and the final printed signs in AGENT-HANDOFF.md.

**Design:** Make the café the default shared map at demo/grady-ground.json (keep the established filename and endpoint contract). Show four pillars with markers on the south, west, south, south faces respectively. Route nodes sit in clear space beside the pillars: Entrance -> Lobby east, Lobby -> Pharmacy north, Pharmacy -> X-ray north. Each edge is approximately 5 m / 7 estimated steps. Final names are Entrance, Lobby, Pharmacy, X-ray; lab remains an alias for X-ray. Keep original hospital geometry available through an explicit build option, without mixing hospital markers into the café route.

**Architecture:** Reuse the Python generator, vendored Three.js viewer, and unchanged Navigator API. Generate café geometry and navigation together. Adapt existing viewer labels, framing and reference-overlay behavior to the active map metadata. No dependency installation, endpoint changes, live tracking additions, or phone changes.

**Tech stack:** Existing Python standard library and vendored Three.js.

## Tasks

- [x] Add failing café geometry and fake-perception route checks, including unique markers, heading/facing, aliases and arrival.
- [x] Generate the four-pillar map and matching GLB through build_model.py; preserve the hospital generator option.
- [x] Adapt the viewer's destination labels, camera framing and simulation instructions to the café map while preserving controls and setMarker.
- [x] Run geometry/export/route checks and navigator regression tests; inspect the viewer in a browser and exercise both destinations, reset and marker adapter.
- [x] Obtain code-critic and pentest-reviewer reviews, fix relevant findings, document estimated distances and untested physical behavior, and append the local work log. Do not commit or push.

## Review focus

- Marker 0 faces north despite the first route leg heading east.
- Marker 1 is on the west face; markers 2 and 3 are on the south face.
- Routes stay beside the pillar footprints, including the straight path past pillar 2.
- Speech names match the printed signs and accepts x ray and lab.
- Standalone viewer stays explicit about simulation; steps remain estimates.

Validation: 45 Python checks pass; JavaScript syntax and git whitespace checks pass. Browser exercised both destinations, initial right turn, Lobby left turn, reset, overhead and 3D views, plus phone/tablet/desktop layouts. Code-critic findings were corrected and re-reviewed; pentest-reviewer found no introduced issues. Physical phone/perception and step calibration remain untested.
