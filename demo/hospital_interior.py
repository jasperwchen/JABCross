"""Illustrative hospital set for the scripted café route, separate from the phone map."""


def add_interior(data):
    data['title'] = 'Hospital route demo'
    data['interior'] = True
    data['palette'].update(wall='#eef1ef', pillar='#e2e7e4', floor='#e2e7e5',
                           trim='#739a9c', metal='#aebbc2', wood='#bf9c72',
                           glass='#94c6d1', seat='#286f7b', plaque='#174e60',
                           ceiling='#f4f6f5', ceiling_grid='#c9d2d2',
                           light='#ffffff', grout='#bfcaca')
    objects = data['objects']
    # Replace the staging map's blank nameplates with mounted department signs.
    objects[:] = [obj for obj in objects if not obj['name'].endswith(' sign')]

    def box(name, x, y, width, depth, height, material, base=0):
        objects.append(dict(name=name, position=[x/20-42.5, base+height/2, y/20-16.25],
                            size=[width/20, height, depth/20], rotation=0, material=material))

    # One model unit is approximately half a meter on this staged route.
    for obj in objects:
        if obj['material'] == 'pillar':
            obj['size'][1] = 6
            obj['position'][1] = 3
        elif obj['material'] in ('sign', 'marker'):
            obj['position'][1] *= 2
    # Enclose an L-shaped corridor; no wall or furnishing crosses the walking line.
    corners = [(680, 580), (1040, 580), (1040, 50), (880, 50), (880, 450), (680, 450)]
    for i, ((x, y), (u, v)) in enumerate(zip(corners, corners[1:] + corners[:1])):
        w, d = abs(u-x) or 5, abs(v-y) or 5
        box(f'Corridor wall {i}', (x+u)/2, (y+v)/2, w, d, 6, 'wall')
        box(f'Wall protection {i}', (x+u)/2, (y+v)/2, w+1, d+1, .16, 'trim', 1.6)
        box(f'Handrail {i}', (x+u)/2, (y+v)/2, w+3, d+3, .12, 'wood', 1.85)
        box(f'Skirting {i}', (x+u)/2, (y+v)/2, w+1, d+1, .25, 'metal')
        data['walls'].append([x, y, u, v])
    for x, y, w, d in [(860, 515, 360, 130), (960, 250, 160, 400)]:
        box('Ceiling panel', x, y, w, d, .12, 'ceiling', 6)
    for y in range(70, 580, 30):
        x0 = 680 if y >= 450 else 880
        box('Floor tile joint', (x0+1040)/2, y, 1040-x0, .25, .005, 'grout', .005)
        box('Ceiling seam', (x0+1040)/2, y, 1040-x0, .35, .025, 'ceiling_grid', 5.97)
    for x in range(700, 1040, 30):
        y0 = 50 if x >= 880 else 450
        box('Floor tile joint', x, (y0+580)/2, .25, 580-y0, .005, 'grout', .005)
        box('Ceiling seam', x, (y0+580)/2, .35, 580-y0, .025, 'ceiling_grid', 5.97)
    for x, y in [(750, 525), (850, 525), (940, 525), (940, 405), (940, 285), (940, 165)]:
        box('Ceiling light surround', x, y, 34, 16, .06, 'ceiling_grid', 5.9)
        box('Ceiling light', x, y, 32, 14, .05, 'light', 5.86)
    for name, y in [('Consultation', 410), ('Pharmacy', 325), ('Imaging', 160)]:
        box(name+' door frame', 1036, y, 5, 54, 4.7, 'metal')
        box(name+' door', 1032, y, 3, 46, 4.4, 'wood')
        box(name+' window', 1030, y, 1, 20, 1.5, 'glass', 2.3)
        box(name+' handle', 1028, y-16, 2, 3, .55, 'metal', 1.9)
        box(name+' kick plate', 1030, y, .8, 42, .65, 'metal', .12)
        box(name+' sanitizer', 1033, y-36, 7, 8, .5, 'sign', 2.1)
        box(name+' sanitizer window', 1029, y-36, .5, 4, .2, 'glass', 2.25)
        box(name+' sanitizer lever', 1028, y-36, 2, 6, .08, 'metal', 2.1)
    for x in [780, 810, 840]:
        box('Waiting chair seat', x, 563, 22, 20, .25, 'seat', .85)
        box('Waiting chair back', x, 574, 22, 3, 1.35, 'seat', .9)
        for dx in [-8, 8]:
            box('Waiting chair leg', x+dx, 563, 2, 16, .85, 'metal')
    box('Reception desk', 712, 465, 48, 21, 2, 'wood')
    box('Reception counter', 712, 465, 50, 24, .15, 'sign', 2)
    # Signs are textured by the viewer; their placements are exported with the set.
    data['signs'] = [
        dict(text='Welcome', detail='Reception / Outpatient care', x=740, y=506, height=3.4, rotation=0, width=1.8),
        dict(text='Lobby', detail='← Pharmacy / X-ray', x=959, y=525, height=3.8, rotation=-1.5707963267948966, width=1.8),
        dict(text='Pharmacy', detail='02 / Prescriptions', x=980, y=306, height=3.8, rotation=0, width=1.8),
        dict(text='X-ray', detail='03 / Diagnostic imaging', x=980, y=106, height=3.8, rotation=0, width=1.8),
    ]
    for number, y in [('101', 410), ('102', 325), ('103', 160)]:
        data['signs'].append(dict(text=number, detail='Outpatient', x=1036, y=y+36,
                                  height=3.6, rotation=-1.5707963267948966, width=.8))
    for sign in data['signs']:
        west = sign['rotation'] != 0
        width = sign['width']
        box(sign['text']+' plaque backing', sign['x']+(.35 if west else 0),
            sign['y']-(0 if west else .35), .7 if west else width*20+.8,
            width*20+.8 if west else .7, width/4+.04, 'plaque', sign['height']-width/8-.02)
