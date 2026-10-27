#!/usr/bin/env python3
"""
Parse an Eagle .sch into flat netlist / BOM / pinmap CSVs.

Design notes:
  * Every part is resolved through (library, deviceset, device) to get its
    package and the gate/pin -> pad mapping from <connects>.
  * <pinref> gives us the *symbol* pin name; <connect> gives the *physical*
    pad number. Those are not the same thing and both are preserved.
  * Nets are also given a canonical signature (sorted ref.pad) so that two
    tools that auto-name nets differently can still be compared pin-for-pin.
  * Nothing here silently drops parts: skipped items are reported as warnings.
"""
import csv, hashlib, sys, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

SHEET = "1"


def load(path):
    return ET.parse(path).getroot().find("drawing/schematic")


def build_library(sch):
    """(lib, deviceset, device) -> {package, gates, connects[(gate,pin)]=pad, symbol}"""
    libs = {}
    for library in sch.findall("libraries/library"):
        lname = library.get("name")
        for ds in library.findall("devicesets/deviceset"):
            dsname = ds.get("name")
            gates = {}
            for g in ds.findall("gates/gate"):
                gates[g.get("name")] = g.get("symbol")
            for dev in ds.findall("devices/device"):
                devname = dev.get("name") or ""
                connects = {}
                for c in dev.findall("connects/connect"):
                    connects[(c.get("gate"), c.get("pin"))] = c.get("pad") or ""
                libs[(lname, dsname, devname)] = {
                    "package": dev.get("package"),
                    "prefix": ds.get("prefix"),
                    "gates": gates,
                    "connects": connects,
                    "symbols": library,
                }
    return libs


def symbol_pins(library_el):
    """symbol name -> ordered list of pin names"""
    out = {}
    for sym in library_el.findall("symbols/symbol"):
        out[sym.get("name")] = [p.get("name") for p in sym.findall("pin")]
    return out


def parse(sch_path, outdir):
    sch = load(sch_path)
    libs = build_library(sch)

    parts = {}
    warnings = []
    for p in sch.findall("parts/part"):
        name = p.get("name")
        key = (p.get("library"), p.get("deviceset"), p.get("device") or "")
        info = libs.get(key)
        if info is None:
            warnings.append(f"part {name}: no library entry for {key}")
            info = {"package": None, "prefix": None, "gates": {}, "connects": {}, "symbols": None}
        parts[name] = {
            "name": name,
            "value": p.get("value"),
            "library": p.get("library"),
            "deviceset": p.get("deviceset"),
            "device": p.get("device") or "",
            "package": info["package"],
            "prefix": info["prefix"],
            "connects": info["connects"],
            "gates": info["gates"],
            "library_el": info["symbols"],
        }

    # Nets: collect pinrefs, tolerating both net-level and segment-level refs.
    nets = defaultdict(list)
    net_numbers = {}
    seen_pinrefs = Counter()
    for sheet in sch.findall("sheets/sheet"):
        for net in sheet.findall("nets/net"):
            nname = net.get("name")
            net_numbers.setdefault(nname, net.get("class"))
            refs = list(net.findall("pinref"))
            for seg in net.findall("segment"):
                refs.extend(seg.findall("pinref"))
                for portref in seg.findall("portref"):
                    refs.append(portref)
            for pr in refs:
                part = pr.get("part")
                gate = pr.get("gate")
                pin = pr.get("pin")
                if part not in parts:
                    warnings.append(f"net {nname}: pinref to unknown part {part}")
                    continue
                seen_pinrefs[(part, gate, pin)] += 1
                nets[nname].append({"part": part, "gate": gate, "pin": pin})

    # Resolve pad numbers and pin names.
    # Eagle allows one symbol pin to map to several physical pads by listing
    # them space-separated (e.g. a castellated pad "7" plus its hole "7C").
    # Each physical pad becomes its own row so pad-level diffs are exact.
    rows = []
    multi_pad_pins = []
    for nname, conns in nets.items():
        for c in conns:
            part = parts[c["part"]]
            raw = part["connects"].get((c["gate"], c["pin"]), "")
            pads = raw.split() if raw else [""]
            if len(pads) > 1:
                multi_pad_pins.append((c["part"], c["pin"], raw))
            for pad in pads:
                rows.append({
                    "net": nname,
                    "net_class": net_numbers.get(nname) or "",
                    "ref": c["part"],
                    "gate": c["gate"],
                    "pin": c["pin"],
                    "pad": pad,
                    "value": part["value"] or "",
                    "package": part["package"] or "",
                })

    # Canonical net signature: sorted physical ref.pad (falls back to ref.pin).
    sig_for = {}
    for nname, conns in nets.items():
        keys = []
        for c in conns:
            part = parts[c["part"]]
            raw = part["connects"].get((c["gate"], c["pin"]), "")
            for pad in (raw.split() if raw else [""]):
                keys.append(f'{c["part"]}.{pad or c["pin"]}')
        sig_for[nname] = "|".join(sorted(keys))

    # Duplicate pinref check (a pin on two nets is a real error).
    dupes = {k: v for k, v in seen_pinrefs.items() if v > 1}
    for (part, gate, pin), n in dupes.items():
        warnings.append(f"pin {part}/{gate}/{pin} referenced {n} times")

    # Unconnected symbol pins: present in the symbol, absent from every net.
    used = set(seen_pinrefs)
    unconnected = []
    for name, part in parts.items():
        if part["library_el"] is None:
            continue
        syms = symbol_pins(part["library_el"])
        for gate, symname in part["gates"].items():
            for pin in syms.get(symname, []):
                if (name, gate, pin) not in used:
                    unconnected.append({"ref": name, "gate": gate, "pin": pin,
                                        "symbol": symname, "package": part["package"]})

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # netlist.csv
    rows.sort(key=lambda r: (r["net"], r["ref"], r["pad"] or r["pin"]))
    with open(outdir / "netlist.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["net", "net_class", "ref", "gate", "pin", "pad", "value", "package"])
        w.writeheader(); w.writerows(rows)

    # pinmap.csv (same data, component order + canonical signal name)
    pm = sorted(rows, key=lambda r: (r["ref"], r["pad"] or r["pin"]))
    with open(outdir / "pinmap.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ref", "package", "value", "pin", "pad", "net", "gate", "net_class"])
        w.writeheader(); w.writerows(pm)

    # bom.csv — group identical parts, exclude power/frame/fiducial symbols? No:
    # keep everything and mark the class so the filter is explicit downstream.
    def kind(p):
        # Order matters: the frame and power symbols both have no package.
        if p["deviceset"] == "FRAME_A_L":
            return "frame"
        if p["deviceset"] in ("GND", "+5V", "3.3V", "VBUS"):
            return "power_symbol"
        if p["deviceset"] == "FIDUCIAL":
            return "fiducial"
        if p["package"] is None:
            return "symbol"
        return "component"

    groups = defaultdict(list)
    for p in parts.values():
        groups[(p["value"] or "", p["deviceset"], p["device"], p["package"] or "")].append(p)

    with open(outdir / "bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "qty", "refs", "value", "deviceset", "device", "package", "library", "kind", "dnp_note"])
        for i, ((value, ds, dev, pkg), ps) in enumerate(
                sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2]))):
            refs = sorted(p["name"] for p in ps)
            k = kind(ps[0])
            note = ""
            if value.strip() in ("TBD",):
                note = "value TBD in source"
            if value.strip() == "0 ohm" or value.strip() == "0":
                note = "zero-ohm link"
            w.writerow([i + 1, len(ps), " ".join(refs), value, ds, dev, pkg,
                        ps[0]["library"], k, note])

    # nets.csv — one row per net with its canonical signature (extra, for diffing)
    with open(outdir / "nets.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["net", "net_class", "pin_count", "signature", "signature_sha1"])
        for nname in sorted(nets):
            sig = sig_for[nname]
            w.writerow([nname, net_numbers.get(nname) or "", len(nets[nname]), sig,
                        hashlib.sha1(sig.encode()).hexdigest()[:12]])

    # unconnected.csv
    with open(outdir / "unconnected.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ref", "gate", "pin", "symbol", "package"])
        w.writeheader()
        for u in sorted(unconnected, key=lambda u: (u["ref"], u["pin"])):
            w.writerow(u)

    return {
        "parts": parts, "nets": nets, "rows": rows, "warnings": warnings,
        "unconnected": unconnected, "sig_for": sig_for, "net_numbers": net_numbers,
        "kind": {n: kind(p) for n, p in parts.items()},
    }


if __name__ == "__main__":
    data = parse(sys.argv[1], sys.argv[2])
    kinds = Counter(data["kind"].values())
    print(f"parts total: {len(data['parts'])}  ({dict(kinds)})")
    print(f"nets: {len(data['nets'])}")
    print(f"pinrefs: {len(data['rows'])}")
    print(f"unconnected symbol pins: {len(data['unconnected'])}")
    print(f"warnings: {len(data['warnings'])}")
    for w in data["warnings"]:
        print("  WARN", w)
