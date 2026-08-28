# Voorstel · de bibliotheek indelen op herkomst

> **English summary.** This proposal reorganises the library from a
> building-element hierarchy (`DXF Library/001 Vloeren`, `002 Aluminium
> kozijnen`, …) into four folders defined by *where a file comes from*:
> manufacturer source, generated extract, human-maintained administration, and
> archive. It brings the architecture document, the working method, and three
> Python generators. **This pull request moves and deletes nothing** — the
> existing `DXF Library/` is left untouched; only new folders are added
> alongside it.

---

## Waar het project voor is

Dit staat nergens in de repo, en het is de eerste vraag die een bezoeker stelt.
De README noemt drie features maar geen doel. Het voorstel begint daarom hier,
en niet bij mappen — de indeling is een gevolg, geen uitgangspunt.

> Het doel is een **leveranciersonafhankelijke productbibliotheek** op te
> bouwen waarin technische producten van verschillende fabrikanten centraal
> worden beheerd en gecontroleerd.

De bibliotheek moet het mogelijk maken om fabrikantbestanden centraal te
verzamelen, versieerbaar en traceerbaar op te slaan, op actualiteit te
controleren, als 2D-vectorbestand te hergebruiken, op schaal in PDF-tekeningen
toe te passen, als 2D Revit Family te gebruiken, eventueel als 3D BIM-object te
gebruiken, en **automatisch te signaleren wanneer een product of bronbestand is
gewijzigd, vervangen of uitgefaseerd**.

Twee uitgangspunten bepalen daarna de hele architectuur:

**Eén product is niet één CAD-bestand.** Een fabrikant kan voor hetzelfde
artikel meerdere DXF-aanzichten leveren, plus een RFA, een IFC, een STEP-model,
een datasheet en een montage-instructie. Elk daarvan is een eigen source asset,
en geen ervan vervangt stilzwijgend een ander. Een vereenvoudigd IFC mag nooit
een fabrikant-DXF overrulen voor 2D-detailwerk.

**Het fabrikantsbestand is de bron, alles wat wij maken is afgeleid.** Een SVG
of een Revit-family draagt de hash van het bestand waar hij uit komt. Daardoor is
een gewijzigd fabrikantsbestand te detecteren — ook als naam en URL gelijk
blijven — en is te bepalen wat er stroomafwaarts opnieuw beoordeeld moet worden.

Rothoblaas is de eerste leverancier waarop dit is toegepast, maar de architectuur
is niet specifiek voor Rothoblaas. Würth, Fischer, Hilti, Leviat, Schöck,
staalproducenten en plaatleveranciers moeten in hetzelfde model passen; elke
leverancier krijgt een eigen bronconfiguratie voor de formaten die hij werkelijk
levert.

De volledige uitwerking staat in §1 t/m §11 van de
[systeemomschrijving](Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md).
In deze PR is dat doel ook in de [README](README.md) gezet, zodat het niet
alleen in een bijlage staat.

---

## 1. Waar het om gaat

De bibliotheek is nu ingedeeld op **bouwdeel**: `001 Vloeren`,
`002 Aluminium kozijnen`, `003 Kunststeen onderdorpel`, en zo verder. Dat werkt
zolang je zoekt, maar het beantwoordt de vraag niet die er bij beheer toe doet:

> Mag ik dit bestand weggooien, of is het onvervangbaar?

In de huidige indeling kunnen een fabrikants-DWG, een door ons opgeschoonde
versie en een handmatig ingevulde maattabel naast elkaar in dezelfde map staan,
zonder dat je aan het pad ziet welke van de drie het is. Dat maakt drie dingen
lastig:

* je kunt niet veilig opruimen — je weet niet wat herbouwbaar is;
* je kunt niet zien of iets nog actueel is — er is geen plek voor bronversie,
  hash of downloaddatum;
* je kunt niet automatiseren — een generator heeft een vaste bron- en doelmap
  nodig, en die is er niet.

**Het voorstel is om te herindelen op herkomst.** Eén vraag bepaalt waar een
bestand hoort: *waar komt het vandaan?*

| Map | Herkomst | Herbouwbaar |
|---|---|---|
| `01_SOURCE` | van buiten, van de fabrikant | nooit — read-only, bewaren voor altijd |
| `02_EXTRACTEN` | door een script gemaakt | ja, volledig — mag in zijn geheel weg |
| `00_DATABASE` | door een mens ingevuld | nee — beslissingen en historie |
| `_TOOLS` | code | via versiebeheer |
| `99_ARCHIVE` | vervangen versies, per datum | nee — traceerbaarheid |

Het bouwdeel verdwijnt daarmee niet; het verhuist van het **pad** naar de
**database** (`category` in `products.csv`). Daar kan het naast NL-SfB,
leverancier en productlijn staan, en kun je erop filteren zonder bestanden te
verplaatsen.

## 2. Wat dat oplevert

**Alles onder `02_EXTRACTEN` is automatisch te maken.** DXF, SVG én RFA. De
regel die daarbij hoort is hard: *pas nooit met de hand iets aan in
`02_EXTRACTEN`* — de volgende generatieslag overschrijft handwerk geruisloos.
Klopt er iets niet, dan pas je de generator aan. De kwaliteitscontrole geldt
daarmee de generator, niet het losse bestand.

**De keten is expliciet.** SVG en DXF komen allebei rechtstreeks uit de bron,
de RFA komt uit de DXF:

```text
01_SOURCE/…/CAD/bron.dxf
        ├──> dxf/<code>.dxf ──> rfa/<code>.rfa
        └──> svg/<code>.svg
```

**Actualiteit wordt controleerbaar.** Van elk bronbestand ligt een SHA-256 vast
in `assets.csv`, met `source_url`, `source_page` en `download_date`. Verandert
de fabrikant het bestand achter dezelfde naam en URL, dan ziet de checker dat
aan de hash. Via `dependencies.csv` volgt daarna wat er opnieuw beoordeeld moet
worden.

**Het pad is voorspelbaar.** Onder `01_SOURCE` en `02_EXTRACTEN` is het pad na
het eerste segment identiek — `<Leverancier>/<Productlijn>/` — zodat je van
bron naar extract springt door alleen dat eerste segment om te wisselen.

## 3. Wat er in deze pull request zit

Documentatie, administratie en generatorcode. **Geen bestanden verplaatst, geen
bestanden verwijderd.**

| Pad | Wat |
|---|---|
| `README.md` | **gewijzigd** — het doel uit §1 van de systeemomschrijving is aan de bestaande README toegevoegd, plus de mappentabel en verwijzingen. De bestaande regels en de features-lijst zijn ongemoeid gelaten |
| `VOORSTEL.md` | dit document |
| `Manufacturer CAD-BIM Product Library - systeemomschrijving.md` | de architectuur: mappen, metadata, statusmodel, actualiteitschecker, versiebeheer — **leidend document** |
| `Ocondat bibliotheek instructie/Bibliotheek opbouwen - werkwijze.md` | de bewerkingsstappen van fabrikantstekening naar extract, met de valkuilen die we echt zijn tegengekomen |
| `02_EXTRACTEN/LEESMIJ.md` | overzicht van de drie extracttypen en de keten ertussen |
| `02_EXTRACTEN/Extract DXF.md` | genormaliseerde CAD per product, invoegpunt op nul, `$INSUNITS = 4` |
| `02_EXTRACTEN/Extract SVG.md` | vector 1:1 in mm, bogen als echte `A`-segmenten |
| `02_EXTRACTEN/Extract RFA.md` | Revit detailcomponenten, inclusief de curve-opschoning die Revit afdwingt |
| `_TOOLS/` | negen generators plus een [LEESMIJ](_TOOLS/LEESMIJ.md) die de volgorde beschrijft: `blad_naar_dxf` / `blad_naar_svg` / `blokken_naar_extract` splitsen het bronblad, `curveclean` + `rfa_opdrachten` schonen de geometrie op tot boven de Revit-tolerantie, `revit_bouw` bouwt de families binnen Revit, `registreer` verzoent de database met de schijf, en twee `openpdfstudio_*`-exporters staan los van die keten |
| `00_DATABASE/*.csv` + `manifests/` | de administratie, ingevuld met de Rothoblaas HBS PLATE-pilot als werkend voorbeeld |

### Wat er bewust níet in zit

* **Geen fabrikantsbestanden.** `01_SOURCE` is in deze PR leeg. De vraag of
  fabrikants-CAD op een publieke repo gepubliceerd mag worden is een aparte
  beslissing — zie §6.
* **Geen extracten.** `02_EXTRACTEN` bevat alleen de instructiedocumenten. De
  18 SVG's, 18 DXF's en 21 RFA's van de pilot (samen circa 15 MB) zijn
  achtergehouden om de repo licht te houden; ze zijn met de generators opnieuw
  te maken.
* **De rijen in `00_DATABASE` verwijzen daardoor naar bestanden die hier niet
  staan.** Dat is expliciet: ze zijn meegestuurd om te laten zien hoe de
  administratie eruitziet als hij gevuld is, niet als losse dataset.

## 4. Hoe de huidige inhoud erop past

`DXF Library/` blijft staan. De migratie is stapsgewijs en per productlijn te
doen; er hoeft niets in één keer om.

| Nu | Straks |
|---|---|
| `DXF Library/Downloads/ArcelorMittal/IPE_dwg/` | `01_SOURCE/ArcelorMittal/IPE/CAD/` — onbewerkte fabrikantsdownload |
| `DXF Library/001 Vloeren/Kanaalplaatvloer/` | `02_EXTRACTEN/<leverancier>/Kanaalplaatvloer/dxf/`, met `category = SLAB` in `products.csv` |
| `DXF Library/Componenten/28 Staalconstructie/` | idem; de NL-SfB-code `28` verhuist naar een kolom |
| `steelprofile.json`, `Ocondat.py` | blijven waar ze zijn — dit zijn geen CAD-assets |
| `Standards/`, `Libraries/`, `BlenderBIM/` | ongemoeid; het voorstel gaat over de CAD/BIM-assets |

Per productlijn is de volgorde: bron terugvinden en in `01_SOURCE` zetten →
hash en herkomst in `assets.csv` → generator draaien → oude map naar
`99_ARCHIVE/<datum>/`. Zolang een bron niet terug te vinden is, blijft de
bestaande map staan en noteer je dat expliciet — **een reconstructie is geen
bron.**

## 5. Status van de pilot

| Fabrikant | Productlijn | Producten | Bron | DXF | SVG | RFA | Database |
|---|---|---|---|---|---|---|---|
| Rothoblaas | HBS PLATE | 18 | ✔ | ✔ | ✔ | ✔ | ✔ |

Alle assets staan op `REVIEW REQUIRED`, niet op `APPROVED`. Wat daarvoor nog
ontbreekt staat in de werkwijze-instructie: de vergelijking met de
fabrikantdocumentatie, en de directe downloadlink plus `download_date` van het
bronbestand.

## 6. Te beslissen

1. **Mag fabrikants-CAD publiek?** `01_SOURCE` is per definitie materiaal van
   derden. De repo bevat al `DXF Library/Downloads/ArcelorMittal/`, dus in de
   praktijk gebeurt het al — maar als de bibliotheek groeit is het de moeite
   waard dit een keer expliciet vast te leggen, per leverancier, in
   `suppliers.csv`.
2. **Repo-grootte.** Gegenereerde extracten horen strikt genomen niet in
   versiebeheer: ze zijn herbouwbaar. De 21 RFA's van één productlijn zijn al
   12 MB. Alternatief is ze in `.gitignore` zetten en via een release-asset of
   Git LFS te leveren.
3. **Taal.** Deze documenten zijn Nederlands. Voor een repo onder de OpenAEC
   Foundation is Engels waarschijnlijk logischer; ze zijn te vertalen als dat
   het voorstel wordt.

## 7. Verwante documenten

| Document | Waarvoor |
|---|---|
| [Systeemomschrijving](Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) | architectuur, metadata, versiebeheer, statusmodel — **leidend** |
| [Bibliotheek opbouwen · werkwijze](Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md) | de stappen van bron naar extract |
| [02_EXTRACTEN/LEESMIJ](02_EXTRACTEN/LEESMIJ.md) | overzicht van de extracttypen |
