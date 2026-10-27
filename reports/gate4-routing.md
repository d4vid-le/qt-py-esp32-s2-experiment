# Gate 4 — Routing

Status: **complete with a documented shortfall — 20 connections remain unrouted.
Awaiting review. No Gerbers or fabrication.**

## Verdict

| Check | Result |
|---|---|
| Precondition DRC | **0 errors**, 196 warnings, 111 unconnected |
| Routed board DRC | **0 errors**, 196 warnings, **20 unconnected** |
| Tracks / vias | 323 segments / 18 vias |
| Total track length | 298.86 mm |
| Critical nets routed | USB D+/D-, antenna, crystal, NeoPixel, I2C, 3.3 V, GND pours |
| Diff-pair length match | **not matched**: D+ 10.30 mm, D- 6.79 mm (3.51 mm skew) |
| Human interventions | 0 |

**The 20 unrouted connections are a real shortfall, not a pass.** They are listed
below and not described as intentional.

## Preconditions — all five addressed

1. **Testpoints.** The no-net copper polygon was converted to an equivalent
   `P$1` pad (2.9762 × 1.5762 mm roundrect, from the polygon bounding box); the
   broken courtyard line was replaced with a closed rectangle; `${TP_SIGNAL_NAME}`
   was removed from `B1_27` and from the placed SWC1/SWC2 instances.
   Result: `shorting_items` 2→0, `malformed_courtyard` 2→0,
   `unresolved_variable` 2→0, testpoint `solder_mask_bridge` 2→0.
2. **USB-C NPTH.** Eagle has two 0.65 mm holes at (±2.89, 2.47). KiCad had
   inflated the NPTH pads to 1.158 mm. Resized to **0.65 mm**, matching the
   source drill. The remaining 0.1755 mm hole-to-pad clearance is intentional
   (holes inside the connector shell) and is covered by a documented
   `hole_clearance` rule.
3. **Courtyard overlaps.** Six pairs (C18/C14, C16/C15, C14/C3, C14/R1,
   C20/R17, C3/R1) come from the source 0402 placement at 0.889 mm pitch.
   Non-electrical; recorded as a documented `courtyards_overlap = ignore`
   waiver rather than silently redrawing standard footprints.
4. **USB-C lib mismatch.** The real defect was the NPTH size, now corrected in
   both library and instance. The remaining `lib_footprint_mismatch` warnings
   (USB-C + 2 testpoints) are formatting/instance differences, not geometry.
5. **Castellation / mask waivers.** `.kicad_dru` rules for castellation edge
   clearance and USB-C internal hole clearance; `copper_edge_clearance` and
   `via_dangling` severities are documented waivers. Silkscreen warnings are
   left for Gate 5.

## Routing method

1. Freerouting 2.5.0 via its CLI, **200 passes, 18 threads**, from the clean
   pre-route board: 125 initially unrouted → **24 unrouted**, 0 violations.
2. SES imported into KiCad.
3. GND pours added on F.Cu and B.Cu (solid pad connection, island removal off)
   and refilled to absorb the GND ratsnest.
4. DRC with the Eagle rules and the documented waivers.

The MCP's `add_zone` command returned “Unknown command”; the pours were written
as KiCad zone S-expressions and refilled with `kicad-cli pcb drc --refill-zones
--save-board`. That tool failure is recorded rather than hidden.

## Unconnected — 20 items

| Net | Items | What is missing |
|---|---:|---|
| GND | 13 | cross-layer zone joins and 5 pad-to-zone gaps (C7/Q2, C4/Q2, C19/X6, CONN1/C17, LED1/U$15) |
| +3V3 | 4 | track-to-track gaps, two requiring layer changes |
| VBUS | 2 | USB-C pads to D1 cathode, layer changes |
| IO0 | 1 | track-to-track gap, layer change |

These are the router's unfinished connections, not intentional no-connects.
Fixing them needs either targeted manual routing with vias or a second routing
pass; both are deferred to the Gate 4 review decision.

## DRC before/after

| | Before routing | After routing |
|---|---:|---:|
| Errors | 0 | **0** |
| Warnings | 196 | 196 |
| Unconnected | 111 | **20** |

Warning types after routing: `silk_over_copper` 114, `silk_overlap` 61,
`text_height` 12, `silk_edge_clearance` 4, `lib_footprint_mismatch` 3,
`text_thickness` 2. All are silkscreen/cosmetic and deferred to Gate 5.

Files: `rebuild/gate4-drc-before.json`, `rebuild/gate4-drc-after.json`.

## Comparison with the original routing

| Metric | Original | Rebuild | Note |
|---|---:|---:|---|
| Total track length | 343.93 mm | 298.86 mm | lower partly because 20 links are missing and GND is poured |
| Vias | 36 | 18 | fewer, but the original distributes GND with 16 vias |
| F.Cu length | 128.8 mm | 83.9 mm | rebuild uses B.Cu more |
| B.Cu length | 215.1 mm | 215.0 mm | effectively identical |
| D+ length | 9.24 mm | 10.30 mm | 1 via each |
| D- length | 8.14 mm | 6.79 mm | 1 via each |
| **D+/D- skew** | **1.10 mm** | **3.51 mm** | **not length-matched** |
| 3.3 V length | 55.73 mm | 43.98 mm | 1 via vs 5 |
| GND | 29.08 mm + 16 vias | 0.90 mm + pours | pours replace most GND tracks |

Critical nets were routed: USB pair (with the skew above), antenna feed
`RF_ANT` 5.70 mm / `RF_LNA` 2.37 mm, crystal `XTAL_N` 2.86 / `XTAL_P` 5.12 mm,
NeoPixel 2.73 / 2.52 mm, I2C SDA 8.58 / SCL 10.84 mm.

## Renders

- `renders/gate4-3d-top.png`
- `renders/gate4-3d-bottom.png`
- `renders/gate4-2d.png` — F.Cu / B.Cu / Edge.Cuts

## Honest assessment

- The routing is **not finished**: 20 connections remain. A finished board
  would need targeted manual routing, especially the five GND pad-to-zone gaps
  and the +3V3/VBUS/IO0 layer changes.
- The USB pair is **not length-matched** (3.51 mm skew); it needs tuning.
- The lower total length is not a win — it partly reflects missing links and
  poured GND, not a better layout.
- The GND pours are electrically reasonable but their cross-layer joins are the
  main source of the remaining unconnected items.

## Human interventions

**0.**

**Stopped before Gate 5. No Gerbers or fabrication.**
