"""Matched baseline/refined previews; 1200 px, 24 samples, <=3 CPU threads.
Run Blender --background --threads 3 --python render_previews.py -- [--baseline]
"""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path(__file__).resolve().parent
baseline='--baseline' in sys.argv
SRC=OUT.parent/'Production_NIU/NIU_NXT_2025_Production.blend' if baseline else OUT/'NIU_NXT_2025_Refined.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene
for ob in list(scene.objects):
    if ob.type in {'LIGHT','CAMERA'} or ob.name.startswith('NXT studio ground'):bpy.data.objects.remove(ob,do_unlink=True)
studio=bpy.data.collections.new('NXT matched preview studio');scene.collection.children.link(studio)
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def area(n,pos,power,size,size_y,color):
    d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='RECTANGLE';d.size=size;d.size_y=size_y;d.color=color
    ob=bpy.data.objects.new(n,d);studio.objects.link(ob);ob.location=pos;aim(ob,(0,0,.6))
area('NXT silk key',(1.7,2.6,4.2),500,3.8,2.8,(1,.97,.92))
area('NXT rear edge strip',(-1.8,-1.8,2.1),420,3.0,.7,(.89,.94,1))
area('NXT glass reflection',(2.6,-1.3,2.8),260,1.4,2.6,(1,1,1))
area('NXT side fill',(-.6,2.8,1.5),95,2.5,1.8,(1,1,1))
world=bpy.data.worlds.new('NXT preview neutral ambient');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.3,.32,.35,1);bg.inputs[1].default_value=.25;scene.world=world
m=bpy.data.materials.new('NXT studio warm grey');m.use_nodes=True
bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.35,.34,.325,1);bs.inputs['Roughness'].default_value=.82
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001));ground=bpy.context.object;ground.name='NXT studio ground';ground.data.materials.append(m)
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
poses={
 'hero':((3.0,3.7,1.72),(-.03,0,.615),68,None),
 'optics':((1.48,1.08,1.26),(.43,0,.80),85,None),
 'side':((0,4,.655),(0,0,.655),70,2.24),
 'cockpit':((-.68,1.28,1.69),(.16,0,.87),75,None),
 'bucket':((.27,1.38,1.63),(-.29,0,.565),75,None),
}
cameras={}
for name,(pos,target,lens,ortho) in poses.items():
    d=bpy.data.cameras.new('NXT '+name);d.lens=lens;d.clip_start=.005;d.clip_end=300
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    ob=bpy.data.objects.new('NXT '+name,d);studio.objects.link(ob);ob.location=pos;aim(ob,target);cameras[name]=ob
scene.camera=cameras['hero'];scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=10;scene.cycles.glossy_bounces=6
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
scene.render.threads_mode='FIXED';scene.render.threads=3
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.5
scene.render.film_transparent=False;scene.view_layers[0].material_override=None
scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
if not baseline:bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'NIU_NXT_2025_Refined.blend'))
views=['hero','optics','side'] if baseline else list(poses)
if '--views' in sys.argv:views=sys.argv[sys.argv.index('--views')+1].split(',')
for name in views:
    saved={}
    if name=='bucket' and not baseline:
        pivot=Vector((-.133,0,.646));transform=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(70),4,'Y')@Matrix.Translation(-pivot)
        for ob in bpy.data.objects:
            if ob.name.startswith(('Reference shaped saddle','Saddle edge piping','Individual saddle stitch','NXT short saddle rigid underside')):
                saved[ob]=ob.matrix_world.copy();ob.matrix_world=transform@ob.matrix_world
    scene.camera=cameras[name];prefix='baseline' if baseline else 'refined'
    scene.render.filepath=str(OUT/f'NIU_{prefix}_{name}_1200.png');bpy.ops.render.render(write_still=True)
    for ob,matrix in saved.items():ob.matrix_world=matrix
scene.camera=cameras['hero']
print('MATCHED_PREVIEWS_COMPLETE',prefix,views)
