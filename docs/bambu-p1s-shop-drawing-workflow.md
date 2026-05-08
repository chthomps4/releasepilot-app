# Bambu Lab P1S shop-drawing-to-print workflow

This workflow turns a dimensioned 2D shop drawing into a clean 3D model that Bambu Studio can slice for a Bambu Lab P1S.

## What this produces

- A `.scad` model file generated from dimensions.
- An optional `.stl` file if OpenSCAD is installed.
- A repeatable JSON source file that can be edited when the drawing changes.

The printer itself should still receive sliced output from Bambu Studio. Do not hand-write machine G-code for the P1S unless you are deliberately testing machine control and understand the risk.

## Basic workflow

1. Measure the 2D shop drawing.
2. Create a JSON model config in `models/`.
3. Generate the OpenSCAD file:

```bash
python3 scripts/build_shop_part.py models/example_shop_part.json
```

4. If OpenSCAD is installed, generate an STL directly:

```bash
python3 scripts/build_shop_part.py models/example_shop_part.json --stl
```

5. Open the STL in Bambu Studio.
6. Select printer: `Bambu Lab P1S`.
7. Select the right filament profile.
8. Slice, inspect, then send to the printer.

## JSON fields

Required fields:

```json
{
  "name": "part_name",
  "units": "mm",
  "thickness": 6,
  "outline": [[0, 0], [90, 0], [90, 42], [0, 42]]
}
```

Optional fields:

```json
{
  "corner_radius": 1.5,
  "fn": 96,
  "holes": [
    {"x": 15, "y": 15, "diameter": 5.2}
  ],
  "slots": [
    {"x1": 18, "y1": 48, "x2": 42, "y2": 48, "diameter": 6.5}
  ],
  "rectangular_cutouts": [
    {"x": 68, "y": 28, "width": 16, "height": 10, "center": true}
  ]
}
```

## Coordinate system

- Points are entered as `[x, y]`.
- Units may be `mm` or `in`.
- The generated OpenSCAD file is always converted to millimeters.
- Outline points should go around the outside perimeter in order.
- Holes, slots, and cutouts are subtracted from the body.

## Bambu P1S starting settings

For a first functional prototype in PLA or PETG:

- Nozzle: `0.4 mm`
- Layer height: `0.20 mm`
- Walls: `3`
- Top layers: `5`
- Bottom layers: `5`
- Infill: `20% gyroid` for normal parts, `35%+` for stronger brackets
- Supports: off unless overhangs are added later
- Brim: use for tall, narrow, or warp-prone parts
- Orientation: keep the largest flat face on the build plate when possible

## Tolerance notes

Typical starting clearances:

- Screw clearance hole: nominal screw diameter + `0.2 mm` to `0.5 mm`
- Snug peg/socket fit: add `0.15 mm` to `0.3 mm` clearance per side
- Loose fit: add `0.4 mm` to `0.7 mm` clearance per side
- Press fit: test with a small coupon first

Print a small test section before committing to a full functional part.

## Suggested next upgrade

The current generator handles flat extruded parts. Good next additions would be:

- countersunk holes
- counterbored holes
- chamfers
- bosses/standoffs
- text labels
- DXF import
- multi-view shop drawing support
