#!/usr/bin/env python3
"""
Build a simple 3D-printable model from a dimensioned 2D shop drawing.

The workflow is:
1. Translate the shop drawing into a JSON config.
2. Run this script to generate an OpenSCAD file.
3. Optionally run OpenSCAD from the script to export an STL.
4. Import the STL into Bambu Studio for slicing on the Bambu Lab P1S.

This is intentionally conservative: the model comes from explicit dimensions,
not image tracing, so the part stays measurable and repeatable.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable


MM_PER_INCH = 25.4


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    required = ["name", "units", "thickness", "outline"]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"Missing required config field(s): {', '.join(missing)}")

    if config["units"] not in {"mm", "in"}:
        raise ValueError("units must be either 'mm' or 'in'")

    if not isinstance(config["outline"], list) or len(config["outline"]) < 3:
        raise ValueError("outline must contain at least three [x, y] points")

    return config


def scale_for_units(units: str) -> float:
    return MM_PER_INCH if units == "in" else 1.0


def mm(value: float | int, scale: float) -> float:
    return round(float(value) * scale, 5)


def point_to_scad(point: Iterable[float | int], scale: float) -> str:
    x, y = point
    return f"[{mm(x, scale)}, {mm(y, scale)}]"


def list_to_scad(points: list[list[float | int]], scale: float) -> str:
    return "[" + ", ".join(point_to_scad(point, scale) for point in points) + "]"


def clean_name(name: str) -> str:
    allowed = [character if character.isalnum() or character in "-_" else "_" for character in name.strip()]
    return "".join(allowed).strip("_") or "shop_part"


def generate_scad(config: dict[str, Any]) -> str:
    scale = scale_for_units(config["units"])
    name = clean_name(str(config["name"]))
    thickness = mm(config["thickness"], scale)
    outline = list_to_scad(config["outline"], scale)
    corner_radius = mm(config.get("corner_radius", 0), scale)
    fn = int(config.get("fn", 96))

    holes = config.get("holes", [])
    slots = config.get("slots", [])
    rectangular_cutouts = config.get("rectangular_cutouts", [])

    lines: list[str] = [
        f"// Generated from shop-drawing config: {name}",
        "// Units in this OpenSCAD file are millimeters.",
        f"$fn = {fn};",
        "",
        f"part_thickness = {thickness};",
        f"corner_radius = {corner_radius};",
        "",
        "linear_extrude(height = part_thickness)",
        "difference() {",
        "  base_outline();",
    ]

    for index, hole in enumerate(holes, start=1):
        x = mm(hole["x"], scale)
        y = mm(hole["y"], scale)
        diameter = mm(hole["diameter"], scale)
        lines.extend(
            [
                f"  // Hole {index}",
                f"  translate([{x}, {y}]) circle(d = {diameter});",
            ]
        )

    for index, slot in enumerate(slots, start=1):
        x1 = mm(slot["x1"], scale)
        y1 = mm(slot["y1"], scale)
        x2 = mm(slot["x2"], scale)
        y2 = mm(slot["y2"], scale)
        diameter = mm(slot["diameter"], scale)
        lines.extend(
            [
                f"  // Slot {index}",
                "  hull() {",
                f"    translate([{x1}, {y1}]) circle(d = {diameter});",
                f"    translate([{x2}, {y2}]) circle(d = {diameter});",
                "  }",
            ]
        )

    for index, cutout in enumerate(rectangular_cutouts, start=1):
        x = mm(cutout["x"], scale)
        y = mm(cutout["y"], scale)
        width = mm(cutout["width"], scale)
        height = mm(cutout["height"], scale)
        center = str(bool(cutout.get("center", True))).lower()
        lines.extend(
            [
                f"  // Rectangular cutout {index}",
                f"  translate([{x}, {y}]) square([{width}, {height}], center = {center});",
            ]
        )

    lines.extend(
        [
            "}",
            "",
            "module base_outline() {",
        ]
    )

    if corner_radius > 0:
        lines.extend(
            [
                "  // For exact sharp-corner dimensions, set corner_radius to 0 in the config.",
                "  offset(r = corner_radius)",
                "    offset(delta = -corner_radius)",
                f"      polygon(points = {outline});",
            ]
        )
    else:
        lines.append(f"  polygon(points = {outline});")

    lines.extend(
        [
            "}",
            "",
        ]
    )

    return "\n".join(lines)


def write_scad(config_path: Path, output_dir: Path) -> Path:
    config = load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    part_name = clean_name(str(config["name"]))
    scad_path = output_dir / f"{part_name}.scad"
    scad_path.write_text(generate_scad(config), encoding="utf-8")
    return scad_path


def export_stl(scad_path: Path, openscad_binary: str) -> Path:
    openscad = shutil.which(openscad_binary)
    if not openscad:
        raise RuntimeError(
            f"OpenSCAD executable '{openscad_binary}' was not found. "
            "Install OpenSCAD or run without --stl and export manually."
        )

    stl_path = scad_path.with_suffix(".stl")
    subprocess.run([openscad, "-o", str(stl_path), str(scad_path)], check=True)
    return stl_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an OpenSCAD/STL model from a 2D shop-drawing JSON file.")
    parser.add_argument("config", type=Path, help="Path to the shop drawing JSON config.")
    parser.add_argument("--out-dir", type=Path, default=Path("model_build"), help="Directory for generated files.")
    parser.add_argument("--stl", action="store_true", help="Also export STL using the OpenSCAD command-line tool.")
    parser.add_argument("--openscad", default="openscad", help="OpenSCAD executable name or full path.")
    args = parser.parse_args()

    scad_path = write_scad(args.config, args.out_dir)
    print(f"Generated OpenSCAD: {scad_path}")

    if args.stl:
        stl_path = export_stl(scad_path, args.openscad)
        print(f"Generated STL: {stl_path}")
    else:
        print("Next step: open the SCAD file in OpenSCAD, export STL, then import the STL into Bambu Studio.")


if __name__ == "__main__":
    main()
