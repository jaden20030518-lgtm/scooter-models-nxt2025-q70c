"""Reference-calibrated NXT 2025 exterior; metres, +X front, +Y left.
Side pixel coordinates are explicitly retained so outline edits stay traceable.
"""
import bpy, math, json, sys, bmesh
from pathlib import Path
from mathutils import Vector, Matrix

OUT=Path(__file__).resolve().parent
S=1.790/1782
U0=(434+1673)/2
GROUND=1820
def px(p): return Vector(((U0-p[0])*S,(GROUND-p[1])*S))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
veh=bpy.data.collections.new('NIU_NXT_ULTRA_2025');scene.collection.children.link(veh)
root=bpy.data.objects.new('NIU_ROOT',None);veh.objects.link(root)
root['year']=2025;root['wheelbase_m']=(1673-434)*S
root['wheelbase_basis']='Inferred from official 2025 orthographic reference, not a published measurement'
root['reference_scale_m_per_pixel']=S

def mat(n,c,rough=.35,metal=0,emit=0):
    m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*c,1)
    b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if emit:b.inputs['Emission Color'].default_value=(*c,1);b.inputs['Emission Strength'].default_value=emit
    return m
paint=mat('Black graphite molded paint',(.018,.021,.025),.29,.22)
inner=mat('Inner textured moulding',(.027,.03,.034),.5)
rubber=mat('Black tyre and footmat',(.012,.014,.017),.65)
floor_mat=mat('Low gloss TPE footwell',(.019,.022,.026),.9)
next(n for n in floor_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Specular IOR Level'].default_value=.12
seatmat=mat('Charcoal seat upholstery',(.026,.028,.032),.72)
metal=mat('Satin black metal',(.019,.021,.025),.34,.55)
silver=mat('Machined aluminium',(.3,.33,.37),.27,.85)
smoke=mat('Smoked optical face',(.022,.032,.04),.15,.15)
red=mat('Red painted accents',(.52,.008,.012),.35)
white=mat('DRL white',(.84,.91,1),.2,0,2)
amber=mat('Amber reflector',(.9,.22,.006),.28)
tail=mat('Rear red lens',(.6,.006,.005),.23,0,1)
clay=mat('Neutral geometry inspection',(.46,.48,.51),.62)

def mesh(n,vs,fs,m,smooth=True):
    me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(n,me);veh.objects.link(o);o.parent=root;me.materials.append(m)
    for p in me.polygons:p.use_smooth=smooth
    return o
def finish(o,n,m):
    o.name=n
    for c in list(o.users_collection):c.objects.unlink(o)
    veh.objects.link(o);o.parent=root;o.data.materials.append(m)
    if hasattr(o.data,'polygons'):
        for p in o.data.polygons:p.use_smooth=True
    return o
def box(n,loc,dims,m,r=.004,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,n,m)
    be=o.modifiers.new('Molded edge radius','BEVEL');be.width=r;be.segments=5
    no=o.modifiers.new('Face normals','WEIGHTED_NORMAL');no.keep_sharp=True
    if rot:o.rotation_euler=rot
    return o
def cyl(n,loc,r,d,m,axis=(0,1,0),verts=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=finish(bpy.context.object,n,m);o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
    be=o.modifiers.new('Machined edge','BEVEL');be.width=.0015;be.segments=3
    return o
def line(n,pts,r,m,closed=False):
    cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,c in zip(sp.points,pts):p.co=(*c,1)
    sp.use_cyclic_u=closed
    o=bpy.data.objects.new(n,cu);veh.objects.link(o);o.parent=root;cu.materials.append(m);return o
def rod(n,a,b,r,m):
    a,b=Vector(a),Vector(b);return cyl(n,(a+b)/2,r,(b-a).length,m,b-a,32)
def sample(points,steps=5,closed=False):
    ps=[Vector(p) for p in points];out=[];N=len(ps)
    for i in range(N if closed else N-1):
        p0=ps[(i-1)%N] if closed else ps[max(0,i-1)]
        p1=ps[i];p2=ps[(i+1)%N];p3=ps[(i+2)%N] if closed else ps[min(N-1,i+2)]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    if not closed:out.append(ps[-1])
    return out
def signpow(v,p):return math.copysign(abs(v)**p,v)

# Continuous U-shaped moulding. At each station both exterior and interior
# side boundaries are digitised, with a rounded-rectangle transverse section.
stations=[
    (718,879,831,898,.168),(661,934,813,952,.183),
    (586,1020,779,1035,.201),(500,1123,749,1123,.22),
    (444,1194,741,1200,.234),(439,1248,751,1260,.237),
    (486,1287,771,1360,.232),(557,1455,792,1452,.23),
    (647,1594,818,1501,.225),(735,1647,888,1495,.225),
    (1000,1640,1060,1488,.225),(1250,1631,1260,1480,.217),
    (1355,1620,1340,1475,.19),(1455,1536,1412,1465,.16),
]
curves=sample([(*px((a,b)),*px((c,d)),w) for a,b,c,d,w in stations],6)
vs=[];N=48
for ox,oz,ix,iz,w in curves:
    center=Vector(((ox+ix)/2,(oz+iz)/2));depth=Vector(((ox-ix)/2,(oz-iz)/2))
    for j in range(N):
        # Flat front crown, crisp shoulder and tapered return: cross-section
        # from black dealer 025s, preserving the calibrated XZ silhouette.
        a=2*math.pi*j/N
        d=signpow(math.cos(a),.38)
        y=signpow(math.sin(a),.22)*w*(.83+.17*(d+1)/2)
        p=center+depth*d;vs.append((p.x,y,p.y))
fs=[]
for k in range(len(curves)-1):
    for j in range(N):fs.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
fs += [tuple(range(N-1,-1,-1)),tuple((len(curves)-1)*N+j for j in range(N))]
shell=mesh('Continuous apron and lower sill',vs,fs,paint)

# Separate inner liner follows the same inner boundary, slightly above it.
liner=[];lf=[];cross=17
for ox,oz,ix,iz,w in curves:
    for j in range(cross):
        u=-1+2*j/(cross-1)
        liner.append((ix+.004, u*w*.91, iz+.004+.003*(1-u*u)))
for k in range(len(curves)-1):
    for j in range(cross-1):lf.append((k*cross+j,k*cross+j+1,(k+1)*cross+j+1,(k+1)*cross+j))
liner_ob=mesh('Continuous textured inner legshield',liner,lf,inner)
liner_ob.data.materials.append(floor_mat)
for poly in liner_ob.data.polygons:
    if poly.index//(cross-1)>=7*6:poly.material_index=1

# Battery pedestal: four-sided rounded cross sections in XY, with independently
# controlled top/bottom and front waist. Overlay covers are crowned quad patches.
zrows=[(.235,-.285,.175,.16),(.30,-.28,.19,.171),(.38,-.285,.19,.176),(.47,-.275,.185,.176),(.56,-.28,.185,.176),(.62,-.305,.17,.175),(.655,-.335,.145,.174)]
def vertical_body(n,rows,m):
    rows=sample(rows,5);vv=[];ff=[];N=48
    for z,x,hx,hy in rows:
        for j in range(N):
            a=2*math.pi*j/N;vv.append((x+signpow(math.cos(a),.4)*hx,signpow(math.sin(a),.4)*hy,z))
    for k in range(len(rows)-1):
        for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    ff.extend([tuple(range(N-1,-1,-1)),tuple((len(rows)-1)*N+j for j in range(N))])
    return mesh(n,vv,ff,m)
vertical_body('Shaped battery pedestal',zrows,inner)

cover_px=[(1318,1164),(1498,1145),(1514,1152),(1531,1350),(1527,1435),(1504,1484),(1270,1502),(1220,1480),(1200,1447),(1216,1365),(1267,1225)]
cover=sample([px(p) for p in cover_px],6,True)
def domed_patch(n,outline,side,m,yfactor=1):
    center=sum(outline,Vector((0,0)))/len(outline);vv=[];ff=[];N=len(outline)
    # Tight rolled perimeter and a broad mildly crowned central surface.
    rings=[(1,.180),(.987,.200),(.955,.222),(.87,.237),(.65,.242),(.35,.246),(.08,.247)]
    for r,y in rings:
        for p in outline:
            q=center+(p-center)*r;vv.append((q.x,side*y*yfactor,q.y))
    for k in range(len(rings)-1):
        for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    vv.append((center.x,side*.247*yfactor,center.y));c=len(vv)-1
    for j in range(N):ff.append(((len(rings)-1)*N+j,(len(rings)-1)*N+(j+1)%N,c))
    return mesh(n,vv,ff,m)
for side in [-1,1]:
    domed_patch(('Left' if side>0 else 'Right')+' moulded trapezoid cover',cover,side,paint)
    stripe=[px(p) for p in [(1509,1221),(1518,1293),(1523,1380)]]
    line('Flush red rear seam',[(p.x,side*.222,p.y) for p in stripe],.0045,red)

# Saddle cross sections: digitised upper and lower edge, width comes from 3/4.
seat_st=[(1132,1218,1233,.139),(1149,1189,1234,.164),(1185,1119,1230,.202),
         (1210,1090,1212,.205),(1260,1088,1180,.212),(1335,1090,1161,.218),
         (1455,1078,1154,.202),(1491,1073,1149,.196),(1520,1100,1145,.193),(1535,1130,1141,.165)]
rows=sample([((U0-u)*S,(GROUND-top)*S,(GROUND-bot)*S,w) for u,top,bot,w in seat_st],5)
vv=[];ff=[];N=48
for x,zt,zb,w in rows:
    for j in range(N):
        a=2*math.pi*j/N
        # A 4.5mm central crown is inferred from the oblique upholstery view.
        vv.append((x,signpow(math.sin(a),.42)*w,(zt+zb)/2+signpow(math.cos(a),.55)*(zt-zb)/2+.0045*max(0,math.cos(a))**2))
for k in range(len(rows)-1):
    for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
ff.extend([tuple(range(N-1,-1,-1)),tuple((len(rows)-1)*N+j for j in range(N))])
mesh('Reference shaped saddle',vv,ff,seatmat)

# Tyres use an explicit bead/sidewall/crown section, not round torus tubes.
WB=(1673-434)*S
def wheel(label,x,z,r):
    profile=[(-.025,.15),(-.047,.163),(-.052,.189),(-.044,.211),(-.028,r-.001),(0,r),(.028,r-.001),(.044,.211),(.052,.189),(.047,.163),(.025,.15)]
    vs=[];fs=[];N=144;P=len(profile)
    for a in range(N):
        t=2*math.pi*a/N
        for y,rad in profile:vs.append((x+rad*math.cos(t),y,z+rad*math.sin(t)))
    for a in range(N):
        for j in range(P-1):fs.append((a*P+j,((a+1)%N)*P+j,((a+1)%N)*P+j+1,a*P+j+1))
    mesh(label+' profiled road tyre',vs,fs,rubber)
    for y in [-.036,.036]:
        for radius in [.151,.144]:
            line(label+' rim lip',[(x+radius*math.cos(t*2*math.pi/128),y,z+radius*math.sin(t*2*math.pi/128)) for t in range(128)],.006,metal,True)
    cyl(label+' axle',(x,0,z),.036,.19,metal)
    for side in [-1,1]:
        for j in range(5):
            a=j*2*math.pi/5
            for delta in [-.075,.075]:
                rod(label+' split cast spoke',(x+.041*math.cos(a),side*.032,z+.041*math.sin(a)),(x+.142*math.cos(a+delta),side*.038,z+.142*math.sin(a+delta)),.0065,metal)
    for j in range(56):
        a=j*2*math.pi/56
        pts=[]
        for y in [-.038,-.02,0,.02,.038]:
            t=a+abs(y)*2.6;rad=r-.003-abs(y)*.09
            pts.append((x+rad*math.cos(t),y,z+rad*math.sin(t)))
        line(label+' tread groove',pts,.0011,inner)
def disc(n,x,z,r,side):
    N=120;vv=[];ff=[]
    for rad in [.045,r]:
        for j in range(N):a=j*2*math.pi/N;vv.append((x+rad*math.cos(a),side*.067,z+rad*math.sin(a)))
    for j in range(N):ff.append((j,(j+1)%N,(j+1)%N+N,j+N))
    ob=mesh(n,vv,ff,silver);sol=ob.modifiers.new('Rotor thickness','SOLIDIFY');sol.thickness=.004
    for i in range(28):
        a=2*math.pi*i/28
        cyl(n+' perforation',(x+r*.82*math.cos(a),side*.070,z+r*.82*math.sin(a)),.003,.005,rubber,verts=12)
zf=(GROUND-1600)*S;zr=(GROUND-1601)*S
wheel('Front',WB/2,zf,220*S);wheel('Rear',-WB/2,zr,218*S)
disc('Front 220 mm disc',WB/2,zf,.11,1);disc('Rear 190 mm disc',-WB/2,zr,.095,1)
cyl('Rear hub motor',(-WB/2,0,zr),.126,.10,metal)

# Actual fork travel path and hardware, independent of shell alignment.
for side in [-1,1]:
    rod('Front chrome sliding stanchion',(.47,side*.091,.55),(.56,side*.091,.35),.016,silver)
    rod('Front lower fork',(.56,side*.091,.35),(WB/2,side*.091,zf),.025,metal)
    box('Fork side reflector',(.535,side*.12,.38),(.027,.008,.076),amber,.008,rot=(0,.35,0))
box('Front caliper',(.525,.101,.26),(.063,.038,.067),metal,.018)

def fender(n,cx,cz,r,width,a0,a1,m):
    vs=[];fs=[];A=64;B=17
    for i in range(A+1):
        a=math.radians(a0+(a1-a0)*i/A)
        for j in range(B):
            u=-1+2*j/(B-1);rad=r+.025*math.sqrt(max(0,1-u*u))
            vs.append((cx+rad*math.cos(a),u*width/2,cz+rad*math.sin(a)))
    for i in range(A):
        for j in range(B-1):fs.append((i*B+j,i*B+j+1,(i+1)*B+j+1,(i+1)*B+j))
    o=mesh(n,vs,fs,m);so=o.modifiers.new('3mm shell','SOLIDIFY');so.thickness=.003
fender('Close fitting front fender',WB/2,zf,.222,.17,49,149,paint)
fender('Rear swept fender',-WB/2,zr,.237,.19,32,173,inner)

# Rack height, length and support anchors digitised from the side view.
def p3(u,v,y):
    p=px((u,v));return (p.x,y,p.y)
for side in [-1,1]:
    y=side*.174
    line('Rack perimeter side',[p3(1525,1168,y),p3(1620,1151,y),p3(1780,1140,y)],.0105,metal)
    line('Triangular rack support',[p3(1530,1278,y),p3(1694,1247,y),p3(1725,1160,y)],.011,metal)
for u in [1570,1640,1710,1775]:rod('Rack crossmember',p3(u,1150,-.178),p3(u,1150,.178),.008,metal)
for side in [-1,1]:
    line('Upper cargo platform rail',[p3(1540,1149,side*.163),p3(1655,1132,side*.163),p3(1780,1128,side*.163)],.0085,metal)
for u in [1558,1610,1662,1714,1766]:rod('Cargo platform top slat',p3(u,1140,-.164),p3(u,1140,.164),.0055,metal)
for side in [-1,1]:
    a=Vector(p3(1601,1510,side*.17));b=Vector(p3(1520,1300,side*.17));axis=(b-a).normalized()
    rod('Rear damper',a,b,.024,metal);u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u)
    pts=[]
    for i in range(241):
        t=i/240;p=a+(b-a)*t+.034*(u*math.cos(t*20*math.pi)+v*math.sin(t*20*math.pi));pts.append(p)
    line('Rear continuous spring',pts,.0045,metal)
    cyl('Shock collar',a+(b-a)*.15,.032,.03,red,axis)
rod('Rear swingarm',(-.22,.092,.26),(-WB/2,.092,zr),.035,metal)
arm_outline=sample([px(p) for p in [(1380,1585),(1410,1530),(1493,1504),(1810,1587),(1801,1624),(1670,1642)]],5,True)
domed_patch('Contoured rear swingarm cover',arm_outline,1,inner,.59)
box('Taillight casing',p3(1784,1190,0),(.054,.23,.068),metal,.009)
box('Taillight red lens',p3(1810,1190,0),(.014,.207,.044),tail,.009)
box('Rear number plate carrier',p3(1930,1536,0),(.029,.17,.19),metal,.006,rot=(0,-.45,0))

# Handlebar cockpit: no oversized rectangular instrument block.
rod('Steering neck',(.275,0,.92),(.26,0,1.00),.033,metal)
barpts=[(.255,-.315,1.012),(.24,-.21,1.021),(.258,-.12,.999),(.26,0,.995),(.258,.12,.999),(.24,.21,1.021),(.255,.315,1.012)]
line('Swept handlebar',sample(barpts,6),.011,metal)
box('Compact steering centre',(.26,0,.995),(.095,.195,.084),inner,.027,rot=(0,-.12,0))
for side in [-1,1]:
    cyl('Grip rubber',(.255,side*.315,1.012),.020,.115,rubber)
    box('Switchgear',(.244,side*.235,1.023),(.073,.064,.058),inner,.012)
    line('Brake lever',[(.29,side*.225,1.015),(.316,side*.29,1.007),(.324,side*.374,1.0)],.0045,metal)
box('5 inch TFT display',(.235,0,1.069),(.080,.133,.016),smoke,.008,rot=(0,-.22,0))

# Optical panel is carried by a frame defined by its side-view endpoints.
top=px((724,880));bottom=px((434,1197));up=(Vector((top.x,0,top.y))-Vector((bottom.x,0,bottom.y))).normalized()
right=Vector((0,1,0));normal=right.cross(up).normalized();basis=Matrix((right,up,normal)).transposed().to_quaternion()
center=(Vector((top.x,0,top.y))+Vector((bottom.x,0,bottom.y)))/2
def rounded_plate(n,center,w,h,r,d,m,orientation):
    outline=[]
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(13):
            a=math.radians(start+j*90/12);outline.append(Vector((x+r*math.cos(a),y+r*math.sin(a),0)))
    vv=[center+orientation@Vector((p.x,p.y,z)) for z in [-d/2,d/2] for p in outline];N=len(outline)
    ff=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]
    for j in range(N):ff.append((j,(j+1)%N,(j+1)%N+N,j+N))
    return mesh(n,vv,ff,m,False)
pl=rounded_plate('Flush rounded smoked front lens',center+normal*.008,.325,(top-bottom).length,.024,.006,smoke,basis)
lamp=center-up*.089+normal*.018
for rr,th,m in [(.083,.006,white),(.072,.002,silver)]:
    line('Circular front DRL', [lamp+right*(rr*math.cos(j*2*math.pi/128))+up*(rr*math.sin(j*2*math.pi/128)) for j in range(128)],th,m,True)
cyl('Projector dark cavity',lamp,.065,.012,smoke,normal)
ob=box('Headlight rectangular optic',lamp+normal*.009,(.070,.031,.008),silver,.006)
ob.rotation_mode='QUATERNION';ob.rotation_quaternion=basis
for side in [-1,1]:
    for i in range(5):
        a=px((482,1205+i*15));b=px((497,1195+i*15))
        line('Five flush red apron gills',[(a.x,side*.231,a.y),(b.x,side*.231,b.y)],.0027,red)

# Footwell top is a shallow rubber surface over the traced upper floor edge.
for i in range(10):
    u=835+i*29;p=px((u,1496-(u-835)*.03))
    line('Floor moulded rib',[(p.x,-.193,p.y+.006),(p.x,.193,p.y+.006)],.0018,rubber)
for side in [-1,1]:
    rod('Pedal spindle',(-.18,0,.237),(-.18,side*.25,.237),.010,metal)
    box('Bicycle pedal',(-.18,side*.249,.237),(.086,.051,.016),rubber,.004)

exec(compile((OUT/'production_details.py').read_text(), str(OUT/'production_details.py'), 'exec'), globals())
exec(compile((OUT/'refine_assemblies.py').read_text(), str(OUT/'refine_assemblies.py'), 'exec'), globals())

# Editable model saved before any studio/render setup.
scene['reference_pixel_mapping']=json.dumps({'scale':S,'origin_u':U0,'ground_v':GROUND,'wheelbase_estimate':WB})
scene.render.threads_mode='FIXED';scene.render.threads=3
scene['refinement_revision']='2026-09-13 real-video refinement 01'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'NIU_NXT_2025_Refined.blend'))
print('REFINED_MODEL_SAVED',len(veh.all_objects),'objects; WB',WB)
