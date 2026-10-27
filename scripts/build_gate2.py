#!/usr/bin/env python3
"""
Gate 2 — rebuild the QT Py ESP32-S2 schematic from the ground-truth netlist.

Strategy:
  * 12 custom symbols whose PIN NUMBERS equal the Eagle physical pad names
    (1..57 for the ESP32, A1B12 for USB-C, A/A'/B/B' for buttons, ...).
    That makes the KiCad netlist directly comparable to the pad-level ground truth.
  * R / C / L use KiCad's Device library (pins 1,2 already match).
  * Every net is built with labels: global labels for power rails, local labels
    for signals. No Eagle import, no kicad-sch-api.
  * 28 no-connect flags cover every pin that is unconnected in the source.

Run: python3 scripts/build_gate2.py
"""
import csv, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCP

ROOT = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2"
REBUILD = f"{ROOT}/rebuild"
LIBNAME = "qt-py-esp32-s2"
LIBFILE = f"{REBUILD}/{LIBNAME}.kicad_sym"
PRO = f"{REBUILD}/{LIBNAME}.kicad_pro"
SCH = f"{REBUILD}/{LIBNAME}.kicad_sch"
NET = f"{REBUILD}/{LIBNAME}.net"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

POWER = {"GND", "+3V3", "+5V", "VBUS"}
REF_RENAME = {"GND": "GND0", "VBAT": "VBAT0"}
RENAME = {"!RESET": "RESET_N", "N$2": "RF_LNA", "N$3": "RF_ANT",
          "N$5": "XTAL_N_R", "N$6": "XTAL_P", "N$7": "XTAL_N",
          "3.3V": "+3V3"}


# ----------------------------------------------------------------- symbol data
def esp32_pins():
    rows = list(csv.DictReader(open(f"{ROOT}/design/u15-pinmap.csv")))
    out = []
    for r in rows:
        n = r["eagle_symbol_pin"]
        if n == "VDD_SPI":
            t = "power_out"
        elif n.startswith(("VDDA", "VDD3P3", "GND")):
            t = "power_in"
        elif n == "CHIP_PU":
            t = "input"
        elif n in ("XTAL_N", "XTAL_P", "LNA_IN"):
            t = "passive"
        else:
            t = "bidirectional"
        out.append((n, r["eagle_pad"], t))
    return out


CUSTOM = {
    "ESP32-S2FN4R2": (esp32_pins, "U"),
    "USB_C": ([("CC1", "A5", "bidirectional"), ("SBU1", "A8", "passive"),
               ("CC2", "B5", "bidirectional"), ("SBU2", "B8", "passive"),
               ("D+", "A6", "bidirectional"), ("D+", "B6", "bidirectional"),
               ("D-", "A7", "bidirectional"), ("D-", "B7", "bidirectional"),
               ("VBUS", "A4B9", "power_in"), ("VBUS", "B4A9", "power_in"),
               ("GND", "A1B12", "power_in"), ("GND", "B1A12", "power_in")], "X"),
    "HEADER_1X7": ([(f"{i}", f"{i}", "passive") for i in range(1, 8)] +
                   [(f"{i}C", f"{i}C", "passive") for i in range(1, 8)], "JP"),
    "JST_SH4": ([("GND", "1", "passive"), ("V+", "2", "passive"),
                 ("SDA", "3", "passive"), ("SCL", "4", "passive"),
                 ("MT1", "MT1", "passive"), ("MT2", "MT2", "passive")], "CONN"),
    "TACT_4": ([("P", "A", "passive"), ("P1", "A'", "passive"),
                ("S", "B", "passive"), ("S1", "B'", "passive")], "Q"),
    "DIODE_A_C": ([("A", "A", "passive"), ("C", "C", "passive")], "D"),
    "CRYSTAL_2PIN": ([("1", "1", "passive"), ("2", "3", "passive")], "Y"),
    "ANTENNA_FP": ([("P$1", "FP", "passive")], "X"),
    "TESTPOINT_P": ([("P$1", "P$1", "passive")], "TP"),
    "TESTPAD_TP": ([("TP", "TP", "passive")], "TP"),
    "WS2812B": ([("DI", "1", "input"), ("VDD", "2", "power_in"),
                 ("DO", "3", "output"), ("GND", "4", "power_in")], "LED"),
    "VREG_5": ([("IN", "1", "power_in"), ("GND", "2", "power_in"),
                ("EN", "3", "input"), ("P4", "4", "passive"),
                ("OUT", "5", "power_out")], "U"),
}

# component mapping: deviceset + package -> (symbol, footprint)
def symbol_for(device, package):
    table = {
        ("CAP_CERAMIC", "_0402NO"): ("Device:C", "Capacitor_SMD:C_0402_1005Metric"),
        ("CAP_CERAMIC", "0805-NO"): ("Device:C", "Capacitor_SMD:C_0805_2012Metric"),
        ("RESISTOR", "_0402NO"): ("Device:R", "Resistor_SMD:R_0402_1005Metric"),
        ("INDUCTOR", "_0402"): ("Device:L", "Inductor_SMD:L_0402_1005Metric"),
        ("DIODE", "SOD-323_MINI"): (f"{LIBNAME}:DIODE_A_C", "qt-py:SOD-323_MINI"),
        ("CRYSTAL", "CRYSTAL_2X1.6"): (f"{LIBNAME}:CRYSTAL_2PIN", "qt-py:CRYSTAL_2X1.6"),
        ("ESP32-S2", "QFN56_7X7"): (f"{LIBNAME}:ESP32-S2FN4R2", "qt-py:QFN56_7X7"),
        ("HEADER-1X7", "1X07_CASTEL"): (f"{LIBNAME}:HEADER_1X7", "qt-py:1X07_CASTEL"),
        ("STEMMA_I2C", "JST_SH4_SKINNY"): (f"{LIBNAME}:JST_SH4", "qt-py:JST_SH4_SKINNY"),
        ("SWITCH_TACT_SMT", "BTN_KMR2_4.6X2.8"): (f"{LIBNAME}:TACT_4", "qt-py:BTN_KMR2_4.6X2.8"),
        ("TESTPOINT", "TESTPOINT_MINUS_1X3MM"): (f"{LIBNAME}:TESTPOINT_P", "qt-py:TESTPOINT_MINUS_1X3MM"),
        ("TESTPOINT", "TESTPOINT_PLUS_1X3MM"): (f"{LIBNAME}:TESTPOINT_P", "qt-py:TESTPOINT_PLUS_1X3MM"),
        ("TP", "B1,27"): (f"{LIBNAME}:TESTPAD_TP", "qt-py:B1_27"),
        ("USB_C", "USB_C_CUSB31-CFM2AX-01-X"): (f"{LIBNAME}:USB_C", "qt-py:USB_C_CUSB31-CFM2AX-01-X"),
        ("VREG_SOT23-5", "SOT23-5"): (f"{LIBNAME}:VREG_5", "qt-py:SOT23-5"),
        ("WS2812B", "SK6805_1515"): (f"{LIBNAME}:WS2812B", "qt-py:SK6805_1515"),
        ("ANTENNA_JOHANSON_2450AT18B100", "ANT_2450AT18B100"): (f"{LIBNAME}:ANTENNA_FP", "qt-py:ANT_2450AT18B100"),
    }
    if (device, package) not in table:
        raise KeyError(f"no symbol mapping for {device}/{package}")
    return table[(device, package)]


def two_side(items, body_w=10.16, pitch=2.54):
    n = len(items)
    left = items[:(n + 1) // 2]
    right = items[(n + 1) // 2:]
    height = max(len(left), len(right)) * pitch + 5.08
    top = height / 2 - 2.54
    pins = []
    for i, (name, num, typ) in enumerate(left):
        pins.append({"name": name, "number": num, "type": typ,
                     "at": {"x": -(body_w / 2 + 2.54), "y": top - i * pitch, "angle": 0}})
    for i, (name, num, typ) in enumerate(right):
        pins.append({"name": name, "number": num, "type": typ,
                     "at": {"x": (body_w / 2 + 2.54), "y": top - i * pitch, "angle": 180}})
    return pins, [{"x1": -body_w / 2, "y1": -height / 2,
                   "x2": body_w / 2, "y2": height / 2, "fill": "background"}]


def one_pin(item):
    name, num, typ = item
    return ([{"name": name, "number": num, "type": typ,
              "at": {"x": 2.54, "y": 0, "angle": 180}}],
            [{"x1": -1.27, "y1": -1.27, "x2": 1.27, "y2": 1.27, "fill": "background"}])


# ----------------------------------------------------------------------- build
def clean():
    os.makedirs(REBUILD, exist_ok=True)
    for pattern in (f"{LIBNAME}.kicad_pro", f"{LIBNAME}.kicad_sch", f"{LIBNAME}.kicad_pcb",
                    f"{LIBNAME}.kicad_prl", f"{LIBNAME}.kicad_sym", f"{LIBNAME}.net",
                    "sym-lib-table", "fp-lib-table", "erc.json"):
        p = f"{REBUILD}/{pattern}"
        if os.path.exists(p):
            os.remove(p)
    for d in ("_pilot", "_pilot2"):
        shutil.rmtree(f"{REBUILD}/{d}", ignore_errors=True)


def main():
    clean()
    m = MCP()
    try:
        print("== project ==")
        print(m.call("create_project", {"path": REBUILD, "name": LIBNAME}))

        print("== custom symbols ==")
        for name, (fn, prefix) in CUSTOM.items():
            items = fn() if callable(fn) else fn
            if len(items) == 1:
                pins, rects = one_pin(items[0])
            else:
                w = 30.48 if name == "ESP32-S2FN4R2" else (15.24 if len(items) > 6 else 10.16)
                pins, rects = two_side(items, body_w=w)
            r = m.call("create_symbol", {
                "libraryPath": LIBFILE, "name": name, "referencePrefix": prefix,
                "description": f"QT Py ESP32-S2 reconstruction: {name}",
                "datasheet": "~", "overwrite": True,
                "pins": pins, "rectangles": rects})
            print(f"  {name}: {len(pins)} pins -> {r}")
        print(m.call("register_symbol_library", {
            "libraryPath": LIBFILE, "libraryName": LIBNAME,
            "scope": "project", "projectPath": REBUILD}))

        print("== schematic ==")
        print(m.call("create_schematic", {"name": LIBNAME, "path": SCH}))
        # A2 sheet so 91 symbols fit on one page
        s = open(SCH).read().replace('(paper "A4")', '(paper "A2")')
        open(SCH, "w").write(s)

        print("== components ==")
        comps = []
        for row in csv.DictReader(open(f"{ROOT}/design/bom_clean.csv")):
            sym, fp = symbol_for(row["device"], row["package"])
            for ref in row["refs"].split():
                comps.append({"ref": ref, "sym": sym, "val": row["value"].strip(),
                              "fp": fp, "dnp": row["dnp"] == "yes"})
        # ESP32 gets its own area; everything else a 6-column grid
        for c in comps:
            c["ref"] = REF_RENAME.get(c["ref"], c["ref"])
        for i, c in enumerate(comps):
            if c["ref"] == "U$15":
                c["x"], c["y"] = 400, 150
            else:
                idx = i if i < 6 * 8 else i
                c["x"] = 30 + (idx % 6) * 40
                c["y"] = 30 + (idx // 6) * 30
            r = m.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": c["sym"], "reference": c["ref"],
                "value": c["val"], "footprint": c["fp"],
                "position": {"x": c["x"], "y": c["y"]}})
            print(f"  {c['ref']:6} {c['sym']:28} {str(r)[:60]}")

        print("== power symbols + flags ==")
        power_specs = ([("power:GND", "GND")] * 32 +
                       [("power:+3V3", "+3V3")] * 10 +
                       [("power:+5V", "+5V")] * 3 +
                       [("power:VBUS", "VBUS")])
        pwr = []
        for i, (sym, val) in enumerate(power_specs, 1):
            ref = f"#PWR{i:03d}"
            x = 500 + ((i - 1) % 3) * 14
            y = 30 + ((i - 1) // 3) * 14
            m.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": sym, "reference": ref,
                "value": val, "position": {"x": x, "y": y}})
            pwr.append({"ref": ref, "val": val})
        flags = []
        for i, (net, glob) in enumerate([("GND", True), ("+5V", True), ("VBUS", True),
                                         ("VDD3P3", False), ("NEOPIX_PWR", False)], 1):
            ref = f"#FLG{i:02d}"
            m.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": "power:PWR_FLAG", "reference": ref,
                "value": "PWR_FLAG", "position": {"x": 540, "y": 30 + i * 12}})
            flags.append({"ref": ref, "net": net, "global": glob})
        print(f"  {len(pwr)} power symbols, {len(flags)} PWR_FLAGs")

        print("== connections ==")
        rows = list(csv.DictReader(open(f"{ROOT}/design/netlist_original.csv")))
        signal_conn, power_conn = {}, {}
        for r in rows:
            if not r["pad"]:
                continue
            net = RENAME.get(r["net"], r["net"])
            target = power_conn if net in POWER else signal_conn
            target.setdefault(REF_RENAME.get(r["ref"], r["ref"]), {})[r["pad"]] = net
        # power symbols and flags
        for p in pwr:
            power_conn.setdefault(p["ref"], {})["1"] = p["val"]
        for f in flags:
            target = power_conn if f["global"] else signal_conn
            target.setdefault(f["ref"], {})["1"] = f["net"]

        def chunked(conn, label_type, size=10):
            items = [(ref, pin, net) for ref, pins in conn.items() for pin, net in pins.items()]
            total = (len(items) + size - 1) // size
            for i in range(0, len(items), size):
                part = {}
                for ref, pin, net in items[i:i + size]:
                    part.setdefault(ref, {})[pin] = net
                r = m.call("batch_connect", {"schematicPath": SCH, "connections": part,
                                             "labelType": label_type})
                print(f"    {label_type} chunk {i // size + 1}/{total}: {r}")
        chunked(signal_conn, "label")
        chunked(power_conn, "global_label", size=20)

        print("== no-connects ==")
        nc = []
        for r in csv.DictReader(open(f"{ROOT}/design/u15-pinmap.csv")):
            if r["net"] == "(unconnected)":
                nc.append({"componentRef": "U$15", "pinName": r["eagle_pad"]})
        nc += [{"componentRef": "LED1", "pinName": "3"},
               {"componentRef": "U1", "pinName": "4"},
               {"componentRef": "X6", "pinName": "A8"},
               {"componentRef": "X6", "pinName": "B8"}]
        r3 = m.call("batch_add_no_connects", {"schematicPath": SCH, "pins": nc})
        print("  ", r3 if isinstance(r3, str) else (r3.get("message"), len(r3.get("failed", []))))
        if isinstance(r3, dict) and r3.get("failed"):
            print(r3["failed"][:10])

        print("== summary ==")
        text = open(SCH).read()
        print("  lib_symbols:", text.count(f'(symbol "{LIBNAME}:'))
        print("  components :", len(comps), "power:", len(pwr), "flags:", len(flags))
    finally:
        m.close()


if __name__ == "__main__":
    main()
