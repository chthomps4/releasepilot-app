#!/usr/bin/env python3
"""
Build a printable 3D concept model from the Greg Allen shed shop drawings.

This script produces an STL sized for Bambu Studio / Bambu Lab P1S.
The source dimensions remain in inches and are scaled down for printing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import trimesh

MM_PER_INCH = 25.4


def inches(value: float, scale: float) -> float:
    return float(value) * MM_PER_INCH / scale


def clean_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_" else "_" for char in value)
    return cleaned.strip("_") or "greg_allen_shed"


def transform_mesh(mesh: trimesh.Trimesh, translation=(0, 0, 0), rotation_z: float = 0.0) -> trimesh.Trimesh:
    result = mesh.copy()
    if rotation_z:
        transform = trimesh.transformations.rotation_matrix(rotation_z, [0, 0, 1])
        result.apply_transform(transform)
    result.apply_translation(translation)
    return result


def box(name: str, size: Iterable[float], center: Iterable[float], rotation_z: float = 0.0) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=list(size))
    mesh.metadata["name"] = name
    return transform_mesh(mesh, translation=center, rotation_z=rotation_z)


def polygon_prism(points_xy: list[tuple[float, float]], z_min: float, z_max: float, name: str) -> trimesh.Trimesh:
    vertices: list[list[float]] = []
    for x, y in points_xy:
        vertices.append([x, y, z_min])
    for x, y in points_xy:
        vertices.append([x, y, z_max])

    n = len(points_xy)
    faces: list[list[int]] = []

    for i in range(1, n - 1):
        faces.append([0, i + 1, i])
        faces.append([n, n + i, n + i + 1])

    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j + n])
        faces.append([i, j + n, i + n])

    mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces), process=True)
    mesh.metadata["name"] = name
    return mesh


def triangle_prism(x_left: float, x_right: float, y_center: float, thickness: float,
                   z_base: float, z_peak: float, name: str) -> trimesh.Trimesh:
    y0 = y_center - thickness / 2
    y1 = y_center + thickness / 2
    vertices = np.array([
        [x_left, y0, z_base],
        [x_right, y0, z_base],
        [0, y0, z_peak],
        [x_left, y1, z_base],
        [x_right, y1, z_base],
        [0, y1, z_peak],
    ])
    faces = np.array([
        [0, 2, 1], [3, 4, 5],
        [0, 1, 4], [0, 4, 3],
        [1, 2, 5], [1, 5, 4],
        [2, 0, 3], [2, 3, 5],
    ])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    mesh.metadata["name"] = name
    return mesh


def quad_plate(points: list[np.ndarray], thickness: float, name: str) -> trimesh.Trimesh:
    p0, p1, p2, p3 = points
    normal = np.cross(p1 - p0, p2 - p1)
    normal = normal / np.linalg.norm(normal)
    offset = -normal * thickness if normal[2] > 0 else normal * thickness

    vertices = np.array([p0, p1, p2, p3, p0 + offset, p1 + offset, p2 + offset, p3 + offset])
    faces = np.array([
        [0, 1, 2], [0, 2, 3],
        [7, 6, 5], [7, 5, 4],
        [0, 4, 5], [0, 5, 1],
        [1, 5, 6], [1, 6, 2],
        [2, 6, 7], [2, 7, 3],
        [3, 7, 4], [3, 4, 0],
    ])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    mesh.metadata["name"] = name
    return mesh


def add_front_back_battens(meshes: list[trimesh.Trimesh], *, y: float, width: float, z_bottom: float, z_top: float,
                           spacing: float, batten_width: float, batten_depth: float, label: str) -> None:
    count = max(2, int(width // spacing))
    xs = np.linspace(-width / 2 + spacing, width / 2 - spacing, count - 1)
    for index, x in enumerate(xs, start=1):
        meshes.append(box(
            f"{label}_vertical_batten_{index}",
            [batten_width, batten_depth, z_top - z_bottom],
            [x, y, (z_bottom + z_top) / 2],
        ))


def add_side_battens(meshes: list[trimesh.Trimesh], *, x_front: float, y_front: float, x_back: float, y_back: float,
                     side_sign: float, z_bottom: float, z_top: float, spacing: float,
                     batten_width: float, batten_depth: float, label: str) -> None:
    dx = x_back - x_front
    dy = y_back - y_front
    length = (dx ** 2 + dy ** 2) ** 0.5
    angle = np.arctan2(dy, dx)
    count = max(2, int(length // spacing))
    for index in range(1, count):
        t = index / count
        x = x_front + dx * t
        y = y_front + dy * t
        meshes.append(box(
            f"{label}_side_batten_{index}",
            [batten_width, batten_depth, z_top - z_bottom],
            [x + side_sign * batten_depth * 0.35, y, (z_bottom + z_top) / 2],
            rotation_z=angle,
        ))


def build_model(config: dict) -> trimesh.Trimesh:
    scale = float(config["print_scale"])
    d = config["dimensions_in"]
    f_width = inches(d["front_width"], scale)
    b_width = inches(d["back_width"], scale)
    depth = inches(d["depth"], scale)
    eave_h = inches(d["eave_height"], scale)
    total_h = inches(d["ridge_height"], scale)
    base_h = inches(d.get("base_height", 2.0), scale)
    wall_t = inches(d.get("wall_thickness", 1.5), scale)
    roof_t = inches(d.get("roof_thickness", 1.25), scale)
    overhang = inches(d.get("roof_overhang", 3.0), scale)

    detail = config.get("detail_in", {})
    batten_spacing = inches(detail.get("batten_spacing", 7.5), scale)
    batten_w = max(0.65, inches(detail.get("batten_width", 0.75), scale))
    batten_depth = max(0.45, inches(detail.get("batten_depth", 0.35), scale))
    trim_w = max(1.0, inches(detail.get("trim_width", 1.5), scale))
    trim_d = max(0.55, inches(detail.get("trim_depth", 0.45), scale))

    y_front = -depth / 2
    y_back = depth / 2
    z0 = base_h
    z_eave = base_h + eave_h
    z_peak = base_h + total_h

    meshes: list[trimesh.Trimesh] = []

    footprint = [
        (-f_width / 2 - wall_t, y_front - wall_t),
        (f_width / 2 + wall_t, y_front - wall_t),
        (b_width / 2 + wall_t, y_back + wall_t),
        (-b_width / 2 - wall_t, y_back + wall_t),
    ]
    meshes.append(polygon_prism(footprint, 0, base_h, "tapered_floor_base"))

    meshes.append(box("front_wall_rect", [f_width + 2 * wall_t, wall_t, eave_h], [0, y_front - wall_t / 2, z0 + eave_h / 2]))
    meshes.append(box("back_wall_rect", [b_width + 2 * wall_t, wall_t, eave_h], [0, y_back + wall_t / 2, z0 + eave_h / 2]))
    meshes.append(triangle_prism(-f_width / 2 - wall_t, f_width / 2 + wall_t, y_front - wall_t / 2, wall_t, z_eave, z_peak, "front_gable"))
    meshes.append(triangle_prism(-b_width / 2 - wall_t, b_width / 2 + wall_t, y_back + wall_t / 2, wall_t, z_eave, z_peak, "back_gable"))

    for side_name, sign in [("left", -1.0), ("right", 1.0)]:
        x_f = sign * f_width / 2
        x_b = sign * b_width / 2
        dx = x_b - x_f
        dy = depth
        length = (dx ** 2 + dy ** 2) ** 0.5
        angle = np.arctan2(dy, dx)
        center_x = (x_f + x_b) / 2 + sign * wall_t / 2
        meshes.append(box(
            f"{side_name}_wall_rect",
            [length, wall_t, eave_h],
            [center_x, 0, z0 + eave_h / 2],
            rotation_z=angle,
        ))

    front_ridge = np.array([0, y_front - overhang, z_peak])
    back_ridge = np.array([0, y_back + overhang, z_peak])
    front_right_eave = np.array([f_width / 2 + overhang, y_front - overhang, z_eave])
    back_right_eave = np.array([b_width / 2 + overhang, y_back + overhang, z_eave])
    front_left_eave = np.array([-f_width / 2 - overhang, y_front - overhang, z_eave])
    back_left_eave = np.array([-b_width / 2 - overhang, y_back + overhang, z_eave])

    meshes.append(quad_plate([front_ridge, back_ridge, back_right_eave, front_right_eave], roof_t, "right_roof_panel"))
    meshes.append(quad_plate([back_ridge, front_ridge, front_left_eave, back_left_eave], roof_t, "left_roof_panel"))
    meshes.append(box("ridge_cap", [inches(2.0, scale), depth + 2 * overhang, inches(2.0, scale)], [0, 0, z_peak + inches(0.5, scale)]))

    door_w = inches(config.get("front_door_in", {}).get("width", 45.0), scale)
    door_h = inches(config.get("front_door_in", {}).get("height", 45.0), scale)
    door_y = y_front - wall_t - trim_d * 0.55
    door_z_center = z0 + door_h / 2
    meshes.append(box("front_double_door_panel", [door_w, trim_d, door_h], [0, door_y, door_z_center]))
    meshes.append(box("door_left_trim", [trim_w, trim_d * 1.2, door_h], [-door_w / 2, door_y - 0.1, door_z_center]))
    meshes.append(box("door_right_trim", [trim_w, trim_d * 1.2, door_h], [door_w / 2, door_y - 0.1, door_z_center]))
    meshes.append(box("door_center_seam", [trim_w * 0.65, trim_d * 1.25, door_h], [0, door_y - 0.15, door_z_center]))
    meshes.append(box("door_top_trim", [door_w + trim_w, trim_d * 1.2, trim_w], [0, door_y - 0.1, z0 + door_h]))
    meshes.append(box("door_bottom_trim", [door_w + trim_w, trim_d * 1.2, trim_w], [0, door_y - 0.1, z0]))
    handle_z = z0 + door_h * 0.55
    meshes.append(box("left_door_handle", [trim_w * 0.7, trim_d * 1.6, trim_w * 1.8], [-door_w * 0.08, door_y - trim_d * 0.8, handle_z]))
    meshes.append(box("right_door_handle", [trim_w * 0.7, trim_d * 1.6, trim_w * 1.8], [door_w * 0.08, door_y - trim_d * 0.8, handle_z]))

    add_front_back_battens(meshes, y=y_front - wall_t - batten_depth / 2, width=door_w, z_bottom=z0 + trim_w, z_top=z0 + door_h - trim_w,
                           spacing=batten_spacing, batten_width=batten_w, batten_depth=batten_depth, label="front_door")
    add_front_back_battens(meshes, y=y_back + wall_t + batten_depth / 2, width=b_width, z_bottom=z0, z_top=z_eave,
                           spacing=batten_spacing, batten_width=batten_w, batten_depth=batten_depth, label="back_wall")
    add_side_battens(meshes, x_front=-f_width / 2 - wall_t, y_front=y_front, x_back=-b_width / 2 - wall_t, y_back=y_back,
                     side_sign=-1.0, z_bottom=z0, z_top=z_eave, spacing=batten_spacing,
                     batten_width=batten_w, batten_depth=batten_depth, label="left_wall")
    add_side_battens(meshes, x_front=f_width / 2 + wall_t, y_front=y_front, x_back=b_width / 2 + wall_t, y_back=y_back,
                     side_sign=1.0, z_bottom=z0, z_top=z_eave, spacing=batten_spacing,
                     batten_width=batten_w, batten_depth=batten_depth, label="right_wall")

    model = trimesh.util.concatenate(meshes)
    model.metadata["name"] = clean_name(config["name"])
    model.fix_normals()
    return model


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Greg Allen shed STL for Bambu Studio.")
    parser.add_argument("config", type=Path, help="Path to Greg Allen shed JSON config.")
    parser.add_argument("--out-dir", type=Path, default=Path("model_build"), help="Output directory.")
    args = parser.parse_args()

    config = load_config(args.config)
    model = build_model(config)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_name = clean_name(config["name"])
    stl_path = args.out_dir / f"{out_name}.stl"
    model.export(stl_path)
    print(f"Generated STL: {stl_path}")
    print(f"Extents mm: {model.extents.tolist()}")


if __name__ == "__main__":
    main()
