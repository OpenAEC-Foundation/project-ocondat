# _TOOLS

De generatorcode van de bibliotheek. Geen bron en geen extract: dit is de
machinerie waarmee `02_EXTRACTEN` uit `01_SOURCE` gemaakt wordt.

> **Eerlijk over de staat.** Dit zijn de werkscripts van de eerste set
> (Rothoblaas HBS PLATE), niet een afgeronde pijplijn. Ze doen wat ze moeten
> doen en zijn gedocumenteerd, maar paden en aannames zijn deels op die set
> geschreven. Reken op aanpassen bij een volgende leverancier — en lees de
> valkuilen in de scripts, want die zijn duur betaald.

## Bestanden

| Bestand | Wat het doet |
|---|---|
| `curveclean.py` | Leest DXF-curves en knijpt curves onder de Revit-tolerantie eruit. Het hart van de RFA-keten. |
| `bbox.py` | Exacte bounding boxes, ook voor bogen. Nodig om producten te clusteren. |
| `blad_naar_svg.py` | Splitst een bronblad in producten en schrijft per product een SVG (1:1, mm). |
| `blad_naar_dxf.py` | Idem, maar schrijft genormaliseerde DXF-extracten plus het manifest. |
| `blokken_naar_extract.py` | Haalt benoemde blokken uit de bron als losse extracten. Gebruikt voor de kopaanzichten. |
| `rfa_opdrachten.py` | Maakt per product een JSON-opdracht voor Revit, met geschoonde geometrie. |
| `revit_bouw.py` | **Draait binnen Revit.** Bouwt de families en de verzamelfamilie, en controleert ze. |
| `registreer.py` | Verzoent `00_DATABASE` met wat er op schijf staat: hasht alles, vult ontbrekende assetregels aan, leidt de afhankelijkheden af. |
| `openpdfstudio_*.py` | Los van bovenstaande keten. |

## Volgorde

```text
01_SOURCE/…/CAD/bron.dxf
        │
        ├─ blad_naar_dxf.py ────────> 02_EXTRACTEN/…/dxf/
        ├─ blad_naar_svg.py ────────> 02_EXTRACTEN/…/svg/
        └─ blokken_naar_extract.py ─> beide, voor losse aanzichten
                    │
                    ▼
            rfa_opdrachten.py  (buiten Revit: schoonmaken + JSON)
                    │
                    ▼
            revit_bouw.py      (binnen Revit: families + verzamelfamilie)
                    │
                    ▼
            registreer.py      (database bijwerken - altijd als laatste)
```

De zware rekenstap staat bewust buiten Revit. Dat houdt de Revit-kant kort en
maakt hem herhaalbaar zonder de applicatie.

## registreer.py — verzoenen, niet verzinnen

Draai hem na elke generatieslag. Zonder argumenten rapporteert hij alleen;
met `--schrijf` werkt hij `assets.csv`, `dependencies.csv` en `update-log.csv`
bij.

Drie eigenschappen die de moeite van het onthouden waard zijn:

* **Menselijke velden blijven staan.** `source_url`, `source_page`,
  `download_date`, `status` en `product_id` worden op bestaande regels nooit
  overschreven. Dat is juist de informatie die geen script terug kan maken.
* **Niets wordt verzonnen.** Kan hij een veld niet uit het pad afleiden, dan
  laat hij het leeg. Een leeg veld is eerlijker dan een geraden waarde.
* **Een vermist bestand wordt gemeld, niet verwijderd.** Weggooien is een
  beslissing.

Let op: `dependencies.csv` wordt wél volledig opnieuw afgeleid uit de
conventie. Met de hand toegevoegde toelichtingen daarin gaan verloren.
`products.csv` raakt hij niet aan — productgegevens komen uit de tekening en de
datasheet, niet uit het bestandssysteem.

## Twee omgevingen

`curveclean` en de blad-scripts draaien op **CPython 3** met `ezdxf`.
`revit_bouw.py` draait op **IronPython 2.7 binnen Revit** — geen f-strings, geen
`pathlib`, en alleen wat de Revit API biedt.

## Waar de uitleg staat

De inhoudelijke regels — waarom er geschoond wordt, welke tolerantie geldt, hoe
bogen omgezet worden, wat er gecontroleerd moet worden — staan niet hier maar in:

* [Extract DXF](../02_EXTRACTEN/Extract%20DXF.md)
* [Extract SVG](../02_EXTRACTEN/Extract%20SVG.md)
* [Extract RFA](../02_EXTRACTEN/Extract%20RFA.md)
* [Bibliotheek opbouwen - werkwijze](../Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md)
* [Systeemomschrijving](../Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) — leidend
