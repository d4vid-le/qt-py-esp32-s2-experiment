#!/usr/bin/env python3
"""Pilot 2: standard symbol + power symbols + PWR_FLAG + ERC."""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCP

BASE = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2/rebuild/_pilot2"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
os.makedirs(BASE, exist_ok=True)

m = MCP()
try:
    m.call("create_project", {"path": BASE, "name": "pilot2"})
    sch = f"{BASE}/pilot2.kicad_sch"
    m.call("create_schematic", {"name": "pilot2", "path": sch})
    for sym, ref, val, x, y in [
        ("Device:R", "R1", "10k", 100, 100),
        ("power:GND", "#PWR01", "GND", 115, 100),
        ("power:+3V3", "#PWR02", "+3V3", 85, 100),
        ("power:PWR_FLAG", "#FLG01", "PWR_FLAG", 130, 100),
        ("power:PWR_FLAG", "#FLG02", "PWR_FLAG", 130, 110),
    ]:
        r = m.call("add_schematic_component", {
            "schematicPath": sch, "symbol": sym, "reference": ref,
            "value": val, "position": {"x": x, "y": y}})
        print(ref, "->", r.get("success", r) if isinstance(r, dict) else r)
    print("connect:", m.call("batch_connect", {
        "schematicPath": sch,
        "connections": {
            "R1": {"1": "+3V3", "2": "GND"},
            "#PWR01": {"1": "GND"},
            "#PWR02": {"1": "+3V3"},
            "#FLG01": {"1": "GND"},
            "#FLG02": {"1": "+3V3"},
        },
        "labelType": "global_label"}))
finally:
    m.close()

r = subprocess.run([CLI, "sch", "erc", "--format", "json", "-o", f"{BASE}/erc.json", sch],
                   capture_output=True, text=True)
print("erc rc:", r.returncode, r.stdout.strip()[-160:])
net = f"{BASE}/pilot2.net"
r = subprocess.run([CLI, "sch", "export", "netlist", "-o", net, sch], capture_output=True, text=True)
print("net rc:", r.returncode)
if os.path.exists(net):
    s = open(net).read(); i = s.find("(nets")
    print(s[i:i+1200])
