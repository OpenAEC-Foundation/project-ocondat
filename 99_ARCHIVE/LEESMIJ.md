# 99_ARCHIVE

Vervangen versies, per datum. Hier wordt niets weggegooid.

```text
99_ARCHIVE/
└── YYYY-MM-DD/
    └── <Leverancier>/
        └── <Productlijn>/
            └── …
```

De map beantwoordt één vraag:

> Welke fabrikantversie was beschikbaar toen dit detail werd gemaakt?

Zonder die vraag te kunnen beantwoorden is een detail in een uitgevoerd project
niet meer te verantwoorden. Daarom gaat een vervangen bron hierheen en niet in
de prullenbak, ook als de nieuwe versie in alles beter lijkt.

## Wanneer er iets heen gaat

Bij een gewijzigde fabrikantbron, vóór de verwerking:

```text
NIEUWE DXF
  ↓
ARCHIVEER DE OUDE          <- hier
  ↓
VALIDEER → NORMALISEER → GENEREER
  ↓
VERGELIJK GEOMETRIE
  ↓
MARKEER AFHANKELIJKHEDEN
  ↓
BEOORDEEL → KEUR GOED
```

Een gewijzigde bron wordt dus **niet stilzwijgend in de definitieve bibliotheek
gezet**. Zie §21 en §22 van de systeemomschrijving.

Ook hierheen: mappen uit de oude, op bouwdeel ingedeelde structuur nadat hun
inhoud is teruggebracht tot bron en extract. Zie §6 van
[VOORSTEL.md](../VOORSTEL.md).

## Wat er in de update-log bij hoort

Elke archiveerslag krijgt een regel in `../00_DATABASE/update-log.csv` met de
datum, wie het deed, en waarom. De archiefmap zelf zegt alleen *wat* er lag; de
log zegt *waarom* het er niet meer ligt.
