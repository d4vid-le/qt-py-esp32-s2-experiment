# Gate 2 — Schematic reconstruction

Status: **complete — awaiting review. No PCB or routing work started.**

## Verdict

| Check | Result |
|---|---|
| 45 physical components | **45 / 45** |
| 46 power symbols | **46 / 46** |
| No-connects on unconnected pins | **28 / 28** |
| Custom symbols embedded in `lib_symbols` | **12** |
| ERC errors | **0** |
| Netlist vs ground truth | **34 / 34 nets, 159 / 159 pads, identical** |
| Human interventions | **0** |

## Approach

Rebuilt from `design/netlist_original.csv` + `design/bom_clean.csv` +
`design/u15-pinmap.csv`. No Eagle import into `rebuild/`. No `kicad-sch-api`.

The key decision: **every custom symbol's pin numbers are the Eagle physical pad
names**, not invented pin numbers.

- ESP32-S2FN4R2: pins `1..57`, names from `design/u15-pinmap.csv`
- USB-C: pins `A5 A8 B5 B8 A6 B6 A7 B7 A4B9 B4A9 A1B12 B1A12`
- Headers: pins `1..7` and `1C..7C` (castellation = a second physical pad per position)
- JST-SH: `1 2 3 4 MT1 MT2`
- Buttons: `A A' B B'`
- Diode: `A C`; crystal: `1 3`; antenna: `FP`; testpoint: `P$1`; test pad: `TP`
- WS2812B: `1 2 3 4`; regulator: `1..5`

That makes the KiCad netlist directly comparable to the pad-level ground truth
without a translation layer.

Connectivity uses labels: **global labels** for `GND`, `+3V3`, `+5V`, `VBUS`
(so they merge with KiCad power symbols), **local labels** for signals.
All 159 pad connections, 46 power-symbol pins and 5 PWR_FLAG pins were labeled:
**210 labels (89 local, 121 global)**, 0 failures, placed in 16 chunks because
the MCP's per-command timeout is 30 s.

## Commands

```sh
# build
python3 scripts/build_gate2.py

# ERC
kicad-cli sch erc --format json -o rebuild/erc.json rebuild/qt-py-esp32-s2.kicad_sch

# netlist
kicad-cli sch export netlist -o rebuild/qt-py-esp32-s2.net rebuild/qt-py-esp32-s2.kicad_sch

# parse + drop the 28 intentionally-unconnected single-pin nets
python3 scripts/parse_kicad_netlist.py rebuild/qt-py-esp32-s2.net rebuild/rebuild_netlist.csv
# filter rows whose net starts with "unconnected-" -> rebuild_netlist_connected.csv

# diff
python3 scripts/diff_netlists.py design/netlist_original.csv \
  rebuild/rebuild_netlist_connected.csv --label-a original --label-b rebuild
```

## Build result

| Item | Count |
|---|---:|
| Symbol instances | 96 |
| Physical components | 45 |
| Power symbols | 46 |
| PWR_FLAGs | 5 |
| Custom symbol definitions embedded | 12 |
| Local labels (87 signal pads + 2 flags) | 89 |
| Global labels (72 power pads + 46 power symbols + 3 flags) | 121 |
| No-connect markers | 28 |
| Netlist components | 45 |
| Netlist nodes | 187 |

`lib_symbols` contains all 12 custom definitions plus the KiCad standard symbols
actually used. Verified by grep and by the fact that KiCad exports a netlist
without missing-symbol errors.

## Netlist diff — actual output

```
original: 34 nets, 159 pad connections
rebuild: 34 nets, 159 pad connections

matched net signatures : 34
only in original    : 0
only in rebuild     : 0

--- same connectivity, different net names ---
  !RESET    -> /RESET_N      3.3V      -> +3V3      N$2 -> /RF_LNA
  N$3       -> /RF_ANT       N$5       -> /XTAL_N_R  N$6 -> /XTAL_P
  N$7       -> /XTAL_N       ... (all local nets gain a leading "/")
  GND, +5V, VBUS keep their names

RESULT: IDENTICAL CONNECTIVITY
```

Full output: `rebuild/netlist-diff.txt`.

The 28 `unconnected-(...)` nets in the raw netlist are exactly the 28 pins with
no-connect markers. They are excluded from the connectivity diff because the
original netlist has no net for an unconnected pin.

## Net name mapping

| Eagle | Rebuild | Why |
|---|---|---|
| `3.3V` | `+3V3` | KiCad power-symbol convention |
| `!RESET` | `RESET_N` | `!` is not a robust label character |
| `N$2` | `RF_LNA` | auto-name → function |
| `N$3` | `RF_ANT` | auto-name → function |
| `N$5` | `XTAL_N_R` | auto-name → function (after R3) |
| `N$6` | `XTAL_P` | auto-name → function |
| `N$7` | `XTAL_N` | auto-name → function |
| all other signals | unchanged + `/` prefix | KiCad local-label scoping |

Renames do not affect the diff, which compares connectivity signatures.

## ERC — 35 warnings, 0 errors

| Type | Count | Explanation |
|---|---:|---|
| `footprint_link_issues` | 17 | `qt-py` footprint library is not created yet. Footprint names are assigned from the Eagle packages; geometry is Gate 3 work. |
| `lib_symbol_mismatch` | 17 | Embedded symbols differ from the library copy only in whitespace/formatting. Verified by normalized block comparison — pins, numbers and graphics are identical. |
| `pin_to_pin` | 1 | `NEOPIX_PWR`: PWR_FLAG (power_out) meets ESP32 `IO38` (bidirectional). Intentional — the GPIO switches the NeoPixel rail; the flag exists to satisfy LED `VDD` (power_in). |

Two errors were found and fixed during the gate:

1. `power_pin_not_driven` on `NEOPIX_PWR` → added a PWR_FLAG.
2. `pin_to_pin` error on `+3V3` → U1 `OUT` already drives it; removed the
   redundant PWR_FLAG.

Remaining non-ERC warning: `kicad-cli sch export netlist` prints
“schematic has annotation errors”. Cause: the testpoints keep their source
designators `GND` and `VBAT`, which have no numeric suffix. Renaming them would
break the exact 159/159 pad diff, so this is a deliberate trade-off.

## Footprint coverage

45/45 components have a footprint assigned; 17 unique footprint names.

| Class | Example | Source |
|---|---|---|
| Standard passives | `Capacitor_SMD:C_0402_1005Metric` | KiCad library |
| Standard IC | `qt-py:SOT23-5` | Eagle package name (custom library pending) |
| ESP32 | `qt-py:QFN56_7X7` | Eagle package |
| USB-C | `qt-py:USB_C_CUSB31-CFM2AX-01-X` | Eagle package |
| JST-SH | `qt-py:JST_SH4_SKINNY` | Eagle package |
| Buttons | `qt-py:BTN_KMR2_4.6X2.8` | Eagle package |
| Headers | `qt-py:1X07_CASTEL` | Eagle package |
| Antenna | `qt-py:ANT_2450AT18B100` | Eagle package |
| NeoPixel | `qt-py:SK6805_1515` | Eagle package |
| Test points | `qt-py:TESTPOINT_*`, `qt-py:B1_27` | Eagle package |

The 17 `qt-py:` names are **assigned but not yet built**. Creating them from the
Eagle package geometry is Gate 3 work and is recorded as such.

## Visual validation

- `renders/gate2-schematic.png` — rendered from KiCad's own SVG export
- SVG is generated locally (`rebuild/svg/`) but not committed (size)
- ESP32 symbol, 57 pins, 31 component groups, 46 power symbols, 28 NC flags all visible

## Tool failures / bugs found

1. **MCP symbol loader bug:** a symbol named `CRYSTAL_1_3` was rejected as a
   sub-symbol because the filter regex `.*_\d+_\d+"` also matches the top-level
   name. Renamed to `CRYSTAL_2PIN` and documented.
2. **MCP 30 s command timeout:** one `batch_connect` with 187 pins timed out.
   Worked around by chunking into 10-pin calls (16 calls, all 0 failures).
3. `batch_connect` returns a plain string, not a JSON object; the build script
   handles both.

## Unresolved / next gate

- Build the `qt-py` footprint library from the Eagle packages (Gate 3).
- ~~Decide whether to keep `GND`/`VBAT` refs or rename them.~~ Resolved in Gate 3:
  renamed `GND0`/`VBAT0`; the annotation warning is gone.
- The schematic is electrically correct but visually sparse: components are on
  a grid, not grouped by function. A cosmetic pass is optional.

## Human interventions

**0.** Entirely scripted.


## Gate 3 update (post-approval)

- Testpoints renamed `GND0` / `VBAT0`; `kicad-cli sch export netlist` no longer
  prints the annotation warning.
- `qt-py` footprint library built from the imported board; ERC
  `footprint_link_issues` **17 → 0**.
- ERC is now **18 warnings, 0 errors**: 17 `lib_symbol_mismatch` (17 instances
  of the 12 custom definitions, formatting-only) + 1 intentional `pin_to_pin`.
- Netlist diff command now uses `--rename-b "GND0=GND,VBAT0=VBAT"` and still
  reports **34/34 nets, 159/159 pads, identical**.
