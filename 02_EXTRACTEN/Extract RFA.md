# Extract · RFA

Revit detailcomponenten, automatisch gegenereerd uit de DXF-extracten.

Locatie: `02_EXTRACTEN/<Leverancier>/<Productlijn>/rfa/`

Dit is het enige extracttype waarbij de geometrie **vereenvoudigd** wordt, en
dat is geen keuze maar een harde eis van Revit. Die vereenvoudiging hoort hier
en mag niet doorwerken in [DXF](Extract%20DXF.md) of [SVG](Extract%20SVG.md).

## 1. Revit weigert korte curves

`Application.ShortCurveTolerance` is bij een standaardinstallatie
**0,7804 mm** (1/32 inch). Fabrikantgeometrie zit daar geregeld onder: in de
HBS PLATE-set was 4,9 % van de 5248 curves te kort, waarvan **135 exact nul
lang** — dubbele punten in de fabrikantspolylijnen.

Er gaat dus een schoonmaakstap aan vooraf: `_TOOLS/curveclean.py`.

## 2. Schoonmaken — drie regels die ertoe doen

**Weld op verbinding, nooit op afstand.** De twee flanken van een draadtand
liggen bij de tip ~0,7 mm uit elkaar. Punten samenvoegen op nabijheid laat elke
tand instorten terwijl alle statistieken er goed uit blijven zien. Alleen curves
die *daadwerkelijk op hetzelfde eindpunt eindigen* mogen meebewegen.

**Pak boog-hoeken uit rond de oude waarde.** Bewaar een boog als
`(center, radius, a0, a1)` met `a1 = a0 + sweep`. Verschuift een eindpunt,
bereken de nieuwe hoek dan en verschuif hem met een veelvoud van 2π naar de tak
die het dichtst bij de oude ligt. Doe je dat niet en gebruik je
`(a1 - a0) % 2π`, dan klapt een minieme negatieve draai om naar bijna 2π en
wordt een boogje van een halve millimeter **een cirkel van 20 mm**.

**Trek samen naar het snijpunt van de buren, niet naar het midden.** Bij een
afgeronde hoek kost het midden maatverlies ter grootte van de straal: een
kwartboog R0,5 in een kophoek trekt de omtrek 0,25 mm naar binnen in x én y —
een kop van Ø13,5 wordt dan 13,00. Met het snijpunt wordt de afronding een
scherpe hoek en blijft de maat exact. Val terug op het midden als de buren
bijna evenwijdig zijn.

Resultaat op de HBS PLATE-set: 5248 → 4921 curves, kortste 0,886 mm,
25 restgaten van maximaal 0,37 mm, hoofdmaten exact.

## 3. Familie bouwen

Sjabloon: `…\Family Templates\English\Metric Detail Item.rft`
(pad via `Application.FamilyTemplatePath`; de taalsubmap verschilt per
installatie).

```text
NewFamilyDocument(sjabloon)
  → view = FloorPlan "Ref. Level"
  → transactie
      → per curve: FamilyCreate.NewDetailCurve(view, curve)
      → FamilyManager.NewType(naam)        <-- eerst het type!
      → AddParameter + Set per metadataveld
  → SaveAs
```

**`NewType()` moet vóór het zetten van typeparameters.** Een verse familie heeft
geen type, en dan faalt elke `Set` met *"There is no current type."*

Eenheden: Revit rekent intern in voet, dus deel millimeters door **304,8**.

## 4. Metadata

Verplicht per familie, conform §7 van de systeemomschrijving:

```text
OCD_Supplier        OCD_ProductCode     OCD_SourceFile
OCD_ProductFamily   OCD_ProductName     OCD_SourceSHA256
OCD_ThreadDia_mm    OCD_Length_mm       OCD_SourceDate
OCD_HeadDia_mm      OCD_HeadThk_mm      OCD_CheckedDate
OCD_HoleDiaSteel_mm                     OCD_Status
```

De bronhash en brondatum maken het mogelijk dat de actualiteitschecker bepaalt
of een family opnieuw beoordeeld moet worden.

## 5. Types en geometrie

**Een Revit-type varieert parameters, geen lijnwerk.** Producten die in
geometrie verschillen — bij HBS PLATE loopt het aantal draadtanden van 10 naar
33 — kunnen dus niet zomaar types van elkaar zijn.

De gekozen oplossing: **één familie per productlijn met een type per product,
waarin de losse productfamilies genest zijn**, elk met een
zichtbaarheidsparameter die per type geschakeld wordt.

Nest, en schakel niet de losse detaillijnen. Bij HBS PLATE scheelt dat
**18 koppelingen in plaats van 4921**, en de geometrie blijft per product
herleidbaar. De losse `<code>.rfa` blijven daarom bestaan: ze zijn zowel
zelfstandig bruikbaar als bouwsteen.

Prijs, bewust geaccepteerd: alle geometrie zit in één bestand en elk project dat
één product plaatst laadt de hele lijn mee.

## 6. Naamgeving

De verzamelfamilie volgt de **NLRS-conventie**, onderdelen gescheiden door
underscores:

```text
NLRS_<SfB>_<categorie>_<plaatsing>_<omschrijving>_<fabrikant>_<provider>
NLRS_28_DI_UN_schroef_HBS-PLATE_Rothoblaas_bluetek
```

`DI` is de categorie-afkorting voor Detail Item, `28` de NL-SfB-hoofdgroep voor
een schroef, `UN` de plaatsingscode voor een component zonder host, en `bluetek`
de contentprovider.

**De geneste productfamilies houden hun productcode** (`HBSPL860.rfa`,
`HBSPL_HEAD_8.rfa`). Zij zijn bouwstenen, geen zelfstandige
bibliotheekfamilies, en een NLRS-naam per stuk zou de familielijst van een
project vullen met 21 lange namen zonder dat iemand ze los plaatst.

**Typenamen dragen de productaanduiding** zoals de fabrikant die op de tekening
zet: `HBSPL860 - 8x60`, `kop D8`. In de typekeuzelijst zie je zo meteen welke
maat je pakt. De NLRS-conventie geldt voor de familienaam, niet voor de types.

## 7. Valkuilen bij het aansturen van Revit

* **Een familie die in Revit openstaat blokkeert `SaveAs`** met *"File has been
  opened by another Revit instance."* Sluit open documenten voor een batch.
* **Het actieve document kan niet via de API dicht** — *"The active document may
  not be closed from the API."* Sla dat product over of laat het handmatig
  sluiten.
* **Een batch van 18 families overschrijdt de time-out van de MCP-aanroep.**
  Bouw in blokken en controleer de voortgang op de schijf, niet in de aanroep.
* Revit laat bij overschrijven backups achter als `<naam>.0001.rfa`. Die horen
  niet in de bibliotheek en moeten na afloop weg.

## 8. Geen tekst in de familie

Ook stempeling op het product blijft uit de RFA, terwijl die in
[SVG](Extract%20SVG.md) en [DXF](Extract%20DXF.md) wél meegaat. Reden: tekst in
een Revit-detailcomponent is **papiergebonden**, niet modelgebonden. Een
stempeling van 2,6 mm op het product is daarmee niet schaalvast weer te geven —
bij 1:5 zou hij vijf keer te groot staan.

## 9. Controle

1. **Lees de familie terug van schijf** en tel de curve-elementen per type
   (`Line`, `Arc`) — die moeten gelijk zijn aan de opdracht.
2. **Meet de extents.** Voor een 8×60: `x -4,500 … 60,000`, `y ±6,750`, dus
   64,500 × 13,500 mm. Deze controle vond twee keer een fout van 0,25 mm die er
   in Revit volkomen normaal uitzag.
3. Controleer categorie (`Detail Items`), typenaam en alle `OCD_`-parameters.
4. Bij een verzamelfamilie: controleer per type dat er **precies één**
   zichtbaarheidsparameter aan staat en dat die bij het product van dat type
   hoort.

> **Valkuil bij het meten.** Gebruik geen `Curve.Tessellate()` om extents te
> bepalen. Revit hakt een halve cirkel in drie koorden, waardoor de gemeten
> hoogte `sin 60° = 0,866` van de werkelijke wordt — een kop van Ø13,5 meet dan
> 11,69. Bemonster in plaats daarvan het parameterbereik met `Curve.Evaluate()`,
> of lees `Arc.Radius` rechtstreeks. Eindpunten alleen volstaan evenmin: bij een
> boog ligt het uiterste punt tussen de eindpunten in.

## Verwante documenten

* [LEESMIJ](LEESMIJ.md) — overzicht van de extracttypen
* [Extract DXF](Extract%20DXF.md) — de invoer voor dit extract
* [Extract SVG](Extract%20SVG.md)
* [Systeemomschrijving](../Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) — §7 Revit, §8 detailniveaus, §25 kwaliteitscontrole
