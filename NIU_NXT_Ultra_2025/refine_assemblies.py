"""Evidence-led NXT 2025 refinements, executed by build_niu_refined.py.
No manufacturer CAD dimensions are implied. +X front, +Y left, metres.
Source frame times and configuration boundaries are retained on assemblies.
"""
def tag(ob,evidence,assembly):
    ob['evidence']=evidence;ob['assembly']=assembly;return ob

def apply_cut(target,cutter,name='Actual opening'):
    mod=target.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

def plate(n,c,w,h,r,d,m,q=basis):return rounded_plate(n,Vector(c),w,h,r,d,m,q)

def panel_outline(w,h,r):
    pts=[]
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(13):
            a=math.radians(start+j*90/12);pts.append(Vector((x+r*math.cos(a),y+r*math.sin(a),0)))
    return pts

# 526s teardown removes the transparent outer window and reveals three optics.
remove_prefixes(['Optical technical backing','Clear polycarbonate front cover','Technical moulded channel',
 'Front cover recessed fixing','Front cover Torx centre','Optical cavity back wall','Dark projector chamber',
 'Black reflector shroud','Front optical annulus','Rounded projector optic mount','Clear square projector surround',
 'Single convex projector lens','Projector upper cutoff hood','NIU cover wordmark','Technical NXT print'])

smoked_glass=mat('NXT smoke-tinted outer polycarbonate',(.76,.80,.84),.022,0)
bs=next(n for n in smoked_glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=1.49
carrier_mat=mat('NXT graphite lamp carrier',(.022,.026,.029),.40,.07)
seal=mat('NXT black elastomer sealing lip',(.006,.007,.008),.56)
optic_clear=mat('NXT optical clear lens',(.94,.97,1),.025)
bs=next(n for n in optic_clear.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=1.49
diffuse_white=mat('NXT satin ring diffuser',(.75,.80,.85),.26,0,1.25)
H=(top-bottom).length
carrier=plate('NXT lamp carrier with service fixings',center+normal*.003,.319,H-.006,.025,.008,carrier_mat)
tag(carrier,'teardown 526s; trial 24s,34.5s','front_optics')
lamp=center-up*.089+normal*.005
cut=cyl('Temp carrier lamp opening',lamp,.0775,.05,metal,normal,96);apply_cut(carrier,cut)
cyl('NXT lamp cavity closed back',lamp-normal*.042,.077,.005,dark_refl,normal,96)

def lenslathe(n,c,profile,m):
    vv=[];ff=[];N=80
    for z,r in profile:
        for j in range(N):
            a=j*2*math.pi/N;vv.append(Vector(c)+normal*z+right*r*math.cos(a)+up*r*math.sin(a))
    for k in range(len(profile)-1):
        for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
    return mesh(n,vv,ff,m)

lenslathe('NXT annular dark cavity',lamp,[(-.04,.030),(-.036,.064),(-.005,.076),(.005,.079)],dark_refl)
shared_frame_mat=mat('NXT shared satin optical frame',(.15,.17,.19),.32,.65)
module=plate('NXT three-optic horizontal carrier',lamp-normal*.002,.133,.049,.014,.009,shared_frame_mat)
line('NXT continuous shared optical frame lip',[lamp+normal*.004+basis@v for v in panel_outline(.133,.049,.014)],.0013,silver,True)
for i,u in enumerate([-.039,0,.039],1):
    c=lamp+right*u
    cut=cyl('Temp three optic socket',c,.0178,.09,metal,normal,48);apply_cut(module,cut)
    lenslathe(f'NXT optic {i} reflector cup',c,[(-.023,.010),(-.016,.014),(-.003,.0175),(.003,.018)],refl)
    cyl(f'NXT optic {i} back baffle',c-normal*.028,.012,.003,dark_refl,normal,32)
    plate(f'NXT optic {i} LED substrate',c-normal*.025,.007,.006,.001,.002,silver)
    # Shallow rounded-rectangle primary windows, not protruding glass spheres.
    ob=plate(f'NXT main optical lens {i}',c+normal*.0045,.032,.029,.0055,.0025,optic_clear)
    plate(f'NXT optic {i} inner rectangular baffle',c-normal*.018,.027,.023,.005,.003,dark_refl)
    tag(ob,'three principal optical zones visible at teardown 526s','front_optics')
for rr,th,ma in [(.083,.0050,diffuse_white),(.090,.0015,silver),(.075,.0011,metal)]:
    line('NXT independent lamp ring',[lamp+normal*.007+right*rr*math.cos(j*2*math.pi/160)+up*rr*math.sin(j*2*math.pi/160) for j in range(160)],th,ma,True)
lampcap=cyl('NXT independent lamp clear cap',lamp+normal*.010,.0888,.0012,optic_clear,normal,128)
# Flat optical faces require flat shading: averaging their normals with the rim
# creates an unintended magnifying lens even when the geometry is almost flat.
for face in lampcap.data.polygons:
    if len(face.vertices)>4:face.use_smooth=False
tag(lampcap,'independent ring/lamp cap under outer front window, teardown 526s','front_optics')
for i in range(7):
    u=(i-3)*.012
    plate('NXT carrier upper cooling-style rib',onpanel(u,.064,.010),.0055,.093,.0022,.010,carrier_mat)
plate('NXT carrier upper badge recess',onpanel(0,.150,.012),.092,.065,.010,.005,dark_refl)
plate('NXT carrier niu badge plate',onpanel(0,.165,.016),.075,.025,.005,.004,carrier_mat)
text3d('niu','NXT retained niu front wordmark',onpanel(0,.166,.019),.026,mark,basis)
for sg in [-1,1]:
    line('NXT carrier perimeter channel',[onpanel(sg*.135,-.17,.009),onpanel(sg*.140,-.02,.009),onpanel(sg*.127,.022,.009),onpanel(sg*.127,.17,.009)],.00065,seal)
    for v in [-.183,.183]:
        c=onpanel(sg*.135,v,.012)
        cyl('NXT carrier recessed screw boss',c,.008,.005,inner,normal,32)
        cyl('NXT carrier recessed service fastener',c+normal*.003,.0033,.003,metal,normal,6)
outer=plate('NXT removable smoked front window',center+normal*.026,.327,H+.002,.027,.0025,smoked_glass)
tag(outer,'outer cover lifted off as one part at teardown 520s','front_optics')
line('NXT front window perimeter gasket',[center+normal*.024+basis@v for v in panel_outline(.331,H+.006,.028)],.0014,seal,True)

# Less uniformly swollen surfaces: pinched return and retained digitised side profile.
body=bpy.data.objects['Continuous apron and lower sill']
body['refinement']='cross-section taper derived from dealer 025s; calibrated XZ contour retained'
next(n for n in paint.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Coat Weight'].default_value=.22
next(n for n in paint.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Coat Roughness'].default_value=.19
next(n for n in seatmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=(.013,.015,.017,1)
remove_prefixes(['NXT apron angled silver accent','NXT accent red end'])
bpy.context.view_layer.update();be=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
for sg in [-1,1]:
    # Actual parting seam follows the inner side return; shell stays continuous.
    path=[]
    for u,v in [(820,918),(786,1048),(748,1160),(771,1360),(816,1500),(1020,1490),(1244,1482)]:
        q=px((u,v));hit,p,n,idx=be.ray_cast(Vector((q.x,sg,q.y)),Vector((0,-sg,0)))
        if hit:path.append(p+Vector((0,sg*.001,0)))
    # The side-ray contour crossed the inner face; omit unsupported V-shaped seam.
    path=[]
    for u,v in [(503,1260),(547,1370),(590,1447)]:
        q=px((u,v));hit,p,n,idx=be.ray_cast(Vector((q.x,sg,q.y)),Vector((0,-sg,0)))
        if hit:path.append(p+Vector((0,sg*.001,0)))
    if len(path)>2:
        line('NXT crisp shoulder silver stripe',sample(path,4),.0026,mark)
        a,b=path[-2],path[-1];line('NXT shoulder small red terminus',[b+(a-b)*.12,b],.0028,red)
    # Smooth transition loft, each column shares a cross-section with adjacent pieces.
    sk=[];sf=[]
    for xx,y,lo,hi in [(-.245,.209,.201,.279),(-.31,.204,.205,.285),(-.39,.186,.222,.299),(-.455,.164,.256,.315)]:
        for v in [0,.25,.5,.75,1]:
            sk.append((xx,sg*(y+.002*math.sin(v*math.pi)),lo+(hi-lo)*v))
    for k in range(3):
        for j in range(4):a=k*5+j;sf.append((a,a+1,a+6,a+5))
    ob=mesh('NXT rear sill angled continuation',sk,sf,inner,True)
    so=ob.modifiers.new('Separate lower shell wall','SOLIDIFY');so.thickness=.003


# A continuous side return closes the physical gap between the pinched apron
# section and the separately offset inner liner. Both edges follow the source loft.
for sg in [-1,1]:
    rv=[];rf=[];d=-.82
    aa=math.acos(signpow(d,1/.38))
    for ox,oz,ix,iz,w in curves[:49]:
        bx=(ox+ix)/2+(ox-ix)/2*d;bz=(oz+iz)/2+(oz-iz)/2*d
        by=sg*signpow(math.sin(aa),.22)*w*(.83+.17*(d+1)/2)
        shift=.009*max(0,min(1,(iz+.004-.325)/.07))
        rv.extend([(bx,by,bz),(ix+.004-shift,sg*w*.91,iz+.004)])
    for k in range(len(rv)//2-1):rf.append((2*k,2*k+1,2*k+3,2*k+2))
    ret=mesh('NXT continuous apron inner side return',rv,rf,inner,True)
    sol=ret.modifiers.new('Inner side return wall','SOLIDIFY');sol.thickness=.0025

# Functional front-inner pocket. Cut through both apron and its inner liner.
inner_q=Matrix((Vector((0,-1,0)),Vector((0,0,1)),Vector((-1,0,0)))).transposed().to_quaternion()
pc=Vector((.265,.078,.842))
for target in [body,bpy.data.objects['Continuous textured inner legshield']]:
    if target.name=='Continuous textured inner legshield':
        for vertex in target.data.vertices:
            vertex.co.x-=.009*max(0,min(1,(vertex.co.z-.325)/.07))
        so=target.modifiers.new('Closed liner wall before service openings','SOLIDIFY');so.thickness=.003
        bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=so.name)
    cut=plate('Temp actual inner pocket opening',pc,.120,.094,.014,.10,metal,inner_q)
    apply_cut(target,cut,'Recess for inner storage pocket')
plate('NXT inner front storage pocket back',pc+Vector((.046,0,0)),.115,.087,.012,.006,inner,inner_q)
for yy in [pc.y-.060,pc.y+.060]:box('NXT pocket side wall',(.280,yy,pc.z),(.062,.006,.087),inner,.005)
box('NXT storage pocket floor',(.280,pc.y,.798),(.062,.119,.006),inner,.004)
line('NXT pocket rolled mouth',[pc+inner_q@v for v in panel_outline(.127,.101,.017)],.003,inner,True)
plate('NXT ignition socket inner moulding',Vector((.264,-.086,.84)),.092,.074,.013,.006,inner,inner_q)
cyl('NXT round ignition bezel',(.255,-.086,.841),.015,.005,metal,(-1,0,0),48)
cyl('NXT ignition centre',(.251,-.086,.841),.010,.002,silver,(-1,0,0),48)
box('NXT inner apron bag hook base',(.227,0,.781),(.016,.035,.044),inner,.005)
line('NXT hinged luggage hook',[(.215,0,.798),(.201,0,.787),(.201,0,.767),(.218,0,.767)],.0045,metal)
# Attach hook to the actual inner apron rather than guessed X coordinates.
bpy.context.view_layer.update();ie=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
hit,hp,hn,ix=ie.ray_cast(Vector((-1,0,.781)),Vector((1,0,0)))
if hit:
    if hn.x>0:hn=-hn
    delta=hp+hn*.006-Vector((.227,0,.781))
    for ob in veh.all_objects:
        if ob.name.startswith(('NXT inner apron bag hook base','NXT hinged luggage hook')):ob.location+=delta
# Place the lower cover directly on the evaluated inner apron surface.
bpy.context.view_layer.update();inner_eval=bpy.data.objects['Continuous textured inner legshield'].evaluated_get(bpy.context.evaluated_depsgraph_get())
hit,p,n,ix=inner_eval.ray_cast(Vector((-1,0,.575)),Vector((1,0,0)))
if hit:
    if n.x>0:n=-n
    rr=Vector((0,-1,0));uu=n.cross(rr).normalized();q=Matrix((rr,uu,n)).transposed().to_quaternion()
    service=plate('NXT inner lower service cover',p+n*.003,.165,.113,.014,.004,inner,q)
    count=len(service.data.vertices)//2
    for vi,v in enumerate(service.data.vertices):
        ok,sp,sn,fi=inner_eval.ray_cast(Vector((-1,v.co.y,v.co.z)),Vector((1,0,0)))
        if ok:
            if sn.x>0:sn=-sn
            v.co=sp+sn*(.0008 if vi<count else .0032)
    for yy in [-.063,.063]:cyl('NXT inner service cover screw',p+n*.006+rr*yy-uu*.033,.003,.002,metal,n,6)
    print('INNER_SERVICE_COVER_SURFACE',tuple(p),tuple(n))
hit,ip,inn,ix=inner_eval.ray_cast(Vector((-1,-.086,.840)),Vector((1,0,0)))
if hit:
    if inn.x>0:inn=-inn
    delta=ip+inn*.004-Vector((.264,-.086,.840))
    for ob in veh.all_objects:
        if ob.name.startswith(('NXT ignition socket inner moulding','NXT round ignition bezel','NXT ignition centre')):ob.location+=delta



# Reproject footwell tread onto the thickened liner rather than its former height.
remove_prefixes(['Floor moulded rib'])
bpy.context.view_layer.update();floor_ev=bpy.data.objects['Continuous textured inner legshield'].evaluated_get(bpy.context.evaluated_depsgraph_get())
for i in range(11):
    x=(U0-(842+i*23))*S;pts=[]
    for j in range(19):
        y=-.18+j*.02;hit,p,n,idx=floor_ev.ray_cast(Vector((x,y,.95)),Vector((0,0,-1)))
        if hit:pts.append(p+Vector((0,0,.0016)))
    if len(pts)>2:line('NXT surface-fitted footwell tread rib',pts,.0012,rubber)

# TFT-centred faceted cockpit, with the short factory saddle kept independent.
remove_prefixes(['Tapered central cockpit moulding','Cockpit front four fastener plate','Cockpit fixing screw',
 'Instrument support stalk','TFT sealed housing','TFT powered-off lens','TFT rear cooling rib'])
screen_n=Vector((-.69,0,.724)).normalized();screen_r=Vector((0,-1,0));screen_u=screen_n.cross(screen_r)
screen_q=Matrix((screen_r,screen_u,screen_n)).transposed().to_quaternion();screen_c=Vector((.242,0,1.050))
outline=[(-.095,-.042),(-.068,-.075),(.068,-.075),(.095,-.042),(.100,.035),(.076,.074),(-.076,.074),(-.100,.035)]
vv=[]
for depth,sc in [(-.056,.75),(-.038,1),(.006,1)]:
    for x,y in outline:vv.append(screen_c+screen_r*x*sc+screen_u*y*sc+screen_n*depth)
ff=[tuple(range(7,-1,-1))]
for k in range(2):
    for j in range(8):ff.append((k*8+j,k*8+(j+1)%8,(k+1)*8+(j+1)%8,(k+1)*8+j))
# Open bezel centre remains an aperture, screen and under-chin surfaces are distinct.
pod=mesh('NXT faceted steering and instrument cowl',vv,ff,inner,False)
bev=pod.modifiers.new('Small cowl edge radii','BEVEL');bev.width=.004;bev.segments=3
tag(pod,'dealer 110s; trial 152.5/155s; low rectangular TFT within angular cowl','cockpit')
plate('NXT TFT instrument housing',screen_c,.140,.084,.010,.014,metal,screen_q)
plate('NXT TFT silver perimeter bezel',screen_c+screen_n*.009,.133,.077,.008,.004,silver,screen_q)
plate('NXT TFT dark display lens',screen_c+screen_n*.012,.124,.066,.006,.002,smoke,screen_q)
for u in [-.024,0,.024]:
    line('NXT subtle inactive screen glyph',[screen_c+screen_n*.013+screen_r*(u-.006)+screen_u*.004,screen_c+screen_n*.013+screen_r*(u+.006)+screen_u*.004],.0005,mark)
plate('NXT cockpit lower chin',screen_c-screen_u*.056,.13,.025,.005,.010,inner,screen_q)
line('NXT TFT lower silver bridge',[screen_c+screen_n*.016+screen_r*u+screen_u*v for u,v in [(-.033,-.036),(-.023,-.023),(.023,-.023),(.033,-.036)]],.0025,silver)
for sg in [-1,1]:
    # Mirror fitting differs between assembled riding and dealer delivery state.
    a=Vector((.263,sg*.210,1.055));b=Vector((.274,sg*.255,1.150));c=Vector((.277,sg*.338,1.192))
    cyl('NXT mirror threaded boss',a,.010,.026,metal,(0,0,1),12)
    line('NXT independent mirror bent stalk',sample([a,b,c],8),.0045,metal)
    n=Vector((-.74,-sg*.20,.642)).normalized();r=Vector((0,-1,0));r=(r-n*r.dot(n)).normalized();u=n.cross(r);q=Matrix((r,u,n)).transposed().to_quaternion()
    ob=cyl('NXT round mirror casing',c,.044,.012,inner,n,64)
    cyl('NXT mirror reflective glass',c+n*.007,.039,.0015,refl,n,64)
    tag(ob,'round mirrors on same-model riding footage 152.5s; dealer may omit fitting','cockpit')

# Factory short saddle bucket: real cavity, rolled rim, lid base and front hinge.
pedestal=bpy.data.objects['Shaped battery pedestal']
bucket_c=Vector((-.304,0,.516))
cut=plate('Temp separate bucket mouth',Vector((-.308,0,.580)),.291,.276,.047,.32,metal,Matrix.Identity(3).to_quaternion())
apply_cut(pedestal,cut,'Open independent underseat bucket')
outline=panel_outline(.287,.274,.045)
vv=[];ff=[];N=len(outline)
for z,sc in [(.647,1),(.624,.96),(.433,.83)]:
    for p in outline:vv.append((-.308+p.x*sc,p.y*sc,z))
for k in range(2):
    for j in range(N):ff.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
ff.append(tuple(2*N+j for j in range(N)))
bucket=mesh('NXT independent short-seat storage bucket',vv,ff,inner)
so=bucket.modifiers.new('Bucket moulded wall','SOLIDIFY');so.thickness=.003
tag(bucket,'dealer 060s open short saddle; separate tub and rim','underseat')
for z,w,h in [(.650,.300,.288),(.646,.293,.281)]:
    line('NXT underseat double rolled rim',[Vector((-.308,0,z))+p for p in panel_outline(w,h,.048)],.0028,seal,True)
lid=plate('NXT short saddle rigid underside',Vector((-.312,0,.663)),.302,.293,.048,.006,inner,Matrix.Identity(3).to_quaternion())
hingemat=mat('NXT plated seat hinge',(.38,.32,.14),.31,.76)
hinge=box('NXT short-seat front hinge leaf',(-.144,0,.639),(.030,.050,.006),hingemat,.002)
cyl('NXT short-seat hinge pin',(-.133,0,.646),.004,.061,silver,(0,1,0),32)
for yy in [-.018,.018]:cyl('NXT seat hinge mounting screw',(-.148,yy,.645),.003,.003,metal,(0,0,1),6)
box('NXT bucket rear latch striker',(-.450,0,.641),(.016,.037,.020),metal,.004)

# Open-centre brake rotors. Annulus and spokes are real metal, openings are air.
remove_prefixes(['Front drilled 220mm rotor','Rear drilled 190mm rotor','Rotor mounting fastener','ABS tone ring tooth','ABS encoder inner band'])
def annulus(name,x,z,ri,ro,y,th,m,N=144):
    vv=[];ff=[]
    for yy in [y-th/2,y+th/2]:
        for r in [ri,ro]:
            for j in range(N):a=j*2*math.pi/N;vv.append((x+r*math.cos(a),yy,z+r*math.sin(a)))
    for j in range(N):
        k=(j+1)%N;ff.extend([(j,k,k+N,j+N),(2*N+j,3*N+j,3*N+k,2*N+k),(j,2*N+j,2*N+k,k),(N+j,N+k,3*N+k,3*N+j)])
    return mesh(name,vv,ff,m,False)
def open_rotor(label,x,z,r,y):
    ob=annulus(f'NXT {label} open-window brake rotor',x,z,r*.68,r,y,.004,silver)
    cv=[];cf=[]
    for j in range(30):
        a=j*2*math.pi/30;rr=r*(.83 if j%2 else .93);hr=.0030;n=12;s=len(cv)
        for yy in [y-.010,y+.010]:
            for k in range(n):t=k*2*math.pi/n;cv.append((x+rr*math.cos(a)+hr*math.cos(t),yy,z+rr*math.sin(a)+hr*math.sin(t)))
        cf.extend([tuple(s+k for k in range(n-1,-1,-1)),tuple(s+n+k for k in range(n))])
        for k in range(n):cf.append((s+k,s+(k+1)%n,s+(k+1)%n+n,s+k+n))
    apply_cut(ob,mesh('Temp sparse rotor drillings',cv,cf,metal,False))
    annulus(f'NXT {label} rotor mounting centre',x,z,.020,.035,y,.004,silver,96)
    for j in range(5):
        a=j*2*math.pi/5
        vs=[]
        for rr,aa in [(.030,a-.13),(r*.70,a-.075),(r*.70,a+.08),(.030,a+.17)]:vs.append((x+rr*math.cos(aa),y,z+rr*math.sin(aa)))
        arm=mesh(f'NXT {label} rotor connecting arm',vs,[(0,1,2,3)],silver,False);so=arm.modifiers.new('Rotor connecting arm thickness','SOLIDIFY');so.thickness=.004
        cyl(f'NXT {label} rotor mounting bolt',(x+.029*math.cos(a),y+.004,z+.029*math.sin(a)),.003,.004,metal,verts=6)
    encoder=annulus(f'NXT {label} independent ABS encoder',x,z,.040,.061,y+.007,.0012,metal,144)
    # The slotted encoder uses individual actual cut-out windows.
    for j in range(36):
        a=j*2*math.pi/36;cp=(x+.051*math.cos(a),y+.007,z+.051*math.sin(a))
        cut=box('Temp ABS radial slot',cp,(.014,.010,.0045),metal,.0003,rot=(0,-a,0))
        apply_cut(encoder,cut)
    tag(ob,'trial 121.5s, dealer 025s: narrow drilled friction ring and open inner windows','brakes')
open_rotor('front',WB/2,zf,.11,.067)
open_rotor('rear',-WB/2,zr,.095,.067)

# Evidence of the front-axle fork brackets and the separate rear hub cover.
remove_prefixes(['Rear split cast spoke'])
for sg in [-1,1]:
    disk=cyl('NXT rear full-disc hub cover',(-WB/2,sg*.051,zr),.132,.006,metal,(0,1,0),96)
    for j in range(10):
        a=j*2*math.pi/10
        cyl('NXT rear motor perimeter fixing',(-WB/2+.125*math.cos(a),sg*.056,zr+.125*math.sin(a)),.0025,.002,silver,(0,sg,0),6)
    for j in range(3):
        a=j*2*math.pi/3
        line('NXT rear motor machined sector trim',[(-WB/2+r*math.cos(t),sg*.055,zr+r*math.sin(t)) for r,t in [(.025,a),(.116,a+.18),(.116,a+1.80),(.025,a)]],.0022,silver)
root['configuration']='2025 black factory short saddle and extended rear cargo rack; independently fitted round mirrors'
root['evidence_note']='Shared structure from public videos; short seat/rack from official reference and black dealer 060/110s. All non-published dimensions remain approximations.'
root['refined_optical_zones']=3
