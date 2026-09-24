"""Bouw Revit detailcomponenten uit de opdrachtbestanden.

DRAAIT BINNEN REVIT, niet als los script. IronPython 2.7 via pyRevit, of via
de revit-mcp-python MCP-server met `execute_revit_code(use_transaction=False)`.
De transacties worden hier zelf beheerd, want er is geen actief document.

Twee stappen:
    bouw_families(opdrachtmap)    -> een .rfa per product
    bouw_verzamelfamilie(...)     -> een familie met een type per product,
                                     waarin die .rfa's genest zijn

Valkuilen die hier al opgelost zijn - zie ook 02_EXTRACTEN/Extract RFA.md:
  * FamilyManager.NewType() MOET voor het zetten van typeparameters, anders
    faalt elke Set met "There is no current type."
  * Document.LoadFamily() geeft in IronPython een bool terug, niet de Family.
    Zoek de familie daarna op via een FilteredElementCollector.
  * Een .rfa die in Revit openstaat blokkeert SaveAs. Het ACTIEVE document kan
    niet via de API dicht - sla dat product over of sluit het met de hand.
  * Een batch van 18+ families overschrijdt de time-out van een MCP-aanroep.
    Bouw in blokken en controleer de voortgang op de schijf.
"""
import json, os, time
from Autodesk.Revit import DB

MM = 304.8                      # Revit rekent intern in voet


def _view(fam):
    return [v for v in DB.FilteredElementCollector(fam).OfClass(DB.View)
            if not v.IsTemplate and v.ViewType == DB.ViewType.FloorPlan][0]


def _curve(c):
    if c[0] == 0:
        return DB.Line.CreateBound(DB.XYZ(c[1] / MM, c[2] / MM, 0.0),
                                   DB.XYZ(c[3] / MM, c[4] / MM, 0.0))
    return DB.Arc.Create(DB.XYZ(c[1] / MM, c[2] / MM, 0.0), c[3] / MM, c[4], c[5],
                         DB.XYZ.BasisX, DB.XYZ.BasisY)


def bouw_families(opdrachtmap, app, alleen=None):
    """Een .rfa per opdracht. `alleen` is een lijst productcodes, of None."""
    index = json.load(open(os.path.join(opdrachtmap, "_index.json")))
    bezet = set(d.Title.upper() for d in app.Documents)
    res, over = [], []
    for it in index:
        if alleen and it["code"] not in alleen:
            continue
        if it["code"].upper() in bezet:          # staat open: SaveAs zou falen
            over.append(it["code"]); continue
        job = json.load(open(it["job"]))
        fam = app.NewFamilyDocument(job["template"])
        view = _view(fam)
        t = DB.Transaction(fam, "opbouw"); t.Start()
        n = 0
        for c in job["curves"]:
            fam.FamilyCreate.NewDetailCurve(view, _curve(c)); n += 1
        fm = fam.FamilyManager
        fm.NewType(job["family_name"])           # eerst het type, dan de parameters
        p = 0
        for naam, waarde in job["parameters"]:
            try:
                par = fm.AddParameter(naam, DB.GroupTypeId.IdentityData,
                                      DB.SpecTypeId.String.Text, False)
                fm.Set(par, str(waarde)); p += 1
            except Exception:
                pass
        t.Commit()
        opts = DB.SaveAsOptions(); opts.OverwriteExistingFile = True
        fam.SaveAs(job["out"], opts); fam.Close(False)
        res.append((job["product_code"], n, p))
    return res, over


def bouw_verzamelfamilie(opdrachtmap, app, sjabloon, uitpad, typenaam=None):
    """Een familie met per opdracht een genest exemplaar en een eigen type.

    Nesten in plaats van alle losse detaillijnen zichtbaar schakelen: dat
    scheelt een koppeling per curve en houdt de geometrie per product
    herleidbaar.
    """
    index = json.load(open(os.path.join(opdrachtmap, "_index.json")))
    host = app.NewFamilyDocument(sjabloon)
    view = _view(host)
    fm = host.FamilyManager
    t = DB.Transaction(host, "nesten"); t.Start()
    gedaan = []
    for it in index:
        code = it["code"]
        host.LoadFamily(it["rfa"])               # retour is een bool, niet de Family
        fam = None
        for f in DB.FilteredElementCollector(host).OfClass(DB.Family):
            if f.Name == code:
                fam = f; break
        if fam is None:
            continue
        sym = host.GetElement(list(fam.GetFamilySymbolIds())[0])
        if not sym.IsActive:
            sym.Activate()
        inst = host.FamilyCreate.NewFamilyInstance(DB.XYZ(0, 0, 0), sym, view)
        fp = fm.AddParameter("V_" + code, DB.GroupTypeId.Visibility,
                             DB.SpecTypeId.Boolean.YesNo, False)
        fm.AssociateElementParameterToFamilyParameter(
            inst.get_Parameter(DB.BuiltInParameter.IS_VISIBLE_PARAM), fp)
        gedaan.append(code)

    zicht = dict((p.Definition.Name[2:], p) for p in fm.Parameters
                 if p.Definition.Name.startswith("V_"))
    tekst = {}
    for naam, _ in json.load(open(index[0]["job"]))["parameters"]:
        tekst[naam] = fm.AddParameter(naam, DB.GroupTypeId.IdentityData,
                                      DB.SpecTypeId.String.Text, False)
    for it in index:
        job = json.load(open(it["job"]))
        fm.NewType(typenaam(it) if typenaam else it["code"])
        for c, p in zicht.items():
            fm.Set(p, 1 if c == it["code"] else 0)
        for pn, w in job["parameters"]:
            if pn in tekst:
                fm.Set(tekst[pn], str(w))
    t.Commit()
    opts = DB.SaveAsOptions(); opts.OverwriteExistingFile = True
    host.SaveAs(uitpad, opts); host.Close(False)
    return gedaan


def controleer(pad, app):
    """Lees terug en controleer: per type precies een zichtbaar product.

    Meet extents NIET met Curve.Tessellate() - Revit hakt een halve cirkel in
    drie koorden, waardoor de hoogte sin(60) = 0,866 van de werkelijke wordt.
    Bemonster het parameterbereik met Evaluate().
    """
    d = app.OpenDocumentFile(pad)
    fm = d.FamilyManager
    zicht = [p for p in fm.Parameters if p.Definition.Name.startswith("V_")]
    pc = [p for p in fm.Parameters if p.Definition.Name == "OCD_ProductCode"][0]
    fout = []
    for ty in fm.Types:
        if not ty.Name:
            continue
        aan = [p.Definition.Name[2:] for p in zicht if ty.AsInteger(p) == 1]
        if len(aan) != 1 or aan[0] != ty.AsString(pc):
            fout.append((ty.Name, aan, ty.AsString(pc)))
    xs, ys = [], []
    for ce in DB.FilteredElementCollector(d).OfClass(DB.CurveElement):
        g = ce.GeometryCurve
        p0, p1 = g.GetEndParameter(0), g.GetEndParameter(1)
        for i in range(33):
            p = g.Evaluate(p0 + (p1 - p0) * i / 32.0, False)
            xs.append(p.X * MM); ys.append(p.Y * MM)
    d.Close(False)
    return {"types": len([t for t in fm.Types if t.Name]), "fout": fout,
            "breedte": (max(xs) - min(xs)) if xs else 0,
            "hoogte": (max(ys) - min(ys)) if ys else 0}
