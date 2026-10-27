# Gate 4B — Routing completion attempt

Status: **NOT COMPLETE. 0 unconnected was not achieved.**

Final board state: **0 DRC errors, 196 cosmetic warnings, 20 unconnected**.
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
