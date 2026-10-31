# Grady viewer implementation plan

Approved scope: a browser cutaway of the GMH-G entrance/lab area with routing simulation, GLB and JSON outputs. Source: PDF page 3. Approximate geometry, no clinical navigation claim.

1. Trace simplified walls against the rendered crop; generate a reusable GLB and a route graph in shared coordinates.
2. Build a locally served Three.js viewer with destination selection, orbit/top views, labels, route playback, pause/reset, and downloads.
3. Check graph reachability, GLB structure, JS syntax, HTTP delivery, and browser interactions.

Keep work in demo/ to avoid the team's server and phone files. No live perception connection is available yet; expose an explicit integration method.
