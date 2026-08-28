"""Breng de database in overeenstemming met wat er op schijf staat.

De laatste schakel van de pipeline. Loopt `01_SOURCE` en `02_EXTRACTEN` af,
hasht elk bestand en zorgt dat er voor elk een regel in `assets.csv` staat met
het juiste pad en de juiste hash. Leidt daarna de afhankelijkheden af.

UITGANGSPUNT: dit script VERZOENT, het VERZINT NIET.

  * Velden die een mens invult - `source_url`, `source_page`, `download_date`,
    `status` - worden op bestaande regels nooit overschreven. Dat is precies de
    informatie die geen script terug kan maken.
  * Kan het script iets niet afleiden, dan laat het het leeg. Liever een leeg
    veld dan een verzonnen waarde.
  * Een bestand dat verdwenen is wordt GEMELD, niet verwijderd. Weggooien is een
    beslissing, geen opruimactie.

Draaien:
    python registreer.py            # alleen rapporteren
    python registreer.py --schrijf  # ook wegschrijven
"""
import sys, os, csv, re, hashlib, datetime

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
DB = os.path.join(ROOT, "00_DATABASE")

KOLOMMEN = ["asset_id", "supplier_id", "product_id", "product_code", "file_name",
            "file_path", "file_type", "representation_type", "view_type", "units",
            "scale", "status", "derived_from", "file_hash", "source_url",
            "source_page", "download_date", "source_date", "checked_date"]
DEP_KOLOMMEN = ["asset_id", "depends_on", "relation", "note"]
MENSELIJK = ["source_url", "source_page", "download_date", "status", "product_id"]
FORMAAT = {"dxf": "DXF", "svg": "SVG", "rfa": "RFA", "dwg": "DWG", "pdf": "PDF",
           "ifc": "IFC"}


def sha(pad):
    h = hashlib.sha256()
    with open(pad, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def lees(naam, kolommen):
    pad = os.path.join(DB, naam)
    if not os.path.exists(pad):
        return []
    with open(pad, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def schrijf(naam, rijen, kolommen):
    with open(os.path.join(DB, naam), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=kolommen, delimiter=";")
        w.writeheader()
        for r in rijen:
            w.writerow(dict((k, r.get(k, "")) for k in kolommen))


def relpad(pad):
    return os.path.relpath(pad, ROOT).replace(os.sep, "/")


def scan():
    """-> lijst van (pad, leverancier, productlijn, formaat, is_bron)"""
    uit = []
    bron = os.path.join(ROOT, "01_SOURCE")
    for w, _, fs in os.walk(bron):
        for f in fs:
            ext = f.rsplit(".", 1)[-1].lower()
            if ext not in FORMAAT:
                continue
            deel = relpad(os.path.join(w, f)).split("/")
            lev = deel[1] if len(deel) > 2 else ""
            lijn = deel[2] if len(deel) > 4 else ""
            uit.append((os.path.join(w, f), lev, lijn, FORMAAT[ext], True))
    ext_root = os.path.join(ROOT, "02_EXTRACTEN")
    for w, _, fs in os.walk(ext_root):
        for f in fs:
            ext = f.rsplit(".", 1)[-1].lower()
            if ext not in FORMAAT:
                continue
            deel = relpad(os.path.join(w, f)).split("/")
            if len(deel) < 5:            # verwacht 02_EXTRACTEN/lev/lijn/formaat/bestand
                continue
            uit.append((os.path.join(w, f), deel[1], deel[2], FORMAAT[ext], False))
    return uit


def afgeleid_id(lev, stam, formaat, view):
    kort = re.sub(r"[^A-Z0-9]", "", lev.upper())[:3] or "XXX"
    code = re.sub(r"[^A-Za-z0-9]", "", stam).upper()
    return "%s-%s-%s-%s" % (kort, code, formaat, view.upper() or "NA")


def verzoen(schrijven=False):
    assets = lees("assets.csv", KOLOMMEN)
    per_pad = dict((a["file_path"], a) for a in assets)
    vandaag = datetime.date.today().isoformat()

    nieuw, gewijzigd, ongewijzigd = [], [], 0
    gezien = set()
    for pad, lev, lijn, formaat, is_bron in scan():
        rp = relpad(pad)
        gezien.add(rp)
        h = sha(pad)
        stam = os.path.splitext(os.path.basename(pad))[0]
        bestaand = per_pad.get(rp)
        if bestaand:
            if bestaand.get("file_hash") != h:
                gewijzigd.append((bestaand["asset_id"], bestaand.get("file_hash", "")[:12], h[:12]))
                bestaand["file_hash"] = h
                bestaand["checked_date"] = vandaag
            else:
                ongewijzigd += 1
            continue
        # nieuw: alleen afleiden wat uit het pad volgt, de rest leeg laten
        view = "top" if "HEAD" in stam.upper() else ("" if is_bron else "side")
        rij = dict((k, "") for k in KOLOMMEN)
        rij.update(asset_id=afgeleid_id(lev, stam, formaat, view or "SRC"),
                   supplier_id=re.sub(r"[^A-Z0-9]", "", lev.upper())[:3],
                   product_code="" if is_bron else stam,
                   file_name=os.path.basename(pad), file_path=rp, file_type=formaat,
                   representation_type="HIGH DETAIL" if is_bron else "DETAIL",
                   view_type=view, units="mm", scale="1:1",
                   status="REVIEW REQUIRED", file_hash=h, checked_date=vandaag)
        assets.append(rij); per_pad[rp] = rij
        nieuw.append(rij["asset_id"])

    vermist = [a["asset_id"] for a in assets
               if a["file_path"] and a["file_path"] not in gezien]

    # ---- afhankelijkheden afleiden uit de conventie
    bron = next((a for a in assets if a["file_type"] in ("DXF", "DWG")
                 and a["file_path"].startswith("01_SOURCE")), None)
    deps = []
    if bron:
        rfa_ids = []
        for a in assets:
            if not a["file_path"].startswith("02_EXTRACTEN"):
                continue
            if a["file_type"] in ("DXF", "SVG"):
                a["derived_from"] = bron["asset_id"]
                deps.append(dict(asset_id=a["asset_id"], depends_on=bron["asset_id"],
                                 relation="derived_from", note="afgeleid uit de fabrikantsbron"))
            elif a["file_type"] == "RFA":
                zus = next((b for b in assets if b["file_type"] == "DXF"
                            and b["product_code"] == a["product_code"]
                            and b["file_path"].startswith("02_EXTRACTEN")), None)
                if zus:
                    a["derived_from"] = zus["asset_id"]
                    deps.append(dict(asset_id=a["asset_id"], depends_on=zus["asset_id"],
                                     relation="derived_from",
                                     note="Revit family uit het DXF-extract"))
                    rfa_ids.append(a["asset_id"])
                else:
                    # geen gelijknamig DXF: dit is de verzamelfamilie
                    a["derived_from"] = bron["asset_id"]
        verzamel = next((a for a in assets if a["file_type"] == "RFA"
                         and a["asset_id"] not in rfa_ids
                         and a["file_path"].startswith("02_EXTRACTEN")), None)
        if verzamel:
            for rid in rfa_ids:
                deps.append(dict(asset_id=verzamel["asset_id"], depends_on=rid,
                                 relation="nested_family",
                                 note="genest, per type zichtbaar geschakeld"))

    print("bestanden gevonden : %d" % len(gezien))
    print("  ongewijzigd      : %d" % ongewijzigd)
    print("  nieuw            : %d %s" % (len(nieuw), nieuw if nieuw else ""))
    print("  hash gewijzigd   : %d" % len(gewijzigd))
    for aid, o, n in gewijzigd:
        print("      %-32s %s -> %s" % (aid, o, n))
    print("  bestand vermist  : %d %s" % (len(vermist), vermist if vermist else ""))
    print("afhankelijkheden   : %d afgeleid" % len(deps))

    if not schrijven:
        print("\n(alleen gerapporteerd - draai met --schrijf om weg te schrijven)")
        return
    schrijf("assets.csv", assets, KOLOMMEN)
    schrijf("dependencies.csv", deps, DEP_KOLOMMEN)
    log = lees("update-log.csv", ["date", "actor", "action", "scope", "detail"])
    log.append(dict(date=vandaag, actor="registreer.py", action="RECONCILED",
                    scope="bibliotheek",
                    detail="%d bestanden; %d nieuw, %d hash gewijzigd, %d vermist"
                           % (len(gezien), len(nieuw), len(gewijzigd), len(vermist))))
    schrijf("update-log.csv", log, ["date", "actor", "action", "scope", "detail"])
    print("\nweggeschreven naar 00_DATABASE")


if __name__ == "__main__":
    verzoen("--schrijf" in sys.argv)
