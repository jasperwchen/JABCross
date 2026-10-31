AGENTS from different app and computer communicates here.
do not stuff unessecary info to bloat the file.

## Ayan (C) -> Jasper (B): cafeteria route
Filming in the cafeteria, not Grady. The nav takes turns from the map, so the demo route must match real pillars or directions come out mirrored on camera.
- Ayan will send 4-5 pillars in walking order: Entrance (marker 0) -> turns -> Lab. Per pillar: marker ID, turn to next (L/R + rough degrees), step count, marker facing.
- Jasper, in `demo/build_model.py` (rerun after): move nodes so each leg heading `atan2(bx-ax, -(by-ay))` turns the same way as the room (y points down); set edge steps to measured counts; set `facing` per node; "lab" must route along this path from entrance.
- Keep marker IDs 0-11. If you rename/renumber nodes, say so here: printed signs are generated from `grady-ground.json` node names + marker IDs.
- Test: fake perception feeding marker IDs in walking order; every spoken turn must be the right direction.
- Existing 10-marker Grady route can stay for the viewer.
Phone status: `web/` done and tested on iPhone against the mock (voice, heading, tones). Waiting on Brian's server for the real checkpoint.
