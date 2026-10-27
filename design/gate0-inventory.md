# Gate 0 — Inventory

Status: **complete, awaiting human approval. Nothing beyond Gate 0 was done.**

## Method

1. Cloned the authoritative repo into `reference/eagle/` (never modified).
2. Enumerated every file and checked git history per schematic variant.
3. Parsed `Adafruit QT Py ESP32-S2 Rev C.sch` as XML (Eagle 9.6.2), resolving
   `part → (library, deviceset, device) → package` and
   `connect(gate,pin) → pad`.
4. Cross-checked the result against the independent `.brd` signal/contactref
   table — a different file that must agree pin-for-pin.
5. Emitted `netlist.csv`, `bom.csv`, `pinmap.csv` (+ `nets.csv`,
   `unconnected.csv`, `unconnected` list).

## File inventory (`reference/eagle/`)

| File | Role |
|---|---|
| `Adafruit QT Py ESP32-S2 Rev C.sch` | **authoritative schematic (target)** |
| `Adafruit QT Py ESP32-S2 Rev C.brd` | **authoritative board (target)** |
| `Adafruit QT Py ESP32-S2.sch` / `.brd` | earlier Rev (base) — reference only |
| `Adafruit QT Py ESP32-S2 uFL.sch` / `.brd` | u.FL antenna variant — not the target |
| `Adafruit QT Py ESP32-S2 Pinout.pdf` | visual cross-check only |
| `assets/5325.jpg` | product photo, visual cross-check only |
| `factory-reset/` | firmware binaries, not design data |
| `README.md`, `license.txt` | CC BY-SA license terms |

No fab print (Gerber/PDF) was present in the repo. Gate 5 will need one supplied
or generated.

## Why this file is Rev C (evidence, not filename)

Three schematic variants exist. Rev C differs from base in exactly the two ways
the product notes describe:

**1. Rotated antenna (board file).**

| | base `.brd` | Rev C `.brd` |
|---|---|---|
| `X1` antenna rotation | `R270` | `R180` |
| `X1` position | (4.7371, 2.6416) | (4.8260, 1.3335) |
| ESP32 module `U$15` | (10.287, 9.1948) `MR180` | unchanged |

**2. Low-power sleep fix (schematic).** In Rev C, `VDD_SPI` is a **separate net**
(`C12.1`, `C13.1`, `U$15.30`) instead of being tied to `3.3V`. The `U$22` 3.3V
power symbol present in base is gone. Net-level diff base → Rev C:

- added net: `VDD_SPI`
- `3.3V` lost `C12.1`, `C13.1`, `U$22`
- all other nets identical

Rev C was added in the most recent commit, `7df4eac` (2022-03-29).
The uFL variant is a different product configuration (external antenna), not a
revision.

## Counts (Rev C)

| Quantity | Count | Notes |
|---|---:|---|
| Parts in `.sch` | 94 | raw `<part>` elements |
| **Electrical components** | **45** | parts with a package |
| Power symbols | 46 | GND ×32, 3.3V ×10, +5V ×3, VBUS ×1 |
| Drawing frame | 1 | `FRAME1` |
| Fiducials | 2 | `U$6`, `U$8` — no nets |
| Nets | 34 | 0 empty nets |
| Schematic pin connections (`pinref`) | 187 | unique part/gate/pin |
| Pin→pad mappings | 205 | after expanding multi-pad pins |
| Physical pad contacts | 159 | excludes 46 package-less symbols |
| Unconnected symbol pins | 28 | all explained below |
| Resolved library entries | 100% | 0 warnings |

## Component inventory (45)

| Qty | Value | Device | Package | Refs |
|---:|---|---|---|---|
| 1 | — | ANTENNA_JOHANSON_2450AT18B100 | ANT_2450AT18B100 | X1 |
| 5 | 0.1uF | CAP_CERAMIC | _0402NO | C10 C11 C12 C14 C4 |
| 1 | 100pF | CAP_CERAMIC | _0402NO | C16 |
| 2 | 16pF | CAP_CERAMIC | _0402NO | C17 C18 |
| 7 | 1uF | CAP_CERAMIC | _0402NO | C13 C15 C19 C2 C20 C3 C5 |
| 3 | 22uF | CAP_CERAMIC | 0805-NO | C1 C6 C8 |
| 2 | **TBD** | CAP_CERAMIC | _0402NO | C7 C9 |
| 1 | 40MHz | CRYSTAL | CRYSTAL_2X1.6 | Y1 |
| 2 | NSR0320 | DIODE | SOD-323_MINI | D1 D2 |
| 1 | — | ESP32-S2 | QFN56_7X7 | U$15 |
| 2 | — | HEADER-1X7 | 1X07_CASTEL | JP1 JP3 |
| 1 | 0 ohm | INDUCTOR | _0402 | L2 |
| 1 | 2nH | INDUCTOR | _0402 | L1 |
| 1 | 0 | RESISTOR | _0402NO | R3 |
| 2 | 10K | RESISTOR | _0402NO | R1 R2 |
| 1 | 1Meg | RESISTOR | _0402NO | R17 |
| 2 | 5.1K | RESISTOR | _0402NO | R5 R6 |
| 1 | STEMMA_I2C_QTSKINNY | STEMMA_I2C | JST_SH4_SKINNY | CONN1 |
| 1 | BOOT0 | SWITCH_TACT_SMT | BTN_KMR2_4.6X2.8 | Q1 |
| 1 | reset | SWITCH_TACT_SMT | BTN_KMR2_4.6X2.8 | Q2 |
| 1 | — | TESTPOINT | TESTPOINT_MINUS_1X3MM | GND |
| 1 | — | TESTPOINT | TESTPOINT_PLUS_1X3MM | VBAT |
| 2 | TPB1,27 | TP | B1,27 | SWC1 SWC2 |
| 1 | USB TYPE C | USB_C | USB_C_CUSB31-CFM2AX-01-X | X6 |
| 1 | AP2112K-3.3 | VREG_SOT23-5 | SOT23-5 | U1 |
| 1 | WS2812B_SK6805_1515 | WS2812B | SK6805_1515 | LED1 |

## Netlist — all 34 nets, pad-level

| net | class | pads | members |
|---|---|---:|---|
| `!RESET` | 0 | 6 | C3.1, Q2.A, Q2.A', R1.2, SWC1.TP, U$15.56 |
| `+5V` | 1 | 10 | C1.1, D1.C, D2.C, JP3.7, JP3.7C, SUPPLY1.+5V, SUPPLY2.+5V, SUPPLY3.+5V, U1.1, U1.3 |
| `3.3V` | 1 | 34 | C10.1, C11.1, C14.1, C15.1, C16.1, C19.1, C2.1, C4.1, C5.1, C6.1, C8.1, CONN1.2, JP3.5, JP3.5C, L1.1, R1.1, R2.1, U$10.3.3V, U$15.1, U$15.20, U$15.27, U$15.45, U$15.51, U$15.54, U$16.3.3V, U$17.3.3V, U$19.3.3V, U$2.3.3V, U$20.3.3V, U$21.3.3V, U$23.3.3V, U$24.3.3V, U$4.3.3V, U1.5 |
| `A0` | 0 | 4 | JP1.1, JP1.1C, R2.2, U$15.24 |
| `A1` | 0 | 3 | JP1.2, JP1.2C, U$15.23 |
| `A2` | 0 | 3 | JP1.3, JP1.3C, U$15.14 |
| `A3` | 0 | 3 | JP1.4, JP1.4C, U$15.13 |
| `CC1` | 0 | 2 | R6.2, X6.A5 |
| `CC2` | 0 | 2 | R5.2, X6.B5 |
| `D+` | 0 | 3 | U$15.26, X6.A6, X6.B6 |
| `D-` | 0 | 3 | U$15.25, X6.A7, X6.B7 |
| `GND` | 1 | 70 | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2, C19.2, C2.2, C20.2, C3.2, C4.2, C5.2, C6.2, C7.2, C8.2, C9.2, CONN1.1, CONN1.MT1, CONN1.MT2, GND.P$1, GND1.GND … GND27.GND, JP3.6, JP3.6C, LED1.4, Q1.B, Q1.B', Q2.B, Q2.B', R17.1, R5.1, R6.1, U$1.GND, U$14.GND, U$15.57, U$26.GND, U$40.GND, U$9.GND, U1.2, X6.A1B12, X6.B1A12 |
| `IO0` | 0 | 4 | Q1.A, Q1.A', SWC2.TP, U$15.5 |
| `IO10_DBLTAP` | 0 | 3 | C20.1, R17.2, U$15.15 |
| `MISO` | 0 | 3 | JP3.3, JP3.3C, U$15.41 |
| `MOSI` | 0 | 3 | JP3.4, JP3.4C, U$15.39 |
| `N$2` | 0 | 3 | C7.1, L2.2, U$15.2 |
| `N$3` | 0 | 3 | C9.1, L2.1, X1.FP |
| `N$5` | 0 | 2 | R3.2, U$15.52 |
| `N$6` | 0 | 3 | C17.1, U$15.53, Y1.3 |
| `N$7` | 0 | 3 | C18.1, R3.1, Y1.1 |
| `NEOPIX` | 0 | 2 | LED1.1, U$15.43 |
| `NEOPIX_PWR` | 0 | 2 | LED1.2, U$15.42 |
| `RX` | 0 | 3 | JP3.1, JP3.1C, U$15.22 |
| `SCK` | 0 | 3 | JP3.2, JP3.2C, U$15.40 |
| `SCL` | 0 | 3 | JP1.6, JP1.6C, U$15.11 |
| `SCL1` | 0 | 2 | CONN1.4, U$15.44 |
| `SDA` | 0 | 3 | JP1.5, JP1.5C, U$15.12 |
| `SDA1` | 0 | 2 | CONN1.3, U$15.46 |
| `TX` | 0 | 3 | JP1.7, JP1.7C, U$15.10 |
| `VBAT` | 0 | 2 | D2.A, VBAT.P$1 |
| `VBUS` | 1 | 4 | D1.A, U$5.VBUS, X6.A4B9, X6.B4B9 |
| `VDD3P3` | 0 | 3 | L1.2, U$15.3, U$15.4 |
| `VDD_SPI` | 1 | 3 | C12.1, C13.1, U$15.30 |

`GND` is abbreviated in `GND1…GND27.GND`; the full 70-entry list is in
`design/gate0-nets.md` and `reference/netlist.csv`.

## Independent cross-check: `.sch` vs `.brd`

The board file lists signals as `contactref element/pad`; the schematic netlist
is derived from `pinref → connect → pad`. These are two different files.

```
.sch nets with pads : 34   (159 pads)
.brd signals        : 34   (159 contacts)
nets only in .sch: 0 []
nets only in .brd: 0 []
common nets compared: 34  mismatched: 0
```

**Result: exact pad-level agreement.** The CSV netlist is trustworthy.

## Unconnected symbol pins (28) — all legitimate

| Part | Pins | Reason |
|---|---|---|
| `U$15` ESP32-S2 | 24 | GPIOs/SPI/UART/32k not broken out on QT Py |
| `U1` AP2112 | 1 | `P4` is the no-connect pin on SOT23-5 |
| `X6` USB-C | 2 | `SBU1`, `SBU2` intentionally unused |
| `LED1` SK6805 | 1 | `DO` unused (last LED in chain) |

No pin is referenced twice; no pinref points at an unknown part.

## Ambiguities requiring human input

1. **`C7`, `C9` = TBD.** Antenna matching shunt caps (N$2/N$3). Assumed
   unpopulated placeholders. Confirm before BOM in Gate 3.
2. **Board size mismatch.** Eagle outline `17.78 × 20.701 mm` vs published
   `21.8 × 17.9 mm`. Assumed to include USB-C overhang. Confirm in Gate 3.
3. **`R3` = 0 Ω in series with the crystal** (`Y1.1 → R3 → U$15.XTAL_N`).
   Unusual but present in the source; will be preserved as-is.
4. **No fab print in the repo.** Gate 5 visual comparison needs one.
5. **`U$15` naming inconsistency** — symbol `ESP-32-S2`, device `QFN54`,
   package `QFN56_7X7` with 57 pads. Treated as the module, not a bare die.

## What was deliberately NOT done

- No import of Eagle into KiCad (that is Gate 1, under `reference/imported-kicad/`).
- No schematic or PCB created in `rebuild/`.
- No routing, no Gerbers, no fabrication.
- No `kicad-sch-api`.
