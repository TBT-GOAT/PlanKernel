# -*- coding: utf-8 -*-
import scriptcontext as sc
import Rhino.Geometry as rg
import Rhino
import rhinoscriptsyntax as rs

#create layer "CONVERTED LINE SEGMENTS"
layer_name = "CONVERTED LINE SEGMENTS"
layer_index = sc.doc.Layers.FindByFullPath(layer_name, True)
if layer_index < 0:
    layer = Rhino.DocObjects.Layer()
    layer.Name = layer_name
    layer_index = sc.doc.Layers.Add(layer)

title= "Input file"
INPUT_FILE= rs.OpenFileName(title)


# Read segments from file
with open(INPUT_FILE, "r") as f:
    SEGMENTS = f.readlines()

for line in SEGMENTS:
    line = line.strip()
    if not line:
        continue

    parts = line.split()
    if len(parts) < 5:
        print("Invalid line: " + line)
        continue

    x1 = float(parts[1])
    y1 = float(parts[2])
    x2 = float(parts[3])
    y2 = float(parts[4])

    pt1 = rg.Point3d(x1, y1, 0.0)
    pt2 = rg.Point3d(x2, y2, 0.0)

    attr = Rhino.DocObjects.ObjectAttributes()
    attr.LayerIndex = layer_index
    sc.doc.Objects.AddLine(rg.Line(pt1, pt2), attr)

sc.doc.Views.Redraw()
print("All segments drawn successfully.")