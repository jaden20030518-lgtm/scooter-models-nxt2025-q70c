"""Geometry regressions for the Q70C seat-edge and mudguard correction."""
import argparse,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

parser=argparse.ArgumentParser()
parser.add_argument('--asset',default=str(Path(__file__).with_name('Ninebot_Q70C_Refined.blend')))
parser.add_argument('--output',default=str(Path(__file__).with_name('seat_fender_validation.json')))
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else[])
bpy.ops.wm.open_mainfile(filepath=str(Path(args.asset).resolve()))
scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
assert not any(o.name.startswith('SaddlePeripheralRubberSeal')for o in scene.objects),'Exterior black seat piping remains'

def geometry(name):
    ev=bpy.data.objects[name].evaluated_get(dg);me=ev.to_mesh()
    points=[ev.matrix_world@v.co for v in me.vertices]
    polygons=[tuple(f.vertices)for f in me.polygons];ev.to_mesh_clear()
    return points,BVHTree.FromPolygons(points,polygons,all_triangles=False)

seat_points,seat_tree=geometry('TaupeSaddle')
pan_points,_=geometry('SaddleBlackStructuralPan')
for axis in [0,1]:
    assert min(v[axis]for v in pan_points)>min(v[axis]for v in seat_points)+.002
    assert max(v[axis]for v in pan_points)<max(v[axis]for v in seat_points)-.002
guard_points,guard_tree=geometry('IvoryRoundedFrontFender')
tyre_points,tyre_tree=geometry('FrontWheel_Tire')
center=sum(tyre_points,Vector())/len(tyre_points)
radius=max(((p.x-center.x)**2+(p.z-center.z)**2)**.5 for p in tyre_points)
front_overhang=max(v.x for v in guard_points)-center.x
assert front_overhang<radius,'Mudguard bill extends too far ahead of the tyre'
top,normal,index,distance=guard_tree.ray_cast(Vector((.525,0,1)),Vector((0,0,-1)))
assert top is not None and normal.z>.7,'Upper painted surface normal faces inward'
assert not guard_tree.overlap(tyre_tree),'Mudguard and tyre intersect'
clearances=[guard_tree.find_nearest(p)[3]for p in tyre_points[::16]]
minimum_clearance=min(clearances)
assert minimum_clearance>.003,'Insufficient static tyre clearance'
support=[]
for side in [-1,1]:
    p,n,idx,d=guard_tree.ray_cast(Vector((.473,side*.5,.321)),Vector((0,-side,0)))
    assert p is not None,'Reflector has no painted side skirt behind it'
    support.append({'side':side,'surface_xyz_m':list(p)})
report={'asset':Path(args.asset).name,'exterior_black_piping_absent':True,
        'black_structural_pan_inside_upholstery_bounds':True,
        'fender_outward_top_normal':list(normal),
        'fender_front_overhang_in_tyre_radii':front_overhang/radius,
        'fender_tyre_triangle_overlap_count':0,
        'minimum_sampled_tyre_clearance_m':minimum_clearance,
        'painted_side_skirt_at_reflectors':support,
        'checks_pass':True,
        'scope':'Static model regressions and image-derived shape constraints; not a factory measurement or suspension-travel certification.'}
Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Q70_SEAT_FENDER_CHECKS_PASS',json.dumps(report))
