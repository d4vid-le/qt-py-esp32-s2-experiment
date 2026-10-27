# State — QT Py ESP32-S2 reconstruction

## Objective

Reconstruct Adafruit QT Py ESP32-S2 (product 5325, **Rev C**) in KiCad from the
authoritative Eagle source. Experiment only — no fabrication, no ordering.

## Hard rules

- Work only in this repository.
- `reference/` is evidence and is gitignored; `reference/eagle/` is never modified.
- Netlist ground truth comes from parsing the Eagle `.sch`, not from PDFs.
- No routing before the netlist gate passes and a human approves.
- No import of the Eagle design into `rebuild/`.
- No `kicad-sch-api`.
- Report failures honestly; never fake success.
- Git commit after every gate.

## Pinned source of truth

| Field | Value |
|---|---|
| Repository | https://github.com/adafruit/Adafruit-QT-Py-ESP32-S2-PCB |
| Commit | `7df4eac2c0b9a73ba966766ae6027b0a4d8a6901` |
| Commit date | 2022-03-29 |
| Schematic | `Adafruit QT Py ESP32-S2 Rev C.sch` |
| Board | `Adafruit QT Py ESP32-S2 Rev C.brd` |
| Eagle format | 9.6.2 |
| Checksums | `design/SHA256SUMS` |
| Local fetch | `scripts/fetch-reference.sh` |

## Gate status

| Gate | Name | Status |
|---|---|---|
| 0 | Inventory | complete, human approved |
| 1 | Ground truth in KiCad | **complete, human approved** |
| 2 | Schematic reconstruction | **complete, human approved** |
| 3 | PCB | **complete, human approved** |
| 4 | Routing | **PASS — 0 unconnected / 0 errors / 1.093 mm (verified reconstruction)** |
| 5 | Manufacturing | **outputs generated — PASS** |

## Final state

- Stackup: **4 layers, 1.6 mm** (source-faithful; the 2-layer premise was wrong).
- Routing: **0 unconnected / 0 DRC errors**, D+ 9.238 mm, D− 8.145 mm, **skew 1.093 mm**.
- Final board: **verified reconstruction** using reference signal routing, not an independent route.
- Manufacturing outputs generated in `exports/`; **nothing fabricated or ordered**.

## Decisions

1. **Rev C is the target** — confirmed by antenna rotation R270→R180 and the
   `VDD_SPI` split, not just the filename.
2. **Connectivity is compared by canonical pad signature**, never by net name.
3. **Multi-pad pins are expanded** (`"7 7C"` → two pads).
4. **`C7` / `C9` are DNP**, value TBD, antenna-match placeholders. Not guessed.
5. **Board size uses the Eagle outline** (17.78 × 20.701 mm). The product page's
   21.8 × 17.9 mm is assumed to include USB-C overhang; verify at Gate 3.
6. **`R3` = 0 Ω is preserved** and flagged as a source quirk.
7. **Physical BOM** = 45 components / 26 groups, excluding 46 power symbols,
   2 fiducials and 1 frame. Raw group count is 32.
8. **Netlist diff is name-agnostic**; reference renames are reported separately.
9. **No schematic import.** Human decision (Option 2): board-only import.
   Gate 2 is a from-scratch reconstruction. A GUI import remains available later
   as a recorded human intervention if symbol/wire mapping gets stuck.
10. **U$15 is an ESP32-S2FN4R2** (QFN56 7×7, 4 MB flash + 2 MB PSRAM).
    Device name `QFN54` is a library label error; package and 57 pads are correct.
11. **`nets.csv` distinguishes** `unique_pins`, `pad_count`, `power_pins`, and a
    pad-only signature. `pin_count` was removed as ambiguous.
12. **Custom symbols use Eagle pad names as pin numbers** (1..57, A1B12, A',
    MT1, FP, TP, ...), so the KiCad netlist is pad-comparable without a
    translation layer.
13. **Connectivity is label-based**: global labels for `GND`/`+3V3`/`+5V`/`VBUS`,
    local labels for signals. 187 connections, 28 no-connects.
14. **Net renames** are limited to invalid/auto names: `3.3V`→`+3V3`,
    `!RESET`→`RESET_N`, `N$2/3/5/6/7`→functional names. Diff is by signature.
15. **Footprints are assigned** from the Eagle package names for the 17
    QT-Py-specific parts.
16. **Testpoints renamed `GND0`/`VBAT0`** so KiCad annotation passes; the diff
    normalizes them back to `GND`/`VBAT`.
17. **Footprints were extracted from the imported board**, not redrawn.
    `B1,27` → `B1_27`; pad names preserved exactly.
18. **Castellation pad rotation restored** from Eagle `R90`; the importer stored
    270°/90°, which made adjacent ovals overlap.
19. **Eagle rules converted**: 6 mil clearance/width, 15.5 mil drill, 25%
    annulus, 0.254 edge. Final stack is **4 layers / 1.6 mm** per the source
    `layerSetup`, corrected at Gate 4B with approval.

20. **Testpoint copper polygon -> pad** (from its bounding box), closed courtyard,
    removed `${TP_SIGNAL_NAME}`.
21. **USB-C NPTH resized 1.158 -> 0.65 mm** to match the Eagle drill.
22. **Waivers**: castellation edge, USB-C internal hole clearance, courtyard
    overlap, via dangling. All documented in `.kicad_pro` / `.kicad_dru`.
23. **Routing**: independent Freerouting attempts peaked at **9 unconnected /
    0 errors** on 2 layers. The approved fallback used full reference signal
    routing on the source 4-layer stack, yielding **0 unconnected / 0 errors /
    1.093 mm skew** as a verified reconstruction.

## Closed pre-Gate-5 items

- **Precondition DRC**: 0 errors, 196 warnings, 111 unconnected.
- **Final DRC**: 0 errors, 0 unconnected.
- **Final routing**: 344.12 mm total, 43 vias, reference reconstruction.
- **Critical nets**: USB pair, antenna, crystal, NeoPixel, I2C routed.
- **Comparison**: original 343.93 mm / 36 vias; final 344.12 mm / 43 vias.

## Closed pre-Gate-4 items

- **Board creation — PASS.** 45/45 footprints, 34 nets, 159 pads assigned;
  37 unmatched are NC/mechanical.
- **Placement — PASS.** 45/45 exact x/y/rotation/layer vs the imported board.
- **Outline — PASS.** 17.78 × 20.701 mm, 8 segments, 2 fiducials, no frame.
- **DRC run** with Eagle rules: 236 violations (37 errors, 199 warnings),
  111 unconnected (unrouted, expected).
- **ERC** now 18 warnings, 0 errors (footprint-link warnings gone).

## Closed pre-Gate-3 items

- **Netlist — PASS.** 34/34 nets, 159/159 pads, identical connectivity.
- **ERC — 0 errors.** 35 warnings: 17 footprint-library, 17 formatting-only
  symbol-cache, 1 intentional PWR_FLAG-on-GPIO.
- **Symbols embedded.** 12 custom `lib_symbols`; 96 symbol instances.
- **No-connects.** All 28 unconnected pins flagged.
- **Zero human interventions.**

## Closed pre-Gate-2 items

- **U$15 pin audit — PASS.** 57/57 pads match the datasheet; 33 connected,
  24 unconnected. See `reports/gate1-u15-audit.md` and `design/u15-pinmap.csv`.
- **MCP/SWIG backend — healthy.** `get_board_info`/`get_layer_list` succeed on a
  known-good board. The authoritative import fails to load because of its
  `UNDEFINED` layers, not because SWIG is broken.
- **Viz copy equivalence — confirmed.** Normalized original is byte-identical to
  the viz copy; nets/pads/tracks unchanged.
- **License — CC BY-SA 3.0 Unported**, verified in `reference/eagle/license.txt`
  and linked from the README.

## Gate 4B — PASS (verified reconstruction)

2-layer independent routing peaked at **9 unconnected / 0 errors**; targeted
4-layer replacement reached 8 / 0. The approved fallback (full reference signal
routing, source 4-layer stack, reference zones) reached **0 / 0 / 1.093 mm**.
Details: `reports/gate4b-routing.md`.

## Open items

- **Silkscreen warnings**: 196 cosmetic warnings (114 over-copper, 61 overlap,
  12 text-height, 4 silk-edge, 3 lib-footprint, 2 text-thickness).
- **Final board is a verified reconstruction** (reference signal routing), not
  an independent route.
- **`lib_footprint_mismatch` x3**: USB-C + 2 testpoints, formatting/instance only.
- **Schematic parity naming**: 162 warnings, no connectivity difference.
- **NEOPIX_PWR `pin_to_pin`**: intentional PWR_FLAG on a GPIO-switched rail.
- **Importer defect**: Eagle user layers 200/201 (and 46/51) become `UNDEFINED`;
  the imported board is not DRC-loadable. Electrical data is intact. Affects only
  reference/visual use, not the rebuild.
- **`pcbnew.LoadBoard()` is broken outside KiCad** — use the S-expression
  extractor. The MCP's own SWIG backend is unaffected.

## Tooling

- KiCad 10.0.7, macOS arm64.
- `kicad-cli` for import/ERC/DRC/render.
- MCP toolboxes scoped per stage (`KICAD_MCP_TOOLBOXES=core`), categories opened
  only as needed. Gate 0 and Gate 1 used no MCP tools.
