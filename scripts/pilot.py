#!/usr/bin/env python3
"""Pilot: prove custom symbol -> schematic -> labels -> netlist export."""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCP

BASE = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2/rebuild/_pilot"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
os.makedirs(BASE, exist_ok=True)

m = MCP()
try:
    print("project:", m.call("create_project", {"path": BASE, "name": "pilot"}))
    lib = f"{BASE}/pilot.kicad_sym"
    print("symbol:", m.call("create_symbol", {
        "libraryPath": lib, "name": "Test2", "referencePrefix": "U",
        "description": "pilot 2-pin", "overwrite": True,
        "pins": [
            {"name": "A", "number": "1", "type": "passive", "at": {"x": -7.62, "y": 0, "angle": 0}},
            {"name": "B", "number": "2", "type": "passive", "at": {"x": 7.62, "y": 0, "angle": 180}},
        ],
        "rectangles": [{"x1": -5.08, "y1": -2.54, "x2": 5.08, "y2": 2.54}],
    }))
    print("register:", m.call("register_symbol_library", {
        "libraryPath": lib, "libraryName": "pilot", "scope": "project", "projectPath": BASE}))
    sch = f"{BASE}/pilot.kicad_sch"
    print("schematic:", m.call("create_schematic", {"name": "pilot", "path": sch}))
    print("component:", m.call("add_schematic_component", {
        "schematicPath": sch, "symbol": "pilot:Test2", "reference": "U1",
        "value": "test", "position": {"x": 100, "y": 100}}))
    print("connect:", m.call("batch_connect", {
        "schematicPath": sch,
        "connections": {"U1": {"1": "NET_A", "2": "NET_B"}}}))
finally:
    m.close()

print("--- lib_symbols ---")
s = open(sch).read()
print("lib_symbols present:", "(lib_symbols" in s, "| symbol defs:", s.count('(symbol "pilot:'))
print("--- netlist ---")
net = f"{BASE}/pilot.net"
r = subprocess.run([CLI, "sch", "export", "netlist", "-o", net, sch], capture_output=True, text=True)
print("export rc:", r.returncode, r.stdout.strip()[-200:], r.stderr.strip()[-200:])
if os.path.exists(net):
    print(open(net).read()[:1600])
