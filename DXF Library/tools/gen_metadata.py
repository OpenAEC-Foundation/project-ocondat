"""Generate metadata MD files at every level of the component hierarchy.

Walks components/ and details/ directory trees and generates:
  - _fabrikant.md  (manufacturer level)
  - _serie.md      (series level)
  - _product.md    (product level)
  - {variant}.md   (variant level, next to each .dxf)

Usage:
    python tools/gen_metadata.py                # Generate all metadata
    python tools/gen_metadata.py --dry-run       # Preview without writing
    python tools/gen_metadata.py --overwrite      # Overwrite existing MD files
"""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
COMPONENTS_DIR = BASE / "components"
DETAILS_DIR = BASE / "details"
TODAY = str(date.today())


# ── Manufacturer metadata ──────────────────────────────────────────────────
MANUFACTURERS = {
    "ArcelorMittal": {
        "website": "https://constructalia.arcelormittal.com",
        "source": "Constructalia DWG downloads",
        "license": "Manufacturer documentation - free for engineering use",
        "ifc_categories": ["IfcMember", "IfcColumn"],
        "status": "active",
        "country": "LU",
        "founded": "2006",
        "description": "European steel profile manufacturer. Profiles conform to EN 10365.",
    },
    "Halfen": {
        "website": "https://www.halfen.com",
        "source": "Halfen CAD portal downloads",
        "license": "Manufacturer documentation - free for engineering use",
        "ifc_categories": ["IfcMechanicalFastener", "IfcMember"],
        "status": "active",
        "country": "DE",
        "founded": "1929",
        "description": "Connection technology, anchoring systems, and facade fasteners.",
    },
    "Generic": {
        "website": "https://github.com/OpenAEC-Foundation/Project-Ocondat",
        "source": "Project OconDat component library",
        "license": "LGPL-3.0",
        "ifc_categories": ["Various"],
        "status": "active",
        "country": "",
        "founded": "",
        "description": "Generic construction components organized by NL-SfB category. No specific manufacturer attribution.",
    },
    "Community": {
        "website": "https://github.com/OpenAEC-Foundation/Project-Ocondat",
        "source": "Community contributions (DXF-library, dxfBlocks)",
        "license": "Mixed - see individual series",
        "ifc_categories": ["Various"],
        "status": "active",
        "country": "",
        "founded": "",
        "description": "Community-contributed CAD blocks from open-source libraries.",
    },
    "DwgModels": {
        "website": "",
        "source": "DwgModels.com downloads",
        "license": "Free for personal and commercial use",
        "ifc_categories": ["Various"],
        "status": "active",
        "country": "",
        "founded": "",
        "description": "Construction detail blocks from DwgModels.com.",
    },
    "Geberit": {
        "website": "https://www.geberit.nl",
        "source": "Geberit CAD downloads",
        "license": "Manufacturer documentation - free for engineering use",
        "ifc_categories": ["IfcSanitaryTerminal"],
        "status": "active",
        "country": "CH",
        "founded": "1874",
        "description": "Sanitary systems and installation elements.",
    },
    "Peikko": {
        "website": "https://www.peikko.com",
        "source": "Peikko CAD library",
        "license": "Manufacturer documentation - free for engineering use",
        "ifc_categories": ["IfcMember", "IfcMechanicalFastener"],
        "status": "active",
        "country": "FI",
        "founded": "1965",
        "description": "Concrete connections, composite beams, and fastening technology.",
    },
    "VBI": {
        "website": "https://www.vbi.nl",
        "source": "VBI product documentation",
        "license": "Manufacturer documentation - free for engineering use",
        "ifc_categories": ["IfcSlab", "IfcBeam"],
        "status": "active",
        "country": "NL",
        "founded": "1949",
        "description": "Prefabricated concrete elements: floor slabs, beams, and walls.",
    },
}

# ── Series metadata hints ──────────────────────────────────────────────────
SERIES_HINTS = {
    "HE-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcIShapeProfileDef", "standard": "EN 10365", "description": "Wide-flange H-profiles (HEA, HEB, HEM) for structural applications."},
    "HD-profielen": {"ifc_class": "IfcColumn", "ifc_predefined_type": "COLUMN", "ifc_profile": "IfcIShapeProfileDef", "standard": "EN 10365", "description": "Heavy wide-flange H-profiles for column applications."},
    "HL-profielen": {"ifc_class": "IfcColumn", "ifc_predefined_type": "COLUMN", "ifc_profile": "IfcIShapeProfileDef", "standard": "EN 10365", "description": "Extra-wide flange H-profiles for heavy column applications."},
    "IPE-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcIShapeProfileDef", "standard": "EN 10365", "description": "European I-beams (IPE series) for structural applications."},
    "IPN-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcIShapeProfileDef", "standard": "EN 10365", "description": "European standard I-beams (IPN/INP series) with tapered flanges."},
    "L-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcLShapeProfileDef", "standard": "EN 10056", "description": "Angle sections (equal and unequal leg)."},
    "UPE-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcUShapeProfileDef", "standard": "EN 10365", "description": "European parallel flange channel sections."},
    "UB-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcIShapeProfileDef", "standard": "BS 4", "description": "British universal beams."},
    "UC-profielen": {"ifc_class": "IfcColumn", "ifc_predefined_type": "COLUMN", "ifc_profile": "IfcIShapeProfileDef", "standard": "BS 4", "description": "British universal columns."},
    "UPN-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcUShapeProfileDef", "standard": "EN 10365", "description": "European standard channel sections (UPN/UPE)."},
    "W-profielen": {"ifc_class": "IfcMember", "ifc_predefined_type": "MEMBER", "ifc_profile": "IfcIShapeProfileDef", "standard": "ASTM A6", "description": "American wide-flange beam sections (W series)."},
    "Damwandprofielen": {"ifc_class": "IfcPile", "ifc_predefined_type": "SHEET", "ifc_profile": "IfcArbitraryClosedProfileDef", "standard": "EN 10248", "description": "Steel sheet pile profiles for retaining walls."},
    "Ankerschienen-HTA": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "ANCHORBOLT", "standard": "ETA", "description": "Halfen anchor channels for cast-in connections."},
    "Bodyanker-BA": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "ANCHORBOLT", "standard": "ETA", "description": "Halfen body anchors for natural stone facade cladding."},
    "Curtain-Wall-HCW": {"ifc_class": "IfcElementAssembly", "ifc_predefined_type": "ACCESSORY_ASSEMBLY", "standard": "ETA", "description": "Halfen curtain wall connections."},
    "HIT-Verbindungen": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "SHEARCONNECTOR", "standard": "ETA", "description": "Halfen HIT thermal insulation connections."},
    "Deckenanker-SOF": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "ANCHORBOLT", "standard": "ETA", "description": "Halfen soffit anchors for natural stone ceilings."},
    "Konsolen-UK": {"ifc_class": "IfcElementAssembly", "ifc_predefined_type": "ACCESSORY_ASSEMBLY", "standard": "ETA", "description": "Halfen brackets for facade support."},
    "Zubehoer-A": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "USERDEFINED", "standard": "ETA", "description": "Halfen accessories type A."},
    "Zubehoer-B": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "USERDEFINED", "standard": "ETA", "description": "Halfen accessories type B."},
    "Zubehoer-M": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "USERDEFINED", "standard": "ETA", "description": "Halfen accessories type M."},
    "Sanitair": {"ifc_class": "IfcSanitaryTerminal", "ifc_predefined_type": "USERDEFINED", "standard": "", "description": "Sanitary installation elements."},
    # Community/DXF-library series
    "appliances": {"ifc_class": "IfcElectricAppliance", "ifc_predefined_type": "USERDEFINED", "standard": "", "description": "Household and kitchen appliances."},
    "basins": {"ifc_class": "IfcSanitaryTerminal", "ifc_predefined_type": "WASHHANDBASIN", "standard": "", "description": "Wash basins and sinks."},
    "bathtubs": {"ifc_class": "IfcSanitaryTerminal", "ifc_predefined_type": "BATH", "standard": "", "description": "Bathtubs."},
    "beds": {"ifc_class": "IfcFurniture", "ifc_predefined_type": "BED", "standard": "", "description": "Beds and sleeping furniture."},
    "cars": {"ifc_class": "IfcTransportElement", "ifc_predefined_type": "USERDEFINED", "standard": "", "description": "Vehicle outlines for parking layouts."},
    "chairs": {"ifc_class": "IfcFurniture", "ifc_predefined_type": "CHAIR", "standard": "", "description": "Chairs and seating."},
    "lounge": {"ifc_class": "IfcFurniture", "ifc_predefined_type": "SOFA", "standard": "", "description": "Lounge and sofa furniture."},
    "office": {"ifc_class": "IfcFurniture", "ifc_predefined_type": "DESK", "standard": "", "description": "Office furniture and desks."},
    "people": {"ifc_class": "IfcAnnotation", "ifc_predefined_type": "USERDEFINED", "standard": "", "description": "Human figure annotations for scale reference."},
    "tables": {"ifc_class": "IfcFurniture", "ifc_predefined_type": "TABLE", "standard": "", "description": "Tables and dining furniture."},
    "vegetation": {"ifc_class": "IfcGeographicElement", "ifc_predefined_type": "VEGETATION", "standard": "", "description": "Trees, plants and vegetation symbols."},
    "wc": {"ifc_class": "IfcSanitaryTerminal", "ifc_predefined_type": "TOILETPAN", "standard": "", "description": "Toilets and WC elements."},
    # Community/dxfBlocks series
    "Architecture": {"ifc_class": "IfcFurniture", "ifc_predefined_type": "USERDEFINED", "standard": "", "description": "Architectural symbols and furniture blocks."},
    "DrawingSymbols": {"ifc_class": "IfcAnnotation", "ifc_predefined_type": "USERDEFINED", "standard": "", "description": "Drawing symbols and annotations."},
    "Fasteners": {"ifc_class": "IfcMechanicalFastener", "ifc_predefined_type": "BOLT", "standard": "", "description": "Bolts, nuts, and fastener details."},
    "InfoTech": {"ifc_class": "IfcElectricAppliance", "ifc_predefined_type": "USERDEFINED", "standard": "", "description": "IT equipment and network symbols."},
}

# NL-SfB to IFC mapping (for Generic components)
NLSFB_IFC = {
    "00": ("IfcMechanicalFastener", "USERDEFINED"),
    "16": ("IfcPile", "DRIVEN"),
    "17": ("IfcPile", "DRIVEN"),
    "20": ("IfcMechanicalFastener", "USERDEFINED"),
    "21": ("IfcWall", "STANDARD"),
    "22": ("IfcWall", "STANDARD"),
    "23": ("IfcSlab", "FLOOR"),
    "27": ("IfcRoof", "FLAT_ROOF"),
    "28": ("IfcMember", "MEMBER"),
    "30": ("IfcPlate", "CURTAIN_PANEL"),
    "31": ("IfcWindow", "WINDOW"),
    "32": ("IfcWindow", "WINDOW"),
    "33": ("IfcOpeningElement", "OPENING"),
    "34": ("IfcBuildingElementProxy", "USERDEFINED"),
    "35": ("IfcMember", "MULLION"),
    "37": ("IfcBuildingElementProxy", "USERDEFINED"),
    "40": ("IfcCovering", "CLADDING"),
    "41": ("IfcCurtainWall", "USERDEFINED"),
    "42": ("IfcMember", "MULLION"),
    "43": ("IfcCovering", "CLADDING"),
    "45": ("IfcCovering", "CEILING"),
    "47": ("IfcRoof", "USERDEFINED"),
    "52": ("IfcPipeSegment", "USERDEFINED"),
    "90": ("IfcSlab", "PAVING"),
    "91": ("IfcBuildingElementProxy", "USERDEFINED"),
}

# Reverse mapping: NL-SfB category name -> cat_id for Generic
NLSFB_BY_NAME = {
    "Basismaterialen": "00",
    "Funderingspalen": "16",
    "Palen": "17",
    "Ankers-en-verbindingen": "20",
    "Wanden-metselwerk": "21",
    "Wanden-blokken": "22",
    "Vloeren": "23",
    "Dakbedekking": "27",
    "Staalconstructie": "28",
    "Glas-en-gevelbekleding": "30",
    "Ramen-en-deuren": "31",
    "Kozijnen": "32",
    "Sparingen": "33",
    "Diversen-bent": "34",
    "Kantlatten": "35",
    "Diversen-DI": "37",
    "Vloerplaten-en-afwerking": "40",
    "Gevelafwerking": "41",
    "Afwerkprofielen": "42",
    "Vloer-en-wandafwerking": "43",
    "Plafonds": "45",
    "Dakdetails": "47",
    "Hemelwaterafvoer": "52",
    "Bestrating": "90",
    "Overig": "91",
}


def yaml_list(items, indent=2):
    """Format a list as YAML."""
    prefix = " " * indent
    return "\n".join(f"{prefix}- {item}" for item in items)


def write_md(path, content, dry_run=False, overwrite=False):
    """Write an MD file if it doesn't exist (or overwrite is set)."""
    if path.exists() and not overwrite:
        return False
    if dry_run:
        return True
    os.makedirs(path.parent, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def gen_fabrikant_md(fabrikant_name, fab_dir, dry_run=False, overwrite=False):
    """Generate _fabrikant.md at manufacturer level."""
    meta = MANUFACTURERS.get(fabrikant_name, {})

    ifc_list = meta.get("ifc_categories", ["Various"])
    ifc_yaml = "\n".join(f"  - {c}" for c in ifc_list)
    status = meta.get("status", "active")
    country = meta.get("country", "")
    founded = meta.get("founded", "")

    content = f"""---
name: "{fabrikant_name}"
type: fabrikant
status: "{status}"
country: "{country}"
founded: "{founded}"
website: "{meta.get('website', '')}"
source: "{meta.get('source', 'Unknown')}"
license: "{meta.get('license', 'Unknown')}"
ifc_categories:
{ifc_yaml}
date_added: "{TODAY}"
---
# {fabrikant_name}

{meta.get('description', f'{fabrikant_name} components.')}
"""
    path = fab_dir / "_fabrikant.md"
    return write_md(path, content, dry_run, overwrite)


def gen_serie_md(serie_name, fabrikant_name, serie_dir, dry_run=False, overwrite=False):
    """Generate _serie.md at series level."""
    hints = SERIES_HINTS.get(serie_name, {})

    # Try to infer IFC from NL-SfB for Generic manufacturer
    ifc_class = hints.get("ifc_class", "IfcBuildingElementProxy")
    ifc_pred = hints.get("ifc_predefined_type", "USERDEFINED")

    if fabrikant_name == "Generic" and serie_name in NLSFB_BY_NAME:
        cat_id = NLSFB_BY_NAME[serie_name]
        ifc_class, ifc_pred = NLSFB_IFC.get(cat_id, (ifc_class, ifc_pred))

    # Count products (subdirectories)
    product_count = sum(
        1 for d in serie_dir.iterdir()
        if d.is_dir() and not d.name.startswith('_')
    ) if serie_dir.is_dir() else 0

    nl_sfb = ""
    if fabrikant_name == "Generic" and serie_name in NLSFB_BY_NAME:
        nl_sfb = f'\nnl_sfb: "{NLSFB_BY_NAME[serie_name]}"'

    description = hints.get("description", f"{serie_name} series from {fabrikant_name}.")

    ifc_profile = hints.get("ifc_profile", "")
    ifc_profile_line = f'\nifc_profile: "{ifc_profile}"' if ifc_profile else ""

    content = f"""---
name: "{serie_name}"
fabrikant: "{fabrikant_name}"
type: serie
ifc_class: "{ifc_class}"
ifc_predefined_type: "{ifc_pred}"{ifc_profile_line}
standard: "{hints.get('standard', '')}"{nl_sfb}
product_count: {product_count}
---
# {serie_name}

{description}
"""
    path = serie_dir / "_serie.md"
    return write_md(path, content, dry_run, overwrite)


def gen_product_md(product_name, serie_name, fabrikant_name, product_dir,
                   dry_run=False, overwrite=False):
    """Generate _product.md at product level."""
    hints = SERIES_HINTS.get(serie_name, {})
    ifc_class = hints.get("ifc_class", "IfcBuildingElementProxy")
    ifc_pred = hints.get("ifc_predefined_type", "USERDEFINED")

    if fabrikant_name == "Generic" and serie_name in NLSFB_BY_NAME:
        cat_id = NLSFB_BY_NAME[serie_name]
        ifc_class, ifc_pred = NLSFB_IFC.get(cat_id, (ifc_class, ifc_pred))

    # Count variants (DXF files)
    variant_count = sum(
        1 for f in product_dir.iterdir()
        if f.is_file() and f.suffix.lower() == '.dxf'
    ) if product_dir.is_dir() else 0

    nl_sfb_field = ""
    if fabrikant_name == "Generic" and serie_name in NLSFB_BY_NAME:
        nl_sfb_field = f'\nnl_sfb: "{NLSFB_BY_NAME[serie_name]}"'

    content = f"""---
name: "{product_name}"
serie: "{serie_name}"
fabrikant: "{fabrikant_name}"
type: product
ifc_class: "{ifc_class}"
ifc_predefined_type: "{ifc_pred}"{nl_sfb_field}
variant_count: {variant_count}
date_available: "current"
---
# {product_name}

{product_name} from {fabrikant_name} {serie_name}.
"""
    path = product_dir / "_product.md"
    return write_md(path, content, dry_run, overwrite)


def gen_variant_md(dxf_file, product_name, serie_name, fabrikant_name,
                   dry_run=False, overwrite=False):
    """Generate {variant}.md next to a DXF file."""
    variant_name = dxf_file.stem
    md_path = dxf_file.with_suffix('.md')
    svg_file = dxf_file.with_suffix('.svg').name

    content = f"""---
name: "{variant_name}"
product: "{product_name}"
serie: "{serie_name}"
fabrikant: "{fabrikant_name}"
type: variant
dxf_file: "{dxf_file.name}"
svg_file: "{svg_file}"
source_file: ""
date_added: "{TODAY}"
---
"""
    return write_md(md_path, content, dry_run, overwrite)


def process_tree(root_dir, tree_type="components", dry_run=False, overwrite=False):
    """Walk a component/details tree and generate MD files at every level."""
    if not root_dir.is_dir():
        print(f"  SKIP: {root_dir} not found")
        return 0, 0, 0, 0

    fab_count = 0
    serie_count = 0
    product_count = 0
    variant_count = 0

    # Level 1: Manufacturer folders
    for fab_dir in sorted(root_dir.iterdir()):
        if not fab_dir.is_dir() or fab_dir.name.startswith('.'):
            continue

        fabrikant_name = fab_dir.name
        if gen_fabrikant_md(fabrikant_name, fab_dir, dry_run, overwrite):
            fab_count += 1

        # Level 2: Series folders
        for serie_dir in sorted(fab_dir.iterdir()):
            if not serie_dir.is_dir() or serie_dir.name.startswith('_'):
                continue

            serie_name = serie_dir.name

            # Handle Community sub-manufacturers (Community/DXF-library/serie)
            if fabrikant_name == "Community":
                # serie_dir is actually the sub-source (DXF-library, dxfBlocks)
                sub_source = serie_dir.name
                for actual_serie_dir in sorted(serie_dir.iterdir()):
                    if not actual_serie_dir.is_dir() or actual_serie_dir.name.startswith('_'):
                        continue

                    actual_serie_name = actual_serie_dir.name
                    if gen_serie_md(actual_serie_name, f"{fabrikant_name}/{sub_source}",
                                    actual_serie_dir, dry_run, overwrite):
                        serie_count += 1

                    # Level 3: Products
                    for product_dir in sorted(actual_serie_dir.iterdir()):
                        if not product_dir.is_dir() or product_dir.name.startswith('_'):
                            continue

                        product_name = product_dir.name
                        if gen_product_md(product_name, actual_serie_name,
                                          f"{fabrikant_name}/{sub_source}",
                                          product_dir, dry_run, overwrite):
                            product_count += 1

                        # Level 4: Variants
                        for f in sorted(product_dir.iterdir()):
                            if f.is_file() and f.suffix.lower() == '.dxf':
                                if gen_variant_md(f, product_name, actual_serie_name,
                                                  f"{fabrikant_name}/{sub_source}",
                                                  dry_run, overwrite):
                                    variant_count += 1
                continue

            if gen_serie_md(serie_name, fabrikant_name, serie_dir, dry_run, overwrite):
                serie_count += 1

            # Level 3: Product folders
            for product_dir in sorted(serie_dir.iterdir()):
                if not product_dir.is_dir() or product_dir.name.startswith('_'):
                    continue

                product_name = product_dir.name
                if gen_product_md(product_name, serie_name, fabrikant_name,
                                  product_dir, dry_run, overwrite):
                    product_count += 1

                # Level 4: Variant files
                for f in sorted(product_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() == '.dxf':
                        if gen_variant_md(f, product_name, serie_name, fabrikant_name,
                                          dry_run, overwrite):
                            variant_count += 1

    return fab_count, serie_count, product_count, variant_count


def main():
    parser = argparse.ArgumentParser(description="Generate metadata MD files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing files")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing MD files")
    args = parser.parse_args()

    print("Generating metadata MD files...")
    if args.dry_run:
        print("(DRY RUN - no files will be written)")
    if args.overwrite:
        print("(OVERWRITE mode - existing MD files will be replaced)")
    print()

    # Process components/
    print("Processing components/...")
    c_fab, c_ser, c_prod, c_var = process_tree(
        COMPONENTS_DIR, "components", args.dry_run, args.overwrite
    )
    print(f"  Manufacturers: {c_fab}")
    print(f"  Series:        {c_ser}")
    print(f"  Products:      {c_prod}")
    print(f"  Variants:      {c_var}")

    # Process details/
    print()
    print("Processing details/...")
    d_fab, d_ser, d_prod, d_var = process_tree(
        DETAILS_DIR, "details", args.dry_run, args.overwrite
    )
    print(f"  Collections:   {d_fab}")
    print(f"  Series:        {d_ser}")
    print(f"  Details:       {d_prod}")
    print(f"  Variants:      {d_var}")

    total = (c_fab + c_ser + c_prod + c_var +
             d_fab + d_ser + d_prod + d_var)
    action = "Would generate" if args.dry_run else "Generated"
    print()
    print(f"{action} {total} MD files total")


if __name__ == "__main__":
    main()
