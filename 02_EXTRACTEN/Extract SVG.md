# Extract · SVG

Eén SVG per product, geometrisch 1:1 in millimeters. Bedoeld voor technische
PDF-tekeningen, documentatie en web — overal waar je vector wil zonder CAD.

Locatie: `02_EXTRACTEN/<Leverancier>/<Productlijn>/svg/<productcode>.svg`

De SVG komt **rechtstreeks uit de bron**, niet uit het DXF-extract. Beide zijn
onafhankelijke afgeleiden van hetzelfde bronbestand.

## Schaal

De geometrie blijft 1:1; de schaal wordt pas in de uiteindelijke tekening
toegepast. Daarom:

```xml
<svg width="65.0mm" height="14.0mm" viewBox="0 0 65.0 14.0">
```

`width`/`height` in **mm** en de `viewBox` in dezelfde getallen. Plak je hem op
ware grootte, dan meet het product exact.

Neem een marge van **0,25 mm** rondom en verreken die in zowel de `viewBox` als
de mm-maat, zodat de lijndikte niet afgekapt wordt en de schaal zuiver blijft.

Die marge hangt aan de lijndikte: bij `stroke-width` 0,12 steekt de streek 0,06
mm buiten de geometrie, dus 0,25 mm is ruim. Verander je de lijndikte, pas dan
ook de marge aan — anders kapt de rand alsnog af.

## Bogen blijven bogen

Geen polygoonbenadering. Twee dingen om goed te doen:

**Polylijn-bulges omrekenen:**

```text
hoek   = 4 · atan(bulge)
straal = koorde / (2 · sin(hoek/2))
```

**Y spiegelen én de sweep-vlag omkeren.** DXF telt omhoog, SVG omlaag. Na het
spiegelen keert de draairichting om: tegen de klok in wordt `0`, met de klok mee
wordt `1`. Vergeet je dat, dan bollen alle bogen de verkeerde kant op — en dat
is in de getallen onzichtbaar.

## Opmaak

| | |
|---|---|
| `fill` | `none` |
| `stroke` | `#1a1a1a` |
| `stroke-width` | `0.12` (mm, dus 0,12 mm op ware grootte) |
| Lagen | behouden als `<g id="laagnaam">` |
| Tekst | zie hieronder |
| `<desc>` | fabrikant, schaal, eenheid, brondatum |

### Wel of geen tekst

Er zijn twee soorten tekst in een fabrikantstekening, en ze horen verschillend
behandeld te worden:

**Bladannotatie** — de productcode naast de tekening, maatvoering, disclaimers.
Die hoort bij het blad en niet bij het product. Laat weg; zet de productcode in
`<title>` en in de bestandsnaam.

**Stempeling op het product** — letters die fysiek op het onderdeel staan.
Bij HBS PLATE staat in het kopaanzicht `H B S P` en drie `X`-en binnen de
kopcirkel. Die horen er wél in: ze zijn onderdeel van het product.

Onderscheid ze op positie, niet op inhoud: valt de tekst binnen de omtrek van
het product, dan is het stempeling.

Neem stempeling op als `<text>` met `font-size` in mm en
`text-anchor="middle"`. De letters zijn dan positioneel exact; de precieze
glyphvorm hangt af van het lettertype van de kijker, en dat is acceptabel voor
een stempeling.

> **Valkuil.** Gebruik `dominant-baseline` **of** een handmatige verschuiving
> van ongeveer 0,35 em, nooit allebei. Renderers die de eigenschap ondersteunen
> corrigeren dan dubbel en de tekst zakt een derde regelhoogte weg. Omdat lang
> niet elke renderer `dominant-baseline` ondersteunt, is de handmatige
> verschuiving de veiligste keuze.

### De lijndikte is een modelruimte-maat

`stroke-width` 0,12 is 0,12 mm **op ware grootte**, niet op papier. De dikte
schaalt dus mee met de tekening:

| Toegepaste schaal | Product op papier | Lijn op papier |
|---|---|---|
| 1:1 | 65 mm | 0,12 mm |
| 1:10 | 6,5 mm | 0,012 mm |
| 1:20 | 3,3 mm | 0,006 mm |

Over het bereik dat §5 van de systeemomschrijving noemt loopt de papierdikte dus
een factor 20 uiteen. Lees 0,12 daarom niet als "een dunne lijn op papier".

Dat is bewust: het extract is de 1:1-bron en mag geen schaalbeslissing bevatten.
Een papierdikte hoort thuis in het programma dat de tekening maakt. Open PDF
Studio schaalt de lijndikte op dit moment mee met het symbool; het vasthouden
van een papierdikte staat daar open als
[issue #341](https://github.com/OpenAEC-Foundation/open-pdf-studio/issues/341).

## Detailniveau per schaal

§8 van de systeemomschrijving kent SYMBOL, DETAIL en HIGH DETAIL. Voor SVG is
dat geen luxe: fabrikantgeometrie is vaak fijner dan het papier aankan.

Gemeten aan de HBS PLATE-set liggen de draadlijnen **0,75 mm** uit elkaar.

| Toegepaste schaal | Afstand tussen draadlijnen op papier |
|---|---|
| 1:1 | 0,750 mm |
| 1:10 | 0,075 mm |
| 1:20 | 0,037 mm |

Een normale dunne lijn is 0,25 mm. Op 1:10 is die dus **ruim drie keer breder
dan de tussenruimte** — het draad loopt dicht tot een zwart blok, bij elke
lijndikte die een printer of scherm kan zetten. Dat is geen conversiefout, en
ook niet met een lijndikte-instelling op te lossen.

**De SVG blijft niettemin de volledige fabrikantgeometrie.** Er wordt hier
niet vereenvoudigd. Dit extract is de getrouwe 1:1-weergave van de bron, en
vereenvoudigen zou er een interpretatie van maken — dan is niet meer na te gaan
of een afwijking van de fabrikant komt of van ons.

Een vereenvoudigde weergave is een **ander detailniveau** (`SYMBOL` uit §8) en
daarmee een zelfstandige representation met een eigen asset en eigen herkomst,
niet een variant van dit bestand. Zolang die er niet is, is de leesbaarheids-
grens iets wat degene die de tekening maakt moet kennen — het is geen gebrek
in het extract.

Bepaal die grens door te rekenen, niet op het oog: is de kleinste terugkerende
maatvoering in het extract op de doelschaal kleiner dan de lijndikte waarmee
geplot wordt, dan is de volledige geometrie daar onbruikbaar.

## Dubbel en overlappend lijnwerk verwijderen

Fabrikantstekeningen bevatten regelmatig lijnstukken die twee keer getekend
zijn, of die elkaar gedeeltelijk overlappen. Onzichtbaar op het scherm, maar
wel schadelijk: het bestand wordt groter, de lijn wordt bij half-transparante
weergave donkerder, en alles wat later uit deze geometrie wordt afgeleid erft
de dubbeling.

Drie controles, in deze volgorde — elke volgende vangt wat de vorige mist:

**1. Exacte duplicaten.** Twee curves met dezelfde eindpunten. Vergelijk
**richtingongevoelig**: een lijn van A naar B is dezelfde als van B naar A.

**2. Bijna-duplicaten.** Eindpunten die binnen een kleine tolerantie (0,01 mm)
samenvallen. Ontstaan door afrondingen bij eerdere conversies.

**3. Collineaire overlappingen.** Twee lijnen op dezelfde oneindige lijn
waarvan de intervallen elkaar overlappen. Dit is de lastigste en tegelijk de
meest voorkomende: de eindpunten verschillen, dus 1 en 2 vinden hem niet.

Aanpak voor 3: bereken per lijn de genormaliseerde richting en de loodrechte
afstand tot de oorsprong, en groepeer daarop — dan zitten alleen collineaire
lijnen bij elkaar. Projecteer binnen zo'n groep elk lijnstuk op de richting,
sorteer de intervallen en voeg overlappende samen tot één lijnstuk.

> **Verwijder nooit blind.** Bij overlap houd je het samengevoegde,
> langere lijnstuk over — niet één van de twee. Gooi je er zomaar één weg, dan
> ontstaat er een gat waar het ene stuk verder liep dan het andere.

Meet altijd wat je vindt, en leg het vast. Bij de HBS PLATE-set:
**0 exacte duplicaten, 0 bijna-duplicaten en 1 collineaire overlap** van
2,2 mm in de 12x200. Dat is uitzonderlijk schoon voor een fabrikantsbestand —
reken er bij een volgende leverancier niet op.

Deze controle geldt ook voor [Extract DXF](Extract%20DXF.md); voer hem daarom
uit op de brongeometrie, vóór het splitsen in producten, zodat beide extracten
ervan profiteren.

## Controle

1. **Tel de paden.** De som over alle SVG's moet gelijk zijn aan het aantal
   geometrie-entiteiten in de bron, zonder tekstlabels — na aftrek van wat de
   ontdubbeling heeft verwijderd.
2. **Render de weggeschreven SVG's terug** — niet de brondata. Alleen zo test je
   ook de `A`-vlaggen.
3. **Meet de hoofdmaten na** tegen de productaanduiding.

## Verwante documenten

* [LEESMIJ](LEESMIJ.md) — overzicht van de extracttypen
* [Extract DXF](Extract%20DXF.md) · [Extract RFA](Extract%20RFA.md)
* [Bibliotheek opbouwen - werkwijze](../Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md)
