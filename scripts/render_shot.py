# © 2026 Nikolas Xes. Todos los derechos reservados.
"""
Blockout renderer: cámara + personaje placeholder animados por código, render Eevee.
Uso (headless):
  blender -b --python scripts/render_shot.py -- --out shots/test01_blockout.mp4 --angle 0
  blender -b --python scripts/render_shot.py -- --out shots/test02_blockout.mp4 --angle 120
"""
import bpy
import os
import sys
import argparse
import math

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--angle", type=float, default=0.0, help="offset de ángulo de cámara en grados, para variar el plano")
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    args = p.parse_args(argv)
    # Blender resuelve rutas relativas de forma ambigua sin un .blend guardado
    # (no siempre respeta el cwd del proceso) -> anclar siempre a la carpeta del proyecto.
    if not os.path.isabs(args.out):
        args.out = os.path.join(PROJECT_ROOT, args.out)
    return args


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def build_character_placeholder():
    """Silueta humanoide simple (geometría, sin textura) que sirve de andamio para Seedance."""
    parts = []

    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.1, location=(0, 0, 1.15))
    torso = bpy.context.active_object
    torso.name = "Torso"
    parts.append(torso)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(0, 0, 1.95))
    head = bpy.context.active_object
    head.name = "Head"
    parts.append(head)

    for side, x in (("L", -0.55), ("R", 0.55)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.1, location=(x, 0, 1.2))
        arm = bpy.context.active_object
        arm.name = f"Arm_{side}"
        parts.append(arm)

    for side, x in (("L", -0.2), ("R", 0.2)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=1.1, location=(x, 0, 0.05))
        leg = bpy.context.active_object
        leg.name = f"Leg_{side}"
        parts.append(leg)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    root = bpy.context.active_object
    root.name = "Character"
    for part in parts:
        part.parent = root

    return root


def animate_camera(character, angle_offset_deg, seconds, fps):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = int(seconds * fps)

    bpy.ops.object.camera_add(location=(0, -4, 1.6))
    cam = bpy.context.active_object
    cam.name = "ShotCamera"
    cam.data.lens = 35
    scene.camera = cam

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 1.2))
    pivot = bpy.context.active_object
    pivot.name = "CameraPivot"
    cam.parent = pivot

    constraint = cam.constraints.new(type="TRACK_TO")
    constraint.target = character
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    start_deg = angle_offset_deg
    end_deg = angle_offset_deg + 90
    pivot.rotation_euler = (0, 0, math.radians(start_deg))
    pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=scene.frame_start)
    pivot.rotation_euler = (0, 0, math.radians(end_deg))
    pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=scene.frame_end)

    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

    return cam


def setup_render(out_path, width, height, fps):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.fps = fps
    scene.render.filepath = out_path
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"

    bpy.ops.object.light_add(type="SUN", location=(2, -2, 4))
    bpy.context.active_object.data.energy = 3.0


def main():
    args = parse_args()
    clear_scene()
    character = build_character_placeholder()
    animate_camera(character, args.angle, args.seconds, args.fps)
    setup_render(args.out, args.width, args.height, args.fps)
    bpy.ops.render.render(animation=True)
    print(f"[render_shot] listo -> {args.out}")


if __name__ == "__main__":
    main()
