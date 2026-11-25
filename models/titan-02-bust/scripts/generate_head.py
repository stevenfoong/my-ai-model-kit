"""Generate Titan 02 V0.1 in Blender. See the model README for CLI usage."""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
MODEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODEL.parents[1] / "shared" / "scripts" / "blender"))
from kit_mesh import boolean, box, chamfered_rectangle, loft, write_stl


def inset(bounds, delta):
    left, right, front, rear = bounds
    return left + delta, right - delta, front + delta, rear - delta


def profile(bounds, chamfer):
    return chamfered_rectangle(bounds, chamfer)


def beveled_section(name, spec):
    bottom, top = spec["z"]
    bounds, chamfer, bevel = spec["bounds"], spec["chamfer"], spec["bevel"]
    narrow = profile(inset(bounds, bevel), chamfer)
    wide = profile(bounds, chamfer)
    return loft(name, [(bottom, narrow), (bottom + bevel, wide),
                       (top - bevel, wide), (top, narrow)])


def joint_box(part, joint, axis, start, end, clearance, operation):
    u, v, width, height = joint
    u0, u1 = u - width / 2 - clearance, u + width / 2 + clearance
    v0, v1 = v - height / 2 - clearance, v + height / 2 + clearance
    low, high = ((u0, v0, start), (u1, v1, end)) if axis == "Z" else (
        (u0, start, v0), (u1, end, v1))
    boolean(part, box("Joint tool", low, high), operation)


def generate(config):
    frame_spec, helmet_spec, mask_spec = (
        config["frame"], config["helmet"], config["mask"])
    joints, envelope = config["joint"], config["prototype"]
    side, end, fuse = (joints[key] for key in ("side_clearance", "end_clearance", "fuse_overlap"))
    frame_front = frame_spec["base"]["bounds"][2]
    crown_top = frame_spec["crown"]["z"][1]
    helmet_tip, mask_tip = frame_spec["helmet_tab_tip_z"], mask_spec["tip_y"]

    frame = beveled_section("H001 Inner head frame", frame_spec["base"])
    boolean(frame, beveled_section("Crown", frame_spec["crown"]), "UNION")
    for joint in frame_spec["helmet_tabs"]:
        joint_box(frame, joint, "Z", crown_top - fuse, helmet_tip, 0, "UNION")
    for joint in frame_spec["mask_sockets"]:
        joint_box(frame, joint, "Y", frame_front - fuse, mask_tip + end, side, "DIFFERENCE")

    half_width = envelope["width"] / 2
    max_z = envelope["height"]
    helmet_bounds = (-half_width, half_width, helmet_spec["front_y"], envelope["depth"] / 2)
    bottom, chamfer, bevel, ceiling = (
        helmet_spec[key] for key in ("bottom_z", "chamfer", "bevel", "ceiling_z"))
    full = profile(helmet_bounds, chamfer)
    helmet = loft("H002 Helmet shell", [(bottom, full), (max_z - bevel, full),
                                       (max_z, profile(inset(helmet_bounds, bevel), chamfer))])
    cavity = profile(inset(helmet_bounds, helmet_spec["wall"]), chamfer)
    boolean(helmet, loft("Helmet cavity", [(bottom - fuse, cavity), (ceiling, cavity)]),
            "DIFFERENCE")
    for joint in frame_spec["helmet_tabs"]:
        joint_box(helmet, joint, "Z", ceiling - fuse, helmet_tip + end, side, "DIFFERENCE")

    outline = mask_spec["profile"]
    center_z = sum(z for _, z in outline) / len(outline)
    inset_scale = 0.88
    front = [(x * inset_scale, center_z + (z - center_z) * inset_scale) for x, z in outline]
    front_y = helmet_bounds[3] - envelope["depth"]
    rear = mask_spec["rear_y"]
    mask = loft("H003 Face mask", [(front_y, front), (front_y + mask_spec["bevel"], outline),
                                  (rear, outline)], axis="Y")
    for joint in frame_spec["mask_sockets"]:
        joint_box(mask, joint, "Y", rear - fuse, mask_tip, 0, "UNION")
    return frame, helmet, mask


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene(parts, output):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    for part, (color, metallic) in zip(parts, [
        ((0.19, 0.25, 0.29, 1), 0.42), ((0.045, 0.14, 0.23, 1), 0.36),
        ((0.67, 0.29, 0.07, 1), 0.4),
    ]):
        material = bpy.data.materials.new(part.name)
        material.diffuse_color = color
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        surface = nodes.new("ShaderNodeOutputMaterial")
        material.node_tree.links.new(shader.outputs["BSDF"], surface.inputs["Surface"])
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Roughness"].default_value = 0.35
        part.data.materials.clear()
        part.data.materials.append(material)
        for face in part.data.polygons:
            face.material_index = 0

    rig = bpy.data.collections.new("Preview rig")
    scene.collection.children.link(rig)
    camera = bpy.data.objects.new("Orthographic camera", bpy.data.cameras.new("Orthographic"))
    rig.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 106
    camera.data.clip_end = 1000
    camera.location = (115, -176, 113)
    aim(camera, (0, 0, 30))
    scene.camera = camera

    for name, location, watts, size in [
        ("Key", (35, -85, 125), 26000, 85),
        ("Fill", (-95, -50, 50), 15000, 105),
        ("Rim", (35, 65, 140), 32000, 70),
    ]:
        light = bpy.data.lights.new(name, "AREA")
        light.energy = watts
        light.shape = "DISK"
        light.size = size
        lamp = bpy.data.objects.new(name, light)
        rig.objects.link(lamp)
        lamp.location = location
        aim(lamp, (0, 0, 35))

    scene.world = bpy.data.worlds.new("Studio world")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.15, 0.19, 0.24, 1)
    background.inputs["Strength"].default_value = 0.55
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = "//../exports/preview-renders/assembled.png"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "blender" / "titan-02-head-v0.1.blend"))

    preview = output / "exports" / "preview-renders"
    scene.render.filepath = str(preview / "assembled.png")
    bpy.ops.render.render(write_still=True)
    parts[1].location.z += 43
    parts[2].location.y -= 38
    camera.data.ortho_scale = 147
    aim(camera, (0, -10, 49))
    scene.render.filepath = str(preview / "exploded.png")
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=MODEL / "specifications" / "dimensions.json")
    parser.add_argument("--output", type=Path, default=MODEL)
    parser.add_argument("--stl-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    output = args.output.resolve()
    for directory in ("exports/stl", "exports/preview-renders", "blender"):
        (output / directory).mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts = generate(config)
    bpy.context.view_layer.update()
    for part in parts:
        write_stl(part, output / "exports" / "stl" / (part.name.split()[0] + ".stl"))
    if not args.stl_only:
        setup_scene(parts, output)


if __name__ == "__main__":
    main()
