#!/usr/bin/env python3
"""
Independent check: compare the schematic-derived netlist (via pads) with the
.brd signal/contactref table. These are two different files that must agree.
"""
import csv, sys, xml.etree.ElementTree as ET
from collections import defaultdict


def sch_pads(netlist_csv):
    """net -> {(ref, pad)} using only rows that have a real pad."""
    nets = defaultdict(set)
    with open(netlist_csv) as f:
        for r in csv.DictReader(f):
            if r["pad"]:
                nets[r["net"]].add((r["ref"], r["pad"]))
    return nets


def brd_pads(brd_path):
    root = ET.parse(brd_path).getroot()
    board = root.find("drawing/board")
    nets = defaultdict(set)
    for sig in board.findall("signals/signal"):
        for c in sig.findall("contactref"):
            nets[sig.get("name")].add((c.get("element"), c.get("pad")))
    elements = {e.get("name"): e.get("package") for e in board.findall("elements/element")}
    return nets, elements


def main(netlist_csv, brd_path):
    s = sch_pads(netlist_csv)
    b, elems = brd_pads(brd_path)

    print(f".sch nets with pads : {len(s)}   ({sum(len(v) for v in s.values())} pads)")
    print(f".brd signals        : {len(b)}   ({sum(len(v) for v in b.values())} contacts)")

    only_s = sorted(set(s) - set(b))
    only_b = sorted(set(b) - set(s))
    print(f"\nnets only in .sch: {len(only_s)} {only_s}")
    print(f"nets only in .brd: {len(only_b)} {only_b}")

    mismatches = 0
    for n in sorted(set(s) & set(b)):
        if s[n] != b[n]:
            mismatches += 1
            miss = sorted(s[n] - b[n])
            extra = sorted(b[n] - s[n])
            print(f"\nNET {n}: MISMATCH")
            print(f"  in .sch not .brd: {miss}")
            print(f"  in .brd not .sch: {extra}")
    print(f"\ncommon nets compared: {len(set(s) & set(b))}  mismatched: {mismatches}")

    # Board elements with no schematic counterpart
    sch_refs = {ref for v in s.values() for ref, _ in v}
    missing = sorted(set(elems) - sch_refs)
    if missing:
        print(f"\nboard elements absent from schematic netlist: {missing}")
    return 1 if (only_s or only_b or mismatches) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
