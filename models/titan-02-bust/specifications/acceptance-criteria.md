# V0.1 acceptance criteria

- Exactly three generated parts, each a single closed oriented manifold solid with positive volume and no degenerate triangles.
- Assembled bounding box measures 56 × 60 × 64 mm in width, height and depth within 0.05 mm. Blender declares millimetres and STL coordinates are interpreted as millimetres.
- Inspect the thinnest designed wall sections, pocket covers and ligaments against the 2.4 mm design minimum. Edge bevels and open rims require separate geometric interpretation.
- Configured socket clearance is 0.25 mm per side and 0.5 mm at the tip. Repeat the build with a different side clearance to verify that both mating socket pairs respond.
- No positive-volume overlap above 0.001 mm³ at the seated pose or with either part moving toward its seated pose on the documented straight axis.
- A repeated build with the same Blender version and configuration produces byte-identical STL files.
- Record process-specific wall adequacy, fit, retention, and ease of removal after a physical test print.
