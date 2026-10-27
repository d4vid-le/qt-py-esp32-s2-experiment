#!/usr/bin/env python3
"""
Extract a pad-level netlist from a KiCad .kicad_pcb with no dependencies.

Why not pcbnew? In this environment the SWIG LoadBoard() returns None or raises
even for valid boards, so we read the S-expression directly. That is KiCad's own
file format, not a re-implementation of Eagle.

Emits: net,ref,pad,value,footprint
"""
import csv, sys

WS = " \t\r\n"
DELIM = "()"


def tokenize(text):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in DELIM:
            out.append(c); i += 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n:
                if text[j] == "\\":
                    buf.append(text[j + 1]); j += 2
                elif text[j] == '"':
                    break
                else:
                    buf.append(text[j]); j += 1
            out.append(("str", "".join(buf))); i = j + 1
        elif c in WS:
            i += 1
        else:
            j = i
            while j < n and text[j] not in WS and text[j] not in DELIM:
                j += 1
            out.append(("atom", text[i:j])); i = j
    return out


def parse(text):
    stack = [[]]
    for tok in tokenize(text):
        if tok == "(":
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif tok == ")":
            if len(stack) > 1:
                stack.pop()
        else:
            stack[-1].append(tok[1])
    return stack[0][0] if stack[0] else []


def find_all(node, name):
    found = []
    if isinstance(node, list) and node and node[0] == name:
        found.append(node)
    if isinstance(node, list):
        for c in node:
            if isinstance(c, list):
                found.extend(find_all(c, name))
    return found


def child(node, name):
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def prop(fp, key):
    for c in fp:
        if isinstance(c, list) and c and c[0] == "property" and len(c) >= 3 and c[1] == key:
            return c[2]
    for c in fp:
        if isinstance(c, list) and c and c[0] == "fp_text" and len(c) >= 3 and c[1] == key.lower():
            return c[2]
    return ""


def main(path, out_csv):
    root = parse(open(path, encoding="utf-8", errors="replace").read())
    rows, fps = [], find_all(root, "footprint")
    for fp in fps:
        ref, val = prop(fp, "Reference"), prop(fp, "Value")
        lib = fp[1] if len(fp) > 1 and isinstance(fp[1], str) else ""
        for pad in find_all(fp, "pad"):
            if len(pad) < 2 or not isinstance(pad[1], str):
                continue
            net = child(pad, "net")
            if not net:
                continue
            # KiCad 10 writes (net "NAME"); older files use (net CODE "NAME").
            name = net[2] if len(net) >= 3 else (net[1] if len(net) == 2 else "")
            if not name:
                continue
            rows.append({"net": name, "ref": ref, "pad": pad[1],
                         "value": val, "footprint": lib})
    rows.sort(key=lambda r: (r["net"], r["ref"], r["pad"]))
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["net", "ref", "pad", "value", "footprint"])
        w.writeheader(); w.writerows(rows)
    print(f"footprints parsed : {len(fps)}")
    print(f"pad/net rows      : {len(rows)}")
    print(f"unique pads       : {len({(r['ref'], r['pad']) for r in rows})}")
    print(f"distinct nets     : {len({r['net'] for r in rows})}")
    print(f"wrote             : {out_csv}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
