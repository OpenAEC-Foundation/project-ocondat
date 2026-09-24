"""SVG-extracten omzetten naar een Open PDF Studio symboolbibliotheek.

Open PDF Studio kent twee bibliotheekformaten. Dit script schrijft het
formaat dat de knop **Import Group** leest:

    {"name": "<groepsnaam>", "symbols": [{"name": ..., "svg": ...}]}

De SVG staat daarin INLINE als string; het formaat kent geen verwijzingen
naar losse bestanden. Het bestandsgebaseerde formaat (collection.json +
symbols/*.svg) bestaat wel, maar de app leest dat uitsluitend uit
OpenAEC-Foundation/open-pdf-studio-library - een lokale map kan pas na een
codewijziging in de app.

Drie dingen die de app oplegt en die hier gecontroleerd worden:

1. De app leidt het symbool-id af uit de NAAM, niet uit de bestandsnaam.
   Twee symbolen met dezelfde naam krijgen dus hetzelfde id, waarna
   verwijderen er twee tegelijk raakt. Namen moeten uniek zijn.

2. Het groeps-id wordt eveneens uit de naam afgeleid ('custom-' + slug).
   Twee productlijnen die naar dezelfde slug herleiden overschrijven
   elkaar bij import.

3. Alleen `name` en `svg` overleven de import. Productcode, aanzicht en
   herkomst uit het manifest gaan verloren, dus die horen in de naam
   verwerkt te zijn wil je ze in het palet terugzien.

De maatvoering komt uit de SVG zelf: de extracten dragen `width="105.5mm"`
op de root en worden daarmee door Open PDF Studio op ware maat geplaatst,
omgerekend met de schaal van de tekening.
"""
import json, re, sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
EXTRACTEN = WORTEL / "02_EXTRACTEN"

TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
ROOT_MM = re.compile(r"<svg\b[^>]*\b(?:width|height)\s*=\s*\"[\d.]+\s*(?:mm|cm|in|pt|pc)\"", re.I)


def _slug(naam):
    """Zelfde afleiding als de app: kleine letters, niet-alfanumeriek -> '-'."""
    return re.sub(r"-+$", "", re.sub(r"[^a-z0-9]+", "-", naam.lower()))


def naam_van(pad, svg):
    """<title> is leidend - die bevat ook het aanzicht. Anders de bestandsnaam."""
    m = TITLE.search(svg)
    return m.group(1).strip() if m else pad.stem


def bouw(productlijn_map):
    """Bouw de groep uit <productlijn>/svg/*.svg."""
    svg_map = productlijn_map / "svg"
    if not svg_map.is_dir():
        raise SystemExit(f"geen svg/ in {productlijn_map}")

    leverancier = productlijn_map.parent.name
    productlijn = productlijn_map.name
    groepsnaam = f"{leverancier} {productlijn}"

    symbolen, zonder_maat = [], []
    for pad in sorted(svg_map.glob("*.svg")):
        svg = pad.read_text(encoding="utf-8")
        if not ROOT_MM.search(svg):
            zonder_maat.append(pad.name)
        symbolen.append({"name": naam_van(pad, svg), "svg": svg})

    if not symbolen:
        raise SystemExit(f"geen SVG's gevonden in {svg_map}")

    # Controle 1: namen moeten uniek zijn, want daar leidt de app het id uit af.
    gezien = {}
    for s in symbolen:
        gezien.setdefault(_slug(s["name"]), []).append(s["name"])
    botsend = {k: v for k, v in gezien.items() if len(v) > 1}
    if botsend:
        for slug, namen in botsend.items():
            print(f"  BOTSING op id '{slug}': {', '.join(namen)}", file=sys.stderr)
        raise SystemExit("namen leiden naar hetzelfde symbool-id; los dat op in de SVG-titels")

    uit_map = productlijn_map / "openpdfstudio"
    uit_map.mkdir(exist_ok=True)
    doel = uit_map / f"{leverancier} - {productlijn}.json"
    doel.write_text(
        json.dumps({"name": groepsnaam, "symbols": symbolen}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    omvang = doel.stat().st_size
    print(f"{doel.relative_to(WORTEL)}")
    print(f"  groep        : {groepsnaam}  (id wordt 'custom-{_slug(groepsnaam)}')")
    print(f"  symbolen     : {len(symbolen)}")
    print(f"  omvang       : {omvang/1024:.0f} KB  ({omvang/len(symbolen)/1024:.1f} KB per symbool)")
    if zonder_maat:
        # Zonder echte eenheid op de root plaatst de app op een vaste
        # standaardgrootte in plaats van op ware maat.
        print(f"  LET OP       : {len(zonder_maat)} SVG's zonder mm/cm/in op de root: "
              f"{', '.join(zonder_maat[:3])}{' ...' if len(zonder_maat) > 3 else ''}")
    return doel


if __name__ == "__main__":
    if len(sys.argv) > 1:
        doelen = [Path(a) for a in sys.argv[1:]]
    else:
        doelen = sorted(p.parent for p in EXTRACTEN.glob("*/*/svg") if p.is_dir())
    if not doelen:
        raise SystemExit("geen productlijnen met een svg/-map gevonden")
    for d in doelen:
        bouw(d)
