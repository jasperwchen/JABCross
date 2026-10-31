"""Cafeteria staging contract, geometry and real Navigator with fake camera frames."""
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'server'))
from nav import Navigator


def frame(*ids):
    return {'view_ok': True, 'obstacles': dict(left=3, center=3, right=3),
            'markers': [dict(id=id, distance_m=1, bearing_deg=0) for id in ids]}


class CafeDemo(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'demo/grady-ground.json').read_text(encoding='utf8'))
        self.time = 100
        self.nav = Navigator(clock=lambda: self.time)

    def update(self, heading, *ids):
        self.time += 3.1
        return self.nav.update(frame(*ids), heading)['speak']

    def test_staged_nodes_and_turns(self):
        nodes = self.data['nodes']
        self.assertEqual({n['marker']: n['name'] for n in nodes.values()},
                         {0: 'Entrance', 1: 'Lobby', 2: 'Pharmacy', 3: 'X-ray'})
        self.assertEqual(self.data['destinations'], ['pharmacy', 'xray'])
        for (a, b, steps), expected in zip(self.data['edges'], [90, 0, 0]):
            heading = math.degrees(math.atan2(nodes[b]['x'] - nodes[a]['x'],
                                              -(nodes[b]['y'] - nodes[a]['y']))) % 360
            self.assertEqual(heading, expected)
            self.assertEqual(steps, 7)
        self.assertEqual([nodes[k]['facing'] for k in ['entrance', 'lobby', 'pharmacy', 'xray']], [0, 90, 0, 0])

    def test_pillar_faces_and_clear_walking_space(self):
        self.assertEqual(len(self.data.get('pillars', [])), 4)
        for id, face in enumerate(['south', 'west', 'south', 'south']):
            pillar = self.data['pillars'][id]
            node = next(n for n in self.data['nodes'].values() if n['marker'] == id)
            self.assertEqual(node['markerFace'], face)
            mx, my = node['markerPosition']
            if face == 'south':
                self.assertEqual((mx, my), (pillar['x'], pillar['y'] + pillar['size'] / 2))
            else:
                self.assertEqual((mx, my), (pillar['x'] - pillar['size'] / 2, pillar['y']))
        for a, b, _ in self.data['edges']:
            a, b = self.data['nodes'][a], self.data['nodes'][b]
            for i in range(101):
                x, y = a['x'] + (b['x'] - a['x']) * i / 100, a['y'] + (b['y'] - a['y']) * i / 100
                for p in self.data['pillars']:
                    self.assertFalse(abs(x - p['x']) < p['size']/2 + 8 and abs(y - p['y']) < p['size']/2 + 8)

    def test_full_xray_walk(self):
        self.update(0, 0)
        self.assertIn('Turn right about 90 degrees.', self.nav.command('take me to x ray'))
        self.assertEqual(self.update(90), 'Walk forward about 7 steps.')
        self.assertEqual(self.update(90, 1), 'Lobby. Turn left about 90 degrees.')
        self.assertEqual(self.update(0), 'Walk forward about 7 steps.')
        self.assertEqual(self.update(0, 2), 'Pharmacy. Walk forward about 7 steps.')
        self.assertEqual(self.update(0, 3), 'You have arrived at X-ray.')
        self.assertEqual(self.nav.state(), dict(node='xray', marker=3, destination=None))

    def test_pharmacy_arrival_and_aliases(self):
        for alias in ['pharmacy', 'medicine', 'prescription']:
            self.assertIn('Going to Pharmacy.', self.nav.command(alias))
        self.update(0, 0)
        self.update(90)
        self.update(90, 1)
        self.update(0)
        self.assertEqual(self.update(0, 2), 'You have arrived at Pharmacy.')

    def test_xray_aliases(self):
        for alias in ['x-ray', 'x ray', 'xray', 'radiology', 'radiation lab', 'imaging', 'lab']:
            with self.subTest(alias=alias):
                self.assertIn('Going to X-ray.', self.nav.command(alias))


if __name__ == '__main__':
    unittest.main()
