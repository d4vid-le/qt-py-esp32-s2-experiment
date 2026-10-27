# qt-py-esp32-s2-experiment

A personal, non-production experiment: reconstruct the **Adafruit QT Py ESP32-S2
(Product 5325, Rev C)** in KiCad from the authoritative Eagle source, measuring
how accurately an AI agent can do it — and documenting every failure.

**This is not affiliated with or endorsed by Adafruit.** No boards are fabricated.

## Status

| Gate | Stage | Result |
|---|---|---|
| 0 | Inventory | ✅ 45 components, 34 nets, 159 pads; `.sch` vs `.brd` exact |
| 1 | Ground truth in KiCad | ✅ board imported; netlist identical after 2 ref renames; 57/57 pin audit |
| 2 | Schematic reconstruction | ✅ 45 components, 46 power symbols, 34/34 nets, 0 ERC errors |
| 3 | PCB | ✅ 45/45 placed, 17.78×20.701 outline, DRC run |
| 4 | Routing | ⚠️ Gate 4B blocked: 0 DRC errors, 20 unconnected |
| 5 | Manufacturing | ⏸ |

Read `reports/gate0-inventory.md`, `reports/gate1-ground-truth.md`,
`reports/gate1-u15-audit.md`, and `reports/gate2-schematic.md`.

## Attribution

The reference design is Adafruit's work, licensed **CC BY-SA 3.0 Unported**.
Verified in the source repository's
[`license.txt`](https://github.com/adafruit/Adafruit-QT-Py-ESP32-S2-PCB/blob/main/license.txt)
(shasum `075dad5e…86b74`):

- Product: https://www.adafruit.com/product/5325
- Learn guide: https://learn.adafruit.com/adafruit-qt-py-esp32-s2
- Downloads: https://learn.adafruit.com/adafruit-qt-py-esp32-s2/downloads
- Authoritative Eagle source: https://github.com/adafruit/Adafruit-QT-Py-ESP32-S2-PCB
- ESP32-S2 datasheet: https://cdn-learn.adafruit.com/assets/assets/000/096/705/original/esp32-s2_datasheet_en.pdf
- AP2112 datasheet: https://www.diodes.com/assets/Datasheets/AP2112.pdf

**Their Eagle files, PDFs and images are not committed here.** `reference/` is
gitignored; run `scripts/fetch-reference.sh` to pull them locally.

## Reproduce the netlist

```sh
scripts/fetch-reference.sh
python3 scripts/parse_eagle_netlist.py \
  "reference/eagle/Adafruit QT Py ESP32-S2 Rev C.sch" design
python3 scripts/compare_sch_brd.py \
  design/netlist_original.csv \
  "reference/eagle/Adafruit QT Py ESP32-S2 Rev C.brd"
python3 scripts/make_clean_bom.py \
  design/bom_original.csv design/bom_clean.csv design/bom_symbols.csv
```

Pin audit (needs PyMuPDF: `pip install -r scripts/requirements.txt`):

```sh
python3 scripts/parse_esp32s2_pins.py \
  reference/assets/esp32-s2_datasheet.pdf reference/imported-kicad/esp32s2-pins.csv
python3 scripts/make_u15_audit.py \
  "reference/eagle/Adafruit QT Py ESP32-S2 Rev C.sch" \
  reference/imported-kicad/esp32s2-pins.csv \
  design/netlist_original.csv design/u15-pinmap.csv
```

Import the board and diff it:

```sh
kicad-cli pcb import --format eagle \
  -o reference/imported-kicad/qt-py-esp32-s2.kicad_pcb \
  "reference/eagle/Adafruit QT Py ESP32-S2 Rev C.brd"

python3 scripts/extract_kicad_netlist.py \
  reference/imported-kicad/qt-py-esp32-s2.kicad_pcb \
  reference/imported-kicad/imported_netlist.csv

python3 scripts/diff_netlists.py \
  design/netlist_original.csv \
  reference/imported-kicad/imported_netlist.csv
```

## Layout

```
design/     ground-truth CSVs, STATE.md, checksums   (committed)
reports/    per-gate evidence                        (committed)
scripts/    parser, diff, fetch                      (committed)
renders/    PNG/JPG evidence                         (committed)
rebuild/    the KiCad reconstruction                 (Gate 2+)
reference/  Adafruit material + imported board       (gitignored)
```

## What is deliberately not here

- Adafruit's Eagle/PDF/image files (license + redistribution hygiene)
- `reference/`, venvs, `node_modules/`, secrets, logs
- Fabrication files: nothing is ordered or produced for manufacturing

## Notes

- KiCad 10.0.7, macOS arm64.
- The Eagle importer maps custom user layers 200/201 to `UNDEFINED`, which makes
  the imported board unloadable by DRC. Electrical data is unaffected. See the
  Gate 1 report.
- `kicad-sch-api` is not used: it does not embed `lib_symbols`.
