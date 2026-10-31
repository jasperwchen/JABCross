"""Hand-traced coverage of the complete displayed GMH-G crop (1700 x 650).
Heights and fixtures are illustrative; plan positions follow the reference image.
Shared box primitives feed both the browser and GLB to prevent export omissions.
"""
import math

PALETTE = {'wall':'#cbd6cd','floor':'#f8f6ef','clinic':'#e6eee7','service':'#e7e6db','waiting':'#e2e9dc','toilet':'#dde8eb','circulation':'#eeeade','glass':'#9cbfc3','metal':'#92a5a1','furniture':'#9db5a7','seat':'#688d7b','fixture':'#f7faf8','stair':'#aab9af'}
rooms, walls, objects, facilities = [], [], [], []

def box(name,x,y,w,d,h=1,base=0,material='wall',angle=0):
    objects.append(dict(name=name,position=[x/20-42.5,base+h/2,y/20-16.25],size=[w/20,h,d/20],rotation=-angle,material=material))

def segment(name,a,b,c,d,height=2,material='wall',thickness=4,base=0):
    if height==2 and material=='wall':walls.append([a,b,c,d])
    box(name,(a+c)/2,(b+d)/2,math.hypot(c-a,d-b),thickness,height,base,material,math.atan2(d-b,c-a))

def poly(name,points,**kw):
    for a,b in zip(points,points[1:]):segment(name,*a,*b,**kw)

def room(name,x,y,w,d,kind='clinic',door='S',opening=None):
    rooms.append(dict(name=name,x=x,y=y,width=w,height=d,kind=kind))
    box(name+' floor',x+w/2,y+d/2,w,d,.035,0,kind)
    sides={'N':(x,y,x+w,y),'S':(x,y+d,x+w,y+d),'W':(x,y,x,y+d),'E':(x+w,y,x+w,y+d)}
    for side,(a,b,c,e) in sides.items():
        if side==door:
            gap=min(19,(w if side in 'NS' else d)*.5)
            center=opening if opening is not None else .5
            length=math.hypot(c-a,e-b);lo=center-gap/2/length;hi=center+gap/2/length
            segment(name,a,b,a+(c-a)*lo,b+(e-b)*lo)
            segment(name,a+(c-a)*hi,b+(e-b)*hi,c,e)
            # Door head makes the opening legible while preserving clearance below.
            segment(name+' door head',a+(c-a)*lo,b+(e-b)*lo,a+(c-a)*hi,b+(e-b)*hi,height=.15,base=1.85,material='metal')
        else:segment(name,a,b,c,e)

def stair(name,x,y,w,d,steps=11):
    facilities.append(dict(name=name,kind='stairs',x=x+w/2,y=y+d/2))
    for i in range(steps):box(name+f' step {i+1}',x+w/2,y+(i+.5)*d/steps,w,d/steps,(i+1)*.105,0,'stair')
    for sx in [x+2,x+w-2]:segment(name+' handrail',sx,y,sx,y+d,height=.06,base=1.3,material='metal',thickness=2)

def elevator(name,x,y,w,d):
    room(name,x,y,w,d,'service','S')
    facilities.append(dict(name=name,kind='elevator',x=x+w/2,y=y+d/2))
    box(name+' cabin',x+w/2,y+d/2,w-6,d-6,.08,0,'metal')
    for dx in [-5,5]:box(name+' sliding door',x+w/2+dx,y+d,9,2,1.7,0,'glass')

def fixture(name,x,y,kind):
    if kind=='toilet':
        box(name+' tank',x,y-4,10,5,.7,0,'fixture');box(name+' bowl',x,y+2,9,12,.44,0,'fixture')
    elif kind=='exam':
        box(name+' exam base',x,y,13,23,.5,0,'metal');box(name+' exam cushion',x,y,14,25,.16,.5,'fixture')
    else:box(name,x,y,16,9,.75,0,'furniture')

# Upper service strip.
room('Cashier G8-108',285,120,147,56,'service','S',.15)
room('Housekeeping G8-110',434,120,32,56,'service','N')
elevator('Elevator G8',474,123,54,52)
room('Service room G8-112',556,123,37,53,'service','S')
room('Service room G8-113',596,123,43,53,'service','S')
room('Electrical G12',643,123,43,53,'service','S')
room('Workstations B12-144',697,121,165,129,'service','S',.85)
room('Stair 14 enclosure',867,126,79,96,'circulation','S',.78)
stair('Stair 14',876,151,26,62);stair('Stair 14 return',913,151,24,62)
# Separate waiting areas share an open transition as drawn.
room('Financial counseling waiting',954,123,119,100,'waiting','S',.72)
room('Lab waiting B12-102',1073,123,145,100,'waiting','S',.12)
# Remove internal division of the open waiting lounge.
walls[:] = [w for w in walls if w not in [[1073,123,1073,223]]]
objects[:] = [o for o in objects if not(o['material']=='wall' and abs(o['position'][0]-(1073/20-42.5))<.001 and abs(o['size'][0]-5)<.001)]
poly('East egress corridor',[(1274,126),(1274,320),(1250,343),(1230,331)])
# Central patient clinic. Room identifiers are transcribed from the source crop.
room('Employee health waiting B12-145',624,278,97,156,'waiting','S',.72)
room('Check-in G12-146',723,278,52,104,'service','W',.2)
for args in [
 ('Consult 141',776,278,50,53,'S'),('Consult 140',776,334,50,48,'E'),
 ('Consult 139',776,385,50,49,'S'),('Consult 123',857,280,51,51,'W'),
 ('Consult 124',857,334,51,54,'W'),('Consult 125',857,391,51,43,'S'),
 ('Consult 122',911,280,54,21,'S'),('Consult 121',911,334,54,54,'E'),
 ('Consult 120',911,391,54,43,'S'),('Consult 117',996,338,38,49,'W'),
 ('Consult 118',996,391,48,42,'W'),('Draw 113',1048,338,31,49,'E'),
 ('Draw 112',1048,391,31,42,'E'),('Draw 107',1110,330,44,34,'W'),
 ('Draw 108',1110,367,44,24,'W'),('Draw 109',1110,394,44,30,'W'),
 ('Draw 110',1084,451,26,28,'S')]:
    n,x,y,w,d,door=args;room(n,x,y,w,d,door=door)
    if d>30:fixture(n,x+w*.55,y+d*.65,'exam')
room('Lab G12-111',996,436,84,29,'clinic','S',.7)
room('Draw G12-137',696,384,35,50,'clinic','W')
room('Patient toilet G12-138',734,384,41,50,'toilet','S')
room('Patient toilet G12-119',996,299,40,36,'toilet','S')
room('Patient toilet G12-114',1039,299,40,36,'toilet','S')
room('Nurse G12-105',1082,280,88,46,'service','S')
room('Patient toilet G12-104',1173,280,44,46,'toilet','S')
room('Utility G12-106',1158,330,59,34,'service',None)
# Southern exam / staff rooms, with entrances off the staff corridor to the north.
for n,x,w in [('Medication room',460,60),('Exam 134',523,56),('Exam 133',582,55),('Exam 132',640,34),('Exam 131',677,45),('Exam 130',725,44),('Nurse touchdown',772,70),('MD office',845,46),('Quiet room',894,56),('Breakroom',953,108)]:
    room(n,x,468,w,81,'clinic' if n.startswith('Exam') else 'service','N')
    fixture(n,x+w*.58,518,'exam' if n.startswith('Exam') else 'desk')
# Lobby/cafe and workroom use open perimeter segments rather than inventing rectangular room walls.
rooms.extend([dict(name='Café G6-103',x=364,y=211,width=104,height=108,kind='service'),dict(name='Entrance vestibule G6-101',x=172,y=476,width=153,height=73,kind='circulation')])
poly('Cafe perimeter',[(364,211),(470,211),(470,238)])
poly('Cafe east wall',[(470,296),(470,320),(387,320),(387,359)])
poly('Cafe counter',[(407,335),(507,335),(507,354),(407,354)],height=.85,material='furniture',thickness=9)
poly('Cafe return counter',[(390,360),(390,374),(510,374),(510,356)],height=.85,material='furniture',thickness=6)
room('Workroom G6-103A',563,340,58,93,'service','N')
elevator('Lobby elevator 1',474,239,43,57);elevator('Lobby elevator 2',522,239,45,57)
poly('Lobby west wall',[(45,211),(45,460),(172,460),(172,477)])
poly('Lobby south wall',[(325,477),(325,460),(452,460)])
poly('Lobby staff corridor',[(364,418),(364,434),(622,434)])
poly('Clinic west wall',[(622,254),(622,340)])
poly('Vestibule west',[(172,491),(172,549),(198,549)])
poly('Vestibule east',[(325,491),(325,549),(278,549)])
segment('Vestibule glass doors',231,549,278,549,height=1.7,material='glass',thickness=2)
# Existing lobby columns and central structure preserved.
for x,y,w,d in [(219,322,60,60),(157,208,35,48),(305,208,36,48)]:
    box('Lobby column / structure',x+w/2,y+d/2,w,d,1.9,0,'wall')
    walls.extend([[x,y,x+w,y],[x,y+d,x+w,y+d],[x,y,x,y+d],[x+w,y,x+w,y+d]])
# East vestibule envelope, angled approach, enclosed stairs and outdoor stair run.
poly('East vestibule north',[(1326,165),(1326,141),(1490,141),(1490,179),(1578,179)])
poly('East vestibule glazing',[(1318,364),(1404,315),(1414,332),(1462,258),(1489,274),(1489,181)],height=1.65,material='glass',thickness=3)
poly('East vestibule base',[(1318,364),(1318,332),(1295,332)])
poly('Clinic diagonal facade',[(1102,550),(1102,500),(1128,447),(1178,391),(1196,374)],material='wall')
poly('Facade glazing',[(1110,550),(1110,501),(1138,450),(1185,399),(1205,383)],height=1.5,material='glass',thickness=2)
room('Stair 16 enclosure',1287,418,55,132,'circulation','W',.8)
stair('Stair 16',1296,451,38,66)
stair('Exterior entrance stairs',1347,440,350,77,8)
# Edge-of-crop spaces: retain cut edges rather than pretending the crop is a complete floor.
for n,x,y,w,d,kind,door in [
 ('North lobby elevator 1',155,-20,48,54,'service','S'),('North lobby elevator 2',155,35,48,39,'service','S'),
 ('North core elevator 1',294,-25,54,53,'service','S'),('North core elevator 2',294,30,54,44,'service','S'),
 ('North waiting area',435,-45,309,119,'waiting','S'),
 ('North restroom 1',801,0,64,36,'toilet','S'),('North restroom 2',868,0,70,36,'toilet','S'),
 ('North elevator 3',994,-30,35,80,'service','S'),('North elevator 4',1032,-30,36,80,'service','S'),
 ('North service room',1072,-30,83,104,'service','S'),
 ('East room A',1583,34,67,92,'service','E'),('East room B',1583,129,59,61,'service','E'),
 ('East room C',1645,129,52,61,'service','N'),('East room D',1653,34,44,92,'service','E'),
 ('West edge room A',-25,210,69,108,'service','E'),('West edge room B',-25,324,69,58,'toilet','E'),
 ('West edge room C',-25,386,69,74,'service','E'),('West edge room D',-25,468,69,84,'service','E')]:
    # Clip the visible north/left room geometry to this crop.
    if y<0:d+=y;y=0
    if x<0:w+=x;x=0
    room(n,x,y,w,d,kind,door)
    if 'elevator' in n.lower():
        facilities.append(dict(name=n,kind='elevator',x=x+w/2,y=y+d/2));box(n+' door',x+w/2,y+d,20,2,1.7,0,'metal')
poly('North core partitions',[(204,0),(211,0),(211,74),(99,74),(99,0)])
poly('North core divider',[(350,0),(350,74),(435,74),(435,0)])
poly('North sanitary core',[(747,0),(747,74),(951,74),(951,0)])
for x in [780,801,866,940]:segment('Sanitary partition',x,36,x,72)
segment('North restroom corridor',801,40,938,40)
poly('Northeast enclosure',[(1303,0),(1303,51),(1273,51),(1273,76),(1263,76)])
# Source's curved north wall, sampled into short solid wall segments.
poly('Curved north wall',[(1303,51),(1326,49),(1348,42),(1368,29),(1385,13),(1394,0)])
# Northwest services visible at the cropped boundary.
room('Northwest service room',0,0,70,40,'service','S')
room('Northwest toilet',0,46,64,29,'toilet','E')
elevator('West edge elevator',0,124,29,49)
room('West stair enclosure',33,124,29,49,'circulation','S')
stair('West edge stairs',38,130,19,36,8)
poly('West entry wall',[(64,124),(64,174),(34,174)])
segment('Northwest shaft wall',100,0,100,73)
# Structural columns, exterior bollards and fixtures.
for x,y in [(186,125),(311,127),(814,125),(1151,217),(1267,214),(1267,293),(1326,169),(1326,333),(1468,252),(1545,169),(1210,420),(1210,500)]:
    box('Structural column',x,y,8,8,2,0,'wall')
for x in [20,37,183,198,322,339,450,465,598,742,884,1028,1158,1292]:box('Exterior bollard',x,599,7,7,.75,0,'metal')
for r in rooms:
    if r['kind']=='toilet':
        fixture(r['name'],r['x']+r['width']*.35,r['y']+r['height']*.4,'toilet')
        box(r['name']+' basin',r['x']+r['width']*.77,r['y']+9,11,8,.65,0,'fixture')
for x in [477,517,560,607,655]:
    box('North waiting seat',x,40,16,16,.42,0,'seat');box('North seat back',x,33,16,3,.5,.42,'seat')
for x in [980,1010,1150,1180]:
    box('Waiting seat',x,150,16,15,.42,0,'seat');box('Waiting seat back',x,144,16,3,.5,.42,'seat')
for x in [735,782,825]:fixture('Workstation desk',x,155,'desk')
box('Check-in desk',746,303,36,12,.85,0,'furniture')
box('Cashier counter',355,163,104,9,.85,0,'furniture')
box('Medication cabinet',475,525,10,30,1.5,0,'furniture')
box('Breakroom table',1000,513,35,22,.7,0,'furniture')
box('Ground floor',850,325,1700,650,.2,-.25,'floor')
