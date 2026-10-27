# Gate 3 — PCB placement

Status: **complete — awaiting review. No routing started.**

## Verdict

| Check | Result |
|---|---|
| Components from schematic | **45 / 45 footprints** |
| Nets | **34** |
| Assigned pads | **159** |
| Unmatched electrical pads | **0** (37 unmatched are NC/mechanical) |
| Footprint library warnings | **17 → 0** |
| Placement vs source, exact x/y/rotation/layer | **45 / 45** |
| Board outline | **17.78 × 20.701 mm**, 8 Edge.Cuts segments |
| Fiducials | **2**, at source positions |
| Tracks / vias | **0 / 0** (placement only) |
| Human interventions | **0** |

## Testpoint rename

`GND` → **`GND0`**, `VBAT` → **`VBAT0`**, matching KiCad's importer convention.
The diff now runs with `--rename-b "GND0=GND,VBAT0=VBAT"` and still reports
**34/34 nets, 159/159 pads, identical connectivity**.

This cleared the `schematic has annotation errors` warning: `TP_GND`/`TP_VBAT`
would still have no numeric suffix, so the numeric form was required.

## Footprint library

`rebuild/qt-py.pretty/` — 14 footprints extracted **from the imported KiCad
board**, not drawn from scratch:

```
SOD-323_MINI  CRYSTAL_2X1.6  QFN56_7X7  1X07_CASTEL  JST_SH4_SKINNY
BTN_KMR2_4.6X2.8  TESTPOINT_MINUS_1X3MM  TESTPOINT_PLUS_1X3MM
B1_27  USB_C_CUSB31-CFM2AX-01-X  SOT23-5  SK6805_1515
ANT_2450AT18B100  FIDUCIAL_1MM
```

Pad names preserved exactly, verified by grep:

| Footprint | Pads |
|---|---|
| QFN56_7X7 | 1…57 |
| USB-C | A1B12 A4B9 A5 A6 A7 A8 B1A12 B4A9 B5 B6 B7 B8 M1–M4 |
| 1X07_CASTEL | 1 1C 2 2C … 7 7C |
| JST-SH | 1 2 3 4 MT1 MT2 |
| Button | A A' B B' |
| Diode | A C |
| Crystal | 1 2 3 4 (nets use 1, 3) |
| Antenna | FP NC |
| Test point | P$1 |
| Test pad | TP |

Two source-driven fixes:

1. **Castellation pad rotation.** Eagle says `rot=R90`; KiCad's importer stored
   270°/90° absolute, making adjacent oval pads overlap (26 shorts). Rotating to
   0°/180° restored the source geometry: **shorting items 26 → 2, mask bridges
   30 → 6**.
2. **`B1,27` → `B1_27`** (filename-safe); `FIDUCIAL_1MM` added for the two
   board-only fiducials.

`fp-lib-table` uses `${KIPRJMOD}/qt-py.pretty`; the project is portable.

## Board creation

`create_board_from_schematic`:

```
45 footprints added, 34 nets added, 159 pads assigned
37 pads have no net — all are intentional NC or mechanical pads
```

The 37: 24 ESP32 unconnected pins, LED `DO`, regulator `P4`, USB-C `SBU1/SBU2`,
crystal pads 2/4, USB-C mechanical `M1–M4`, antenna `NC`, and two unnumbered
USB-C mechanics.

## Placement

Every one of the 45 footprints was moved to the imported board's exact
`(x, y, rotation, layer)`. 36 matched on the first pass; the 9 symmetric
passives on B.Cu needed an absolute-rotation correction after the flip. Final
verification: **45/45 exact**.

`design/gate3-placement.csv` — 47 rows (45 components + 2 fiducials).

Notable source facts: the ESP32 and most passives are on **B.Cu**; USB-C,
headers, buttons, NeoPixel, regulator and antenna are on **F.Cu**.

## Outline, castellations, fiducials

- 8 Edge.Cuts segments copied from the imported board: rounded rectangle
  **17.78 × 20.701 mm**, corner radius 2.54 mm.
- Castellations come from the `1X07_CASTEL` footprints (7 through-hole + 7
  castellation pads per side).
- USB-C at the bottom edge, antenna at the top, STEMMA QT on the right.
- 2 fiducials at the source positions `(6.1976, -19.4945)` and
  `(10.8585, -0.762)`.
- The drawing frame is **not** included.

## Design rules (from Eagle)

| Rule | Eagle | KiCad |
|---|---|---|
| Clearance | 6 mil | 0.1524 mm |
| Min track width | 6 mil | 0.1524 mm |
| Min drill | 15.5 mil | 0.3937 mm |
| Via outer restring | 25% | 0.0984 mm annular |
| Via diameter | derived | 0.5906 mm |
| Copper-to-edge | 10 mil | 0.254 mm |
| Drill clearance | 8 mil | 0.2032 mm |
| Layers / thickness | 2 / 1.6 mm | 2 / 1.6 mm |

Net classes: `Default` (0.1524), `Power` (0.254 track), `GND` (0.254 track).

## ERC after the footprint library

**0 errors, 18 warnings.** 17 are `lib_symbol_mismatch` — these are **17
instances of the 12 custom symbol definitions**, not 17 separate defects
(formatting-only; pins and graphics identical). The 18th is the intentional
`pin_to_pin` on `NEOPIX_PWR`.

## DRC — 236 violations, 111 unconnected

Command:

```sh
kicad-cli pcb drc --severity-all --format json \
  -o rebuild/gate3-drc.json rebuild/qt-py-esp32-s2.kicad_pcb
```

| Type | Errors | Warnings | Cause |
|---|---:|---:|---|
| `silk_over_copper` | 0 | 120 | dense source silkscreen |
| `silk_overlap` | 0 | 60 | source silkscreen text |
| `copper_edge_clearance` | 14 | 0 | castellation pads sit on the edge **by design** |
| `text_height` | 0 | 12 | source 0.6–0.7 mm text |
| `solder_mask_bridge` | 6 | 0 | castellation / connector mask openings |
| `courtyards_overlap` | 6 | 0 | source placement of 0402 passives |
| `clearance` | 5 | 0 | USB-C NPTH holes near pads; C19 near NPTH |
| `silk_edge_clearance` | 0 | 4 | source silkscreen |
| `shorting_items` | 2 | 0 | testpoint copper polygon has no net |
| `malformed_courtyard` | 2 | 0 | testpoint courtyard not closed |
| `unresolved_variable` | 2 | 0 | `${TP_SIGNAL_NAME}` in testpad text |
| `text_thickness` | 0 | 2 | source text |
| `lib_footprint_mismatch` | 0 | 1 | USB-C instance vs library |
| **Total** | **37** | **199** | **236** |

**111 unconnected items** are expected: the board is unrouted. They are the
ratsnest lines Gate 4 will route.

All 37 errors are source geometry or import artifacts, not placement mistakes:
the same footprints and positions are in the imported board. The two testpoint
`shorting_items` are the Eagle copper polygon represented as no-net copper in
KiCad; the pad and polygon are intentionally the same node.

## Schematic parity (extra check)

`--schematic-parity` reports **162 warnings**, all of one of:

- `footprint_symbol_field_mismatch` — the `Description` field is empty on the
  board footprints.
- `net_conflict` — board nets are `RESET_N`, schematic local labels are
  `/RESET_N`. Same connectivity, different name scope.
- `extra_footprint` — the two fiducials, intentionally board-only.

No connectivity discrepancies.

## Renders

- `renders/gate3-3d-top.png`
- `renders/gate3-3d-bottom.png`
- `renders/gate3-2d.png` (all layers; bottom text is mirrored as expected)

Visual comparison: the QFN56 with thermal pad, passives, testpoints, USB-C,
castellations and antenna land in the same positions as the Rev C fab print.
The 3D camera orientation is rotated relative to the fab print, but the
coordinate data matches the source 45/45.

## What worked / what failed

- Worked: footprint extraction from the imported board, exact placement,
  outline copy, Eagle-rule conversion, castellation rotation fix.
- Failed / limitations: testpoint copper polygon cannot be assigned a net in a
  `.kicad_mod`; USB-C NPTH holes violate KiCad's hole clearance; castellations
  violate the edge rule by design.

## Unresolved

- Testpoint `shorting_items` (2): would need the polygon converted to a pad.
- Castellation edge clearance (14): expected for this form factor.
- Schematic-parity naming: could be fixed by using global labels in Gate 2.

## Human interventions

**0.** No GUI steps.

**Stopped before Gate 4.** No routing.
