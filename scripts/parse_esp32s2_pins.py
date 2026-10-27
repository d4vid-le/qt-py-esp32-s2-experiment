#!/usr/bin/env python3
"""
Parse Table 2 (Pin Description) from the ESP32-S2 Family Datasheet PDF.

Pages 12-14 in datasheet V1.1. The PDF extracts as a flat line stream, so a pin
record is detected as:  NAME line, then a 1-2 digit pin number line, then type,
then power domain, then function lines until the next record.

Usage: parse_esp32s2_pins.py <datasheet.pdf> <out.csv>
"""
import csv, re, sys
import fitz

NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
NUM_RE = re.compile(r"^\d{1,2}$")
STOP = {"Espressif Systems", "Submit Documentation Feedback",
        "ESP32-S2 Family Datasheet V1.1", "Pin Definitions", "Name", "No.",
        "Type", "Power domain", "Function", "Table 2: Pin Description"}


def main(pdf, out_csv):
    doc = fitz.open(pdf)
    lines = []
    for page in (11, 12, 13):  # 0-based -> pages 12,13,14
        for ln in doc[page].get_text().splitlines():
            ln = ln.strip()
            if ln and ln not in STOP and not ln.startswith("Espressif"):
                lines.append(ln)

    recs, i = [], 0
    while i < len(lines) - 1:
        expected = len(recs) + 1
        if (NAME_RE.match(lines[i]) and NUM_RE.match(lines[i + 1])
                and int(lines[i + 1]) == expected):
                name, num = lines[i], int(lines[i + 1])
                j = i + 2
                rtype = lines[j] if j < len(lines) else ""
                j += 1
                domain = lines[j] if j < len(lines) else ""
                j += 1
                func = []
                while j < len(lines) - 1 and not (NAME_RE.match(lines[j]) and NUM_RE.match(lines[j + 1])):
                    line = lines[j]
                    noise = (line.isdigit() or line in ("Pin Definitions", "Pins")
                             or line.startswith("Cont") or re.match(r"^\d+\.\s*Pin", line))
                    if not noise:
                        func.append(line)
                    j += 1
                func_text = "; ".join(func)
                func_text = func_text.split("Note:")[0].rstrip("; ").strip()
                recs.append({"pin": num, "name": name, "type": rtype,
                             "power_domain": domain, "function": func_text})
                i = j
                continue
        i += 1

    recs.sort(key=lambda r: r["pin"])
    missing = [n for n in range(1, 58) if n not in {r["pin"] for r in recs}]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pin", "name", "type", "power_domain", "function"])
        w.writeheader(); w.writerows(recs)
    print(f"parsed {len(recs)} pins -> {out_csv}")
    if missing:
        print("MISSING:", missing)
    for r in recs[:6]:
        print(" ", r)
    return 0 if len(recs) == 57 and not missing else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
