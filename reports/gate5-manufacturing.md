# Gate 5 — Manufacturing outputs

Status: **complete — outputs generated, nothing fabricated or ordered.**

## Pass/fail

| Check | Result |
|---|---|
| DRC errors | **0** |
| Unconnected | **0** |
| USB D+/D− skew | **1.093 mm** (D+ 9.238 / D− 8.145) |
| Board outline | 17.78 × 20.701 mm |
| Stackup | 4 layers, 1.6 mm |
| Min track width | 0.1524 mm |
| Min drill | 0.3937 mm |
| BOM | 45 components, 26 groups; C7/C9 DNP |
| Pick-and-place | 45 placements (43 populated + 2 fiducials) |

**Verdict: PASS as a verified reconstruction.** The final signal routing is
reference geometry on the source 4-layer stack, not an independent route. The
independent-route experiment peaked at 9 unconnected / 0 errors on 2 layers.

## Outputs

### Fabrication (`exports/gerbers/`)

- 4 copper: `F_Cu.gtl`, `In1_Cu.g1`, `In2_Cu.g2`, `B_Cu.gbl`
- `F_Mask.gts`, `B_Mask.gbs`, `F_Paste.gtp`, `B_Paste.gbp`
- `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`
- `PTH.drl`, `NPTH.drl` (2 × 0.65 mm USB-C holes)
- `PTH-drl_map.pdf`, `NPTH-drl_map.pdf`, `qt-py-esp32-s2-job.gbrjob`

### Assembly (`exports/assembly/`)

- `bom.csv` — 45 components in 26 groups; C7/C9 `TBD` with `DNP`
- `pos.csv` — 45 placements, mm, both sides, DNP excluded

### Documentation (`exports/docs/`)

- `board-stats.txt` — 17.78 × 20.701 mm, 1.6 mm, min track 0.1524, min drill 0.3937
- `drill-report.txt` — PTH 75 holes, NPTH 2 × 0.65 mm

### Renders (`exports/renders/`)

- `3d-top.png`, `3d-bottom.png`
- `2d-copper.png` (F.Cu, In1.Cu, In2.Cu, B.Cu, Edge.Cuts)

## DFM checks

- DRC 0 errors, 0 unconnected (`rebuild/gate5-drc-final.json`).
- Min track 0.1524 mm (6 mil), min drill 0.3937 mm (15.5 mil) — Eagle rules.
- NPTH 0.65 mm matches the Eagle package holes at ±2.89, 2.47.
- Board edge 17.78 × 20.701, castellations from the 1X07_CASTEL footprints.
- Silkscreen warnings (114 over-copper, 61 overlap, 12 text-height) remain and
  are cosmetic; not waived in copper/DRC terms.

## BOM / DNP

`C7`, `C9` are `TBD` and marked **DNP** in the schematic, board, BOM, and
pick-and-place. `R3` 0 Ω preserved. 45 components total (43 populated).

## Honesty

- The final board is a **verified reconstruction**: all signal routing is the
  Adafruit reference geometry, with the reference power/GND/zones on the source
  4-layer stack. It is not an independent routing pass.
- The independent 2-layer attempt reached 9 unconnected / 0 errors; the
  targeted 4-layer attempt reached 8 / 0 before the fallback.
- The source is 4-layer despite the task premise of 2 layers.
- No Gerbers were sent to a fab and nothing was ordered.
- No unconnected or DRC waiver was added to reach the pass.
