"""Geometric delivery checks run against the saved .blend, not source strings."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'NIU_NXT_2025_Refined.blend'))
scene=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
root=bpy.data.objects['NIU_ROOT'];vehicle=bpy.data.collections['NIU_NXT_ULTRA_2025']
front=bpy.data.objects['Front axle'].matrix_world.translation
rear=bpy.data.objects['Rear axle'].matrix_world.translation
wb=abs(front.x-rear.x)
result={'wheelbase_measured_from_axle_objects_m':wb,'wheelbase_baseline_m':1.2445622895622896,
 'units':scene.unit_settings.system,'axis_front':'+X','vehicle_objects':len(vehicle.all_objects),
 'three_optics':[o.name for o in vehicle.all_objects if o.name.startswith('NXT main optical lens ')],
 'obsolete_single_projector_present':any(o.name.startswith('Single convex projector lens') for o in vehicle.all_objects),
 'temporary_cutters':[o.name for o in vehicle.all_objects if o.name.startswith(('Temp','Temporary'))],
 'nonfinite_mesh_vertices':0,'footwell_passage_rays':[], 'geometry_notes':[]}
mesh_verts=0;mesh_faces=0
for ob in vehicle.all_objects:
    if ob.type=='MESH':
        mesh_verts+=len(ob.data.vertices);mesh_faces+=len(ob.data.polygons)
        for v in ob.data.vertices:
            if not all(math.isfinite(x) for x in v.co):result['nonfinite_mesh_vertices']+=1
result['mesh_base_vertices']=mesh_verts;result['mesh_base_faces']=mesh_faces
# A formerly open side return was visible at this matched optics-camera pixel.
camera=bpy.data.objects.get('NXT optics')
result['apron_seam_pixel_ray']=None
if camera:
    frame=camera.data.view_frame(scene=scene)
    u=(1014.5/1200);v=1-(299.5/900)
    q=Vector((min(p.x for p in frame)+(max(p.x for p in frame)-min(p.x for p in frame))*u,
              min(p.y for p in frame)+(max(p.y for p in frame)-min(p.y for p in frame))*v,frame[0].z))
    direction=camera.matrix_world.to_3x3()@q.normalized()
    hit,p,n,idx,ob,m=scene.ray_cast(dg,camera.matrix_world.translation,direction,distance=100)
    result['apron_seam_pixel_ray']={'pixel':[1014,299],'hit_object':ob.name if hit else None,
       'sealed':bool(hit and ob.name!='NXT studio ground')}
# These samples fall in the open foot passage, clear of apron, pedestal and floor.
for x in [-.025,.04,.115]:
    for z in [.43,.53]:
        hit,p,n,idx,ob,m=scene.ray_cast(dg,Vector((x,2,z)),Vector((0,-1,0)),distance=4)
        result['footwell_passage_rays'].append({'x':x,'z':z,'clear':not hit,'hit_object':ob.name if hit else None})
for name in ['NXT independent short-seat storage bucket','NXT removable smoked front window','NXT three-optic horizontal carrier',
 'NXT front open-window brake rotor','NXT front independent ABS encoder','NXT short-seat front hinge leaf']:
    ob=bpy.data.objects.get(name)
    result['geometry_notes'].append({'part':name,'present':ob is not None})
result['checks_pass']=(abs(wb-result['wheelbase_baseline_m'])<1e-7 and len(result['three_optics'])==3
 and not result['obsolete_single_projector_present'] and not result['temporary_cutters']
 and not result['nonfinite_mesh_vertices'] and all(r['clear'] for r in result['footwell_passage_rays'])
 and all(r['present'] for r in result['geometry_notes'])
 and (result['apron_seam_pixel_ray'] is None or result['apron_seam_pixel_ray']['sealed']))
(OUT/'NIU_refined_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
if not result['checks_pass']:raise RuntimeError('Saved refined geometry failed a delivery check')
