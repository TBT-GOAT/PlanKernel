# -*- coding: utf-8 -*-

import Rhino.Geometry as rg
import scriptcontext as sc
import Rhino
import math

# configuration 

DECIMAL_PLACES       = 5
COORD_SEPARATOR      = " "
INCLUDE_HIDDEN       = False
DEDUPLICATE_SEGMENTS = True

LAYERS_TO_EXPORT = [
    u"\u58c1",                                      # 壁 wall
    u"\u67f1",                                      # 柱 pillar
    u"\u30ac\u30e9\u30b9",                          # ガラス glass
    u"\u30d1\u30fc\u30c6\u30a3\u30b7\u30e7\u30f3",  # パーティション partition wall
    u"\u5e8a\u9762\u5916\u5f62\u7dda",              # 床面外形線 floor boundary line
]

# code

def discretize_curve(curve, tol, warnings, obj_id):
    
    segments = []

    length = curve.GetLength()
    if length is None or length < tol:
        warnings.append("  WARNING [" + str(obj_id) + "]: Curve has null lenght. Skipped.")
        return segments

    n_segments = int(math.ceil(length))
    if n_segments < 1:
        n_segments = 1

    warnings.append(
        "  INFO [" + str(obj_id) + "]: Curve lenght=" + str(round(length, 4)) +
        " -> " + str(n_segments) + " segments of " + str(round(length / n_segments, 4)) + " each."
    )

    points = []
    for i in range(n_segments + 1):
        fraction = i / float(n_segments)
        success, t = curve.NormalizedLengthParameter(fraction)
        if not success:
            warnings.append("  WARNING [" + str(obj_id) + "]: point at fraction " + str(round(fraction, 3)) + " can't calculate it.") 
            continue
        points.append(curve.PointAt(t))

    for i in range(len(points) - 1):
        segments.append((points[i], points[i + 1]))

    return segments