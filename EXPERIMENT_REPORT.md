# Experiment Report — QT Py ESP32-S2 reconstruction

Final report is written after Gate 5. This file tracks results as gates close.

## Summary

| Gate | Result | Evidence |
|---|---|---|
| 0 Inventory | 45 components, 34 nets, 187 connected pins, 159 pads; `.sch` vs `.brd` 0 mismatches | `reports/gate0-inventory.md` |
| 1 Ground truth | Board imported; 34/34 nets and 159/159 pads match after 2 ref renames; U$15 audit 57/57 | `reports/gate1-ground-truth.md`, `reports/gate1-u15-audit.md` |
| 2 Schematic | 45 components, 46 power symbols, 34/34 nets, 159/159 pads, 0 ERC errors | `reports/gate2-schematic.md` |
| 3 PCB | not started | — |
| 4 Routing | not started | — |
| 5 Manufacturing | not started | — |

## Netlist diff

Original vs KiCad-imported board: **identical connectivity**, 34 nets,
159 pad connections. Differences are two reference renames
(`GND`→`GND0`, `VBAT`→`VBAT0`) and one display rename (`!RESET`→`~{RESET}`).

## BOM

45 physical components in 26 groups; `C7`/`C9` DNP (TBD in source). See
`design/bom_clean.csv`.

## Human interventions

Gate 0: 0. Gate 1: 0 (schematic GUI import pending decision).

## What worked / failed

- Worked: XML parsing, `.sch`↔`.brd` cross-check, headless Eagle board import,
  S-expression netlist extraction.
- Failed: `pcbnew.LoadBoard()` in this environment (returns `None`/raises);
  KiCad's Eagle importer maps user layers 200/201 to `UNDEFINED`, so the
  imported board cannot be opened by DRC; `kicad-cli` has no schematic importer.
- Parser bug caught by independent cross-check: compound pads (`"7 7C"`) were
  initially treated as one pad, producing 17 false mismatches.
- Parser bug caught by sequence check: a page-footer `12` was read as a pin
  number in the datasheet table; requiring sequential pins fixed it.
- U$15 is an ESP32-S2FN4R2; the Eagle device label `QFN54` is wrong but the
  57-pad QFN56 package and every pin name are correct.

## Honesty section

Filled in at Gate 5.
