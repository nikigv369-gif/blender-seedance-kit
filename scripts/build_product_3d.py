# -*- coding: utf-8 -*-
# (c) 2026 Nikolas Xes. Todos los derechos reservados.
#
# Construye un producto tapizado en 3D REAL (geometria modelada por codigo, no
# cajas con fotos pegadas como los GLB de los servicios "foto a 3D") y lo viste
# con la tela sacada de la foto real. Renderiza el giro 360 para el hook visual
# o como andamio de movimiento para Seedance.
#
#   blender -b -P scripts/build_product_3d.py -- --tela ruta/tela.png --out DIR
#           --name v1 [--frames 150] [--w 1080] [--h 1920] [--still 1] [--alpha 1]
#
# La tela se saca con scripts/fabric_swatch.py. Ver docs/05-BLENDER.md.

import sys
import os
import math

import bpy
from mathutils import Vector


def get_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    args = {}
    i = 0
    while i < len(argv):
        args[argv[i].lstrip("-")] = argv[i + 1] if i + 1 < len(argv) else ""
        i += 2
    return args


def block(name, x0, x1, y0, y1, z0, z1, bevel=0.11):
    """Cojin redondeado (bevel grueso + subsurf, ya aplicados). El volumen
    mullido nace ACA; el remesh posterior solo suelda los cojines entre si."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    b = o.modifiers.new("bevel", "BEVEL")
    b.width = bevel
    b.segments = 6
    b.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=b.name)

    s = o.modifiers.new("subsurf", "SUBSURF")
    s.levels = 2
    bpy.ops.object.modifier_apply(modifier=s.name)
    return o


def fuse(parts, voxel=0.013, smooth_repeat=26):
    """Une las cajas en un solo cuerpo: remesh volumetrico (union real de
    volumenes) + suavizado = tapiceria mullida sin aristas ni juntas."""
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = "Sillon"

    r = o.modifiers.new("remesh", "REMESH")
    r.mode = "VOXEL"
    r.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier=r.name)

    # suavizado corto: solo funde la juntura. La redondez ya viene de los
    # bevels; pasarse de iteraciones aplasta el sillon en un bloque de espuma.
    s = o.modifiers.new("smooth", "SMOOTH")
    s.factor = 1.0
    s.iterations = smooth_repeat
    bpy.ops.object.modifier_apply(modifier=s.name)

    bpy.ops.object.shade_smooth()
    return o


def fabric_material(name, tela_path, scale=2.6, blend=0.5):
    """Tela real de la foto, proyeccion BOX (sin UV unwrap) + relieve sutil."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.92
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 0.18
    except KeyError:
        bsdf.inputs["Specular"].default_value = 0.18

    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(tela_path)
    tex.projection = "BOX"
    # compromiso: bajo = costura visible en caras planas; alto = la tela se
    # chorrea en las caras inclinadas (hueco del asiento, cara interna del brazo)
    tex.projection_blend = blend
    tex.extension = "REPEAT"

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    coord = nt.nodes.new("ShaderNodeTexCoord")

    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    # relieve: la textura tambien manda el bump (hilos/chenille)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.28
    nt.links.new(tex.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def build_chair(tela_path, tex_scale=1.4, voxel=0.013, smooth_repeat=26, blend=0.5):
    """Sillon de nino tal como es el real: UN SOLO cuerpo tapizado que apoya
    directo en el piso — sin zocalo ni patas. Los bloques se solapan y el
    remesh los funde: asiento, brazos y respaldo son la misma masa."""
    parts = [
        # masa principal: del piso hasta el asiento (sin base ni patas)
        block("cuerpo", -0.54, 0.54, -0.48, 0.50, 0.00, 0.58),
        # asiento: apenas sobre el cuerpo, para que el hueco entre brazos se lea
        block("asiento", -0.36, 0.36, -0.42, 0.26, 0.50, 0.62),
        # respaldo alto
        block("respaldo", -0.52, 0.52, 0.26, 0.50, 0.40, 1.18),
        # rollo superior del respaldo
        block("corona", -0.54, 0.54, 0.20, 0.54, 1.02, 1.30),
        # brazos rollizos y ALTOS: definen el hueco del asiento
        block("brazo_izq", -0.60, -0.34, -0.46, 0.32, 0.42, 1.00),
        block("brazo_der", 0.34, 0.60, -0.46, 0.32, 0.42, 1.00),
    ]

    o = fuse(parts, voxel=voxel, smooth_repeat=smooth_repeat)
    o.data.materials.append(fabric_material("tela", tela_path, scale=tex_scale,
                                            blend=blend))

    root = bpy.data.objects.new("Sillon_Root", None)
    bpy.context.scene.collection.objects.link(root)
    o.parent = root
    return root, [o]


def setup_studio(size):
    scene = bpy.context.scene
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("W")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.55, 0.47, 1.0)
    bg.inputs[1].default_value = 0.9

    bpy.ops.mesh.primitive_plane_add(size=size * 16, location=(0, 0, 0))
    floor = bpy.context.active_object
    m = bpy.data.materials.new("piso")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.55, 0.48, 0.41, 1.0)
    b.inputs["Roughness"].default_value = 0.62
    floor.data.materials.append(m)

    bpy.ops.mesh.primitive_plane_add(size=size * 16, location=(0, size * 3.4, size * 3),
                                     rotation=(math.radians(90), 0, 0))
    wall = bpy.context.active_object
    mw = bpy.data.materials.new("pared")
    mw.use_nodes = True
    bw = mw.node_tree.nodes["Principled BSDF"]
    bw.inputs["Base Color"].default_value = (0.63, 0.56, 0.48, 1.0)
    bw.inputs["Roughness"].default_value = 0.85
    wall.data.materials.append(mw)


def add_lights(center, size, gain=1.0):
    def area(name, loc, energy, sz):
        energy *= gain
        d = bpy.data.lights.new(name, type="AREA")
        d.energy = energy
        d.size = sz
        d.color = (1.0, 0.96, 0.90)
        o = bpy.data.objects.new(name, d)
        o.location = loc
        bpy.context.scene.collection.objects.link(o)
        return o

    d = size * 2.2
    h = center.z + size * 1.1
    key = area("key", (center.x - d * 0.7, center.y - d * 0.8, h), 900 * size * size, size * 2.4)
    fill = area("fill", (center.x + d * 0.9, center.y - d * 0.6, center.z + size * 0.5),
                260 * size * size, size * 2.8)
    rim = area("rim", (center.x + d * 0.2, center.y + d * 1.0, h * 1.1),
               560 * size * size, size * 1.6)

    tgt = bpy.data.objects.new("light_target", None)
    tgt.location = center
    bpy.context.scene.collection.objects.link(tgt)
    for o in (key, fill, rim):
        c = o.constraints.new("TRACK_TO")
        c.target = tgt
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"


def add_camera(center, azimuth_deg, elevation_deg, dist):
    cd = bpy.data.cameras.new("cam")
    cd.lens = 50.0
    cd.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    cam.location = (
        center.x + dist * math.cos(el) * math.sin(az),
        center.y - dist * math.cos(el) * math.cos(az),
        center.z + dist * math.sin(el),
    )
    tgt = bpy.data.objects.new("cam_target", None)
    tgt.location = center
    bpy.context.scene.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


def main():
    a = get_args()
    # ruta de la textura: absoluta, o relativa al cwd desde donde se invoca
    tela = os.path.abspath(a["tela"])
    if not os.path.exists(tela):
        raise SystemExit("No existe la textura: %s" % tela)
    out = a["out"]
    name = a["name"]
    frames = int(a.get("frames", 150))
    W, H = int(a.get("w", 1080)), int(a.get("h", 1920))
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    root, parts = build_chair(tela, tex_scale=float(a.get("scale", 1.4)),
                              voxel=float(a.get("voxel", 0.008)),
                              smooth_repeat=int(a.get("smooth", 3)),
                              blend=float(a.get("blend", 0.5)))

    center = Vector((0.0, 0.0, 0.62))
    size = 1.30
    if a.get("alpha") == "1":
        # sin piso ni pared: PNG con alfa para flotar sobre otro material
        scene0 = bpy.context.scene
        scene0.render.film_transparent = True
        w = bpy.data.worlds.new("Wa")
        scene0.world = w
        w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 0.97, 0.94, 1.0)
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
    else:
        setup_studio(size)
    add_lights(center, size, gain=float(a.get("light", 0.30)))
    dist = (size / 2.0) / math.tan(math.radians(19.5)) * 1.30
    add_camera(center, 0, 9, dist)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if a.get("alpha") == "1" else "RGB"
    scene.eevee.taa_render_samples = 48
    for vt in ("Khronos PBR Neutral", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = vt
            break
        except TypeError:
            continue

    if a.get("still") == "1":
        scene.render.filepath = os.path.join(out, name)
        bpy.ops.render.render(write_still=True)
        return

    scene.frame_start = 1
    scene.frame_end = frames
    root.rotation_mode = "XYZ"
    root.rotation_euler.z = 0
    root.keyframe_insert("rotation_euler", index=2, frame=1)
    root.rotation_euler.z = math.pi * 2
    root.keyframe_insert("rotation_euler", index=2, frame=frames + 1)
    for fc in root.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

    scene.render.filepath = os.path.join(out, "%s_" % name)
    bpy.ops.render.render(animation=True)


main()
