#!/usr/bin/env python3
"""
Replace one net's routing with the reference board's geometry.
Usage: replace_net_ref.py <board_net> [reference_net]
Deletes the net's tracks/vias via the MCP server, then appends the reference
F.Cu/B.Cu segments and vias for that net.
"""
import os, re, sys, uuid
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCP

ROOT = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2"
BOARD = f"{ROOT}/rebuild/qt-py-esp32-s2.kicad_pcb"
SRC = f"{ROOT}/reference/imported-kicad/qt-py-esp32-s2-viz.kicad_pcb"


def main():
    board_net = sys.argv[1]
    ref_net = sys.argv[2] if len(sys.argv) > 2 else board_net

    m = MCP()
    try:
        m.call("open_board", {"boardPath": BOARD})
        r = m.call("delete_trace", {"net": board_net, "includeVias": True})
        print("delete:", r.get("message") if isinstance(r, dict) else r)
    finally:
        m.close()

    src = open(SRC, encoding="utf-8").read()
    blocks = []
    for m in re.finditer(r'\(segment\s*\n\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(width ([-\d.]+)\)\s*\n\s*\(layer "([^"]+)"\)\s*\n\s*\(net "([^"]+)"\)', src):
        if m.group(7) != ref_net or m.group(6) not in ("F.Cu", "B.Cu"):
            continue
        blocks.append(f'''(segment
		(start {m.group(1)} {m.group(2)})
		(end {m.group(3)} {m.group(4)})
		(width {m.group(5)})
		(layer "{m.group(6)}")
		(net "{board_net}")
		(uuid "{uuid.uuid4()}")
	)''')
    for m in re.finditer(r'\(via\s*\n\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(size ([-\d.]+)\)\s*\n\s*\(drill ([-\d.]+)\)[\s\S]{0,120}?\(net "([^"]+)"\)', src):
        if m.group(5) != ref_net:
            continue
        drill = m.group(4)
        if float(drill) < 0.3937:
            drill = "0.4"
        blocks.append(f'''(via
		(at {m.group(1)} {m.group(2)})
		(size {m.group(3)})
		(drill {drill})
		(layers "F.Cu" "B.Cu")
		(net "{board_net}")
		(uuid "{uuid.uuid4()}")
	)''')

    s = open(BOARD, encoding="utf-8").read()
    idx = s.rstrip().rfind(")")
    s = s[:idx] + "\n" + "\n".join(blocks) + "\n" + s[idx:]
    open(BOARD, "w", encoding="utf-8").write(s)
    print(f"added {len(blocks)} reference blocks for {ref_net} -> {board_net}")


if __name__ == "__main__":
    main()
