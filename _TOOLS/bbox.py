import math
def arc_bbox(cx, cy, r, a0, a1):
    """Exacte bbox van een CCW-boog (hoeken in radialen)."""
    pts = [(cx+r*math.cos(a0), cy+r*math.sin(a0)),
           (cx+r*math.cos(a1), cy+r*math.sin(a1))]
    sweep = (a1 - a0) % (2*math.pi)
    for k in range(4):                       # 0, 90, 180, 270 graden
        ang = k*math.pi/2
        if ((ang - a0) % (2*math.pi)) <= sweep:
            pts.append((cx+r*math.cos(ang), cy+r*math.sin(ang)))
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)

def bbox(e):
    t = e.get("type")
    if t == "line":
        (x0,y0),(x1,y1) = e["start"][:2], e["end"][:2]
        return min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)
    if t == "circle":
        cx,cy = e["center"][:2]; r = e["radius"]; return cx-r,cy-r,cx+r,cy+r
    if t == "arc":
        return arc_bbox(*e["center"][:2], e["radius"], e["start_angle"], e["end_angle"])
    if t == "lwpolyline":
        xs=[v[0] for v in e["vertices"]]; ys=[v[1] for v in e["vertices"]]
        return min(xs),min(ys),max(xs),max(ys)
    if t in ("text","mtext"):
        x,y = e["position"][:2]; return x,y,x,y
    return None
