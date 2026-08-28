# Project Ocondat

Open building data using WikiData and other datasources.

## Purpose

Project Ocondat builds a **vendor-independent product library**: technical
products from many manufacturers, collected, versioned and checked in one place.

The library should make it possible to take manufacturer files and:

* collect them centrally;
* store them versioned and traceable;
* check them for currency;
* reuse them as 2D vector artwork;
* apply them at any scale in PDF drawings;
* use them as a 2D Revit family;
* optionally use them as a 3D BIM object;
* and flag automatically when a product or source file has been changed,
  replaced or discontinued.

Two things follow from that, and they shape the whole architecture:

**One product is not one CAD file.** A manufacturer may ship several DXF views,
an RFA, an IFC, a STEP model, a datasheet and an installation guide for the same
article. Each is registered as its own source asset, and none of them silently
replaces another. A simplified IFC must never override a manufacturer DXF for 2D
detailing.

**The manufacturer's own file is the source; everything we make is derived.**
An SVG or a Revit family carries the hash of the file it came from, so a changed
manufacturer file can be detected — even when the name and download URL stay the
same — and everything downstream can be flagged for review.

Rothoblaas is the first supplier the system is applied to, but the architecture
is not specific to Rothoblaas. Würth, Fischer, Hilti, Leviat, Schöck, steel
producers, sheet suppliers and others should fit the same model; each supplier
gets its own source configuration for the formats it actually delivers.

## Features

- DXF component libraries organized by building element type (floors, walls, etc.)
- Blender/BlenderBIM IFC library generation
- Material and component definitions for Dutch construction industry

## Library structure

Files are organised by **where they come from**, not by building element. One
question decides where something belongs: *can I throw this away and remake it?*

| Folder | Origin | Rebuildable |
|---|---|---|
| `01_SOURCE` | from the manufacturer | never — read-only, keep forever |
| `02_EXTRACTEN` | produced by a script | yes, entirely |
| `00_DATABASE` | filled in by a person | no — decisions and history |
| `_TOOLS` | code | through version control |
| `99_ARCHIVE` | superseded versions, by date | no — traceability |

The building element does not disappear: it moves from the path into a column
(`category` in `products.csv`), alongside NL-SfB, supplier and product line.

> **Never edit anything under `02_EXTRACTEN` by hand.** The next generation pass
> overwrites manual work silently. If something is wrong, fix the generator.

## Documentation

The design documents are in Dutch.

| Document | What for |
|---|---|
| [Systeemomschrijving](Manufacturer%20CAD-BIM%20Product%20Library%20-%20systeemomschrijving.md) | architecture, metadata, status model, currency checker, versioning — **leading document** |
| [Bibliotheek opbouwen · werkwijze](Ocondat%20bibliotheek%20instructie/Bibliotheek%20opbouwen%20-%20werkwijze.md) | the steps from manufacturer drawing to extract, with the pitfalls |
| [02_EXTRACTEN/LEESMIJ](02_EXTRACTEN/LEESMIJ.md) | the three extract types and the chain between them |
| [_TOOLS/LEESMIJ](_TOOLS/LEESMIJ.md) | the generators and the order to run them in |
| [VOORSTEL](VOORSTEL.md) | why the library is organised this way, and how the existing content maps onto it |
