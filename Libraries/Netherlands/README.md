# NL-Drawing-Standards

Open Construction Data (OconDat) module voor Nederlandse bouwkundige tekenstandaarden.

## Overzicht

Dit project bevat de geverifieerde Nederlandse tekenstandaarden voor bouwkundige tekeningen, gebaseerd op:
- **NEN 47:1970** - Doorsnede-aanduidingen (arceringen)
- **NEN 2302** - Maatvoering en annotatie
- **INB-Template** - Open source implementatie door 3BMLabs

## Structuur

```
NL-Drawing-Standards/
├── data/
│   ├── hatches/
│   │   └── NEN47-hatches.json    # 29 NEN 47 arceringen + varianten
│   ├── linetypes/
│   │   └── NL-linetypes.json     # Lijntypen en lijndiktes
│   └── colors/
│       └── NL-colors.json        # Materiaal kleuren
├── css/                          # Gegenereerde CSS per schaal
├── svg/                          # SVG pattern definities
└── docs/
    └── NL-Drawing-Standards.md   # Volledige documentatie
```

## Gebruik

### JSON Data
De JSON-bestanden bevatten alle gestructureerde data over arceringen, lijntypen en kleuren. Deze kunnen worden geimporteerd in tekenprogramma's zoals:
- Bonsai/BlenderBIM
- FreeCAD
- Andere open source CAD/BIM tools

### CSS/SVG
De CSS-bestanden zijn schaalspecifiek en kunnen direct worden gebruikt in SVG-gebaseerde tekenoutput.

## Schalen

Ondersteunde schalen met hun schaalfactoren:
| Schaal | Factor |
|--------|--------|
| 1:200 | 0.5 |
| 1:100 | 0.75 |
| 1:50 | 0.75 |
| 1:20 | 0.75 |
| 1:10 | 0.9 |
| 1:5 | 2.6 |
| 1:2 | 6.0 |
| 1:1 | 12.0 |

## Bronnen

- [INB-Template](https://github.com/3BMLabs/INB-Template)
- [NEN 47:1970](https://www.nen.nl/nen-47-1970-nl-7779)
- [TU Delft BK Wiki](http://wiki.bk.tudelft.nl/bk-wiki/Standaard_lijndiktes_en_arceringen)

## Licentie

GPL-3.0 - Zie LICENSE bestand
