"""The filming set must preserve the phone route and leave room for the walker."""
import copy
import json
import math
from pathlib import Path
import struct
import unittest

from cafe_geometry import build_cafe
from hospital_interior import add_interior


class HospitalSet(unittest.TestCase):
    def setUp(self):
        self.data = build_cafe()
        self.original = copy.deepcopy(self.data)
        add_interior(self.data)

    def test_route_contract_unchanged(self):
        for key in ('nodes', 'edges', 'pillars', 'destinations'):
            self.assertEqual(self.data[key], self.original[key])
        self.assertNotIn('interior', build_cafe())

    def test_department_signs_fit_pillars_and_have_backing(self):
        names = {obj['name'] for obj in self.data['objects']}
        self.assertFalse(any(name.endswith(' sign') for name in names))
        for sign in self.data['signs']:
            self.assertIn(sign['text']+' plaque backing', names)
            self.assertLessEqual(sign['width'], 1.8)
        self.assertEqual(sum(obj['material']=='light' for obj in self.data['objects']), 6)

    def test_body_and_eye_clearance_for_entire_route(self):
        for a, b, _ in self.data['edges']:
            a, b = self.data['nodes'][a], self.data['nodes'][b]
            for i in range(101):
                x = (a['x']+(b['x']-a['x'])*i/100)/20-42.5
                z = (a['y']+(b['y']-a['y'])*i/100)/20-16.25
                for obj in self.data['objects']:
                    px, py, pz = obj['position']
                    w, h, d = obj['size']
                    if py+h/2 <= .1 or py-h/2 >= 3.7:
                        continue
                    self.assertFalse(abs(x-px) < w/2+.3 and abs(z-pz) < d/2+.3,
                                     f"Route intersects {obj['name']}")

    def test_viewer_export_matches_set_and_glb(self):
        root = Path(__file__).parent/'maps/cafe'
        data = json.loads((root/'grady-ground.json').read_text())
        self.assertEqual(data, self.data)
        raw = (root/'grady-ground.glb').read_bytes()
        length = struct.unpack_from('<I', raw, 12)[0]
        glb = json.loads(raw[20:20+length])
        self.assertEqual(len(glb['nodes']), len(data['objects']))
        for node, obj in zip(glb['nodes'], data['objects']):
            self.assertEqual(node['translation'], obj['position'])
            self.assertEqual(node['scale'], obj['size'])

    def test_camera_setback_clear_during_turns(self):
        for key, start, end in [('entrance', 0, 90), ('lobby', 90, 0)]:
            node = self.data['nodes'][key]
            for degrees in range(min(start, end), max(start, end)+1):
                angle = math.radians(degrees)
                x = node['x']/20-42.5-math.sin(angle)*1.2
                z = node['y']/20-16.25+math.cos(angle)*1.2
                for obj in self.data['objects']:
                    px, py, pz = obj['position']
                    w, h, d = obj['size']
                    if abs(3.2-py) > h/2:
                        continue
                    self.assertFalse(abs(x-px) < w/2+.1 and abs(z-pz) < d/2+.1,
                                     f"Camera intersects {obj['name']}")


if __name__ == '__main__':
    unittest.main()
