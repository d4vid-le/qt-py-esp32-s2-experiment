#!/usr/bin/env python3
"""Parse a KiCad .net netlist into net,ref,pad CSV (pad = symbol pin number)."""
import csv, sys
from extract_kicad_netlist import tokenize, parse, find_all, child


def main(net_path, out_csv):
    root = parse(open(net_path, encoding="utf-8", errors="replace").read())
    nets = find_all(root, "net")
    rows = []
    for net in nets:
        name = child(net, "name")
        if not name or len(name) < 2:
            continue
        for node in find_all(net, "node"):
            ref = child(node, "ref")
            pin = child(node, "pin")
            if ref and pin and len(ref) >= 2 and len(pin) >= 2:
                rows.append({"net": name[1], "ref": ref[1], "pad": pin[1]})
    rows.sort(key=lambda r: (r["net"], r["ref"], r["pad"]))
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["net", "ref", "pad"])
        w.writeheader(); w.writerows(rows)
    print(f"nets: {len({r['net'] for r in rows})}  nodes: {len(rows)}  -> {out_csv}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
