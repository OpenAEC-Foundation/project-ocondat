"""Generate DXF files + js/data.js from extracted Revit data (v3).

Usage:
    python gen_all.py              # all components
    python gen_all.py --limit 30   # 30 diverse components for experimenting
"""
import json, re, os, math, argparse

base = os.path.dirname(os.path.abspath(__file__))
dxf_dir = os.path.join(base, 'components', 'dxf')
data_dir = os.path.join(base, 'data')
js_dir = os.path.join(base, 'js')
os.makedirs(dxf_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--limit', type=int, default=0, help='Limit to N diverse components')
args = parser.parse_args()

# --- DXF linetype definitions ---
LTYPES = {
    'solid': ('CONTINUOUS', []),
    'center': ('CENTER', [12.7, -6.35, 3.175, -6.35]),
    'hidden': ('HIDDEN', [6.35, -3.175]),
    'dashed': ('DASHED', [6.35, -6.35]),
}

# --- Read types TSV ---
names = {}
with open(os.path.join(data_dir, 'all_types.tsv'), 'r') as f:
    for line in f.readlines()[1:]:
        parts = line.strip().split('\t')
        if len(parts) >= 5:
            names[int(parts[0])] = (parts[3], parts[4])

# --- Read curves data (v3 format with optional style suffix) ---
components = []
with open(os.path.join(data_dir, 'all_curves_v3.dat'), 'r') as f:
    current = None
    for line in f:
        line = line.rstrip()
        if line.startswith('#'):
            if current and current['curves']:
                components.append(current)
            parts = line[1:].split('\t')
            tid = int(parts[0])
            fam, typ = names.get(tid, ('unknown', 'unknown'))
            current = {
                'tid': tid, 'eid': int(parts[1]), 'vid': int(parts[2]),
                'bb': [float(parts[3]), float(parts[4]), float(parts[5]), float(parts[6])],
                'fam': fam, 'typ': typ, 'curves': []
            }
        elif current and line:
            # Skip reference planes (center line style)
            parts = line.split('|')
            style = None
            if parts[0] == 'L' and len(parts) > 5:
                style = parts[5]
            elif parts[0] == 'A' and len(parts) > 8:
                style = parts[8]
            if style != 'center':
                current['curves'].append(line)
    if current and current['curves']:
        components.append(current)

print(f'Loaded {len(components)} components (reference planes excluded)')

# --- Read filled regions data ---
fr_data = {}  # tid -> list of { pattern, boundary_curves }
fr_path = os.path.join(data_dir, 'all_filled_regions.dat')
if os.path.exists(fr_path):
    with open(fr_path, 'r') as f:
        current_tid = None
        current_hatch = None
        for line in f:
            line = line.rstrip()
            if line.startswith('F|'):
                if current_hatch and current_hatch['boundary']:
                    fr_data.setdefault(current_tid, []).append(current_hatch)
                parts = line.split('|')
                current_tid = int(parts[1])
                current_hatch = {'pattern': parts[2], 'boundary': []}
            elif line.startswith('FL|') or line.startswith('FA|'):
                if current_hatch is not None:
                    current_hatch['boundary'].append(line)
        if current_hatch and current_hatch['boundary']:
            fr_data.setdefault(current_tid, []).append(current_hatch)
    print(f'Loaded filled regions for {len(fr_data)} component types')

# --- Select diverse subset when --limit is used ---
def select_diverse(components, limit):
    """Select components from diverse family prefixes, preferring those with hatches."""
    # Group by family prefix (first 2 digits)
    by_prefix = {}
    for c in components:
        m = re.match(r'^(\d{2})', c['fam'].strip())
        prefix = m.group(1) if m else '??'
        by_prefix.setdefault(prefix, []).append(c)

    prefixes = sorted(by_prefix.keys())
    print(f'Found {len(prefixes)} family prefixes: {", ".join(prefixes)}')

    # Sort each group: hatched first, then by number of curves (more interesting first)
    for p in prefixes:
        by_prefix[p].sort(key=lambda c: (
            0 if c['tid'] in fr_data else 1,  # hatched first
            -len(c['curves'])                   # more curves = more interesting
        ))

    # Round-robin pick from each prefix
    selected = []
    per_prefix = max(1, limit // len(prefixes))
    remainder = limit - per_prefix * len(prefixes)

    for p in prefixes:
        take = min(per_prefix, len(by_prefix[p]))
        selected.extend(by_prefix[p][:take])

    # Fill remainder from largest groups
    if remainder > 0:
        for p in sorted(prefixes, key=lambda p: len(by_prefix[p]), reverse=True):
            available = by_prefix[p][per_prefix:]
            for c in available:
                if len(selected) >= limit:
                    break
                selected.append(c)
            if len(selected) >= limit:
                break

    return selected[:limit]

if args.limit > 0:
    components = select_diverse(components, args.limit)
    print(f'Selected {len(components)} diverse components')

# --- Arc center calculation ---
def arc_center(x0, y0, x1, y1, r, large, sweep):
    dx, dy = x1 - x0, y1 - y0
    d = math.sqrt(dx*dx + dy*dy)
    if d > 2*r:
        r = d/2 + 0.01
    a = d / 2
    h = math.sqrt(max(r*r - a*a, 0))
    mx, my = (x0+x1)/2, (y0+y1)/2
    cx1 = mx + h*(y0-y1)/d
    cy1 = my + h*(x1-x0)/d
    cx2 = mx - h*(y0-y1)/d
    cy2 = my - h*(x1-x0)/d
    if (large == 0 and sweep == 1) or (large == 1 and sweep == 0):
        return cx1, cy1, r
    return cx2, cy2, r

def parse_curve(curve_str):
    """Parse curve string, return (type, params, style)"""
    p = curve_str.split('|')
    if p[0] == 'L':
        style = p[5] if len(p) > 5 else 'solid'
        return 'L', (float(p[1]), float(p[2]), float(p[3]), float(p[4])), style
    elif p[0] == 'A':
        style = p[8] if len(p) > 8 else 'solid'
        return 'A', (float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5]), int(p[6]), int(p[7])), style
    return None, None, 'solid'

# --- Write DXF with linetypes ---
def write_dxf(filepath, curves):
    styles_used = set()
    for curve in curves:
        _, _, style = parse_curve(curve)
        styles_used.add(style)

    lines = []
    lines.append("0\nSECTION\n2\nHEADER\n0\nENDSEC")
    lines.append("0\nSECTION\n2\nTABLES")
    lines.append("0\nTABLE\n2\nLTYPE\n70\n%d" % (len(styles_used) + 1))
    lines.append("0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid line\n72\n65\n73\n0\n40\n0.0")
    for sname in styles_used:
        if sname == 'solid':
            continue
        lt_name, segs = LTYPES.get(sname, ('CONTINUOUS', []))
        if segs:
            total = sum(abs(s) for s in segs)
            lines.append("0\nLTYPE\n2\n%s\n70\n0\n3\n%s\n72\n65\n73\n%d\n40\n%s" % (
                lt_name, sname, len(segs), total))
            for s in segs:
                lines.append("49\n%s" % s)
    lines.append("0\nENDTAB")
    lines.append("0\nTABLE\n2\nLAYER\n70\n1")
    lines.append("0\nLAYER\n2\n0\n70\n0\n62\n7\n6\nCONTINUOUS")
    lines.append("0\nENDTAB")
    lines.append("0\nENDSEC")
    lines.append("0\nSECTION\n2\nENTITIES")

    for curve in curves:
        ctype, params, style = parse_curve(curve)
        lt_name = LTYPES.get(style, ('CONTINUOUS', []))[0]

        if ctype == 'L':
            x0, y0, x1, y1 = params
            lines.append("0\nLINE\n8\n0\n6\n%s\n10\n%s\n20\n%s\n30\n0\n11\n%s\n21\n%s\n31\n0" % (lt_name, x0, y0, x1, y1))
        elif ctype == 'A':
            x0, y0, x1, y1, r, la, sf = params
            cx, cy, rr = arc_center(x0, y0, x1, y1, r, la, sf)
            sa = math.degrees(math.atan2(y0 - cy, x0 - cx))
            ea = math.degrees(math.atan2(y1 - cy, x1 - cx))
            if sa < 0: sa += 360
            if ea < 0: ea += 360
            if sf == 1:
                lines.append("0\nARC\n8\n0\n6\n%s\n10\n%s\n20\n%s\n30\n0\n40\n%s\n50\n%s\n51\n%s" % (lt_name, cx, cy, rr, sa, ea))
            else:
                lines.append("0\nARC\n8\n0\n6\n%s\n10\n%s\n20\n%s\n30\n0\n40\n%s\n50\n%s\n51\n%s" % (lt_name, cx, cy, rr, ea, sa))

    lines.append("0\nENDSEC\n0\nEOF")
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))

# --- Process all ---
def safe_filename(fam, typ):
    name = (fam.strip() + '__' + typ).replace(' ', '_').replace('/', '_')
    return re.sub(r'[^a-zA-Z0-9_\-.]', '', name) + '.dxf'

def calc_bb(curves):
    """Recalculate bounding box from curves (without center lines)."""
    mnX, mnY, mxX, mxY = 1e9, 1e9, -1e9, -1e9
    for curve in curves:
        ctype, params, _ = parse_curve(curve)
        if ctype == 'L':
            x0, y0, x1, y1 = params
            mnX = min(mnX, x0, x1); mxX = max(mxX, x0, x1)
            mnY = min(mnY, y0, y1); mxY = max(mxY, y0, y1)
        elif ctype == 'A':
            x0, y0, x1, y1 = params[:4]
            mnX = min(mnX, x0, x1); mxX = max(mxX, x0, x1)
            mnY = min(mnY, y0, y1); mxY = max(mxY, y0, y1)
    if mnX > mxX:
        return [0, 0, 0, 0]
    return [mnX, mnY, mxX, mxY]

db_comps = []
for c in components:
    fname = safe_filename(c['fam'], c['typ'])
    fpath = os.path.join(dxf_dir, fname)
    write_dxf(fpath, c['curves'])
    bb = calc_bb(c['curves'])
    comp_entry = {
        'element_id': c['eid'], 'type_id': c['tid'],
        'family': c['fam'], 'type': c['typ'],
        'width_mm': round(bb[2]-bb[0], 1), 'height_mm': round(bb[3]-bb[1], 1),
        'dxf': 'components/dxf/' + fname,
        'curves': c['curves']
    }
    # Add hatches if available
    if c['tid'] in fr_data:
        comp_entry['hatches'] = fr_data[c['tid']]
    db_comps.append(comp_entry)

hatched = sum(1 for c in db_comps if 'hatches' in c)
print(f'Generated {len(db_comps)} DXF files ({hatched} with hatching)')

# --- Write js/data.js ---
db = {'source': 'Project OconDat', 'version': '4.0', 'total': len(db_comps), 'components': db_comps}

js_content = 'const DB = ' + json.dumps(db, indent=2) + ';\n'
with open(os.path.join(js_dir, 'data.js'), 'w') as f:
    f.write(js_content)
print(f'Written js/data.js ({len(js_content)//1024} KB)')

# --- Also write components.json for reference ---
with open(os.path.join(data_dir, 'components.json'), 'w') as f:
    json.dump(db, f, indent=2)

print('Done!')
