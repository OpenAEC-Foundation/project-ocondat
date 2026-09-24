"""Maak opdrachtbestanden voor de Revit-generator.

Leest de DXF-extracten en de database, schoont de geometrie op tot boven de
Revit ShortCurveTolerance, en schrijft per product een JSON die `revit_bouw.py`
binnen Revit uitleest.

Waarom een tussenbestand: duizenden coordinaten passen niet door een
tool-aanroep, en zo is de zware rekenstap (schoonmaken) buiten Revit gedaan.

Gebruik:
    python rfa_opdrachten.py <opdrachtmap> [<leverancier>] [<productlijn>]
"""
import sys, os, json, csv

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
from curveclean import lees, schoon, lengte                      # noqa: E402

ROOT = os.path.dirname(HIER)
SJABLOON = (r"C:\ProgramData\Autodesk\RVT 2025\Family Templates"
            r"\English\Metric Detail Item.rft")


def csvlees(naam):
    with open(os.path.join(ROOT, "00_DATABASE", naam), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def maak(opdrachtmap, leverancier="Rothoblaas", lijn="HBS PLATE"):
    os.makedirs(opdrachtmap, exist_ok=True)
    prods = csvlees("products.csv")
    assets = csvlees("assets.csv")
    bron = next(a for a in assets if a["derived_from"] == "" and a["file_type"] == "DXF")
    rfamap = os.path.join(ROOT, "02_EXTRACTEN", leverancier, lijn, "rfa")
    os.makedirs(rfamap, exist_ok=True)

    index = []
    for dxf in [a for a in assets
                if a["file_type"] == "DXF" and a["derived_from"] and a["product_code"]]:
        code = dxf["product_code"]
        prod = next((p for p in prods if p["product_code"] == code), None)
        uit, st = schoon(lees(os.path.join(ROOT, dxf["file_path"].replace("/", os.sep))))
        curves = []
        for c in uit:
            if c["kind"] == "line":
                curves.append([0, round(c["p0"][0], 5), round(c["p0"][1], 5),
                                  round(c["p1"][0], 5), round(c["p1"][1], 5)])
            else:
                curves.append([1, round(c["center"][0], 5), round(c["center"][1], 5),
                                  round(c["radius"], 5), round(c["a0"], 8), round(c["a1"], 8)])
        veld = lambda n, d="": (prod or {}).get(n, d)
        job = {
            "product_code": code, "family_name": code, "template": SJABLOON,
            "out": os.path.join(rfamap, code + ".rfa"),
            "parameters": [
                ["OCD_Supplier", leverancier],
                ["OCD_ProductFamily", veld("product_family", lijn)],
                ["OCD_ProductCode", code],
                ["OCD_ProductName", veld("product_name")],
                ["OCD_ThreadDia_mm", veld("thread_diameter_mm")],
                ["OCD_Length_mm", veld("length_mm")],
                ["OCD_HeadDia_mm", veld("head_diameter_mm")],
                ["OCD_HeadThk_mm", veld("head_thickness_mm")],
                ["OCD_HoleDiaSteel_mm", veld("hole_diameter_steel_mm")],
                ["OCD_SourceFile", bron["file_name"]],
                ["OCD_SourceSHA256", bron["file_hash"][:16]],
                ["OCD_SourceDate", bron["source_date"]],
                ["OCD_CheckedDate", dxf["checked_date"]],
                ["OCD_Status", dxf["status"]],
            ],
            "curves": curves,
        }
        json.dump(job, open(os.path.join(opdrachtmap, code + ".json"), "w"),
                  separators=(",", ":"))
        index.append({"code": code, "job": os.path.join(opdrachtmap, code + ".json"),
                      "rfa": job["out"], "curves": len(curves),
                      "view": dxf["view_type"]})
        print("%-18s %4d curves  %-34s kortste %.3f mm"
              % (code, len(curves), st, min(lengte(c) for c in uit)))
    json.dump(index, open(os.path.join(opdrachtmap, "_index.json"), "w"), indent=1)
    print("\n%d opdrachten in %s" % (len(index), opdrachtmap))
    return index


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    maak(*sys.argv[1:])
