# Experiment Report — QT Py ESP32-S2 reconstruction

## Conclusion

- **The authoritative Eagle source is 4-layer**, not 2-layer: `layerSetup = (1+2*15+16)`, with GND on `In1.Cu` and 3.3V on `In2.Cu`. The earlier 2-layer premise was wrong and was corrected with explicit approval.
- **The independent 2-layer route peaked at 9 unconnected / 0 DRC errors.** It did not reach zero; the missing 3.3V plane made the last links unreachable without the source stackup.
- **The final board is a verified reconstruction using reference signal routing, not an independent route.** It passes with **0 unconnected / 0 DRC errors / D+ 9.238 mm, D− 8.145 mm, skew 1.093 mm**.

## Final numbers

| Metric | Result |
|---|---|
| Board | 17.78 × 20.701 mm, 4-layer, 1.6 mm FR4 |
| Components | 45 (43 populated; C7/C9 DNP) |
| Nets / pads | 34 / 159 |
| DRC | **0 errors, 0 unconnected** |
| USB skew | **1.093 mm** |
| Min track / space | 0.1524 mm |
| Min drill | 0.3937 mm |
| USB-C NPTH | 2 × 0.65 mm |
| Human interventions | 0 |

## Gates

| Gate | Result | Evidence |
|---|---|---|
| 0 Inventory | 45 components, 34 nets, 187 connected pins, 159 pads; `.sch` vs `.brd` 0 mismatches | `reports/gate0-inventory.md` |
| 1 Ground truth | Board imported; 34/34 nets and 159/159 pads match after 2 ref renames; U$15 audit 57/57 | `reports/gate1-ground-truth.md`, `reports/gate1-u15-audit.md` |
| 2 Schematic | 45 components, 46 power symbols, 34/34 nets, 159/159 pads, 0 ERC errors | `reports/gate2-schematic.md` |
| 3 PCB | 45/45 placed, 34 nets, 159 pads, outline 17.78×20.701, DRC run | `reports/gate3-pcb.md` |
| 4 Routing | **PASS as verified reconstruction**: 0 unconnected / 0 errors / 1.093 mm | `reports/gate4b-routing.md` |
| 5 Manufacturing | Gerbers, drill, BOM, PnP, DFM, renders; nothing fabricated | `reports/gate5-manufacturing.md` |

## Netlist and BOM

- Original vs KiCad-imported board: **identical connectivity**, 34 nets, 159 pad connections. Differences are two reference renames (`GND`→`GND0`, `VBAT`→`VBAT0`) and one display rename (`!RESET`→`~{RESET}`).
- BOM: 45 components in 26 groups; `C7`/`C9` are TBD and **DNP**. `R3` 0 Ω preserved.

## Routing provenance

- **Model-routed (Freerouting, intermediate 2-layer board):** A1/A2/A3, CC1/CC2, D−, IO10, MOSI, NEOPIX, NEOPIX_PWR, RESET_N, RF_ANT, RF_LNA, SCK, SCL, SCL1, SDA1, VBAT, VDD3P3, VDD_SPI, XTAL_N, XTAL_N_R, XTAL_P.
- **Reference-assisted (final board):** all signal nets, plus GND/+3V3/VBUS/IO0 and the source zone outlines on the 4-layer stack.
- **Independent-route peak:** 9 unconnected / 0 errors (2-layer). **Targeted 4-layer peak:** 8 / 0. The final artifact uses the approved full-reference fallback.

## Manufacturing outputs

`exports/gerbers/` — 4 copper layers (`F_Cu.gtl`, `In1_Cu.g1`, `In2_Cu.g2`, `B_Cu.gbl`), masks, paste, silk, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`, drill maps, `.gbrjob`.

`exports/assembly/` — `bom.csv` (45/26, C7/C9 DNP), `pos.csv` (45 placements, 43 populated + 2 fiducials).

`exports/docs/` — `board-stats.txt`, `drill-report.txt`, `fabrication-notes.md`.

`exports/renders/` — `3d-top.png`, `3d-bottom.png`, `2d-copper.png`.

## What worked / failed

Worked: Eagle XML parsing, `.sch`↔`.brd` cross-check, headless Eagle board import, S-expression netlist extraction, custom symbols with Eagle pad numbers, exact placement, castellation pad-rotation fix, 4-layer stack conversion.

Failed or limited:

- `pcbnew.LoadBoard()` is broken outside KiCad in this environment; the S-expression extractor is the workaround.
- KiCad's Eagle importer maps user layers 200/201 (and 46/51) to `UNDEFINED`; the authoritative import is not DRC-loadable. Electrical data is intact.
- `kicad-cli` has no schematic importer.
- MCP `add_zone` is unimplemented in this build; zones were written as S-expressions.
- The 2-layer premise was wrong; the source is 4-layer.
- Independent routing did not reach zero on 2 layers; the reference fallback was required.

Bugs caught by independent checks:

- Compound pads (`"7 7C"`) were initially treated as one pad — 17 false mismatches.
- A page-footer `12` was read as a datasheet pin number; requiring sequential pins fixed it.
- `U$15` is an ESP32-S2FN4R2; the Eagle device label `QFN54` is wrong but the 57-pad QFN56 package is correct.

## Human interventions

**0** across all gates. No GUI schematic import; no interactive routing.

## Time and tokens

- Wall-clock: approximately 10 hours (first file 03:45, final exports 13:44 local).
- Token counts are not exposed to the agent; no estimate is fabricated.

## Honesty section

- The final board is **not an independent routing pass**. It is a verified reconstruction: the signal routing is the Adafruit reference geometry, with the reference power/GND/zones on the source 4-layer stack.
- The independent 2-layer attempt reached 9 unconnected / 0 errors; the targeted 4-layer attempt reached 8 / 0 before the fallback.
- The 2-layer task premise was contradicted by the authoritative source; the 4-layer correction was approved explicitly.
- No unconnected or DRC waiver was added to reach the pass. Silkscreen warnings remain cosmetic.
- No board was fabricated or ordered.

## Attribution

The reference design is Adafruit's work, **CC BY-SA 3.0 Unported**. Sources:
<https://www.adafruit.com/product/5325>,
<https://learn.adafruit.com/adafruit-qt-py-esp32-s2>,
<https://github.com/adafruit/Adafruit-QT-Py-ESP32-S2-PCB>.
Their files are not redistributed here; `scripts/fetch-reference.sh` pulls them locally.
