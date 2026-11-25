# Titan 02 Bust

V0.1 is a simplified, mechanically oriented head prototype. The assembled head measures 56 × 60 × 64 mm (width × height × depth). The 62 × 67 × 72 mm accessorized head and the concept scale of 1/35 remain provisional.

- [Dimensions and clearances](specifications/dimensions.json)
- [Part list](specifications/part-list.md), [assembly plan](specifications/assembly-plan.md), and [acceptance criteria](specifications/acceptance-criteria.md)
- [Assembled Blender project](blender/titan-02-head-v0.1.blend)
- [H001 inner frame](exports/stl/H001.stl), [H002 helmet shell](exports/stl/H002.stl), and [H003 face mask](exports/stl/H003.stl)
- [Assembled preview](exports/preview-renders/assembled.png) and [exploded preview](exports/preview-renders/exploded.png)
- [Mesh validation](experiments/mesh-validation-v0.1.md) and [build notes](experiments/v0.1-build-notes.md)

The three original design images are under [references](references/). STL coordinates are in millimetres. Joint retention, printing settings, and physical fit await evaluation. Record the first test under [test_prints](test_prints/) before expanding beyond the V0.1 head.

## Rebuild and validate

Run from the repository root with Blender 5.2.0 LTS and Python 3.13. The generator uses Blender's bundled Python. On Windows, point the PowerShell variable below to your Blender executable. A native Windows ARM64 portable build was used for the prototype. Install the independent validator dependencies if missing.

```powershell
python -m pip install numpy==2.5.5 trimesh==5.2.2 manifold3d==3.5.5
$blender = 'C:\path\to\blender.exe'
$model = 'models/titan-02-bust'
$generator = "$model/scripts/generate_head.py"
$run = "--background --factory-startup --threads 6 --python-exit-code 12 --python $generator"

function Invoke-BlenderBuild([string]$arguments) {
    $process = Start-Process -FilePath $blender -ArgumentList $arguments -NoNewWindow -PassThru -Wait
    if ($process.ExitCode -ne 0) { throw "Blender exited with code $($process.ExitCode)" }
}

Invoke-BlenderBuild $run
$work = Join-Path ([System.IO.Path]::GetTempPath()) "titan-v01-$([guid]::NewGuid())"
New-Item -ItemType Directory -Path $work | Out-Null
$variant = Join-Path $work 'variant.json'
$config = Get-Content "$model/specifications/dimensions.json" -Raw | ConvertFrom-Json
$config.joint.side_clearance = 0.40
$config | ConvertTo-Json -Depth 10 | Set-Content -Encoding utf8 $variant
Invoke-BlenderBuild "$run -- --stl-only --output `"$work/repeat`""
Invoke-BlenderBuild "$run -- --stl-only --output `"$work/variant`" --config `"$variant`""
python "$model/scripts/validate_head.py" --repeat "$work/repeat" --variant "$work/variant" --variant-config "$variant"
```

The build overwrites the model deliverables. The repeat and variant write into a separate temporary directory. For a geometry experiment, pass a separate `--config` and `--output` to the generator. Coordinates, joint directions, and assembly order are documented in the assembly plan.
