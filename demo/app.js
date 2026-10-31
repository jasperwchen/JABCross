import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
const $=s=>document.querySelector(s), host=$('#viewport');
try {
const data=await fetch('./grady-ground.json').then(r=>{if(!r.ok)throw Error('Map data unavailable');return r.json()});
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
const dot=new THREE.Mesh(new THREE.SphereGeometry(.55,24,16),new THREE.MeshStandardMaterial({color:0xe8ad35}));scene.add(dot);
const labels=[];
function addLabel(name,x,y,priority,width=80,height=60,id=null){
 const el=document.createElement('div');el.className='label';el.textContent=name;el.hidden=true;
 $('#labels').appendChild(el);labels.push({el,pos:xyz(x,y,2.4),priority,width,height,id});
}
for(const id of ['entrance','lab','cafe','cashier']){const n=data.nodes[id];addLabel(n.name,n.x,n.y,0,100,80,id)}
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
let path=[],routeIds=[],route,playing=false,offRoute=false,segment=0,fraction=0,last=0,elapsed=0,total=0;
function shortest(target){const distances={entrance:0},previous={},todo=new Set(Object.keys(data.nodes));while(todo.size){let u=[...todo].reduce((a,b)=>(distances[a]??Infinity)<(distances[b]??Infinity)?a:b);todo.delete(u);if(u===target)break;for(const [a,b,w] of data.edges){let v=a===u?b:b===u?a:null;if(v&&todo.has(v)&&(distances[u]??Infinity)+w<(distances[v]??Infinity)){distances[v]=distances[u]+w;previous[v]=u}}}const result=[target];while(result[0]!=='entrance'){const n=previous[result[0]];if(!n)throw Error('Destination is unreachable');result.unshift(n)}return result}
function say(text){$('#guidance').textContent=text;if($('#voice').checked&&'speechSynthesis'in window){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(text))}}
function reset(){playing=false;offRoute=false;segment=0;fraction=0;elapsed=0;$('#play').textContent='Simulate walk';$('#progress').value=0;dot.position.copy(path[0]);say('Ready at the entrance.')}
function choose(){if(route){scene.remove(route);route.geometry.dispose();route.material.dispose()}routeIds=shortest($('#destination').value);path=routeIds.map(id=>{const n=data.nodes[id];return xyz(n.x,n.y,.65)});total=path.slice(1).reduce((s,p,i)=>s+p.distanceTo(path[i]),0);route=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());route.geometry.dispose();const curve=new THREE.CurvePath();for(let i=1;i<path.length;i++)curve.add(new THREE.LineCurve3(path[i-1],path[i]));route.geometry=new THREE.TubeGeometry(curve,Math.ceil(total*3),.13,8,false);route.material.color.set(0x14856c);scene.add(route);$('#target').textContent=data.nodes[$('#destination').value].name;reset()}
$('#destination').onchange=choose;$('#reset').onclick=reset;$('#play').onclick=()=>{if(offRoute||segment>=path.length-1)reset();playing=!playing;$('#play').textContent=playing?'Pause walk':'Resume walk';if(playing)say('Follow the highlighted route.')};
function view(top){camera.position.set(...(top?[0,100,.01]:[4,73,64]));camera.position.multiplyScalar(Math.max(1,1.3/camera.aspect));controls.target.set(0,0,0);$('#top').setAttribute('aria-pressed',top);$('#angled').setAttribute('aria-pressed',!top);controls.update()}$('#top').onclick=()=>view(true);$('#angled').onclick=()=>view(false);
// Explicit adapter for the team's future perception integration. Does not infer live tracking.
window.jabCross={setMarker(id){const key=Object.keys(data.nodes).find(k=>data.nodes[k].marker===id);if(!key)return false;const node=data.nodes[key],at=routeIds.indexOf(key);playing=false;offRoute=at<0;if(!offRoute){segment=at;fraction=0;elapsed=path.slice(1,at+1).reduce((s,p,i)=>s+p.distanceTo(path[i]),0);$('#progress').value=elapsed/total}$('#play').textContent=offRoute||at===path.length-1?'Replay walk':'Resume simulation';dot.position.copy(xyz(node.x,node.y,.65));say('Marker received: '+node.name);return true},map:data};
function resize(){camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.clientWidth,host.clientHeight)}new ResizeObserver(resize).observe(host);resize();view(false);choose();
function animate(t){requestAnimationFrame(animate);let dt=Math.min((t-last)/1000,.05);last=t;if(playing&&segment<path.length-1){let budget=dt*5;while(budget>0&&segment<path.length-1){const len=path[segment].distanceTo(path[segment+1]),step=Math.min(budget,len*(1-fraction));fraction+=step/len;elapsed+=step;budget-=step;dot.position.lerpVectors(path[segment],path[segment+1],Math.min(fraction,1));if(fraction>=.999999){segment++;fraction=0;if(segment===path.length-1){playing=false;$('#play').textContent='Replay walk';say('You have arrived at '+$('#target').textContent+'.')}else say('Continue along the highlighted route.')}}$('#progress').value=Math.min(elapsed/total,1)}controls.update();updateLabels();renderer.render(scene,camera)}requestAnimationFrame(animate);
} catch(error){$('#error').textContent='Could not load the 3D viewer: '+error.message;console.error(error)}


