# Nederlandse Tekenstandaard voor Bouwkundige Tekeningen

## 1. Inleiding

Dit document beschrijft de Nederlandse standaard voor bouwkundige tekeningen, gebaseerd op:
- **NEN 47:1970** - Doorsnede-aanduidingen van materialen op bouwkundige tekeningen
- **NEN 2302** - Maatvoering en annotatie
- **NEN 128-50** - Arceringsrichtlijnen
- **GB CAD-afspraken** - Digitale implementatie van NEN-normen
- **INB-Template** - Open source implementatie door 3BMLabs/OpenAEC

## 2. Relevante NEN-normen

| Norm | Onderwerp |
|------|-----------|
| NEN 47:1970 | Doorsnede-aanduidingen van materialen |
| NEN 47:1970/C1:1971 | Correctieblad bij NEN 47 |
| NEN 2302 | Maatvoering, maatinschrijving, lijnsoorten, arceringen |
| NEN 128-50 | Arceringsrichtlijnen bij aangrenzende materialen |
| NEN 6135-6142 | Gewapend betontekeningen |
| NEN-bundel 10 | Verzameling van 41 tekennormen |

## 3. Arceringen (Hatches)

### 3.1 Algemene Principes

Arceringen zijn **niet verplicht** zolang de tekening duidelijk is. Wanneer arceringen worden toegepast:
- Moeten ze volgens **NEN 47** worden getekend
- Gestandaardiseerde arceringen hoeven niet in het renvooi
- Afwijkende arceringen moeten wel in het renvooi worden vermeld
- Bij aangrenzende doorsneden van hetzelfde materiaal: arcering in verschillende richtingen (NEN 128-50)

### 3.2 Materiaalgroepen

De materialen worden in vier hoofdgroepen ingedeeld:

1. **Steenachtige materialen**
   - Metselwerk baksteen
   - Kalkzandsteen
   - Natuursteen
   - Speciale steenachtige materialen

2. **Beton**
   - Gewapend beton (ter plaatse gestort)
   - Gewapend beton (prefab)
   - Ongewapend beton
   - Sierbeton

3. **Houtachtige materialen**
   - Naaldhout
   - Loofhout
   - Bekledingsplaten (multiplex, MDF, OSB)

4. **Metalen en overige**
   - Staal, aluminium, koper, lood, zink
   - Isolatiematerialen
   - Kunststoffen
   - Afdichtingsmiddelen

### 3.3 NEN 47 Arceringscatalogus

| Nr | Materiaal | Arceringstype | Hoek | Lijnafstand |
|----|-----------|---------------|------|-------------|
| 1 | Metselwerk baksteen | Dubbele diagonale lijn | 45° | 3mm |
| 2 | Speciale steenachtige materialen | Raster | 45° | 2mm |
| 3 | Kalkzandsteen | Enkele diagonale lijn | 45° | 1.5mm |
| 4 | Lichte scheidingswanden | Verticale lijnen | 0° | 0.5mm |
| 5 | Gewapend beton TPG | Solid grijs | - | - |
| 6 | Gewapend beton prefab | Enkele diagonale lijn | 45° | 1.5mm |
| 7 | Ongewapend beton | Kruisarcering | 45° | 3mm |
| 8 | Sierbeton | Horizontale lijnen + half | 135° | 3mm |
| 9 | Natuursteen | Korte horizontale lijnen | 135° | 1.5mm |
| 10 | Enkele afwerking | Zigzag | 0° | 6mm |
| 11 | Samengestelde afwerking | Zigzag + horizontaal | 0° | 6mm |
| 12 | Naaldhout | Enkele diagonale lijn | 45° | 1.5mm |
| 13 | Loofhout | Kruisarcering | 45° | 1.5mm |
| 14 | Hout langsarcering | Horizontale lijnen | 0° | 1.5mm |
| 16 | Bekledingsplaat | Verticale lijnen | 90° | 1.5mm |
| 17 | Isolatie | Kruis (X) | 0° | 1.5mm |
| 18 | Staal | Solid zwart | - | - |
| 19 | Aluminium/koper | Solid grijs | - | - |
| 20 | Lood | Dambord | - | 3mm |
| 21 | Zink | Solid zwart | - | - |
| 22 | Kunststof | Enkele diagonale lijn | 45° | 1.5mm |
| 23 | Afdichtingsmiddel | Puntjes | - | 10mm |
| 24 | Bitumen | Solid zwart | - | - |
| 25 | Maaiveld/grond | Diagonale vulling | 45° | 2.5mm |
| 26 | Zand | Puntjes | - | 50mm |
| 27 | Grind | Cirkels | - | 40mm |
| 28 | Water | Golflijnen | 0° | 5mm |
| 29 | Glas | Horizontale lijnen schuin | 0° | 3mm |

### 3.4 Achtergrondkleuren

Naast de arcering kan een achtergrondkleur worden toegepast die het materiaal visueel ondersteunt. Dit komt voort uit de oude tekentafel-traditie waar de arcering op de voorgrond werd getekend en de achtergrond de 'doorsnedekleur' representeerde.

## 4. Lijndiktes

### 4.1 Standaard Verhoudingen

Lijndiktes verhouden zich als **1:2:4** (dun:dik:extra dik).

Standaard set: 0.13mm, 0.25mm, 0.5mm

### 4.2 Volledig Bereik

| Dikte (mm) | Naam | Toepassing |
|------------|------|------------|
| 0.13 | Extra fijn | Hulplijnen, arceringen kleine schaal |
| 0.18 | Fijn | Arceringen, schaduwen |
| 0.25 | Normaal | Aanzichtlijnen, annotaties |
| 0.35 | Medium | Doorsneden lichte elementen |
| 0.50 | Dik | Doorsneden constructie |
| 0.70 | Extra dik | Zware constructie, beton |
| 1.00 | Zwaar | Snijlijnen, titels |
| 1.40 | Extra zwaar | Kaderlijnen |

### 4.3 Belangrijke Regel

> Een doorsnedelijn is **altijd dikker** dan een aanzichtlijn.

## 5. Lijntypen

### 5.1 Standaard Lijntypen

| Type | Patroon | Toepassing |
|------|---------|------------|
| Continuous | Doorlopend | Zichtbare contouren, maatlijnen |
| Dashed | 6-3 | Verborgen lijnen |
| Hidden | 9-3 | Verborgen contouren |
| Center | 12-3-3-3 | Hartlijnen, aslijnen |
| Phantom | 12-3-3-3-3-3 | Bewegende delen |
| Dot | 1-3 | Grenzen, projecties |
| Dashdot | 6-3-1-3 | Snijvlakken |

### 5.2 Nederlandse Specifieke Lijntypen

- **Hartlijn**: 10-1-1-1 (korter streepje dan center)
- **Folie**: 3-1.5-3-1.5 (voor dampremmende lagen)
- **Stramien**: 10-4-2-4 (blauw, met grid markers)

## 6. Schaalafhankelijkheid

Arceringen zijn schaalafhankelijk. De INB-Template definieert de volgende schaalfactoren:

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

## 7. Renvooi (Legenda)

### 7.1 Plaatsing

Het renvooi wordt geplaatst **boven de identificatiestrook** (tekeningkop).

### 7.2 Inhoud

- Alleen niet-standaard arceringen
- Afwijkingen van NEN 47
- Project-specifieke aanvullingen
- Kleuraanduidingen indien afwijkend

## 8. Bestandsformaten

### 8.1 OconDat Datastructuur

De tekenstandaard wordt opgeslagen in de volgende formaten:

```
NL-Drawing-Standards/
├── data/
│   ├── hatches/
│   │   └── NEN47-hatches.json      # Volledige arceringsdefinities
│   ├── linetypes/
│   │   └── NL-linetypes.json       # Lijntypen en diktes
│   └── colors/
│       └── NL-colors.json          # Kleurendefinities
├── css/
│   ├── NL-BWK-1_50.css            # Per schaal gegenereerd
│   └── ...
├── svg/
│   └── patterns.svg               # SVG patronen
└── docs/
    └── NL-Drawing-Standards.md    # Deze documentatie
```

### 8.2 CSS-implementatie

De CSS-bestanden bevatten:
- `.material-{naam}` classes voor IFC-materialen
- `.PredefinedType-{type}` classes voor Bonsai/BlenderBIM
- Schaalspecifieke patronen

## 9. Bronnen

- [NEN 47:1970](https://www.nen.nl/nen-47-1970-nl-7779)
- [TU Delft BK Wiki - Standaard lijndiktes en arceringen](http://wiki.bk.tudelft.nl/bk-wiki/Standaard_lijndiktes_en_arceringen)
- [INB-Template GitHub](https://github.com/3BMLabs/INB-Template)
- [Bouwkundig detailleren - Arceringen](https://berkela.home.xs4all.nl/tekenen/arceren.html)
- [OpenAEC Foundation](https://github.com/OpenAEC-Foundation)

## 10. Licentie

Dit document en de bijbehorende databestanden vallen onder de **GPL-3.0** licentie, in lijn met de INB-Template waarop dit is gebaseerd.

---

*Versie 1.0.0 - Januari 2026*
*Onderdeel van het OconDat (Open Construction Data) project*
