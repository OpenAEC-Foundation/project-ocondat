"""DXF-geometrie geschikt maken voor Revit detaillijnen.

Twee valkuilen die hier expliciet vermeden worden:

1. Welden op afstand stort draadtanden in - de twee flanken van een tand
   liggen bij de tip ~0,7 mm uit elkaar. Er wordt daarom uitsluitend langs
   de KETEN samengevoegd: buren die echt aan elkaar vastzitten.

2. Een boog wordt bewaard als (center, radius, a0, a1) met a1 = a0 + sweep.
   Verschuift een eindpunt, dan wordt de nieuwe hoek UITGEPAKT rond de oude.
   Zonder dat klapt een minieme negatieve draai om naar bijna 2*pi en wordt
   een boogje van een halve millimeter een hele cirkel.
"""
import ezdxf, math

EPS = 1e-6
TOL = 0.00256026 * 304.8                 # Revit ShortCurveTolerance, mm
MARGE = 1.10                             # ruimte boven de tolerantie

def _pt(c, a): return (c["center"][0] + c["radius"]*math.cos(a),
                       c["center"][1] + c["radius"]*math.sin(a))

def _arc(cx, cy, r, a0, a1, laag):
    sweep = (a1 - a0) % (2*math.pi)
    if sweep < EPS: sweep = 2*math.pi
    c = dict(kind="arc", center=(cx, cy), radius=r, a0=a0, a1=a0+sweep, layer=laag)
    c["p0"], c["p1"] = _pt(c, c["a0"]), _pt(c, c["a1"])
    return c

def lees(pad):
    def uitpakken(msp):
        for e in msp:
            if e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                for v in e.virtual_entities(): yield v
            else: yield e
    uit = []
    for c in uitpakken(ezdxf.readfile(pad).modelspace()):
        t, laag = c.dxftype(), c.dxf.layer
        if t == "LINE":
            uit.append(dict(kind="line", p0=(c.dxf.start.x, c.dxf.start.y),
                            p1=(c.dxf.end.x, c.dxf.end.y), layer=laag))
        elif t == "ARC":
            uit.append(_arc(c.dxf.center.x, c.dxf.center.y, c.dxf.radius,
                            math.radians(c.dxf.start_angle),
                            math.radians(c.dxf.end_angle), laag))
        elif t == "CIRCLE":
            for a0 in (0.0, math.pi):
                uit.append(_arc(c.dxf.center.x, c.dxf.center.y, c.dxf.radius,
                                a0, a0 + math.pi, laag))
    return uit

def lengte(c):
    return math.dist(c["p0"], c["p1"]) if c["kind"] == "line" \
           else (c["a1"] - c["a0"]) * c["radius"]

def _verschuif(c, welk, punt):
    c = dict(c)
    if c["kind"] == "line":
        c["p0" if welk == 0 else "p1"] = punt
        return c
    cx, cy = c["center"]
    a = math.atan2(punt[1]-cy, punt[0]-cx)
    oud = c["a0"] if welk == 0 else c["a1"]
    a += 2*math.pi * round((oud - a) / (2*math.pi))     # uitpakken rond de oude hoek
    if welk == 0: c["a0"] = a
    else:         c["a1"] = a
    c["p0"], c["p1"] = _pt(c, c["a0"]), _pt(c, c["a1"])
    return c

def _sleutel(p): return (round(p[0]/EPS), round(p[1]/EPS))

def ketens(curves):
    op_punt = {}
    for i, c in enumerate(curves):
        op_punt.setdefault(_sleutel(c["p0"]), []).append(i)
        op_punt.setdefault(_sleutel(c["p1"]), []).append(i)
    gezien, uit = set(), []
    for start in range(len(curves)):
        if start in gezien: continue
        keten = [start]; gezien.add(start)
        for kant in (0, 1):
            while True:
                i = keten[-1] if kant else keten[0]
                p = curves[i]["p1"] if kant else curves[i]["p0"]
                buren = [j for j in op_punt.get(_sleutel(p), []) if j not in gezien]
                if len(buren) != 1: break
                j = buren[0]; gezien.add(j)
                keten.append(j) if kant else keten.insert(0, j)
        uit.append(keten)
    return uit

def _snijpunt(a, b):
    """Snijpunt van twee oneindige lijnen; None bij (bijna) evenwijdig."""
    (x1, y1), (x2, y2) = a["p0"], a["p1"]
    (x3, y3), (x4, y4) = b["p0"], b["p1"]
    d = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if abs(d) < 1e-12: return None
    t1 = x1*y2 - y1*x2
    t2 = x3*y4 - y3*x4
    return ((t1*(x3-x4) - (x1-x2)*t2)/d, (t1*(y3-y4) - (y1-y2)*t2)/d)


def schoon(curves, tol=TOL*MARGE):
    """Knijp te korte curves eruit door hun eindpunten samen te voegen.

    Er wordt geweld op VERBINDING: alleen curves die exact op dat eindpunt
    eindigen schuiven mee. Twee punten die enkel dicht bij elkaar liggen
    blijven gescheiden, anders stort een draadtand in.

    Het samentrekpunt is bij voorkeur het SNIJPUNT van de twee buren, niet
    het midden van de weggeknepen curve. Bij een afgeronde hoek levert het
    midden namelijk maatverlies op ter grootte van de straal: een kwartboog
    R0,5 in een kophoek trekt de omtrek 0,25 mm naar binnen in x en in y.
    Met het snijpunt wordt de afronding een scherpe hoek en blijft de maat
    exact. Ligt het snijpunt onredelijk ver weg (bijna evenwijdige buren),
    dan valt het terug op het midden.
    """
    cs = [dict(c) for c in curves]
    nul = kort = 0
    via_snijpunt = 0
    while True:
        idx = next((i for i, c in enumerate(cs) if lengte(c) < tol), None)
        if idx is None:
            break
        c = cs.pop(idx)
        L = lengte(c)
        if L < 1e-9: nul += 1
        else: kort += 1
        A, B = _sleutel(c["p0"]), _sleutel(c["p1"])
        M = ((c["p0"][0] + c["p1"][0]) / 2.0, (c["p0"][1] + c["p1"][1]) / 2.0)

        bij_A = [j for j, d in enumerate(cs)
                 if _sleutel(d["p0"]) == A or _sleutel(d["p1"]) == A]
        bij_B = [j for j, d in enumerate(cs)
                 if _sleutel(d["p0"]) == B or _sleutel(d["p1"]) == B]
        doel = M
        if len(bij_A) == 1 and len(bij_B) == 1:
            a, b = cs[bij_A[0]], cs[bij_B[0]]
            if a["kind"] == "line" and b["kind"] == "line":
                X = _snijpunt(a, b)
                if X is not None and math.dist(X, M) <= 3.0 * max(L, tol):
                    doel = X; via_snijpunt += 1

        for j, d in enumerate(cs):
            veranderd = False
            if _sleutel(d["p0"]) in (A, B): d = _verschuif(d, 0, doel); veranderd = True
            if _sleutel(d["p1"]) in (A, B): d = _verschuif(d, 1, doel); veranderd = True
            if veranderd: cs[j] = d
    return cs, dict(nul=nul, kort=kort, via_snijpunt=via_snijpunt)
