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
| 2 | Schematic reconstruction | **next — preconditions met** |
| 3 | PCB | not started |
| 4 | Routing | not started |
| 5 | Manufacturing | not started |

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

## Open items

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
