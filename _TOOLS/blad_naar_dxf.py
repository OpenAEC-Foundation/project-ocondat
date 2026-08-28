import json, math, os, re, sys, collections, datetime
sys.path.insert(0, sys.argv[1]); from bbox import bbox
import ezdxf
S, BASE = sys.argv[1], sys.argv[2]
p = json.load(open(S+"/selectie18.json")); ents = p["entities"]
assert p.get("insertion_units") == 4

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
    cl.append({"gid":gid,"idxs":idxs,"x0":min(b[0] for b in bs),"y0":min(b[1] for b in bs),
               "x1":max(b[2] for b in bs),"y1":max(b[3] for b in bs)})
for c in cl: c["w"]=round(c["x1"]-c["x0"],2); c["h"]=round(c["y1"]-c["y0"],2)
lab=[]
for e in labels:
    m=re.search(r'(\d+)\s*x\s*(\d+)\s*$', str(e.get("value","")))
    lab.append({"naam":str(e["value"]).strip(),"d":int(m.group(1)),"L":int(m.group(2))})
info={}
for h,d in zip(sorted({c['h'] for c in cl}), sorted({l['d'] for l in lab})):
    cs=sorted([c for c in cl if c["h"]==h], key=lambda c:c["w"])
    ls=sorted([l for l in lab if l["d"]==d], key=lambda l:l["L"])
    resten={round(c["w"]-l["L"],2) for c,l in zip(cs,ls)}
    assert len(resten)==1, f"kopdikte niet constant voor D{d}: {resten}"
    t=resten.pop()
    for c,l in zip(cs,ls): info[c["gid"]]=dict(naam=l["naam"], d=d, L=l["L"], kopdikte=t, kopdiam=h)

def schrijf_dxf(pad, entiteiten, dx=0.0, dy=0.0):
    doc = ezdxf.new(setup=False)
    doc.header["$INSUNITS"] = 4          # millimeters - Revit leest dit
    msp = doc.modelspace()
    for laag in sorted({str(e.get("layer","0")) for e in entiteiten} - {"0"}):
        if laag not in doc.layers: doc.layers.add(laag)
    for e in entiteiten:
        t=e.get("type"); a={"layer":str(e.get("layer","0"))}
        if t=="line":
            msp.add_line((e["start"][0]+dx, e["start"][1]+dy),
                         (e["end"][0]+dx, e["end"][1]+dy), dxfattribs=a)
        elif t=="circle":
            msp.add_circle((e["center"][0]+dx, e["center"][1]+dy), e["radius"], dxfattribs=a)
        elif t=="arc":
            msp.add_arc((e["center"][0]+dx, e["center"][1]+dy), e["radius"],
                        math.degrees(e["start_angle"]), math.degrees(e["end_angle"]), dxfattribs=a)
        elif t=="lwpolyline":
            msp.add_lwpolyline([(v[0]+dx, v[1]+dy, 0.0, 0.0, (v[2] if len(v)>2 else 0.0))
                                for v in e["vertices"]], format="xyseb",
                               dxfattribs={**a, "closed": bool(e.get("closed"))})
        elif t in ("text","mtext"):
            msp.add_text(str(e.get("value","")), height=e.get("height",2.5),
                         dxfattribs=a).set_placement((e["position"][0]+dx, e["position"][1]+dy))
    doc.saveas(pad)

os.makedirs(BASE+"/revit", exist_ok=True); os.makedirs(BASE+"/bron", exist_ok=True)
producten=[]
for c in sorted(cl, key=lambda c: (info[c["gid"]]["d"], info[c["gid"]]["L"])):
    i=info[c["gid"]]; naam=i["naam"]; veilig=re.sub(r'[<>:"/\|?*]',"-",naam)
    # invoegpunt: onderkant kop, op de hartlijn. Schroef loopt daarna in +X.
    ox = c["x0"] + i["kopdikte"]
    oy = (c["y0"] + c["y1"]) / 2.0
    schrijf_dxf(f"{BASE}/revit/{veilig}.dxf", [geo[k][0] for k in c["idxs"]], -ox, -oy)
    producten.append({
        "code": naam.split(" - ")[0], "aanduiding": f"{i['d']}x{i['L']}", "label": naam,
        "draad_diameter_mm": i["d"], "lengte_onder_kop_mm": i["L"],
        "kop_diameter_mm": round(i["kopdiam"],2), "kop_dikte_mm": round(i["kopdikte"],2),
        "totale_lengte_mm": round(c["w"],2), "entiteiten": len(c["idxs"]),
        "svg": f"svg/{veilig}.svg", "revit_dxf": f"revit/{veilig}.dxf"})

schrijf_dxf(f"{BASE}/bron/HBS PLATE - alle 18 (reconstructie uit levend document).dxf", ents)

doc = {
 "fabrikant": "Rothoblaas", "productlijn": "HBS PLATE", "aantal_producten": len(producten),
 "eenheid": "mm", "aanzicht": "zijaanzicht",
 "gegenereerd_op": datetime.date.today().isoformat(),
 "herkomst": {
   "methode": "Open CAD Studio MCP Bridge, live selectie uit het geopende document",
   "insertion_units_bron": 4,
   "originele_fabrikantsbestand": "ONTBREEKT - zie bron/LEESMIJ.txt",
   "afgeleide_maten": ("kop_diameter uit de hoogte van het aanzicht; lengte_onder_kop uit de "
       "labeltekst; kop_dikte als totale_lengte minus lengte_onder_kop, per diameter "
       "constant gecontroleerd (4,5 / 5,0 / 5,5 mm)")},
 "invoegpunt": {"x": "onderkant kop", "y": "hartlijn schroef",
   "richting": "schroef loopt in +X, punt op x = lengte_onder_kop",
   "geldt_voor": "de DXF-bestanden in revit/"},
 "niet_inbegrepen": ("Mechanische waarden (karakteristieke draagkracht, ETA-gegevens, "
   "voorboormaten, materiaal, coating). Die staan niet in de tekening en zijn bewust "
   "niet afgeleid of geraden - haal ze uit de ETA of de fabrikantsdocumentatie."),
 "producten": producten}
json.dump(doc, open(BASE+"/producten.json","w",encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"{len(producten)} producten, revit-dxf's en producten.json geschreven")
