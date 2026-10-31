"""Four-pillar staged café route; coordinates are illustrative, steps are estimates."""


def build_cafe():
    palette = {'floor': '#edf0e9', 'pillar': '#b9c6bc', 'plinth': '#dde4db',
               'marker': '#2864aa', 'sign': '#f9fbf7'}
    objects, walls, pillars = [], [], []

    def box(name, x, y, width, depth, height, material, base=0):
        objects.append(dict(name=name, position=[x/20-42.5, base+height/2, y/20-16.25],
                            size=[width/20, height, depth/20], rotation=0, material=material))

    # Same turn geometry as AGENT-HANDOFF.md. Pillars sit outside the walking line.
    nodes = {
        'entrance': dict(name='Entrance', x=740, y=525, marker=0, facing=0,
                         aliases=['entrance', 'main entrance', 'front door', 'exit']),
        'lobby': dict(name='Lobby', x=940, y=525, marker=1, facing=90, aliases=['lobby']),
        'pharmacy': dict(name='Pharmacy', x=940, y=325, marker=2, facing=0,
                         aliases=['pharmacy', 'medicine', 'prescription']),
        'xray': dict(name='X-ray', x=940, y=125, marker=3, facing=0,
                     aliases=['x-ray', 'x ray', 'xray', 'radiology', 'radiation lab', 'imaging', 'lab']),
    }
    box('Cafeteria floor', 850, 325, 440, 660, .08, 'floor', -.08)
    for key, x, y, face in [('entrance', 740, 485, 'south'), ('lobby', 980, 525, 'west'),
                             ('pharmacy', 980, 285, 'south'), ('xray', 980, 85, 'south')]:
        node = nodes[key]
        pillars.append(dict(marker=node['marker'], x=x, y=y, size=40))
        box('Pillar ' + str(node['marker']), x, y, 40, 40, 2.4, 'pillar')
        box(node['name'] + ' base', x, y, 44, 44, .08, 'plinth')
        x0, y0, x1, y1 = x-20, y-20, x+20, y+20
        walls.extend([[x0,y0,x1,y0], [x1,y0,x1,y1], [x1,y1,x0,y1], [x0,y1,x0,y0]])
        mx, my = (x-20, y) if face == 'west' else (x, y+20)
        node.update(markerFace=face, markerPosition=[mx, my])
        box('Marker ' + str(node['marker']) + ' face', mx, my,
            .8 if face == 'west' else 6, 6 if face == 'west' else .8, .3, 'marker', 1.1)
        box(node['name'] + ' sign', mx, my, .9 if face == 'west' else 20,
            20 if face == 'west' else .9, .35, 'sign', 1.5)
    return dict(
        venue='cafe', title='Cafeteria demo',
        source='cafe-route-sketch.png; final staging in AGENT-HANDOFF.md',
        units='Illustrative plan units; each 200-unit leg is approximately 5 m; edge values are estimated steps',
        coordinateSystem='x right, y down; 3D x=x/20-42.5, z=y/20-16.25',
        stepCalibration='7 steps per leg is an estimate; replace after walking the venue route',
        rooms=[], facilities=[], palette=palette, objects=objects, walls=walls, pillars=pillars,
        nodes=nodes, edges=[['entrance','lobby',7], ['lobby','pharmacy',7], ['pharmacy','xray',7]],
        destinations=['pharmacy','xray'],
        view=dict(center=[0, 0, 0], distance=52),
    )
