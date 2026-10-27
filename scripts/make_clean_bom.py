#!/usr/bin/env python3
"""
Split the raw Eagle BOM into:
  design/bom_clean.csv    physical components only, with DNP flags
  design/bom_symbols.csv  power symbols, fiducials, frame (audit only)

Rules from the Gate 1 human review:
  * C7 / C9 stay TBD and are marked DNP. Do not guess values.
  * R3 (0R) is preserved and flagged as a source quirk.
"""
import csv, sys

DNP = {"C7", "C9"}
NOTE = {
    "C7": "TBD in source; DNP; antenna match placeholder",
    "C9": "TBD in source; DNP; antenna match placeholder",
    "R3": "0R in series with crystal XTAL_N; source quirk, preserved",
}


def main(src, clean_out, symbols_out):
    rows = list(csv.DictReader(open(src, newline="")))
    comp = [r for r in rows if r["kind"] == "component"]
    other = [r for r in rows if r["kind"] != "component"]

    with open(clean_out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "qty", "refs", "value", "device", "package",
                    "library", "populate", "dnp", "note"])
        for i, r in enumerate(comp, 1):
            refs = r["refs"].split()
            dnp = any(x in DNP for x in refs)
            notes = sorted({NOTE[x] for x in refs if x in NOTE})
            if dnp and not notes:
                notes = ["DNP"]
            w.writerow([i, r["qty"], r["refs"], r["value"].strip(), r["deviceset"],
                        r["package"], r["library"], "no" if dnp else "yes",
                        "yes" if dnp else "no", "; ".join(notes)])

    with open(symbols_out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["qty", "refs", "deviceset", "kind"])
        for r in other:
            w.writerow([r["qty"], r["refs"], r["deviceset"], r["kind"]])

    n_comp = sum(int(r["qty"]) for r in comp)
    print(f"physical BOM : {n_comp} components in {len(comp)} groups -> {clean_out}")
    print(f"non-physical : {sum(int(r['qty']) for r in other)} parts in {len(other)} groups -> {symbols_out}")
    print(f"DNP groups   : {sum(1 for r in comp if any(x in DNP for x in r['refs'].split()))}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
