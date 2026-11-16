# Lab 02 reference solution

Written by `src/make_reference.py` from the arithmetic in `src/land_pattern.py`, then saved
once by `kicad-cli fp upgrade --force` and `kicad-cli sym upgrade --force` in the pinned image.

| File | What it is |
|---|---|
| `pads.md` | the hand calculation |
| `ic103.pretty/RHL0024A.kicad_mod` | the footprint |
| `ic103.kicad_sym` | the symbol `SN74LVC8T245RHL` |

| | Long sides (2–11, 14–23) | Short sides (1, 12, 13, 24) |
|---|---|---|
| Z | 4.23 | 6.23 |
| G | 2.39 | 4.39 |
| X | 0.26 | 0.26 |
| Pad | 0.89 × 0.26 at x = ±1.67 | 0.26 × 0.89 at y = ±2.67 |

Exposed pad 2.05 × 4.05 on F.Cu and F.Mask, with paste through eight 0.83 × 0.82 windows
(66 % of its area). Courtyard ±2.37 × ±3.37.
