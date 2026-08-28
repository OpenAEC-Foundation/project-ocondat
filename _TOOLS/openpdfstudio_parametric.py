"""SVG-extracten omzetten naar een Open PDF Studio linework-catalogus.

Schrijft `parametric.json` in het formaat `linework-variants`: één familie per
aanzicht, met de producten als varianten. In Open PDF Studio wordt dat één
palet-ingang met een maat-keuze in het eigenschappenpaneel, in plaats van een
los symbool per product.

Verschil met `openpdfstudio_library.py`, dat platte stempels maakt:

| | library.py | dit script |
|---|---|---|
| Palet-ingangen | één per product | één per aanzicht |
| Maat wisselen | nee | ja, dropdown |
| Bogen | blijven SVG-bogen | blijven echte bogen |

**Bogen blijven bogen.** De SVG-boog (`A`, eindpuntnotatie) wordt omgerekend
naar middelpunt + straal + hoeken, niet gepolygoniseerd. Dat is de reden dat
dit script bestaat en niet gewoon punten uitdeelt: een benadering is bij het
terugmeten niet meer te herstellen, en `Extract SVG.md` verbiedt hem.

**Stempeling telt mee.** `<text>` binnen de omtrek is onderdeel van het product
(bij HBS PLATE de `H B S P` in de kopcirkel) en gaat als tekst mee.

Aannames, met een harde controle erop:
  * paden zijn absoluut (M/L/A/Z), zoals `Extract SVG.md` voorschrijft;
  * bogen zijn cirkelbogen (rx == ry) zonder rotatie.
Wijkt de bron daarvan af, dan stopt het script in plaats van stilletjes iets
verkeerds te schrijven.
"""
import json, math, re, sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
EXTRACTEN = WORTEL / "02_EXTRACTEN"

TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
DESC = re.compile(r"<desc>(.*?)</desc>", re.S | re.I)
VIEWBOX = re.compile(r'viewBox="\s*([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s*"')
PATH_D = re.compile(r'\bd="([^"]*)"')
TEXT_EL = re.compile(
    r'<text\b([^>]*)>(.*?)</text>', re.S | re.I)
ATTR = re.compile(r'(\b[\w-]+)\s*=\s*"([^"]*)"')
TOKEN = re.compile(r"([MLAZmlaz])|([-+]?[\d.]+(?:[eE][-+]?\d+)?)")


def _tokens(d):
    for m in TOKEN.finditer(d):
        yield m.group(1) if m.group(1) else float(m.group(2))


def _arc_center(x1, y1, x2, y2, r, laf, sf):
    """SVG-boog (eindpunten) -> (cx, cy, r, a0, a1, ccw). Alleen cirkelbogen."""
    dx, dy = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    # Te kleine straal oprekken tot hij de koorde haalt (SVG-spec F.6.6).
    lam = (dx * dx + dy * dy) / (r * r)
    if lam > 1:
        r *= math.sqrt(lam)
    num = r * r * r * r - r * r * dy * dy - r * r * dx * dx
    den = r * r * dy * dy + r * r * dx * dx
    factor = math.sqrt(max(0.0, num / den)) if den else 0.0
    if laf == sf:
        factor = -factor
    cxp, cyp = factor * dy, -factor * dx
    cx, cy = cxp + (x1 + x2) / 2.0, cyp + (y1 + y2) / 2.0
    a0 = math.atan2(y1 - cy, x1 - cx)
    a1 = math.atan2(y2 - cy, x2 - cx)
    # sweep-flag 1 = oplopende hoek = met de klok mee op een y-omlaag-canvas.
    return cx, cy, r, a0, a1, (sf == 0)


def _parse_paths(svg, bestand):
    """-> (paths, arcs). paths zijn polylijnen, arcs echte cirkelbogen."""
    paths, arcs = [], []
    for m in PATH_D.finditer(svg):
        d = m.group(1)
        if re.search(r"[mlazcsqtvhCSQTVH]", d):
            # Relatieve of curve-commando's: niet ondersteund, en stilzwijgend
            # negeren zou geometrie laten verdwijnen.
            raise SystemExit(
                f"{bestand}: pad met niet-ondersteund commando "
                f"(alleen absolute M/L/A/Z): {d[:60]}")
        toks = list(_tokens(d))
        i, cur, start, run = 0, None, None, []
        while i < len(toks):
            t = toks[i]
            if t == "M":
                if len(run) >= 2:
                    paths.append({"p": [c for pt in run for c in pt]})
                cur = (toks[i + 1], toks[i + 2]); start = cur; run = [cur]; i += 3
            elif t == "L":
                cur = (toks[i + 1], toks[i + 2]); run.append(cur); i += 3
            elif t == "A":
                rx, ry, rot, laf, sf, x2, y2 = toks[i + 1:i + 8]
                if abs(rx - ry) > 1e-9 or abs(rot) > 1e-9:
                    raise SystemExit(
                        f"{bestand}: elliptische of geroteerde boog "
                        f"(rx={rx}, ry={ry}, rot={rot}) wordt niet ondersteund")
                cx, cy, r, a0, a1, ccw = _arc_center(cur[0], cur[1], x2, y2, rx, int(laf), int(sf))
                arcs.append({"cx": round(cx, 4), "cy": round(cy, 4), "r": round(r, 4),
                             "a0": round(a0, 6), "a1": round(a1, 6), "ccw": 1 if ccw else 0})
                # De boog onderbreekt de polylijn.
                if len(run) >= 2:
                    paths.append({"p": [c for pt in run for c in pt]})
                cur = (x2, y2); run = [cur]; i += 8
            elif t == "Z":
                if len(run) >= 2:
                    paths.append({"c": 1, "p": [c for pt in run for c in pt]})
                run = [start] if start else []
                cur = start; i += 1
            else:
                raise SystemExit(f"{bestand}: onverwacht token {t!r} in pad")
        if len(run) >= 2:
            paths.append({"p": [c for pt in run for c in pt]})
    return paths, arcs


def _parse_texts(svg):
    out = []
    for m in TEXT_EL.finditer(svg):
        attrs = dict(ATTR.findall(m.group(1)))
        inhoud = re.sub(r"<[^>]*>", "", m.group(2)).strip()
        if not inhoud:
            continue
        try:
            x, y = float(attrs.get("x", "")), float(attrs.get("y", ""))
        except ValueError:
            continue
        s = attrs.get("font-size", "2")
        try:
            s = float(re.sub(r"[a-z]+$", "", s.strip()))
        except ValueError:
            s = 2.0
        out.append({"x": round(x, 4), "y": round(y, 4), "t": inhoud, "s": round(s, 4)})
    return out


def _aanzicht(titel, stem):
    """Familie volgt het aanzicht: dat is een eigen representatie, geen maat."""
    m = re.search(r"-\s*([a-z]+aanzicht|doorsnede|plattegrond|detail)\s*$", titel, re.I)
    return (m.group(1).lower() if m else "aanzicht")


MAAT_TOKEN = re.compile(r"\b(\d+\s*[xX\u00d7]\s*\d+|[Dd]\s*\d+(?:[.,]\d+)?)\b")


def _maat(titel, desc, stem):
    """Maatlabel voor de dropdown.

    Eerst het stuk vóór het aanzicht in de titel ("8x60"). Levert dat alleen de
    productcode op - bij de kopaanzichten heet het bestand HBSPL_HEAD_10 - dan
    de maat uit de <desc> ("kopaanzicht D10"). Zo leest de dropdown als D8/D10
    in plaats van als bestandsnamen.
    """
    kern = re.sub(r"\s*-\s*[a-z]+(aanzicht|doorsnede|plattegrond|detail)\s*$", "", titel, flags=re.I)
    deel = [d.strip() for d in kern.split("-") if d.strip()]
    kandidaat = deel[-1] if deel else stem
    if MAAT_TOKEN.search(kandidaat):
        return MAAT_TOKEN.search(kandidaat).group(1).replace(" ", "")
    m = MAAT_TOKEN.search(desc or "")
    return m.group(1).replace(" ", "") if m else kandidaat


def bouw(productlijn_map):
    svg_map = productlijn_map / "svg"
    if not svg_map.is_dir():
        raise SystemExit(f"geen svg/ in {productlijn_map}")
    leverancier, productlijn = productlijn_map.parent.name, productlijn_map.name

    families = {}
    for pad in sorted(svg_map.glob("*.svg")):
        svg = pad.read_text(encoding="utf-8")
        vb = VIEWBOX.search(svg)
        if not vb:
            raise SystemExit(f"{pad.name}: geen viewBox")
        w, h = float(vb.group(3)), float(vb.group(4))
        titel = (TITLE.search(svg).group(1).strip() if TITLE.search(svg) else pad.stem)
        desc = (DESC.search(svg).group(1).strip() if DESC.search(svg) else "")
        paths, arcs = _parse_paths(svg, pad.name)
        texts = _parse_texts(svg)
        fam = _aanzicht(titel, pad.stem)
        families.setdefault(fam, []).append({
            "id": pad.stem, "label": _maat(titel, desc, pad.stem),
            "w": round(w, 4), "h": round(h, 4),
            "paths": paths, "arcs": arcs, "texts": texts,
        })

    catalogus = {
        "format": "linework-variants",
        "formatVersion": 1,
        "units": "mm",
        "id": f"{leverancier}-{productlijn}".lower().replace(" ", "-"),
        "name": f"{leverancier} {productlijn}",
        "label": {"nl": leverancier, "en": leverancier},
        "families": [{
            "id": f"{productlijn}-{fam}".lower().replace(" ", "-"),
            "name": {"nl": f"{productlijn} ({fam})", "en": f"{productlijn} ({fam})"},
            "defaultSize": varianten[0]["label"],
            "variants": varianten,
        } for fam, varianten in sorted(families.items())],
    }

    uit = productlijn_map / "openpdfstudio"
    uit.mkdir(exist_ok=True)
    doel = uit / "parametric.json"
    doel.write_text(json.dumps(catalogus, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{doel.relative_to(WORTEL)}  ({doel.stat().st_size/1024:.0f} KB)")
    for f in catalogus["families"]:
        n_p = sum(len(v["paths"]) for v in f["variants"])
        n_a = sum(len(v["arcs"]) for v in f["variants"])
        n_t = sum(len(v["texts"]) for v in f["variants"])
        print(f"  {f['name']['nl']:<34} {len(f['variants']):>3} varianten, "
              f"{n_p} paden, {n_a} bogen, {n_t} stempelingen")
    return doel


if __name__ == "__main__":
    doelen = ([Path(a) for a in sys.argv[1:]]
              or sorted(p.parent for p in EXTRACTEN.glob("*/*/svg") if p.is_dir()))
    if not doelen:
        raise SystemExit("geen productlijnen met een svg/-map gevonden")
    for d in doelen:
        bouw(d)
