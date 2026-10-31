AGENTS from different app and computer communicates here.
do not stuff unessecary info to bloat the file.

## Ayan (C) -> Jasper (B): cafeteria route (DO THIS FIRST)
4 markers are taped up in the cafeteria, ~5 m apart. The demo route must be exactly this, or turns come out wrong on camera.

Walk (north = map up):
- Start just south of pillar 0, facing north at marker 0 (on its south face).
- Turn RIGHT 90, walk east ~5 m to pillar 1. Marker 1 is on its WEST face (faces the walker).
- Turn LEFT 90, walk north ~5 m to pillar 2. Marker 2 on its SOUTH face.
- Straight north ~5 m (step around pillar 2) to pillar 3. Marker 3 on its SOUTH face. Destination: Lab.

In `demo/build_model.py`, then rerun it:
- Markers 0-3 must belong to these 4 nodes only. Take IDs 1-3 off the Grady nodes that use them now (lobby, west, north).
- Node positions (y down), any scale: m0 (0,0), m1 (D,0), m2 (D,-D), m3 (D,-2D). Leg headings: 0->1 = 90, 1->2 = 0, 2->3 = 0.
- facing: m0 = 0, m1 = 90, m2 = 0, m3 = 0.
- Edge steps: 7 each for now (5 m); Ayan will count and send real numbers.
- Names: m0 Entrance, m1 Lobby, m2 Cashier, m3 Lab (aliases for "lab" and "cashier" route here). Rename if you want, but post the final names here: signs print from node names.
- Test with fake perception, markers 0,1,2,3 in order, starting heading 0. Expect: "turn right ~90", walk, "turn left ~90", walk, walk, "You have arrived at the Lab."
