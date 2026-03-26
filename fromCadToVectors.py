
# -*- coding: utf-8 -*-

import Rhino.Geometry as rg
import scriptcontext as sc
import rhinoscriptsyntax as rs
import Rhino
import math

#Configuration

DECIMAL_PLACES       = 5
COORD_SEPARATOR      = " "
SPLIT_LENGTH = 100
INCLUDE_HIDDEN       = False
DEDUPLICATE_SEGMENTS = True

LAYERS_TO_EXPORT = [
    u"\u58c1",                                      # 壁 wall
    u"\u67f1",                                      # 柱 pillar
    u"\u30ac\u30e9\u30b9",                          # ガラス glass
    u"\u30d1\u30fc\u30c6\u30a3\u30b7\u30e7\u30f3",  # パーティション partition wall
    u"\u5e8a\u9762\u5916\u5f62\u7dda",              # 床面外形線 floor boundary line
]

# Functions

def get_doc_tolerance():
    return sc.doc.ModelAbsoluteTolerance


def get_layer_name(obj): # Returns the name of the layer of the object
    return sc.doc.Layers[obj.Attributes.LayerIndex].Name.strip()


def should_export(obj): # Returns True if the layer of the object is in the whitelist
    return get_layer_name(obj) in LAYERS_TO_EXPORT


def is_nonzero_z(pt, tol): # Returns True if the Z coordinate is not zero
    return abs(pt.Z) > tol


def discretize_curve(curve, tol, warnings, obj_id, split_num=16): # Discretizes a curve into N segments 
    segments = []

    def get_points(n_segments, curve):
        points = []
        for i in range(n_segments + 1):
            fraction = i / float(n_segments)
            success, t = curve.NormalizedLengthParameter(fraction)
            if not success:
                warnings.append("  WARNING [" + str(obj_id) + "]: point at fraction " + str(round(fraction, 3)) + " could not be calculated.")
                continue
            points.append(curve.PointAt(t))

        for i in range(len(points) - 1):
            segments.append((points[i], points[i + 1]))
        return segments

    length = curve.GetLength()
    
    if length is None:
        return segments
        
    if length < tol:
        if not curve.IsClosed: #if a curve DOES NOT starts and ends at the same point, IF IT DOESN'T form a continuous, enclosed shape, IF IT HAS endpoints
            warnings.append("  WARNING [" + str(obj_id) + "]: curve too short. Returning endpoint segment.")
            return [(curve.PointAtStart, curve.PointAtEnd)]
        elif curve.IsClosed: #if a curve starts and ends at the same point, forming a continuous, enclosed shape without endpoints
            warnings.append("  WARNING [" + str(obj_id) + "]: short closed curve. Dividing into " + str(split_num) + " parts.")
            n_segments = split_num
            return get_points(n_segments, curve)
    else:
        n_segments = length // SPLIT_LENGTH 
        n_segments = int(n_segments) + 1 
        return get_points(n_segments, curve)


def extract_segments_from_object(obj, tol, warnings): # Extracts a list of (Point3d, Point3d) from any Rhino object
    segments = []
    geom = obj.Geometry

    # Straight line
    if isinstance(geom, rg.LineCurve):
        line = geom.Line
        if is_nonzero_z(line.From, tol):
            warnings.append("  WARNING [" + str(obj.Id) + "]: Z non-zero. Projected onto Z=0.")
        segments.append((line.From, line.To))

    # Polyline
    elif isinstance(geom, rg.PolylineCurve):
        success, polyline = geom.TryGetPolyline()
        if not success or polyline is None:
            # Fallback: discretize if polyline extraction fails
            segs = discretize_curve(geom, tol, warnings, obj.Id)
            segments.extend(segs)
            return segments
        for i in range(polyline.Count - 1):
            segments.append((polyline[i], polyline[i + 1]))

    # Generic curve (arcs, etc.)
    elif isinstance(geom, rg.Curve):
        if geom.IsLinear(): # Treat as a single straight segment
            segments.append((geom.PointAtStart, geom.PointAtEnd))
        elif geom.IsPolyline():
            success, polyline = geom.TryGetPolyline()
            if success and polyline is not None:
                for i in range(polyline.Count - 1):
                    segments.append((polyline[i], polyline[i + 1]))
            else:
                segs = discretize_curve(geom, tol, warnings, obj.Id)
                segments.extend(segs)
        else: # Non-linear, non-polyline curve: discretize it
            segs = discretize_curve(geom, tol, warnings, obj.Id)
            segments.extend(segs)

    # Non-geometric types: silently ignore
    elif type(geom).__name__ in ("Hatch", "TextEntity", "AnnotationBase",
                                  "Dimension", "Leader", "Brep",
                                  "Point", "PointCloud"):
        pass

    return segments


def project_to_xy(pt): # Projects a 3D point onto the XY plane (Z=0)
    return rg.Point3d(pt.X, pt.Y, 0.0)


def deduplicate(segments_by_layer, tol):# Removes duplicate segments within each layer # A segment is a duplicate if both endpoints match (in any order) within tolerance
    result = {}
    for layer, segs in segments_by_layer.items():
        unique = []
        for seg in segs:
            a1, a2 = seg
            is_duplicate = False
            for u in unique:
                b1, b2 = u
                if (a1.DistanceTo(b1) < tol and a2.DistanceTo(b2) < tol) or \
                   (a1.DistanceTo(b2) < tol and a2.DistanceTo(b1) < tol):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(seg)
        removed = len(segs) - len(unique)
        if removed > 0:
            print("  Dedup '" + layer + "': removed " + str(removed) + " duplicates.")
        result[layer] = unique
    return result


def format_point(pt): # Formats a point as "X Y" with the configured number of decimal places
    fmt = "{:." + str(DECIMAL_PLACES) + "f}"
    return fmt.format(pt.X) + COORD_SEPARATOR + fmt.format(pt.Y)

#Main

def main():
    tol = get_doc_tolerance()
    
    # Explode all objects in the document
    rs.Command("_SelAll", False)
    rs.Command("_Explode", False)
    sc.doc.Views.Redraw()
    
    all_objects = [o for o in sc.doc.Objects if not o.IsDeleted]

    segments_by_layer = {}
    warnings          = []

    for obj in all_objects:
        if not INCLUDE_HIDDEN and not obj.Visible:
            continue
        if not should_export(obj):
            continue

        layer_name = get_layer_name(obj)
        segs = extract_segments_from_object(obj, tol, warnings)

        for (p1, p2) in segs:
            pp1 = project_to_xy(p1)
            pp2 = project_to_xy(p2)
            if pp1.DistanceTo(pp2) > tol:
                segments_by_layer.setdefault(layer_name, []).append((pp1, pp2))

    # Remove duplicate segments
    if DEDUPLICATE_SEGMENTS and segments_by_layer:
        segments_by_layer = deduplicate(segments_by_layer, tol)

    # Print warnings
    if warnings:
        print("")
        for w in warnings:
            print(w)
        print("")

    # Save output in a .cin file in the same folder as the .dwg file
    if not segments_by_layer:
        print("ERROR: no segments found!")
        print("Check that the layers in the file match those in LAYERS_TO_EXPORT.")
        return
        
    import os
    folder = Rhino.ApplicationSettings.FileSettings.WorkingFolder
    if not folder:
        print("ERROR: could not find the working folder.")
        return
    dwg_name = os.path.basename(folder)
    for ext in [".cin", ".txt"]:
        output_path = os.path.join(folder, dwg_name + ext)
        with open(output_path, "w") as f:
            for layer_name, segs in segments_by_layer.items():
                for (p1, p2) in segs:
                    p1_str = format_point(p1)
                    p2_str = format_point(p2)
                    f.write("s " + p1_str + " " + p2_str + "\n")
        print("Saved to: " + output_path)

main()