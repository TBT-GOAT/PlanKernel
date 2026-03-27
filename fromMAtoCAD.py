
# -*- coding: utf-8 -*-

import rhinoscriptsyntax as rs
import os


def load_coordinates(filepath):
    coords = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            x, y = float(parts[0]), float(parts[1])
            coords.append((x, y, 0))  # z = 0 
    return coords


def load_clearance(filepath):
    radii = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            radii.append(float(line))
    return radii


def load_adjacency(filepath):
    adjacency = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = list(map(int, line.split()))
            node = parts[0]
            neighbors = parts[1:]
            adjacency[node] = neighbors
    return adjacency


def main():
    #Ask user to pick the folder with the .nk files
    base_path = rs.BrowseForFolder(
        folder=None,
        message="Select the folder containing the .nk files (ma_... folder)",
        title="Select MA folder"
    )

    if not base_path:
        print("No folder selected. Exiting.")
        return

    print("Selected folder: " + base_path)

    #Build file paths
    adjacency_file = os.path.join(base_path, "adjacency.nk")
    clearance_file = os.path.join(base_path, "clearance.nk")
    coord_file     = os.path.join(base_path, "coordination.nk")

    #Check that all files exist
    for filepath in [adjacency_file, clearance_file, coord_file]:
        if not os.path.exists(filepath):
            print("ERROR: File not found: " + filepath)
            return

    #Load data
    coords    = load_coordinates(coord_file)
    radii     = load_clearance(clearance_file)
    adjacency = load_adjacency(adjacency_file)

    num_nodes = len(coords)
    print("Nodes found: " + str(num_nodes))
    print("Radii found: " + str(len(radii)))
    print("Adjacency rows found: " + str(len(adjacency)))

    #Add layers in Rhino
    if not rs.IsLayer("MA_NODES"):
        rs.AddLayer("MA_NODES", (0, 200, 0))      # green
    if not rs.IsLayer("MA_CIRCLES"):
        rs.AddLayer("MA_CIRCLES", (255, 0, 0))    # red
    if not rs.IsLayer("MA_LINES"):
        rs.AddLayer("MA_LINES", (0, 0, 255))      # blue

    #Draw node points and clearance circles
    print("Drawing nodes and clearance circles...")
    for i in range(num_nodes):
        center = coords[i]
        r = radii[i] if i < len(radii) else 0

        #Node point
        rs.CurrentLayer("MA_NODES")
        rs.AddPoint(center)

        #Circle with clearance radius
        if r > 0:
            rs.CurrentLayer("MA_CIRCLES")
            rs.AddCircle(center, r)

    #Draw adjacency lines
    drawn_edges = set()
    rs.CurrentLayer("MA_LINES")

    for node, neighbors in adjacency.items():
        if node >= num_nodes:
            continue
        pt1 = coords[node]
        for neighbor in neighbors:
            if neighbor >= num_nodes:
                continue
            edge = tuple(sorted((node, neighbor)))
            if edge in drawn_edges:
                continue
            drawn_edges.add(edge)
            pt2 = coords[neighbor]
            rs.AddLine(pt1, pt2)

    print("Done! " + str(num_nodes) + " nodes drawn in Rhino.")

main()