# PCB edge post, 304. One-sided milled slot on a small cylinder.
# OD 10 mm x 15 mm. Slot floor at 10 mm. Depth 5 mm.
# Cutter is wider than the cylinder so both side ears are removed.
# 10 deg ceiling, opens outward. 1.6 mm board seats 4.5 mm in.
#
# freecadcmd this file

import os

import FreeCAD as App
import Part

OUT = os.path.dirname(os.path.abspath(__file__))
TAN10 = 0.17632698070846498

R = 5.0
H = 15.0
Z_FLOOR = 10.0
SLOT_W = 12.0
SLOT_DEPTH = 5.0
GAP_BACK = 1.51
X_BACK = R - SLOT_DEPTH  # 0, the center plane


def ceil_z(x):
    return Z_FLOOR + GAP_BACK + (x - X_BACK) * TAN10


cyl = Part.makeCylinder(R, H)
cut_pts = [
    App.Vector(X_BACK, 0, Z_FLOOR),
    App.Vector(R + 1.0, 0, Z_FLOOR),
    App.Vector(R + 1.0, 0, ceil_z(R + 1.0)),
    App.Vector(X_BACK, 0, ceil_z(X_BACK)),
]
cut_face = Part.Face(Part.makePolygon(cut_pts + [cut_pts[0]]))
cutter = cut_face.extrude(App.Vector(0, SLOT_W, 0))
cutter.translate(App.Vector(0, -SLOT_W / 2, 0))
solid = cyl.cut(cutter)
solid = solid.removeSplitter()
if not solid.isValid() or len(solid.Solids) != 1:
    raise SystemExit("solid invalid: %s" % len(solid.Solids))


def inside(x, y, z):
    return solid.isInside(App.Vector(x, y, z), 1e-7, True)


# Side ear at y=4.5 used to stay; the slot must be empty there.
if inside(2, 4.5, 11) or inside(2, 0, 11) or not inside(2, 0, 14):
    raise SystemExit("slot edges still closed")

step = os.path.join(OUT, "pcb-edge-post.step")
solid.exportStep(step)

# Side profile of the metal through the slot centerline.
# X = distance from the far side, Y = height. Axis of the cylinder at X = 5.
profile = [
    (0.0, 0.0),
    (10.0, 0.0),
    (10.0, Z_FLOOR),
    (5.0, Z_FLOOR),
    (5.0, ceil_z(X_BACK)),
    (10.0, ceil_z(R)),
    (10.0, H),
    (0.0, H),
]
dxf = os.path.join(OUT, "pcb-edge-post-profile.dxf")
loop = profile + [profile[0]]
lines = [
    "0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4",
    "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES",
]
for (x0, y0), (x1, y1) in zip(loop, loop[1:]):
    lines += [
        "0", "LINE", "8", "SIDE",
        "10", f"{x0:.4f}", "20", f"{y0:.4f}", "30", "0",
        "11", f"{x1:.4f}", "21", f"{y1:.4f}", "31", "0",
    ]
# Plan: circle and the slot rectangle, offset in Y so it does not sit on the side view.
ox, oy = 20.0, 0.0
lines += [
    "0", "CIRCLE", "8", "PLAN",
    "10", f"{ox:.4f}", "20", f"{oy:.4f}", "30", "0",
    "40", f"{R:.4f}",
]
rect = [
    (ox + X_BACK, oy - SLOT_W / 2),
    (ox + R, oy - SLOT_W / 2),
    (ox + R, oy + SLOT_W / 2),
    (ox + X_BACK, oy + SLOT_W / 2),
]
rect.append(rect[0])
for (x0, y0), (x1, y1) in zip(rect, rect[1:]):
    lines += [
        "0", "LINE", "8", "PLAN",
        "10", f"{x0:.4f}", "20", f"{y0:.4f}", "30", "0",
        "11", f"{x1:.4f}", "21", f"{y1:.4f}", "31", "0",
    ]
lines += ["0", "ENDSEC", "0", "EOF"]
with open(dxf, "w", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

seat_x = X_BACK + (1.6 - GAP_BACK) / TAN10
print("step", step)
print("volume_mm3 %.1f" % solid.Volume)
print("mouth_gap %.3f" % (ceil_z(R) - Z_FLOOR))
print("bite %.3f" % (R - seat_x))
