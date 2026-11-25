# Titan 02 V0.1 resin print setup

Import the oriented STLs into CHITUBOX at 100% scale in millimetres. The files are centered individually with their lowest point at Z = 0. Keep the baked rotations, arrange the parts in XY, and use the slicer's support lift to make room for the supports and raft. Each part can be printed separately if the plate is small.

| Part | Bounds X × Y × Z (mm), before supports | Where to start supports | Where to keep contact tips off |
| --- | --- | --- | --- |
| H001 inner frame | 57.13 × 60.51 × 72.70 | Start under the low front-side corner of the broad base. Spread contacts across the underside and along the lower bevel as it grows. | Both rectangular front socket mouths and interiors, the front seating face, the top seating face, and the two upper tabs. |
| H002 helmet | 69.09 × 65.40 × 71.48 | Start at the low rear-side corner of the open rim. Follow the rear and lower side rim. If the layer preview calls for additional contacts, prefer a hidden non-mating inner sidewall or the exterior rear face. | Keep the opening unobstructed. Avoid the socket pockets and the inner roof seating face. Preserve the cosmetic top and front where possible. |
| H003 face mask | 49.65 × 18.41 × 45.92 | Start on the low corner of the chin bevel. Follow the underside and lower side edge as they appear. The two tabs rise away from the plate. | The broad show face, the flat rear seating face, and both tabs, including their tips and sidewalls. |

Run the CHITUBOX island check and step through the sliced layers after supporting. Pay particular attention to the helmet cavity and the blind sockets. Keep a clear resin path out through the helmet's existing lower opening. The frame and mask are exported as solid parts so their mating geometry is preserved. This setup has not been sliced for a specific machine or test-printed.

The STL copies use rigid rotations only. To recreate them from the original assembly-pose STLs, run from the repository root with the existing NumPy and trimesh dependencies.

```powershell
python models/titan-02-bust/scripts/orient_resin.py
```
