"""Convex sections, solid Boolean operations and millimetre STL export."""
import struct

import bmesh
import bpy
from mathutils import Vector


def chamfered_rectangle(bounds, chamfer):
    left, right, front, rear = bounds
    return [(left + chamfer, front), (right - chamfer, front),
            (right, front + chamfer), (right, rear - chamfer),
            (right - chamfer, rear), (left + chamfer, rear),
            (left, rear - chamfer), (left, front + chamfer)]


def loft(name, sections, axis="Z"):
    vertices = []
    for coordinate, profile in sections:
        vertices.extend((u, v, coordinate) if axis == "Z" else (u, coordinate, v)
                        for u, v in profile)
    count = len(sections[0][1])
    faces = [tuple(reversed(range(count)))]
    for first in range(0, len(vertices) - count, count):
        for index in range(count):
            a, b = first + index, first + (index + 1) % count
            faces.append((a, b, b + count, a + count))
    faces.append(tuple(range(len(vertices) - count, len(vertices))))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    with_bmesh = bmesh.new()
    with_bmesh.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(with_bmesh, faces=list(with_bmesh.faces))
    with_bmesh.to_mesh(mesh)
    with_bmesh.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def box(name, low, high):
    profile = [(low[0], low[1]), (high[0], low[1]),
               (high[0], high[1]), (low[0], high[1])]
    return loft(name, [(low[2], profile), (high[2], profile)])


def boolean(target, tool, operation):
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new(operation, "BOOLEAN")
    modifier.solver = "EXACT"
    modifier.operation = operation
    modifier.object = tool
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    mesh = tool.data
    bpy.data.objects.remove(tool, do_unlink=True)
    bpy.data.meshes.remove(mesh)


def write_stl(obj, path):
    mesh = obj.data
    mesh.calc_loop_triangles()
    with path.open("wb") as output:
        output.write(obj.name.encode("ascii").ljust(80, b"\0"))
        output.write(struct.pack("<I", len(mesh.loop_triangles)))
        for triangle in mesh.loop_triangles:
            a, b, c = (obj.matrix_world @ mesh.vertices[index].co for index in triangle.vertices)
            normal = Vector(b - a).cross(c - a).normalized()
            output.write(struct.pack("<12fH", *normal, *a, *b, *c, 0))
