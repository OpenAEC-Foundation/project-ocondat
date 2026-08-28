# _TOOLS

De generatorcode. Alles in `02_EXTRACTEN` komt hiervandaan.

> **Klopt er iets niet aan een extract, pas dan het script aan — niet het
> bestand.** De volgende generatieslag overschrijft handwerk geruisloos. De
> kwaliteitscontrole uit §25 van de systeemomschrijving geldt daarom de
> generator, niet het losse resultaat.

## De scripts

| Script | Van | Naar |
|---|---|---|
| `curveclean.py` | DXF-extract | opgeschoonde geometrie voor Revit-detaillijnen |
| `openpdfstudio_library.py` | SVG-extracten | Open PDF Studio symboolbibliotheek (`Import Group`-formaat) |
| `openpdfstudio_parametric.py` | SVG-extracten | Open PDF Studio linework-catalogus met maatvarianten |

### `curveclean.py`

Revit weigert curves korter dan `ShortCurveTolerance` — 0,7804 mm bij een
standaardinstallatie — en fabrikantgeometrie zit daar regelmatig onder. Dit
script voegt zulke segmenten samen. Twee dingen die het expliciet níet doet:

* **niet welden op afstand.** Dat stort draadtanden in: de twee flanken van een
  tand liggen bij de tip zo'n 0,7 mm uit elkaar. Er wordt uitsluitend langs de
  *keten* samengevoegd — buren die echt aan elkaar vastzitten.
* **niet een boog als eindpuntenpaar behandelen.** Een boog blijft
  `(center, radius, a0, a1)` met `a1 = a0 + sweep`, en een verschoven eindpunt
  wordt uitgepakt rond de oude hoek. Zonder dat klapt een minieme negatieve
  draai om naar bijna 2π en wordt een boogje van een halve millimeter een hele
  cirkel.

De afwijking blijft onder 0,4 mm; nominale hoofdmaten blijven exact. De
vereenvoudiging hoort in de RFA-tak en mag niet doorwerken in de DXF en SVG,
die het volledige fabrikantdetail houden.

### `openpdfstudio_library.py`

Schrijft platte stempels: één palet-ingang per product. De app leidt het
symbool-id af uit de **naam**, niet uit de bestandsnaam, dus namen moeten uniek
zijn — twee gelijke namen delen één id en verwijderen raakt er dan twee. Alleen
`name` en `svg` overleven de import; productcode en aanzicht horen dus in de
naam verwerkt te zijn.

### `openpdfstudio_parametric.py`

Schrijft `parametric.json` in het formaat `linework-variants`: één familie per
aanzicht, met de producten als varianten — één palet-ingang met een maat-keuze
in plaats van een los symbool per product.

**Bogen blijven bogen.** De SVG-boog (`A`, eindpuntnotatie) wordt teruggerekend
naar middelpunt, straal en hoeken, niet gepolygoniseerd; een benadering is bij
het terugmeten niet meer te herstellen. Wijkt de bron af van de aannames — paden
absoluut, bogen cirkelvormig zonder rotatie — dan stopt het script in plaats van
stilletjes iets verkeerds te schrijven.

## Afhankelijkheden

`ezdxf` voor het lezen en schrijven van DXF. De rest is standaardbibliotheek.

De scripts gaan uit van de bibliotheekwortel als bovenliggende map (`WORTEL =
Path(__file__).resolve().parent.parent`) en zoeken hun invoer in
`02_EXTRACTEN/<Leverancier>/<Productlijn>/`.

## Nog te schrijven

De keten is nog niet volledig geautomatiseerd. Wat er nog niet als script
bestaat, en dus nu nog handwerk is:

* **bron → dxf/svg.** Het opsplitsen in producten en het koppelen van labels is
  in de pilot stap voor stap gedaan; de werkwijze is beschreven in
  [Bibliotheek opbouwen · werkwijze](../Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md),
  inclusief de twee controles die je niet mag overslaan.
* **dxf → rfa.** De aansturing van Revit staat in
  [Extract RFA.md](../02_EXTRACTEN/Extract%20RFA.md). Zolang iemand de familie
  met de hand maakt, is `rfa/` een uitzondering op de regel dat `02_EXTRACTEN`
  herbouwbaar is — en die uitzondering breekt het model.
* **de actualiteitschecker** uit §15 en §20 van de systeemomschrijving.
