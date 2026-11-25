# Titan 02 head V0.1 mesh validation

Geometry build with Blender 5.2.0 LTS. Validation uses STL coordinates in mm.

| Part | X x Y x Z (mm) | Triangles | Volume (mm³) | SHA-256 |
| --- | --- | ---: | ---: | --- |
| H001 | 44.00 x 48.00 x 56.50 | 174 | 89967.00 | `7cf2a7e521cf33487f79403757ccfcf42adac5b9af165707cfc93019b6da0018` |
| H002 | 56.00 x 56.00 x 37.00 | 108 | 39885.67 | `e00dc66460d9e11c7e588267cea094d36405394a0fc7c22e7d0c42a9189cab1f` |
| H003 | 48.00 x 13.00 x 35.00 | 80 | 10572.40 | `99fb6f615a94b3e98e079283efcaed8f109a79fb99f6ef1851480413dfe26e49` |

Assembled W × H × D measured **56 × 60 × 64 mm**.
All three meshes passed watertightness, winding, connectedness, degenerate-face,
positive-volume and Manifold import checks. A clean repeat produced byte-identical STLs.

## Intersections

Continuous swept volumes over 34.5 mm of helmet travel and 7 mm of mask travel. The travel starts fully disengaged.

- H001/H002 seated measured 0.000000 mm³ overlap.
- H001/H003 seated measured 0.000000 mm³ overlap.
- H002/H003 seated measured 0.000000 mm³ overlap.
- Helmet insertion vs frame measured 0.000000 mm³ overlap.
- Mask insertion vs frame measured 0.000000 mm³ overlap.
- Mask insertion vs seated helmet measured 0.000000 mm³ overlap.

## Clearances

- Baseline helmet tab at X=-11 mm measured 0.25 mm on each side and 0.5 mm at the tip.
- Baseline helmet tab at X=11 mm measured 0.25 mm on each side and 0.5 mm at the tip.
- Baseline mask tab at X=-11 mm measured 0.25 mm on each side and 0.5 mm at the tip.
- Baseline mask tab at X=11 mm measured 0.25 mm on each side and 0.5 mm at the tip.
- Variant helmet tab at X=-11 mm measured 0.4 mm on each side and 0.5 mm at the tip.
- Variant helmet tab at X=11 mm measured 0.4 mm on each side and 0.5 mm at the tip.
- Variant mask tab at X=-11 mm measured 0.4 mm on each side and 0.5 mm at the tip.
- Variant mask tab at X=11 mm measured 0.4 mm on each side and 0.5 mm at the tip.

## Wall checks

Design minimum is 2.4 mm. Measurements cover critical sections of this faceted design.

- Shell side panels (eight normals) measured 3.50 mm.
- Shell roof above both socket tips measured 3.00 mm.
- Mask plate at centre measured 7.00 mm.
- Mask plate lower bound at bevel measured 5.00 mm.
- Frame pocket ligaments at sampled sections measured 5.75 mm.

Physical fit, retention, print orientation, and material-dependent wall
adequacy remain pending a test print.
