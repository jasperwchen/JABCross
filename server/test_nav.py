import re
import unittest
import subprocess
import sys
import tempfile
from pathlib import Path

from nav import MAP_PATH, Navigator

# Keep the existing hospital regression scenarios even when the café is active.
def setUpModule():
    global hospital_temp, hospital_map
    hospital_temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'demo/build_model.py'),
                    '--hospital', '--output-dir', hospital_temp.name], check=True, capture_output=True)
    hospital_map = Path(hospital_temp.name) / 'grady-ground.json'


def tearDownModule():
    hospital_temp.cleanup()

GYRO_START = 200  # The phone's heading is relative, so it never matches map headings.


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
        self.nav = Navigator(map_path=hospital_map, clock=self.clock)

    def update(self, perception, map_heading=0):
        self.clock.now += 3.1
        return self.nav.update(perception, phone(map_heading))

    def start(self, text="take me to the cashier"):
        self.nav.update(frame(), phone(0))
        return self.nav.command(text)


class SharedMap(NavTest):
    def test_navigator_reads_the_one_shared_map(self):
        self.assertEqual(MAP_PATH.name, "grady-ground.json")
        self.assertEqual(MAP_PATH.parent.name, "demo")


class Commands(NavTest):
    def test_route_reply_names_destination_and_first_instruction(self):
        reply = self.start()
        self.assertIn("Starting route to Cashier.", reply)
        self.assertRegex(reply, r"Walk forward about \d+ steps")
        self.assertEqual(self.nav.state()["destination"], "cashier")

    def test_alias_finds_destination(self):
        self.assertIn("Lab waiting", self.start("I need a blood test"))

    def test_alias_matches_whole_words_only(self):
        self.assertNotIn("Starting route", self.start("take me to the labyrinth"))

    def test_unknown_destination_lists_places(self):
        reply = self.start("take me to radiology")
        self.assertIn("Cashier", reply)
        self.assertIsNone(self.nav.state()["destination"])

    def test_already_at_destination(self):
        self.assertIn("already", self.start("take me to the front door"))
        self.assertIsNone(self.nav.state()["destination"])

    def test_where_am_i_without_route(self):
        self.assertEqual(self.nav.command("where am I?"), "You are at Entrance vestibule.")

    def test_where_am_i_on_route(self):
        self.start()
        self.assertEqual(
            self.nav.command("where am I"),
            "You are near Entrance vestibule, heading to Cashier.",
        )

    def test_repeat_returns_last_spoken_line(self):
        reply = self.start()
        self.assertEqual(self.nav.command("repeat"), reply)

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
        self.assertIsNone(self.update(frame())["speak"])

    def test_cancel_ends_guidance(self):
        self.start()
        self.nav.command("cancel")
        self.assertIsNone(self.nav.state()["destination"])


class Guidance(NavTest):
    def test_full_cashier_route(self):
        self.start()
        self.assertIsNone(self.update(frame())["speak"])

        self.assertEqual(self.update(frame(marker(10)))["speak"], "Turn right about 90 degrees.")
        self.assertRegex(self.update(frame(), 90)["speak"], r"^Walk forward about \d+ steps\.$")
        self.assertEqual(self.update(frame(marker(11)), 90)["speak"], "Turn left about 90 degrees.")
        self.assertRegex(self.update(frame(), 0)["speak"], r"^Walk forward about \d+ steps\.$")
        self.assertRegex(self.update(frame(marker(1)))["speak"], r"^Walk forward about \d+ steps\.$")
        self.assertEqual(self.update(frame(marker(8)))["speak"], "You have arrived at Cashier.")

        self.assertEqual(self.nav.state(), {"node": "cashier", "marker": 8, "destination": None})
        self.assertIsNone(self.update(frame())["speak"])

    def test_far_marker_does_not_count_as_arrival(self):
        self.start()
        self.update(frame(marker(10, distance=3.0)))
        self.assertEqual(self.nav.state()["node"], "entrance")

    def test_turn_amount_crosses_north(self):
        self.start("take me to the cashier")
        self.nav.update(frame(), phone(0))
        self.assertEqual(self.update(frame(), 350)["speak"], None)
        self.assertEqual(self.update(frame(), 330)["speak"], "Turn right about 30 degrees.")

    def test_marker_bearing_reanchors_drifted_gyro(self):
        self.start()
        self.nav.update(frame(), phone(0))
        # Gyro says straight on, but the marker ahead sits 40 degrees right.
        self.assertEqual(
            self.update(frame(marker(10, distance=3.0, bearing=40.0)))["speak"],
            "Turn right about 40 degrees.",
        )

    def test_keep_walking_after_correction(self):
        self.start()
        self.update(frame(), 330)
        self.assertEqual(self.update(frame(), 0)["speak"], "Keep walking.")
        self.assertIsNone(self.update(frame(), 0)["speak"])

    def test_off_route_marker_reroutes(self):
        self.start()
        self.assertEqual(self.update(frame(marker(11)))["alert"], "none")
        self.nav.update(frame(marker(2), center=3.0), phone(270))
        self.assertEqual(self.nav.state()["node"], "west")
        self.assertEqual(self.nav.state()["destination"], "cashier")

    def test_passing_a_reached_marker_does_not_redirect(self):
        self.start()
        for id, map_heading in ((10, 0), (11, 90), (1, 0)):
            self.update(frame(marker(id)), map_heading)
        self.update(frame(), 0)
        # Walking straight past the lobby marker, its bearing swings out to the side.
        self.assertIsNone(self.update(frame(marker(1, distance=0.8, bearing=40.0)))["speak"])

    def test_marker_updates_position_without_route(self):
        self.update(frame(marker(1)))
        self.assertEqual(self.nav.state()["node"], "lobby")

    def test_unknown_marker_is_ignored(self):
        self.start()
        self.assertIsNone(self.update(frame(marker(49)))["speak"])


class Safety(NavTest):
    def test_center_obstacle_stops_with_side_hint(self):
        self.start()
        reply = self.update(frame(center=0.8, left=2.5, right=1.0))
        self.assertEqual(reply, {"speak": "Stop. Obstacle ahead. More space on your left.", "alert": "stop"})

    def test_obstacle_side_hint_right(self):
        self.start()
        self.assertIn("right", self.update(frame(center=0.8, left=1.0, right=2.5))["speak"])

    def test_obstacle_beats_turn_but_keeps_turn_instruction(self):
        # A walker facing the junction wall must still hear which way to turn.
        self.start()
        self.update(frame(marker(10)))
        reply = self.update(frame(center=0.8))
        self.assertEqual(reply["alert"], "stop")
        self.assertEqual(reply["speak"], "Stop. Obstacle ahead. Turn right about 90 degrees.")

    def test_clear_path_after_obstacle_says_keep_walking(self):
        self.start()
        self.update(frame(center=0.8))
        self.assertEqual(self.update(frame())["speak"], "Keep walking.")

    def test_blocked_view_warns_before_obstacle(self):
        self.start()
        reply = self.update(frame(center=0.5, view_ok=False))
        self.assertEqual(
            reply,
            {"speak": "Camera blocked. Hold the phone flat against your chest.", "alert": "warn"},
        )

    def test_no_obstacle_alert_without_route(self):
        self.assertEqual(self.update(frame(center=0.5)), {"speak": None, "alert": "none"})

    def test_arrival_beats_obstacle_from_destination_wall(self):
        self.start()
        for id in (10, 11, 1):
            self.update(frame(marker(id)))
        reply = self.update(frame(marker(8), center=0.9))
        self.assertEqual(reply["speak"], "You have arrived at Cashier.")


    def test_overrunning_a_leg_stops_the_walker(self):
        self.start()
        self.clock.now += 1000
        reply = self.nav.update(frame(), phone(0))
        self.assertEqual(reply["alert"], "stop")
        self.assertIn("next sign", reply["speak"])

    def test_no_overrun_inside_expected_leg_time(self):
        self.start()
        self.clock.now += 12
        self.assertEqual(self.nav.update(frame(), phone(0))["alert"], "none")

    def test_seeing_next_marker_after_overrun_resumes(self):
        self.start()
        self.clock.now += 1000
        self.nav.update(frame(), phone(0))
        self.assertEqual(self.update(frame(marker(10, distance=3.0)))["speak"], "Keep walking.")

    def test_markers_after_route_ends_are_harmless(self):
        self.start()
        self.nav.command("cancel")
        self.assertIsNone(self.update(frame(marker(10, distance=3.0)))["speak"])

    def test_no_overrun_before_walking_starts(self):
        self.nav.update(frame(), phone(0))
        self.nav.update(frame(), phone(90))
        self.nav.command("take me to the cashier")
        self.clock.now += 1000
        self.assertIn("Turn", self.nav.update(frame(), phone(90))["speak"])


class Pacing(NavTest):
    def test_same_kind_of_line_waits_three_seconds(self):
        self.start()
        self.nav.update(frame(), phone(0))
        self.assertIsNotNone(self.update(frame(), 300)["speak"])
        self.clock.now += 1
        self.assertIsNone(self.nav.update(frame(), phone(310))["speak"])

    def test_repeated_stop_alert_stays_quiet_inside_window(self):
        self.start()
        self.update(frame(center=0.8))
        self.clock.now += 1
        self.assertEqual(
            self.nav.update(frame(center=0.8), phone(0)),
            {"speak": None, "alert": "none"},
        )

    def test_throttled_walk_line_is_spoken_later_not_lost(self):
        self.start()
        self.update(frame(marker(10)))
        self.update(frame(), 90)
        self.clock.now += 0.5
        self.nav.update(frame(marker(11)), phone(90))
        self.update(frame(), 0)
        self.clock.now += 0.5
        # Reached the lobby straight after the previous walk line: held back for now.
        self.assertIsNone(self.nav.update(frame(marker(1)), phone(0))["speak"])
        self.clock.now += 3
        self.assertRegex(self.nav.update(frame(), phone(0))["speak"], r"Walk forward")


if __name__ == "__main__":
    unittest.main()
