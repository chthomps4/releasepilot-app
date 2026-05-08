# releasepilot-app

GitHub App for org-wide release policy, pull request compliance, and release readiness dashboards.

## 3D print model builder

This repository now includes a starter workflow for building a 3D-printable model from a dimensioned 2D shop drawing for use with Bambu Studio and a Bambu Lab P1S.

### Generate a model locally

```bash
python3 scripts/build_shop_part.py models/example_shop_part.json
```

That creates an OpenSCAD file in `model_build/`.

If OpenSCAD is installed, generate an STL directly:

```bash
python3 scripts/build_shop_part.py models/example_shop_part.json --stl
```

Then open the STL in Bambu Studio, select the Bambu Lab P1S profile, slice, inspect, and send the sliced job to the printer.

### Files added

- `scripts/build_shop_part.py` — converts a shop-drawing JSON file into OpenSCAD and optionally STL.
- `models/example_shop_part.json` — editable example dimensions.
- `docs/bambu-p1s-shop-drawing-workflow.md` — step-by-step model and slicer workflow.
- `.github/workflows/build-3d-models.yml` — optional GitHub Actions build that exports STL artifacts when model files change.

### Current model support

The first version supports flat extruded parts with:

- custom outside outline
- part thickness
- rounded outside corners
- circular holes
- slotted holes
- rectangular cutouts
- millimeter or inch input

Good next additions are countersunk holes, counterbores, chamfers, raised bosses, text labels, and DXF import.
