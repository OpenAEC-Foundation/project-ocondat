"""Extract detail components from Revit via MCP execute_revit_code.

Generates IronPython 2.7 code strings for each extraction step.
Run each step's code via the Revit MCP connection (execute_revit_code).
Results are written to library/data/extraction/ as JSON files.

Usage:
    # Print the code for each step (copy-paste into MCP):
    python extract_from_revit.py --step 1a
    python extract_from_revit.py --step 1b
    python extract_from_revit.py --step 1c
    python extract_from_revit.py --step 1d

    # Or print all steps:
    python extract_from_revit.py --step all
"""
import argparse, os, json

base = os.path.dirname(os.path.abspath(__file__))
extraction_dir = os.path.join(base, 'data', 'extraction')
os.makedirs(extraction_dir, exist_ok=True)

# Resolve output path for use inside IronPython code strings
OUT_DIR = extraction_dir.replace('\\', '/')


def step_1a():
    """Discovery: collect all detail component types + generic annotations."""
    return r'''
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
import json, os

doc = DocumentManager.Instance.CurrentDBDocument
OUT_DIR = "''' + OUT_DIR + r'''"

# --- Detail Components ---
dc_collector = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_DetailComponents)

# Collect types
dc_types = {}
for el in dc_collector:
    if isinstance(el, FamilySymbol):
        tid = el.Id.IntegerValue
        fam = el.Family.Name if el.Family else "unknown"
        typ = el.Name if el.Name else "unknown"
        dc_types[tid] = {"family": fam, "type": typ, "instance_id": 0, "view_id": 0}

# Collect instances to find representative instance + view per type
dc_inst_collector = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_DetailComponents).WhereElementIsNotElementType()

views_with_dc = set()
for inst in dc_inst_collector:
    tid = inst.GetTypeId().IntegerValue
    if tid in dc_types and dc_types[tid]["instance_id"] == 0:
        dc_types[tid]["instance_id"] = inst.Id.IntegerValue
        dc_types[tid]["view_id"] = inst.OwnerViewId.IntegerValue
        views_with_dc.add(inst.OwnerViewId.IntegerValue)

# Filter out types without instances
dc_types = {k: v for k, v in dc_types.items() if v["instance_id"] != 0}

# --- Generic Annotations ---
ga_collector = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType()

ga_instances = []
for inst in ga_collector:
    tid = inst.GetTypeId().IntegerValue
    fs = doc.GetElement(inst.GetTypeId())
    fam = fs.Family.Name if fs and fs.Family else "unknown"
    typ = fs.Name if fs else "unknown"
    ga_instances.append({
        "instance_id": inst.Id.IntegerValue,
        "type_id": tid,
        "view_id": inst.OwnerViewId.IntegerValue,
        "family": fam,
        "type": typ
    })

result = {
    "detail_components": dc_types,
    "generic_annotations": ga_instances,
    "views_with_dc": list(views_with_dc),
    "total_dc_types": len(dc_types),
    "total_ga_instances": len(ga_instances)
}

out_path = os.path.join(OUT_DIR, "types.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=2)

OUT = "Discovered %d detail component types, %d generic annotations. Saved to %s" % (
    len(dc_types), len(ga_instances), out_path)
'''


def step_1b(batch_start=0, batch_size=200):
    """Geometry extraction for detail component types (batch)."""
    return r'''
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
import json, os, math

doc = DocumentManager.Instance.CurrentDBDocument
OUT_DIR = "''' + OUT_DIR + r'''"
BATCH_START = ''' + str(batch_start) + r'''
BATCH_SIZE = ''' + str(batch_size) + r'''
FEET_TO_MM = 304.8
MAX_NEST_DEPTH = 3

# Load types.json from step 1a
with open(os.path.join(OUT_DIR, "types.json"), "r") as f:
    types_data = json.load(f)

dc_types = types_data["detail_components"]
type_ids = sorted(dc_types.keys(), key=lambda x: int(x))
batch_ids = type_ids[BATCH_START:BATCH_START + BATCH_SIZE]

def classify_style(gs_id):
    """Classify line style from GraphicsStyleId."""
    if gs_id == ElementId.InvalidElementId:
        return "solid"
    gs = doc.GetElement(gs_id)
    if gs is None:
        return "solid"
    name = gs.Name.lower() if gs.Name else ""
    if "center" in name or "reference" in name:
        return "center"
    if "hidden" in name:
        return "hidden"
    if "dash" in name:
        return "dashed"
    return "solid"

def extract_curves(geom, depth=0):
    """Recursively extract lines and arcs from geometry."""
    curves = []
    if geom is None or depth > MAX_NEST_DEPTH:
        return curves
    for g in geom:
        if isinstance(g, Line):
            s = g.GetEndPoint(0)
            e = g.GetEndPoint(1)
            style = classify_style(g.GraphicsStyleId)
            x0 = round(s.X * FEET_TO_MM, 2)
            y0 = round(s.Y * FEET_TO_MM, 2)
            x1 = round(e.X * FEET_TO_MM, 2)
            y1 = round(e.Y * FEET_TO_MM, 2)
            curves.append("L|%s|%s|%s|%s|%s" % (x0, y0, x1, y1, style))
        elif isinstance(g, Arc):
            s = g.GetEndPoint(0)
            e = g.GetEndPoint(1)
            r = round(g.Radius * FEET_TO_MM, 2)
            style = classify_style(g.GraphicsStyleId)
            normal = g.Normal
            # Determine sweep: CCW if normal.Z > 0
            sweep = 1 if normal.Z > 0 else 0
            # Determine large arc flag
            param_range = abs(g.GetEndParameter(1) - g.GetEndParameter(0))
            large = 1 if param_range > math.pi else 0
            x0 = round(s.X * FEET_TO_MM, 2)
            y0 = round(s.Y * FEET_TO_MM, 2)
            x1 = round(e.X * FEET_TO_MM, 2)
            y1 = round(e.Y * FEET_TO_MM, 2)
            curves.append("A|%s|%s|%s|%s|%s|%s|%s|%s" % (
                x0, y0, x1, y1, r, large, sweep, style))
        elif isinstance(g, GeometryInstance):
            nested = g.GetInstanceGeometry()
            curves.extend(extract_curves(nested, depth + 1))
    return curves

results = []
for tid_str in batch_ids:
    tid = int(tid_str)
    info = dc_types[tid_str]
    eid = info["instance_id"]
    vid = info["view_id"]

    elem = doc.GetElement(ElementId(eid))
    view = doc.GetElement(ElementId(vid))
    if elem is None or view is None:
        continue

    opt = Options()
    opt.View = view
    opt.ComputeReferences = False
    geom = elem.get_Geometry(opt)
    curves = extract_curves(geom)

    if not curves:
        continue

    # Calculate bounding box
    xs = []
    ys = []
    for c in curves:
        p = c.split("|")
        if p[0] == "L":
            xs.extend([float(p[1]), float(p[3])])
            ys.extend([float(p[2]), float(p[4])])
        elif p[0] == "A":
            xs.extend([float(p[1]), float(p[3])])
            ys.extend([float(p[2]), float(p[4])])

    bb = [min(xs), min(ys), max(xs), max(ys)] if xs else [0, 0, 0, 0]

    results.append({
        "type_id": tid,
        "element_id": eid,
        "view_id": vid,
        "family": info["family"],
        "type": info["type"],
        "bb": bb,
        "curves": curves
    })

# Write results (append-safe: use batch index in filename)
out_path = os.path.join(OUT_DIR, "curves_%d.json" % BATCH_START)
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

OUT = "Extracted %d components (batch %d-%d). Saved to %s" % (
    len(results), BATCH_START, BATCH_START + BATCH_SIZE, out_path)
'''


def step_1c():
    """Extract filled regions linked to detail component views."""
    return r'''
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
import json, os, math

doc = DocumentManager.Instance.CurrentDBDocument
OUT_DIR = "''' + OUT_DIR + r'''"
FEET_TO_MM = 304.8

# Load types.json to know which views have detail components
with open(os.path.join(OUT_DIR, "types.json"), "r") as f:
    types_data = json.load(f)

views_with_dc = set(types_data["views_with_dc"])
dc_types = types_data["detail_components"]

# Build type_id -> bounding box lookup from extracted curves
type_bbs = {}
for fname in os.listdir(OUT_DIR):
    if fname.startswith("curves_") and fname.endswith(".json"):
        with open(os.path.join(OUT_DIR, fname), "r") as f:
            for comp in json.load(f):
                tid = comp["type_id"]
                type_bbs[tid] = {
                    "bb": comp["bb"],
                    "view_id": comp["view_id"]
                }

def get_pattern_name(pattern_id):
    """Get fill pattern name from pattern ID."""
    if pattern_id == ElementId.InvalidElementId:
        return None
    pat = doc.GetElement(pattern_id)
    if pat is None:
        return None
    return pat.Name

def extract_boundary(region):
    """Extract boundary curves from a filled region."""
    boundaries = []
    try:
        loops = region.GetBoundaries()
        for loop in loops:
            for curve in loop:
                if isinstance(curve, Line):
                    s = curve.GetEndPoint(0)
                    e = curve.GetEndPoint(1)
                    x0 = round(s.X * FEET_TO_MM, 2)
                    y0 = round(s.Y * FEET_TO_MM, 2)
                    x1 = round(e.X * FEET_TO_MM, 2)
                    y1 = round(e.Y * FEET_TO_MM, 2)
                    boundaries.append("FL|%s|%s|%s|%s" % (x0, y0, x1, y1))
                elif isinstance(curve, Arc):
                    s = curve.GetEndPoint(0)
                    e = curve.GetEndPoint(1)
                    r = round(curve.Radius * FEET_TO_MM, 2)
                    normal = curve.Normal
                    sweep = 1 if normal.Z > 0 else 0
                    param_range = abs(curve.GetEndParameter(1) - curve.GetEndParameter(0))
                    large = 1 if param_range > math.pi else 0
                    x0 = round(s.X * FEET_TO_MM, 2)
                    y0 = round(s.Y * FEET_TO_MM, 2)
                    x1 = round(e.X * FEET_TO_MM, 2)
                    y1 = round(e.Y * FEET_TO_MM, 2)
                    boundaries.append("FA|%s|%s|%s|%s|%s|%s|%s" % (
                        x0, y0, x1, y1, r, large, sweep))
    except:
        pass
    return boundaries

# Collect all filled regions from views that contain detail components
fr_collector = FilteredElementCollector(doc).OfClass(FilledRegion)

results = []
for fr in fr_collector:
    vid = fr.OwnerViewId.IntegerValue
    if vid not in views_with_dc:
        continue

    boundary = extract_boundary(fr)
    if not boundary:
        continue

    # Get foreground and background patterns
    fr_type = doc.GetElement(fr.GetTypeId())
    fg_pattern = None
    bg_pattern = None
    if fr_type:
        fg_id = fr_type.ForegroundPatternId if hasattr(fr_type, "ForegroundPatternId") else ElementId.InvalidElementId
        bg_id = fr_type.BackgroundPatternId if hasattr(fr_type, "BackgroundPatternId") else ElementId.InvalidElementId
        fg_pattern = get_pattern_name(fg_id)
        bg_pattern = get_pattern_name(bg_id)

    # If no foreground pattern, try the fill pattern from the type
    if fg_pattern is None:
        try:
            fg_id = fr_type.GetCompoundStructure()
        except:
            pass

    # Calculate filled region bounding box for matching
    fr_bb = None
    bx = fr.get_BoundingBox(None)
    if bx:
        fr_bb = [
            round(bx.Min.X * FEET_TO_MM, 2), round(bx.Min.Y * FEET_TO_MM, 2),
            round(bx.Max.X * FEET_TO_MM, 2), round(bx.Max.Y * FEET_TO_MM, 2)
        ]

    # Match to closest detail component type by bounding box overlap
    best_tid = None
    best_overlap = 0
    for tid, info in type_bbs.items():
        if info["view_id"] != vid:
            continue
        cbb = info["bb"]
        if fr_bb is None:
            continue
        # Calculate overlap area
        ox = max(0, min(cbb[2], fr_bb[2]) - max(cbb[0], fr_bb[0]))
        oy = max(0, min(cbb[3], fr_bb[3]) - max(cbb[1], fr_bb[1]))
        overlap = ox * oy
        if overlap > best_overlap:
            best_overlap = overlap
            best_tid = tid

    if best_tid is None:
        continue

    entry = {
        "type_id": best_tid,
        "view_id": vid,
        "element_id": fr.Id.IntegerValue,
        "bb": fr_bb
    }
    if fg_pattern:
        entry["foreground"] = {"pattern": fg_pattern, "boundary": boundary}
    if bg_pattern:
        entry["background"] = {"pattern": bg_pattern, "boundary": boundary}
    # If neither pattern found, default to solid foreground
    if not fg_pattern and not bg_pattern:
        entry["foreground"] = {"pattern": "solid", "boundary": boundary}

    results.append(entry)

out_path = os.path.join(OUT_DIR, "filled_regions.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

OUT = "Extracted %d filled regions. Saved to %s" % (len(results), out_path)
'''


def step_1d():
    """Extract generic annotations geometry."""
    return r'''
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
import json, os, math

doc = DocumentManager.Instance.CurrentDBDocument
OUT_DIR = "''' + OUT_DIR + r'''"
FEET_TO_MM = 304.8
MAX_NEST_DEPTH = 3

# Load types.json
with open(os.path.join(OUT_DIR, "types.json"), "r") as f:
    types_data = json.load(f)

ga_instances = types_data["generic_annotations"]

def classify_style(gs_id):
    if gs_id == ElementId.InvalidElementId:
        return "solid"
    gs = doc.GetElement(gs_id)
    if gs is None:
        return "solid"
    name = gs.Name.lower() if gs.Name else ""
    if "center" in name or "reference" in name:
        return "center"
    if "hidden" in name:
        return "hidden"
    if "dash" in name:
        return "dashed"
    return "solid"

def extract_curves(geom, depth=0):
    curves = []
    if geom is None or depth > MAX_NEST_DEPTH:
        return curves
    for g in geom:
        if isinstance(g, Line):
            s = g.GetEndPoint(0)
            e = g.GetEndPoint(1)
            style = classify_style(g.GraphicsStyleId)
            x0 = round(s.X * FEET_TO_MM, 2)
            y0 = round(s.Y * FEET_TO_MM, 2)
            x1 = round(e.X * FEET_TO_MM, 2)
            y1 = round(e.Y * FEET_TO_MM, 2)
            curves.append("L|%s|%s|%s|%s|%s" % (x0, y0, x1, y1, style))
        elif isinstance(g, Arc):
            s = g.GetEndPoint(0)
            e = g.GetEndPoint(1)
            r = round(g.Radius * FEET_TO_MM, 2)
            style = classify_style(g.GraphicsStyleId)
            normal = g.Normal
            sweep = 1 if normal.Z > 0 else 0
            param_range = abs(g.GetEndParameter(1) - g.GetEndParameter(0))
            large = 1 if param_range > math.pi else 0
            x0 = round(s.X * FEET_TO_MM, 2)
            y0 = round(s.Y * FEET_TO_MM, 2)
            x1 = round(e.X * FEET_TO_MM, 2)
            y1 = round(e.Y * FEET_TO_MM, 2)
            curves.append("A|%s|%s|%s|%s|%s|%s|%s|%s" % (
                x0, y0, x1, y1, r, large, sweep, style))
        elif isinstance(g, GeometryInstance):
            nested = g.GetInstanceGeometry()
            curves.extend(extract_curves(nested, depth + 1))
    return curves

results = []
seen_types = set()

for ga in ga_instances:
    eid = ga["instance_id"]
    vid = ga["view_id"]
    tid = ga["type_id"]

    # Only extract one instance per type
    if tid in seen_types:
        continue

    elem = doc.GetElement(ElementId(eid))
    view = doc.GetElement(ElementId(vid))
    if elem is None or view is None:
        continue

    opt = Options()
    opt.View = view
    opt.ComputeReferences = False
    geom = elem.get_Geometry(opt)
    curves = extract_curves(geom)

    if not curves:
        continue

    seen_types.add(tid)

    # Try to get text parameters
    text_params = {}
    for p in elem.Parameters:
        if p.StorageType == StorageType.String:
            val = p.AsString()
            if val:
                text_params[p.Definition.Name] = val

    xs = []
    ys = []
    for c in curves:
        p = c.split("|")
        if p[0] == "L":
            xs.extend([float(p[1]), float(p[3])])
            ys.extend([float(p[2]), float(p[4])])
        elif p[0] == "A":
            xs.extend([float(p[1]), float(p[3])])
            ys.extend([float(p[2]), float(p[4])])

    bb = [min(xs), min(ys), max(xs), max(ys)] if xs else [0, 0, 0, 0]

    results.append({
        "type_id": tid,
        "element_id": eid,
        "view_id": vid,
        "family": ga["family"],
        "type": ga["type"],
        "bb": bb,
        "curves": curves,
        "text_params": text_params
    })

out_path = os.path.join(OUT_DIR, "annotations.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

OUT = "Extracted %d generic annotation types. Saved to %s" % (len(results), out_path)
'''


def print_step(step_name):
    """Print the IronPython code for a given step."""
    steps = {
        '1a': ('Step 1a: Discovery', step_1a),
        '1b': ('Step 1b: Geometry extraction (batch 0)', lambda: step_1b(0, 200)),
        '1c': ('Step 1c: Filled regions', step_1c),
        '1d': ('Step 1d: Generic annotations', step_1d),
    }

    if step_name == 'all':
        for name, (title, func) in steps.items():
            print(f'\n{"="*60}')
            print(f'  {title}')
            print(f'{"="*60}')
            print(func())
        return

    if step_name not in steps:
        print(f'Unknown step: {step_name}')
        print(f'Available: {", ".join(steps.keys())}, all')
        return

    title, func = steps[step_name]
    print(f'# {title}')
    print(func())


def count_types():
    """Check how many types need extraction and suggest batch calls."""
    types_path = os.path.join(extraction_dir, 'types.json')
    if not os.path.exists(types_path):
        print('Run step 1a first to discover types.')
        return

    with open(types_path, 'r') as f:
        data = json.load(f)

    total = data['total_dc_types']
    batch_size = 200
    batches = (total + batch_size - 1) // batch_size

    print(f'Total detail component types: {total}')
    print(f'Suggested batches ({batch_size} per batch): {batches}')
    for i in range(batches):
        start = i * batch_size
        end = min(start + batch_size, total)
        print(f'  Batch {i}: types {start}-{end}')
        print(f'    python extract_from_revit.py --step 1b --batch-start {start}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract detail components from Revit via MCP')
    parser.add_argument('--step', required=True,
                        help='Step to run: 1a, 1b, 1c, 1d, all')
    parser.add_argument('--batch-start', type=int, default=0,
                        help='Batch start index for step 1b')
    parser.add_argument('--batch-size', type=int, default=200,
                        help='Batch size for step 1b')
    parser.add_argument('--count', action='store_true',
                        help='Count types and suggest batch calls')
    args = parser.parse_args()

    if args.count:
        count_types()
    elif args.step == '1b':
        print(f'# Step 1b: Geometry extraction (batch {args.batch_start})')
        print(step_1b(args.batch_start, args.batch_size))
    else:
        print_step(args.step)
