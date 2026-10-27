# Fabrication notes — QT Py ESP32-S2 reconstruction

These notes are for a hypothetical fabrication quote. **Nothing was fabricated or ordered.**

## Stackup

4-layer, 1.60 mm finished thickness, FR4. From `exports/gerbers/qt-py-esp32-s2-job.gbrjob`:

| Layer | Material | Thickness |
|---|---|---:|
| F.Cu | copper | 0.035 mm |
| F.Cu / In1.Cu dielectric | FR4 | 0.48 mm |
| In1.Cu | copper | 0.035 mm |
| In1.Cu / In2.Cu dielectric | FR4 | 0.48 mm |
| In2.Cu | copper | 0.035 mm |
| In2.Cu / B.Cu dielectric | FR4 | 0.48 mm |
| B.Cu | copper | 0.035 mm |
| Solder mask (each side) | — | 0.01 mm |

Copper weights are 1 oz (0.035 mm).

## Rules

- Minimum track width: **0.1524 mm** (6 mil)
- Minimum clearance: **0.1524 mm** (6 mil)
- Minimum drill: **0.3937 mm** (15.5 mil)
- Board outline: **17.78 × 20.701 mm** (Gerber job size 17.83 × 20.751 includes the profile line width)

## USB-C NPTH

Two non-plated holes, **0.65 mm**, at (±2.89, 2.47) in the connector package, from the
Eagle source (`<hole drill="0.65"/>`). These are inside the USB-C shell area and
must not be plated.

## Castellated edges — explicit fab note

`JP1` and `JP3` use the `1X07_CASTEL` footprints. Each position has a normal
plated through-hole pad **and** a half-hole castellation pad (`1C`…`7C`).
KiCad's stats report says `Castellated: 0`; that field is not a reliable count
for this board.

**Tell the fab:** the left and right edge pads on JP1/JP3 are **plated
castellated half-holes** and must be routed as such (half-hole plating, not
plain through-holes). The castellation pads are the `*C` pads in those
footprints.

## Population

- **C7, C9: DNP** — value TBD in the source, antenna-matching placeholders.
- **R3: 0 Ω** — series element in the crystal path, preserved from the source.
- All other 43 components populated.

## Files

- Gerbers: `exports/gerbers/` (F.Cu, In1.Cu, In2.Cu, B.Cu, masks, paste, silk, Edge.Cuts)
- Drill: `PTH.drl`, `NPTH.drl` (PTH 75 holes, NPTH 2 × 0.65 mm)
- BOM: `exports/assembly/bom.csv`
- Pick-and-place: `exports/assembly/pos.csv`
- Drill report/maps: `exports/docs/drill-report.txt`, `exports/gerbers/*-drl_map.pdf`

## Status

DRC 0 errors / 0 unconnected. USB D+/D− skew 1.093 mm. No fabrication or
ordering performed.
