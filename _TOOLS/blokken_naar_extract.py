import sys, os, math, ezdxf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRON = os.path.join(ROOT, "01_SOURCE","Rothoblaas","HBS PLATE","CAD",
                    "HBS-PLATE_wd04-rothoblaas.dxf")
EXT  = os.path.join(ROOT, "02_EXTRACTEN","Rothoblaas","HBS PLATE")
BLOKKEN = [("HBSPL_HEAD_8", 8), ("HBSPL_HEAD_10", 10), ("HBSPl_HEAD_12", 12)]

src = ezdxf.readfile(BRON)
M = 0.25
for blok, dia in BLOKKEN:
    b = src.blocks.get(blok)
    naam = "HBSPL_HEAD_%d" % dia          # typefout in de bron gecorrigeerd
    ents = [e for e in b]
    # ---- DXF
    doc = ezdxf.new(setup=False); doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    for laag in sorted({str(e.dxf.layer) for e in ents} - {"0"}):
        if laag not in doc.layers: doc.layers.add(laag)
    for e in ents:
        a = {"layer": str(e.dxf.layer)}; t = e.dxftype()
        if t == "CIRCLE":   msp.add_circle(e.dxf.center, e.dxf.radius, dxfattribs=a)
        elif t == "ARC":    msp.add_arc(e.dxf.center, e.dxf.radius,
                                        e.dxf.start_angle, e.dxf.end_angle, dxfattribs=a)
        elif t == "LWPOLYLINE":
            msp.add_lwpolyline([(v[0],v[1],0.0,0.0,v[4]) for v in e.get_points()],
                               format="xyseb", dxfattribs={**a,"closed":bool(e.closed)})
        elif t == "TEXT":
            msp.add_text(e.dxf.text, height=e.dxf.height,
                         dxfattribs=a).set_placement((e.dxf.insert.x, e.dxf.insert.y))
    doc.saveas(os.path.join(EXT, "dxf", naam + ".dxf"))

    # ---- SVG
    xs=[]; ys=[]
    for e in ents:
        t = e.dxftype()
        if t in ("CIRCLE","ARC"):
            c=e.dxf.center; r=e.dxf.radius
            xs += [c.x-r,c.x+r]; ys += [c.y-r,c.y+r]
        elif t == "LWPOLYLINE":
            for v in e.get_points(): xs.append(v[0]); ys.append(v[1])
    x0,x1,y0,y1 = min(xs),max(xs),min(ys),max(ys)
    vw, vh = (x1-x0)+2*M, (y1-y0)+2*M
    X = lambda x: round(x - x0 + M, 4)
    Y = lambda y: round(y1 + M - y, 4)
    paden = []; teksten = []
    for e in ents:
        t = e.dxftype(); laag = str(e.dxf.layer)
        if t == "CIRCLE":
            c=e.dxf.center; r=e.dxf.radius
            paden.append((laag, "M%s,%s A%g,%g 0 1,0 %s,%s A%g,%g 0 1,0 %s,%sZ" %
                (X(c.x-r),Y(c.y),r,r,X(c.x+r),Y(c.y),r,r,X(c.x-r),Y(c.y))))
        elif t == "ARC":
            c=e.dxf.center; r=e.dxf.radius
            a0=math.radians(e.dxf.start_angle); a1=math.radians(e.dxf.end_angle)
            sw=(a1-a0)%(2*math.pi)
            paden.append((laag, "M%s,%s A%g,%g 0 %d,0 %s,%s" %
                (X(c.x+r*math.cos(a0)), Y(c.y+r*math.sin(a0)), r, r,
                 1 if sw>math.pi else 0,
                 X(c.x+r*math.cos(a1)), Y(c.y+r*math.sin(a1)))))
        elif t == "LWPOLYLINE":
            pts = e.get_points(); d = ["M%s,%s" % (X(pts[0][0]), Y(pts[0][1]))]
            n = len(pts); rng = range(n) if e.closed else range(n-1)
            for i in rng:
                x_0,y_0,bl = pts[i][0], pts[i][1], pts[i][4]
                x_1,y_1 = pts[(i+1)%n][0], pts[(i+1)%n][1]
                if abs(bl) < 1e-12: d.append("L%s,%s" % (X(x_1), Y(y_1)))
                else:
                    th = 4*math.atan(bl); ch = math.hypot(x_1-x_0, y_1-y_0)
                    r = abs(ch/(2*math.sin(th/2)))
                    d.append("A%g,%g 0 %d,%d %s,%s" % (r,r,1 if abs(th)>math.pi else 0,
                             0 if bl>0 else 1, X(x_1), Y(y_1)))
            if e.closed: d.append("Z")
            paden.append((laag, "".join(d)))
        elif t == "TEXT":
            teksten.append((laag, X(e.dxf.insert.x), Y(e.dxf.insert.y),
                            e.dxf.height, e.dxf.text))
    lagen = sorted({l for l,_ in paden} | {l for l,_,_,_,_ in teksten})
    body = []
    for laag in lagen:
        body.append('  <g id="%s">' % laag)
        body += ['    <path d="%s"/>' % d for l,d in paden if l == laag]
        for l,tx,ty,h,txt in teksten:
            if l != laag: continue
            body.append('    <text x="%s" y="%s" font-size="%g" text-anchor="middle" '
                        'fill="#1a1a1a" stroke="none" '
                        'font-family="Arial, Helvetica, sans-serif">%s</text>'
                        % (tx, ty+h*0.35, h, txt))
        body.append('  </g>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg"\n'
           '     width="%.4gmm" height="%.4gmm" viewBox="0 0 %.4g %.4g">\n'
           '  <title>%s - kopaanzicht</title>\n'
           '  <desc>Rothoblaas HBS PLATE, kopaanzicht D%d, schaal 1:1, eenheden mm. '
           'De letters zijn de stempeling op de schroefkop.</desc>\n'
           '  <g fill="none" stroke="#1a1a1a" stroke-width="0.12"\n'
           '     stroke-linecap="round" stroke-linejoin="round">\n%s\n  </g>\n</svg>\n'
           % (vw, vh, vw, vh, naam, dia, "\n".join(body)))
    open(os.path.join(EXT, "svg", naam + ".svg"), "w", encoding="utf-8").write(svg)
    print("%-16s bbox %.2f x %.2f mm   %d paden, %d teksten"
          % (naam, x1-x0, y1-y0, len(paden), len(teksten)))
