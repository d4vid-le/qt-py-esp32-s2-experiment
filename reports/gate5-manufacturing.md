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

## Assembled 3D mock-up (visualization only)

A copy of the final board with 3D models added. **The electrical design, Gerbers,
BOM, DRC, and drill files were not changed.** `rebuild/` is untouched.

### Files

| File | What |
|---|---|
| `mockup/qt-py-esp32-s2-assembled.kicad_pcb` | board copy + 17 added models |
| `exports/renders/mockup/top.png` | 2400 × 1800 orthographic top |
| `exports/renders/mockup/bottom.png` | 2400 × 1800 orthographic bottom |
| `exports/renders/mockup/top-iso.png` | 2400 × 1800 perspective top |
| `exports/renders/mockup/bottom-iso.png` | 2400 × 1800 perspective bottom |
| `exports/renders/qt-py-esp32-s2-assembled.step` | assembled STEP (13 MB) |
| `exports/renders/qt-py-esp32-s2-assembled.glb` | binary glTF (1.7 MB) |

### Model coverage

45 of 47 footprints carry a model. `JP1`/`JP3` intentionally have no body:
their castellations are PCB features, not separate components.

| Part | Model | Fidelity |
|---|---|---|
| ESP32-S2 QFN56 7×7 | KiCad `QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm` | exact package body; pin 1 aligned |
| USB-C | KiCad `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | **representative**; shell wider than the exact CUSB31 |
| 0402 / 0805 passives | KiCad standard models | exact |
| SOT-23-5 regulator | KiCad standard | exact |
| JST-SH | KiCad `JST_SH_SM04B-SRSS-TB` | representative |
| Buttons | KiCad `SW_SPST_B3U-1000P` | **placeholder** for the side-actuated KMR2 |
| Antenna | KiCad `Johanson_2450AT18x100` | **representative** of the 2450AT18B100 |
| NeoPixel | KiCad 0603 LED, scaled | **placeholder** for SK6805 1.5×1.5 |
| Testpoints/testpads/fiducials | flat scaled test-point model | **placeholder**; copper pad shape is the accurate part |
| Diodes / crystal | KiCad SOD-323 / 2016 4-pad | representative |

### Visual comparison to the physical QT Py

- **ESP32:** on B.Cu, centered under the QFN pads, pin-1 dot visible — matches.
- **USB-C:** at the board edge, opening outward, pads aligned — orientation matches; the shell is a representative GCT model, not the exact CUSB31.
- **Buttons:** Q1/Q2 positions match the reset/boot locations; the B3U body is a representative tactile switch, not the KMR2.
- **JST-SH:** at the edge, 4-pin, opening outward — placement matches; representative body.
- **Antenna:** at the correct corner/edge; Johanson 18x100 family model, not the exact B100.
- **Testpoints:** GND0/VBAT0 at the two source positions; flat placeholders, copper pads accurate.
- **Castellations:** visible as plated half-holes around JP1/JP3; no separate body, as intended.

No placement mismatch was found. The visible differences are model shells for
USB-C, buttons, antenna, NeoPixel, and the flat placeholders — all labeled
above. Nothing in this mock-up is evidence of an electrical change.
