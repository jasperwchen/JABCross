import json, pathlib, struct, unittest
P=pathlib.Path(__file__).parent
class ModelCoverage(unittest.TestCase):
 def setUp(self):self.d=json.loads((P/'grady-ground.json').read_text())
 def test_complete_crop_coverage(self):
  names=' '.join(r['name'] for r in self.d['rooms'])
  for area in ['Exam 134','Patient toilet','Breakroom','Stair 16','North waiting','East room','Medication']:self.assertIn(area,names)
  self.assertGreaterEqual(len(self.d['rooms']),60)
  self.assertGreaterEqual(len(self.d['objects']),400)
 def test_glb_matches_viewer(self):
  raw=(P/'grady-ground.glb').read_bytes();magic,version,size=struct.unpack_from('<III',raw)
  self.assertEqual((magic,version,size),(0x46546c67,2,len(raw)))
  length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length])
  self.assertEqual(len(g['nodes']),len(self.d['objects']))
  for n,obj in zip(g['nodes'],self.d['objects']):
   self.assertEqual(n['translation'],obj['position']);self.assertEqual(n['scale'],obj['size'])
 def test_route_clearance(self):
  def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  for start,end,_ in self.d['edges']:
   a,b=[(self.d['nodes'][k]['x'],self.d['nodes'][k]['y']) for k in [start,end]]
   for x,y,u,v in self.d['walls']:
    c,d=(x,y),(u,v)
    self.assertFalse(cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0, f'{start}->{end} crosses wall {c}->{d}')
if __name__=='__main__':unittest.main()
