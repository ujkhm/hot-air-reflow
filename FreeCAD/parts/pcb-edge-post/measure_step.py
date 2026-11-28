import os

import FreeCAD as App
import Part

step = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcb-edge-post.step")
shape = Part.Shape()
shape.read(step)
bb = shape.BoundBox
print("xmin %.4f xmax %.4f" % (bb.XMin, bb.XMax))
print("ymin %.4f ymax %.4f" % (bb.YMin, bb.YMax))
print("zmin %.4f zmax %.4f" % (bb.ZMin, bb.ZMax))
print("dx %.4f dy %.4f dz %.4f" % (bb.XLength, bb.YLength, bb.ZLength))
print("solids", len(shape.Solids))
# cylinder radius from the round face
for i, f in enumerate(shape.Faces):
    if f.Surface.TypeId == "Part::GeomCylinder":
        print("cyl radius", round(f.Surface.Radius, 4))
        break
