#!/usr/bin/env python3
"""
Gate 3 board finishing:
  * copy the Edge.Cuts outline from the imported board (8 segments, 17.78 x 20.701)
  * add the two FIDUCIAL_1MM footprints at the original positions
  * set Eagle-derived design rules and net classes in the .kicad_pro
"""
import json, re, sys

ROOT = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2"
SRC = f"{ROOT}/reference/imported-kicad/qt-py-esp32-s2-viz.kicad_pcb"
BOARD = f"{ROOT}/rebuild/qt-py-esp32-s2.kicad_pcb"
PRO = f"{ROOT}/rebuild/qt-py-esp32-s2.kicad_pro"

MIL = 0.0254
CLEAR = 6 * MIL          # mdWireWire
WIDTH = 6 * MIL          # msWidth
DRILL = 15.5 * MIL       # msDrill
ANNULAR = 0.25 * DRILL   # rvViaOuter
VIA = DRILL + 2 * ANNULAR
EDGE = 10 * MIL          # mdCopperDimension
HOLE = 8 * MIL           # mdDrill


def blocks(text, tag, filter_text=None):
    out, i = [], 0
    while True:
        i = text.find(f"({tag}\n", i)
        if i < 0:
            return out
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    b = text[i:j + 1]
                    if not filter_text or filter_text in b:
                        out.append(b)
                    i = j
                    break


def main():
    src = open(SRC, encoding="utf-8").read()
    board = open(BOARD, encoding="utf-8").read()

    edge = [b for b in blocks(src, "gr_line", "Edge.Cuts")] + \
           [b for b in blocks(src, "gr_arc", "Edge.Cuts")]
    print(f"Edge.Cuts segments: {len(edge)}")

    fids = []
    for ref in ("U$6", "U$8"):
        i = src.find(f'(footprint "FIDUCIAL_1MM"')
        while i >= 0:
            depth = 0
            for j in range(i, len(src)):
                if src[j] == "(":
                    depth += 1
                elif src[j] == ")":
                    depth -= 1
                    if depth == 0:
                        b = src[i:j + 1]
                        if f'(property "Reference" "{ref}"' in b:
                            b = b.replace('(footprint "FIDUCIAL_1MM"',
                                          '(footprint "qt-py:FIDUCIAL_1MM"')
                            b = b.replace(f'(property "Reference" "{ref}"',
                                          f'(property "Reference" "FID{len(fids)+1}"')
                            fids.append(b)
                        i = j
                        break
            i = src.find(f'(footprint "FIDUCIAL_1MM"', j + 1)
    print(f"fiducials: {len(fids)}")

    insert = "\n\n".join(edge + fids)
    idx = board.rstrip().rfind(")")
    board = board[:idx] + "\n" + insert + "\n" + board[idx:]
    open(BOARD, "w", encoding="utf-8").write(board)

    # design rules
    d = json.load(open(PRO))
    rules = d["board"]["design_settings"]["rules"]
    rules.update({
        "min_clearance": round(CLEAR, 4),
        "min_track_width": round(WIDTH, 4),
        "min_via_diameter": round(VIA, 4),
        "min_via_annular_width": round(ANNULAR, 4),
        "min_through_hole_diameter": round(DRILL, 4),
        "min_copper_edge_clearance": round(EDGE, 4),
        "min_hole_clearance": round(HOLE, 4),
        "min_hole_to_hole": round(HOLE, 4),
    })
    default = d["net_settings"]["classes"][0]
    default.update({"clearance": round(CLEAR, 4), "track_width": round(WIDTH, 4),
                    "via_diameter": round(VIA, 4), "via_drill": round(DRILL, 4)})
    d["net_settings"]["classes"] = [default,
        {"name": "Power", "clearance": round(CLEAR, 4), "track_width": 0.254,
         "via_diameter": round(VIA, 4), "via_drill": round(DRILL, 4),
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2,
         "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6,
         "bus_width": 12, "line_style": 0, "priority": 2147483647,
         "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)",
         "tuning_profile": ""},
        {"name": "GND", "clearance": round(CLEAR, 4), "track_width": 0.254,
         "via_diameter": round(VIA, 4), "via_drill": round(DRILL, 4),
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2,
         "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6,
         "bus_width": 12, "line_style": 0, "priority": 2147483647,
         "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)",
         "tuning_profile": ""}]
    d["net_settings"]["netclass_patterns"] = [
        {"netclass": "GND", "pattern": "GND"},
        {"netclass": "Power", "pattern": "+5V"},
        {"netclass": "Power", "pattern": "+3V3"},
        {"netclass": "Power", "pattern": "VBUS"},
    ]
    json.dump(d, open(PRO, "w"), indent=2)
    print(f"rules: clearance={CLEAR:.4f} width={WIDTH:.4f} via={VIA:.4f}/{DRILL:.4f} edge={EDGE:.4f}")


if __name__ == "__main__":
    main()
