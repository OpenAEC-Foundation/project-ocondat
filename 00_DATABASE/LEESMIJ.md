# 00_DATABASE

De administratie. Alles hier is **door een mens ingevuld** en kan door geen
enkel script worden teruggemaakt.

Daarom staat deze map bewust **buiten** `02_EXTRACTEN`: `update-log.csv` is
geschiedenis, en `source_url`, `download_date` en beoordeelde statussen zijn
beslissingen. Eén opruimactie op de extracten zou die wissen.

## De bestanden

| Bestand | Wat erin staat |
|---|---|
| `suppliers.csv` | per leverancier: website, welke formaten ze leveren, scope, status |
| `products.csv` | het product zelf: code, naam, categorie, variant, maten, status |
| `assets.csv` | elk bestand apart: bron én afgeleide, met hash, herkomst, eenheid, aanzicht |
| `dependencies.csv` | welke afgeleide van welke bron komt (`derived_from`) |
| `update-log.csv` | wat er wanneer door wie is gewijzigd, en waarom |
| `manifests/` | per productlijn een JSON met de afleidingsdetails: hoe de maten zijn bepaald, welk invoegpunt is gekozen, wat er niet is opgenomen |

Scheidingsteken is de puntkomma, tekstcodering UTF-8.

## Waarom assets los van producten staan

Eén product heeft meerdere bronnen. Een fabrikant kan voor hetzelfde product
een DXF per aanzicht leveren, plus een RFA, plus een IFC, plus een datasheet.
Geen van die bestanden vervangt een ander. In `assets.csv` is elk bestand
daarom een eigen rij, gekoppeld via `product_id`, met `representation_type`
(`SYMBOL` / `DETAIL` / `HIGH DETAIL` / `3D`) en `view_type` (`side`, `top`, …).

Een representation kan een andere granulariteit hebben dan het product. Bij de
HBS PLATE-pilot is `side` per product maar `top` per diameter — de kop is gelijk
voor alle lengtes. Die kopaanzichten staan in `assets.csv` daarom zonder
`product_id`; de koppeling loopt via `product_code` en `view_type`.

## Statusmodel

```text
ACTIVE · NEW · UPDATED · REVIEW REQUIRED · REPLACED · DISCONTINUED · UNKNOWN
```

Een verdwenen downloadlink betekent **niet** automatisch `DISCONTINUED`. De
checker stelt eerst vast of de URL is veranderd, het bestand is vervangen, of
het product een nieuwe code heeft. Zie §17 en §18 van de systeemomschrijving.

## De rijen in deze pull request

Gevuld met de **Rothoblaas HBS PLATE-pilot**: 18 producten met hun bron- en
afgeleide assets. Dat is meegestuurd om te laten zien hoe de administratie
eruitziet als hij gevuld is.

> **De `file_path`-kolommen verwijzen naar bestanden die niet in deze pull
> request zitten.** `01_SOURCE` is leeg gelaten en de extracten zijn
> achtergehouden; zie §8 van [VOORSTEL.md](../VOORSTEL.md). De rijen zijn dus
> een voorbeeld van de vorm, geen werkende dataset.

Alle assets staan op `REVIEW REQUIRED`. Wat er voor `APPROVED` nog ontbreekt —
de vergelijking met de fabrikantdocumentatie, en de directe downloadlink met
`download_date` — staat onderaan de werkwijze-instructie.

## Verwante documenten

* [Systeemomschrijving](../Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) — §13 productstructuur, §14 metadata, §17 statusmodel, §19 dependency tracking
* [Bibliotheek opbouwen · werkwijze](../Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md) — stap 9, wat er in het manifest hoort
