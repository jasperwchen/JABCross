import argparse,json,struct,pathlib,math
p=pathlib.Path(__file__).parent
parser=argparse.ArgumentParser(description='Build the shared café demo map; --hospital restores the Grady reference.')
parser.add_argument('--hospital',action='store_true')
parser.add_argument('--output-dir',type=pathlib.Path,default=p)
args=parser.parse_args()
args.output_dir.mkdir(parents=True,exist_ok=True)
from model_geometry import rooms, walls, objects, facilities, PALETTE
nodes={'entrance':{'name':'Entrance vestibule','x':245,'y':535,'marker':0},'lobbyfront':{'name':'Lobby front','x':245,'y':420,'marker':10},'lobbyeast':{'name':'Lobby east aisle','x':292,'y':420,'marker':11},'lobby':{'name':'Lobby','x':292,'y':300,'marker':1},'west':{'name':'Lobby junction','x':100,'y':300,'marker':2},'north':{'name':'North corridor','x':100,'y':90,'marker':3},'east':{'name':'East junction','x':1260,'y':90,'marker':4},'labturn':{'name':'Lab corridor','x':1260,'y':240,'marker':5},'lab':{'name':'Lab waiting','x':1090,'y':195,'marker':6},'cafe':{'name':'Café','x':350,'y':300,'marker':7},'cashier':{'name':'Cashier','x':292,'y':196,'marker':8}}
edges=[['entrance','lobbyfront'],['lobbyfront','lobbyeast'],['lobbyeast','lobby'],['lobby','west'],['west','north'],['north','east'],['east','labturn'],['labturn','lab'],['lobby','cafe'],['lobby','cashier']]
# Additional corner keeps the lab route orthogonal.
nodes['labdoor']={'name':'Lab waiting doorway','x':1090,'y':240,'marker':9};edges.remove(['labturn','lab']);edges += [['labturn','labdoor'],['labdoor','lab']]
data={'source':'Grady base plans, PDF page 3, GMH-G; entrance/lab crop','units':'x and y in illustrative plan units; edge values in estimated walking steps','coordinateSystem':'x right, y down; 3D x=x/20-42.5, z=y/20-16.25','rooms':rooms,'objects':objects,'facilities':facilities,'palette':PALETTE,'walls':walls,'nodes':nodes,'edges':[[a,b,round(math.hypot(nodes[a]['x']-nodes[b]['x'],nodes[a]['y']-nodes[b]['y']),2)] for a,b in edges],'destinations':['cashier','cafe','lab']}
# Navigation fields read by server/nav.py.
STEPS_PER_UNIT=.1 # Estimate from room sizes; set from the measured venue route.
aliases={'entrance':['entrance','main entrance','front door','exit'],'lobby':['lobby'],'lab':['lab','laboratory','lab waiting','blood work','blood test'],'cafe':['cafe','café','coffee','food'],'cashier':['cashier','billing','pay my bill','payment']}
def heading(a,b):return round(math.degrees(math.atan2(nodes[b]['x']-nodes[a]['x'],-(nodes[b]['y']-nodes[a]['y']))))%360
# Each marker faces the walker arriving from the entrance, so facing is the arrival heading.
facing={'entrance':heading('entrance','lobbyfront')};todo=['entrance']
while todo:
 u=todo.pop(0)
 for a,b in edges:
  v=b if a==u else a if b==u else None
  if v and v not in facing:facing[v]=heading(u,v);todo.append(v)
for k,n in nodes.items():n['aliases']=aliases.get(k,[]);n['facing']=facing[k]
data['edges']=[[a,b,max(1,round(w*STEPS_PER_UNIT))] for a,b,w in data['edges']]
if not args.hospital:
 from cafe_geometry import build_cafe
 data=build_cafe()
 rooms,walls,objects,facilities,PALETTE=(data[k] for k in ['rooms','walls','objects','facilities','palette'])
(args.output_dir/'grady-ground.json').write_text(json.dumps(data,indent=2),encoding='utf8')
# Portable GLB: reusable cube mesh instanced for each wall and floor.
verts=[[-.5,-.5,-.5],[.5,-.5,-.5],[.5,.5,-.5],[-.5,.5,-.5],[-.5,-.5,.5],[.5,-.5,.5],[.5,.5,.5],[-.5,.5,.5]]
indices=[0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,3,7,6,3,6,2,0,4,7,0,7,3,1,2,6,1,6,5]
blob=struct.pack('<24f',*[a for v in verts for a in v])+struct.pack('<36H',*indices)
g={'asset':{'version':'2.0','generator':'JabCross simplified Grady trace'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],'materials':[{'name':'Warm plaster','pbrMetallicRoughness':{'baseColorFactor':[.78,.82,.80,1],'metallicFactor':0,'roughnessFactor':.9}}],'buffers':[{'byteLength':len(blob)}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':96},{'buffer':0,'byteOffset':96,'byteLength':72}],'accessors':[{'bufferView':0,'componentType':5126,'count':8,'type':'VEC3','min':[-.5,-.5,-.5],'max':[.5,.5,.5]},{'bufferView':1,'componentType':5123,'count':36,'type':'SCALAR'}]}
# One indexed cube per material, shared by all authored objects.
g['materials']=[];g['meshes']=[]
g['asset']['generator']='JabCross cafeteria staging' if not args.hospital else 'JabCross simplified Grady trace'
for name,color in PALETTE.items():
 srgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
 rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in srgb]
 g['materials'].append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':rgb+[1],'metallicFactor':.15 if name=='metal' else 0,'roughnessFactor':.8}})
 g['meshes'].append({'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':len(g['materials'])-1}]})
for obj in objects:
 angle=obj['rotation']
 g['nodes'].append({'name':obj['name'],'mesh':list(PALETTE).index(obj['material']),'translation':obj['position'],'scale':obj['size'],'rotation':[0,math.sin(angle/2),0,math.cos(angle/2)]})
g['scenes'][0]['nodes']=list(range(len(g['nodes'])))
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob+=b'\0'*((-len(blob))%4)
(args.output_dir/'grady-ground.glb').write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob)
print('Generated',len(rooms),'rooms,',len(walls),'wall segments,',len(objects),'3D objects,',len(facilities),'facilities; JSON and GLB match')
