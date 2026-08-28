import json, math, os, re, sys, collections
sys.path.insert(0, sys.argv[1]); from bbox import bbox
S, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
p = json.load(open(S+"/selectie18.json")); ents = p["entities"]
assert p.get("insertion_units") == 4, "verwacht mm"

geo=[(e,b) for e,b in ((e,bbox(e)) for e in ents if e.get("type") not in ("text","mtext")) if b]
labels=[e for e in ents if e.get("type") in ("text","mtext")]
T=4.0; parent=list(range(len(geo)))
def find(a):
    while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
    return a
grid=collections.defaultdict(list)
for i,(e,b) in enumerate(geo):
    for gx in range(int((b[0]-T)//T), int((b[2]+T)//T)+1):
        for gy in range(int((b[1]-T)//T), int((b[3]+T)//T)+1):
            grid[(gx,gy)].append(i)
for cell in grid.values():
    r0=find(cell[0])
    for j in cell[1:]:
        rj=find(j)
        if rj!=r0: parent[rj]=r0
groups=collections.defaultdict(list)
for i in range(len(geo)): groups[find(i)].append(i)
assert len(groups)==18

cl=[]
for gid,idxs in groups.items():
    bs=[geo[i][1] for i in idxs]
    cl.append({"gid":gid,"idxs":idxs,
               "x0":min(b[0] for b in bs),"y0":min(b[1] for b in bs),
               "x1":max(b[2] for b in bs),"y1":max(b[3] for b in bs)})
for c in cl: c["w"]=round(c["x1"]-c["x0"],2); c["h"]=round(c["y1"]-c["y0"],2)
lab=[]
for e in labels:
    m=re.search(r'(\d+)\s*x\s*(\d+)\s*$', str(e.get("value","")))
    lab.append({"naam":str(e["value"]).strip(),"d":int(m.group(1)),"L":int(m.group(2))})
naam_van={}
for h,d in zip(sorted({c['h'] for c in cl}), sorted({l['d'] for l in lab})):
    cs=sorted([c for c in cl if c["h"]==h], key=lambda c:c["w"])
    ls=sorted([l for l in lab if l["d"]==d], key=lambda l:l["L"])
    assert len(set(round(c["w"]-l["L"],2) for c,l in zip(cs,ls)))==1
    for c,l in zip(cs,ls): naam_van[c["gid"]]=(l["naam"], l["d"], l["L"])
assert len({v[0] for v in naam_van.values()})==18

def arc_cmd(x1,y1,r,sweep,ccw,X,Y):
    return (f"A{r:.5g},{r:.5g} 0 {1 if abs(sweep)>math.pi else 0},"
            f"{0 if ccw else 1} {X(x1):.4f},{Y(y1):.4f}")
def paths_for(e,X,Y):
    t=e.get("type"); out=[]
    if t=="line":
        (x0,y0),(x1,y1)=e["start"][:2],e["end"][:2]
        out.append(f"M{X(x0):.4f},{Y(y0):.4f}L{X(x1):.4f},{Y(y1):.4f}")
    elif t=="circle":
        cx,cy=e["center"][:2]; r=e["radius"]
        out.append(f"M{X(cx-r):.4f},{Y(cy):.4f}A{r:.5g},{r:.5g} 0 1,0 {X(cx+r):.4f},{Y(cy):.4f}"
                   f"A{r:.5g},{r:.5g} 0 1,0 {X(cx-r):.4f},{Y(cy):.4f}Z")
    elif t=="arc":
        cx,cy=e["center"][:2]; r=e["radius"]; a0,a1=e["start_angle"],e["end_angle"]
        out.append(f"M{X(cx+r*math.cos(a0)):.4f},{Y(cy+r*math.sin(a0)):.4f}"
                   + arc_cmd(cx+r*math.cos(a1), cy+r*math.sin(a1), r,(a1-a0)%(2*math.pi),True,X,Y))
    elif t=="lwpolyline":
        vs=e["vertices"]; closed=bool(e.get("closed")); n=len(vs)
        d=[f"M{X(vs[0][0]):.4f},{Y(vs[0][1]):.4f}"]
        for i in (range(n) if closed else range(n-1)):
            x0,y0,b=vs[i][0],vs[i][1],(vs[i][2] if len(vs[i])>2 else 0.0)
            x1,y1=vs[(i+1)%n][0],vs[(i+1)%n][1]
            if abs(b)<1e-12: d.append(f"L{X(x1):.4f},{Y(y1):.4f}")
            else:
                th=4*math.atan(b); ch=math.hypot(x1-x0,y1-y0)
                d.append(arc_cmd(x1,y1,abs(ch/(2*math.sin(th/2))),th,b>0,X,Y))
        if closed: d.append("Z")
        out.append("".join(d))
    return out

M=0.25; rijen=[]
for c in cl:
    naam,d_,L_ = naam_van[c["gid"]]
    vw,vh = (c["x1"]-c["x0"])+2*M, (c["y1"]-c["y0"])+2*M
    X=lambda x,c=c: x-c["x0"]+M
    Y=lambda y,c=c: c["y1"]+M-y
    per=collections.defaultdict(list)
    for i in c["idxs"]:
        e=geo[i][0]; per[str(e.get("layer","0"))].extend(paths_for(e,X,Y))
    body=[]
    for laag in sorted(per):
        body.append(f'  <g id="{laag}">')
        body += [f'    <path d="{p}"/>' for p in per[laag]]
        body.append('  </g>')
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg"\n'
         f'     width="{vw:.4g}mm" height="{vh:.4g}mm" viewBox="0 0 {vw:.4g} {vh:.4g}">\n'
         f'  <title>{naam} - zijaanzicht</title>\n'
         f'  <desc>Rothoblaas HBS PLATE, schaal 1:1, eenheden mm. '
         f'Draad D{d_}, lengte onder kop {L_} mm.</desc>\n'
         f'  <g fill="none" stroke="#1a1a1a" stroke-width="0.12"\n'
         f'     stroke-linecap="round" stroke-linejoin="round">\n'+"\n".join(body)+"\n  </g>\n</svg>\n")
    open(os.path.join(OUT, re.sub(r'[<>:"/\|?*]',"-",naam)+".svg"),"w",encoding="utf-8").write(svg)
    rijen.append((d_,L_,naam,len(c["idxs"]),vw,vh))
rijen.sort()
print(f"{len(rijen)} SVG's -> {OUT}\n")
print(f"{'bestand':26s} {'ent':>5s} {'breedte':>10s} {'hoogte':>9s}")
for d_,L_,naam,n,vw,vh in rijen:
    print(f"{naam+'.svg':26s} {n:5d} {vw:9.2f}mm {vh:8.2f}mm")
