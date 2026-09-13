"""Validate physical scale, hierarchy and native hinged-seat accessibility without changing the scene."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'Ninebot_Q70C_Refined.blend'))
sc=bpy.context.scene;col=bpy.data.collections['NINEBOT_Q70C'];root=bpy.data.objects['Q70C_ROOT']
sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
seat=bpy.data.objects['TaupeSaddle'];ev=seat.evaluated_get(dg);inv=ev.matrix_world.inverted()
hit,p,n,idx=ev.ray_cast(inv@Vector((-.355,0,2)),inv.to_3x3()@Vector((0,0,-1)))
assert hit
height=(ev.matrix_world@p).z
front=bpy.data.objects['FrontWheel_Tire'];rear=bpy.data.objects['RearWheel_Tire']
fx=sum((front.matrix_world@v.co).x for v in front.data.vertices)/len(front.data.vertices)
rx=sum((rear.matrix_world@v.co).x for v in rear.data.vertices)/len(rear.data.vertices)
wb=fx-rx
assert abs(wb-1.110)<1e-5 and abs(height-.730)<1e-5
# A center vertical ray must meet upholstery when closed and the bucket bottom when open.
pose_checks=[]
for frame in [1,45]:
 sc.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 hit,p,n,idx,obj,mat=sc.ray_cast(dg,Vector((-.40,0,1.65)),Vector((0,0,-1)))
 assert hit
 pose_checks.append({'frame':frame,'first_hit':obj.name,'height_m':p.z})
 if frame==1:assert obj.name=='TaupeSaddle',obj.name
 else:assert obj.name=='IndependentDeepSeatBucket' and p.z<.50,(obj.name,p.z)
sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
vs=[];parts=0
for o in col.all_objects:
 if o.type not in {'MESH','CURVE','FONT'}:continue
 a=o.parent
 while a and a!=root:a=a.parent
 assert a==root,o.name
 e=o.evaluated_get(dg);me=e.to_mesh();vs.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear();parts+=1
assert all(math.isfinite(v) for p in vs for v in p)
bounds=[max(v[i] for v in vs)-min(v[i] for v in vs) for i in range(3)]
report={'wheelbase_m':wb,'seat_contact_height_m':height,'root_hierarchy_verified':True,'all_finite_vertices':True,'geometric_parts':parts,'closed_bounds_m':bounds,'pose_raycast_checks':pose_checks,'limits':'Reconstructed visual model, not measured factory CAD. Ray checks prove two reference poses, not full collision certification.'}
(base/'native_refined_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('Q70_REFINED_NATIVE_PASS',json.dumps(report))
