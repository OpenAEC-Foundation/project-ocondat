# Oconda bibliotheek — werkwijze

Hoe je van een fabrikantstekening een set herbruikbare extracten maakt: SVG's
voor documentatie, DXF's voor Revit-detailcomponenten, en een JSON met de
productgegevens.

Geschreven op 28-08-2026, naar aanleiding van de eerste set: Rothoblaas
HBS PLATE, 18 schroeven.

> **Dit document beschrijft de bewerkingsstappen, niet de architectuur.**
> Leidend voor mappen, metadata, versiebeheer en statusmodel is
> `Manufacturer CAD-BIM Product Library - systeemomschrijving.md` in de
> hoofdmap.

---

## 1. Mappenstructuur

```
project-ocondat\
  Manufacturer CAD-BIM Product Library - systeemomschrijving.md
  Ocondat bibliotheek instructie\      <- dit document
  00_DATABASE\      administratie: products, assets, suppliers, dependencies,
                    update-log, manifests
  01_SOURCE\        fabrikantsbestanden, READ-ONLY
  02_EXTRACTEN\     alles wat wij zelf genereren
  99_ARCHIVE\       YYYY-MM-DD\ vervangen versies
  DXF Library\      de huidige, op bouwdeel ingedeelde mappen
```

### Drie soorten invoer

De indeling volgt niet de bewerkingsvolgorde maar de **herkomst** van een
bestand. Eén vraag bepaalt waar iets hoort:

| Map | Herkomst | Weggooien? |
|---|---|---|
| `01_SOURCE` | van buiten, van de fabrikant | nooit |
| `02_EXTRACTEN` | door een script gemaakt | mag altijd, wordt opnieuw gemaakt |
| `00_DATABASE` | door een mens ingevuld | nooit, bevat beslissingen en historie |

**Regel: pas nooit met de hand iets aan in `02_EXTRACTEN`.** Alles daarin —
SVG, DXF, en straks ook de `.rfa` — wordt automatisch gegenereerd, en de
volgende generatieslag overschrijft handwerk geruisloos. Klopt er iets niet,
pas dan de generator aan, niet het bestand. De kwaliteitscontrole van §25 geldt
daarmee de generator, niet het losse bestand.

### Diepte in 01_SOURCE

Een niveau bestaat pas als er iets op dat niveau ligt. Een bedrijfsbrochure
hoort bij de leverancier, een productgroepcatalogus bij de productgroep:

```
01_SOURCE\Rothoblaas\                      <- bedrijfsbrochure, algemene catalogus
01_SOURCE\Rothoblaas\Screws\               <- alleen als er een schroeven-catalogus is
01_SOURCE\Rothoblaas\HBS PLATE\CAD\        <- brondata van deze productlijn
01_SOURCE\Rothoblaas\HBS PLATE\DOCUMENTATION\   <- datasheet, ETA, montage
```

Is er alleen brondata en documentatie per productlijn, dan valt de
tussenlaag weg en krijg je direct `01_SOURCE\Rothoblaas\HBS PLATE\`. Zo staat
het nu: Rothoblaas heeft nog geen brochures in de bibliotheek, dus er is geen
`Screws\`-niveau.

### Diepte in 02_EXTRACTEN

Onder elke fase hetzelfde pad, zodat je van bron naar extract springt door
alleen het eerste segment om te wisselen:

```
02_EXTRACTEN\Rothoblaas\HBS PLATE\dxf\     genormaliseerd, invoegpunt op nul
02_EXTRACTEN\Rothoblaas\HBS PLATE\svg\     1:1 in mm
02_EXTRACTEN\Rothoblaas\HBS PLATE\rfa\     Revit families, automatisch gegenereerd
```

### Naamgeving

Bestandsnaam = de producttekst zoals die in de tekening staat, ongewijzigd.
Bijvoorbeeld `HBSPL860 - 8x60.svg`. Zo blijft het spoor naar de bron kort en
hoef je geen vertaaltabel bij te houden. Windows-verboden tekens vervang je
door een streepje.

---

## 2. Werkwijze

### Stap 1 — Bron binnenhalen

Zet het onbewerkte fabrikantsbestand in `bron\`. Bewerk het niet. Heb je het
niet, noteer dat expliciet: een reconstructie is geen bron (zie §4).

### Stap 2 — Openen en selecteren

Open de tekening in Open CAD Studio en selecteer de producten die je wil
extraheren. Klik één keer op **Connect** in het tabblad MCP Bridge als de
verbinding nog niet staat.

Controleer met `ocs_live_layers` of je krijgt wat je verwacht:

- Klopt het aantal geselecteerde handles?
- Zijn de laagnamen herkenbaar voor *deze* tekening?

Die tweede vraag is geen formaliteit. Zie §4, valkuil 1.

### Stap 3 — Eenheid vaststellen — niet overslaan

Haal `insertion_units` op uit het levende document. **4 = millimeter.** Is de
waarde 0, dan legt de tekening geen eenheid vast en moet je hem afleiden uit een
bekende maat: een productaanduiding als "8x60" tegen de gemeten geometrie. Leg
vast wat je gedaan hebt.

Zonder deze stap staat alles wat je maakt mogelijk een factor mis.

### Stap 4 — Geometrie ophalen

Via de MCP Bridge, niet via een bestand. Haal bij grote selecties de entiteiten
niet stuk voor stuk door de tool, maar in één keer, en cache het resultaat als
JSON zodat je verderop niet opnieuw hoeft op te halen.

Blokreferenties worden serverkant uitgeklapt (plugin 0.7.0 en hoger). Je hoeft
in de GUI niets te exploden.

### Stap 5 — Opsplitsen in producten

Producten staan meestal als losse eilandjes op één blad. Groepeer met union-find
over de bounding boxes: alles binnen T mm van elkaar hoort bij elkaar.

Twee dingen die ertoe doen:

1. **Bereken boog-bounding boxes exact.** De volledige cirkel als bbox nemen
   blaast ze zo ver op dat losse producten aan elkaar plakken. Neem de begin- en
   eindpunten plus de asuitersten die binnen de doorlopen hoek vallen.
2. **Controleer dat T op een plateau ligt.** Draai een reeks waarden en kijk waar
   het aantal groepen stabiel blijft. Bij HBS PLATE gaf T = 1 t/m 8 mm steeds 18
   groepen; pas bij 12 mm liep het vast. Zit je antwoord op een smalle piek, dan
   klopt er iets niet.

### Stap 6 — Labels koppelen: op geometrie, niet op afstand

Koppel elk product aan zijn tekstlabel via **afmetingen**, niet via het
dichtstbijzijnde label. Bij HBS PLATE gaf afstand-koppeling 14 unieke namen op
18 groepen: de lange schroeven kwamen dichter bij het label van de buurrij.

De werkwijze die wel klopt:

1. Groepeer de producten op hoogte van het aanzicht — dat is hier de kopdiameter,
   en daarmee de kolom.
2. Groepeer de labels op de diameter uit de tekst.
3. Sorteer beide oplopend en koppel op volgorde.

**En controleer jezelf:** breedte minus nominale lengte moet binnen één diameter
constant zijn. Bij HBS PLATE is dat 4,5 / 5,0 / 5,5 mm — de kopdikte. Was de
koppeling ook maar één rij verschoven, dan had die reeks gevarieerd. Deze
controle is het hart van de stap; sla hem niet over.

### Stap 7 — SVG schrijven

Per product één bestand:

- `width` en `height` in **mm**, `viewBox` in dezelfde eenheid, zodat de schaal
  1:1 is
- Marge van 0,25 mm rondom, verrekend in zowel viewBox als mm-maat, zodat de
  lijndikte niet afgekapt wordt en de schaal zuiver blijft
- Bogen als echte `A`-segmenten, geen polygoonbenadering
- Polylijn-bulges omrekenen: hoek = 4·atan(bulge), straal = koorde / (2·sin(hoek/2))
- Y spiegelen, want DXF telt omhoog en SVG omlaag — **en daarmee de sweep-vlag
  omkeren**: tegen de klok in wordt 0, met de klok mee wordt 1
- Lagen behouden als `<g id="laagnaam">`
- `fill="none"`, `stroke-width` 0,12 mm
- Producttekst niet in de SVG zetten: die hoort bij het blad, niet bij het
  product. Zet hem in `<title>` en in de bestandsnaam.

### Stap 8 — Genormaliseerde DXF schrijven

DXF is een zelfstandig uitvoerformaat, geen Revit-tussenbestand. Het staat naast
`svg\` en `rfa\` in dezelfde extractenmap, niet erboven.

Per product één DXF in `dxf\`:

- **`$INSUNITS = 4`** (mm). Zet dit expliciet. Revit leest het, en een verkeerde
  of ontbrekende waarde geeft een factorfout bij import.
- **Invoegpunt op onderkant kop, op de hartlijn.** Verschuif de geometrie zo dat
  de kop van `-kopdikte` tot `0` loopt, de punt op `x = lengte onder kop` ligt en
  de hartlijn op `y = 0`.
- Lagen behouden, geen tekst.

Waarom dit invoegpunt: bij het plaatsen in een detail zet je een schroef op het
vlak waar de kop landt. Dan is dat punt het handigste greeppunt, en ligt de punt
op een voorspelbare, uitrekenbare coördinaat.

### Stap 9 — producten.json

Per product minimaal: code, aanduiding, draaddiameter, lengte onder kop,
kopdiameter, kopdikte, totale lengte, en de paden naar de SVG en de DXF.

Op documentniveau: fabrikant, productlijn, eenheid, datum, en een `herkomst`-blok
dat vastlegt hoe de maten zijn afgeleid.

**Verzin geen productgegevens.** Karakteristieke draagkracht, ETA-nummers,
voorboormaten, materiaal en coating staan niet in de tekening. Neem ze niet op
tenzij je ze uit de ETA of de fabrikantsdocumentatie haalt, en noteer in
`niet_inbegrepen` wat er ontbreekt.

### Stap 10 — Controleren

Drie controles, alle drie goedkoop:

1. **Tel de paden.** De som van alle gerenderde paden over alle SVG's moet gelijk
   zijn aan het aantal geometrie-entiteiten, dus zonder de tekstlabels. Bij
   HBS PLATE: 4899 = 4917 − 18. Klopt dit niet, dan is er iets dubbel of kwijt.
2. **Render een contactblad.** Render de weggeschreven SVG's terug, niet de
   brondata. Alleen zo test je ook de `A`-vlaggen. Een omgeklapte boog zie je in
   cijfers niet.
3. **Controleer de extents van een paar DXF-extracten.** `x` moet van
   `-kopdikte` tot de nominale lengte lopen, `y` symmetrisch om nul.

---

## 3. Van DXF naar detailcomponent

**Dit moet een generator worden, geen handwerk.** De `.rfa` hoort bij de
extracten en moet dus net zo goed opnieuw te maken zijn als de SVG. Zolang
iemand hem met de hand maakt, is de map `rfa\` een uitzondering op de regel uit
§1 — en uitzonderingen op die regel breken het hele model.

Wat de generator moet doen, per product:

1. Nieuwe familie op basis van `Detailitem.rft` (metrisch).
2. De DXF uit `dxf\` inlezen. Eenheid millimeter, oorsprong op oorsprong: het
   invoegpunt uit stap 8 valt dan samen met de familie-oorsprong.
3. De geometrie omzetten naar **detaillijnen**, niet als CAD-import laten staan.
   Een geïmporteerde CAD-laag sleept lagen en lijntypes mee die je later niet
   meer kwijtraakt.
4. Metadata meegeven zoals §7 van de systeemomschrijving voorschrijft:
   leverancier, productcode, productnaam, gebruikte bronbestanden, bronversie,
   controledatum, bibliotheekstatus.
5. Opslaan als `<code>.rfa`, bijvoorbeeld `HBSPL860.rfa`.

Revit is via de `revit-mcp-python` MCP-server aanstuurbaar, dus dit is
programmatisch haalbaar.

**De volledige uitwerking staat in
[Extract RFA.md](../02_EXTRACTEN/Extract%20RFA.md)** — inclusief de
schoonmaakstap die nodig is omdat Revit curves onder 0,78 mm weigert, en de
valkuilen bij het aansturen van Revit.

---

## 4. Valkuilen die we echt zijn tegengekomen

**1. De brug kan een verouderde documentsnapshot vasthouden.**
Bij een tekening met lagen `0` en `_RB_product` kwamen entiteiten terug op de
lagen `KOZIJN` en `LATTEN` — uit een heel andere tekening. Handles zijn
oplopende getallen die in elk document bestaan, dus een deel resolveert toevallig
wél en komt binnen alsof er niets aan de hand is. Dat is stille datacorruptie,
geen foutmelding. *Controleer altijd of de laagnamen bij deze tekening horen.*

**2. `ocs_convert` laat de eenheid vallen.**
Hetzelfde bestand gaf `insertion_units = 4` in het levende document en
`INSUNITS = 0` in de DXF die de conversie ervan maakte. Neem de eenheid dus uit
het levende document, niet uit een geëxporteerd bestand.

**3. Vuur geen twee brugverzoeken tegelijk af.**
`ocs_live_layers` en `ocs_live_export` in één bericht versturen liet de brug
hangen: 30 minuten geen antwoord, geen bestand. Doe ze na elkaar.

**4. `ocs_live_export` hing op een selectie van 4917 entiteiten**, terwijl het
ophalen van diezelfde selectie 0,11 s kost. Wijk uit naar de brug rechtstreeks
aanroepen als de tool blijft hangen.

**5. Een herlaad van de plugin verbreekt de verbinding stil.**
`verbonden` springt terug op `false`, zonder onderscheid tussen "nooit verbonden"
en "de plugin is onder je weggetrokken". Na sleutelen aan de plugin: opnieuw
Connect.

---

## 5. Verwante documenten

| Document | Waarvoor |
|---|---|
| [Systeemomschrijving](../Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) | architectuur, metadata, versiebeheer, statusmodel — **leidend** |
| dit document | de bewerkingsstappen van bron naar extract |
| [02_EXTRACTEN/LEESMIJ](../02_EXTRACTEN/LEESMIJ.md) | overzicht van de extracttypen |
| [Extract DXF](../02_EXTRACTEN/Extract%20DXF.md) | genormaliseerde CAD per product |
| [Extract SVG](../02_EXTRACTEN/Extract%20SVG.md) | vector 1:1 voor PDF en documentatie |
| [Extract RFA](../02_EXTRACTEN/Extract%20RFA.md) | Revit detailcomponenten |

## 6. Status

| Fabrikant | Productlijn | Producten | Bron | DXF | SVG | RFA | Database |
|---|---|---|---|---|---|---|---|
| Rothoblaas | HBS PLATE | 18 | ✔ | ✔ | ✔ | ✔ | ✔ |

Alle assets staan op `REVIEW REQUIRED`. Wat daarvoor nog moet gebeuren:

* **Vergelijking met de fabrikantdocumentatie** — het laatste punt uit §25 van
  de systeemomschrijving. Daarvoor is de datasheet of ETA nodig; die staat nog
  niet in `01_SOURCE/Rothoblaas/HBS PLATE/DOCUMENTATION/`.
* **Herkomst van het bronbestand** — `source_url`, `source_page` en
  `download_date` zijn leeg. Zonder die velden kan de actualiteitschecker de
  productpagina niet volgen. De hash en de brondatum (09-09-2024, uit de
  tekening zelf) zijn er wel.
