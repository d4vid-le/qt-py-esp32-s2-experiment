# State — QT Py ESP32-S2 reconstruction

## Objective

Reconstruct Adafruit QT Py ESP32-S2 (product 5325, **Rev C**) in KiCad from the
authoritative Eagle source. Experiment only — no fabrication, no ordering.

## Hard rules (from the task)

- Work only in `projects/qt-py-esp32-s2/`.
- `reference/` is evidence; `reference/eagle/` is never modified.
- Netlist ground truth comes from parsing the Eagle `.sch`, not from PDFs.
- No routing before the netlist gate passes and the human approves.
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
| .sch sha256 | `808a72e62ccfe99e7be6f4bd7102395402d270f19298865e63b8bd5a6a23d5f5` |
| .brd sha256 | `8bf3bbd36baa60cdb2e61accf4954786f0b25854471922261bcc58b5cf3bfb2c` |
| Pinout PDF sha256 | see `reference/SHA256SUMS` |

## Gate status

| Gate | Name | Status |
|---|---|---|
| 0 | Inventory | **complete — awaiting human approval** |
| 1 | Ground truth in KiCad | not started |
| 2 | Schematic reconstruction | not started |
| 3 | PCB | not started |
| 4 | Routing | not started |
| 5 | Manufacturing | not started |

## Decisions

1. **Rev C is the target.** Three schematic variants exist (base, uFL, Rev C).
   Rev C was confirmed by evidence, not just filename — see `design/gate0-inventory.md`.
2. **Nets are compared by canonical pad signature**, not by name. Eagle
   auto-names nets (`N$2`, `N$3`…); KiCad will name them differently. The
   signature is the sorted list of `ref.pad` on each net.
3. **Multi-pad pins are expanded.** Eagle maps one symbol pin to several pads
   (`"7 7C"`); each physical pad is a separate row so pad-level diffs are exact.
4. **Extra CSVs** beyond the required three: `nets.csv` (signatures),
   `unconnected.csv` (unused symbol pins). Both exist to make later diffs
   mechanical rather than judgement calls.
5. **Power symbols are not BOM components.** They are kept in `bom.csv` with
   `kind=symbol` so the filter is explicit and auditable.

## Assumptions / open questions

- `C7` and `C9` have value **TBD** in the source. They sit in the antenna
  matching network and are assumed to be unpopulated tuning placeholders.
  **Needs human confirmation before Gate 3 BOM.**
- PCB outline in Eagle is **17.78 × 20.701 mm**, while the product page states
  **21.8 × 17.9 mm**. Working assumption: published length includes the USB-C
  overhang (~1.1 mm). To be verified against the fab print in Gate 3.
- `U$15` uses package `QFN56_7X7` but the symbol is named `ESP-32-S2` and the
  device is `QFN54`. There are 57 pads (56 + exposed pad 57). Treated as the
  ESP32-S2 module, not a bare chip.

## Tooling

- MCP toolboxes are scoped per stage. Gate 0 used **no MCP tools** — only
  `git`, `python3` and the XML parser — so tool count was irrelevant here.
- Gate 1 will set `KICAD_MCP_TOOLBOXES=core` and open only the categories needed.
