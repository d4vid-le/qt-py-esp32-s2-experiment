# Gate 1 — Ground truth in KiCad

Status: **complete for the board import; schematic import is blocked and needs
one human GUI step. Awaiting review before Gate 2.**

## What was done

1. Imported `Adafruit QT Py ESP32-S2 Rev C.brd` headlessly with `kicad-cli`.
2. Extracted a pad-level netlist from the imported `.kicad_pcb`.
3. Diffed it against `design/netlist_original.csv` — by **connectivity
   signature**, not net name.
4. Recorded an importer defect that makes the imported board unloadable by DRC.
5. Produced the clean physical BOM with DNP flags.
6. Recomputed the count reconciliation; two of the supplied figures were wrong.

No Eagle file was modified. No GUI step was performed yet.

## Command used (reproducible)

```sh
kicad-cli pcb import \
  --format eagle \
  --report-format json \
  --report-file reference/imported-kicad/import-report.json \
  -o reference/imported-kicad/qt-py-esp32-s2.kicad_pcb \
  "reference/eagle/Adafruit QT Py ESP32-S2 Rev C.brd"
```

Output: `Successfully saved imported board` — no warnings, 0 errors.

Import statistics from `import-report.json`:

| Metric | Value |
|---|---:|
| Footprints | 50 |
| Tracks | 418 |
| Vias | 36 |
| Zones | 4 |
| Errors | 0 |
| Warnings | 0 |

50 footprints = 45 components + 2 fiducials + 3 non-electrical board elements
(`U$7`/`U$13` artwork, `U$12` revision marker).

## Importer defect (must be recorded)

**The imported board cannot be loaded by `kicad-cli pcb drc`.**

```
Failed to load board: One or more items were found on undefined layers
(UNDEFINED). Open the board in the PCB Editor to resolve.
```

Cause: 5,385 graphics items carry `(layer "UNDEFINED")`.

| Source | Items |
|---|---:|
| `QTPY_ESP32_TOP` artwork | 3,295 |
| `QTPYS2_BOT` artwork | 2,026 |
| USB-C, testpoints, fiducials, pads | 64 |

Root cause is traceable in the Eagle source: those footprints draw on **Eagle
user layers 200 and 201**, plus a few items on layer 46 (Milling) and 51
(Document). KiCad's Eagle importer maps user layers 1–9 only; 200/201 have no
destination and become `UNDEFINED`.

**Impact:** electrical data is intact — 159/159 pad nets extracted. Visual and
DRC use of the imported board is blocked until those graphics are remapped to a
legal non-copper layer. This is recorded as a known importer limitation, not
worked around inside the authoritative import.

## Netlist extraction

`scripts/extract_kicad_netlist.py` reads the `.kicad_pcb` S-expression directly
(stdlib only). `pcbnew.LoadBoard()` was tried first and failed in this
environment — it returns `None` for valid boards, and raises
`SystemError: <built-in function LoadBoard> returned a result with an error set`
once a `wx.App` exists. Both are recorded as tool failures; the S-expression
path is KiCad's own file format, so it is still KiCad's data.

Result:

```
footprints parsed : 50
pad/net rows      : 159
unique pads       : 159
distinct nets     : 34
```

## Diff — actual output

Raw diff (`scripts/diff_netlists.py`), see
`reference/imported-kicad/netlist-diff.txt`:

```
original: 34 nets, 159 pad connections
imported: 34 nets, 159 pad connections

matched net signatures : 32
only in original    : 2
only in imported    : 2

--- only in original ---
  [GND] (38) ... GND.P$1 ...
  [VBAT] (2) D2.A VBAT.P$1

--- only in imported ---
  [GND] (38) ... GND0.P$1 ...
  [VBAT] (2) D2.A VBAT0.P$1

--- same connectivity, different net names ---
  !RESET                   -> ~{RESET}

RESULT: DIFFERENT
```

After normalizing the two reference designators:

```
matched net signatures : 34
only in original    : 0
only in imported-normalized: 0

--- same connectivity, different net names ---
  !RESET                   -> ~{RESET}

RESULT: IDENTICAL CONNECTIVITY
```

### Every difference, explained

| Difference | Count | Explanation | Verdict |
|---|---:|---|---|
| `GND` → `GND0` | 1 ref | KiCad renamed the testpoint reference; pad `P$1`, package `TESTPOINT_MINUS_1X3MM` unchanged | cosmetic |
| `VBAT` → `VBAT0` | 1 ref | same for the battery testpoint | cosmetic |
| `!RESET` → `~{RESET}` | 1 net name | KiCad overbar notation for active-low | cosmetic |
| Auto net names (`N$2`…) | — | not compared; matched by signature | by design |

**No connectivity difference exists.** 34/34 nets and 159/159 pad connections
match after accounting for two reference renames.

## Count reconciliation (corrected)

Two supplied figures did not reconcile. The corrected table:

| Quantity | Count | Relationship |
|---|---:|---|
| `<part>` elements | 94 | 45 + 46 + 2 + 1 |
| Physical components | 45 | — |
| Power symbols | 46 | — |
| Fiducials | 2 | no nets |
| Drawing frame | 1 | no nets |
| Connected symbol pins `(ref,gate,pin)` | 187 | 141 component + 46 power |
| Component pins with pads | 141 | — |
| Multi-pad pins | 18 | each maps to 2 pads |
| **Physical pad contacts** | **159** | 141 + 18 |
| Power-symbol rows | 46 | no pad |
| **Net-CSV rows** | **205** | 159 + 46 |
| Unconnected symbol pins | 28 | audited individually |
| **Total symbol pins** | **215** | 187 connected + 28 unconnected |
| BOM groups (raw) | 32 | 26 component + 4 power + 1 fiducial + 1 frame |
| **Physical BOM groups** | **26** | 45 components |

Corrections to the requested list:

- **“187 connected + unconnected symbol pins” is wrong.** 187 is *connected
  only*. Total symbol pins = 187 + 28 = **215**.
- **“45 components, 32 groups” is wrong.** 32 is the raw group count including
  non-physical parts. The physical BOM is **45 components in 26 groups**.
- `187` vs `186`: pin names are only unique within a gate. `CONN1` has two
  shield pins both named `MT` in gates `G$2`/`G$3`, mapping to `MT1`/`MT2`.
  Counting `(ref,pin)` merges them; counting `(ref,gate,pin)` does not.

## Clean BOM

`design/bom_clean.csv`: 45 components, 26 groups, excludes power symbols,
fiducials and frame. `design/bom_symbols.csv` keeps the 49 excluded parts for
audit.

- `C7`, `C9`: **DNP**, value `TBD`, antenna-match placeholders — not guessed.
- `R3`: 0 Ω, preserved, flagged as the crystal series quirk.
- Values are whitespace-stripped (`"  NSR0320"` → `NSR0320`).

## Reference images

Downloaded to `reference/assets/` (gitignored, not redistributed):

- `revc-schematic.png` — 5520×4270
- `revc-fabprint.png` — 780×854

The `/assets/110384` URLs return HTML; the real PNGs are on
`cdn-learn.adafruit.com` and were resolved from the downloads page.

## Visual check

The authoritative import cannot be rendered either — same `UNDEFINED` failure.
A **visualization-only copy** was made by moving all 5,385 unmatched graphics to
`Dwgs.User`:

- authoritative: `reference/imported-kicad/qt-py-esp32-s2.kicad_pcb` (untouched)
- viz copy: `reference/imported-kicad/qt-py-esp32-s2-viz.kicad_pcb`
- render: `renders/gate1-imported-top.png`

The two artwork footprints (`QTPY_ESP32_TOP`, `QTPYS2_BOT`) are on `Dwgs.User`
in the copy, so they do **not** appear in the 3D render. Everything else —
outline, castellations, USB-C, antenna, components, original routing — renders.
This is evidence that the import is geometrically sound, not that the board is
manufacturable as imported.

## Schematic import — deliberately not done

`kicad-cli` has **no schematic importer** (`sch` supports only erc/export/upgrade).
KiCad's Eagle project import is GUI-only.

**Decision (human, Gate 1 review): Option 2 — board-only import.** No GUI import.
Connectivity is already proven from two independent sources, and Gate 2 must be a
from-scratch reconstruction, not a copy of an imported schematic. A GUI import
remains available later as a recorded human intervention if symbol/wire mapping
gets stuck.

## MCP/SWIG backend test (blocking item closed)

The earlier `pcbnew.LoadBoard()` failure was suspected to affect the MCP server's
SWIG backend. It does not.

| Test | Result |
|---|---|
| `get_backend_state` | `swig`, board loaded, IPC connected |
| `check_kicad_ui` | KiCad running, IPC connected |
| `get_board_info` on known-good board | **success** — 30 × 20 mm, 24 layers |
| `get_layer_list` on known-good board | **success** |
| `open_board` on authoritative import | **fail** — “LoadBoard failed or returned an unusable board proxy” |
| `open_board` on viz copy | **success** — 17.83 × 20.75 mm, 26 layers |

Conclusion: the SWIG backend is functional. The failure is specific to the
imported file's `UNDEFINED` layer items. No IPC switch is required for Gate 2.
The one standalone-script limitation (`pcbnew.LoadBoard` outside KiCad) stands and
is documented; the S-expression extractor is the workaround.

## Viz copy equivalence (confirmed)

Moving `UNDEFINED` → `Dwgs.User` changes graphics layers only:

- Normalized original is **byte-identical** to the viz copy.
- 50 footprints, 198 pad declarations, 418 track segments, 13 zone references —
  identical counts. The “44 via references” is 36 `(via ...)` objects plus
  8 `(vias ...)` tokens (net-class/via settings), so it agrees with the import
  report's 36 vias.
- Netlist extracted from both: **34/34 nets, 159/159 pads, identical**.
- Authoritative import remains untouched.

## Data hygiene: `nets.csv`

`pin_count` was ambiguous (unique pins vs pad contacts). Replaced with explicit
columns:

`net, net_class, unique_pins, pad_count, power_pins, pad_signature, pad_signature_sha1`

Example: `+5V` = 9 unique pins, 7 pads, 3 power symbols; `3.3V` = 33 unique
pins, 24 pads, 10 power symbols. `pad_signature` matches the diff tool exactly.

## License verification

`reference/eagle/license.txt` is **Creative Commons Attribution-ShareAlike 3.0
Unported** (CC BY-SA 3.0), confirmed by reading the file. The repo README also
states CC BY-SA. The README now links the license text and pins the claim to the
source repository.

## Human interventions at Gate 1

**0.** No GUI schematic import, per the Option 2 decision.
