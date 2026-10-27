#!/usr/bin/env python3
"""Apply the imported board's placement to the rebuild board, then verify it."""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCP

ROOT = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2"
SRC = f"{ROOT}/reference/imported-kicad/qt-py-esp32-s2-viz.kicad_pcb"
BOARD = f"{ROOT}/rebuild/qt-py-esp32-s2.kicad_pcb"
CSV_OUT = f"{ROOT}/design/gate3-placement-source.csv"


def parse_board(path):
    s = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'\(footprint "([^"]+)"\s*\n\s*\(layer "([^"]+)"\)', s):
        name, layer = m.group(1), m.group(2)
        # find the first (at ...) after the header
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', s[m.end():m.end() + 400])
        ref = re.search(r'\(property "Reference" "([^"]+)"', s[m.end():m.end() + 3000])
        if at and ref:
            out[ref.group(1)] = {"footprint": name, "layer": layer,
                                 "x": float(at.group(1)), "y": float(at.group(2)),
                                 "rot": float(at.group(3) or 0)}
    return out


def main():
    src = parse_board(SRC)
    dst = parse_board(BOARD)
    refs = [r for r in dst if r in src]
    print(f"source footprints: {len(src)}  rebuild: {len(dst)}  matched: {len(refs)}")

    with open(CSV_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ref", "footprint", "x", "y", "rotation", "layer"])
        for r in sorted(refs):
            s = src[r]
            w.writerow([r, s["footprint"], s["x"], s["y"], s["rot"], s["layer"]])

    m = MCP()
    try:
        m.call("open_board", {"boardPath": BOARD})
        moves = {r: {"x": src[r]["x"], "y": src[r]["y"], "unit": "mm",
                     "rotation": src[r]["rot"], "layer": src[r]["layer"]} for r in refs}
        for i in range(0, len(moves), 12):
            part = dict(list(moves.items())[i:i + 12])
            r = m.call("batch_move_components", {"moves": part, "save": True})
            print(f"  chunk {i//12+1}: {r.get('success') if isinstance(r, dict) else r}")
    finally:
        m.close()

    # verify
    after = parse_board(BOARD)
    bad = []
    for ref in sorted(refs):
        a, b = src[ref], after.get(ref, {})
        if (round(a["x"], 3), round(a["y"], 3), round(a["rot"], 1), a["layer"]) != \
           (round(b.get("x", 0), 3), round(b.get("y", 0), 3), round(b.get("rot", 0), 1), b.get("layer")):
            bad.append((ref, a, b))
    print(f"verified {len(refs) - len(bad)}/{len(refs)} placements")
    for x in bad[:10]:
        print("  MISMATCH", x)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
