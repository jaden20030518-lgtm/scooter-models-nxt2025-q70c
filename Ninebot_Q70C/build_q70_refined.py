import bpy, math, os, json
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob,do_unlink=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.length_unit='METERS'
scene.render.engine='BLENDER_EEVEE'; scene.render.threads_mode='FIXED'; scene.render.threads=3
scene.render.resolution_x=1200; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
vehicle=bpy.data.collections.new('NINEBOT_Q70C'); scene.collection.children.link(vehicle)
studio=bpy.data.collections.new('STUDIO'); scene.collection.children.link(studio)
root=bpy.data.objects.new('Q70C_ROOT',None); vehicle.objects.link(root)
root['wheelbase_m']=1.110; root['rider_seat_height_m']=.730
root['geometry_basis']='Official side traced landmarks and official lemon-yellow 3/4; transverse sections estimated'
def material(name, color, metallic=0.0, rough=.36, emission=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1)
    m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); out=nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=rough
    if emission:
        bs.inputs['Emission Color'].default_value=(*emission,1); bs.inputs['Emission Strength'].default_value=4
    return m

IVORY=material("Q70C Ivory Gloss",(0.92,.885,.77),0,.22)
YELLOW=material("Q70C Lemon Yellow",(.95,.64,.001),0,.23)
YELLOW_DARK=material("Q70C Floor Grip Yellow",(.60,.40,.001),0,.38)
BROWN=material("Taupe Brown Saddle",(.30,.18,.12),0,.56)
SEAM=material("Saddle Stitch",(.61,.42,.28),0,.7)
BLACK=material("Satin Black",(.018,.022,.025),.15,.28)
RUBBER=material("Tire Rubber",(.012,.014,.015),0,.72)
DARK=material("Dark Metallic",(.055,.065,.07),.7,.24)
SILVER=material("Machined Silver",(.48,.52,.54),.8,.2)
SEAM_GRAY=material("Panel Seam Gray",(.28,.29,.27),.05,.5)
GREEN=material("Switch Green",(.16,1.0,.025),0,.25, (.08,.8,.01))
AMBER=material("Amber Reflector",(1.0,.25,.015),0,.22, (1,.08,0))
RED=material("Tail Red",(.65,.012,.008),0,.2, (1,.01,0))
WHITE=material("Headlamp Ring",(.94,1.0,.92),0,.15, (1,1,.88))
GLASS=material("Smoked Lens",(.025,.035,.04),.25,.08)

def finish(ob, mat=None, bevel=0.0, smooth=True, parent=True):
    # move generated object into the vehicle collection
    for col in list(ob.users_collection): col.objects.unlink(ob)
    vehicle.objects.link(ob)
    if mat: ob.data.materials.append(mat)
    if smooth and hasattr(ob.data,'polygons'):
        for p in ob.data.polygons: p.use_smooth=True
    if bevel:
        mod=ob.modifiers.new("Soft molded edges",'BEVEL'); mod.width=bevel; mod.segments=3
    if parent: ob.parent=root
    return ob

def cube(name, loc, scale, mat, bevel=.02):
    bpy.ops.mesh.primitive_cube_add(location=loc); ob=bpy.context.object; ob.name=name; ob.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(ob,mat,bevel)

def uv(name, loc, scale, mat, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=24, location=loc)
    ob=bpy.context.object; ob.name=name; ob.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(ob,mat)

def cyl(name, loc, radius, depth, mat, rot=(0,0,0), verts=48, bevel=.004):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    ob=bpy.context.object; ob.name=name
    return finish(ob,mat,bevel)

def torus(name, loc, major, minor, mat, rot=(math.pi/2,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=64, minor_segments=12, location=loc, rotation=rot)
    ob=bpy.context.object; ob.name=name; return finish(ob,mat)

def tube(name, pts, radius, mat, bevel_res=3):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=radius; cu.bevel_resolution=bevel_res; cu.resolution_u=16; cu.use_fill_caps=True
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for bp,co in zip(sp.bezier_points,pts): bp.co=co; bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,cu); vehicle.objects.link(ob); cu.materials.append(mat); ob.parent=root; return ob

def text_obj(name, body, loc, rot, size, mat, extrude=.001):
    cu=bpy.data.curves.new(name+"Curve",'FONT'); cu.body=body; cu.align_x='CENTER'; cu.align_y='CENTER'
    cu.size=size; cu.extrude=extrude; cu.bevel_depth=.0004; cu.bevel_resolution=2; cu.materials.append(mat)
    ob=bpy.data.objects.new(name,cu); vehicle.objects.link(ob); ob.location=loc; ob.rotation_euler=rot; ob.parent=root
    return ob

# New surface geometry. Main body meshes use sectional quads and subdivision.
def mesh(name,vs,fs,mat,sub=0,solid=0):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(vs,[],fs); me.update()
    ob=bpy.data.objects.new(name,me); vehicle.objects.link(ob); ob.parent=root; me.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    if sub:
        m=ob.modifiers.new('Curvature from control sections','SUBSURF');m.levels=sub;m.render_levels=sub
    if solid:
        m=ob.modifiers.new('Molded wall','SOLIDIFY');m.thickness=solid
    return ob

def section_body(name,stations,mat,n=40,power=2.7,sub=2):
    # x, halfwidth, lower z, upper z. Every station is an actual rounded section.
    vs=[]
    for x,w,lo,hi in stations:
        for j in range(n):
            a=2*math.pi*j/n;s=math.sin(a);c=math.cos(a)
            y=w*math.copysign(abs(s)**(2/power),s)
            z=(lo+hi)/2+(hi-lo)/2*math.copysign(abs(c)**(2/power),c)
            vs.append((x,y,z))
    fs=[]
    for i in range(len(stations)-1):
        for j in range(n):fs.append((i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n))
    # Small end rings converge to poles; avoid a broad extruded end ngon.
    for i in [0,len(stations)-1]:
        x,w,lo,hi=stations[i];idx=len(vs);vs.append((x,0,(lo+hi)/2))
        for j in range(n):fs.append((idx,i*n+j,i*n+(j+1)%n) if i==0 else (idx,i*n+(j+1)%n,i*n+j))
    return mesh(name,vs,fs,mat,sub)

body=section_body('ContinuousDeepYellowTub',[
(-.775,.025,.335,.40),(-.757,.095,.31,.47),(-.725,.163,.292,.51),(-.68,.195,.266,.603),
(-.60,.204,.225,.673),(-.49,.216,.141,.661),(-.38,.226,.119,.638),(-.28,.231,.114,.612),
(-.20,.223,.115,.586),(-.162,.217,.116,.562),(-.137,.21,.117,.495),(-.127,.21,.117,.353),
(-.103,.22,.117,.296),(-.06,.228,.118,.283),(.08,.23,.12,.279),(.17,.231,.126,.287),
(.22,.228,.14,.312),(.265,.209,.166,.346),(.29,.16,.19,.348),(.30,.04,.232,.30)],YELLOW)
# Shallow top deck remains a real rounded transverse section.
section_body('YellowFloorboard', [(-.16,.04,.265,.283),(-.13,.202,.266,.294),(-.06,.22,.263,.295),(.15,.22,.266,.295),(.22,.19,.276,.305),(.245,.04,.287,.303)],YELLOW,power=5,sub=2)
for xx in [-.10,-.055,-.01,.035,.08,.125,.17]:
    tube('FloorGripRib',[(xx,-.175,.295),(xx,0,.298),(xx,.175,.295)],.002,YELLOW_DARK,2)

def interp(z,table):
    if z<=table[0][0]:return table[0][1]
    for i,((a,b),(c,d)) in enumerate(zip(table,table[1:])):
        if z<=c:
            prev=table[max(0,i-1)];nxt=table[min(len(table)-1,i+2)]
            m0=(d-prev[1])/(c-prev[0]);m1=(nxt[1]-b)/(nxt[0]-a)
            t=(z-a)/(c-a)
            return (2*t**3-3*t*t+1)*b+(t**3-2*t*t+t)*(c-a)*m0+(-2*t**3+3*t*t)*d+(t**3-t*t)*(c-a)*m1
    return table[-1][1]

# Apron is an open arched curved sheet, with its lower opening varying across Y.
# Center has smooth convex depth; side edges curl back into floor sill.
def apron(name,mat,offset=0,widen=0):
    nu=40;nv=32;vs=[]
    edge=[(.13,.137),(.23,.205),(.37,.28),(.53,.294),(.64,.235),(.76,.185),(.89,.18)]
    crown=[(.13,.45),(.34,.49),(.51,.531),(.61,.476),(.72,.393),(.83,.327),(.91,.264)]
    for j in range(nv+1):
        t=j/nv
        for i in range(nu+1):
            u=-1+2*i/nu
            bot=.14+.360*(max(0,1-(abs(u)/.89)**2)**1.30)
            top=.887-.045*u*u
            z=bot+(top-bot)*t
            w=interp(z,[(.13,.225),(.4,.24),(.57,.23),(.75,.215),(.9,.18)])+widen
            x=interp(z,edge)+(interp(z,crown)-interp(z,edge))*max(0,1-u*u)**.7+offset
            vs.append((x,u*w,z))
    fs=[]
    for j in range(nv):
        for i in range(nu):
            k=j*(nu+1)+i;fs.append((k,k+1,k+nu+2,k+nu+1))
    return mesh(name,vs,fs,mat,1,.012)
apron('YellowInnerLegshield',YELLOW,-.025,.006)
apron('IvoryConvexApron',IVORY)

# Convex pebble cover: 12 concentric rings follow the asymmetric traced boundary.
profile=[(-.773,.355),(-.749,.452),(-.68,.55),(-.573,.609),(-.443,.615),(-.348,.558),(-.302,.46),(-.328,.384),(-.402,.32),(-.564,.317),(-.704,.336)]
def catmull(points,steps=5):
    arr=[]
    for i in range(len(points)):
        p0=Vector(points[(i-1)%len(points)]);p1=Vector(points[i]);p2=Vector(points[(i+1)%len(points)]);p3=Vector(points[(i+2)%len(points)])
        for st in range(steps):
            t=st/steps
            arr.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    return arr
for sg in [-1,1]:
    stations=[(-.777,.346,.355,.002),(-.747,.333,.406,.019),(-.685,.324,.486,.036),(-.60,.317,.549,.05),(-.5,.313,.597,.06),(-.4,.316,.620,.065),(-.31,.333,.612,.066),(-.243,.367,.564,.057),(-.20,.416,.514,.035),(-.188,.453,.467,.002)]
    vs=[];fs=[];n=32
    for x,lo,hi,depth in stations:
        for j in range(n+1):
            t=math.pi*j/n
            vs.append((x,sg*(.207+depth*math.sin(t)),(lo+hi)/2+(hi-lo)/2*math.cos(t)))
    for i in range(len(stations)-1):
        for j in range(n):
            k=i*(n+1)+j;fs.append((k,k+1,k+n+2,k+n+1))
    mesh(('Left' if sg>0 else 'Right')+'IvoryConvexSideCover',vs,fs,IVORY,2,.007)
    tube('FootProtectionInsert',[(-.452,sg*.239,.294),(-.40,sg*.245,.292),(-.328,sg*.241,.294)],.020,BLACK)

# Saddle top has a measured .730 m rider contact, with slender downturned nose.
seat=section_body('TaupeSaddle',[
(-.711,.023,.693,.723),(-.70,.092,.682,.743),(-.678,.155,.67,.751),(-.626,.186,.655,.751),
(-.55,.193,.646,.742),(-.465,.19,.633,.735),(-.38,.181,.617,.733),(-.30,.164,.594,.734),
(-.23,.135,.566,.73),(-.188,.111,.551,.72),(-.164,.086,.550,.699),(-.154,.045,.561,.673),(-.152,.008,.587,.644)],BROWN,power=3.1,sub=2)
for v in seat.data.vertices:
    v.co.x+=.070
    if v.co.x>-.17:v.co.z-=.026*max(0,(-v.co.z+.72)/.18)
# Normalize evaluated contact at a deliberately defined rider patch to exactly 730 mm.
bpy.context.view_layer.update()
eval_ob=seat.evaluated_get(bpy.context.evaluated_depsgraph_get())
hit,loc,norm,idx=eval_ob.ray_cast(Vector((-.355,0,2)),Vector((0,0,-1)))
if not hit:raise RuntimeError('Seat contact ray missed')
seat.location.z=.730-loc.z
seat['contact_x_m']=-.355;seat['contact_z_m']=.730
for sg in [-1,1]:
    tube('SaddleSideSeam',[(-.694,sg*.11,.707),(-.65,sg*.17,.709),(-.61,sg*.183,.703),(-.55,sg*.19,.687)],.0008,SEAM,2)
tube('UShapedRearGrabRail',[(-.473,-.213,.66),(-.595,-.218,.70),(-.677,-.15,.739),(-.705,0,.754),(-.677,.15,.739),(-.595,.218,.70),(-.473,.213,.66)],.012,DARK)

# Running gear with unequal nominal front/rear diameters and explicit rim sizes.
def wheel(name,x,r,rim):
    minor=(r-rim)/2
    torus(name+'_Tire',(x,0,r),r-minor,minor,RUBBER)
    torus(name+'_Rim',(x,0,r),rim-.009,.009,DARK)
    cyl(name+'_Hub',(x,0,r),rim*.36,.102,DARK,(math.pi/2,0,0),48,.003)
    for sg in [-1,1]:
        torus(name+'_SidewallBead',(x,sg*(minor*.80),r),r-minor*.98,.0028,RUBBER)
        for k in range(8):
            a=2*math.pi*k/8
            tube(name+'_CastSpoke',[(x+math.cos(a)*rim*.31,sg*.044,r+math.sin(a)*rim*.31),(x+math.cos(a+.14)*rim*.91,sg*.044,r+math.sin(a+.14)*rim*.91)],.010,DARK,2)
    # Broken alternating tread grooves are represented by raised shallow rubber ridges.
    for k in range(36):
        a=2*math.pi*k/36
        for sg in [-1,1]:
            pts=[]
            for t in [0,.35,.7,1]:
                yy=sg*(.008+t*minor*.76);rr=r-.003-t*t*.012;aa=a+.06*t
                pts.append((x+math.sin(aa)*rr,yy,r+math.cos(aa)*rr))
            tube(name+'_Tread',pts,.0018,RUBBER,1)
wheel('FrontWheel',.555,.178,.1016)
wheel('RearWheel',-.555,.191,.127)

# Molded front fender has transverse crown and visibly broad flared side lips.
def fender(name,cx,cz,r,w,mat,a0,a1):
    vs=[];fs=[];ny=20;na=42
    for iy in range(ny+1):
        u=-1+2*iy/ny
        for ia in range(na+1):
            a=math.radians(a0+(a1-a0)*ia/na)
            rr=r+.065-.019*u*u
            vs.append((cx+math.cos(a)*rr,u*w/2,cz+math.sin(a)*rr-.05*u*u))
    for iy in range(ny):
        for ia in range(na):
            k=iy*(na+1)+ia;fs.append((k,k+1,k+na+2,k+na+1))
    return mesh(name,vs,fs,mat,1,.006)
# Asymmetric fender outline from near-side photograph, swept with transverse crown.
fender_outline=[(.329,.187),(.337,.245),(.345,.319),(.38,.378),(.429,.427),(.48,.45),(.532,.445),(.585,.418),(.639,.387),(.684,.36),(.711,.338)]
vs=[];fs=[];ny=40
for i,(x,z) in enumerate(fender_outline):
    for j in range(ny+1):
        u=-1+2*j/ny
        drop=interp(x,[(.318,.007),(.345,.045),(.38,.085),(.43,.106),(.50,.113),(.58,.095),(.65,.067),(.711,.051)])
        # Leading edge bows rearwards near its sides, with no wing tip.
        xx=x-(.027*u*u)*max(0,(i/(len(fender_outline)-1)-.65)/.35)
        yy=u*.124*(1-.14*max(0,(i/(len(fender_outline)-1)-.8)/.2))
        vs.append((xx,yy,z-drop*u*u))
for i in range(len(fender_outline)-1):
    for j in range(ny):
        k=i*(ny+1)+j;fs.append((k,k+1,k+ny+2,k+ny+1))
mesh('IvoryFrontFender',vs,fs,IVORY,2,.009)
fender('RearBlackMudguard',-.555,.191,.191,.16,BLACK,22,169)
for sg in [-1,1]:
    tube('Fork',[(.555,sg*.070,.178),(.425,sg*.070,.397),(.165,sg*.070,.755)],.016,DARK)
    cube('AmberReflector',(.49,sg*.12,.332),(.010,.006,.027),AMBER,.007).rotation_euler[1]=-.3
cyl('FrontBrakeDisc',(.555,-.060,.178),.089,.007,SILVER,(math.pi/2,0,0),64,.001)
for k in range(16):
    a=k*math.pi/8
    cyl('RotorHole',(.555+math.cos(a)*.073,-.065,.178+math.sin(a)*.073),.0045,.001,BLACK,(math.pi/2,0,0),12,0)
cyl('FrontBrakeHub',(.555,-.068,.178),.030,.01,BLACK,(math.pi/2,0,0))
cube('BrakeCaliper',(.49,-.078,.213),(.023,.016,.034),BLACK,.008)
section_body('RearSwingarm',[(-.681,.045,.169,.208),(-.65,.105,.136,.241),(-.53,.10,.134,.262),(-.34,.086,.185,.298),(-.29,.035,.228,.278)],DARK,power=3,sub=1)
cyl('RearMotor',(-.555,-.056,.191),.104,.022,DARK,(math.pi/2,0,0))
for sg in [-1,1]:
    tube('RearShock',[(-.61,sg*.083,.215),(-.50,sg*.084,.417)],.015,DARK)
    tube('PassengerFootrest',[(-.30,sg*.222,.192),(-.22,sg*.233,.192)],.015,DARK)
# Tail and black plate flap
cube('TailLamp',(-.761,0,.452),(.016,.077,.022),RED,.014)
cube('PlateCarrier',(-.766,0,.309),(.012,.095,.092),BLACK,.008).rotation_euler[1]=-.27

# Compact headlamp centered near +.28,.99; front face at +.35.
section_body('BlackLampPod',[(.185,.049,.949,1.039),(.192,.061,.937,1.051),(.225,.070,.926,1.062),(.273,.08,.912,1.076),(.302,.083,.911,1.077),(.317,.078,.917,1.071)],BLACK,power=2,sub=2)
torus('YellowHeadlampRim',(.317,0,.994),.075,.009,YELLOW,(0,math.pi/2,0))
cyl('Lens',(.326,0,.994),.066,.005,GLASS,(0,math.pi/2,0),64,.001)
torus('WhiteHeadlightRing',(.331,0,.994),.059,.005,WHITE,(0,math.pi/2,0))
cube('CentralOptic',(.337,0,.994),(.006,.025,.018),SILVER,.005)
cyl('RearDisplay',(.192,0,1.0),.069,.009,GLASS,(0,math.pi/2,0),64,.003)
for sg in [-1,1]:
    tube('Handlebar',[(.225,0,.923),(.20,sg*.14,.957),(.16,sg*.245,.977),(.128,sg*.31,.968)],.012,BLACK)
    cyl('Grip',(.128,sg*.315,.968),.019,.12,BLACK,(math.pi/2,0,0),40,.004)
    torus('GreenControlRing',(.138,sg*.254,.973),.022,.0035,GREEN)
    tube('BrakeLever',[(.177,sg*.245,.974),(.205,sg*.29,.956),(.205,sg*.365,.946)],.0045,BLACK)
    tube('MirrorStem',[(.167,sg*.242,.985),(.16,sg*.248,1.071),(.16,sg*.305,1.154)],.005,BLACK,2)
    uv('MirrorBack',(.16,sg*.313,1.173),(.019,.048,.064),BLACK)
    uv('MirrorGlass',(.144,sg*.313,1.173),(.003,.042,.057),DARK)
# Emblem and service seam laid on the convex front shell.
for sg in [-1,1]:
    tube('CenterStand',[(-.32,sg*.08,.195),(-.35,sg*.11,.05),(-.39,sg*.12,.039)],.009,BLACK)


# Front emblem/service oval follows evaluated convex apron, rather than floating decals.
bpy.context.view_layer.update()
ev=bpy.data.objects['IvoryConvexApron'].evaluated_get(bpy.context.evaluated_depsgraph_get())
pts=[]
for i in range(65):
    a=2*math.pi*i/64;y=.032*math.cos(a);z=.827+.05*math.sin(a)
    hit,p,n,ix=ev.ray_cast(Vector((2,y,z)),Vector((-1,0,0)))
    if hit:pts.append(p+n*.001)
if pts:tube('ApronServiceSeam',pts,.0007,SEAM_GRAY,2)
hit,p,n,ix=ev.ray_cast(Vector((2,0,.845)),Vector((-1,0,0)))
if hit:
    badge=cyl('NinebotFrontBadge',p+n*.003,.0155,.003,BLACK,(0,0,0),48,.001)
    badge.rotation_mode='QUATERNION';badge.rotation_quaternion=n.to_track_quat('Z','Y')
    core=cyl('BadgeInset',p+n*.005,.008,.003,SILVER,(0,0,0),40,.0007)
    core.rotation_mode='QUATERNION';core.rotation_quaternion=n.to_track_quat('Z','Y')

# --- Production surface, optical and mechanical pass ---
def remove_matching(prefixes):
    for ob in list(vehicle.objects):
        if any(ob.name.startswith(p) for p in prefixes):bpy.data.objects.remove(ob,do_unlink=True)
def bsdf(mat):return next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def noise_finish(mat,scale,distance,strength,rough_lo,rough_hi):
    nt=mat.node_tree;p=bsdf(mat)
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.68
    coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],tex.inputs['Vector'])
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=distance
    nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(rough_lo,rough_lo,rough_lo,1);ramp.color_ramp.elements[1].color=(rough_hi,rough_hi,rough_hi,1)
    nt.links.new(tex.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs['Color'],p.inputs['Roughness'])
for m in [IVORY,YELLOW]:
    bsdf(m).inputs['Coat Weight'].default_value=.25;bsdf(m).inputs['Coat Roughness'].default_value=.17
    noise_finish(m,1650,.000025,.14,.19,.245)
bsdf(YELLOW).inputs['Base Color'].default_value=(.84,.62,.0005,1)
bsdf(IVORY).inputs['Base Color'].default_value=(.84,.825,.76,1)
bsdf(BROWN).inputs['Base Color'].default_value=(.245,.172,.123,1)
noise_finish(BROWN,1500,.00016,.55,.49,.67)
noise_finish(RUBBER,1150,.000075,.34,.55,.79)
noise_finish(BLACK,950,.000025,.2,.24,.34)
noise_finish(DARK,1700,.000012,.18,.21,.32)
noise_finish(YELLOW_DARK,650,.00007,.3,.39,.52)
SILVER_FINE=material('Brushed stainless rotor',(.46,.49,.50),.95,.26)
noise_finish(SILVER_FINE,2800,.000008,.12,.22,.31)
LENS_CLEAR=material('Optical polycarbonate clear',(.975,.985,1),0,.055)
bsdf(LENS_CLEAR).inputs['Transmission Weight'].default_value=.98;bsdf(LENS_CLEAR).inputs['IOR'].default_value=1.49
CHROME=material('Reflector vacuum metallization',(.78,.81,.82),1,.075)
MIRROR=material('Convex mirror reflective silver',(.65,.7,.73),.96,.055)
for m in [AMBER,RED]:bsdf(m).inputs['Emission Strength'].default_value=.05
bsdf(WHITE).inputs['Emission Strength'].default_value=1.4
bsdf(GREEN).inputs['Emission Strength'].default_value=.6

# True carved radial tread channels: dense analytic quad surface rather than raised stripes.
remove_matching(['FrontWheel_Tire','RearWheel_Tire','FrontWheel_Tread','RearWheel_Tread','FrontWheel_SidewallBead','RearWheel_SidewallBead'])
def production_tire(name,x,r,rim,width):
    nm=384;np=72;minor=(r-rim)/2;R=r-minor;vs=[];fs=[]
    for i in range(nm):
        a=2*math.pi*i/nm
        for j in range(np):
            p=2*math.pi*j/np;yy=width/2*math.sin(p);outer=max(0,math.cos(p));yn=yy/(width/2)
            phase=(a/(2*math.pi)*28+.52*abs(yn))%1
            delta=min(phase,1-phase)
            groove=max(0,1-delta/.075)**.5*.0032*outer**.4
            # Alternating outer shoulder cuts join the chevron crown channels.
            shoulder=((a/(2*math.pi)*28-.3*abs(yn)+.45)%1)
            sidecut=max(0,1-min(shoulder,1-shoulder)/.055)*.0016*outer*abs(yn)
            rr=R+minor*math.cos(p)-groove-sidecut
            vs.append((x+math.cos(a)*rr,yy,r+math.sin(a)*rr))
    for i in range(nm):
        for j in range(np):fs.append((i*np+j,i*np+(j+1)%np,((i+1)%nm)*np+(j+1)%np,((i+1)%nm)*np+j))
    mesh(name+'_Tire',vs,fs,RUBBER)
    for sg in [-1,1]:
        for rad in [rim+.009,r-.026]:torus(name+'_MoldedSidewallRing',(x,sg*width*.44,r),rad,.0012,RUBBER)
        for k in range(12):
            a=k*math.pi/6
            uv(name+'_SidewallMolding',(x+math.cos(a)*(r-.029),sg*width*.484,r+math.sin(a)*(r-.029)),(.004,.0009,.002),RUBBER,16)
production_tire('FrontWheel',.555,.178,.1016,.078)
production_tire('RearWheel',-.555,.191,.127,.08)

# Cast wheel spokes with a real inner rim channel and rim flange on each face.
for name,x,r,rr in [('FrontWheel',.555,.178,.1016),('RearWheel',-.555,.191,.127)]:
    for sg in [-1,1]:
        torus(name+'_RimLip',(x,sg*.033,r),rr-.004,.0045,DARK)
        torus(name+'_RimBarrel',(x,sg*.019,r),rr-.009,.008,DARK)
        for k in range(8):
            a=k*math.pi/4
            bolt=cyl(name+'_HubScrew',(x+math.cos(a)*.027,sg*.058,r+math.sin(a)*.027),.0032,.0025,SILVER_FINE,(math.pi/2,0,0),6,.0004)
    tube(name+'_Valve',[(x+.051,.034,r+.068),(x+.055,.051,r+.071)],.0035,BLACK,2)

# Left (+Y) front disc, with real open holes and vent slots cut through the metal.
remove_matching(['FrontBrakeDisc','RotorHole','FrontBrakeHub','BrakeCaliper'])
rotor=cyl('FrontBrakeDisc',(.555,.058,.178),.089,.0038,SILVER_FINE,(math.pi/2,0,0),128,0)
cutters=[]
for k in range(24):
    a=k*math.pi/12;rad=.074 if k%2==0 else .079
    cutters.append(cyl('RotorCut',(.555+math.cos(a)*rad,.058,.178+math.sin(a)*rad),.0036,.015,None,(math.pi/2,0,0),16,0))
for k in range(6):
    a=k*math.pi/3
    cutters.append(cyl('RotorCut',(.555+math.cos(a)*.052,.058,.178+math.sin(a)*.052),.007,.015,None,(math.pi/2,0,0),24,0))
bpy.ops.object.select_all(action='DESELECT')
for ob in cutters:ob.select_set(True)
bpy.context.view_layer.objects.active=cutters[0];bpy.ops.object.join();cut=cutters[0]
mod=rotor.modifiers.new('Drilled through rotor','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
bpy.context.view_layer.objects.active=rotor;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bev=rotor.modifiers.new('Rotor machined edge','BEVEL');bev.width=.00045;bev.segments=2
cyl('FrontRotorHub',(.555,.061,.178),.028,.012,DARK,(math.pi/2,0,0),64,.002)
for k in range(6):
    a=k*math.pi/3;cyl('RotorMountBolt',(.555+math.cos(a)*.023,.070,.178+math.sin(a)*.023),.0033,.003,SILVER_FINE,(math.pi/2,0,0),6,.0005)
cal=cube('FrontHydraulicCaliper',(.487,.076,.221),(.023,.017,.035),BLACK,.006);cal.rotation_euler[1]=-.22
for z in [.204,.238]:cyl('CaliperPin',(.48,.095,z),.004,.003,SILVER_FINE,(math.pi/2,0,0),6,.0005)
tube('BraidedBrakeHose',[(.49,.083,.25),(.43,.087,.40),(.30,.105,.58),(.17,.13,.82),(.16,.21,.961)],.0036,BLACK,3)
# Brake hose clamps, axle hardware and reflecting amber insert inset in dark housing.
for sg in [-1,1]:
    cyl('FrontAxleNut',(.555,sg*.087,.178),.010,.009,DARK,(math.pi/2,0,0),6,.001)
    cube('ReflectorBlackMount',(.473,sg*.129,.32),(.012,.006,.03),BLACK,.006).rotation_euler[1]=-.3
    cube('AmberLensInsert',(.472,sg*.137,.32),(.008,.002,.023),AMBER,.005).rotation_euler[1]=-.3
remove_matching(['AmberReflector'])

# Nested optical bowl, lamp reflector and lens stack; no plain opaque disk substitute.
remove_matching(['Lens','CentralOptic','WhiteHeadlightRing'])
vs=[];fs=[];nr=12;na=96
for i in range(nr+1):
    rr=.012+(.063-.012)*i/nr;xx=.307+.018*(rr/.063)**1.65
    for j in range(na):a=2*math.pi*j/na;vs.append((xx,rr*math.cos(a),.994+rr*math.sin(a)))
for i in range(nr):
    for j in range(na):fs.append((i*na+j,i*na+(j+1)%na,(i+1)*na+(j+1)%na,(i+1)*na+j))
mesh('HeadlampChromeReflectorBowl',vs,fs,CHROME,1,.0007)
cyl('HeadlampDarkOpticalCore',(.323,0,.994),.019,.016,BLACK,(0,math.pi/2,0),64,.002)
cube('ProjectorChromeFrame',(.339,0,.994),(.009,.023,.016),CHROME,.004)
cube('ProjectorLens',(.348,0,.994),(.004,.018,.011),LENS_CLEAR,.004)
torus('WhiteHeadlightRing',(.33,0,.994),.058,.0037,WHITE,(0,math.pi/2,0))
torus('LampInternalDarkGasket',(.328,0,.994),.064,.0024,BLACK,(0,math.pi/2,0))
# A shallow spherical outer lens with finite edge thickness.
uv('HeadlampClearCover',(.335,0,.994),(.006,.067,.067),LENS_CLEAR,96)
for a in [0,math.pi/2,math.pi,math.pi*1.5]:
    cyl('LampMountRecess',(.313,.071*math.cos(a),.994+.071*math.sin(a)),.0023,.003,BLACK,(0,math.pi/2,0),24,.0005)

remove_matching(['Handlebar'])
for sg in [-1,1]:
    tube('Handlebar',[(.235,sg*.043,.891),(.222,sg*.13,.903),(.208,sg*.158,.96),(.171,sg*.214,.982),(.135,sg*.252,.972)],.0115,BLACK)
    tube('FrontSignalStem',[(.25,sg*.064,.925),(.268,sg*.12,.925)],.006,BLACK,2)
    cube('FrontSignalHousing',(.27,sg*.143,.925),(.012,.029,.01),BLACK,.009)
    cube('FrontSignalLens',(.282,sg*.143,.925),(.002,.024,.007),GLASS,.006)
    for j in range(4):uv('SignalLED',(.286,sg*(.126+j*.011),.925),(.0018,.003,.003),SILVER,16)

# Switchgear: cast housings, controls, grip ribs, levers, cable boots and mirror joints.
for sg in [-1,1]:
    switch=cube('SwitchgearHousing',(.145,sg*.245,.972),(.033,.025,.027),BLACK,.015)
    cube('SwitchgearUpperButton',(.132,sg*.244,.997),(.009,.012,.003),DARK,.003)
    cube('SignalRocker',(.113,sg*.246,.968),(.004,.013,.006),DARK,.002)
    for j in range(19):torus('GripRecessRib',(.128,sg*(.266+.0054*j),.968),.0194,.0008,RUBBER)
    cyl('GripBarEnd',(.128,sg*.377,.968),.019,.006,DARK,(math.pi/2,0,0),48,.0015)
    cyl('LeverPivotBolt',(.18,sg*.238,.975),.0055,.007,SILVER_FINE,(0,0,0),6,.0008)
    cube('BrakeLeverMasterBody',(.185,sg*.224,.973),(.023,.019,.019),BLACK,.006)
    tube('ControlCableBoot',[(.163,sg*.222,.954),(.149,sg*.206,.934),(.161,sg*.177,.913)],.006,BLACK,3)
    tube('ElectricalCable',[(.162,sg*.20,.936),(.207,sg*.16,.888),(.23,sg*.08,.895)],.0028,BLACK,3)
    cyl('MirrorStemLocknut',(.167,sg*.242,.996),.007,.007,DARK,(0,0,0),6,.001)
    ob=bpy.data.objects.get('MirrorGlass' if sg==-1 else 'MirrorGlass.001')
    if ob:ob.data.materials.clear();ob.data.materials.append(MIRROR)

# Exposed inboard green control rings, kept clear of switchgear housings.
remove_matching(['GreenControlRing'])
for sg in [-1,1]:
    torus('GreenControlRing',(.169,sg*.215,.981),.025,.0045,GREEN)
    cyl('ControlRingBacking',(.169,sg*.217,.981),.027,.009,BLACK,(math.pi/2,0,0),64,.002)

# Instrument has a circular cover, LCD digits and low-contrast perimeter marks.
remove_matching(['RearDisplay'])
cyl('InstrumentBezel',(.184,0,1.0),.072,.012,BLACK,(0,math.pi/2,0),96,.003)
cyl('InstrumentScreen',(.176,0,1.0),.065,.006,GLASS,(0,math.pi/2,0),96,.001)
def rear_text(name,body,loc,size,mat):
    ob=text_obj(name,body,loc,(0,0,0),size,mat,.00003)
    ob.rotation_euler=Vector((-1,0,0)).to_track_quat('Z','Y').to_euler();return ob
rear_text('SpeedDigits','00',(.171,0,1.011),.038,WHITE)
rear_text('SpeedUnits','km/h',(.170,0,.988),.008,SILVER)
rear_text('InstrumentReady','READY',(.170,0,.966),.006,GREEN)
for i in range(5):cube('BatterySegment',(.17,-.018+i*.009,.978),(.0008,.003,.0023),GREEN,.0006)

# Panel joints, front cubby rim, seat piping and fasteners are actual modeled details.
remove_matching(['SaddleSideSeam','SeatStitch','SeatUpholsteryPiping'])
bpy.context.view_layer.update()
se=seat.evaluated_get(bpy.context.evaluated_depsgraph_get())
for sg in [-1,1]:
    seam=[]
    for i in range(65):
        xx=-.678+.476*i/64;zz=interp(xx,[(-.678,.715),(-.60,.708),(-.45,.69),(-.30,.672),(-.202,.635)])
        hit,p,n,ix=se.ray_cast(Vector((xx,sg*2,zz-seat.location.z)),Vector((0,-sg,0)))
        if hit:seam.append(p+seat.location+n*.001)
    if len(seam)>2:tube('SeatUpholsteryPiping',seam,.0011,BROWN,2)
    for i in range(0,len(seam)-1,2):tube('SeatStitch', [seam[i],seam[i].lerp(seam[i+1],.6)],.0003,SEAM,1)
    # Tucked peripheral flange behind cream rear cover, deliberately dark narrow shadow gap.
    ob=bpy.data.objects['LeftIvoryConvexSideCover' if sg==1 else 'RightIvoryConvexSideCover']
    shell=ob.copy();shell.data=ob.data.copy();vehicle.objects.link(shell);shell.name='RearCoverTuckedLip';shell.location.y=-sg*.006
    shell.data.materials.clear();shell.data.materials.append(YELLOW)
    for x,z in [(-.714,.358),(-.317,.443)]:
        cyl('SidePanelFastener',(x,sg*.221,z),.003,.003,DARK,(math.pi/2,0,0),24,.0005)
    tube('LowerSillJoint',[(-.46,sg*.215,.151),(-.25,sg*.231,.146),(.055,sg*.232,.146),(.18,sg*.227,.16)],.001,SEAM_GRAY,2)
    # Small accurately placed ninebot wordmark on the low rear part of each white cover.
    text_obj('RearCoverWordmark','ninebot',(-.686,sg*.24,.375),(-math.pi/2,0,math.pi) if sg==1 else (math.pi/2,0,0),.018,BLACK,.00015)
    tube('PedestalLowerJoint',[(-.20,sg*.216,.325),(-.155,sg*.219,.318),(-.13,sg*.22,.299)],.001,SEAM_GRAY,2)
# Ignition hardware on the front face of the battery pedestal, visible under saddle nose.
cyl('IgnitionOuterRing',(-.139,.079,.491),.013,.008,DARK,(0,math.pi/2,0),64,.002)
cyl('IgnitionCenter',(-.132,.079,.491),.009,.004,BLACK,(0,math.pi/2,0),48,.001)
cube('KeySlot',(-.128,.079,.491),(.001,.004,.0008),SILVER,.0002)
cube('BagHook',(-.137,-.037,.497),(.007,.009,.018),BLACK,.005)
# Folded black / alloy rear passenger steps: support base, ribbed landing and hinge.
remove_matching(['PassengerFootrest'])
for sg in [-1,1]:
    cube('PassengerStepBase',(-.265,sg*.246,.192),(.074,.018,.016),BLACK,.007)
    tube('PassengerStepAlloyRail',[(-.331,sg*.265,.186),(-.309,sg*.271,.177),(-.211,sg*.271,.18),(-.20,sg*.26,.189)],.0045,SILVER_FINE,2)
    for k in range(6):cube('PassengerStepTread',(-.311+k*.019,sg*.266,.20),(.005,.016,.002),DARK,.001)

remove_matching(['FootProtectionInsert','RearCoverWordmark'])
bpy.context.view_layer.update()
for sg in [-1,1]:
    cube('RubberSideProtectionInsert',(-.326,sg*.243,.286),(.065,.009,.02),BLACK,.015)
    cover=bpy.data.objects['LeftIvoryConvexSideCover' if sg==1 else 'RightIvoryConvexSideCover'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    hit,p,n,idx=cover.ray_cast(Vector((-.685,sg*2,.365)),Vector((0,-sg,0)))
    if hit:
        mark=text_obj('RearCoverWordmark','ninebot',p+n*.001,(-math.pi/2,0,math.pi) if sg==1 else (math.pi/2,0,0),.018,BLACK,.00008)
# Root is the only vehicle transform; geometry remains in physical meters.
root['classification']='Reference-matched visualization reconstructed from public official imagery; not factory CAD'
root['clean_side_source']='K104E official support catalog 1746671307380_light.png'

# Verified final assembly correction: continuous bar and 2 mm optical cover shell.
for ob in list(vehicle.objects):
    if ob.name.startswith('HeadlampClearCover') or ob.name.startswith('HandlebarCenterBridge'):
        bpy.data.objects.remove(ob,do_unlink=True)
tube('HandlebarCenterBridge',[(.235,-.043,.891),(.235,0,.887),(.235,.043,.891)],.0115,BLACK,3)
bpy.data.objects['ProjectorChromeFrame'].location.x=.321
bpy.data.objects['ProjectorLens'].location.x=.330
bpy.data.objects['HeadlampDarkOpticalCore'].location.x=.311
bpy.data.objects['YellowHeadlampRim'].location.x=.327
nr=24;na=96;vs=[];fs=[]
for layer in range(2):
    for i in range(nr+1):
        rr=.00005+(.066-.00005)*i/nr
        xx=.337+.007*(1-(rr/.066)**2)-layer*.002
        for j in range(na):
            a=2*math.pi*j/na;vs.append((xx,rr*math.cos(a),.994+rr*math.sin(a)))
stride=(nr+1)*na
for layer in range(2):
    for i in range(nr):
        for j in range(na):
            k=layer*stride+i*na+j;nextj=layer*stride+i*na+(j+1)%na
            face=(k,k+na,nextj+na,nextj)
            fs.append(face if layer==0 else tuple(reversed(face)))
for j in range(na):
    k=nr*na+j;q=nr*na+(j+1)%na
    fs.append((k,k+stride,q+stride,q))
for layer in range(2):
    center=len(vs);vs.append((.344-layer*.002,0,.994))
    for j in range(na):
        face=(center,layer*stride+j,layer*stride+(j+1)%na)
        fs.append(face if layer==0 else tuple(reversed(face)))
mesh('HeadlampClearCover_2mmShell',vs,fs,LENS_CLEAR,1,0)

# Align lettering to the outward panel normal and a readable tangent frame.
from mathutils import Matrix
for ob in list(vehicle.objects):
    if ob.name.startswith('RearCoverWordmark'):bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.view_layer.update()
for sg in [-1,1]:
    cover=bpy.data.objects['LeftIvoryConvexSideCover' if sg==1 else 'RightIvoryConvexSideCover'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    hit,p,n,idx=cover.ray_cast(Vector((-.683,sg*2,.367)),Vector((0,-sg,0)))
    if not hit:raise RuntimeError('Wordmark surface ray missed')
    n=n.normalized()
    if n.y*sg<0:n=-n
    right=Vector((-sg,0,0));right=(right-n*right.dot(n)).normalized();up=n.cross(right).normalized()
    cu=bpy.data.curves.new('RearCoverWordmarkText','FONT');cu.body='ninebot';cu.align_x='CENTER';cu.align_y='CENTER';cu.size=.018;cu.extrude=.00006;cu.bevel_depth=.000015;cu.bevel_resolution=1;cu.materials.append(BLACK)
    ob=bpy.data.objects.new('RearCoverWordmark',cu);vehicle.objects.link(ob);ob.parent=root;ob.location=p+n*.0015;ob.rotation_mode='QUATERNION';ob.rotation_quaternion=Matrix((right,up,n)).transposed().to_quaternion()
    ob['outward_normal']=list(n);ob['reading_tangent']=list(right)

# Flat machined rotor normals and surface-bound seams verified in macro renders.
rotor=bpy.data.objects['FrontBrakeDisc']
for face in rotor.data.polygons:face.use_smooth=False
for mod in rotor.modifiers:
    if mod.type=='BEVEL':mod.harden_normals=True
for ob in list(vehicle.objects):
    if ob.name.startswith('LowerSillJoint') or ob.name.startswith('PedestalLowerJoint'):
        bpy.data.objects.remove(ob,do_unlink=True)
SEAM_GRAY=bpy.data.materials['Panel Seam Gray']
bpy.context.view_layer.update()
body_eval=bpy.data.objects['ContinuousDeepYellowTub'].evaluated_get(bpy.context.evaluated_depsgraph_get())
for sg in [-1,1]:
    for label,mode in [('LowerSillJoint',0),('PedestalLowerJoint',1)]:
        pts=[]
        for i in range(50):
            t=i/49
            x,z=(-.45+.63*t,.15+.01*t*t) if mode==0 else (-.2+.07*t,.325-.026*t)
            hit,p,n,ix=body_eval.ray_cast(Vector((x,sg*2,z)),Vector((0,-sg,0)))
            if hit:
                n=n.normalized()
                if n.y*sg<0:n=-n
                pts.append(p+n*.0008)
        if len(pts)>1:tube(label,pts,.0007,SEAM_GRAY,2)

# --- September 2026 actual-video refinement. All coordinates remain meters. ---
# Evidence: Douyin 7633436353291877233, 11.300 / 54.700 / 62.050 / 183.250 s;
# XHS 6a2eaebf0000000022029594 photos 1-2. No labels/protective packaging reproduced.
root['geometry_basis']='Official scale plus actual lemon Q70C assembly video and XHS rear assembly photographs; hidden dimensions estimated'
root['reference_video']='https://www.douyin.com/video/7633436353291877233'
root['reference_rear_note']='6a2eaebf0000000022029594 photos 1 and 2'
RAIL_GREY=material('Observed light grey matte grab rail',(.48,.51,.50),.06,.53)
BUCKET=material('Molded black seat bucket',(.022,.025,.027),0,.49)
BUTTON=material('Control button pale grey',(.63,.66,.65),0,.42)
CONTROL_ORANGE=material('Observed orange grip ring state',(.95,.22,.025),0,.34,(1,.17,.01))
bsdf(CONTROL_ORANGE).inputs['Emission Strength'].default_value=.7
SEAT_RUBBER=material('Seat underside elastomer gasket',(.012,.014,.014),0,.66)
TAIL_RED=material('Rear red rounded perimeter lens',(.53,.005,.008),0,.23,(.9,.008,.006))
bsdf(TAIL_RED).inputs['Emission Strength'].default_value=.10

# Consistently smooth closed perimeter for shells, lids, seals and optical rings.
def roundrect(cx,cy,hx,hy,rad,n=8):
    out=[]
    for px,py,base in [(cx+hx-rad,cy+hy-rad,0),(cx-hx+rad,cy+hy-rad,90),(cx-hx+rad,cy-hy+rad,180),(cx+hx-rad,cy-hy+rad,270)]:
        for j in range(n+1):
            a=math.radians(base+90*j/n);out.append((px+rad*math.cos(a),py+rad*math.sin(a)))
    return out

def boolean_cut(target,cut,name):
    bpy.context.view_layer.objects.active=target
    m=target.modifiers.new(name,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cut
    bpy.ops.object.modifier_apply(modifier=m.name)

# Fully rounded pebble side panels with a non-pointed rear and gentle lower sweep.
remove_matching(['LeftIvoryConvexSideCover','RightIvoryConvexSideCover','RearCoverTuckedLip','RearCoverWordmark','SidePanelFastener'])
outline=[(-.205,.478),(-.217,.541),(-.267,.587),(-.342,.618),(-.422,.623),(-.513,.597),(-.608,.551),(-.691,.500),(-.742,.459),(-.758,.409),(-.741,.361),(-.664,.340),(-.556,.332),(-.448,.334),(-.343,.349),(-.268,.385),(-.222,.429)]
bound=catmull(outline,6)
for sg in [-1,1]:
    nr=18;nb=len(bound);vs=[];fs=[];center=Vector((-.465,.470))
    # Outer ring is a molded seam, inner rings describe actual transverse convexity.
    for i in range(nr):
        rr=1-i/nr
        for b in bound:
            p=center+(b-center)*rr
            bulge=.061*max(0,1-rr*rr)**.72
            vs.append((p.x,sg*(.207+bulge),p.y))
    for i in range(nr-1):
        for j in range(nb):
            k=i*nb+j;q=i*nb+(j+1)%nb
            face=(k,q,q+nb,k+nb);fs.append(face if sg>0 else tuple(reversed(face)))
    ci=len(vs);vs.append((center.x,sg*.268,center.y))
    for j in range(nb):
        f=((nr-1)*nb+j,(nr-1)*nb+(j+1)%nb,ci);fs.append(f if sg>0 else tuple(reversed(f)))
    ob=mesh(('Left' if sg>0 else 'Right')+'IvoryConvexSideCover',vs,fs,IVORY,1,.006)
    ob['source']='Actual side frame 11.300s; transverse bulge inferred'
    lip=[(b.x,sg*.205,b.y) for b in bound];lip.append(lip[0]);tube('SideCoverNarrowMoldedJoint',lip,.0012,YELLOW_DARK,2)

# Rebuild saddle to remove the excessive triangular wedge while keeping 730 mm contact.
remove_matching(['TaupeSaddle','SeatUpholsteryPiping','SeatStitch','SaddleSideSeam'])
seat=section_body('TaupeSaddle',[
(-.678,.008,.706,.717),(-.668,.070,.684,.734),(-.646,.126,.679,.741),(-.608,.166,.674,.741),
(-.554,.184,.669,.739),(-.470,.186,.660,.735),(-.370,.178,.634,.734),(-.276,.160,.611,.733),
(-.209,.140,.583,.731),(-.163,.113,.574,.720),(-.135,.082,.586,.703),(-.118,.039,.613,.680),(-.114,.005,.651,.664)],BROWN,power=3.0,sub=2)
bpy.context.view_layer.update();ev=seat.evaluated_get(bpy.context.evaluated_depsgraph_get())
hit,p,n,idx=ev.ray_cast(Vector((-.355,0,2)),Vector((0,0,-1)));assert hit
seat.location.z=.730-p.z;seat['contact_x_m']=-.355;seat['contact_z_m']=.730
# Upholstery seam is surface bound; it is not an exposed thick trim cord.
bpy.context.view_layer.update();ev=seat.evaluated_get(bpy.context.evaluated_depsgraph_get())
for sg in [-1,1]:
    pts=[]
    for j in range(60):
        xx=-.652+.498*j/59;zz=interp(xx,[(-.652,.696),(-.55,.691),(-.4,.678),(-.25,.644),(-.154,.621)])
        hit,p,n,idx=ev.ray_cast(Vector((xx,sg*2,zz-seat.location.z)),Vector((0,-sg,0)))
        if hit:pts.append(p+seat.location+n*.00065)
    if len(pts)>2:tube('SeatUpholsterySeam',pts,.0007,BROWN,2)
# ONE shared perimeter controls yellow outside, annular flange and black inside.
# Stable BVH sampling is independent of later dependency-graph updates.
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update();se_eval=seat.evaluated_get(bpy.context.evaluated_depsgraph_get());se_mesh=se_eval.to_mesh()
se_bvh=BVHTree.FromPolygons([se_eval.matrix_world@v.co for v in se_mesh.vertices],[tuple(f.vertices) for f in se_mesh.polygons],all_triangles=False)
se_eval.to_mesh_clear()
def saddle_under(x,y=0):
    p,n,ix,d=se_bvh.ray_cast(Vector((x,y,-.5)),Vector((0,0,1)))
    if p is None:p,n,ix,d=se_bvh.ray_cast(Vector((x,y*.88,-.5)),Vector((0,0,1)))
    return p.z if p is not None else interp(x,[(-.67,.685),(-.55,.668),(-.4,.642),(-.28,.616),(-.2,.590),(-.13,.625)])
underoutline=[(-.125,0),(-.143,.060),(-.199,.118),(-.286,.141),(-.421,.160),(-.557,.155),(-.631,.108),(-.662,.041),(-.67,0),(-.662,-.041),(-.631,-.108),(-.557,-.155),(-.421,-.160),(-.286,-.141),(-.199,-.118),(-.143,-.060)]
outerplan=[tuple(v) for v in catmull(underoutline,8)];nn=len(outerplan)
outertop=[(xx,yy,saddle_under(xx,yy)-.008) for xx,yy in outerplan]
innertop=[(-.4+(xx+.4)*.95,yy*.925,zz-.0015) for xx,yy,zz in outertop]
# Remove only the legacy upper rear volume. Its lower sill and lower body stay intact.
cut=cube('TemporaryRemoveLegacyUpperRear',(-.475,0,.725),(.405,.38,.390),None,.003)
bpy.context.view_layer.objects.active=cut
for m in list(cut.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
for m in list(body.modifiers):
    if m.type=='SUBSURF':
        bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=m.name)
boolean_cut(body,cut,'Replace upper rear by consistent hollow loft');bpy.data.objects.remove(cut,do_unlink=True)
# Boolean creates one large horizontal cap. Keep its normal planar instead of
# interpolating side-wall vertex normals across its arbitrary n-gon tessellation.
# This changes shading only; the visual shape and all vertex positions remain unchanged.
cap_faces=[]
for face in body.data.polygons:
    zs=[body.data.vertices[i].co.z for i in face.vertices]
    if len(face.vertices)>100 and max(zs)-min(zs)<.00002 and abs(sum(zs)/len(zs)-.335)<.00002:
        face.use_smooth=False;cap_faces.append(face.index)
assert len(cap_faces)==1,cap_faces

# Smooth outside loft, widening toward the old sill; no face crosses the mouth.
vs=[];fs=[];levels=12
for k in range(levels):
    t=k/(levels-1)
    for xx,yy,zz in outertop:
        rel=(xx+.4)/.27
        bx=xx-.091*min(1,abs(rel))**2 if xx<-.4 else xx-.012*min(1,abs(rel))**2
        by=yy*1.18
        vs.append((bx+(xx-bx)*t,by+(yy-by)*t+math.copysign(.037*math.sin(math.pi*t)*min(1,abs(yy)/.11),yy),.333+(zz-.333)*t))
for k in range(levels-1):
    for j in range(nn):
        a=k*nn+j;b=k*nn+(j+1)%nn;fs.append((a,b,b+nn,a+nn))
# Annulus outer -> inner, sharing the top wall vertices exactly.
innerstart=len(vs);vs.extend(innertop)
for j in range(nn):
    a=(levels-1)*nn+j;b=(levels-1)*nn+(j+1)%nn;fs.append((a,b,innerstart+(j+1)%nn,innerstart+j))
collar=mesh('YellowSeatPedestalCollar',vs,fs,YELLOW,1,.006)
collar['construction']='Continuous outside loft with annular top flange; identical indexed perimeter to black bucket'
# Independent bucket wall uses the same inner ring. It cannot protrude through the yellow wall.
vs=[];fs=[];blevels=9
for k in range(blevels):
    t=k/(blevels-1)
    for xx,yy,zz in innertop:
        bx=-.4+(xx+.4)*.79;by=yy*.79
        vs.append((bx+(xx-bx)*t,by+(yy-by)*t,.427+(zz-.427)*t))
for k in range(blevels-1):
    for j in range(nn):
        a=k*nn+j;b=k*nn+(j+1)%nn;fs.append((a,b,b+nn,a+nn))
fs.append(tuple(reversed(range(nn))))
bucket=mesh('IndependentDeepSeatBucket',vs,fs,BUCKET,1,.004)
bucket['source']='54.700s and 62.050s, unified nested ring construction; depth estimated'
pts=[(x,y,z+.001) for x,y,z in innertop];pts.append(pts[0]);tube('SeatBucketThickUpperLip',pts,.0032,BUCKET,3)
# Rear raised latch shelf and small front access panel sit inside the independent bucket.
cube('BucketRearRaisedPlatform',(-.584,0,.565),(.055,.131,.069),BUCKET,.017)
cube('BucketRearLatchInset',(-.574,0,.636),(.020,.011,.003),BLACK,.005)
for yy in [-.095,.095]:cyl('BucketRearFastener',(-.589,yy,.638),.007,.003,DARK,(0,0,0),24,.001)
cube('BucketFrontAccessCover',(-.235,0,.441),(.043,.081,.007),BUCKET,.008)
for yy in [-.055,.055]:cyl('BucketAccessFastener',(-.235,yy,.450),.004,.002,DARK,(0,0,0),24,.0007)
cube('BucketRearServiceModule',(-.598,-.086,.638),(.021,.014,.003),BUTTON,.004)
cube('BucketModuleRedTab',(-.599,-.086,.642),(.008,.008,.002),RED,.002)
# Rear support plate and paired grey mounts from the XHS uncovered view.
cube('RearSeatSupportCrossplate',(-.584,0,.609),(.029,.121,.006),BLACK,.008)
for sg in [-1,1]:
    cube('GrabRailGreySupport',(-.590,sg*.106,.625),(.023,.017,.009),RAIL_GREY,.006)
    for xx in [-.605,-.575]:cyl('GrabRailSupportBolt',(xx,sg*.106,.636),.005,.004,DARK,(0,0,0),6,.0008)
# Matte grey hoop, lower nearly horizontal side attachment, round turn across rear.
remove_matching(['UShapedRearGrabRail'])
tube('LightGreyRearGrabRail',[(-.507,-.177,.651),(-.614,-.206,.704),(-.692,-.174,.736),(-.719,-.093,.745),(-.722,0,.745),(-.719,.093,.745),(-.692,.174,.736),(-.614,.206,.704),(-.507,.177,.651)],.014,RAIL_GREY,5)

# Thin black underside pan with visible strengthening webs. Assembly pivots forward.
seat_parts=[ob for ob in vehicle.objects if ob.name.startswith(('TaupeSaddle','SeatUpholsterySeam'))]
underplan=[tuple(v) for v in catmull(underoutline,6)]
def pan_z(x):return saddle_under(x,0)-.003
vs=[];fs=[];nr=14;nb=len(underplan)
for i in range(nr):
    r=1-i/nr
    for xx,yy in underplan:
        x=-.4+(xx+.4)*r;y=yy*r;vs.append((x,y,saddle_under(x,y)-.004))
for i in range(nr-1):
    for j in range(nb):
        k=i*nb+j;q=i*nb+(j+1)%nb;fs.append((k,q,q+nb,k+nb))
ci=len(vs);vs.append((-.4,0,pan_z(-.4)-.004))
for j in range(nb):fs.append(((nr-1)*nb+j,(nr-1)*nb+(j+1)%nb,ci))
pan=mesh('SaddleBlackStructuralPan',vs,fs,BUCKET,1,.005);seat_parts.append(pan)
pts=[(xx,yy,saddle_under(xx,yy)-.007) for xx,yy in underplan];pts.append(pts[0]);seat_parts.append(tube('SaddlePeripheralRubberSeal',pts,.0045,SEAT_RUBBER,3))
for xx,w in [(-.59,.125),(-.53,.146),(-.47,.15),(-.41,.15),(-.35,.141),(-.29,.132),(-.23,.110),(-.18,.079)]:
    seat_parts.append(tube('SaddleUndersideCrossWeb',[(xx,-w,saddle_under(xx,-w)-.013),(xx,0,pan_z(xx)-.018),(xx,w,saddle_under(xx,w)-.013)],.0036,BUCKET,2))
for yy in [-.103,-.052,0,.052,.103]:
    pts=[]
    for xx in [-.596,-.54,-.47,-.4,-.33,-.26,-.211]:pts.append((xx,yy,saddle_under(xx,yy)-.015))
    seat_parts.append(tube('SaddleUndersideLongitudinalWeb',pts,.003,BUCKET,2))
# Rear lock loop and front transverse pin are physically separate from cosmetic seams.
seat_parts.append(tube('SaddleRearMetalLockLoop',[(-.581,-.013,.654),(-.581,-.013,.626),(-.581,.013,.626),(-.581,.013,.654)],.0032,SILVER_FINE,3))
for sg in [-1,1]:
    seat_parts.append(cube('SaddleHingeLeaf',(-.160,sg*.036,.582),(.034,.019,.004),BLACK,.004))
    cyl('FixedFrontHingeBarrel',(-.129,sg*.038,.580),.009,.025,DARK,(math.pi/2,0,0),32,.001)
cyl('FrontHingePin',(-.129,0,.580),.0048,.110,SILVER_FINE,(math.pi/2,0,0),32,.001)
bpy.context.view_layer.update()
pivot=bpy.data.objects.new('SEAT_OPEN_CONTROL',None);vehicle.objects.link(pivot);pivot.parent=root;pivot.location=(-.129,0,.580);pivot.empty_display_type='ARROWS';pivot.empty_display_size=.09
pivot['instructions']='Frame 1 closed; frame 45 open 78 degrees. Rotation Y controls the real front hinge.'
bpy.context.view_layer.update()
for ob in seat_parts:
    mw=ob.matrix_world.copy();ob.parent=pivot;ob.matrix_world=mw
pivot.rotation_euler[1]=0;pivot.keyframe_insert(data_path='rotation_euler',frame=1)
pivot.rotation_euler[1]=math.radians(78);pivot.keyframe_insert(data_path='rotation_euler',frame=45)
scene.frame_start=1;scene.frame_end=45;scene.timeline_markers.new('CLOSED',frame=1);scene.timeline_markers.new('SEAT OPEN',frame=45);scene.frame_set(1)

# Flush removable floor cover, molded nested loop grooves and restrained screw recesses.
remove_matching(['YellowFloorboard','FloorGripRib','PassengerStepBase','PassengerStepAlloyRail','PassengerStepTread'])
section_body('FloorboardContinuousSill',[(-.156,.012,.269,.291),(-.137,.197,.269,.297),(-.08,.218,.268,.299),(.14,.218,.271,.299),(.212,.187,.277,.301),(.229,.03,.288,.300)],YELLOW,power=9,sub=2)
cube('FlushRemovableBatteryFloorLid',(.025,0,.295),(.159,.169,.004),YELLOW,.010)
for hx,hy,rad in [(.161,.171,.024),(.124,.129,.040),(.083,.091,.049)]:
    pts=[(xx,yy,.2994) for xx,yy in roundrect(.025,0,hx,hy,rad,12)];pts.append(pts[0]);tube('FloorLidMoldedGroove',pts,.00065,YELLOW_DARK,2)
for xx in [-.108,.158]:
    for yy in [-.138,.138]:
        cyl('FloorLidRecess',(xx,yy,.299),.006,.001,YELLOW_DARK,(0,0,0),32,.0005)
        cyl('FloorLidFastener',(xx,yy,.2996),.0024,.001,DARK,(0,0,0),6,.0003)
# Only the observed folded side step remains; eliminate the duplicated lower accessory.
remove_matching(['RubberSideProtectionInsert'])
for sg in [-1,1]:
    cube('ObservedFoldedSideStep',(-.301,sg*.239,.304),(.063,.009,.017),BLACK,.012)
    cube('FoldedSideStepInset',(-.301,sg*.249,.306),(.052,.002,.009),DARK,.007)

# Smooth elliptical front fender, broad transverse crown without a roof-like sharp ridge.
remove_matching(['IvoryFrontFender'])
vs=[];fs=[];nx=64;ny=32
for i in range(nx+1):
    a=math.radians(28+130*i/nx)
    for j in range(ny+1):
        u=-1+2*j/ny
        xx=.538+.229*math.cos(a);yy=.119*u
        zz=.194+.267*math.sin(a)-.058*u*u
        # Rounded lips taper slightly at the two open ends rather than forming wing tips.
        xx-=.012*u*u*math.cos(a)
        vs.append((xx,yy,zz))
for i in range(nx):
    for j in range(ny):
        k=i*(ny+1)+j;fs.append((k,k+1,k+ny+2,k+ny+1))
mesh('IvoryRoundedFrontFender',vs,fs,IVORY,1,.008)

# Rear lamp and cap are surface-bound to the new curved tail; no external yellow block.
remove_matching(['TailLamp'])
bpy.context.view_layer.update();rear_eval=collar.evaluated_get(bpy.context.evaluated_depsgraph_get())
rear_mesh=rear_eval.to_mesh();rear_bvh=BVHTree.FromPolygons([rear_eval.matrix_world@v.co for v in rear_mesh.vertices],[tuple(f.vertices) for f in rear_mesh.polygons],all_triangles=False);rear_eval.to_mesh_clear()
def rear_point(y,z,off=.003):
    p,n,ix,d=rear_bvh.ray_cast(Vector((-2,y,z)),Vector((1,0,0)))
    return p+Vector((-off,0,0)) if p is not None else Vector((-.72-off,y,z))
def dense_loop(points,step=.003):
    out=[]
    for i,a in enumerate(points):
        b=points[(i+1)%len(points)];d=math.dist(a,b);n=max(1,math.ceil(d/step))
        for j in range(n):out.append(tuple(a[k]+(b[k]-a[k])*j/n for k in range(len(a))))
    return out
rr=dense_loop(roundrect(0,.465,.083,.036,.022,14));pts=[rear_point(yy,zz,.005) for yy,zz in rr];pts.append(pts[0]);tube('TailLampRedRoundedRing',pts,.0075,TAIL_RED,4)
outline_tail=dense_loop(roundrect(0,.465,.072,.026,.018,12));nr=12;nb=len(outline_tail);vs=[];fs=[]
for i in range(nr):
    r=1-i/nr
    for yy,zz in outline_tail:vs.append(rear_point(yy*r,.465+(zz-.465)*r,.010))
for i in range(nr-1):
    for j in range(nb):
        a=i*nb+j;b=i*nb+(j+1)%nb;fs.append((a,b,b+nb,a+nb))
ci=len(vs);vs.append(rear_point(0,.465,.010))
for j in range(nb):fs.append(((nr-1)*nb+j,(nr-1)*nb+(j+1)%nb,ci))
mesh('TailLampBlackCenter',vs,fs,BLACK,1,.002)
for sg in [-1,1]:
    p=rear_point(sg*.117,.489,.002)
    ob=uv('RearNarrowSideLens',p,(.005,.011,.034),GLASS,40);ob.rotation_euler[0]=sg*.17
pts=[]
for i in range(65):
    a=i*2*math.pi/64;pts.append(rear_point(.014*math.cos(a),.566+.014*math.sin(a),.0008))
tube('RearCircularServiceCapSeam',pts,.00055,YELLOW_DARK,2)
# Rebind cream side-cover transverse sections and returns to the new body surface.
bpy.context.view_layer.update();body_bvhs=[]
for target in [body,collar]:
    ev=target.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    body_bvhs.append(BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[tuple(f.vertices) for f in me.polygons],all_triangles=False));ev.to_mesh_clear()
remove_matching(['SideCoverNarrowMoldedJoint'])
for sg in [-1,1]:
    cover=bpy.data.objects['LeftIvoryConvexSideCover' if sg==1 else 'RightIvoryConvexSideCover']
    perimeter=[]
    for point in bound:
        x,z=point.x,point.y
        z+=.012*max(0,1-(z-.332)/.034)**2
        found=None
        for shift in [0,.006,.012,.018,.025,.034,.044,.055]:
            tx=x+shift if x<-.5 else x-shift;hits=[]
            for tree in body_bvhs:
                hp,hn,hi,hd=tree.ray_cast(Vector((tx,sg*2,z)),Vector((0,-sg,0)))
                if hp is not None:hits.append(hp)
            if hits:found=max(hits,key=lambda p:p.y*sg);break
        if found is None:found=Vector((x,sg*.20,z))
        # Maintain the photographed yellow tail field around the lamp: cream ends at its side border.
        if abs(found.y)<.122 and found.x<-.60:
            hp,hn,hi,hd=rear_bvh.ray_cast(Vector((-2,sg*.122,z)),Vector((1,0,0)))
            if hp is not None:found=hp
            found.y=sg*.122
        perimeter.append(Vector((found.x,sg*(abs(found.y)+.004),z)))
    center=Vector((-.465,sg*.273,.470));nb=len(perimeter);nr=18
    # A single smooth convex dome spans the body-bound rim; interior vertices are not independently snapped.
    for i in range(nr):
        r=1-i/nr
        for j,pb in enumerate(perimeter):
            blend=max(0,1-r*r)**.72
            cover.data.vertices[i*nb+j].co=(center.x+(pb.x-center.x)*r,pb.y+(center.y-pb.y)*blend,center.z+(pb.z-center.z)*r)
    cover.data.vertices[nr*nb].co=center;cover.data.update()
    pts=[v.copy() for v in perimeter];pts.append(pts[0]);tube('SideCoverNarrowMoldedJoint',pts,.0008,YELLOW_DARK,2)
remove_matching(['Fork'])
for sg in [-1,1]:
    tube('EnclosedFrontFork',[(.555,sg*.070,.178),(.472,sg*.070,.356),(.420,sg*.070,.500),(.345,sg*.070,.680),(.245,sg*.070,.885)],.016,DARK,3)
# Driver-side inner legshield closes the shell; two old fork-end stubs are enclosed.
# A molded left cubby and a small central hook follow the XHS assembly photos.
vs=[];fs=[];nz=52;ny=52
for iz in range(nz+1):
    t=iz/nz
    for iy in range(ny+1):
        u=-1+2*iy/ny
        top=.862-.024*u*u;z=.294+(top-.294)*t
        w=interp(z,[(.294,.192),(.45,.221),(.68,.211),(.862,.165)])
        y=u*w
        center_x=interp(z,[(.294,.188),(.40,.160),(.55,.160),(.70,.170),(.862,.172)])
        edge_x=interp(z,[(.294,.216),(.40,.259),(.55,.254),(.70,.174),(.862,.145)])
        x=center_x+(edge_x-center_x)*abs(u)**3
        # Recess moves forward into the shell, not out toward the rider.
        r=((y-.063)/.114)**2+((z-.678)/.069)**2
        if r<1:x+=.048*(1-r)**1.8
        vs.append((x,y,z))
for iz in range(nz):
    for iy in range(ny):
        k=iz*(ny+1)+iy;fs.append((k,k+ny+1,k+ny+2,k+1))
innerpanel=mesh('MoldedInnerLegshieldWithCubby',vs,fs,YELLOW,1,.006)
# Integral upper shoulder joins the inner face to the original yellow shell return.
bridge_vs=[];bridge_fs=[]
for iy in range(ny+1):
    u=-1+2*iy/ny;pin=Vector(vs[nz*(ny+1)+iy]);zz=.887-.045*u*u
    ex=interp(zz,[(.13,.137),(.23,.205),(.37,.28),(.53,.294),(.64,.235),(.76,.185),(.89,.18)])
    cx=interp(zz,[(.13,.45),(.34,.49),(.51,.531),(.61,.476),(.72,.393),(.83,.327),(.91,.264)])
    x=ex+(cx-ex)*max(0,1-u*u)**.7-.025
    bridge_vs.extend([pin,(x,u*.180,zz)])
for iy in range(ny):bridge_fs.append((2*iy,2*iy+1,2*iy+3,2*iy+2))
mesh('InnerLegshieldClosedUpperShoulder',bridge_vs,bridge_fs,YELLOW,1,.005)
bpy.context.view_layer.update();ie=innerpanel.evaluated_get(bpy.context.evaluated_depsgraph_get())
def inner_surface(y,z):
    hit,p,n,ix=ie.ray_cast(Vector((-1,y,z)),Vector((1,0,0)))
    return p if hit else Vector((.23,y,z))
# Surface-bound oval cubby rim and access-panel seam.
pts=[]
for i in range(81):
    a=2*math.pi*i/80;p=inner_surface(.0+.159*math.cos(a),.678+.073*math.sin(a));pts.append(p+Vector((-.0007,0,0)))
tube('InnerCubbyPerimeterJoint',pts,.0008,YELLOW_DARK,2)
p=inner_surface(-.045,.662)
hook=cube('InnerLegshieldBagHook',p+Vector((-.009,0,0)),(.010,.009,.019),BLACK,.006)
pts=[]
for y,z in roundrect(0,.457,.013,.058,.008,10):
    p=inner_surface(y,z);pts.append(p+Vector((-.0007,0,0)))
pts.append(pts[0]);tube('InnerLegshieldLowerAccessSeam',pts,.00065,YELLOW_DARK,2)
# The visible upper steering column is continuous into the handlebar base.
tube('EnclosedSteeringColumn',[(.237,0,.815),(.234,0,.866),(.235,0,.893)],.034,BLACK,4)
# Driver controls: actual grey buttons, orange ring state, compact mirrors, blank unpowered display.
remove_matching(['GreenControlRing','ControlRingBacking','SwitchgearUpperButton','SignalRocker','MirrorStem','MirrorBack','MirrorGlass','MirrorStemLocknut','SpeedDigits','SpeedUnits','InstrumentReady','BatterySegment'])
for sg in [-1,1]:
    torus('AmberControlRing',(.169,sg*.215,.981),.023,.0033,CONTROL_ORANGE)
    # Pale switch faces are on the rider-facing side, not flat on top of the handlebar.
    for yy,zz,sx,sz in [(sg*.236,.984,.006,.010),(sg*.257,.977,.006,.006),(sg*.245,.959,.010,.004)]:
        cube('ObservedPaleControlButton',(.110,yy,zz),(.003,sx,sz),BUTTON,.003)
    btn=cube('LeftRedOrRightGreenLowerButton',(.115,sg*.247,.944),(.005,.009,.004),RED if sg>0 else GREEN,.003)
    tube('MirrorStem',[(.158,sg*.243,.998),(.153,sg*.246,1.055),(.145,sg*.302,1.117)],.0045,BLACK,3)
    cyl('MirrorStemLocknut',(.158,sg*.243,1.001),.0065,.006,DARK,(0,0,0),6,.001)
    uv('MirrorBack',(.145,sg*.316,1.151),(.014,.050,.054),BLACK,48)
    uv('MirrorGlass',(.131,sg*.316,1.151),(.003,.044,.048),MIRROR,48)
# No speculative running UI and no packaging label; clean reflective unpowered screen.
bpy.data.objects['InstrumentScreen']['state']='Unpowered dark screen; publicity/protective film deliberately omitted'
# Project real panel lettering onto the revised convex shells.
bpy.context.view_layer.update()
for sg in [-1,1]:
    cover=bpy.data.objects['LeftIvoryConvexSideCover' if sg==1 else 'RightIvoryConvexSideCover'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    hit,p,n,ix=cover.ray_cast(Vector((-.667,sg*2,.376)),Vector((0,-sg,0)))
    if hit:
        n=n.normalized()
        if n.y*sg<0:n=-n
        right=Vector((-sg,0,0));right=(right-n*right.dot(n)).normalized();up=n.cross(right).normalized()
        ob=text_obj('RearCoverWordmark','ninebot',p+n*.001,(0,0,0),.017,BLACK,.00006)
        ob.rotation_mode='QUATERNION';ob.rotation_quaternion=Matrix((right,up,n)).transposed().to_quaternion()


# Neutral product studio; geometry preview uses the same side as the official yellow render.
world=scene.world or bpy.data.worlds.new('ProductWorld');scene.world=world;world.use_nodes=True
next(n for n in world.node_tree.nodes if n.type=='BACKGROUND').inputs['Color'].default_value=(.88,.9,.92,1)
next(n for n in world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=.35
for name,loc,energy,sx,sy in [('Key',(2.8,3.4,4),410,3.3,2.2),('Fill',(-2,3,2),170,3,3),('Rim',(-2,-3,3.5),420,3,1.7),('ApronStrip',(3,-1.5,1.9),90,1.0,2.7)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='RECTANGLE';d.size=sx;d.size_y=sy
    ob=bpy.data.objects.new(name,d);studio.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.55))-ob.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.004));ground=bpy.context.object;ground.name='WhiteSweep'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground);ground.data.materials.append(material('ProductWhite',(.89,.9,.91),0,.76))
def camera(name,loc,target,scale):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale
    ob=bpy.data.objects.new(name,d);studio.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
hero=camera('Q70C_HERO',(4.8,4.5,1.35),(0,0,.70),2.20)
side=camera('Q70C_SIDE',(0,-6,.61),(0,0,.61),1.84)
optics=camera('Q70C_OPTICS',(3,3,1.7),(.26,0,.96),.89)
wheelcam=camera('Q70C_WHEEL_DETAIL',(2,3,1.05),(.5,0,.255),.72)
rearcam=camera('Q70C_SADDLE_DETAIL',(-2,3,1.4),(-.46,0,.55),1.07)
scene.eevee.use_raytracing=True
scene.camera=hero;scene.render.resolution_x=1300;scene.render.resolution_y=1300
scene.view_settings.view_transform='Khronos PBR Neutral';scene.view_settings.look='None';scene.view_settings.exposure=-.55
scene.render.film_transparent=False
# Refined constraints are checked in evaluated world space with the animated seat closed.
scene.frame_set(1);bpy.context.view_layer.update()
ev=seat.evaluated_get(bpy.context.evaluated_depsgraph_get());inv=ev.matrix_world.inverted()
hit,p,n,idx=ev.ray_cast(inv@Vector((-.355,0,2)),inv.to_3x3()@Vector((0,0,-1)))
actual=(ev.matrix_world@p).z
assert hit and abs(actual-.730)<.0001
front_center=sum(v.co.x for v in bpy.data.objects['FrontWheel_Tire'].data.vertices)/len(bpy.data.objects['FrontWheel_Tire'].data.vertices)
rear_center=sum(v.co.x for v in bpy.data.objects['RearWheel_Tire'].data.vertices)/len(bpy.data.objects['RearWheel_Tire'].data.vertices)
assert abs((front_center-rear_center)-1.110)<.00001
bucketcam=camera('Q70C_OPEN_SEAT',(-1.8,2.6,2.15),(-.34,0,.65),1.20)
cockpitcam=camera('Q70C_DRIVER',(-2.5,2.4,2.0),(.17,0,.95),.84)
tailcam=camera('Q70C_REAR_REFINED',(-3.8,2.4,1.65),(-.52,0,.54),1.22)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=3
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    if any(d.type=='METAL' for d in prefs.devices):
        for d in prefs.devices:d.use=(d.type=='METAL')
        scene.cycles.device='GPU'
except Exception:pass
scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.09;scene.cycles.max_bounces=7;scene.cycles.transmission_bounces=5
scene.camera=hero;scene.render.resolution_x=1200;scene.render.resolution_y=1200
report={'wheelbase_m':front_center-rear_center,'seat_contact_x_m':-.355,'seat_contact_z_m':actual,'seat_open_frame':45,'seat_closed_frame':1,'seat_open_angle_degrees':78,'independent_bucket':True,'reference_video':'7633436353291877233','reference_rear':'6a2eaebf0000000022029594 photos 1-2','limits':'Reconstructed visualization; unmeasured transverse sections and hidden hardware are estimated. Preview uses up to 3 CPU threads, 24 samples, optional per-process Metal.'}
with open(os.path.join(OUT,'Q70C_refined_validation.json'),'w') as fp:json.dump(report,fp,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Ninebot_Q70C_Refined.blend'))
if os.environ.get('Q70_NO_RENDER','0')!='1':
    render_list=[(hero,'Q70C_Refined_Hero_Preview.png',1,1200,1200),(side,'Q70C_Refined_Side_Preview.png',1,1200,840),(bucketcam,'Q70C_Refined_OpenSeat_Preview.png',45,1200,1200),(cockpitcam,'Q70C_Refined_Cockpit_Preview.png',1,1200,1200),(tailcam,'Q70C_Refined_Rear_Preview.png',1,1200,1200)]
    for cam,name,frame,rx,ry in render_list:
        scene.frame_set(frame);scene.camera=cam;scene.render.resolution_x=rx;scene.render.resolution_y=ry;scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)
    scene.frame_set(1);scene.camera=hero;scene.render.resolution_x=1200;scene.render.resolution_y=1200
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Ninebot_Q70C_Refined.blend'))
print('Q70C_REFINED_READY',report)
