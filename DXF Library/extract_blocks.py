"""
Extract all blocks from 2025-componenten.dxf and save as individual DXF files,
grouped by category (prefix number).

Skips internal dimension blocks (DIMBLOCK*) and other non-component blocks.
"""
import ezdxf
import ezdxf.addons.importer
import re
import shutil
import sys
from pathlib import Path

# Category names based on prefix numbers (NL-SfB-style classification)
CATEGORY_NAMES = {
    "00": "00 Basismaterialen",
    "16": "16 Funderingspalen",
    "17": "17 Palen",
    "20": "20 Ankers en verbindingen",
    "21": "21 Wanden - metselwerk",
    "22": "22 Wanden - blokken",
    "23": "23 Vloeren",
    "27": "27 Dakbedekking",
    "28": "28 Staalconstructie",
    "30": "30 Glas en gevelbekleding",
    "31": "31 Ramen en deuren",
    "32": "32 Kozijnen",
    "33": "33 Sparingen",
    "34": "34 Diversen - bent",
    "35": "35 Kantlatten",
    "37": "37 Diversen - DI",
    "40": "40 Vloerplaten en afwerking",
    "41": "41 Gevelafwerking",
    "42": "42 Afwerkprofielen",
    "43": "43 Vloer- en wandafwerking",
    "45": "45 Plafonds",
    "47": "47 Dakdetails",
    "52": "52 Hemelwaterafvoer",
    "90": "90 Bestrating",
    "91": "91 Overig",
}

# Block name prefixes to skip (not real detail components)
SKIP_PREFIXES = (
    "DIMBLOCK",
    "_Dot",
    "Repeating",
    "Family",
    "NLRS_",
)


def sanitize_filename(name: str) -> str:
    """Make a block name safe for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.rstrip('. ')
    if len(name) > 200:
        name = name[:200]
    return name


def is_component_block(block_name: str) -> bool:
    """Return True if this is a real detail component, not an internal/system block."""
    if block_name.startswith('*'):
        return False
    for prefix in SKIP_PREFIXES:
        if block_name.startswith(prefix):
            return False
    return True


def get_category(block_name: str) -> str:
    """Extract category folder name from block name prefix.

    Handles both 'NN description' and 'NN_description' patterns.
    """
    # Try splitting on space first: "28 Staalprofielen ..."
    match = re.match(r'^(\d{2})[\s_]', block_name)
    if match:
        prefix = match.group(1)
        if prefix in CATEGORY_NAMES:
            return CATEGORY_NAMES[prefix]
    return "99 Overig"


def extract_block_to_dxf(source_doc, block, output_path: Path):
    """Extract a single block definition and save as a new DXF file."""
    new_doc = ezdxf.new(dxfversion=source_doc.dxfversion)
    importer = ezdxf.addons.importer.Importer(source_doc, new_doc)
    importer.import_block(block.name)
    importer.finalize()

    # Add INSERT in modelspace so the block is visible when opened
    msp = new_doc.modelspace()
    try:
        msp.add_blockref(block.name, insert=(0, 0, 0))
    except Exception:
        pass

    new_doc.saveas(str(output_path))


def main():
    source_file = Path(r"C:\Users\rickd\Documents\GitHub\Project-Ocondat\DXF Library\2025-componenten.dxf")
    output_dir = Path(r"C:\Users\rickd\Documents\GitHub\Project-Ocondat\DXF Library\Componenten")

    # Clean previous output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    print(f"Reading: {source_file}")
    doc = ezdxf.readfile(str(source_file))

    # Filter to real component blocks only
    all_blocks = [b for b in doc.blocks if is_component_block(b.name)]
    skipped = [b.name for b in doc.blocks if not b.name.startswith('*') and not is_component_block(b.name)]
    print(f"Total blocks: {len(all_blocks)} components, {len(skipped)} skipped (DIMBLOCK/system)")

    # Group by category
    categories = {}
    for block in all_blocks:
        cat = get_category(block.name)
        categories.setdefault(cat, []).append(block)

    print(f"\nCategories: {len(categories)}")
    for cat in sorted(categories.keys()):
        print(f"  {cat}: {len(categories[cat])} blocks")

    # Export
    total = len(all_blocks)
    exported = 0
    errors = 0

    for cat_name in sorted(categories.keys()):
        cat_blocks = categories[cat_name]
        cat_dir = output_dir / cat_name
        cat_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n  [{cat_name}] Exporting {len(cat_blocks)} blocks...")

        for block in cat_blocks:
            safe_name = sanitize_filename(block.name)
            output_path = cat_dir / f"{safe_name}.dxf"

            try:
                extract_block_to_dxf(doc, block, output_path)
                exported += 1
                if exported % 100 == 0:
                    print(f"    Progress: {exported}/{total} ({exported*100//total}%)")
            except Exception as e:
                errors += 1
                print(f"    ERROR '{block.name}': {e}", file=sys.stderr)

    print(f"\nDone!")
    print(f"  Exported: {exported}/{total}")
    print(f"  Errors:   {errors}")
    print(f"  Output:   {output_dir}")


if __name__ == "__main__":
    main()
