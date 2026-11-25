"""Independent numeric checks on the exported Titan 02 STL files."""
import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

MODEL = Path(__file__).resolve().parents[1]
IDS = ("H001", "H002", "H003")
EPS = 0.00001
MAX_OVERLAP = 0.001


def checked(solid):
    if solid.status() != mf.Error.NoError:
        raise ValueError(f"Manifold operation failed with {solid.status()}")
    return solid


def swept(mesh, solid, delta):
    # A point entering the translating solid crosses a swept boundary face.
    # The initial solid plus each triangle's extrusion therefore covers the full path.
    prisms = [checked(mf.Manifold.hull_points(np.concatenate((tri, tri + delta))))
              for tri in mesh.triangles]
    return checked(mf.Manifold.batch_boolean([solid, *prisms], mf.OpType.Add))


def crossings(mesh, origin, direction):
    """Signed intersections with an infinite line, merging shared-edge hits."""
    triangles = mesh.triangles
    a = triangles[:, 0]
    u, v = triangles[:, 1] - a, triangles[:, 2] - a
    perpendicular = np.cross(direction, v)
    det = np.einsum("ij,ij->i", u, perpendicular)
    good = abs(det) > EPS
    offset = np.asarray(origin) - a[good]
    p = perpendicular[good]
    cross = np.cross(offset, u[good])
    bary_u = np.einsum("ij,ij->i", offset, p) / det[good]
    bary_v = (cross @ direction) / det[good]
    distance = np.einsum("ij,ij->i", v[good], cross) / det[good]
    inside = (bary_u >= -EPS) & (bary_v >= -EPS) & (bary_u + bary_v <= 1 + EPS)
    return np.unique(np.round(distance[inside], 5))


def gap(mesh, origin, direction):
    hits = crossings(mesh, origin, direction)
    return np.array([hits[hits < 0][-1], hits[hits > 0][0]])


def joint_measurements(meshes, config):
    frame, helmet, mask = meshes
    spec = config["frame"]
    crown_top = spec["crown"]["z"][1]
    helmet_tip = spec["helmet_tab_tip_z"]
    mask_rear, mask_tip = (config["mask"][key] for key in ("rear_y", "tip_y"))
    helmet_z = (crown_top + helmet_tip) / 2
    mask_y = (mask_rear + mask_tip) / 2
    results = []
    for name, male, female, rows, origin, axes, insertion, reach in (
        ("Helmet", frame, helmet, spec["helmet_tabs"],
         lambda x, y: (x, y, helmet_z), ((1, 0, 0), (0, 1, 0)), (0, 0, 1), helmet_tip - helmet_z),
        ("Mask", mask, frame, spec["mask_sockets"],
         lambda x, z: (x, mask_y, z), ((1, 0, 0), (0, 0, 1)), (0, 1, 0), mask_tip - mask_y),
    ):
        for x, v, width, height in rows:
            point = origin(x, v)
            signed = []
            for direction, size in zip(axes, (width, height)):
                tab = gap(male, point, direction)
                socket = gap(female, point, direction)
                if not np.allclose(tab, [-size / 2, size / 2], atol=EPS, rtol=0):
                    raise ValueError(f"{name} tab does not match specification at X={x}")
                signed.extend((tab[0] - socket[0], socket[1] - tab[1]))
            axial_hits = crossings(female, point, insertion)
            tip_clearance = axial_hits[axial_hits > 0][0] - reach
            results.append((name, x, signed, tip_clearance))
    return results


def walls(meshes, config):
    frame, shell, mask = meshes
    fs, hs, ms, envelope = (config[key] for key in ("frame", "helmet", "mask", "prototype"))
    half_width, rear = envelope["width"] / 2, envelope["depth"] / 2
    z = (hs["bottom_z"] + hs["ceiling_z"]) / 2
    c, front = hs["chamfer"], hs["front_y"]
    center_y = (rear + front) / 2
    samples = []
    for sign in (-1, 1):
        samples.append(((0, center_y, z), (0, sign, 0)))
        samples.append(((0, center_y, z), (sign, 0, 0)))
        for y, ysign in ((front + c / 2, -1), (rear - c / 2, 1)):
            normal = np.array([sign, ysign, 0]) / np.sqrt(2)
            point = np.array([sign * (half_width - c / 2), y, z]) - normal * hs["wall"] * 2
            samples.append((point, normal))

    def positive_hits(mesh, origin, axis):
        distances = crossings(mesh, origin, axis)
        return distances[distances > 0]

    shell_walls = [np.diff(positive_hits(shell, point, normal)[:2])[0]
                   for point, normal in samples]
    caps = [np.diff(positive_hits(shell, (x, y, envelope["height"] + 1), (0, 0, -1))[:2])[0]
            for x, y, *_ in fs["helmet_tabs"]]
    mask_plate = np.diff(crossings(mask, (0, 0, 20.5), (0, 1, 0)))[0]
    mask_bevel_floor = mask_plate - ms["bevel"]
    frame_front = fs["base"]["bounds"][2]
    section_y = (frame_front + ms["tip_y"]) / 2
    ligaments = []
    for x, height, *_ in fs["mask_sockets"]:
        hits = crossings(frame, (x, section_y, height), (0, 0, 1))
        ligaments.extend((hits[1] - hits[0], hits[-1] - hits[-2]))
    hits = crossings(frame, (0, section_y, fs["mask_sockets"][0][1]), (1, 0, 0))
    ligaments.extend(np.diff(hits)[::2])
    for x, height, *_ in fs["mask_sockets"]:
        hits = positive_hits(frame, (x, frame_front - 1, height), (0, 1, 0))
        ligaments.append(hits[-1] - hits[-2])
    return {
        "Shell side panels (eight normals)": min(shell_walls),
        "Shell roof above both socket tips": min(caps),
        "Mask plate at centre": mask_plate,
        "Mask plate lower bound at bevel": mask_bevel_floor,
        "Frame pocket ligaments at sampled sections": min(ligaments),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=MODEL)
    parser.add_argument("--repeat", type=Path, required=True)
    parser.add_argument("--variant", type=Path, required=True)
    parser.add_argument("--variant-config", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=MODEL / "experiments" / "mesh-validation-v0.1.md")
    args = parser.parse_args()
    config = json.loads((MODEL / "specifications/dimensions.json").read_text(encoding="utf-8-sig"))
    variant_config = json.loads(args.variant_config.read_text(encoding="utf-8-sig"))

    def stl(root, part):
        return root / "exports" / "stl" / f"{part}.stl"

    meshes = tuple(trimesh.load_mesh(stl(args.baseline, part)) for part in IDS)
    solids = []
    report = ["# Titan 02 head V0.1 mesh validation", "",
              "Geometry build with Blender 5.2.0 LTS. Validation uses STL coordinates in mm.",
              "", "| Part | X x Y x Z (mm) | Triangles | Volume (mm³) | SHA-256 |",
              "| --- | --- | ---: | ---: | --- |"]
    for part, mesh in zip(IDS, meshes):
        if not (mesh.is_volume and np.min(mesh.area_faces) > EPS):
            raise ValueError(f"{part} failed closed, oriented, connected solid checks")
        solids.append(checked(mf.Manifold(mf.Mesh64(
            np.asarray(mesh.vertices, dtype=np.float64), np.asarray(mesh.faces, dtype=np.uint64)))))
        if len(solids[-1].decompose()) != 1:
            raise ValueError(f"{part} is not a single connected solid")
        path = stl(args.baseline, part)
        if path.read_bytes() != stl(args.repeat, part).read_bytes():
            raise ValueError(f"{part} STL differs between repeated runs")
        dimensions = " x ".join(f"{n:.2f}" for n in mesh.extents)
        report.append(f"| {part} | {dimensions} | {len(mesh.faces)} | {mesh.volume:.2f} | "
                      f"`{hashlib.sha256(path.read_bytes()).hexdigest()}` |")
    bounds = trimesh.util.concatenate(meshes).extents
    expected = [config["prototype"][key] for key in ("width", "depth", "height")]
    if not np.allclose(bounds, expected, atol=0.05, rtol=0):
        raise ValueError(f"Assembled dimensions {bounds} differ from {expected}")

    frame, helmet, mask = solids
    shell_travel = meshes[0].bounds[1, 2] - meshes[1].bounds[0, 2] + 1
    mask_travel = meshes[2].bounds[1, 1] - min(mesh.bounds[0, 1] for mesh in meshes[:2]) + 1
    frame_path = swept(meshes[0], frame, (0, 0, -shell_travel))
    mask_path = swept(meshes[2], mask, (0, -mask_travel, 0))
    checks = [(f"{a}/{b} seated", solids[i], solids[j])
              for (i, a), (j, b) in combinations(enumerate(IDS), 2)]
    checks.extend([("Helmet insertion vs frame", frame_path, helmet),
                   ("Mask insertion vs frame", mask_path, frame),
                   ("Mask insertion vs seated helmet", mask_path, helmet)])
    report.extend(["", f"Assembled W × H × D measured **{bounds[0]:g} × {bounds[2]:g} × {bounds[1]:g} mm**.",
                   "All three meshes passed watertightness, winding, connectedness, degenerate-face,",
                   "positive-volume and Manifold import checks. A clean repeat produced byte-identical STLs.",
                   "", "## Intersections", "",
                   f"Continuous swept volumes over {shell_travel:g} mm of helmet travel and "
                   f"{mask_travel:g} mm of mask travel. The travel starts fully disengaged.", ""])
    for name, left, right in checks:
        volume = abs(checked(left ^ right).volume())
        if volume > MAX_OVERLAP:
            raise ValueError(f"{name} overlap is {volume:.6f} mm³")
        report.append(f"- {name} measured {volume:.6f} mm³ overlap.")

    report.extend(["", "## Clearances", ""])
    variant_meshes = tuple(trimesh.load_mesh(stl(args.variant, part)) for part in IDS)
    for label, parts, spec in (("Baseline", meshes, config), ("Variant", variant_meshes, variant_config)):
        for joint, x, side_values, end in joint_measurements(parts, spec):
            if not np.allclose(side_values, spec["joint"]["side_clearance"], atol=EPS, rtol=0):
                raise ValueError(f"{label} {joint} side clearance differs from specification")
            if not np.isclose(end, spec["joint"]["end_clearance"], atol=EPS, rtol=0):
                raise ValueError(f"{label} {joint} end clearance differs from specification")
            report.append(f"- {label} {joint.lower()} tab at X={x:g} mm measured "
                          f"{min(side_values):g} mm on each side and {end:g} mm at the tip.")

    report.extend(["", "## Wall checks", "",
                   f"Design minimum is {config['minimum_wall']:g} mm. Measurements cover critical "
                   "sections of this faceted design.", ""])
    for name, thickness in walls(meshes, config).items():
        if thickness < config["minimum_wall"] - EPS:
            raise ValueError(f"{name} is below the wall minimum at {thickness:g} mm")
        report.append(f"- {name} measured {thickness:.2f} mm.")
    report.extend(["", "Physical fit, retention, print orientation, and material-dependent wall",
                   "adequacy remain pending a test print.", ""])
    args.report.write_text("\n".join(report), encoding="utf-8")
    print(args.report)


if __name__ == "__main__":
    main()
