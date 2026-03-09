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

def get_doc_tolerance():
    return sc.doc.ModelAbsoluteTolerance


def get_layer_name(obj):
    """Restituisce il nome del layer dell'oggetto."""
    return sc.doc.Layers[obj.Attributes.LayerIndex].Name.strip()


def should_export(obj):
    """True se il layer dell'oggetto e nella whitelist."""
    return get_layer_name(obj) in LAYERS_TO_EXPORT


def is_nonzero_z(pt, tol):
    return abs(pt.Z) > tol


def discretize_curve(curve, tol, warnings, obj_id):
    """
    Discretizza una curva in N segmenti dove N = ceil(lunghezza).
    Punti equidistanti lungo la lunghezza dell'arco.
    """
    segments = []

    length = curve.GetLength()
    if length is None or length < tol:
        warnings.append("  WARNING [" + str(obj_id) + "]: curva con lunghezza nulla. Saltata.")
        return segments

    n_segments = int(math.ceil(length))
    if n_segments < 1:
        n_segments = 1

    warnings.append(
        "  INFO [" + str(obj_id) + "]: CURVA lunghezza=" + str(round(length, 4)) +
        " -> " + str(n_segments) + " segmenti da " + str(round(length / n_segments, 4)) + " l'uno."
    )

    points = []
    for i in range(n_segments + 1):
        fraction = i / float(n_segments)
        success, t = curve.NormalizedLengthParameter(fraction)
        if not success:
            warnings.append("  WARNING [" + str(obj_id) + "]: punto a frazione " + str(round(fraction, 3)) + " non calcolabile.")
            continue
        points.append(curve.PointAt(t))

    for i in range(len(points) - 1):
        segments.append((points[i], points[i + 1]))

    return segments


def extract_segments_from_object(obj, tol, warnings):
    """
    Estrae lista di (Point3d, Point3d) da qualsiasi oggetto Rhino.
    """
    segments = []
    geom = obj.Geometry

    # Linea retta
    if isinstance(geom, rg.LineCurve):
        line = geom.Line
        if is_nonzero_z(line.From, tol):
            warnings.append("  WARNING [" + str(obj.Id) + "]: Z non-zero. Proiettato su Z=0.")
        segments.append((line.From, line.To))

    # Polilinea
    elif isinstance(geom, rg.PolylineCurve):
        success, polyline = geom.TryGetPolyline()
        if not success or polyline is None:
            segs = discretize_curve(geom, tol, warnings, obj.Id)
            segments.extend(segs)
            return segments
        for i in range(polyline.Count - 1):
            segments.append((polyline[i], polyline[i + 1]))

    # Curva generica (archi, NURBS, ecc.)
    elif isinstance(geom, rg.Curve):
        if geom.IsLinear():
            segments.append((geom.PointAtStart, geom.PointAtEnd))
        elif geom.IsPolyline():
            success, polyline = geom.TryGetPolyline()
            if success and polyline is not None:
                for i in range(polyline.Count - 1):
                    segments.append((polyline[i], polyline[i + 1]))
            else:
                segs = discretize_curve(geom, tol, warnings, obj.Id)
                segments.extend(segs)
        else:
            # Curva vera -> discretizza con ceil(lunghezza)
            segs = discretize_curve(geom, tol, warnings, obj.Id)
            segments.extend(segs)

    # Tipi non geometrici -> ignora silenziosamente
    elif type(geom).__name__ in ("Hatch", "TextEntity", "AnnotationBase",
                                  "Dimension", "Leader", "Brep",
                                  "Point", "PointCloud"):
        pass

    return segments


def project_to_xy(pt):
    return rg.Point3d(pt.X, pt.Y, 0.0)


def segments_are_equal(s1, s2, tol):
    a1, a2 = s1
    b1, b2 = s2
    return (a1.DistanceTo(b1) < tol and a2.DistanceTo(b2) < tol) or \
           (a1.DistanceTo(b2) < tol and a2.DistanceTo(b1) < tol)


def deduplicate(segments_by_layer, tol):
    result = {}
    for layer, segs in segments_by_layer.items():
        unique = []
        for seg in segs:
            if not any(segments_are_equal(seg, u, tol) for u in unique):
                unique.append(seg)
        removed = len(segs) - len(unique)
        if removed > 0:
            print("  Dedup '" + layer + "': rimossi " + str(removed) + " duplicati.")
        result[layer] = unique
    return result


def format_point(pt, decimals, sep):
    fmt = "{:." + str(decimals) + "f}"
    return fmt.format(pt.X) + sep + fmt.format(pt.Y)


# =============================================================================
# MAIN
# =============================================================================

def main():
    tol = get_doc_tolerance()
    all_objects = [o for o in sc.doc.Objects if not o.IsDeleted]

    # Diagnosi layer
    print("=" * 50)
    print("LAYER NEL FILE:")
    layer_counts = {}
    for obj in all_objects:
        ln = get_layer_name(obj)
        layer_counts[ln] = layer_counts.get(ln, 0) + 1
    for ln, count in sorted(layer_counts.items()):
        status = "OK  " if ln in LAYERS_TO_EXPORT else "SKIP"
        print("  [" + status + "]  '" + ln + "' : " + str(count) + " oggetti")
    print("=" * 50)

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

    # Deduplicazione
    if DEDUPLICATE_SEGMENTS and segments_by_layer:
        segments_by_layer = deduplicate(segments_by_layer, tol)

    # Warnings
    if warnings:
        print("")
        for w in warnings:
            print(w)
        print("")

    # Output
    if not segments_by_layer:
        print("ERRORE: nessun segmento trovato!")
        print("Controlla che i layer nel file corrispondano a quelli in LAYERS_TO_EXPORT.")
        return

    total = 0
    for layer_name, segs in segments_by_layer.items():
        print("# --- " + layer_name + " ---")
        for (p1, p2) in segs:
            p1_str = format_point(p1, DECIMAL_PLACES, COORD_SEPARATOR)
            p2_str = format_point(p2, DECIMAL_PLACES, COORD_SEPARATOR)
            print("s " + p1_str + " " + p2_str)
            total += 1

    print("")
    print("# Totale segmenti: " + str(total))


main()

