#!/usr/bin/env python3
"""
Extract the QT Py-specific footprints from the imported KiCad board into
rebuild/qt-py.pretty, preserving pad names and geometry exactly.

Source: reference/imported-kicad/qt-py-esp32-s2-viz.kicad_pcb
        (same geometry as the authoritative import; only UNDEFINED graphics
         were remapped to Dwgs.User so the file is loadable)
"""
import os, re, sys

ROOT = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2"
SRC = f"{ROOT}/reference/imported-kicad/qt-py-esp32-s2-viz.kicad_pcb"
OUT = f"{ROOT}/rebuild/qt-py.pretty"

# name in board -> name in library (filename-safe)
WANTED = {
    "SOD-323_MINI": "SOD-323_MINI",
    "CRYSTAL_2X1.6": "CRYSTAL_2X1.6",
    "QFN56_7X7": "QFN56_7X7",
    "1X07_CASTEL": "1X07_CASTEL",
    "JST_SH4_SKINNY": "JST_SH4_SKINNY",
    "BTN_KMR2_4.6X2.8": "BTN_KMR2_4.6X2.8",
    "TESTPOINT_MINUS_1X3MM": "TESTPOINT_MINUS_1X3MM",
    "TESTPOINT_PLUS_1X3MM": "TESTPOINT_PLUS_1X3MM",
    "B1,27": "B1_27",
    "USB_C_CUSB31-CFM2AX-01-X": "USB_C_CUSB31-CFM2AX-01-X",
    "SOT23-5": "SOT23-5",
    "SK6805_1515": "SK6805_1515",
    "ANT_2450AT18B100": "ANT_2450AT18B100",
    "FIDUCIAL_1MM": "FIDUCIAL_1MM",
}


def block(text, name):
    start = text.find(f'(footprint "{name}"')
    if start < 0:
        raise SystemExit(f"footprint {name} not found")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise SystemExit(f"unbalanced block for {name}")


def clean(raw, old, new):
    lines = raw.splitlines()
    out = []
    depth = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        # compute depth at the start of the line
        start_depth = depth
        depth += line.count("(") - line.count(")")
        if idx == 0:
            out.append(f'(footprint "{new}"')
            out.append("\t(version 20260206)")
            out.append('\t(generator "pcbnew")')
            continue
        if start_depth == 1 and (stripped.startswith("(at ") or stripped.startswith("(uuid ")
                                 or stripped.startswith("(path ")):
            continue
        out.append(line)
    text = "\n".join(out) + "\n"
    text = re.sub(r'(\(property "Reference" ")[^"]*(")',
                  lambda m: m.group(1) + "REF**" + m.group(2), text)
    text = re.sub(r'(\(property "Value" ")[^"]*(")',
                  lambda m: m.group(1) + new + m.group(2), text)
    return text


def main():
    os.makedirs(OUT, exist_ok=True)
    src = open(SRC, encoding="utf-8").read()
    for old, new in WANTED.items():
        raw = block(src, old)
        open(f"{OUT}/{new}.kicad_mod", "w", encoding="utf-8").write(clean(raw, old, new))
        print(f"  {old:32} -> {new}.kicad_mod")

    table = '''(fp_lib_table
  (version 7)
  (lib (name "qt-py")(type "KiCad")(uri "${KIPRJMOD}/qt-py.pretty")(options "")(descr "QT Py ESP32-S2 footprints extracted from the imported Eagle board"))
)
'''
    open(f"{ROOT}/rebuild/fp-lib-table", "w", encoding="utf-8").write(table)
    print(f"wrote {len(WANTED)} footprints + fp-lib-table")


if __name__ == "__main__":
    main()
