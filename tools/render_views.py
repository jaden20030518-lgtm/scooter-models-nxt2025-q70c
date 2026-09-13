"""Render the same neutral photographic setup for baseline and refined assets."""
import argparse, json, sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser()
p.add_argument('--asset',required=True);p.add_argument('--kind',choices=['niu','q70'],required=True)
p.add_argument('--out',required=True);p.add_argument('--views',default='hero,side,rear,detail')
p.add_argument('--resolution',type=int,default=1600);p.add_argument('--samples',type=int,default=48)
p.add_argument('--frame',type=int,default=1);p.add_argument('--studio-out');p.add_argument('--clay',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.asset).resolve()))
scene=bpy.context.scene;scene.frame_set(a.frame)
col=bpy.data.collections['NIU_NXT_ULTRA_2025' if a.kind=='niu' else 'NINEBOT_Q70C']
objects=set(col.all_objects)
for ob in list(scene.objects):
    if ob not in objects:bpy.data.objects.remove(ob,do_unlink=True)
studio=bpy.data.collections.new('REFERENCE_REFINEMENT_STUDIO');scene.collection.children.link(studio)
def aim(ob,pt):ob.rotation_euler=(Vector(pt)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,pos,energy,sx,sy,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='RECTANGLE';data.size=sx;data.size_y=sy;data.color=color
    ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=pos;aim(ob,(0,0,.65))
area('Large silk key',(1.7,2.6,4.2),500,3.8,2.8,(1,.97,.92))
area('Long edge strip',(-1.8,-1.8,2.1),420,3,.7,(.89,.94,1))
area('Front glazing reflection',(2.6,-1.3,2.8),260,1.4,2.6,(1,1,1))
area('Low side fill',(-.6,2.8,1.5),95,2.5,1.8,(1,1,1))
world=bpy.data.worlds.new('Neutral refinement ambient');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs[0].default_value=(.3,.32,.35,1)
bg.inputs[1].default_value=.25;scene.world=world
m=bpy.data.materials.new('Neutral warm grey sweep');m.use_nodes=True
bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.48,.47,.45,1);bs.inputs['Roughness'].default_value=.82
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.002))
ground=bpy.context.object;ground.name='Studio floor'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground);ground.data.materials.append(m)
if a.kind=='niu':
    poses={'hero':((3,3.7,1.85),(-.03,0,.65),76,None),
           'side':((0,6,.65),(0,0,.65),None,2.12),
           'rear':((-2.8,3.5,1.9),(-.05,0,.65),76,None),
           'detail':((1.48,1.08,1.28),(.43,0,.82),85,None),
           'seat':((.65,1.5,1.65),(-.28,0,.65),80,None)}
else:
    poses={'hero':((4.8,4.5,1.55),(0,0,.64),None,1.93),
           'side':((0,6,.63),(0,0,.63),None,1.86),
           'rear':((-3,3.5,1.75),(-.1,0,.64),None,1.92),
           'detail':((2.6,2.8,1.75),(.29,0,.98),None,.90),
           'seat':((-.8,2.2,1.65),(-.36,0,.76),None,1.30)}
cameras={}
for name,(pos,target,lens,scale) in poses.items():
    data=bpy.data.cameras.new('Refinement '+name);data.clip_start=.005;data.clip_end=300
    if scale:data.type='ORTHO';data.ortho_scale=scale
    else:data.type='PERSP';data.lens=lens
    ob=bpy.data.objects.new('Refinement '+name,data);studio.objects.link(ob);ob.location=pos;aim(ob,target);cameras[name]=ob
scene.render.engine='CYCLES';scene.cycles.samples=a.samples;scene.cycles.use_denoising=True
scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.025
scene.cycles.max_bounces=12;scene.cycles.transmission_bounces=10;scene.cycles.glossy_bounces=8
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
    for device in pref.devices:device.use=device.type=='METAL'
    scene.cycles.device='GPU' if any(d.type=='METAL'for d in pref.devices)else'CPU'
except Exception:scene.cycles.device='CPU'
scene.render.threads_mode='FIXED';scene.render.threads=3
scene.render.film_transparent=False;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.4
scene.view_layers[0].material_override=None
if a.clay:
    cm=bpy.data.materials.new('Geometry-only neutral clay');cm.use_nodes=True
    b=next(n for n in cm.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(.33,.35,.37,1);b.inputs['Roughness'].default_value=.58
    scene.view_layers[0].material_override=cm
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.resolution_x=a.resolution;scene.render.resolution_y=round(a.resolution*.75)
scene.camera=cameras['hero']
if a.studio_out:bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.studio_out).resolve()))
for view in a.views.split(','):
    scene.camera=cameras[view]
    scene.render.filepath=str(out/f'{a.kind}_{view}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER_FINISHED',view,scene.render.filepath,flush=True)
(out/'render_settings.json').write_text(json.dumps({'asset':str(Path(a.asset).resolve()),'frame':a.frame,'views':a.views.split(','),'width':a.resolution,'height':round(a.resolution*.75),'samples':a.samples,'device':scene.cycles.device,'poses':poses,'clay':a.clay},indent=2))
