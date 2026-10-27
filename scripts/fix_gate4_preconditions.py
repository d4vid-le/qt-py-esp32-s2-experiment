#!/usr/bin/env python3
"""
Gate 4 preconditions:
  * replace the testpoint no-net copper polygon with an equivalent pad
  * close the testpoint courtyard
  * remove ${TP_SIGNAL_NAME} from the testpad footprint
  * update the four placed instances in the board
"""
import re, uuid

ROOT = "/Users/dblab/Development/projects/kicad/projects/qt-py-esp32-s2"
PRETTY = f"{ROOT}/rebuild/qt-py.pretty"
BOARD = f"{ROOT}/rebuild/qt-py-esp32-s2.kicad_pcb"

TP_TEMPLATE = '''(footprint "{name}"
	(version 20260206)
	(generator "pcbnew")
	(layer "B.Cu")
	(descr "QT Py 1x3 mm test point; copper polygon converted to an equivalent pad")
	(property "Reference" "{ref}"
		(at 0.889 -0.127 270)
		(unlocked yes)
		(layer "B.SilkS")
		(effects
			(font
				(size 0.692831 0.692831)
				(thickness 0.119969)
			)
			(justify right mirror)
		)
	)
	(property "Value" "{value}"
		(at 0.889 -0.889 270)
		(unlocked yes)
		(layer "B.Fab")
		(effects
			(font
				(size 0.369824 0.369824)
				(thickness 0.036576)
			)
			(justify right mirror)
		)
	)
	(property "Datasheet" ""
		(at 0 0 270)
		(unlocked yes)
		(layer "B.Fab")
		(hide yes)
		(effects (font (size 1.27 1.27)) (justify mirror))
	)
	(property "Description" ""
		(at 0 0 270)
		(unlocked yes)
		(layer "B.Fab")
		(hide yes)
		(effects (font (size 1.27 1.27)) (justify mirror))
	)
	(duplicate_pad_numbers_are_jumpers no)
	(pad "P$1" smd roundrect
		(at 0 0)
		(size 2.9762 1.5762)
		(layers "B.Cu" "B.Mask")
		(roundrect_rratio 0.25)
{net}\t\t(solder_mask_margin 0.0508)
		(thermal_bridge_angle 0)
		(uuid "{pad_uuid}")
	)
	(fp_rect
		(start -1.64 -0.94)
		(end 1.64 0.94)
		(stroke (width 0.05) (type solid))
		(fill no)
		(layer "B.CrtYd")
		(uuid "{crt_uuid}")
	)
	(embedded_fonts no)
)
'''


def strip_blocks(text, start_marker):
    """Remove every parenthesised block beginning with start_marker."""
    out, i = [], 0
    while True:
        j = text.find(start_marker, i)
        if j < 0:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:j])
        depth = 0
        for k in range(j, len(text)):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    i = k + 1
                    break


def fix_b1_27():
    p = f"{PRETTY}/B1_27.kicad_mod"
    s = open(p).read()
    s = strip_blocks(s, '(fp_text user "${TP_SIGNAL_NAME}"')
    open(p, "w").write(s)
    print("B1_27: removed ${TP_SIGNAL_NAME}")


def write_tp(name, ref, value, net=""):
    body = TP_TEMPLATE.format(name=name, ref=ref, value=value,
                              net=net, pad_uuid=str(uuid.uuid4()),
                              crt_uuid=str(uuid.uuid4()))
    return body


def main():
    fix_b1_27()

    # library versions (no net)
    for name in ("TESTPOINT_MINUS_1X3MM", "TESTPOINT_PLUS_1X3MM"):
        open(f"{PRETTY}/{name}.kicad_mod", "w").write(write_tp(name, "REF**", name))
        print(f"{name}: polygon -> pad, courtyard closed")

    # board instances: replace blocks, preserve placement and net
    s = open(BOARD).read()
    for ref, fp, net, x, y, rot in [
        ("GND0", "TESTPOINT_MINUS_1X3MM", "GND", "6.985", "-18.8722", "270"),
        ("VBAT0", "TESTPOINT_PLUS_1X3MM", "VBAT", "10.795", "-18.8722", "270"),
    ]:
        start = s.find(f'(footprint "qt-py:{fp}"')
        while start >= 0:
            depth = 0
            for k in range(start, len(s)):
                if s[k] == "(":
                    depth += 1
                elif s[k] == ")":
                    depth -= 1
                    if depth == 0:
                        block = s[start:k + 1]
                        if f'(property "Reference" "{ref}"' in block:
                            new = write_tp(fp, ref, fp, net=f'\t\t(net "{net}")\n')
                            new = new.replace(f'(footprint "{fp}"',
                                              f'(footprint "qt-py:{fp}"')
                            new = new.replace('(layer "B.Cu")',
                                              f'(layer "B.Cu")\n\t\t(at {x} {y} {rot})', 1)
                            s = s[:start] + new + s[k + 1:]
                            print(f"{ref}: instance replaced")
                            break
                if k == len(s) - 1:
                    break
            start = s.find(f'(footprint "qt-py:{fp}"', start + 1)
    open(BOARD, "w").write(s)


if __name__ == "__main__":
    main()
