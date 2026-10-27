#!/usr/bin/env python3
"""
Diff two pad-level netlists by connectivity signature, not net name.

Signature = frozenset of (ref, pad) on a net. Tools auto-name nets differently
(Eagle N$2 vs KiCad Net-(U15-Pad2)), so names are reported but never matched on.

Usage: diff_netlists.py A.csv B.csv [--label-a NAME] [--label-b NAME]
CSV columns required: net,ref,pad
Exit code 0 = identical connectivity, 1 = differences.
"""
import argparse, csv, sys
from collections import defaultdict


def read(path):
    nets = defaultdict(set)
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        if not {"net", "ref", "pad"} <= set(r.fieldnames or []):
            raise SystemExit(f"{path}: need net,ref,pad columns")
        for row in r:
            if row["net"] and row["pad"]:
                nets[row["net"]].add((row["ref"], row["pad"]))
    return nets


def by_signature(nets):
    sig = defaultdict(list)
    for name, members in nets.items():
        sig[frozenset(members)].append(name)
    return sig


def fmt(members):
    return " ".join(f"{r}.{p}" for r, p in sorted(members))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    args = ap.parse_args()

    a, b = read(args.a), read(args.b)
    sa, sb = by_signature(a), by_signature(b)

    print(f"{args.label_a}: {len(a)} nets, {sum(len(v) for v in a.values())} pad connections")
    print(f"{args.label_b}: {len(b)} nets, {sum(len(v) for v in b.values())} pad connections")

    only_a = [s for s in sa if s not in sb]
    only_b = [s for s in sb if s not in sa]
    common = [s for s in sa if s in sb]

    print(f"\nmatched net signatures : {len(common)}")
    print(f"only in {args.label_a:12}: {len(only_a)}")
    print(f"only in {args.label_b:12}: {len(only_b)}")

    if only_a:
        print(f"\n--- only in {args.label_a} ---")
        for s in sorted(only_a, key=lambda x: (-len(x), sorted(x))):
            print(f"  [{'/'.join(sorted(sa[s]))}] ({len(s)}) {fmt(s)}")
    if only_b:
        print(f"\n--- only in {args.label_b} ---")
        for s in sorted(only_b, key=lambda x: (-len(x), sorted(x))):
            print(f"  [{'/'.join(sorted(sb[s]))}] ({len(s)}) {fmt(s)}")

    # Name mapping for matched signatures (informational, not a failure)
    renamed = []
    for s in common:
        na, nb = sorted(sa[s]), sorted(sb[s])
        if set(na) != set(nb):
            renamed.append((na, nb))
    if renamed:
        print("\n--- same connectivity, different net names ---")
        for na, nb in sorted(renamed, key=lambda x: x[0]):
            print(f"  {', '.join(na):24} -> {', '.join(nb)}")

    diff = bool(only_a or only_b)
    print(f"\nRESULT: {'DIFFERENT' if diff else 'IDENTICAL CONNECTIVITY'}")
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
