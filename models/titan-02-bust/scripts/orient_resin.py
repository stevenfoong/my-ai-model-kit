"""Export unsupported, rigidly oriented STL copies for the Titan 02 resin trial."""
from pathlib import Path

import numpy as np
import trimesh

MODEL = Path(__file__).resolve().parents[1]
# Fixed printer axes: rotate about X, then about Y. +Z builds away from the plate.
POSES = {
    "H001": ("frame", 30, 17),
    "H002": ("helmet", -40, 18),
    "H003": ("mask", 12, 25),
}


def main():
    output = MODEL / "test_prints" / "v0.1-resin"
    output.mkdir(parents=True, exist_ok=True)
    for part, (name, x_degrees, y_degrees) in POSES.items():
        source = trimesh.load_mesh(MODEL / "exports" / "stl" / f"{part}.stl")
        rotation = trimesh.transformations.euler_matrix(
            *np.radians([x_degrees, y_degrees, 0]), axes="sxyz")
        oriented = source.copy().apply_transform(rotation)
        low, high = oriented.bounds
        oriented.apply_translation([-(low[0] + high[0]) / 2,
                                    -(low[1] + high[1]) / 2, -low[2]])
        path = output / f"{part}-{name}-resin-oriented.stl"
        oriented.export(path)
        saved = trimesh.load_mesh(path)
        if not (saved.is_volume and len(saved.faces) == len(source.faces)
                and np.allclose(saved.bounds, oriented.bounds, rtol=0, atol=1e-4)
                and np.allclose(saved.triangles, oriented.triangles, rtol=0, atol=1e-4)):
            raise ValueError(f"{part} failed orientation export validation")
        lowest = source.vertices[np.argmin(oriented.vertices[:, 2])]
        print(f"{part}: {saved.extents.round(2)} mm X/Y/Z; first point in assembly axes {lowest}")


if __name__ == "__main__":
    main()
