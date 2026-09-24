# Extract · DXF

Eén DXF per product, uit de fabrikantstekening geknipt en genormaliseerd.
DXF is hier een **zelfstandig uitvoerformaat**, geen tussenbestand voor Revit —
al is het wel de invoer voor [Extract RFA.md](Extract%20RFA.md).

Locatie: `02_EXTRACTEN/<Leverancier>/<Productlijn>/dxf/<productcode>.dxf`

## Wat erin moet

| | |
|---|---|
| Eenheid | millimeter, **`$INSUNITS = 4` expliciet zetten** |
| Inhoud | alleen de geometrie van dat ene product |
| Detail | volledig, ongewijzigd fabrikantlijnwerk |
| Lagen | behouden zoals in de bron |
| Tekst | niet opnemen — labels horen bij het blad, niet bij het product |
| Invoegpunt | zie hieronder |

## Invoegpunt

Verschuif de geometrie zo dat het greeppunt op de oorsprong ligt. Voor een
schroef is dat de **onderkant van de kop, op de hartlijn**:

```text
kop loopt van x = -kopdikte tot x = 0
punt ligt op  x = lengte onder kop
hartlijn op   y = 0
```

Waarom daar: bij het plaatsen in een detail zet je een schroef op het vlak waar
de kop landt. Dan is dat het handigste greeppunt, en ligt de punt op een
voorspelbare, uitrekenbare coördinaat.

Voor andere producttypen kies je een even goed te beredeneren punt en **legt dat
vast in het manifest** in `00_DATABASE/manifests/`.

## Werkwijze

1. Haal de geometrie op — bij voorkeur uit het levende document via de
   Open CAD Studio MCP Bridge, zie de werkwijze-instructie.
2. Splits op in producten (union-find over bounding boxes; let op exacte
   boog-bounding boxes en een stabiel drempelplateau).
3. Koppel de labels **op afmetingen, niet op afstand**.
4. Verschuif naar het invoegpunt.
5. Schrijf weg met `$INSUNITS = 4`.

De volledige uitwerking van stap 1 t/m 3 staat in
[Bibliotheek opbouwen - werkwijze](../Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md).

## Valkuil: de eenheid gaat verloren bij conversie

Dezelfde tekening gaf `insertion_units = 4` in het levende document en
`INSUNITS = 0` in de DXF die `ocs_convert` ervan maakte. **Neem de eenheid uit
het levende document of uit het originele bestand, nooit uit een geëxporteerde
tussenversie.** En zet hem in het extract expliciet, want een ontbrekende
eenheid geeft bij import een factorfout.

## Controle

* `x` loopt van `-kopdikte` tot de nominale lengte, `y` symmetrisch om nul
* `$INSUNITS` is 4
* het aantal entiteiten telt op tot dat van de bron, zonder tekstlabels
* geen tekst in het bestand

## Verwante documenten

* [LEESMIJ](LEESMIJ.md) — overzicht van de extracttypen
* [Extract SVG](Extract%20SVG.md) · [Extract RFA](Extract%20RFA.md)
* [Systeemomschrijving](../Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md)
