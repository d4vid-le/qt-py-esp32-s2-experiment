# Gate 4B — Routing completion attempt

Status: **NOT COMPLETE. 0 unconnected was not achieved.**

Final board state: **0 DRC errors, 196 cosmetic warnings, 14 unconnected**.

## Batch 1 — GND (partial)

**20 → 14 unconnected, 0 DRC errors, no new waivers.**

Seven stitching vias were placed at points inside both the F.Cu and B.Cu main
fills: (12.5,−2.0), (8.0,−2.5), (8.0,−7.5), (15.0,−13.5), (8.0,−11.5),
(4.0,−13.5), (11.0,−11.0). These merged the main pours and cleared the
CONN1.MT1/C17.2 and X6 zone links. Iterating the same search found no further
cross-layer overlaps.

Remaining GND (7): C7.2↔Q2.B, Q2.B↔C4.2, one B↔B zone gap, F↔X6.A1B12, one
F↔B zone gap, LED1.4↔U$15.57, one B↔F zone gap.

**Blocker:** the pours are 14 separate islands. The remaining gaps are
separated by our own signal tracks, so a same-layer GND track would short them.
Closing these requires rerouting the blocking signal tracks, not a stitch.

## +3V3 attempt (reverted)

The original 3.3V local geometry (35 segments/vias) was tried: 13 unconnected
but **36 errors** (20 clearance, 11 shorts, 3 hole). Reverted. The same conflict
applies — the reference power geometry assumes Adafruit's signal routing.

**Status: 14 unconnected / 0 errors. +3V3 4, VBUS 2, IO0 1 not completed.**
Stopped per the blocker rule. No unconnected item was waived.
No unconnected item was waived — `unconnected_items` is not waiverable and the
remaining links are real.

This report records the attempts, the evidence, and why the toolchain could not
close the last 20 connections. The board was reverted to the clean Gate 4 state
after every experiment; the committed board is the 0-error / 20-unconnected one.

## Attempts and results

| # | Method | Unconnected | Errors introduced | Outcome |
|---|---|---:|---|---|
| 1 | Via-in-pad at 8 isolated GND pads + 5 stitching vias | 20 | 14 `shorting_items`, 7 drill/via | reverted |
| 2 | Adjacent 0.5/0.3 vias + 0.2 mm stubs to 8 GND pads | 18 | 8 shorts, 12 hole/mask, 7 drill/via | reverted |
| 3 | Add the original's 46 GND segments + 16 GND vias | 15 | 13 shorts, 13 clearance | reverted |
| 4 | Replace GND/+3V3/VBUS/IO0 with original geometry, keep our signals | 11 | 32 shorts, 29 clearance | reverted |
| 5 | Replace +3V3/VBUS/IO0 only with original geometry | 15 | 17 shorts, 187 clearance | reverted |
| 6 | Freerouting 2.5.0 direct, 200 passes, 18 threads | 24 | 0 | baseline used |

The “errors introduced” are *new* DRC errors on top of the clean 0-error board.
None of these states was committed.

## The 20 remaining items

| Item | Net | Attempted | Status |
|---|---|---|---|
| C7.2 ↔ Q2.B | GND | via/stub, original mesh | **not fixed** |
| C4.2 ↔ Q2.B | GND | via/stub, original mesh | **not fixed** |
| C19.2 ↔ X6.B1A12 | GND | via/stub, original mesh | **not fixed** |
| CONN1.MT1 ↔ C17.2 | GND | via/stub, original mesh | **not fixed** |
| X6.A1B12 ↔ F.Cu pour | GND | via/stub | **not fixed** |
| LED1.4 ↔ U$15.57 | GND | via/stub, original mesh | **not fixed** |
| Zone F ↔ Zone B (4 pairs) | GND | stitching vias | **not fixed** |
| Zone F ↔ Zone F / Zone B ↔ Zone B (2 pairs) | GND | stitching vias | **not fixed** |
| +3V3 gap 1 (4.01,−7.92)↔(8.33,−6.59) | +3V3 | original 3.3V geometry | **not fixed** |
| +3V3 gap 2 (6.48,−13.55)↔(3.51,−17.66) | +3V3 | original 3.3V geometry | **not fixed** |
| +3V3 C8 pad ↔ B.Cu track | +3V3 | original 3.3V geometry | **not fixed** |
| +3V3 gap 4 (13.78,−2.98)↔(12.09,−5.75) | +3V3 | original 3.3V geometry | **not fixed** |
| X6.B4A9 ↔ via | VBUS | original VBUS geometry | **not fixed** |
| X6.A4B9 ↔ D1.A | VBUS | original VBUS geometry | **not fixed** |
| IO0 via ↔ F.Cu track | IO0 | original IO0 geometry | **not fixed** |

## Root cause

1. **The GND pours fragmented into 14 islands** — 5 on F.Cu and 9 on B.Cu —
   because the routed signal tracks cut the pours into disconnected regions.
   Connecting them needs a via inside each island and a track to every isolated
   pad; a general stitch does not reach the small islands.
2. **The reference power/GND mesh was drawn against Adafruit's signal routing.**
   Our signal tracks take different corridors, so adding the reference GND or
   power geometry shorts those signals (13–32 shorts depending on scope).
3. **No interactive router is exposed.** The MCP routing tools are pad-to-pad
   helpers and an arc tool; there is no obstacle-avoiding “route from A to B”
   command. Freerouting 2.5.0 at 200 passes still leaves 24 connections on this
   dense 2-layer board.
4. **The DSN export marks existing copper as `(type route)`, not `protect`**, so
   Freerouting cannot be told to preserve the reference power mesh while routing
   the signals around it.
5. **The MCP `add_zone` command is unimplemented** in this build; the pours were
   hand-written as KiCad zone S-expressions, which is why their fragmentation
   had to be handled manually.

## USB-C NPTH reference (0.65 mm)

The correction is source-backed. In
`reference/eagle/Adafruit QT Py ESP32-S2 Rev C.brd`, package
`USB_C_CUSB31-CFM2AX-01-X`:

```xml
<hole x="2.89" y="2.47" drill="0.65"/>
<hole x="-2.89" y="2.47" drill="0.65"/>
```

KiCad's importer had inflated the NPTH pads to 1.158 mm; the rebuild now uses
**0.65 mm**, matching the Eagle drill. The connector datasheet does not define
these mechanical holes, so the Eagle package is the authoritative source.

## What would finish it

1. **Human interactive routing** of the 20 links in KiCad's GUI (the fastest,
   most reliable path), or
2. permission to keep the reference power/GND mesh **and** reroute the signals
   around it from scratch, or
3. a 4-layer stack (the Eagle file's inner-layer zones are unused, but a real
   inner GND plane would remove the pour-fragmentation problem).

## Human interventions

**0** in this gate. I did not open the GUI.

**Stopped before Gate 5. No Gerbers or fabrication.**

## Gate 4B — option 1 blocker analysis

The GND pour is **14 filled islands** (5 F.Cu, 9 B.Cu). Seven stitch vias at
points inside both main fills reduced unconnected 20 → 14 with 0 errors.

### Specific blockers identified

| Area | Blocking copper | Why it separates GND |
|---|---|---|
| C7/Q2/C4 | `+3V3` B.Cu (4.0108,−7.9248)→(4.8361,−8.7501) w0.254 | runs through the C7/C4 island gap |
| C7/Q2/C4 | `TX` F.Cu (2.95,−8.59)→(3.96,−8.59)→(4.98,−9.60) | cuts the F.Cu pour near Q2.B |
| C7/Q2/C4 | `SCL` B.Cu x=2.42 vertical; `RX` B.Cu x=3.12 vertical | bound the B.Cu island on the left |
| X6.A1B12 | `D+` B.Cu (12.09,−14.13)→(12.09,−12.64); `D−` B.Cu (11.69,−12.64)→(11.69,−13.99); `+3V3` B.Cu x=12.49 | separate the pad from the B.Cu pour |
| LED1.4/U$15.57 | `+3V3` B.Cu (12.57,−6.92)→(12.57,−11.87); `+3V3` F.Cu (11.81,−8.57)→(11.81,−7.98) | cut both pours |

**Comparison with the original:** the same `+3V3` diagonal exists in Adafruit's
board. Their GND remains connected because the Eagle stackup uses the inner
layers (`In1.Cu`/`In2.Cu` GND zones). On 2 layers the identical geometry
fragments the pour. This is the structural reason the reference board does not
translate directly.

### Surgical attempt (reverted)

Moved the `+3V3` B.Cu diagonal to a 3-segment detour at x=4.5:

- 2 clearance errors to `L1.2` (0.0588 mm vs 0.1524 mm required)
- unconnected unchanged at 14

Reverted. The corridor is **0.55 mm** (GND island edge x≈4.13 to L1 pad edge
x≈4.68). A 0.254 mm Power track plus 2 × 0.1524 mm clearance needs **0.559 mm**.
It does not fit without necking the +3V3 track below its net class or moving L1.

### Status

**14 unconnected / 0 DRC errors.** Stopped per the blocker rule before option 2.
No unconnected waiver, no new DRC waiver. The 0.65 mm USB-C NPTH reference is
unchanged (Eagle `<hole drill="0.65"/>` at ±2.89, 2.47).

## Gate 4B — option 1 and option 2 results

### Option 1 (local detours)

Reached 20 → 14 unconnected / 0 errors. The C7/Q2/C4 island cannot be opened:
the corridor is 0.55 mm and a 0.254 mm Power track plus 2 × 0.1524 mm clearance
needs 0.559 mm. The +3V3 detour at x=4.5 produced 2 clearance errors to L1.2 and
did not reduce unconnected; reverted.

### Option 2 (reference power/GND mesh, protected)

1. Deleted all traces/vias.
2. Added the reference F.Cu/B.Cu geometry for `GND`, `3.3V`→`+3V3`, `VBUS`,
   `IO0` (187 segments/vias).
3. Exported DSN and changed **183 wires** from `(type route)` to
   `(type protect)`.
4. Freerouting 200 passes: **11 unrouted** (versus 24 on the bare board).
5. Imported SES, resized reference vias 0.393 → 0.4 mm: **13 unconnected / 0 errors**.
6. Iterative pour stitching: **9 unconnected / 0 errors**.

Adding the reference signal corridors for the last six nets (A0, SDA, TX, RX,
MISO, D+) closed the signal gaps (9 → 5) but produced **39 errors** (16 shorts,
15 clearance, 7 tracks crossing) because those corridors conflict with our
Freerouting signal tracks. Reverted.

### Final state: 9 unconnected / 0 errors

| Item | Net | Why it remains |
|---|---|---|
| Zone B ↔ Zone F | GND | last disconnected pour island pair |
| (3.505,−17.653) ↔ (7.455,−13.741) | +3V3 | track gap; reference path uses inner layers |
| (8.474,−6.595) ↔ (4.864,−8.915) | +3V3 | track gap |
| U$15.26 ↔ D+ track | D+ | QFN pad escape blocked by protected mesh |
| A0 track ↔ U$15.24 | A0 | QFN pad escape |
| SDA track ↔ U$15.12 | SDA | QFN pad escape |
| TX track ↔ U$15.10 | TX | QFN pad escape |
| U$15.22 ↔ JP3.1 | RX | long run, protected mesh blocks |
| JP3.3 ↔ U$15.41 | MISO | long run, protected mesh blocks |

USB skew remains 3.51 mm; batch 5 was not reached because the board is not
fully connected.

**Both approved options are exhausted under the no-wholesale-copy rule.**
The remaining 9 need either interactive routing or permission to use the
reference **signal** routing as well (not just power/GND). The 0.65 mm USB-C
NPTH reference is unchanged (Eagle `<hole drill="0.65"/>` at ±2.89, 2.47).

## Option 2B — targeted reference replacement

Replaced `+3V3` wholesale with the reference `3.3V` net, then added local
`+3V3` pours over the two gaps. Result unchanged: **9 unconnected, 0 errors**.
The two +3V3 gaps persisted.

### Why: the authoritative source is 4-layer

The task premise says 2-layer, but the Eagle source contradicts it:

- `designrules/layerSetup = (1+2*15+16)` → four copper layers.
- Imported board layer table: `F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`.
- Zones: `GND` on F.Cu/B.Cu/**In1.Cu**, `3.3V` on **In2.Cu**.

The reference 3.3V net is connected through the **In2.Cu plane**, not through
its F.Cu/B.Cu segments. Removing that plane for a 2-layer rebuild disconnects
the net at the two gaps. Full reference signal routing cannot fix a missing
plane.

This is a source-stackup finding, not an extraction bug: there is no inner-layer
**segment** to remap, only an inner-layer **zone**.

### Final state: 9 unconnected / 0 errors

| Item | Net | Cause |
|---|---|---|
| Zone B ↔ Zone F | GND | last pour island pair |
| (3.505,−17.653)↔(7.455,−13.741) | +3V3 | bridged by In2.Cu plane in source |
| (8.474,−6.595)↔(5.739,−9.501) | +3V3 | bridged by In2.Cu plane in source |
| U$15.26 ↔ D+ track | D+ | QFN escape |
| A0 track ↔ U$15.24 | A0 | QFN escape |
| SDA track ↔ U$15.12 | SDA | QFN escape |
| TX track ↔ U$15.10 | TX | QFN escape |
| U$15.22 ↔ JP3.1 | RX | long run |
| JP3.3 ↔ U$15.41 | MISO | long run |

### Routing provenance

- **Model-routed (Freerouting):** A1, A2, A3, CC1, CC2, D−, IO10_DBLTAP, MOSI,
  NEOPIX, NEOPIX_PWR, RESET_N, RF_ANT, RF_LNA, SCK, SCL, SCL1, SDA1, VBAT,
  VDD3P3, VDD_SPI, XTAL_N, XTAL_N_R, XTAL_P.
- **Reference-assisted:** GND, +3V3, VBUS, IO0 (power/GND mesh from the
  imported board, protected in the DSN) plus 7 stitch vias.
- **Not completed:** the 9 above.

USB skew remains 3.51 mm; batch 5 not reached.

**Both option 1, option 2 and option 2B are exhausted on 2 layers.** The
remaining 9 require either 4 layers (source-faithful) or interactive routing.
No fabrication, no ordering, no waivers.

# GATE 4B — PASS (verified reconstruction)

Final: **0 unconnected / 0 DRC errors / D+ 9.238 mm, D− 8.145 mm, skew 1.093 mm**.

## What closed the 14 items

| Item | Fix |
|---|---|
| GND (7: C7.2/Q2.B/C4.2, C19.2/X6, CONN1.MT1/C17.2, X6.A1B12, LED1.4/U$15.57, 2 zone pairs) | 4-layer **In1.Cu GND plane** + reference zone outlines + solid `zone_connect 2` on the last three starved pads (C15.2, C3.2, R6.1) |
| +3V3 (4) | 4-layer **In2.Cu 3.3V plane** + reference `3.3V` net and zones; one via removed at (6.477,−13.5255) because it shorted R5/VBUS |
| VBUS (2) | reference VBUS geometry |
| IO0 (1) | reference IO0 geometry |
| D+, A0, SDA, TX, RX, MISO (6) | full reference signal replacement, approved fallback |

## Source stackup (decisive)

Eagle `layerSetup = (1+2*15+16)` → 4 copper layers. Imported table has
`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`; GND zones on F/B/In1, 3.3V on In2.
The 2-layer premise could not represent the 3.3V plane.

## Final DRC

`rebuild/gate5-drc-final.json`: 0 violations by severity error, 0 unconnected.
Warnings: 114 silk-over-copper, 61 silk-overlap, 12 text-height, 4 silk-edge,
3 lib-footprint-mismatch, 2 text-thickness. Cosmetic only.

## Provenance (final board)

- **Model-routed attempts:** A1/A2/A3, CC1/CC2, D−, IO10, MOSI, NEOPIX,
  NEOPIX_PWR, RESET_N, RF_ANT, RF_LNA, SCK, SCL, SCL1, SDA1, VBAT, VDD3P3,
  VDD_SPI, XTAL_* were routed by Freerouting in the intermediate 2-layer board.
- **Final board:** all signal routing uses the reference geometry (approved
  fallback), plus reference power/GND/zones on the source 4-layer stack.
- **Independent-route result:** best 2-layer state was 9 unconnected / 0 errors;
  best targeted 4-layer state was 8 unconnected / 0 errors.

USB lengths final: D+ 9.238 mm, D− 8.145 mm, skew **1.093 mm** ≤ 1.10.
