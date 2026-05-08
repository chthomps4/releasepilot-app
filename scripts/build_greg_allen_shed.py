#!/usr/bin/env python3
"""
Build the corrected Greg Allen shed model for Bambu Studio / Bambu Lab P1S.

Corrected interpretation:
- The shed is square-cornered / rectangular in plan.
- Front and back use the same overall width from the elevations.
- Side elevations provide the depth.
- Handwritten source dimensions are kept in inches and scaled for printing.
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
        result.apply_transform(trimesh.transformations.rotation_matrix(rotation_z, [0, 0, 1]))
    result.apply_translation(translation)
    return result


def box(name: str, size: Iterable[float], center: Iterable[float], rotation_z: float = 0.0) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=list(size))
    mesh.metadata["name"] = name
    return transform_mesh(mesh, translation=center, rotation_z=rotation_z)


def triangle_prism(x_left: float, x_right: float, y_center: float, thickness: float,
                   z_base: float, z_peak: float, name: str) -> trimesh.Trimesh:
    y0 = y_center - thickness / 2
    y1 = y_center + thickness / 2
    vertices = np.array([
        [x_left, y0, z_base], [x_right, y0, z_base], [0, y0, z_peak],
        [x_left, y1, z_base], [x_right, y1, z_base], [0, y1, z_peak],
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
        [0, 1, 2], [0, 2, 3], [7, 6, 5], [7, 5, 4],
        [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2],
        [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0],
    ])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    mesh.metadata["name"] = name
    return mesh


def add_vertical_battens(meshes: list[trimesh.Trimesh], *, wall: str, width: float, depth: float,
                         x: float | None = None, y: float | None = None, z_bottom: float,
                         z_top: float, spacing: float, batten_width: float, batten_depth: float) -> None:
    if wall in {"front", "back"}:
        assert y is not None
        count = max(2, int(width // spacing))
        for index in range(1, count):
            xpos = -width / 2 + width * index / count
            meshes.append(box(f"{wall}_vertical_batten_{index}", [batten_width, batten_depth, z_top - z_bottom], [xpos, y, (z_bottom + z_top) / 2]))
    elif wall in {"left", "right"}:
        assert x is not None
        count = max(2, int(depth // spacing))
        for index in range(1, count):
            ypos = -depth / 2 + depth * index / count
            meshes.append(box(f"{wall}_vertical_batten_{index}", [batten_depth, batten_width, z_top - z_bottom], [x, ypos, (z_bottom + z_top) / 2]))


def build_model(config: dict) -> trimesh.Trimesh:
    scale = float(config["print_scale"])
    d = config["dimensions_in"]
    width = inches(d["width"], scale)
    depth = inches(d["depth"], scale)
    eave_h = inches(d["eave_height"], scale)
    ridge_h = inches(d["ridge_height"], scale)
    base_h = inches(d.get("base_height", 2.0), scale)
    wall_t = inches(d.get("wall_thickness", 1.5), scale)
    roof_t = inches(d.get("roof_thickness", 1.25), scale)
    overhang_fb = inches(d.get("roof_overhang_front_back", 3.0), scale)
    overhang_sides = inches(d.get("roof_overhang_sides", 3.0), scale)

    detail = config.get("detail_in", {})
    batten_spacing = inches(detail.get("batten_spacing", 7.5), scale)
    batten_w = max(0.65, inches(detail.get("batten_width", 0.75), scale))
    batten_d = max(0.45, inches(detail.get("batten_depth", 0.35), scale))
    trim_w = max(1.0, inches(detail.get("trim_width", 1.5), scale))
    trim_d = max(0.55, inches(detail.get("trim_depth", 0.45), scale))
    ridge_cap_w = inches(detail.get("ridge_cap_width", 2.0), scale)

    y_front = -depth / 2
    y_back = depth / 2
    z0 = base_h
    z_eave = z0 + eave_h
    z_peak = z0 + ridge_h

    meshes: list[trimesh.Trimesh] = []

    meshes.append(box("rectangular_floor_base", [width + 2 * wall_t, depth + 2 * wall_t, base_h], [0, 0, base_h / 2]))
    meshes.append(box("front_wall", [width + 2 * wall_t, wall_t, eave_h], [0, y_front - wall_t / 2, z0 + eave_h / 2]))
    meshes.append(box("back_wall", [width + 2 * wall_t, wall_t, eave_h], [0, y_back + wall_t / 2, z0 + eave_h / 2]))
    meshes.append(box("left_wall", [wall_t, depth, eave_h], [-width / 2 - wall_t / 2, 0, z0 + eave_h / 2]))
    meshes.append(box("right_wall", [wall_t, depth, eave_h], [width / 2 + wall_t / 2, 0, z0 + eave_h / 2]))
    meshes.append(triangle_prism(-width / 2 - wall_t, width / 2 + wall_t, y_front - wall_t / 2, wall_t, z_eave, z_peak, "front_gable"))
    meshes.append(triangle_prism(-width / 2 - wall_t, width / 2 + wall_t, y_back + wall_t / 2, wall_t, z_eave, z_peak, "back_gable"))

    front_ridge = np.array([0, y_front - overhang_fb, z_peak])
    back_ridge = np.array([0, y_back + overhang_fb, z_peak])
    front_right_eave = np.array([width / 2 + overhang_sides, y_front - overhang_fb, z_eave])
    back_right_eave = np.array([width / 2 + overhang_sides, y_back + overhang_fb, z_eave])
    front_left_eave = np.array([-width / 2 - overhang_sides, y_front - overhang_fb, z_eave])
    back_left_eave = np.array([-width / 2 - overhang_sides, y_back + overhang_fb, z_eave])
    meshes.append(quad_plate([front_ridge, back_ridge, back_right_eave, front_right_eave], roof_t, "right_roof_panel"))
    meshes.append(quad_plate([back_ridge, front_ridge, front_left_eave, back_left_eave], roof_t, "left_roof_panel"))
    meshes.append(box("ridge_cap", [ridge_cap_w, depth + 2 * overhang_fb, ridge_cap_w], [0, 0, z_peak + ridge_cap_w * 0.25]))

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
    meshes.append(box("left_door_handle", [trim_w * 0.7, trim_d * 1.6, trim_w * 1.8], [-door_w * 0.08, door_y - trim_d * 0.8, z0 + door_h * 0.55]))
    meshes.append(box("right_door_handle", [trim_w * 0.7, trim_d * 1.6, trim_w * 1.8], [door_w * 0.08, door_y - trim_d * 0.8, z0 + door_h * 0.55]))

    add_vertical_battens(meshes, wall="front", width=door_w, depth=depth, y=y_front - wall_t - batten_d / 2,
                         z_bottom=z0 + trim_w, z_top=z0 + door_h - trim_w, spacing=batten_spacing,
                         batten_width=batten_w, batten_depth=batten_d)
    add_vertical_battens(meshes, wall="back", width=width, depth=depth, y=y_back + wall_t + batten_d / 2,
                         z_bottom=z0, z_top=z_eave, spacing=batten_spacing,
                         batten_width=batten_w, batten_depth=batten_d)
    add_vertical_battens(meshes, wall="left", width=width, depth=depth, x=-width / 2 - wall_t - batten_d / 2,
                         z_bottom=z0, z_top=z_eave, spacing=batten_spacing,
                         batten_width=batten_w, batten_depth=batten_d)
    add_vertical_battens(meshes, wall="right", width=width, depth=depth, x=width / 2 + wall_t + batten_d / 2,
                         z_bottom=z0, z_top=z_eave, spacing=batten_spacing,
                         batten_width=batten_w, batten_depth=batten_d)

    corner_h = eave_h
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            meshes.append(box("corner_trim", [trim_w, trim_w, corner_h], [sx * (width / 2 + wall_t + trim_w / 4), sy * (depth / 2 + wall_t + trim_w / 4), z0 + corner_h / 2]))

    model = trimesh.util.concatenate(meshes)
    model.metadata["name"] = clean_name(config["name"])
    model.fix_normals()
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate corrected rectangular Greg Allen shed STL for Bambu Studio.")
    parser.add_argument("config", type=Path, help="Path to Greg Allen shed JSON config.")
    parser.add_argument("--out-dir", type=Path, default=Path("model_build"), help="Output directory.")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    model = build_model(config)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stl_path = args.out_dir / f"{clean_name(config['name'])}.stl"
    model.export(stl_path)
    print(f"Generated STL: {stl_path}")
    print(f"Extents mm: {[round(v, 2) for v in model.extents.tolist()]}")


if __name__ == "__main__":
    main()
