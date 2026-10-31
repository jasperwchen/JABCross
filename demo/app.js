import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
const $=s=>document.querySelector(s), host=$('#viewport');
try {
const venue=new URLSearchParams(location.search).get('map')==='cafe'?'cafe':'hospital';
const mapBase=`./maps/${venue}/`;
const data=await fetch(mapBase+'grady-ground.json').then(r=>{if(!r.ok)throw Error('Map data unavailable');return r.json()});
const cafe=data.venue==='cafe';
for(const link of document.querySelectorAll('.map-tabs a'))if(link.dataset.map===venue)link.setAttribute('aria-current','page');
for(const link of document.querySelectorAll('footer a[download]'))link.href=mapBase+link.getAttribute('href');
$('#start-name').textContent=data.nodes.entrance.name+' · Marker 0';
$('#venue').textContent=cafe?'GSMST cafeteria demo':'Grady Memorial Hospital';
$('#map-heading').textContent=cafe?'GSMST cafeteria demo':'Grady Memorial Hospital';
document.title=cafe?'JabCross · GSMST cafeteria demo':'JabCross · Grady Memorial Hospital';
$('#destination').replaceChildren(...data.destinations.map(id=>{const option=document.createElement('option');option.value=id;option.textContent=data.nodes[id].name;return option}));
if(cafe)$('#destination').value='xray';
if(!cafe){$('#map-description').textContent='Plan a route through the entrance and outpatient area, then preview the walk.';$('#scope').textContent='Ground floor · GMH-G';$('#map-scope').textContent='Entrance / outpatient area';$('#route-note').textContent='Based on the Grady floor plan. Routes and distances are illustrative and have not been validated for patient use.'}
const scene=new THREE.Scene();scene.background=new THREE.Color('#eef0e8');
const camera=new THREE.PerspectiveCamera(42,1,.1,500);camera.position.set(4,73,64);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.46;controls.minDistance=15;controls.maxDistance=320;
scene.add(new THREE.HemisphereLight(0xffffff,0x809083,2.4));const light=new THREE.DirectionalLight(0xffffff,2.2);light.position.set(-20,60,30);scene.add(light);
const xyz=(x,y,h=.2)=>new THREE.Vector3(x/20-42.5,h,y/20-16.25);
const materials=Object.fromEntries(Object.entries(data.palette).map(([name,color])=>[name,new THREE.MeshStandardMaterial({color,roughness:.8,metalness:name==='metal'?.15:0})]));
const cube=new THREE.BoxGeometry(1,1,1);
for(const obj of data.objects){const mesh=new THREE.Mesh(cube,materials[obj.material]);mesh.name=obj.name;mesh.position.fromArray(obj.position);mesh.scale.fromArray(obj.size);mesh.rotation.y=obj.rotation;if(obj.material==='wall'){const edge=new THREE.LineSegments(new THREE.EdgesGeometry(cube),new THREE.LineBasicMaterial({color:0x93a99b,transparent:true,opacity:.45}));mesh.add(edge)}scene.add(mesh)}
// The SVG covers the whole sheet. Crop it to the same PDF coordinates as the modeled area.
// Original raster reference: longest side 4200 px, crop (1550,1850,1700,650).
if(!cafe){
const svgResponse=await fetch('./grady-ground.svg');
if(!svgResponse.ok)throw Error('SVG floor plan unavailable');
const svgText=await svgResponse.text(), unit=1224/4200;
const textureWidth=Math.min(4096,renderer.capabilities.maxTextureSize);
const croppedSvg=svgText.replace(/<svg\b[^>]*>/,`<svg xmlns="http://www.w3.org/2000/svg" width="${textureWidth}" height="${Math.round(textureWidth*650/1700)}" viewBox="${1550*unit} ${1850*unit} ${1700*unit} ${650*unit}">`);
const svgUrl=URL.createObjectURL(new Blob([croppedSvg],{type:'image/svg+xml'}));
let texture;
try{texture=await new THREE.TextureLoader().loadAsync(svgUrl)}finally{URL.revokeObjectURL(svgUrl)}
texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
const reference=new THREE.Mesh(new THREE.PlaneGeometry(85,32.5),new THREE.MeshBasicMaterial({map:texture,transparent:true,opacity:.38,depthWrite:false}));reference.rotation.x=-Math.PI/2;reference.position.y=.045;reference.visible=$('#reference').checked;scene.add(reference);$('#reference').onchange=e=>reference.visible=e.target.checked;
}else{$('#reference').checked=false;$('#reference').closest('label').hidden=true;}
const dot=new THREE.Mesh(new THREE.SphereGeometry(.55,24,16),new THREE.MeshStandardMaterial({color:0xe8ad35}));scene.add(dot);
const labels=[];
function addLabel(name,x,y,priority,width=80,height=60,id=null){
 const el=document.createElement('div');el.className='label';el.textContent=name;el.hidden=true;
 $('#labels').appendChild(el);labels.push({el,pos:xyz(x,y,2.4),priority,width,height,id});
}
for(const id of ['entrance',...(cafe?['lobby']:[]),...data.destinations]){const n=data.nodes[id],pillar=data.pillars?.find(p=>p.marker===n.marker);addLabel(cafe?`${n.marker} · ${n.name}`:n.name,pillar?.x??n.x,pillar?.y??n.y,0,100,80,id)}
for(const room of data.rooms){
 if(/^(Cashier|Caf\u00e9|Lab waiting|Entrance vestibule)/.test(room.name))continue;
 const name=room.name.replace(/\s+[BG]\d+-\d+[A-Z]?/g,'').replace(' enclosure','');
 const landmark=/waiting|Check-in|Stair|elevator/i.test(name);
 addLabel(name,room.x+room.width/2,room.y+room.height/2,landmark?1:2,room.width,room.height);
}
// Exterior facilities have no enclosing room in the room catalog.
for(const f of data.facilities){if(f.name.startsWith('Exterior'))addLabel(f.name,f.x,f.y,1,200,70)}
const labelMeasure=document.createElement('canvas').getContext('2d');labelMeasure.font='11px "Segoe UI", sans-serif';
for(const label of labels)label.pixelWidth=Math.ceil(labelMeasure.measureText(label.el.textContent).width)+18;
const occupied=[],projected=new THREE.Vector3();
function updateLabels(){
 const width=host.clientWidth,height=host.clientHeight,hostRect=host.getBoundingClientRect();
 occupied.length=0;
 // Reserve screen chrome so labels never obscure view controls or the legend.
 for(const selector of ['.tools','.maptitle','.legend','.hint']){const r=$(selector).getBoundingClientRect();occupied.push({left:r.left-hostRect.left-6,right:r.right-hostRect.left+6,top:r.top-hostRect.top-6,bottom:r.bottom-hostRect.top+6})}
 const selected=$('#destination').value;
 const ordered=[...labels].sort((a,b)=>(a.id===selected?-2:a.id==='entrance'?-1:a.priority)-(b.id===selected?-2:b.id==='entrance'?-1:b.priority));
 for(const label of ordered){
  const {el,pos,pixelWidth}=label;el.hidden=true;
  projected.copy(pos).project(camera);
  if(projected.z< -1||projected.z>1)continue;
  const x=(projected.x*.5+.5)*width,y=(-projected.y*.5+.5)*height;
  const pixelsPerUnit=height/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*camera.position.distanceTo(pos));
  if(label.priority===2&&(label.width/20*pixelsPerUnit<38||label.height/20*pixelsPerUnit<22))continue;
  const rect={left:x-pixelWidth/2-5,right:x+pixelWidth/2+5,top:y-27,bottom:y+3};
  if(rect.left<6||rect.right>width-6||rect.top<6||rect.bottom>height-6)continue;
  if(occupied.some(r=>rect.left<r.right&&rect.right>r.left&&rect.top<r.bottom&&rect.bottom>r.top))continue;
  occupied.push(rect);el.style.left=x+'px';el.style.top=y+'px';el.style.width=pixelWidth+'px';el.hidden=false;
 }
}
// Line of sight: rays at chest height stop at the first object that reaches that height.
const SIGHT_HEIGHT=.8,SIGHT_RANGE=12,SIGHT_FOV=THREE.MathUtils.degToRad(70),SIGHT_RAYS=73,TURN_SPEED=4;
const blockers=data.objects.filter(o=>Math.abs(o.position[1]-SIGHT_HEIGHT)<=o.size[1]/2).map(o=>({x:o.position[0],z:o.position[2],hx:o.size[0]/2,hz:o.size[2]/2,c:Math.cos(o.rotation),s:Math.sin(o.rotation)}));
function cast(x,z,dx,dz,range=Infinity){let nearest=range;for(const b of blockers){const px=x-b.x,pz=z-b.z,ax=b.c*px-b.s*pz,az=b.s*px+b.c*pz,vx=b.c*dx-b.s*dz,vz=b.s*dx+b.c*dz;let near=0,far=nearest,miss=false;for(const [a,v,h] of [[ax,vx,b.hx],[az,vz,b.hz]]){if(Math.abs(v)<1e-9){if(Math.abs(a)>h)miss=true}else{const t1=(-h-a)/v,t2=(h-a)/v;near=Math.max(near,Math.min(t1,t2));far=Math.min(far,Math.max(t1,t2))}}if(!miss&&near<=far)nearest=near}return nearest}
const beamVertices=2*SIGHT_RAYS+1,beamPositions=new Float32Array(beamVertices*3),beamColors=new Float32Array(beamVertices*4),beamIndex=[];
for(let i=0;i<beamVertices;i++)beamColors.set([.96,.62,.08,i?0:.6],i*4);
for(let i=0;i<SIGHT_RAYS-1;i++){const low=1+i,high=1+SIGHT_RAYS+i;beamIndex.push(0,low,low+1,0,high,high+1,low,low+1,high+1,low,high+1,high)}
const beamGeometry=new THREE.BufferGeometry();beamGeometry.setAttribute('position',new THREE.BufferAttribute(beamPositions,3));beamGeometry.setAttribute('color',new THREE.BufferAttribute(beamColors,4));beamGeometry.setIndex(beamIndex);
const beam=new THREE.Mesh(beamGeometry,new THREE.MeshBasicMaterial({vertexColors:true,transparent:true,depthWrite:false,side:THREE.DoubleSide}));beam.frustumCulled=false;beam.renderOrder=2;scene.add(beam);
// Each marker sits on the first wall ahead of its node, where a walker with that node's facing sees it.
const markerGeometry=new THREE.SphereGeometry(.36,16,12),markerIdle=new THREE.MeshBasicMaterial({color:0x2b5fb8,transparent:true,depthTest:false}),markerSeen=new THREE.MeshBasicMaterial({color:0x00b7ff,transparent:true,depthTest:false}),markers=[];
for(const node of Object.values(data.nodes)){
 const angle=THREE.MathUtils.degToRad(node.facing),dx=Math.sin(angle),dz=-Math.cos(angle),mesh=new THREE.Mesh(markerGeometry,markerIdle);mesh.name='Marker '+node.marker;mesh.renderOrder=3;
 if(node.markerPosition){mesh.position.copy(xyz(...node.markerPosition,1.25));mesh.position.addScaledVector(new THREE.Vector3(-dx,0,-dz),.06)}
 else{mesh.position.copy(xyz(node.x,node.y,1));mesh.position.addScaledVector(new THREE.Vector3(dx,0,dz),cast(mesh.position.x,mesh.position.z,dx,dz)-.05);}
 // Nodes in a straight line share a wall spot, so spread those markers along the wall.
 while(markers.some(m=>m.position.distanceTo(mesh.position)<.8))mesh.position.add(new THREE.Vector3(-dz*.8,0,dx*.8));
 markers.push(mesh);scene.add(mesh);
}
function updateSight(){
 const {x,z}=dot.position,forwardX=Math.sin(heading),forwardZ=-Math.cos(heading);
 beamPositions.set([x,SIGHT_HEIGHT,z]);
 for(let i=0;i<SIGHT_RAYS;i++){
  const angle=heading+SIGHT_FOV*(i/(SIGHT_RAYS-1)-.5),dx=Math.sin(angle),dz=-Math.cos(angle),hit=cast(x,z,dx,dz,SIGHT_RANGE),reach=Math.max(hit-.02,0),alpha=hit<SIGHT_RANGE?.08+.42*(1-hit/SIGHT_RANGE):0;
  const low=1+i,high=1+SIGHT_RAYS+i,spread=reach*.18;
  beamPositions.set([x+dx*reach,Math.max(.06,SIGHT_HEIGHT-spread),z+dz*reach],low*3);beamPositions.set([x+dx*reach,Math.min(1.9,SIGHT_HEIGHT+spread),z+dz*reach],high*3);
  beamColors[low*4+3]=beamColors[high*4+3]=alpha;
 }
 beamGeometry.attributes.position.needsUpdate=true;beamGeometry.attributes.color.needsUpdate=true;
 for(const mesh of markers){
  const dx=mesh.position.x-x,dz=mesh.position.z-z,distance=Math.hypot(dx,dz),seen=distance<SIGHT_RANGE&&(dx*forwardX+dz*forwardZ)/distance>Math.cos(SIGHT_FOV/2)&&cast(x,z,dx/distance,dz/distance,distance)>=distance-.1;
  mesh.material=seen?markerSeen:markerIdle;mesh.scale.setScalar(seen?1.5:1);
 }
}
let path=[],routeIds=[],route,playing=false,offRoute=false,segment=0,fraction=0,last=0,elapsed=0,total=0,heading=0,targetHeading=0;
const legHeading=i=>Math.atan2(path[i+1].x-path[i].x,-(path[i+1].z-path[i].z));
function shortest(target){const distances={entrance:0},previous={},todo=new Set(Object.keys(data.nodes));while(todo.size){let u=[...todo].reduce((a,b)=>(distances[a]??Infinity)<(distances[b]??Infinity)?a:b);todo.delete(u);if(u===target)break;for(const [a,b,w] of data.edges){let v=a===u?b:b===u?a:null;if(v&&todo.has(v)&&(distances[u]??Infinity)+w<(distances[v]??Infinity)){distances[v]=distances[u]+w;previous[v]=u}}}const result=[target];while(result[0]!=='entrance'){const n=previous[result[0]];if(!n)throw Error('Destination is unreachable');result.unshift(n)}return result}
function say(text){$('#guidance').textContent=text;if($('#voice').checked&&'speechSynthesis'in window){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(text))}}
function instruction(i,fromHeading){const error=Math.atan2(Math.sin(legHeading(i)-fromHeading),Math.cos(legHeading(i)-fromHeading))*180/Math.PI;const edge=data.edges.find(([a,b])=>a===routeIds[i]&&b===routeIds[i+1]||b===routeIds[i]&&a===routeIds[i+1]);return `${Math.abs(error)>15?`Turn ${error>0?'right':'left'} about ${Math.round(Math.abs(error)/5)*5} degrees. `:''}Walk forward about ${edge[2]} steps.`}
function reset(){playing=false;offRoute=false;segment=0;fraction=0;elapsed=0;$('#play').textContent='Simulate walk';$('#progress').value=0;dot.position.copy(path[0]);heading=targetHeading=THREE.MathUtils.degToRad(data.nodes.entrance.facing);say('Ready at the entrance. Facing marker 0.')}
function choose(){if(route){scene.remove(route);route.geometry.dispose();route.material.dispose()}routeIds=shortest($('#destination').value);path=routeIds.map(id=>{const n=data.nodes[id];return xyz(n.x,n.y,.65)});total=path.slice(1).reduce((s,p,i)=>s+p.distanceTo(path[i]),0);route=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());route.geometry.dispose();const curve=new THREE.CurvePath();for(let i=1;i<path.length;i++)curve.add(new THREE.LineCurve3(path[i-1],path[i]));route.geometry=new THREE.TubeGeometry(curve,Math.ceil(total*3),.13,8,false);route.material.color.set(0x14856c);scene.add(route);$('#target').textContent=data.nodes[$('#destination').value].name;reset()}
$('#destination').onchange=choose;$('#reset').onclick=reset;$('#play').onclick=()=>{if(offRoute||segment>=path.length-1)reset();playing=!playing;$('#play').textContent=playing?'Pause walk':'Resume walk';if(playing){say(instruction(segment,heading));targetHeading=legHeading(segment)}};
let overhead=false;
function view(top){overhead=top;const distance=data.view?.distance??100;camera.position.set(...(top?[0,distance,.01]:[distance*.3,distance*.73,distance*.64]));camera.position.multiplyScalar(Math.max(1,1.3/camera.aspect));controls.target.fromArray(data.view?.center??[0,0,0]);$('#top').setAttribute('aria-pressed',top);$('#angled').setAttribute('aria-pressed',!top);controls.update()}$('#top').onclick=()=>view(true);$('#angled').onclick=()=>view(false);
// Explicit adapter for the team's future perception integration. Does not infer live tracking.
window.jabCross={setMarker(id){const key=Object.keys(data.nodes).find(k=>data.nodes[k].marker===id);if(!key)return false;const node=data.nodes[key],at=routeIds.indexOf(key);playing=false;offRoute=at<0;if(!offRoute){segment=at;fraction=0;elapsed=path.slice(1,at+1).reduce((s,p,i)=>s+p.distanceTo(path[i]),0);$('#progress').value=elapsed/total}$('#play').textContent=offRoute||at===path.length-1?'Replay walk':'Resume simulation';dot.position.copy(xyz(node.x,node.y,.65));heading=targetHeading=THREE.MathUtils.degToRad(node.facing);say('Marker received: '+node.name);return true},map:data};
function resize(){camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.clientWidth,host.clientHeight);view(overhead)}new ResizeObserver(resize).observe(host);resize();view(cafe);choose();
function animate(t){
 requestAnimationFrame(animate);
 const dt=Math.min((t-last)/1000,.05);last=t;
 if(playing&&segment<path.length-1){
  const turn=Math.atan2(Math.sin(targetHeading-heading),Math.cos(targetHeading-heading));
  let budget=Math.abs(turn)<.04?dt*5:0;
  while(budget>0&&segment<path.length-1){
   const len=path[segment].distanceTo(path[segment+1]),step=Math.min(budget,len*(1-fraction));
   fraction+=step/len;elapsed+=step;budget-=step;
   dot.position.lerpVectors(path[segment],path[segment+1],Math.min(fraction,1));
   if(fraction>=.999999){
    segment++;fraction=0;budget=0;
    if(segment===path.length-1){playing=false;$('#play').textContent='Replay walk';say('You have arrived at '+$('#target').textContent+'.')}
    else{say(instruction(segment,legHeading(segment-1)));targetHeading=legHeading(segment)}
   }
  }
  $('#progress').value=Math.min(elapsed/total,1);
  const remainingTurn=Math.atan2(Math.sin(targetHeading-heading),Math.cos(targetHeading-heading));
  heading+=Math.sign(remainingTurn)*Math.min(Math.abs(remainingTurn),dt*TURN_SPEED);
 }
 updateSight();controls.update();updateLabels();renderer.render(scene,camera);
}requestAnimationFrame(animate);
} catch(error){$('#error').textContent='Could not load the 3D viewer: '+error.message;console.error(error)}


