# 02_EXTRACTEN

Alles in deze map is **automatisch gegenereerd** uit `01_SOURCE`.

> ## Pas hier nooit iets met de hand aan
>
> De volgende generatieslag overschrijft handwerk geruisloos. Klopt er iets
> niet, pas dan de generator in `_TOOLS` aan, niet het bestand. Daarmee geldt
> de kwaliteitscontrole uit §25 van de systeemomschrijving de **generator**,
> niet het losse bestand.

Deze map mag in zijn geheel weg en opnieuw worden opgebouwd. Dat is precies
waarom hij losstaat van `00_DATABASE`, dat beslissingen en historie bevat die
geen script terug kan maken.

## Indeling

```text
02_EXTRACTEN/
├── LEESMIJ.md            <- dit bestand
├── Extract DXF.md
├── Extract SVG.md
├── Extract RFA.md
└── <Leverancier>/<Productlijn>/
    ├── dxf/
    ├── svg/
    └── rfa/
```

Het pad onder `02_EXTRACTEN` is gelijk aan dat onder `01_SOURCE`, zodat je van
bron naar extract springt door alleen het eerste segment om te wisselen.

## De drie extracttypen

| Type | Waarvoor | Eenheid | Instructie |
|---|---|---|---|
| **DXF** | genormaliseerde CAD per product, invoegpunt op nul | mm, `INSUNITS 4` | [Extract DXF.md](Extract%20DXF.md) |
| **SVG** | vector voor PDF, documentatie en web | mm, schaal 1:1 | [Extract SVG.md](Extract%20SVG.md) |
| **RFA** | Revit detailcomponenten | mm → voet | [Extract RFA.md](Extract%20RFA.md) |

De keten is niet lineair: **SVG en DXF komen allebei rechtstreeks uit de bron**,
de RFA komt uit de DXF.

```text
01_SOURCE/…/CAD/bron.dxf
        ├──> dxf/<code>.dxf ──> rfa/<code>.rfa
        └──> svg/<code>.svg
```

## Volgorde en detailniveau

DXF en SVG houden het **volledige fabrikantdetail**. Alleen de RFA wordt
vereenvoudigd, omdat Revit curves onder 0,78 mm weigert. Die vereenvoudiging
hoort in de RFA-generator en mag niet doorwerken in de andere twee.

## Verwante documenten

* [Systeemomschrijving](../Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) — architectuur, metadata, statusmodel (leidend)
* [Bibliotheek opbouwen - werkwijze](../Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md) — de stappen van bron naar extract
* `../_TOOLS/` — de generatorcode
