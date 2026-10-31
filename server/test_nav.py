import json
import tempfile
import unittest
from pathlib import Path

from nav import MAP_PATH, Navigator

GYRO_START = 200  # The phone's heading is relative, so it never matches map headings.

# Small L-shaped route: east from the entrance to the lobby, then north (map up) twice.
FIXTURE = {
    "nodes": {
        "entrance": {"name": "Entrance", "x": 0, "y": 0, "marker": 0, "aliases": ["entrance"], "facing": 0},
        "lobby": {"name": "Lobby", "x": 100, "y": 0, "marker": 1, "aliases": ["lobby"], "facing": 90},
        "pharmacy": {"name": "Pharmacy", "x": 100, "y": -100, "marker": 2, "aliases": ["pharmacy"], "facing": 0},
        "xray": {"name": "X-ray", "x": 100, "y": -200, "marker": 3, "aliases": ["x-ray", "xray"], "facing": 0},
    },
    "edges": [["entrance", "lobby", 7], ["lobby", "pharmacy", 7], ["pharmacy", "xray", 7]],
}
FIXTURE_PATH = Path(tempfile.mkdtemp()) / "fixture.json"
FIXTURE_PATH.write_text(json.dumps(FIXTURE))

WALK = "Walk forward about 7 steps."
STOP_LEFT = {"speak": "Stop. Obstacle ahead. More space on your left.", "alert": "stop"}
QUIET = {"speak": None, "alert": "none"}


def phone(map_heading):
    return (map_heading + GYRO_START) % 360


def marker(id, distance=1.0, bearing=0.0):
    return {"id": id, "distance_m": distance, "bearing_deg": bearing}


def frame(*markers, center=3.0, left=3.0, right=3.0, view_ok=True):
    return {
        "view_ok": view_ok,
        "obstacles": {"left": left, "center": center, "right": right},
        "markers": list(markers),
    }


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class NavTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.nav = Navigator(FIXTURE_PATH, clock=self.clock)

    def update(self, perception=None, map_heading=0, dt=0.25):
        self.clock.now += dt
        return self.nav.update(perception or frame(), phone(map_heading))

    def say(self, perception=None, map_heading=0):
        return self.update(perception, map_heading)["speak"]

    def frames(self, seconds, perception=None, map_heading=0):
        """Replies for `seconds` of frames, 0.25 s apart."""
        return [self.update(perception, map_heading) for _ in range(int(seconds * 4))]

    def spoken(self, seconds, perception=None, map_heading=0):
        return [r["speak"] for r in self.frames(seconds, perception, map_heading) if r["speak"]]

    def start(self, text="take me to x-ray", map_heading=0):
        self.nav.update(frame(), phone(0))  # The first frame anchors on the entrance, map heading 0.
        if map_heading:
            self.nav.update(frame(), phone(map_heading))
        return self.nav.command(text)

    def walking(self):
        """Start the route and turn into the first hallway (map heading 90)."""
        self.start()
        self.assertEqual(self.say(map_heading=90), WALK)

    def at_lobby(self):
        """Walk the first leg and stand at the lobby, turned north (map heading 0)."""
        self.walking()
        self.assertEqual(self.say(frame(marker(1)), 90), "Lobby. Turn left about 90 degrees.")
        self.assertEqual(self.say(map_heading=0), WALK)


class SharedMap(NavTest):
    def test_navigator_reads_the_one_shared_map(self):
        self.assertEqual(MAP_PATH.name, "grady-ground.json")
        self.assertEqual(MAP_PATH.parent.name, "demo")

    def test_shared_map_routes_to_a_destination(self):
        nav = Navigator(clock=self.clock)
        nav.update(frame(), 0)
        start = nav.state()["node"]
        alias = next(n["aliases"][0] for key, n in nav.nodes.items() if n["aliases"] and key != start)
        self.assertTrue(nav.command(f"take me to {alias}").startswith("Going to "))


class Commands(NavTest):
    def test_route_reply_names_destination_and_turn(self):
        self.assertEqual(self.start(), "Going to X-ray. Turn right about 90 degrees.")
        self.assertEqual(self.nav.state()["destination"], "xray")

    def test_route_reply_walks_when_already_facing_the_hallway(self):
        self.assertEqual(self.start(map_heading=90), f"Going to X-ray. {WALK}")

    def test_turn_amount_crosses_north(self):
        self.assertEqual(self.start(map_heading=300), "Going to X-ray. Turn right about 150 degrees.")

    def test_alias_matches_whole_words_only(self):
        self.assertNotIn("Going to", self.start("take me to the lobbyist"))

    def test_unknown_destination_lists_places(self):
        reply = self.start("take me to the moon")
        self.assertIn("Pharmacy", reply)
        self.assertIsNone(self.nav.state()["destination"])

    def test_already_at_destination(self):
        self.assertIn("already", self.start("take me to the entrance"))
        self.assertIsNone(self.nav.state()["destination"])

    def test_where_am_i_without_route(self):
        self.assertEqual(self.nav.command("where am I?"), "You are at Entrance.")

    def test_where_am_i_on_route(self):
        self.start()
        self.assertEqual(self.nav.command("where am I"), "You are near Entrance, heading to X-ray.")

    def test_repeat_returns_last_spoken_line(self):
        reply = self.start()
        self.assertEqual(self.nav.command("repeat"), reply)
        self.assertEqual(self.say(map_heading=90), WALK)
        self.assertEqual(self.nav.command("repeat"), WALK)

    def test_where_am_i_does_not_replace_repeat_line(self):
        reply = self.start()
        self.nav.command("where am I")
        self.assertEqual(self.nav.command("repeat"), reply)

    def test_repeat_with_nothing_said(self):
        self.assertEqual(self.nav.command("repeat"), "Nothing to repeat yet.")

    def test_stop_ends_guidance(self):
        self.start()
        self.nav.command("stop")
        self.assertIsNone(self.nav.state()["destination"])
        self.assertEqual(self.frames(10, frame(center=0.5)), [QUIET] * 40)

    def test_cancel_ends_guidance(self):
        self.start()
        self.nav.command("cancel")
        self.assertIsNone(self.nav.state()["destination"])


class Guidance(NavTest):
    def test_full_walk_says_each_change_once(self):
        lines = [self.start()]
        script = [
            (2, frame(), 0),  # Still facing the entrance.
            (1, frame(), 90),  # Turned into the first hallway.
            (3, frame(), 90),
            (1, frame(marker(1, 3.0)), 90),
            (1, frame(marker(1, 2.0)), 90),
            (0.25, frame(marker(1, 1.0)), 90),  # Reached the lobby.
            (1, frame(marker(1, 0.8, bearing=-40.0)), 90),
            (2, frame(), 0),  # Turned left.
            (1, frame(marker(2, 3.0)), 0),
            (0.25, frame(marker(2, 1.0)), 0),  # Reached the pharmacy, straight on.
            (3, frame(marker(3, 2.5)), 0),
            (0.25, frame(marker(3, 1.0)), 0),  # Reached X-ray.
            (5, frame(marker(3, 0.5), center=0.5), 0),
        ]
        for seconds, perception, map_heading in script:
            lines += self.spoken(seconds, perception, map_heading)
        self.assertEqual(lines, [
            "Going to X-ray. Turn right about 90 degrees.",
            WALK,
            "Lobby ahead.",
            "Lobby. Turn left about 90 degrees.",
            WALK,
            "Pharmacy ahead.",
            f"Pharmacy. {WALK}",
            "X-ray ahead.",
            "You have arrived at X-ray.",
        ])
        self.assertEqual(self.nav.state(), {"node": "xray", "marker": 3, "destination": None})

    def test_turn_is_reprompted_only_after_six_seconds(self):
        self.start()
        self.assertEqual(self.spoken(5.75), [])
        self.assertEqual(self.say(), "Turn right about 90 degrees.")
        self.assertEqual(self.spoken(5.75), [])

    def test_partial_turn_reprompts_remaining_amount(self):
        self.start()
        self.frames(5.75, map_heading=50)
        self.assertEqual(self.say(map_heading=50), "Turn right about 40 degrees.")

    def test_wobble_under_drift_threshold_is_silent(self):
        self.walking()
        for heading in [110, 118, 70, 62] * 15:  # Errors of 20 to 28 degrees either way, for 15 s.
            self.assertIsNone(self.say(map_heading=heading))

    def test_drift_says_bear_then_nothing_once_corrected(self):
        self.walking()
        self.assertEqual(self.say(map_heading=125), "Bear left.")
        self.assertEqual(self.spoken(10, map_heading=90), [])

    def test_drift_repeats_at_most_every_six_seconds(self):
        self.walking()
        self.assertEqual(self.say(map_heading=55), "Bear right.")
        self.assertEqual(self.spoken(5.75, map_heading=55), [])
        self.assertEqual(self.say(map_heading=55), "Bear right.")

    def test_drift_counts_as_corrected_only_under_fifteen(self):
        self.walking()
        self.assertEqual(self.say(map_heading=125), "Bear left.")
        self.frames(5.75, map_heading=110)  # Back to 20 degrees off: not yet corrected.
        self.assertEqual(self.say(map_heading=110), "Bear left.")
        self.frames(1, map_heading=90)  # Corrected.
        self.assertEqual(self.spoken(10, map_heading=110), [])

    def test_huge_drift_gets_full_turn(self):
        self.walking()
        self.assertEqual(self.say(map_heading=160), "Turn left about 70 degrees.")

    def test_never_says_keep_walking(self):
        self.walking()
        lines = []
        for seconds, heading in ((3, 125), (3, 90), (3, 55), (3, 90), (1, 160), (1, 90)):
            lines += self.spoken(seconds, map_heading=heading)
        self.assertNotIn("Keep walking.", lines)
        self.assertEqual(lines, ["Bear left.", "Bear right.", "Turn left about 70 degrees."])

    def test_next_marker_announced_once_per_leg(self):
        self.walking()
        self.assertEqual(self.say(frame(marker(1, 4.0)), 90), "Lobby ahead.")
        for distance in (3.5, 3.0, 2.5, 2.0, 1.5):
            self.assertIsNone(self.say(frame(marker(1, distance)), 90))

    def test_next_marker_waits_behind_walk_line(self):
        self.start()
        # Seeing the lobby straight ahead re-anchors the heading: aligned, so walk comes first.
        self.assertEqual(self.say(frame(marker(1, 3.0)), 0), WALK)
        self.assertEqual(self.say(frame(marker(1, 3.0)), 0), "Lobby ahead.")

    def test_marker_bearing_reanchors_drifted_gyro(self):
        self.start()
        # Gyro says map heading 0, but the lobby marker sits 40 degrees right: really facing 50.
        self.update(frame(marker(1, distance=3.0, bearing=40.0)))
        self.assertAlmostEqual(self.nav._heading_error(), 40.0)

    def test_far_marker_does_not_count_as_arrival(self):
        self.start()
        self.update(frame(marker(1, distance=3.0)))
        self.assertEqual(self.nav.state()["node"], "entrance")

    def test_off_route_marker_reroutes(self):
        self.start()
        self.assertEqual(self.say(frame(marker(2))), f"Pharmacy. {WALK}")
        self.assertEqual(self.nav.state(), {"node": "pharmacy", "marker": 2, "destination": "xray"})

    def test_passing_a_reached_marker_does_not_redirect(self):
        self.at_lobby()
        # Walking past the lobby marker, its bearing swings out to the side.
        self.assertIsNone(self.say(frame(marker(1, distance=0.8, bearing=40.0))))
        self.assertEqual(self.nav.state()["node"], "lobby")

    def test_destination_said_once_then_silence(self):
        self.at_lobby()
        self.say(frame(marker(2)))
        self.assertEqual(self.update(frame(marker(3), center=0.9)),
                         {"speak": "You have arrived at X-ray.", "alert": "none"})
        replies = self.frames(15, frame(marker(3, 0.4), center=0.5, view_ok=False), 270)
        self.assertEqual(replies, [QUIET] * 60)

    def test_marker_updates_position_without_route(self):
        self.update(frame(marker(1)))
        self.assertEqual(self.nav.state()["node"], "lobby")

    def test_far_marker_sets_position_without_route(self):
        self.update(frame(marker(3, distance=1.0)))
        self.update(frame(marker(0, distance=2.5)))
        self.assertEqual(self.nav.state()["node"], self.nav.by_marker[0])
        self.assertTrue(self.nav.command("x-ray").startswith("Going to X-ray"))

    def test_quiet_before_any_route(self):
        self.assertEqual(self.frames(10, frame(marker(1, 3.0), center=0.5, view_ok=False)), [QUIET] * 40)

    def test_unknown_marker_is_ignored(self):
        self.start()
        self.assertIsNone(self.say(frame(marker(49))))


class Safety(NavTest):
    def test_obstacle_stop_needs_two_frames(self):
        self.walking()
        self.assertEqual(self.update(frame(center=0.8, left=2.5, right=1.0), 90), QUIET)
        self.assertEqual(self.update(frame(center=0.8, left=2.5, right=1.0), 90), STOP_LEFT)

    def test_single_frame_blip_is_ignored(self):
        self.walking()
        for center in (0.8, 3.0, 0.8, 3.0, 0.8, 3.0):
            self.assertEqual(self.update(frame(center=center), 90), QUIET)

    def test_obstacle_side_hint_right(self):
        self.walking()
        self.update(frame(center=0.8, left=1.0, right=2.5), 90)
        self.assertIn("right", self.say(frame(center=0.8, left=1.0, right=2.5), 90))

    def test_obstacle_beats_turn_but_keeps_turn_instruction(self):
        # A walker facing the junction wall must still hear which way to turn.
        self.start()
        self.update(frame(center=0.8))
        self.assertEqual(self.update(frame(center=0.8)),
                         {"speak": "Stop. Obstacle ahead. Turn right about 90 degrees.", "alert": "stop"})

    def test_persistent_obstacle_only_beeps(self):
        self.walking()
        self.update(frame(center=0.8, left=2.5, right=1.0), 90)
        replies = [self.update(frame(center=0.8, left=2.5, right=1.0), 90) for _ in range(41)]
        self.assertEqual(replies[0], STOP_LEFT)
        self.assertEqual([r["speak"] for r in replies[1:]], [None] * 40)
        self.assertEqual([r["alert"] for r in replies[1:]].count("warn"), 3)  # At 3, 6, 9 s.
        self.assertNotIn("stop", [r["alert"] for r in replies[1:]])

    def test_clear_needs_margin_and_two_frames(self):
        self.walking()
        self.frames(1, frame(center=0.8), 90)
        self.assertEqual(self.spoken(2, frame(center=1.2), 90), [])
        self.assertIsNone(self.say(frame(center=2.0), 90))
        self.assertEqual(self.update(frame(center=2.0), 90), {"speak": "Clear. Continue.", "alert": "none"})
        self.assertEqual(self.spoken(5, frame(), 90), [])

    def test_clear_says_turn_when_one_is_still_needed(self):
        self.start()
        self.frames(1, frame(center=0.8))
        self.update(frame())
        self.assertEqual(self.say(), "Turn right about 90 degrees.")

    def test_obstacle_wait_does_not_count_as_lost(self):
        self.walking()
        self.frames(30, frame(center=0.8), 90)
        self.update(frame(), 90)
        self.assertEqual(self.say(map_heading=90), "Clear. Continue.")
        self.assertEqual(self.update(map_heading=90), QUIET)

    def test_blocked_view_warns_before_obstacle(self):
        self.walking()
        self.assertEqual(
            self.update(frame(center=0.5, view_ok=False), 90),
            {"speak": "Camera blocked. Hold the phone flat against your chest.", "alert": "warn"},
        )

    def test_blocked_view_repeats_every_ten_seconds(self):
        self.walking()
        self.assertEqual(len(self.spoken(10, frame(view_ok=False), 90)), 1)
        self.assertIn("Camera blocked", self.say(frame(view_ok=False), 90))

    def test_no_obstacle_alert_without_route(self):
        self.assertEqual(self.frames(1, frame(center=0.5)), [QUIET] * 4)

    def test_overrunning_a_leg_stops_the_walker_then_repeats_every_ten_seconds(self):
        self.walking()
        self.clock.now += 1000
        reply = self.update(map_heading=90)
        self.assertEqual(reply["alert"], "stop")
        self.assertIn("next sign", reply["speak"])
        self.assertEqual(self.frames(9.75, map_heading=90), [QUIET] * 39)
        self.assertIn("next sign", self.say(map_heading=90))

    def test_no_overrun_inside_expected_leg_time(self):
        self.walking()
        self.assertEqual(self.frames(12, map_heading=90), [QUIET] * 48)

    def test_seeing_next_marker_after_overrun_resumes(self):
        self.walking()
        self.say(frame(marker(1, 5.0)), 90)  # "Lobby ahead." before getting lost.
        self.clock.now += 1000
        self.update(map_heading=90)
        self.assertEqual(self.say(frame(marker(1, 3.0)), 90), "Lobby ahead.")
        self.assertEqual(self.update(map_heading=90), QUIET)

    def test_markers_after_route_ends_are_harmless(self):
        self.start()
        self.nav.command("cancel")
        self.assertIsNone(self.say(frame(marker(1, distance=3.0))))

    def test_no_overrun_before_walking_starts(self):
        self.start()
        self.clock.now += 1000
        self.assertEqual(self.update(), {"speak": "Turn right about 90 degrees.", "alert": "none"})


if __name__ == "__main__":
    unittest.main()
