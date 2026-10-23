# -*- coding: utf-8 -*-
"""Dump named-solid coordinates for the reflow-oven model.

FreeCAD GUI: select objects, or select nothing for the whole document, then run.
Writes coords.txt beside the FCStd and copies the same text to the clipboard.

Command line (ASCII launcher, so a non-ASCII script path is not on the command line):
    freecadcmd C:\\Users\\LTY-PC\\AppData\\Local\\reflow-oven\\run_dump.py

With no document open, the newest .FCStd in the project's FreeCAD folder is used.
"""

import os
import sys

import FreeCAD as App

EXPECTED = (
    "axis_origin",
    "axis_px",
    "axis_py",
    "gap_upper",
    "gap_lower",
    "plenum_upper",
    "plenum_lower",
    "plate_upper",
    "plate_lower",
    "return_a",
    "return_b",
    "impeller_in",
    "heater",
    "exhaust",
    "board",
    "holes_upper",
    "holes_lower",
)
AXIS_NAMES = ("axis_origin", "axis_px", "axis_py")
TOUCH_MM = 0.5
PROJECT_ROOT = r"E:\hot-air-reflow"
FREECAD_DIR = os.path.join(PROJECT_ROOT, "FreeCAD")


def ident(obj):
    label = getattr(obj, "Label", "") or ""
    if label and label != obj.Name:
        return "%s (%s)" % (label, obj.Name)
    return obj.Name


def key_name(obj):
    label = getattr(obj, "Label", "") or ""
    if label in EXPECTED:
        return label
    if obj.Name in EXPECTED:
        return obj.Name
    return label or obj.Name


def shape_of(obj):
    if not hasattr(obj, "Shape"):
        return None
    try:
        sh = obj.Shape
    except Exception:
        return None
    if sh is None or sh.isNull() or len(sh.Vertexes) == 0:
        return None
    return sh


def global_point(obj):
    sh = shape_of(obj)
    if sh is not None and len(sh.Vertexes) == 1 and len(sh.Faces) == 0 and len(sh.Solids) == 0:
        return sh.Vertexes[0].Point
    if all(hasattr(obj, attr) for attr in ("X", "Y", "Z", "Placement")):
        return obj.Placement.multVec(App.Vector(float(obj.X), float(obj.Y), float(obj.Z)))
    if hasattr(obj, "Placement"):
        return obj.Placement.Base
    return None


def frame_matrix(origin, px_pt, py_pt):
    px = px_pt - origin
    py = py_pt - origin
    if px.Length < 1e-6 or py.Length < 1e-6:
        return None
    px.normalize()
    py = py - px * py.dot(px)
    if py.Length < 1e-6:
        return None
    py.normalize()
    pz = px.cross(py)
    m = App.Matrix()
    m.A11, m.A12, m.A13 = px.x, px.y, px.z
    m.A21, m.A22, m.A23 = py.x, py.y, py.z
    m.A31, m.A32, m.A33 = pz.x, pz.y, pz.z
    m.A14 = -px.dot(origin)
    m.A24 = -py.dot(origin)
    m.A34 = -pz.dot(origin)
    return m


def box_gap(a, b):
    dx = max(0.0, a.XMin - b.XMax, b.XMin - a.XMax)
    dy = max(0.0, a.YMin - b.YMax, b.YMin - a.YMax)
    dz = max(0.0, a.ZMin - b.ZMax, b.ZMin - a.ZMax)
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def fmt_box(bb):
    return "xmin %.3f  xmax %.3f  ymin %.3f  ymax %.3f  zmin %.3f  zmax %.3f" % (
        bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax,
    )


def copy_clipboard(text):
    try:
        import FreeCADGui as Gui
        if not Gui.ActiveDocument:
            return False
    except Exception:
        return False
    for importer in (
        "PySide6.QtGui",
        "PySide2.QtGui",
        "PySide.QtGui",
    ):
        try:
            module = __import__(importer, fromlist=["QGuiApplication"])
            app = module.QGuiApplication.instance()
            if app is None:
                return False
            clipboard = app.clipboard()
            if clipboard is None:
                return False
            clipboard.setText(text)
            return True
        except Exception:
            continue
    return False


def selected_objects():
    try:
        import FreeCADGui as Gui
    except Exception:
        return []
    try:
        if not Gui.ActiveDocument:
            return []
        return list(Gui.Selection.getSelection())
    except Exception:
        return []


def newest_fcstd():
    if not os.path.isdir(FREECAD_DIR):
        return ""
    found = [
        os.path.join(FREECAD_DIR, name)
        for name in os.listdir(FREECAD_DIR)
        if name.lower().endswith(".fcstd")
    ]
    if not found:
        return ""
    return max(found, key=os.path.getmtime)


def open_target():
    try:
        import FreeCADGui as Gui
        if Gui.ActiveDocument is not None:
            return App.ActiveDocument, False
    except Exception:
        pass
    if App.ActiveDocument is not None and App.ActiveDocument.FileName:
        return App.ActiveDocument, False
    path = os.environ.get("REFLOW_FCSTD", "")
    if not path:
        for arg in sys.argv[1:]:
            if arg.lower().endswith((".fcstd", ".step", ".stp")):
                path = arg
                break
    if not path:
        path = newest_fcstd()
    if not path or not os.path.isfile(path):
        App.Console.PrintError("dump_coords: no .FCStd in %s\n" % FREECAD_DIR)
        return None, False
    return App.openDocument(path), True


def main():
    doc, opened = open_target()
    if doc is None:
        App.Console.PrintError("dump_coords: no document\n")
        return

    by_key = {}
    geometric = []
    for obj in doc.Objects:
        sh = shape_of(obj)
        if sh is None:
            continue
        geometric.append(obj)
        by_key[key_name(obj)] = obj

    origin = global_point(by_key["axis_origin"]) if "axis_origin" in by_key else None
    px_pt = global_point(by_key["axis_px"]) if "axis_px" in by_key else None
    py_pt = global_point(by_key["axis_py"]) if "axis_py" in by_key else None
    matrix = None
    if origin is not None and px_pt is not None and py_pt is not None:
        matrix = frame_matrix(origin, px_pt, py_pt)

    picked = selected_objects()
    picked_ids = set(id(obj) for obj in picked)
    targets = picked if picked else geometric

    lines = []
    lines.append("file: %s" % (doc.FileName or "(unsaved)"))
    lines.append("unit: mm")
    if matrix is None:
        lines.append("frame: document axes (axis_origin / axis_px / axis_py missing or colinear)")
    else:
        lines.append("frame: axis_origin, axis_px, axis_py")
    if picked:
        lines.append("selection: %s" % ", ".join(ident(obj) for obj in picked))
    else:
        lines.append("selection: (none, whole document)")
    lines.append("")

    boxes = {}
    for obj in geometric:
        sh = obj.Shape
        if matrix is not None:
            sh = sh.copy()
            sh.transformShape(matrix)
        boxes[obj.Name] = sh.BoundBox

    def touches(obj):
        found = []
        box = boxes[obj.Name]
        for other in geometric:
            if other is obj:
                continue
            if box_gap(box, boxes[other.Name]) > TOUCH_MM:
                continue
            dist, _, _ = obj.Shape.distToShape(other.Shape)
            if dist <= TOUCH_MM:
                found.append((dist, other))
        found.sort(key=lambda item: (item[0], ident(item[1])))
        return found

    for obj in targets:
        kind = "solid" if len(obj.Shape.Solids) else ("face" if len(obj.Shape.Faces) else "point")
        lines.append("%s  %s  %s" % (ident(obj), kind, fmt_box(boxes[obj.Name])))
        if kind == "point" or obj.Name.startswith("holes_") or key_name(obj).startswith("holes_"):
            sh = obj.Shape.copy()
            if matrix is not None:
                sh.transformShape(matrix)
            pts = sh.Vertexes
            lines.append("  points: %d" % len(pts))
            limit = 40
            for vertex in pts[:limit]:
                p = vertex.Point
                lines.append("  %.3f %.3f %.3f" % (p.x, p.y, p.z))
            if len(pts) > limit:
                lines.append("  ... %d more" % (len(pts) - limit))
        pairs = touches(obj)
        if pairs:
            lines.append("  touches: " + ", ".join("%s %.3f" % (ident(other), dist) for dist, other in pairs))
        else:
            lines.append("  touches: (none within %.1f mm)" % TOUCH_MM)
        lines.append("")

    present = set(by_key)
    missing = [name for name in EXPECTED if name not in present]
    if missing:
        lines.append("missing: " + ", ".join(missing))
    else:
        lines.append("missing: (none)")

    text = "\n".join(lines) + "\n"
    out_dir = os.path.dirname(doc.FileName) if doc.FileName else FREECAD_DIR
    if not out_dir:
        out_dir = FREECAD_DIR
    out_path = os.path.join(out_dir, "coords.txt")
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(text)

    copied = copy_clipboard(text)
    App.Console.PrintMessage(text)
    if copied:
        App.Console.PrintMessage("dump_coords: copied to clipboard and wrote %s\n" % out_path)
    else:
        App.Console.PrintMessage("dump_coords: wrote %s (no clipboard in this session)\n" % out_path)

    if opened:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
