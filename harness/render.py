#!/usr/bin/env python3
"""Render a routed OpenROAD database to PNG: every placed cell and every routed wire segment, drawn to scale.
Usage: render.py <routed.odb> <out.png> [px_per_um] [x0 y0 x1 y1 crop in um]"""
import sys
from openroad import odb
from PIL import Image, ImageDraw
src, dst = sys.argv[1], sys.argv[2]
ppu = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
db = odb.dbDatabase.create(); odb.read_db(db, src)
blk = db.getChip().getBlock(); dbu = blk.getDbUnitsPerMicron()
die = blk.getDieArea()
crop = [float(v) for v in sys.argv[4:8]] if len(sys.argv) >= 8 else [0, 0, die.xMax() / dbu, die.yMax() / dbu]
W, H = int((crop[2] - crop[0]) * ppu), int((crop[3] - crop[1]) * ppu)
def X(v): return (v / dbu - crop[0]) * ppu
def Y(v): return H - (v / dbu - crop[1]) * ppu
BG = (13, 17, 23)
img = Image.new("RGB", (W, H), BG)
dr = ImageDraw.Draw(img, "RGBA")
def cell_color(m):
    if "df" in m: return (61, 214, 195, 120)                    # flip-flops
    if "xor" in m or "xnor" in m: return (108, 168, 255, 70)    # adder tree
    if "buf" in m or "inv" in m: return (242, 166, 90, 110)     # buffers, clock tree
    return (139, 150, 163, 55)                                  # other logic
n_inst = 0
for inst in blk.getInsts():
    bb = inst.getBBox(); n_inst += 1
    dr.rectangle([X(bb.xMin()) + .5, Y(bb.yMax()) + .5, X(bb.xMax()) - .5, Y(bb.yMin()) - .5], fill=cell_color(inst.getMaster().getName()))
LAYER = {"Metal1": (150, 160, 172, 150), "Metal2": (61, 214, 195, 215), "Metal3": (242, 166, 90, 215),
         "Metal4": (108, 168, 255, 215), "Metal5": (232, 107, 208, 215)}
segs = {k: [] for k in LAYER}; vias = []; length = {k: 0.0 for k in LAYER}
import re
deftxt = open(sys.argv[1].replace(".odb", ".def")).read()
nets = deftxt[deftxt.index("\nNETS "):deftxt.index("\nEND NETS")]
WIDTH = {"Metal1": 160, "Metal2": 200, "Metal3": 200, "Metal4": 200, "Metal5": 200}       # default wire widths, DBU
tok = re.compile(r"\(|\)|[^\s()]+")
for m in re.finditer(r"(?:ROUTED|NEW)\s+(\S+)([^\n]*)", nets):
    ln, t = m.group(1), tok.findall(m.group(2))
    pts = []; i = 0; px = py = None; on_layer = True
    while i < len(t):
        if t[i] == "RECT":                                   # patch rectangle relative to the last point
            dx0, dy0, dx1, dy1 = (int(v) for v in t[i + 2:i + 6]); i += 7
            if ln in segs and px is not None: segs[ln].append((px + dx0, py + dy0, px + dx1, py + dy1))
            continue
        if t[i] == "(":
            j = t.index(")", i); xs, ys = t[i + 1], t[i + 2]
            x = px if xs == "*" else int(xs); y = py if ys == "*" else int(ys)
            if px is not None and on_layer and ln in segs:
                h = WIDTH[ln] // 2
                segs[ln].append((min(px, x) - h, min(py, y) - h, max(px, x) + h, max(py, y) + h))
                length[ln] += (abs(x - px) + abs(y - py)) / dbu
            px, py = x, y; i = j + 1; continue
        if t[i].startswith(("Via", "TopVia")):
            vias.append((px, py)); on_layer = False            # path leaves this layer at a via
        i += 1
for ln in ("Metal1", "Metal2", "Metal3", "Metal4", "Metal5"):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for x0, y0, x1, y1 in segs[ln]:
        a, b, c, e = X(x0), Y(y1), X(x1), Y(y0)
        if c - a < 1: c = a + 1
        if e - b < 1: e = b + 1
        od.rectangle([a, b, c, e], fill=LAYER[ln])
    img.paste(ov, (0, 0), ov)
dr = ImageDraw.Draw(img, "RGBA")
if ppu >= 12:
    r = max(1.0, 0.1 * ppu)
    for vx, vy in vias: dr.rectangle([X(vx) - r, Y(vy) - r, X(vx) + r, Y(vy) + r], fill=(230, 237, 243, 230))
for bt in blk.getBTerms():
    for bp in bt.getBPins():
        for box in bp.getBoxes():
            dr.rectangle([X(box.xMin()) - 1, Y(box.yMax()) - 1, X(box.xMax()) + 1, Y(box.yMin()) + 1], fill=(230, 237, 243, 255))
img.save(dst)
clock_bufs = sum(1 for i in blk.getInsts() if i.getName().startswith("clkbuf") or i.getName().startswith("clkload"))
print(f"instances {n_inst}  die {die.xMax()/dbu:.1f} x {die.yMax()/dbu:.1f} um  vias {len(vias)}  segments {sum(len(v) for v in segs.values())}")
print("wire length um:", {k: round(v) for k, v in length.items()}, "total", round(sum(length.values())))
