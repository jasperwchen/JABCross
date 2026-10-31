import json,struct,pathlib,math
p=pathlib.Path(__file__).parent
# Coordinates traced against the 1700 x 650 ground-floor crop. Display units only.
rooms=[('Cashier',285,120,145,56),('Housekeeping',434,120,35,56),('Elevator',474,121,70,70),('Workstations',697,124,160,120),('Financial counseling',937,122,118,90),('Lab waiting',1055,122,163,90),('Check-in',711,282,64,104),('Consult 141',779,278,47,44),('Consult 142',831,305,52,42),('Consult 124',779,349,47,43),('Consult 125',831,378,52,42),('Lab',1018,435,62,27)]
walls=[]
# Three sides plus a split front leave a visible entrance in each simplified room.
for name,x,y,w,h in rooms:
 for a,b,c,d in [(x,y,x+w,y),(x,y,x,y+h),(x+w,y,x+w,y+h),(x,y+h,x+w*.35,y+h),(x+w*.65,y+h,x+w,y+h)]:walls.append([a,b,c,d])
# Lobby boundary and entrance vestibule.
walls += [[45,210,45,460],[45,460,172,460],[325,460,385,460],[172,460,172,550],[325,460,325,550],[172,550,230,550],[280,550,325,550],[385,320,385,430],[385,430,620,430],[620,255,620,430]]
nodes={'entrance':{'name':'Entrance vestibule','x':255,'y':535,'marker':0},'lobby':{'name':'Lobby','x':255,'y':300,'marker':1},'west':{'name':'Lobby junction','x':100,'y':300,'marker':2},'north':{'name':'North corridor','x':100,'y':90,'marker':3},'east':{'name':'East junction','x':1260,'y':90,'marker':4},'labturn':{'name':'Lab corridor','x':1260,'y':240,'marker':5},'lab':{'name':'Lab waiting','x':1135,'y':200,'marker':6},'cafe':{'name':'Café','x':400,'y':270,'marker':7},'cashier':{'name':'Cashier','x':355,'y':200,'marker':8}}
edges=[['entrance','lobby'],['lobby','west'],['west','north'],['north','east'],['east','labturn'],['labturn','lab'],['lobby','cafe'],['lobby','cashier']]
# Additional corner keeps the lab route orthogonal.
nodes['labdoor']={'name':'Lab waiting doorway','x':1135,'y':240,'marker':9};edges.remove(['labturn','lab']);edges += [['labturn','labdoor'],['labdoor','lab']]
data={'source':'Grady base plans, PDF page 3, GMH-G; entrance/lab crop','units':'illustrative plan units, not calibrated meters or steps','coordinateSystem':'x right, y down; 3D x=x/20-42.5, z=y/20-16.25','rooms':[dict(name=n,x=x,y=y,width=w,height=h) for n,x,y,w,h in rooms],'walls':walls,'nodes':nodes,'edges':[[a,b,round(math.hypot(nodes[a]['x']-nodes[b]['x'],nodes[a]['y']-nodes[b]['y']),2)] for a,b in edges],'destinations':['lab','cafe','cashier']}
(p/'grady-ground.json').write_text(json.dumps(data,indent=2))
# Portable GLB: reusable cube mesh instanced for each wall and floor.
verts=[[-.5,-.5,-.5],[.5,-.5,-.5],[.5,.5,-.5],[-.5,.5,-.5],[-.5,-.5,.5],[.5,-.5,.5],[.5,.5,.5],[-.5,.5,.5]]
indices=[0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,3,7,6,3,6,2,0,4,7,0,7,3,1,2,6,1,6,5]
blob=struct.pack('<24f',*[a for v in verts for a in v])+struct.pack('<36H',*indices)
g={'asset':{'version':'2.0','generator':'JabCross simplified Grady trace'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],'materials':[{'name':'Warm plaster','pbrMetallicRoughness':{'baseColorFactor':[.78,.82,.80,1],'metallicFactor':0,'roughnessFactor':.9}}],'buffers':[{'byteLength':len(blob)}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':96},{'buffer':0,'byteOffset':96,'byteLength':72}],'accessors':[{'bufferView':0,'componentType':5126,'count':8,'type':'VEC3','min':[-.5,-.5,-.5],'max':[.5,.5,.5]},{'bufferView':1,'componentType':5123,'count':36,'type':'SCALAR'}]}
for i,(a,b,c,d) in enumerate(walls):g['nodes'].append({'name':f'Wall {i+1}','mesh':0,'translation':[(a+c)/40-42.5,1,(b+d)/40-16.25],'scale':[max(abs(c-a)/20,.2),2,max(abs(d-b)/20,.2)]})
g['nodes'].append({'name':'Ground floor','mesh':0,'translation':[0,-.15,0],'scale':[85,.2,32.5]});g['scenes'][0]['nodes']=list(range(len(g['nodes'])))
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob+=b'\0'*((-len(blob))%4)
(p/'grady-ground.glb').write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob)
print('Generated',len(walls),'walls,',len(nodes),'nodes and GLB')
