"""Hand-built arena: dimensionally constructed SVG / PNG / offline Canvas 3D.
Units are mm; Z=0 is walking surface; floor underside Z=-5.
No 3D-print parts. No external assets or network calls.
"""
from pathlib import Path
import math,json,html
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
TAU=math.tau
INK='#35515b';PVC='#e8efed';WALL='#577c83';WOOD='#c5a173'
FIGMA_LOW_DETAIL=False

def tint(c,k):return '#'+''.join(f'{max(0,min(255,round(int(c[i:i+2],16)*k))):02x}' for i in (1,3,5))
def poly(ps,c,ident,stroke=None,layer=2,width=.65):return dict(kind='poly',points=ps,color=c,id=ident,stroke=stroke,layer=layer,width=width)
def line(ps,c,ident,width=1.5,layer=2):return dict(kind='line',points=ps,color=c,id=ident,width=width,layer=layer)
def box(x,y,z,l,w,h,c,ident,layer=2):
 X,Y,Z=x+l,y+w,z+h
 v=[[[x,y,z],[X,y,z],[X,y,Z],[x,y,Z]],[[X,y,z],[X,Y,z],[X,Y,Z],[X,y,Z]],[[X,Y,z],[x,Y,z],[x,Y,Z],[X,Y,Z]],[[x,Y,z],[x,y,z],[x,y,Z],[x,Y,Z]],[[x,y,Z],[X,y,Z],[X,Y,Z],[x,Y,Z]]]
 return [poly(p,tint(c,k),ident, '#94a6a6' if layer==0 else tint(c,.65),layer) for p,k in zip(v,[.78,.87,.91,.8,1.06])]
def sphere(x,y,z,r,c,ident,straps=False):
 a=[];N=40;M=24
 if FIGMA_LOW_DETAIL:N,M=(12,4) if straps else (8,2)
 q=lambda i,j:[x+r*math.sin(math.pi*j/M)*math.cos(TAU*i/N),y+r*math.sin(math.pi*j/M)*math.sin(TAU*i/N),z+r*math.cos(math.pi*j/M)]
 for j in range(M):
  for i in range(N):
   u=TAU*(i+.5)/N;v=math.pi*(j+.5)/M
   k=.78+.18*math.cos(v)+.13*math.sin(v)*math.cos(u+1)
   a.append(poly([q(i,j),q(i+1,j),q(i+1,j+1),q(i,j+1)],tint(c,k),ident))
 # Two orthogonal 10-mm surface ribbons. Bands conform to the ball, rather than screen-width lines.
 if straps:
  rr=math.sqrt((r+.35)**2-25)
  steps=16 if FIGMA_LOW_DETAIL else 120
  for axis in [0,1]:
   for i in range(steps):
    ps=[]
    for ang,cross in [(TAU*i/steps,-5),(TAU*(i+1)/steps,-5),(TAU*(i+1)/steps,5),(TAU*i/steps,5)]:
     ps.append([x+rr*math.cos(ang)*(1-axis)+cross*axis,y+rr*math.cos(ang)*axis+cross*(1-axis),z+rr*math.sin(ang)])
    ribbon=poly(ps,'#e8d8b8',ident+'-strap');ribbon['sphere_overlay']=[x,y,z,r];a.append(ribbon)
 return a
def cylinder(x,y,z,r,h,c,ident,inner=0):
 a=[];N=8 if FIGMA_LOW_DETAIL else 40
 for i in range(N):
  u,v=TAU*i/N,TAU*(i+1)/N
  q=lambda rad,t,zz:[x+rad*math.cos(t),y+rad*math.sin(t),zz]
  a.append(poly([q(r,u,z),q(r,v,z),q(r,v,z+h),q(r,u,z+h)],tint(c,.82+.12*math.cos(u)),ident))
  a.append(poly([q(r,u,z+h),q(r,v,z+h),q(inner,v,z+h),q(inner,u,z+h)],c,ident))
 return a
def ring(cx,cy,color,ident,angle):
 a=[];N=24 if FIGMA_LOW_DETAIL else 90
 for i in range(N):
  t,u=TAU*i/N,TAU*(i+1)/N
  a.append(poly([[cx+90*math.cos(t),cy+90*math.sin(t),.15],[cx+90*math.cos(u),cy+90*math.sin(u),.15],[cx+82*math.cos(u),cy+82*math.sin(u),.15],[cx+82*math.cos(t),cy+82*math.sin(t),.15]],color,ident,layer=1))
 ca,sa=math.cos(angle),math.sin(angle)
 def p(x,y):return[cx+x*ca-y*sa,cy+x*sa+y*ca,.2]
 a.append(poly([p(x,y) for x,y in [[-34,-12],[15,-12],[15,-29],[61,0],[15,29],[15,12],[-34,12]]],color,ident,layer=1))
 # Dashed 200 x 90 footprint: graphic only, not a physical robot proxy.
 corners=[[-100,-45],[100,-45],[100,45],[-100,45],[-100,-45]]
 for q,r in zip(corners,corners[1:]):
  n=math.ceil(math.dist(q,r)/12)
  for i in range(0,n,2):
   a.append(line([p(q[0]+(r[0]-q[0])*i/n,q[1]+(r[1]-q[1])*i/n),p(q[0]+(r[0]-q[0])*min(i+1,n)/n,q[1]+(r[1]-q[1])*min(i+1,n)/n)],'#8f9d9e',ident+'-robot-reference',1.2,1))
 return a

def brace_x(x,y,z,sgn,ident):
 # Triangular prism: 5 along wall; 15 across foot; 30 vertical.
 p=[[x,y,z],[x,y+sgn*15,z],[x,y,z+30]]
 q=[[a+5,b,c] for a,b,c in p]
 return[poly(p,tint(PVC,.84),ident,INK),poly(q,PVC,ident,INK)]+[poly([p[i],p[(i+1)%3],q[(i+1)%3],q[i]],PVC,ident,INK) for i in range(3)]

def wall(ident,x,y,l,h,branch=False):
 a=[]
 if not branch:
  a+=box(x,y,0,l,40,5,PVC,ident+'-foot')
  a+=box(x,y+17.5,5,l,5,h-5,WALL,ident+'-panel')
  a+=brace_x(x+20,y+17.5,5,-1,ident+'-brace1')
  a+=brace_x(x+l-25,y+22.5,5,1,ident+'-brace2')
  # yellow strip: a printed flat face, not protruding geometry.
  a.append(poly([[x+1.5,y+17.49,7],[x+l-1.5,y+17.49,7],[x+l-1.5,y+17.49,14],[x+1.5,y+17.49,14]],'#e4b84c',ident+'-print-front'))
  a.append(poly([[x+1.5,y+22.51,7],[x+l-1.5,y+22.51,7],[x+l-1.5,y+22.51,14],[x+1.5,y+22.51,14]],'#e4b84c',ident+'-print-back'))
 else:
  # Build the same 120-long module and rotate XY to run north-south.
  for p in wall(ident,0,0,l,h,False):
   p['points']=[[x+b,y+a,c] for a,b,c in p['points']];a.append(p)
 return a

def target(cx,cy,s,color,state='ready',ident='target'):
 # Local +Y is rearward; mirrored for blue target.
 a=[]
 def bx(x,y,z,l,w,h,col,tag):
  Y=cy+s*y if s>0 else cy+s*(y+w)
  a.extend(box(cx+x,Y,z,l,w,h,col,ident+'-'+tag))
 bx(-80,90,0,160,120,5,PVC,'base')
 bx(-10,140,5,20,20,173,WOOD,'post')
 bx(-10,-20,178,20,200,20,WOOD,'arm')
 # Steel base brackets: 40 x 40 approximate, 15 wide; hardware indicative.
 for side in [-1,1]:
  xx=-50 if side<0 else 10
  bx(xx,142.5,5.1,40,15,1.5,'#9ca4a6','base-bracket-horizontal')
  bx(-11.5 if side<0 else 10,142.5,5,1.5,15,40,'#9ca4a6','base-bracket-vertical')
 # Small arm/post brackets, 20x20. No fake 3D printed connector.
 for yy in [120,160]:
  bx(-7.5,yy,176.4,15,20,1.5,'#9ca4a6','arm-bracket-horizontal')
  bx(-7.5,yy+18.5 if yy==120 else yy,158,15,1.5,20,'#9ca4a6','arm-bracket-vertical')
 a+=cylinder(cx,cy,176,4,2,'#6e777d',ident+'-magnet')
 ball_y=0 if state=='ready' else 40; z=135 if state=='ready' else 55
 a+=sphere(cx,cy+s*ball_y,z,35,color,ident+'-ball',True)
 # Example stack t=8: overlapped strap/glue3 + cap1 + washer1.5 + paper0.5 + magnet2.
 bx(-5,ball_y-5,z+35,10,10,3,'#f4e6c9','strap-overlap')
 bx(-10,ball_y-10,z+38,20,20,1,'#ddd5b9','cap')
 a+=cylinder(cx,cy+s*ball_y,z+39,7,1.5,'#8e969c',ident+'-washer',2)
 a+=cylinder(cx,cy+s*ball_y,z+40.5,6,.5,'#f4e6c9',ident+'-paper-spacer')
 a.append(line([[cx,cy+s*ball_y,z+35],[cx,cy+s*40,178]],'#615d52',ident+'-cord',1.25))
 if state=='ready':
  # Approximately 47 mm of available travel is collected on the arm top.
  a.append(line([[cx,cy+s*40,198],[cx+6,cy+s*47,200],[cx-5,cy+s*54,200],[cx+4,cy+s*62,200]],'#615d52',ident+'-slack-on-top',1.25))
  a+=sphere(cx+4,cy+s*62,203,5,'#9b8465',ident+'-stop-bead')
 else:a+=sphere(cx,cy+s*40,203,5,'#9b8465',ident+'-stop-bead')
 for p in a:
  if any(p['id'].endswith('-'+suf) for suf in ['cap','washer','paper-spacer','strap-overlap']):p['ball_hardware']=[cx,cy+s*ball_y,z,35]
 return a

WALLS=[('LH1',20,340,180,60,False),('LH2',200,340,180,80,False),('LH3',380,340,180,100,False),('LH4',560,340,180,80,False),('LS',500,380,120,80,True),('RH1',1060,880,180,60,False),('RH2',880,880,180,80,False),('RH3',700,880,180,100,False),('RH4',520,880,180,80,False),('RS',720,760,120,80,True)]
def arena(layout='A',state='ready'):
 a=[]
 for r in range(2):
  for c in range(3):a+=box(c*420,r*630,-5,420,630,5,'#f0f3ef' if(c+r)%2==0 else '#e3eae7',f'F{r*3+c+1}',0)
 a+=ring(260,180,'#d95853','red-spawn',0 if layout=='A' else math.pi/2)
 a+=ring(1000,1080,'#3585cd','blue-spawn',math.pi if layout=='A' else -math.pi/2)
 for i in range(3):
  a+=box(i*420,0,0,420,20,30,WOOD,'south-rail-'+str(i+1))
  a+=box(i*420,1240,0,420,20,30,WOOD,'north-rail-'+str(i+1))
 for i in range(2):
  a+=box(0,20+i*610,0,20,610,30,WOOD,'west-rail-'+str(i+1))
  a+=box(1240,20+i*610,0,20,610,30,WOOD,'east-rail-'+str(i+1))
 for w in WALLS:
  if layout=='A' or w[0] in ['LH4','LS','RH4','RS']:a+=wall(*w)
 a+=target(260,650,1,'#e85852',state,'red')
 a+=target(1000,610,-1,'#3e8bd4',state,'blue')
 return a

class Camera:
 def __init__(self,w=1600,h=1100,center=(630,630,0),scale=.76,yaw=-math.pi/4,pitch=math.asin(1/math.sqrt(3)),offset=None):
  self.w,self.h,self.center,self.scale,self.yaw,self.pitch=w,h,center,scale,yaw,pitch
  self.offset=offset or [w/2,h*.565]
 def project(self,p):
  x,y,z=[p[i]-self.center[i] for i in range(3)];u=x*math.cos(self.yaw)-y*math.sin(self.yaw);v=x*math.sin(self.yaw)+y*math.cos(self.yaw)
  return[self.offset[0]+self.scale*u,self.offset[1]-self.scale*(v*math.sin(self.pitch)+z*math.cos(self.pitch)),v*math.cos(self.pitch)-z*math.sin(self.pitch)]

def render(name,objects,cam,anchors):
 prim=[]
 for p in objects:
  q=[cam.project(pt) for pt in p['points']];depth=sum(t[2] for t in q)/len(q)
  if 'sphere_overlay' in p:
   sc=p['sphere_overlay'];cd=cam.project(sc[:3])[2]
   if depth>cd:continue
   depth=cd-sc[3]-1
  if 'ball_hardware' in p:
   sc=p['ball_hardware'];depth=cam.project(sc[:3])[2]-sc[3]-2+depth*.00001
  prim.append((p,q,depth))
 prim.sort(key=lambda r:(r[0]['layer'],-r[2]))
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{cam.w}" height="{cam.h}" viewBox="0 0 {cam.w} {cam.h}">']
 svg.append('<title>CyberBrick handcrafted arena, millimetre geometry</title>')
 im=Image.new('RGB',(cam.w*2,cam.h*2),'#ffffff');d=ImageDraw.Draw(im)
 for p,q,_ in prim:
  pts=' '.join(f'{v[0]:.3f},{v[1]:.3f}' for v in q);xy=[(round(v[0]*2),round(v[1]*2)) for v in q]
  if p['kind']=='poly':
   svg.append(f'<polygon data-part="{html.escape(p["id"])}" points="{pts}" fill="{p["color"]}"'+(f' stroke="{p["stroke"]}" stroke-width="{p["width"]}" stroke-linejoin="round"' if p.get('stroke') else '')+'/>')
   d.polygon(xy,fill=p['color'])
   if p.get('stroke'):d.line(xy+[xy[0]],fill=p['stroke'],width=max(1,round(p['width']*2)),joint='curve')
  else:
   width=p['width']*cam.scale
   svg.append(f'<polyline data-part="{html.escape(p["id"])}" points="{pts}" fill="none" stroke="{p["color"]}" stroke-width="{width:.3f}" stroke-linecap="round" stroke-linejoin="round"/>')
   d.line(xy,fill=p['color'],width=max(1,round(width*2)),joint='curve')
 svg.append('</svg>');(ROOT/(name+'.svg')).write_text('\n'.join(svg),encoding='utf-8')
 im.resize((cam.w,cam.h),Image.Resampling.LANCZOS).save(ROOT/(name+'.png'))
 return dict(file_svg=name+'.svg',file_png=name+'.png',viewbox=[0,0,cam.w,cam.h],camera=vars(cam),anchors={k:dict(world_mm=v,pixel_xy=cam.project(v)[:2])for k,v in anchors.items()},primitive_count=len(objects),visible_primitive_count=len(prim))

def main():
 global FIGMA_LOW_DETAIL
 manifest=dict(version='v08-handcraft-3d',units='mm',coordinate_system='Left-bottom origin; +X right; +Y up; floor top Z=0, floor underside Z=-5',physical_tested=False,dimensions=dict(arena=[1260,1260],floor=[420,630,5],floor_quantity=6,wall_foot_width=40,wall_panel_thickness=5,rail_section=[20,30],ball_diameter=70,H_example=135,t_example=8,U_example=178,post_example=173,arm=[20,200,20],base=[160,120,5],released_ball_center_z=55,released_ball_rearward_shift=40),notes=['135/173 mm are reference examples and require actual robot measurement.','Hardware brackets and layered t=8 stack are indicative; cord tying point and spare travel must be measured.','3D is dimensional assembly illustration, not a dynamics or reachability simulation.','All floors are fully supported, in one horizontal plane.','Thin arrows, outlines and color accents are printed graphics only.'],views={})
 anchors={'origin':[0,0,0],'x_end':[1260,0,0],'y_end':[0,1260,0],'floor_f1':[210,315,0],'floor_f2':[630,315,0],'floor_f3':[1050,315,0],'floor_f4':[210,945,0],'floor_f5':[630,945,0],'floor_f6':[1050,945,0],'red_spawn':[260,180,0],'blue_spawn':[1000,1080,0],'red_ball':[260,650,135],'blue_ball':[1000,610,135],'red_post_top':[260,800,178],'blue_post_top':[1000,460,178],'low_wall':[110,360,60],'high_wall':[470,360,100],'middle_wall':[650,360,80],'branch_wall':[520,440,80],'gate_left':[20,440,0],'gate_right':[500,440,0],'rail_top':[840,10,30]}
 for layout in 'AB':
  for state in ['ready','released']:
   name=f'arena_{layout}_{state}'
   state_anchors=dict(anchors)
   if state=='released':state_anchors.update(red_ball=[260,690,55],blue_ball=[1000,570,55])
   manifest['views'][name]=render(name,arena(layout,state),Camera(),state_anchors)
 for state in ['ready','released']:
  cam=Camera(w=1000,h=900,center=(0,80,85),scale=2.8,yaw=-math.pi/3,pitch=.58,offset=[470,470])
  anchors2={'ball_center':[0,0 if state=='ready' else 40,135 if state=='ready' else 55],'ball_bottom':[0,0 if state=='ready' else 40,100 if state=='ready' else 20],'arm_front':[0,-20,188],'magnet':[0,0,176],'guide':[0,40,198],'post_top':[0,150,178],'post_bottom':[0,150,5],'base_corner':[-80,90,0],'base_opposite':[80,210,0]}
  manifest['views']['target_'+state]=render('target_'+state,target(0,0,1,'#e85852',state),cam,anchors2)
 cam=Camera(w=1000,h=650,center=(90,20,45),scale=3.4,yaw=-.5,pitch=.6,offset=[500,340])
 manifest['views']['wall_180_H80']=render('wall_180_H80',wall('W80',0,0,180,80),cam,{'panel_front_left':[0,17.5,5],'panel_top_left':[0,17.5,80],'panel_top_right':[180,17.5,80],'foot_origin':[0,0,0],'foot_far':[180,40,0],'brace':[20,2.5,5]})
 scene={f'{l}_{s}':arena(l,s)for l in 'AB' for s in ['ready','released']}
 (ROOT/'scene_data.json').write_text(json.dumps(scene,separators=(',',':')),encoding='utf-8')
 make_viewer(scene)
 FIGMA_LOW_DETAIL=True
 for layout in 'AB':
  key=f'arena_{layout}_ready';result=render(key+'_figma',arena(layout,'ready'),Camera(),anchors)
  assert result['visible_primitive_count']<=800,result['visible_primitive_count']
  manifest['views'][key]['figma_simplified']=result
 (ROOT/'geometry_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v['primitive_count'] for k,v in manifest['views'].items()}))

def make_viewer(scene):
 template=(ROOT/'viewer_template.html').read_text(encoding='utf-8')
 (ROOT/'viewer.html').write_text(template.replace('__SCENE_JSON__',json.dumps(scene,separators=(',',':'))),encoding='utf-8')

if __name__=='__main__':main()
