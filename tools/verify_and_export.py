"""Independent evaluated-mesh checks and optional glTF round-trip for both scooters."""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser()
p.add_argument('--asset',required=True)
p.add_argument('--kind',choices=['niu','q70'],required=True)
p.add_argument('--report',required=True)
p.add_argument('--export')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(Path(args.asset).resolve()))
scene=bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
col=bpy.data.collections['NIU_NXT_ULTRA_2025' if args.kind=='niu' else 'NINEBOT_Q70C']
root=bpy.data.objects['NIU_ROOT' if args.kind=='niu' else 'Q70C_ROOT']
deps=bpy.context.evaluated_depsgraph_get()
minimum=[float('inf')]*3;maximum=[-float('inf')]*3;names=[];faces=0
missing_material=[]
surface_edges={}
for ob in col.all_objects:
    if ob.type not in {'MESH','CURVE','FONT','SURFACE'}:continue
    ancestor=ob.parent
    while ancestor and ancestor!=root:ancestor=ancestor.parent
    assert ancestor==root,('Unparented vehicle part',ob.name)
    ev=ob.evaluated_get(deps);me=ev.to_mesh()
    if not me:continue
    names.append(ob.name);faces+=len(me.polygons)
    if ob.name in {'Continuous textured inner legshield','Continuous apron and lower sill','ContinuousDeepYellowTub'}:
        longest=max(((ev.matrix_world@me.vertices[e.vertices[0]].co)-(ev.matrix_world@me.vertices[e.vertices[1]].co)).length for e in me.edges)
        surface_edges[ob.name]={'longest_edge_m':longest,'faces':len(me.polygons)}
    if not me.materials:missing_material.append(ob.name)
    for v in me.vertices:
        world=ev.matrix_world@v.co
        assert all(math.isfinite(c)for c in world),('Nonfinite coordinate',ob.name)
        for axis in range(3):
            minimum[axis]=min(minimum[axis],world[axis]);maximum[axis]=max(maximum[axis],world[axis])
    ev.to_mesh_clear()
assert not missing_material,missing_material
assert len(names)>30,'Vehicle geometry missing'

def mesh_xcenter(name):
    ob=bpy.data.objects[name];ev=ob.evaluated_get(deps);me=ev.to_mesh()
    result=sum((ev.matrix_world@v.co).x for v in me.vertices)/len(me.vertices)
    ev.to_mesh_clear();return result

if args.kind=='niu':
    wheelbase=abs(bpy.data.objects['Front axle'].matrix_world.translation.x-bpy.data.objects['Rear axle'].matrix_world.translation.x)
    expected=1.24456228956
    seat=bpy.data.objects['Reference shaped saddle'];xs=[-.32,-.28,-.24,-.20,-.18]
else:
    wheelbase=abs(mesh_xcenter('FrontWheel_Tire')-mesh_xcenter('RearWheel_Tire'))
    expected=1.110
    candidates=[o for o in col.all_objects if o.type=='MESH' and ('saddle' in o.name.lower() or 'seat' in o.name.lower())]
    # A ray over the calibrated rider contact point must hit the highest upholstery surface.
    seat=None;xs=[-.355]
assert abs(wheelbase-expected)<.00005,('Wheelbase drift',wheelbase,expected)
samples=[]
for x in xs:
    hits=[]
    for ob in ([seat] if seat else candidates):
        ev=ob.evaluated_get(deps);inv=ev.matrix_world.inverted()
        origin=inv@Vector((x,0,2));direction=(inv.to_3x3()@Vector((0,0,-1))).normalized()
        hit,loc,normal,index=ev.ray_cast(origin,direction)
        if hit:hits.append(((ev.matrix_world@loc).z,ob.name))
    assert hits,('Missing saddle at contact point',x)
    z,name=max(hits);samples.append({'x':x,'z':z,'surface':name})
if args.kind=='q70':assert abs(samples[0]['z']-.730)<.0015,samples
else:assert all(.720<s['z']<.760 for s in samples),samples
report={'asset':str(Path(args.asset).resolve()),'frame':1,'wheelbase_m':wheelbase,
        'wheelbase_basis':'Official 1110 mm' if args.kind=='q70' else 'Existing official-image calibration; not a published dimension',
        'seat_contact_samples_m':samples,'bounds_min_m':minimum,'bounds_max_m':maximum,
        'mesh_parts':len(names),'evaluated_faces':faces,'all_vertices_finite':True,'all_parts_parented':True,
        'principal_surface_edges':surface_edges,
        'limits':'This check validates geometry integrity and retained landmarks; visual fidelity is assessed in separate renders.'}
if args.export:
    bpy.ops.object.select_all(action='DESELECT')
    for ob in col.all_objects:
        if ob.type in {'CURVE','FONT','SURFACE'}:ob.select_set(True)
    active=[ob for ob in bpy.context.selected_objects]
    if active:
        bpy.context.view_layer.objects.active=active[0];bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    for ob in col.all_objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=root
    target=Path(args.export).resolve()
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(target));bpy.context.view_layer.update()
    imported=[ob.matrix_world@v.co for ob in bpy.data.objects if ob.type=='MESH' for v in ob.data.vertices]
    lo=[min(v[i]for v in imported)for i in range(3)];hi=[max(v[i]for v in imported)for i in range(3)]
    delta=max(*(abs(lo[i]-minimum[i])for i in range(3)),*(abs(hi[i]-maximum[i])for i in range(3)))
    assert delta<.0001,('glTF bounds changed',delta)
    report['glb_roundtrip_max_bound_error_m']=delta;report['glb_bytes']=target.stat().st_size
Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('INDEPENDENT_GEOMETRY_CHECK_PASSED',json.dumps(report,ensure_ascii=False))
