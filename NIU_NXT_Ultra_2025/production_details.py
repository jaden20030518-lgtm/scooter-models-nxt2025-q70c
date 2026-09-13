"""Detailed visible assemblies, executed by build_niu_production.py.
Dimensions not supplied by the manufacturer remain visual approximations.
"""
import numpy as np

def remove_prefixes(prefixes):
    for ob in list(veh.all_objects):
        if any(ob.name.startswith(s) for s in prefixes):bpy.data.objects.remove(ob,do_unlink=True)

def microfinish(material,scale,rough_lo,rough_hi,distance,strength=.2):
    nt=material.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=2
    coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],tex.inputs['Vector'])
    ramp=nt.nodes.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1
    ramp.inputs['To Min'].default_value=rough_lo;ramp.inputs['To Max'].default_value=rough_hi
    nt.links.new(tex.outputs['Fac'],ramp.inputs['Value']);nt.links.new(ramp.outputs['Result'],bs.inputs['Roughness'])
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=distance;bump.inputs['Strength'].default_value=strength
    nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])

microfinish(paint,1600,.23,.28,.000022,.10)
pbs=next(n for n in paint.node_tree.nodes if n.type=='BSDF_PRINCIPLED');pbs.inputs['Coat Weight'].default_value=.42;pbs.inputs['Coat Roughness'].default_value=.12
microfinish(inner,2200,.48,.6,.00012,.22)
microfinish(rubber,1900,.56,.7,.00005,.22)
microfinish(seatmat,1100,.68,.79,.00018,.28)
next(n for n in seatmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Sheen Weight'].default_value=.18
microfinish(floor_mat,2300,.69,.81,.00013,.2)
microfinish(metal,2500,.29,.36,.000025,.1)
microfinish(silver,2400,.23,.31,.00001,.08)
silverb= next(n for n in silver.node_tree.nodes if n.type=='BSDF_PRINCIPLED');silverb.inputs['Anisotropic'].default_value=.5
glass=mat('Optical polycarbonate',(.96,.985,1),.035,0)
gb=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED');gb.inputs['Transmission Weight'].default_value=1;gb.inputs['IOR'].default_value=1.49
refl=mat('Lamp vacuum metallised reflector',(.73,.77,.8),.09,1)
dark_refl=mat('Optics deep housing',(.009,.012,.016),.25,.15)
mark=mat('Subdued technical print',(.20,.23,.25),.45)
circuit_mat=mat('Subtle dark technical channels',(.048,.06,.074),.48)
stitch=mat('Seat stitch graphite',(.07,.075,.08),.79)

# Replace polar-fan side covers with longitudinal sectional quad surfaces.
# This removes the diagonal reflection band produced by unequal radial spans.
remove_prefixes(['Left moulded trapezoid cover','Right moulded trapezoid cover'])
cover_sections=[
 (-.146,.367,.380,.002),(-.152,.348,.422,.013),(-.17,.331,.490,.030),
 (-.20,.317,.570,.047),(-.235,.316,.637,.056),(-.28,.321,.660,.058),
 (-.38,.326,.670,.054),(-.442,.336,.673,.045),(-.458,.350,.670,.025),
 (-.466,.382,.662,.008),(-.468,.400,.650,.001)
]
for sg in [-1,1]:
    ss=sample(cover_sections,6);vv=[];ff=[];N=48
    for x,lo,hi,depth in ss:
        for j in range(N+1):
            t=math.pi*j/N
            vv.append((x,sg*(.182+depth*math.sin(t)),(hi+lo)/2+(hi-lo)/2*math.cos(t)))
    for k in range(len(ss)-1):
        for j in range(N):
            i=k*(N+1)+j;ff.append((i,i+1,i+N+2,i+N+1))
    cover=mesh(('Left' if sg>0 else 'Right')+' moulded trapezoid cover',vv,ff,paint)
    so=cover.modifiers.new('Moulded cover thickness','SOLIDIFY');so.thickness=.002

# True recessed patterned rubber. The tread is radial geometry, not floating
# dark lines. Bead/sidewall profile follows the already calibrated tyre size.
remove_prefixes(['Front profiled road tyre','Rear profiled road tyre','Front tread groove','Rear tread groove'])
def production_tyre(label,x,z,r):
    anchors=[(-.025,.15),(-.047,.163),(-.052,.189),(-.044,.211),(-.028,r-.001),(0,r),(.028,r-.001),(.044,.211),(.052,.189),(.047,.163),(.025,.15)]
    # Angular vertices follow each groove boundary rather than cutting across
    # an unrelated regular grid. This prevents stair-stepped diagonal channels.
    section=sample(anchors,9)
    phases=[-.5,-.35,-.20,-.12,-.085,-.065,-.045,0,.045,.065,.085,.12,.20,.35]
    angular=[(sector,phase) for sector in range(48) for phase in phases]
    A=len(angular);B=len(section);vv=[];ff=[]
    for sector,phase in angular:
        for y,rad in section:
            a=(sector+phase)*2*math.pi/48-abs(y)*4.0
            if rad>r-.019:
                wall=max(0,min(1,(.085-abs(phase))/.040));groove=wall*wall*(3-2*wall)*.0021
                shoulder=max(0,min(1,(rad-(r-.019))/.009))
                rad-=groove*shoulder
            vv.append((x+rad*math.cos(a),y,z+rad*math.sin(a)))
    for i in range(A):
        for j in range(B-1):ff.append((i*B+j,((i+1)%A)*B+j,((i+1)%A)*B+j+1,i*B+j+1))
    mesh(label+' recessed road tread',vv,ff,rubber)
    for sg in [-1,1]:
        for rr in [.164,.193]:line(label+' moulded sidewall bead',[(x+rr*math.cos(a*2*math.pi/144),sg*.050,z+rr*math.sin(a*2*math.pi/144)) for a in range(144)],.0006,rubber,True)
production_tyre('Front',WB/2,zf,220*S);production_tyre('Rear',-WB/2,zr,218*S)

# Drilled rotors use actual holes through the metal. Cutters are baked then
# removed; the resulting mesh is portable and has no hidden dependencies.
remove_prefixes(['Front 220 mm disc','Rear 190 mm disc'])
def rotor(name,x,z,r,sg):
    N=160;vv=[];ff=[]
    for y in [sg*.067-.002,sg*.067+.002]:
        for rr in [.046,r]:
            for j in range(N):a=j*2*math.pi/N;vv.append((x+rr*math.cos(a),y,z+rr*math.sin(a)))
    for j in range(N):
        k=(j+1)%N
        ff.extend([(j,k,k+N,j+N),(j+2*N,j+3*N,k+3*N,k+2*N),(j,j+2*N,k+2*N,k),(j+N,k+N,k+3*N,j+3*N)])
    ob=mesh(name,vv,ff,silver,False)
    cv=[];cf=[]
    for count,rr,hr in [(28,r*.89,.0030),(22,r*.69,.0026)]:
        for j in range(count):
            a=2*math.pi*j/count;cx=x+rr*math.cos(a);cz=z+rr*math.sin(a);start=len(cv);n=16
            for yy in [sg*.067-.012,sg*.067+.012]:
                for k in range(n):t=k*2*math.pi/n;cv.append((cx+hr*math.cos(t),yy,cz+hr*math.sin(t)))
            cf += [tuple(start+k for k in range(n-1,-1,-1)),tuple(start+n+k for k in range(n))]
            for k in range(n):cf.append((start+k,start+(k+1)%n,start+(k+1)%n+n,start+k+n))
    cutter=mesh('Temporary rotor hole tool',cv,cf,metal,False)
    mod=ob.modifiers.new('Through drilled holes','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    be=ob.modifiers.new('Rotor edge rounding','BEVEL');be.width=.00028;be.segments=2
    for j in range(5):
        a=2*math.pi*j/5;boltpos=(x+.039*math.cos(a),sg*.072,z+.039*math.sin(a))
        cyl('Rotor mounting fastener',boltpos,.0032,.004,metal,verts=6)
    # Thin ABS encoder ring and open radial windows.
    for j in range(42):
        a=j*2*math.pi/42
        pts=[]
        for rr,ang in [(.048,a),(.06,a),(.06,a+.062),(.048,a+.062)]:pts.append((x+rr*math.cos(ang),sg*.075,z+rr*math.sin(ang)))
        eo=mesh('ABS tone ring tooth',pts,[(0,1,2,3)],metal,False);so=eo.modifiers.new('Tone ring metal thickness','SOLIDIFY');so.thickness=.001
    line('ABS encoder inner band',[(x+.047*math.cos(a*2*math.pi/144),sg*.075,z+.047*math.sin(a*2*math.pi/144)) for a in range(144)],.0015,metal,True)
rotor('Front drilled 220mm rotor',WB/2,zf,.11,1);rotor('Rear drilled 190mm rotor',-WB/2,zr,.095,1)

# Curved cast caliper, its mounting ears, bolt recesses and continuous hose.
remove_prefixes(['Front caliper'])
box('Front caliper casting',(.535,.112,.272),(.056,.045,.088),metal,.016,rot=(0,.25,0))
for zz in [.245,.291]:
    cyl('Caliper piston cover',(.535,.139,zz),.016,.009,metal)
    cyl('Caliper cover hex bolt',(.535,.146,zz),.004,.003,silver,verts=6)
line('Front hydraulic hose',sample([(.537,.12,.30),(.49,.115,.49),(.43,.09,.72),(.31,.13,.92),(.24,.225,1.029)],10),.0032,rubber)

# Smoked technical lens: printed backing, clear three-dimensional cover,
# deeply nested reflector, projector lens and restrained DRL diffusion.
remove_prefixes(['Flush rounded smoked front lens','Circular front DRL','Projector dark cavity','Headlight rectangular optic'])
backing=rounded_plate('Optical technical backing',center+normal*.004,.325,(top-bottom).length,.024,.006,dark_refl,basis)
rounded_plate('Clear polycarbonate front cover',center+normal*.014,.329,(top-bottom).length+.004,.026,.003,glass,basis)
def onpanel(u,v,h=.009):return center+right*u+up*v+normal*h
for u in [-.116,-.085,-.025,.032,.105]:
    bottom_v=.012 if abs(u)<.08 else -.052
    line('Technical moulded channel',[onpanel(u,bottom_v),onpanel(u,.045),onpanel(u+.008,.063),onpanel(u+.008,.16)],.00022,circuit_mat)
for u,v in [(-.135,.183),(.135,.183),(-.135,-.183),(.135,-.183)]:
    cyl('Front cover recessed fixing',onpanel(u,v,.010),.0036,.003,metal,normal,16)
    cyl('Front cover Torx centre',onpanel(u,v,.012),.0017,.001,dark_refl,normal,6)
lamp=center-up*.089+normal*.010
cavity_tool=cyl('Temporary optical recess tool',lamp-normal*.025,.0775,.095,metal,normal,96)
for target in [backing,bpy.data.objects['Continuous apron and lower sill']]:
    mod=target.modifiers.new('Recessed optical cavity','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cavity_tool
    bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cavity_tool,do_unlink=True)
cyl('Optical cavity back wall',lamp-normal*.040,.077,.003,dark_refl,normal,96)
def lathe_optic(name,profile,m):
    vv=[];ff=[];N=96
    for depth,rr in profile:
        for j in range(N):
            t=j*2*math.pi/N;vv.append(lamp+normal*depth+right*rr*math.cos(t)+up*rr*math.sin(t))
    for k in range(len(profile)-1):
        for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    return mesh(name,vv,ff,m)
lathe_optic('Dark projector chamber',[(-.026,.036),(-.023,.044),(-.008,.069),(0,.075),(.002,.077)],dark_refl)
lathe_optic('Black reflector shroud',[(-.028,.034),(-.029,.057),(-.011,.078),(.001,.081)],dark_refl)
for rr,th,m in [(.083,.0065,white),(.091,.0012,silver),(.075,.0012,metal)]:
    line('Front optical annulus',[lamp+normal*.004+right*rr*math.cos(j*2*math.pi/128)+up*rr*math.sin(j*2*math.pi/128) for j in range(128)],th,m,True)
lenscenter=lamp+normal*.005
lens=rounded_plate('Rounded projector optic mount',lenscenter,.049,.042,.009,.014,dark_refl,basis)
rounded_plate('Clear square projector surround',lenscenter+normal*.009,.043,.038,.008,.009,glass,basis)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=lenscenter+normal*.015)
o=finish(bpy.context.object,'Single convex projector lens',glass);o.scale=(.016,.015,.007);o.rotation_mode='QUATERNION';o.rotation_quaternion=basis
rounded_plate('Projector upper cutoff hood',lenscenter+up*.026-normal*.006,.063,.011,.003,.023,metal,basis)

# Geometry typography is used only for visible markings; public photos remain
# references and are not pasted onto the vehicle as substitute geometry.
def text3d(body,name,loc,size,m,orientation,extrude=.00015):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=extrude;cu.bevel_depth=.00004
    ob=bpy.data.objects.new(name,cu);veh.objects.link(ob);ob.parent=root;cu.materials.append(m);ob.location=loc;ob.rotation_mode='QUATERNION';ob.rotation_quaternion=orientation;return ob
text3d('niu','NIU cover wordmark',onpanel(0,.165,.011),.029,mark,basis)
text3d('NXT','Technical NXT print',onpanel(0,.126,.011),.009,mark,basis)
for sg in [-1,1]:
    ori=Matrix((Vector((-sg,0,0)),Vector((0,0,1)),Vector((0,sg,0)))).transposed().to_quaternion()
    text3d('CST','CST sidewall mark',(WB/2,sg*.052,zf-.183),.016,red,ori)
    text3d('NIU ENERGY SYSTEM  /  GoFar','Low sill grey graphic',(.05,sg*.226,.222),.0065,mark,ori)

# Upholstery texture and actual perimeter piping/stitches; not a rectangular
# slab. Stitching follows the calibrated seat section widths.
for sg in [-1,1]:
    seam=[]
    for x,zt,zb,w in rows:
        seam.append((x,sg*w*.92,zt-(zt-zb)*.26))
    line('Saddle edge piping',seam,.001,stitch)
    for j in range(0,len(seam)-1,2):
        a=Vector(seam[j]);b=Vector(seam[min(len(seam)-1,j+1)])
        if (b-a).length>.001:line('Individual saddle stitch',[a,b],.00032,stitch)

# Production cockpit components: ergonomically shaped switchgear, grip ribs,
# reservoir, lever pivots, bezel and display bracket.
remove_prefixes(['Compact steering centre','Switchgear','Grip rubber','5 inch TFT display'])
box('Tapered central cockpit moulding',(.265,0,.992),(.12,.205,.092),inner,.026,rot=(0,-.18,0))
panel=rounded_plate('Cockpit front four fastener plate',Vector((.31,0,1.004)),.156,.052,.012,.004,metal,Matrix((Vector((0,1,0)),Vector((0,0,1)),Vector((1,0,0)))).transposed().to_quaternion())
for yy in [-.054,.054]:
    for zz in [.991,1.02]:cyl('Cockpit fixing screw',(.315,yy,zz),.0035,.003,dark_refl,(1,0,0),6)
for sg in [-1,1]:
    cyl('Soft grip core',(.255,sg*.315,1.012),.019,.115,rubber)
    for i in range(28):
        yy=sg*(.263+i*.0037)
        line('Grip moulded rib',[(.255+.0195*math.cos(t*2*math.pi/40),yy,1.012+.0195*math.sin(t*2*math.pi/40)) for t in range(40)],.00065,rubber,True)
    cyl('Grip end cap',(.255,sg*.374,1.012),.020,.006,metal)
    box('Hand control ergonomic shell',(.247,sg*.235,1.023),(.066,.069,.050),inner,.016,rot=(0,-.12,0))
    box('Thumb selector',(.274,sg*.225,1.034),(.025,.025,.016),metal,.006,rot=(0,-.12,0))
    cyl('Selector surface',(.291,sg*.225,1.034),.008,.003,metal,(1,0,0),20)
    cyl('Brake lever pivot',(.30,sg*.238,1.013),.005,.02,silver,(0,0,1),12)
    box('Front brake master reservoir',(.29,sg*.2,1.056),(.048,.055,.023),metal,.005)
    for yy in [-.012,.012]:cyl('Reservoir cap screw',(.29,sg*.2+yy,1.07),.0015,.001,silver,(0,0,1),6)
    box('Clear front turn indicator',(.283,sg*.25,.975),(.028,.061,.012),glass,.004)
    rod('Indicator rubber mounting stem',(.263,sg*.24,1.005),(.280,sg*.25,.980),.0058,rubber)
    line('Front indicator inner elements',[ (.282,sg*.22,.975),(.282,sg*.28,.975)],.0023,amber)
rod('Instrument support stalk',(.252,0,1.01),(.225,0,1.057),.011,metal)
screen_n=Vector((-.90,0,.43589)).normalized();screen_r=Vector((0,-1,0));screen_u=screen_n.cross(screen_r)
screen_q=Matrix((screen_r,screen_u,screen_n)).transposed().to_quaternion();screen_c=Vector((.241,0,1.052))
rounded_plate('TFT sealed housing',screen_c,.133,.076,.009,.018,metal,screen_q)
rounded_plate('TFT powered-off lens',screen_c+screen_n*.010,.116,.060,.006,.0018,smoke,screen_q)
for yy in [-.040,-.025,-.010,.010,.025,.040]:
    line('TFT rear cooling rib',[screen_c-screen_n*.010+screen_r*yy-screen_u*.020,screen_c-screen_n*.010+screen_r*yy+screen_u*.020],.0012,metal)

# Front pedestal moulding: recess the surface itself, then place the seam
# against the resulting evaluated shape. Avoid detached decorative patches.
pedestal=bpy.data.objects['Shaped battery pedestal']
for vertex in pedestal.data.vertices:
    co=vertex.co
    if co.x>-.14 and .34<co.z<.55 and abs(co.y)<.125:
        wy=max(0,1-(abs(co.y)/.125)**8);wz=max(0,1-(abs(co.z-.445)/.105)**8)
        co.x-=.004*wy*wz
bm=bmesh.new();bm.from_mesh(pedestal.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(pedestal.data);bm.free()
bpy.context.view_layer.update();pe=pedestal.evaluated_get(bpy.context.evaluated_depsgraph_get())
recess_pts=[]
for y,z in [(-.098,.36),(-.115,.39),(-.112,.49),(-.07,.535),(.07,.535),(.112,.49),(.115,.39),(.098,.36),(-.098,.36)]:
    hit,p,n,idx=pe.ray_cast(Vector((1,y,z)),Vector((-1,0,0)))
    if hit:recess_pts.append(p+Vector((.001,0,0)))
if len(recess_pts)>3:line('Underseat moulding recessed outline',sample(recess_pts,5),.0018,metal)
front_q=Matrix((Vector((0,1,0)),Vector((0,0,1)),Vector((1,0,0)))).transposed().to_quaternion()
hit,p,n,idx=pe.ray_cast(Vector((1,0,.387)),Vector((-1,0,0)))
if hit:text3d('GOeasy','Pedestal moulding embossed wordmark',p+Vector((.0012,0,0)),.011,inner,front_q)

# Fine grey lower side-panel graphics and a painted apron shoulder seam.
for sg in [-1,1]:
    name=('Left' if sg>0 else 'Right')+' moulded trapezoid cover'
    cover_obj=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
    p3d=[]
    for u,v in [(1315,1420),(1385,1410),(1487,1402)]:
        q=px((u,v));hit,p,n,idx=cover_obj.ray_cast(Vector((q.x,sg, q.y)),Vector((0,-sg,0)))
        if hit:p3d.append(p+Vector((0,sg*.001,0)))
    if p3d:line('Side cover muted graphic baseline',p3d,.00065,mark)

# Tiny moulded fasteners, proper side reflectors and a cast fork texture.
for sg in [-1,1]:
    for xx,zz in [(.5,.44),(.55,.34),(.60,.245)]:
        cyl('Fork clamp hex fixing',(xx,sg*.12,zz),.0045,.004,metal,verts=6)

# The NXT fender has moulded cheek pieces below the curved crown. Trace their
# side contour; a thin arc alone omitted this prominent visible structure.
fender_cheek=sample([px(p) for p in [(315,1390),(404,1364),(483,1365),(534,1391),(546,1427),(518,1488),(477,1486),(420,1450)]],5,True)
fc=sum(fender_cheek,Vector((0,0)))/len(fender_cheek)
for sg in [-1,1]:
    vv=[];ff=[];N=len(fender_cheek)
    for r,yy in [(1,.079),(.94,.085),(.65,.090),(.12,.091)]:
        for p in fender_cheek:
            q=fc+(p-fc)*r;vv.append((q.x,sg*yy,q.y))
    for k in range(3):
        for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    vv.append((fc.x,sg*.091,fc.y));idx=len(vv)-1
    for j in range(N):ff.append((3*N+j,3*N+(j+1)%N,idx))
    cheek=mesh('Front fender moulded side cheek',vv,ff,paint);so=cheek.modifiers.new('Fender cheek thickness','SOLIDIFY');so.thickness=.0025
    q=px((430,1438));ori=Matrix((Vector((-sg,0,0)),Vector((0,0,1)),Vector((0,sg,0)))).transposed().to_quaternion()
    text3d('ABS','Fender ABS mark',(q.x,sg*.092,q.y),.013,mark,ori)
    for u,v in [(513,1408),(495,1464)]:
        q=px((u,v));cyl('Fender recessed fastener',(q.x,sg*.091,q.y),.0033,.002,metal,(0,sg,0),6)

remove_prefixes(['Fork side reflector'])
for sg in [-1,1]:
    upv=Vector((-.36,0,.93)).normalized();nv=Vector((0,sg,0));rv=upv.cross(nv)
    oq=Matrix((rv,upv,nv)).transposed().to_quaternion();c=Vector((.535,sg*.116,.38))
    rounded_plate('Amber capsule reflector backing',c,.027,.078,.012,.005,metal,oq)
    rounded_plate('Amber capsule prism surface',c+nv*.003,.021,.071,.010,.002,amber,oq)
    for j in range(16):
        p=c+upv*((j/15-.5)*.063)+nv*.0045
        line('Reflector microprism strip',[p-rv*.008,p+rv*.008],.00033,amber)

body_eval=bpy.data.objects['Continuous apron and lower sill'].evaluated_get(bpy.context.evaluated_depsgraph_get())
for sg in [-1,1]:
    stripe=[]
    for u,v in [(500,1270),(537,1360),(591,1450)]:
        q=px((u,v));hit,p,n,idx=body_eval.ray_cast(Vector((q.x,sg,q.y)),Vector((0,-sg,0)))
        if hit:stripe.append(p+Vector((0,sg*.0006,0)))
    if len(stripe)>1:
        line('NXT apron angled silver accent',stripe,.0015,mark)
        a,b=Vector(stripe[-2]),Vector(stripe[-1]);line('NXT accent red end',[b+(a-b)*.14,b],.0016,red)

remove_prefixes(['Flush red rear seam'])
bpy.context.view_layer.update()
for sg in [-1,1]:
    cover_ev=bpy.data.objects[('Left' if sg>0 else 'Right')+' moulded trapezoid cover'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    path=sample([px(p) for p in [(1504,1221),(1510,1293),(1515,1380)]],8)
    vv=[];ff=[]
    for j,p in enumerate(path):
        tangent=(path[min(j+1,len(path)-1)]-path[max(j-1,0)]).normalized();across=Vector((-tangent.y,tangent.x))
        row=[]
        for sign in [-1,1]:
            q=p+across*.004*sign;hit,hp,n,ix=cover_ev.ray_cast(Vector((q.x,sg,q.y)),Vector((0,-sg,0)))
            if hit:row.append(hp+Vector((0,sg*.00045,0)))
        if len(row)==2:vv.extend(row)
    for j in range(len(vv)//2-1):ff.append((2*j,2*j+1,2*j+3,2*j+2))
    if ff:mesh('Flush red painted side stripe',vv,ff,red)

root['production_note']='Public-reference product visualization. Exterior geometry and microfeatures remain reconstructions, not manufacturer CAD.'

# Final fender is one continuous moulding, not intersecting crown/cheek shells.
remove_prefixes(['Close fitting front fender','Front fender moulded side cheek','Fender ABS mark','Fender recessed fastener'])
frows=sample([(*px((u,top)),(GROUND-low)*S,w) for u,top,low,w in [
 (280,1402,1409,.027),(315,1384,1422,.069),(375,1355,1462,.085),
 (434,1350,1485,.087),(486,1360,1488,.085),(535,1390,1450,.074),(563,1420,1431,.033)]],6)
vv=[];ff=[];N=32
for x,topz,lowz,w in frows:
    for j in range(N+1):
        u=-1+2*j/N;vv.append((x,u*w,topz-(topz-lowz)*u*u))
for k in range(len(frows)-1):
    for j in range(N):
        i=k*(N+1)+j;ff.append((i,i+1,i+N+2,i+N+1))
fo=mesh('Continuous moulded front fender',vv,ff,paint);so=fo.modifiers.new('Fender wall','SOLIDIFY');so.thickness=.003
bpy.context.view_layer.update();fe=fo.evaluated_get(bpy.context.evaluated_depsgraph_get())
for sg in [-1,1]:
    q=px((436,1430));hit,p,n,ix=fe.ray_cast(Vector((q.x,sg,q.y)),Vector((0,-sg,0)))
    if hit:
        if n.y*sg<0:n=-n
        rv=Vector((-sg,0,0));rv=(rv-n*rv.dot(n)).normalized();uv=n.cross(rv)
        text3d('ABS','Conforming fender ABS mark',p+n*.0005,.012,mark,Matrix((rv,uv,n)).transposed().to_quaternion())
    for u,v in [(501,1419),(493,1468)]:
        q=px((u,v));hit,p,n,ix=fe.ray_cast(Vector((q.x,sg,q.y)),Vector((0,-sg,0)))
        if hit:
            if n.y*sg<0:n=-n
            cyl('Fender fitted fixing',p+n*.001,.0032,.002,metal,n,6)
