# 01_SOURCE

Fabrikantsbestanden, **read-only**. Alles hier komt van buiten en is niet door
ons gemaakt.

> ## Bewerk hier nooit iets
>
> Een bestand in deze map is het bewijsstuk waar alle extracten en alle
> maatvoering op teruggaan. Wordt het aangepast, dan klopt de hash in
> `assets.csv` niet meer en is de herkomst weg. Opschonen, verschuiven en
> normaliseren gebeurt in de generator, en het resultaat landt in
> `02_EXTRACTEN`.

## Indeling

Een niveau bestaat pas als er iets op dat niveau ligt. Een bedrijfsbrochure
hoort bij de leverancier, een productgroepcatalogus bij de productgroep:

```text
01_SOURCE/
└── <Leverancier>/                 bedrijfsbrochure, algemene catalogus
    └── [<Productgroep>/]          alleen als er iets op dat niveau ligt
        └── <Productlijn>/
            ├── CAD/               DXF, DWG
            ├── BIM/               RFA, IFC, STEP
            └── DOCUMENTATION/     datasheet, ETA, montage-instructie
```

Is er alleen brondata per productlijn, dan valt de tussenlaag weg en krijg je
direct `01_SOURCE/<Leverancier>/<Productlijn>/`.

## Deze map is leeg in deze pull request

Het voorstel gaat over **waar** fabrikantsbestanden horen, niet over welke er
gepubliceerd worden. Of materiaal van derden op een publieke repo mag staan is
een aparte afweging, per leverancier; zie §6 van [VOORSTEL.md](../VOORSTEL.md).

Zolang die afweging niet gemaakt is, kan de bibliotheek ook werken met een
lokale `01_SOURCE` buiten versiebeheer: de administratie in `00_DATABASE`
registreert dan de hash, de `source_url` en de `download_date`, zodat de
herkomst controleerbaar blijft zonder dat het bestand zelf meegaat.

## Wat er wél altijd vastgelegd wordt

Per bronbestand een rij in `../00_DATABASE/assets.csv`, met minimaal:

| Veld | Waarom |
|---|---|
| `file_hash` | SHA-256 — hiermee ziet de actualiteitschecker een gewijzigde bron, ook bij dezelfde naam en URL |
| `source_url` | de directe downloadlink |
| `source_page` | de productpagina, om te kunnen zien of het product nog bestaat |
| `download_date` | wanneer wij het ophaalden |
| `source_date` | de datum die de fabrikant zelf op het bestand zet |

**Heb je het origineel niet, noteer dat dan expliciet.** Een reconstructie is
geen bron.

## Verwante documenten

* [Systeemomschrijving](../Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) — §14 metadata, §15 actualiteitschecker, §16 hash
* [VOORSTEL.md](../VOORSTEL.md) — waarom de indeling op herkomst loopt
