# -*- coding: utf-8 -*-

import Rhino.Geometry as rg
import scriptcontext as sc
import Rhino
import math

#configuration

DECIMAL_PLACES       = 5
COORD_SEPARATOR      = " "
INCLUDE_HIDDEN       = False
DEDUPLICATE_SEGMENTS = True
NORMALIZE_COORDS     = True

LAYERS_TO_EXPORT = [
    u"\u58c1",                                      # 壁 wall
    u"\u67f1",                                      # 柱 pillar
    u"\u30ac\u30e9\u30b9",                          # ガラス glass
    u"\u30d1\u30fc\u30c6\u30a3\u30b7\u30e7\u30f3",  # パーティション partition wall
    u"\u5e8a\u9762\u5916\u5f62\u7dda",              # 床面外形線 floor boundary line
]

# functions

def get_doc_tolerance():
    return sc.doc.ModelAbsoluteTolerance


def get_layer_name(obj): # Returns the name of the layer of the object
    return sc.doc.Layers[obj.Attributes.LayerIndex].Name.strip()


def should_export(obj): # Returns True if the layer of the object is in the whitelist
    return get_layer_name(obj) in LAYERS_TO_EXPORT


def is_nonzero_z(pt, tol): # Returns True if the Z coordinate is not zero
    return abs(pt.Z) > tol


def discretize_curve(curve, tol, warnings, obj_id): # Discretizes a curve into N segments 
    segments = []

    length = curve.GetLength()
    if length is None or length < tol:
        warnings.append("  WARNING [" + str(obj_id) + "]: curve has null length. Ignored.")
        return segments

    n_segments = int(math.ceil(length))
    if n_segments < 1:
        n_segments = 1

    points = []
    for i in range(n_segments + 1):
        fraction = i / float(n_segments) # Search for the point on the curve at the given arc length fraction
        success, t = curve.NormalizedLengthParameter(fraction) # success is a boolean: True if the point t was found
        if not success: # If the point cannot be calculated, skip it and log a warning
            warnings.append("  WARNING [" + str(obj_id) + "]: point at fraction " + str(round(fraction, 3)) + " could not be calculated.")
            continue
        points.append(curve.PointAt(t))

    for i in range(len(points) - 1):
        segments.append((points[i], points[i + 1]))

    return segments


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


def normalize_segments(segments_by_layer): # Translates all segments so that the minimum X and Y become 0 # This moves the drawing origin to (0, 0)
    all_points = []
    for segs in segments_by_layer.values():
        for (p1, p2) in segs:
            all_points.append(p1)
            all_points.append(p2)

    min_x = min(p.X for p in all_points)
    min_y = min(p.Y for p in all_points)

    result = {}
    for layer, segs in segments_by_layer.items():
        result[layer] = []
        for (p1, p2) in segs:
            new_p1 = rg.Point3d(p1.X - min_x, p1.Y - min_y, 0.0)
            new_p2 = rg.Point3d(p2.X - min_x, p2.Y - min_y, 0.0)
            result[layer].append((new_p1, new_p2))
    return result


def format_point(pt): # Formats a point as "X Y" with the configured number of decimal places
    fmt = "{:." + str(DECIMAL_PLACES) + "f}"
    return fmt.format(pt.X) + COORD_SEPARATOR + fmt.format(pt.Y)

#main

def main():
    tol = get_doc_tolerance()
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

    # Translate coordinates so that the bottom-left corner is at (0, 0)
    if NORMALIZE_COORDS and segments_by_layer:
        segments_by_layer = normalize_segments(segments_by_layer)

    # Print warnings
    if warnings:
        print("")
        for w in warnings:
            print(w)
        print("")

    # Print output
    if not segments_by_layer:
        print("ERROR: no segments found!")
        print("Check that the layers in the file match those in LAYERS_TO_EXPORT.")
        return

    total = 0
    for layer_name, segs in segments_by_layer.items():
        for (p1, p2) in segs:
            p1_str = format_point(p1)
            p2_str = format_point(p2)
            print("s " + p1_str + " " + p2_str)
            total += 1

main()