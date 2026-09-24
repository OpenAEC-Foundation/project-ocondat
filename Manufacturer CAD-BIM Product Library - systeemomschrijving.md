# Manufacturer CAD/BIM Product Library

> ## Begin hier — een product toevoegen
>
> Dit document is leidend voor de architectuur. Dit blok is de ingang: het zegt
> wat er is, wat er moet gebeuren en waar de rest staat.
>
> **Wortel:** de repo-wortel van `project-ocondat`.
>
> ### Wat er nu staat
>
> | | |
> |---|---|
> | Leveranciers | 1 — Rothoblaas |
> | Productlijnen | 1 — HBS PLATE, 18 producten (Ø8/10/12 × 60–200 mm) |
> | Extracten | 21 dxf · 21 svg · 22 rfa |
> | Verzamelfamilie | `NLRS_28_DI_UN_schroef_HBS-PLATE_Rothoblaas_bluetek.rfa`, 21 types |
> | Database | `00_DATABASE/` — assets, products, suppliers, dependencies, update-log |
> | Status | alles `REVIEW REQUIRED` — zie Open onderaan |
>
> ### Een product toevoegen aan een bestaande productlijn
>
> 1. Zet het fabrikantsbestand in `01_SOURCE/<leverancier>/<productlijn>/CAD/`
>    en laat het daar ongemoeid. Leg de SHA-256 vast in `assets.csv`.
> 2. `_TOOLS/blad_naar_dxf.py` en `_TOOLS/blad_naar_svg.py` — splitsen het blad
>    in producten en schrijven de extracten. Losse aanzichten die als blok in de
>    bron zitten: `_TOOLS/blokken_naar_extract.py`.
> 3. `_TOOLS/rfa_opdrachten.py` — schoont de geometrie en schrijft de opdrachten.
> 4. `_TOOLS/revit_bouw.py` — **binnen Revit** — bouwt de families en voegt ze
>    als type toe aan de verzamelfamilie.
> 5. `_TOOLS/registreer.py --schrijf` — hasht alles, vult `assets.csv` aan en
>    leidt `dependencies.csv` af. Zonder argumenten rapporteert hij alleen; draai
>    dat eerst. De productgegevens in `products.csv` zet je zelf: die komen uit de
>    tekening en de datasheet, niet uit het bestandssysteem.
> 6. Controleren volgens §25. Sla dat niet over: die controles hebben in de
>    eerste set drie fouten gevonden die er goed uitzagen.
>
> ### Een nieuwe leverancier
>
> Dezelfde stappen, plus een regel in `suppliers.csv` en een map
> `01_SOURCE/<leverancier>/`. De diepte volgt de inhoud: pas een niveau
> aanmaken als er iets op dat niveau ligt (zie §12).
>
> ### Regels die niet gebroken mogen worden
>
> * **`01_SOURCE` is read-only.** Alleen onbewerkte fabrikantsbestanden.
> * **Nooit met de hand iets aanpassen in `02_EXTRACTEN`.** Alles daarin wordt
>   gegenereerd; de volgende slag overschrijft handwerk geruisloos. Klopt er
>   iets niet, pas de generator aan.
> * **Verzin geen productgegevens.** Draagkracht, ETA en voorboormaten komen uit
>   de fabrikantdocumentatie of ze staan er niet in.
> * **Meet na wat je maakt.** Cijfers alleen volstaan niet — render het terug.
>
> ### Waar de rest staat
>
> | | |
> |---|---|
> | Bewerkingsstappen | [Bibliotheek opbouwen - werkwijze](Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md) |
> | Per extracttype | [02_EXTRACTEN/LEESMIJ](02_EXTRACTEN/LEESMIJ.md) → [DXF](02_EXTRACTEN/Extract%20DXF.md) · [SVG](02_EXTRACTEN/Extract%20SVG.md) · [RFA](02_EXTRACTEN/Extract%20RFA.md) |
> | Generatorcode | [_TOOLS/LEESMIJ](_TOOLS/LEESMIJ.md) |
> | Besluiten en open punten | onderaan dit document |

## Systeemomschrijving en structuur

### 1. Doel

Het doel is een **leveranciersonafhankelijke productbibliotheek** op te bouwen waarin technische producten van verschillende fabrikanten centraal worden beheerd en gecontroleerd.

De bibliotheek moet het mogelijk maken om fabrikantbestanden:

* centraal te verzamelen;
* versieerbaar en traceerbaar op te slaan;
* op actualiteit te controleren;
* als 2D-vectorbestand te hergebruiken;
* op schaal in PDF-tekeningen toe te passen;
* als 2D Revit Family te gebruiken;
* eventueel als 3D BIM-object te gebruiken;
* en automatisch te signaleren wanneer een product of bronbestand is gewijzigd, vervangen of uitgefaseerd.

**Rothoblaas is de eerste leverancier waarop het systeem wordt toegepast, maar de architectuur is niet specifiek voor Rothoblaas.**

Het systeem moet later ook leveranciers zoals Würth, Fischer, Hilti, Leviat, Schöck, staalproducenten, plaatleveranciers en andere fabrikanten kunnen verwerken.

---

# 2. Belangrijk uitgangspunt: één product heeft meerdere bronnen

Een product wordt **niet** beschouwd als één CAD-bestand.

Een fabrikant kan voor hetzelfde product verschillende bestanden leveren:

* DXF/DWG met 2D-aanzichten;
* meerdere DXF/DWG-bestanden voor verschillende aanzichten;
* RFA;
* IFC;
* STEP/SAT/andere 3D-formaten;
* technische PDF's;
* catalogusbladen;
* installatie-instructies;
* certificaten en verklaringen.

Deze bestanden worden allemaal als afzonderlijke **source assets** geregistreerd.

Bijvoorbeeld:

```text
PRODUCT
└── Rothoblaas HBS EVO 8×120
    │
    ├── CAD
    │   ├── front.dxf
    │   ├── side.dxf
    │   ├── top.dxf
    │   └── detail.dxf
    │
    ├── BIM
    │   ├── product.rfa
    │   └── product.ifc
    │
    └── DOCUMENTATION
        ├── datasheet.pdf
        └── installation.pdf
```

**Geen van deze bestanden wordt automatisch als vervanging van een ander bestand beschouwd.**

---

# 3. Prioriteit van bronnen

Voor 2D-tekenwerk is de fabrikant-DXF/DWG de primaire bron wanneer die beschikbaar is.

De bronhiërarchie is:

### Voor 2D

1. Fabrikant-DXF/DWG
2. Fabrikant 2D-tekening/PDF
3. Andere officiële 2D-bron
4. Uit 3D gegenereerde projectie — alleen als fallback

### Voor 3D/BIM

1. Fabrikant-RFA
2. Fabrikant-IFC
3. Fabrikant-STEP/SAT/andere 3D-bron
4. Zelf gegenereerd 3D-model — alleen als laatste mogelijkheid

Een vereenvoudigd IFC- of RFA-model mag **nooit automatisch een betere fabrikant-DXF vervangen** voor 2D-detailwerk.

---

# 4. Aanzichten en representaties

Een product bestaat uit één of meerdere **representations**.

Een representation kan bijvoorbeeld zijn:

* Front
* Rear
* Left
* Right
* Top
* Bottom
* Plan
* Elevation
* End
* Section
* Detail
* Installation detail
* 3D

De fabrikant bepaalt welke aanzichten beschikbaar zijn.

Het systeem genereert dus niet automatisch zes aanzichten wanneer de fabrikant zelf specifieke 2D-tekeningen heeft geleverd.

Bijvoorbeeld:

```text
SCHROEF
├── front
├── side
├── head/top
└── detail

BEUGEL
├── front
├── side
├── top
├── section
└── detail

PLAAT
├── plan
├── front
├── side
└── section

PROFIEL
├── longitudinal
├── end
└── section

KANAALPLAAT
├── plan
├── side
├── end
├── longitudinal section
└── connection detail
```

Aanzichten zijn daarmee zelfstandige objecten binnen de bibliotheek.

---

# 5. 2D-vectorbestanden

Wanneer een fabrikant een DXF/DWG levert, wordt dit bestand geconverteerd naar een SVG.

De keten wordt:

```text
OFFICIAL DXF/DWG
       ↓
VALIDATION
       ↓
NORMALISATION
       ↓
SVG
```

De SVG blijft geometrisch **1:1**.

De schaal wordt niet in het bronbestand vastgelegd.

Bij gebruik kan dezelfde geometrie bijvoorbeeld worden toegepast als:

* 1:1
* 1:2
* 1:5
* 1:10
* 1:20

Dit maakt de SVG geschikt voor technische PDF-tekeningen en andere vectorgebaseerde toepassingen.

De oorspronkelijke DXF/DWG blijft altijd behouden.

---

# 6. SVG is een afgeleid bestand

De fabrikant-DXF/DWG blijft de officiële bron.

Bijvoorbeeld:

```text
HBS_FRONT.dxf
       ↓
HBS_FRONT.svg
```

De SVG krijgt metadata waarmee onder andere wordt vastgelegd:

* leverancier;
* product;
* productcode;
* bronbestand;
* bron-URL;
* bronversie;
* datum;
* eenheid;
* hash van het bronbestand.

Als de DXF verandert, kan de SVG opnieuw worden gegenereerd.

---

# 7. Revit

Revit wordt als een aparte output beschouwd.

Een Revit 2D Family wordt gebaseerd op de **beste beschikbare 2D-fabrikantbron**, meestal DXF/DWG.

Dus:

```text
DXF FRONT
DXF SIDE
DXF TOP
DXF SECTION
      ↓
SELECT / CLEAN / QA
      ↓
REVIT 2D FAMILY
```

Niet:

```text
IFC
 ↓
automatische projectie
 ↓
Revit 2D
```

tenzij er geen bruikbare 2D-bron beschikbaar is.

De Revit-family bevat metadata zoals:

* leverancier;
* fabrikantproductcode;
* productnaam;
* gebruikte bronbestanden;
* bronversies;
* datum van controle;
* bibliotheekstatus.

Hierdoor kan de updatechecker later bepalen of een Revit-family opnieuw moet worden beoordeeld.

### De RFA is een extract, geen handwerk

De familie wordt **automatisch gegenereerd** uit de DXF-extracten en staat
daarom in `02_EXTRACTEN/<leverancier>/<productlijn>/rfa/`, naast `dxf/` en
`svg/`. Zie [Extract RFA.md](02_EXTRACTEN/Extract%20RFA.md) voor de werkwijze.

Twee dingen die daarbij vastliggen:

* **Revit weigert curves korter dan `ShortCurveTolerance`** (0,7804 mm bij een
  standaardinstallatie). Fabrikantgeometrie zit daar regelmatig onder. Er gaat
  dus een vereenvoudigingsstap aan vooraf, en die is beschreven in
  [Extract RFA.md](02_EXTRACTEN/Extract%20RFA.md). De afwijking blijft daarbij
  onder 0,4 mm; nominale hoofdmaten blijven exact.
* **Meerdere types in één familie delen dezelfde geometrie.** Producten die in
  lijnwerk verschillen — bij HBS PLATE loopt het aantal draadtanden van 10 naar
  33 — kunnen dus niet zomaar types van elkaar zijn. Zie de besluitenlijst
  onderaan dit document.

---

# 8. Verschillende detailniveaus

Niet ieder product hoeft dezelfde hoeveelheid geometrie te bevatten.

Er worden verschillende detailniveaus ondersteund:

### SYMBOL

Eenvoudige grafische representatie.

### DETAIL

Technisch herkenbare 2D-weergave voor tekeningen.

### HIGH DETAIL

Uitgebreide fabrikantgeometrie.

### 3D

Volledig of fabrikant-specifiek 3D-model.

Hierdoor wordt voorkomen dat een eenvoudige 2D-tekening onnodig wordt gevuld met duizenden lijnen.

---

# 9. Leveranciers

De bibliotheek is leverancier-onafhankelijk.

```text
SUPPLIERS
├── Rothoblaas
├── Würth
├── Fischer
├── Hilti
├── Leviat
├── Schöck
├── Leverancier X
└── ...
```

Iedere leverancier heeft een eigen bronconfiguratie.

Een leverancier kan bijvoorbeeld:

```text
DXF ✓
DWG ✓
RFA ✓
IFC ✓
STEP ✗
```

terwijl een andere leverancier:

```text
DWG ✓
RFA ✗
IFC ✓
STEP ✓
```

levert.

Het systeem past zich hieraan aan.

---

# 10. Productcategorieën

Productcategorieën worden generiek gedefinieerd.

Voorbeelden:

```text
FASTENER
SCREW
ANCHOR
PLATE
BRACKET
CONNECTOR
PROFILE
CHANNEL
PANEL
SLAB
PIPE
DUCT
FITTING
INSULATION
ROOF COMPONENT
FACADE COMPONENT
WINDOW COMPONENT
DOOR COMPONENT
STRUCTURAL COMPONENT
INSTALLATION COMPONENT
```

Iedere categorie kan een eigen standaardset van aanzichten en detailniveaus hebben.

Een nieuwe productcategorie kan later worden toegevoegd zonder de basisarchitectuur te veranderen.

---

# 11. Productscope

Niet alle producten van een leverancier hoeven automatisch te worden opgenomen.

Per leverancier kan worden bepaald:

```text
INCLUDE
EXCLUDE
WATCH
```

Bijvoorbeeld:

```text
Rothoblaas

Schroeven             INCLUDE
Connectors             INCLUDE
Platen                 INCLUDE
Beugels                INCLUDE
Membranen              EXCLUDE
Gereedschap            EXCLUDE
PBM                    EXCLUDE
```

Daarnaast kan ook per productfamilie of productcode worden gefilterd.

Hierdoor blijft de bibliotheek beheersbaar.

---

# 12. Bestandsstructuur

De centrale structuur is:

```text
project-ocondat/                           <- de bibliotheekwortel
│
├── Manufacturer CAD-BIM Product Library - systeemomschrijving.md   <- dit document
│
├── 00_DATABASE/                           administratie
│   ├── products.csv
│   ├── assets.csv
│   ├── suppliers.csv
│   ├── dependencies.csv
│   ├── update-log.csv
│   └── manifests/                         per productlijn een JSON met afleidingsdetails
│
├── 01_SOURCE/                             READ-ONLY, alleen fabrikantsbestanden
│   └── <Leverancier>/                     bedrijfsbrochure, algemene catalogus
│       └── [<Productgroep>/]              alleen als er iets op dat niveau ligt
│           └── <Productlijn>/
│               ├── CAD/
│               ├── BIM/
│               └── DOCUMENTATION/         datasheet, ETA, montage-instructie
│
├── 02_EXTRACTEN/                          alles wat wij zelf genereren
│   ├── LEESMIJ.md                         overzicht + verwijzingen
│   ├── Extract DXF.md
│   ├── Extract SVG.md
│   ├── Extract RFA.md
│   └── <Leverancier>/<Productlijn>/
│       ├── dxf/                           genormaliseerd, invoegpunt op nul
│       ├── svg/                           1:1 in mm
│       └── rfa/                           Revit families
│
├── _TOOLS/                                generatorcode
│
├── 99_ARCHIVE/
│   └── YYYY-MM-DD/                        vervangen versies
│
└── DXF Library/                           de huidige, op bouwdeel ingedeelde mappen
```

### Drie soorten invoer

De indeling volgt niet de bewerkingsvolgorde maar de **herkomst** van een
bestand. Eén vraag bepaalt waar iets hoort: *kan ik dit weggooien en opnieuw
maken?*

| Map | Herkomst | Herbouwbaar |
|---|---|---|
| `01_SOURCE` | van buiten, van de fabrikant | nooit — read-only, back-up voor altijd |
| `02_EXTRACTEN` | door een script gemaakt | ja, volledig |
| `00_DATABASE` | door een mens ingevuld | nee — bevat beslissingen en historie |
| `_TOOLS` | code | via versiebeheer |

Daarom staat `00_DATABASE` **buiten** `02_EXTRACTEN`: `update-log.csv` is
geschiedenis, en `source_url`, `download_date` en beoordeelde statussen zijn
menselijke beslissingen. Eén opruimactie op de extracten zou die wissen.

**Regel: pas nooit met de hand iets aan in `02_EXTRACTEN`.** Alles daarin wordt
automatisch gegenereerd — DXF, SVG én RFA — en de volgende generatieslag
overschrijft handwerk geruisloos. Klopt er iets niet, pas dan de generator aan,
niet het bestand. De kwaliteitscontrole van §25 geldt daarmee de generator.

### Diepte

Een niveau bestaat pas als er iets op dat niveau ligt. Een bedrijfsbrochure
hoort bij de leverancier, een productgroepcatalogus bij de productgroep. Is er
alleen brondata per productlijn, dan valt de tussenlaag weg:

```text
01_SOURCE/Rothoblaas/                      bedrijfsbrochure
01_SOURCE/Rothoblaas/Screws/               alleen bij een schroeven-catalogus
01_SOURCE/Rothoblaas/HBS PLATE/CAD/        brondata van deze productlijn
```

Onder elke fase is het pad daarna identiek — `<leverancier>/<productlijn>/` —
zodat je van bron naar extract springt door alleen het eerste segment om te
wisselen.

### Waarom geen aparte 03_REVIT en 04_CATALOGUES meer

`03_REVIT` is opgegaan in `02_EXTRACTEN/.../rfa/`: een `.rfa` wordt automatisch
gegenereerd en is dus net zo herbouwbaar als een SVG. Een aparte tak zou
suggereren dat het handwerk is.

`04_CATALOGUES` is vervallen: catalogi en brochures zijn fabrikantsdocumenten en
horen in `01_SOURCE`, op het niveau waarop ze van toepassing zijn.

---

# 13. Productstructuur

Binnen de database wordt niet alleen het product opgeslagen, maar ook alle assets.

```text
SUPPLIER
    ↓
PRODUCT FAMILY
    ↓
PRODUCT
    ↓
VARIANT
    ↓
SOURCE ASSETS
    ↓
REPRESENTATIONS
    ↓
DERIVED ASSETS
```

Bijvoorbeeld:

```text
Rothoblaas
└── HBS EVO
    └── HBS EVO 8×120
        ├── front.dxf
        ├── side.dxf
        ├── top.dxf
        ├── product.rfa
        ├── product.ifc
        └── datasheet.pdf
```

---

# 14. Metadata

Iedere asset krijgt minimaal:

```text
asset_id
supplier_id
product_id
product_code
product_name
file_name
file_type
source_url
source_page
download_date
source_date
file_hash
representation_type
view_type
units
scale
status
derived_from
```

Voor Revit en SVG wordt ook vastgelegd van welke bronbestanden ze afhankelijk zijn.

---

# 15. Actualiteitschecker

Actualiteit wordt niet bepaald door alleen een datum.

De checker controleert meerdere bronnen:

### Product

* bestaat de productpagina nog?
* is het product actief?
* is er een opvolger?
* is het product vervangen?
* zijn productcodes gewijzigd?

### Assets

* bestaat het bestand nog?
* is de download-URL veranderd?
* is de bestandshash veranderd?
* is een nieuw bestand beschikbaar?

### Documentatie

* is de datasheet gewijzigd?
* zijn certificaten gewijzigd?
* zijn technische documenten gewijzigd?
* is de catalogusinformatie gewijzigd?

---

# 16. Hash/versionering

Van ieder bronbestand wordt een hash opgeslagen.

Bijvoorbeeld:

```text
HBS_FRONT.dxf

SHA-256:
A83F...91D2
```

Bij een volgende controle:

```text
A83F...91D2
A83F...91D2
        ↓
CURRENT
```

of:

```text
A83F...91D2
7B21...CC84
        ↓
UPDATED
```

Dit werkt ook wanneer de fabrikant dezelfde bestandsnaam en URL blijft gebruiken.

---

# 17. Statusmodel

De bibliotheek gebruikt minimaal:

```text
ACTIVE
NEW
UPDATED
REVIEW REQUIRED
REPLACED
DISCONTINUED
UNKNOWN
```

Een verdwenen downloadlink betekent bijvoorbeeld **niet automatisch DISCONTINUED**.

De checker probeert eerst vast te stellen of:

* de URL is veranderd;
* het bestand is vervangen;
* het product een nieuwe code heeft;
* de productpagina nog actief is.

Alleen wanneer voldoende bewijs aanwezig is, wordt een product als `DISCONTINUED` gemarkeerd.

---

# 18. Confidence level

Automatische statusbepaling krijgt een betrouwbaarheidsniveau.

Bijvoorbeeld:

```text
DISCONTINUED
Confidence: 98%

Productpagina verwijderd
+
fabrikant verwijst naar opvolger
+
oude documentatie gearchiveerd
```

Of:

```text
REVIEW REQUIRED
Confidence: 72%

Oude DXF verdwenen
maar productpagina bestaat nog.
```

Onzekere situaties worden dus aan een gebruiker voorgelegd.

---

# 19. Dependency tracking

Afgeleide bestanden worden gekoppeld aan hun bronnen.

Bijvoorbeeld:

```text
HBS_FRONT.dxf
      ↓
HBS_FRONT.svg
      ↓
HBS_2D.rfa
      ↓
PROJECT DETAIL
```

Wanneer `HBS_FRONT.dxf` verandert:

```text
DXF
 ↓
UPDATED
 ↓
SVG affected
 ↓
Revit Family affected
 ↓
Project detail affected
```

Hierdoor kan het systeem precies aangeven wat gecontroleerd moet worden.

---

# 20. Updateproces

Periodiek wordt automatisch gecontroleerd:

```text
SCHEDULED CHECK
       ↓
SUPPLIER
       ↓
PRODUCT DISCOVERY
       ↓
PRODUCT STATUS
       ↓
SOURCE ASSETS
       ↓
HASH / VERSION CHECK
       ↓
DOCUMENTATION CHECK
       ↓
DEPENDENCY CHECK
       ↓
UPDATE REPORT
```

Bijvoorbeeld:

```text
MANUFACTURER LIBRARY UPDATE

Nieuwe producten             4
Gewijzigde CAD-bestanden     7
Nieuwe RFA-bestanden         3
Gewijzigde documentatie      5
Vervangen producten          2
Uitgefaseerde producten      1

REVIEW REQUIRED              8
```

---

# 21. Automatische verwerking na een wijziging

Wanneer een DXF daadwerkelijk verandert:

```text
NEW DXF
  ↓
ARCHIVE OLD DXF
  ↓
VALIDATE
  ↓
NORMALISE
  ↓
GENERATE SVG
  ↓
COMPARE GEOMETRY
  ↓
FLAG DEPENDENCIES
  ↓
REVIT REVIEW
  ↓
APPROVE
```

Een gewijzigde fabrikantbron wordt dus **niet stilzwijgend in de definitieve bibliotheek gezet**.

---

# 22. Versiebeheer

Oude bronbestanden worden nooit zomaar verwijderd.

Bijvoorbeeld:

```text
99_ARCHIVE/
└── 2026-08-28/
    └── Rothoblaas/
        └── HBS_EVO_8x120/
            ├── front.dxf
            ├── side.dxf
            └── datasheet.pdf
```

Hiermee kan altijd worden vastgesteld:

> Welke fabrikantversie was beschikbaar toen een bepaald detail werd gemaakt?

---

# 23. Gebruik in PDF

De gebruiker kan een productrepresentatie selecteren:

```text
Product:
Rothoblaas HBS EVO 8×120

Representation:
SIDE

Output:
SVG

Scale:
1:10
```

De geometrie blijft technisch 1:1; de schaal wordt toegepast in de uiteindelijke tekening.

Dit maakt het geschikt voor:

* constructiedetails;
* werktekeningen;
* doorsneden;
* montage-details;
* principedetails;
* PDF-documentatie.

---

# 24. Gebruik in Revit

Voor ieder goedgekeurd product kan beschikbaar zijn:

```text
2D DETAIL FAMILY
2D SYMBOL FAMILY
3D BIM FAMILY
```

Niet ieder product hoeft alle drie te hebben.

Bijvoorbeeld:

```text
Schroef
├── 2D Detail ✓
├── Symbol ✓
└── 3D BIM ✓

Kanaalplaat
├── 2D Detail ✓
├── Symbol -
└── 3D BIM ✓

Beugel
├── 2D Detail ✓
├── Symbol ✓
└── 3D BIM -
```

---

# 25. Kwaliteitscontrole

Een bestand krijgt pas de status **APPROVED** na controle.

Controles kunnen bestaan uit:

* juiste eenheden;
* correcte schaal;
* correcte origin;
* geldige geometrie;
* geen corrupte CAD;
* geen ongewenste dubbele lijnen;
* correcte view-orientatie;
* correcte productcode;
* bronbestand aanwezig;
* juiste dependency;
* visuele controle;
* vergelijking met fabrikantdocumentatie.

### Concrete controles die zich bewezen hebben

Deze vier zijn goedkoop en hebben in de praktijk fouten gevonden die de cijfers
alleen niet lieten zien:

1. **Tel de paden.** De som over alle extracten moet gelijk zijn aan het aantal
   geometrie-entiteiten in de bron, zonder tekstlabels. Bij HBS PLATE:
   4899 = 4917 − 18. Klopt dat niet, dan is er iets dubbel of kwijt.
2. **Render het resultaat terug, niet de brondata.** Alleen dan test je ook de
   omzetting zelf. Een omgeklapte boog is in cijfers onzichtbaar.
3. **Reken de hoofdmaten na.** Een extract van een 8×60 moet 64,500 × 13,500 mm
   meten, met de punt exact op x = 60. Twee keer is hier een fout van 0,25 mm
   uit gekomen die er visueel volkomen normaal uitzag.
4. **Controleer de kortste curve** tegen de doeltolerantie van het formaat.

**Visuele controle is niet optioneel.** Bij het opbouwen van de eerste set zijn
twee bewerkingen weggegooid nadat de getallen goed leken maar het beeld het
tegendeel liet zien: één waarbij alle draadtanden waren ingestort, en één die
van een boogje van een halve millimeter een cirkel van 20 mm maakte. Beide
zouden ongemerkt in de families zijn beland.

---

# 26. Eindresultaat

Het eindproduct is geen verzameling losse DWG's, SVG's en Revit-files, maar een **gecontroleerde productdatabase met traceerbare relaties**.

De kernstructuur is:

```text
                    SUPPLIER
                       │
                       ↓
                  PRODUCT
                       │
                       ↓
                  VARIANTS
                       │
             ┌─────────┼─────────┐
             ↓         ↓         ↓
            CAD       BIM      DOCUMENT
             │         │         │
       ┌─────┼─────┐   │         │
       ↓     ↓     ↓   │         │
     FRONT  SIDE  TOP  RFA      PDF
       │     │     │   IFC      ETA
       └─────┼─────┘   │         │
             ↓         │         │
            SVG        │         │
             │         │         │
             └────┬────┘         │
                  ↓              │
             REVIT 2D            │
                  │              │
                  └──────┬───────┘
                         ↓
                  UPDATE ENGINE
                         ↓
              CURRENT / UPDATED /
              REPLACED / DISCONTINUED
```

## Kernprincipes

**1. De fabrikantbron blijft altijd behouden.**

**2. Een product kan meerdere bronbestanden hebben.**

**3. Iedere DXF/DWG-representatie wordt zelfstandig beheerd.**

**4. Fabrikant-2D blijft leidend voor 2D-detailwerk.**

**5. IFC/RFA worden niet automatisch gezien als vervanging van 2D-CAD.**

**6. SVG is een afgeleid vectorformaat.**

**7. Revit 2D is een gecontroleerde afgeleide van de beste 2D-bron.**

**8. Producten kunnen meerdere aanzichten en representaties hebben.**

**9. De architectuur is onafhankelijk van leverancier en producttype.**

**10. Niet alle producten van een leverancier hoeven te worden opgenomen.**

**11. Iedere bron en afgeleide heeft versie- en hashinformatie.**

**12. Wijzigingen veroorzaken automatisch een dependency-check.**

**13. Een product wordt nooit alleen op basis van een verdwenen URL als uitgefaseerd beschouwd.**

**14. Onzekere wijzigingen krijgen `REVIEW REQUIRED`.**

**15. Oude versies blijven beschikbaar voor traceerbaarheid.**

---

## Beoogde eerste implementatie

De eerste praktische implementatie wordt daarom:

**Fase 1:** generieke database + leveranciersstructuur
**Fase 2:** Rothoblaas als eerste leverancier
**Fase 3:** alleen de door jou gewenste Rothoblaas-productgroepen
**Fase 4:** download van alle beschikbare officiële assets per geselecteerd product
**Fase 5:** DXF/DWG-validatie en → SVG-conversie
**Fase 6:** representation/view-management
**Fase 7:** Revit 2D workflow
**Fase 8:** versie-, hash- en dependency-management
**Fase 9:** automatische actualiteitschecker
**Fase 10:** tweede leverancier toevoegen om te bewijzen dat het systeem daadwerkelijk leverancier-onafhankelijk is.

Het einddoel is daarmee een **actuele, gecontroleerde en herleidbare technische productbibliotheek** die dezelfde fabrikantdata kan ontsluiten naar **CAD, SVG, PDF en Revit**, zonder de verschillende bronrepresentaties van een product door elkaar te halen.

---

# Verwante documenten

| Document | Waarvoor |
|---|---|
| dit document | architectuur, metadata, versiebeheer, statusmodel — **leidend** |
| [Bibliotheek opbouwen - werkwijze](Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md) | de bewerkingsstappen van bron naar extract |
| [02_EXTRACTEN/LEESMIJ](02_EXTRACTEN/LEESMIJ.md) | overzicht van de extracttypen |
| [Extract DXF](02_EXTRACTEN/Extract%20DXF.md) | genormaliseerde CAD per product |
| [Extract SVG](02_EXTRACTEN/Extract%20SVG.md) | vectorbestand 1:1 voor PDF en documentatie |
| [Extract RFA](02_EXTRACTEN/Extract%20RFA.md) | Revit detailcomponenten |

---

# Besluiten

Wijzigingen op de oorspronkelijke opzet, met de reden erbij.

### 28-08-2026 · `02_PROCESSED` → `02_EXTRACTEN`

"Extracten" is de term die in huis gebruikt wordt. Strikt genomen dekt het woord
alleen het uitknippen en niet de formaatomzetting — het document gebruikt
elders "afgeleide" — maar consistentie met het spraakgebruik weegt zwaarder.

### 28-08-2026 · `03_REVIT` en `04_CATALOGUES` opgeheven

De `.rfa` wordt automatisch gegenereerd en is dus een extract als elk ander.
Catalogi horen bij de fabrikant en dus in `01_SOURCE`, op het niveau waarop ze
gelden.

### 28-08-2026 · `00_DATABASE` blijft buiten de extracten

Het bevat menselijke beslissingen en historie die geen script terug kan maken.

### 28-08-2026 · Diepte volgt inhoud

Een mapniveau bestaat pas als er iets op dat niveau ligt. Voorkomt lege
tussenlagen bij leveranciers met één productlijn.

### 28-08-2026 · Eén Revit-familie met types, geometrie genest

Een Revit-type varieert parameters, geen lijnwerk — en bij HBS PLATE loopt het
aantal draadtanden van 10 naar 33. Er is bewust gekozen voor **één familie met
18 types waarin de 18 productfamilies genest zijn**, elk met een
zichtbaarheidsparameter.

De prijs is bekend en geaccepteerd: alle geometrie zit in één bestand, en elk
project dat één schroef plaatst laadt alle achttien mee. Het alternatief —
parametrisch hertekenen — is afgewezen omdat het lijnwerk dan niet meer dat van
de fabrikant is, tegen §3 in.

Nesten in plaats van 4921 losse detaillijnen zichtbaar schakelen scheelt
**18 koppelingen in plaats van 4921** en houdt de geometrie per product
herleidbaar.

### 28-08-2026 · Kopaanzicht als tweede representation

Het kopaanzicht (`view_type: top`) is toegevoegd voor D8, D10 en D12 als dxf,
svg en rfa, en als drie extra types in de verzamelfamilie. **Drie stuks voor
achttien producten**: de kop is gelijk voor alle lengtes van een diameter.

Daarmee heeft een representation een eigen granulariteit, los van het product —
`side` is per product, `top` per diameter. In `assets.csv` staan die
kopaanzichten daarom zonder `product_id`; de koppeling loopt via `product_code`
en `view_type`.

De letters in de kop zijn stempeling op het product, geen bladannotatie. Ze
gaan mee in dxf en svg maar niet in de rfa, omdat Revit-tekst papiergebonden is.

### 28-08-2026 · Familienaamgeving volgens de NLRS

De verzamelfamilie volgt de NLRS-conventie: onderdelen gescheiden door
underscores, van groot naar klein.

```text
NLRS_28_DI_UN_schroef_HBS-PLATE_Rothoblaas_bluetek
  1   2  3  4         5             6         7
```

| Pos | Betekenis | Waarde | Herkomst |
|---|---|---|---|
| 1 | standaard | `NLRS` | conventie |
| 2 | NL-SfB hoofdgroep | `28` | opgegeven |
| 3 | Revit-categorie | `DI` (Detail Item) | opgegeven |
| 4 | plaatsingscodering | `UN` | bevestigd |
| 5 | omschrijving | `schroef_HBS-PLATE` | opgegeven |
| 6 | fabrikant | `Rothoblaas` | |
| 7 | contentprovider | `bluetek` | opgegeven |

**Alleen de verzamelfamilie krijgt deze naam.** De 21 geneste families houden
hun productcode; het zijn bouwstenen, geen zelfstandige bibliotheekfamilies.

**Typenamen dragen de productaanduiding**: `HBSPL860 - 8x60`, `kop D8`. Dat is
de tekst zoals de fabrikant hem op de tekening zet, en hij leest in de
typekeuzelijst prettiger dan een kale code — je ziet meteen welke maat je pakt.
De NLRS-conventie geldt voor de familienaam, niet voor de typenaam.

### 28-08-2026 · Documentatie extern, niet lokaal

Datasheets, ETA's en catalogi worden **als URL in de database geregistreerd**,
niet als bestand in `01_SOURCE`. Een documentasset heeft een lege `file_path` en
een gevulde `source_url` plus `source_page`.

Dat scheelt beheer en voorkomt dat de bibliotheek volloopt met PDF's, maar het
heeft twee gevolgen die aandacht vragen:

* **§15 kan niet meer vaststellen of de datasheet gewijzigd is.** Die controle
  berust op een hash, en zonder opgehaald bestand is er niets om te hashen.
* **§22 verliest de traceerbaarheid voor documentatie.** De vraag "welke
  fabrikantversie was beschikbaar toen dit detail gemaakt werd" is voor
  tekeningen wel te beantwoorden en voor documenten niet meer.

Beide zijn op te lossen zonder het document lokaal te bewaren: laat de
actualiteitschecker de URL ophalen, alleen de **hash** vastleggen in
`file_hash`, en het bestand weggooien. Dan werkt wijzigingsdetectie wel en blijft
de map leeg. Zolang dat niet is ingebouwd staat `file_hash` bij documentassets
leeg en is dat een bewust gat.

### 28-08-2026 · De database wordt verzoend, niet bijgehouden

`_TOOLS/registreer.py` sluit de pipeline: hij loopt `01_SOURCE` en
`02_EXTRACTEN` af, hasht elk bestand, vult ontbrekende regels in `assets.csv`
aan en leidt `dependencies.csv` af uit de conventie
(`bron → dxf/svg`, `dxf → rfa`, `rfa → verzamelfamilie`).

Het is bewust een **verzoener** en geen bijhouder: hij vergelijkt de schijf met
de database en meldt het verschil. Menselijke velden blijven staan, niets wordt
verzonnen, en een vermist bestand wordt gemeld maar niet verwijderd.

Getoetst tegen de bestaande set: 65 bestanden, 0 nieuw, 0 hashes gewijzigd, en
84 afgeleide afhankelijkheden — precies de 84 die er met de hand in stonden.
Daarmee reproduceert het script de handmatige registratie onafhankelijk.

### Open

* **`products.csv` blijft handwerk.** `registreer.py` vult assets en
  dependencies, maar productgegevens — maten, drive, ETA — komen uit de tekening
  en de datasheet en niet uit het bestandssysteem. Een script kan ze niet
  afleiden en hoort ze niet te verzinnen.
* **`dependencies.csv` wordt volledig opnieuw afgeleid** bij elke registratie.
  Met de hand toegevoegde toelichtingen daarin gaan verloren.
* **Hash van externe documenten.** Zie het besluit hierboven: zolang de checker
  de URL niet ophaalt, kan §15 een gewijzigde datasheet niet zien.
* Het bronbestand heeft nu een `source_page` (de productpagina), maar de
  **directe downloadlink van de CAD-bestanden** en de `download_date` ontbreken
  nog.
* Alle assets staan op `REVIEW REQUIRED`. Van §25 resteert de vergelijking met
  de fabrikantdocumentatie; daarvoor is de datasheet of ETA nodig.
* De bron bevat **135 nul-lange lijnen** — een kwaliteitsgebrek in het
  fabrikantsbestand zelf, niet in onze verwerking.
