#!/usr/bin/env python3
"""
Add 3D models to the assembled mock-up board. Visualization only.
Does not touch rebuild/ or the fabrication package.
"""
import re

ROOT = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2"
BOARD = f"{ROOT}/mockup/qt-py-esp32-s2-assembled.kicad_pcb"
D = "${KICAD10_3DMODEL_DIR}"

# ref -> (model path, offset xyz, scale xyz, rotate xyz, note)
MODELS = {
    "U$15": (f"{D}/Package_DFN_QFN.3dshapes/QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm.step",
             (0, 0, 0), (1, 1, 1), (0, 0, 0), "generic QFN56, body/pin1 aligned"),
    "X6": (f"{D}/Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "representative 16P top-mount USB-C"),
    "CONN1": (f"{D}/Connector_JST.3dshapes/JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal.step",
              (0, 0, 0), (1, 1, 1), (0, 0, 0), "JST-SH 4-pin horizontal"),
    "Q1": (f"{D}/Button_Switch_SMD.3dshapes/SW_SPST_B3U-1000P.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "representative tactile switch"),
    "Q2": (f"{D}/Button_Switch_SMD.3dshapes/SW_SPST_B3U-1000P.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "representative tactile switch"),
    "X1": (f"{D}/RF_Antenna.3dshapes/Johanson_2450AT18x100.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "Johanson 2450AT18x100 family"),
    "U1": (f"{D}/Package_TO_SOT_SMD.3dshapes/SOT-23-5.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "SOT-23-5"),
    "D1": (f"{D}/Diode_SMD.3dshapes/D_SOD-323.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "SOD-323"),
    "D2": (f"{D}/Diode_SMD.3dshapes/D_SOD-323.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "SOD-323"),
    "Y1": (f"{D}/Crystal.3dshapes/Crystal_SMD_2016-4Pin_2.0x1.6mm.step",
           (0, 0, 0), (1, 1, 1), (0, 0, 0), "2016 4-pad crystal"),
    # placeholders
    "LED1": (f"{D}/LED_SMD.3dshapes/LED_0603_1608Metric.step",
             (0, 0, 0), (1, 1, 1), (0, 0, 0), "PLACEHOLDER: 0603 LED for SK6805"),
    "GND0": (f"{D}/TestPoint.3dshapes/TestPoint_Keystone_5005-5009_Compact.step",
             (0, 0, 0), (0.45, 0.45, 0.05), (0, 0, 0), "PLACEHOLDER: flat testpoint"),
    "VBAT0": (f"{D}/TestPoint.3dshapes/TestPoint_Keystone_5005-5009_Compact.step",
              (0, 0, 0), (0.45, 0.45, 0.05), (0, 0, 0), "PLACEHOLDER: flat testpoint"),
    "SWC1": (f"{D}/TestPoint.3dshapes/TestPoint_Keystone_5005-5009_Compact.step",
             (0, 0, 0), (0.30, 0.30, 0.03), (0, 0, 0), "PLACEHOLDER: flat test pad"),
    "SWC2": (f"{D}/TestPoint.3dshapes/TestPoint_Keystone_5005-5009_Compact.step",
             (0, 0, 0), (0.30, 0.30, 0.03), (0, 0, 0), "PLACEHOLDER: flat test pad"),
    "FID1": (f"{D}/TestPoint.3dshapes/TestPoint_Keystone_5005-5009_Compact.step",
             (0, 0, 0), (0.35, 0.35, 0.02), (0, 0, 0), "PLACEHOLDER: fiducial dot"),
    "FID2": (f"{D}/TestPoint.3dshapes/TestPoint_Keystone_5005-5009_Compact.step",
             (0, 0, 0), (0.35, 0.35, 0.02), (0, 0, 0), "PLACEHOLDER: fiducial dot"),
}


def find_block(s, ref):
    i = s.find(f'(property "Reference" "{ref}"')
    if i < 0:
        return None
    start = s.rfind("\n\t(footprint", 0, i)
    depth = 0
    for k in range(start, len(s)):
        if s[k] == "(":
            depth += 1
        elif s[k] == ")":
            depth -= 1
            if depth == 0:
                return start, k + 1
    return None


def main():
    s = open(BOARD, encoding="utf-8").read()
    added = 0
    for ref, (path, off, scale, rot, note) in MODELS.items():
        loc = find_block(s, ref)
        if not loc:
            print("missing footprint", ref)
            continue
        a, b = loc
        block = s[a:b]
        if "(model " in block:
            print("already has model", ref)
            continue
        ox, oy, oz = off
        sx, sy, sz = scale
        rx, ry, rz = rot
        model = f'''\t\t(model "{path}"
\t\t\t(offset (xyz {ox} {oy} {oz}))
\t\t\t(scale (xyz {sx} {sy} {sz}))
\t\t\t(rotate (xyz {rx} {ry} {rz}))
\t\t)'''
        # insert before final closing paren of the footprint
        block = block[:-1] + model + "\n\t)"
        s = s[:a] + block + s[b:]
        added += 1
        print(f"added {ref}: {note}")
    open(BOARD, "w", encoding="utf-8").write(s)
    print(f"total models added: {added}")


if __name__ == "__main__":
    main()
