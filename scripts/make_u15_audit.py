#!/usr/bin/env python3
"""
Build the U$15 (ESP32-S2) pad audit:
  Eagle symbol pin -> Eagle pad -> datasheet pin/name -> net -> function

Joins three independent things:
  * Eagle schematic symbol + device connects (library truth)
  * ESP32-S2 datasheet Table 2, parsed from the PDF
  * our pad-level netlist (connectivity truth)

Usage:
  make_u15_audit.py <eagle.sch> <datasheet_pins.csv> <netlist_original.csv> <out.csv>
"""
import csv, re, sys
import xml.etree.ElementTree as ET

REF = "U$15"


def normalize(pin):
    base = pin.split("@")[0]
    m = re.fullmatch(r"IO(\d+)", base)
    if m:
        return "GPIO" + m.group(1)
    if base == "MTD0":
        return "MTDO"
    return base


def main(sch_path, ds_csv, netlist_csv, out_csv):
    sch = ET.parse(sch_path).getroot().find("drawing/schematic")
    lib = [l for l in sch.findall("libraries/library") if l.get("name") == "adafruit_wireless"][0]
    ds = [d for d in lib.findall("devicesets/deviceset") if d.get("name") == "ESP32-S2"][0]
    dev = ds.findall("devices/device")[0]

    connects = sorted((int(c.get("pad")), c.get("pin")) for c in dev.findall("connects/connect"))

    dsrows = {int(r["pin"]): r for r in csv.DictReader(open(ds_csv))}
    nets = {}
    for r in csv.DictReader(open(netlist_csv)):
        if r["ref"] == REF and r["pad"]:
            nets[int(r["pad"])] = r["net"]

    rows, mismatches = [], 0
    for pad, eagle_pin in connects:
        norm = normalize(eagle_pin)
        ds = dsrows.get(pad, {})
        ds_name = ds.get("name", "")
        ok = norm == ds_name
        if not ok:
            mismatches += 1
        note = []
        if "@" in eagle_pin:
            note.append("duplicate symbol name disambiguated by @N suffix")
        if eagle_pin != norm:
            note.append(f"nomenclature {eagle_pin} -> {norm}")
        if pad == 57:
            note.append("exposed pad (EPAD)")
        rows.append({
            "eagle_symbol_pin": eagle_pin,
            "eagle_pad": pad,
            "datasheet_pin": pad,
            "datasheet_name": ds_name,
            "net": nets.get(pad, "(unconnected)"),
            "function": ds.get("function", ""),
            "name_check": "match" if ok else "MISMATCH",
            "note": "; ".join(note),
        })

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["eagle_symbol_pin", "eagle_pad", "datasheet_pin",
                                          "datasheet_name", "net", "function",
                                          "name_check", "note"])
        w.writeheader(); w.writerows(rows)

    print(f"pads audited : {len(rows)}")
    print(f"name matches : {sum(1 for r in rows if r['name_check']=='match')}")
    print(f"mismatches   : {mismatches}")
    print(f"connected    : {sum(1 for r in rows if r['net'] != '(unconnected)')}")
    print(f"unconnected  : {sum(1 for r in rows if r['net'] == '(unconnected)')}")
    print(f"wrote        : {out_csv}")
    for r in rows:
        if r["name_check"] != "match":
            print("  MISMATCH", r)
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
