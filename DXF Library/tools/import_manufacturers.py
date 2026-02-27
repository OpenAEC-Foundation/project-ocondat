"""Sort DXF/DWG files into the Fabrikant/Serie/Product/Variant hierarchy.

Reads source directories and copies files into:
  components/{fabrikant}/{serie}/{product}/{variant}.dxf
  details/{collection}/{serie}/{detail}.dxf

Usage:
    python tools/import_manufacturers.py              # Run the import
    python tools/import_manufacturers.py --dry-run     # Preview without copying
    python tools/import_manufacturers.py --clean       # Remove components/ and details/ first
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Output directories
COMPONENTS_DIR = BASE / "components"
DETAILS_DIR = BASE / "details"

# Source directories
COMPONENTEN = BASE / "Componenten"
DOWNLOADS = BASE / "Downloads"
STAGING = BASE / "_staging_dxf"  # DWG->DXF converted files


def safe_name(name, max_len=60):
    """Normalize a name for use as directory/file name.
    Keeps case, replaces spaces with hyphens, removes problematic chars."""
    s = name.strip()
    s = s.replace(' ', '-')
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    # Collapse multiple hyphens
    s = re.sub(r'-{2,}', '-', s)
    s = s.strip('-')
    if len(s) > max_len:
        s = s[:max_len].rstrip('-')
    return s


def safe_filename(name, max_len=60):
    """Create a safe filename (lowercase), truncated to max_len."""
    s = name.lower().strip()
    s = s.replace(' ', '-')
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = re.sub(r'-{2,}', '-', s)
    s = s.strip('-')
    if len(s) > max_len:
        s = s[:max_len].rstrip('-')
    return s


def copy_file(src, dst, dry_run=False):
    """Copy a file, creating parent directories as needed."""
    if dry_run:
        return
    os.makedirs(dst.parent, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


# ── NL-SfB category mapping (from existing Componenten/ folder names) ──────
NLSFB_CATEGORIES = {
    "00": "Basismaterialen",
    "16": "Funderingspalen",
    "17": "Palen",
    "20": "Ankers-en-verbindingen",
    "21": "Wanden-metselwerk",
    "22": "Wanden-blokken",
    "23": "Vloeren",
    "27": "Dakbedekking",
    "28": "Staalconstructie",
    "30": "Glas-en-gevelbekleding",
    "31": "Ramen-en-deuren",
    "32": "Kozijnen",
    "33": "Sparingen",
    "34": "Diversen-bent",
    "35": "Kantlatten",
    "37": "Diversen-DI",
    "40": "Vloerplaten-en-afwerking",
    "41": "Gevelafwerking",
    "42": "Afwerkprofielen",
    "43": "Vloer-en-wandafwerking",
    "45": "Plafonds",
    "47": "Dakdetails",
    "52": "Hemelwaterafvoer",
    "90": "Bestrating",
    "91": "Overig",
}


# ── ArcelorMittal series mapping ──────────────────────────────────────────
ARCELOR_SERIES = {
    "HD_dwg": "HD-profielen",
    "HE_dwg": "HE-profielen",
    "HL_dwg": "HL-profielen",
    "IPE_dwg": "IPE-profielen",
    "IPN_dwg": "IPN-profielen",
    "L_Sections": "L-profielen",
    "SheetPiles_dxf": "Damwandprofielen",
    "UB_Sections_dwg": "UB-profielen",
    "UC_Sections_dwg": "UC-profielen",
    "UPE_dwg": "UPE-profielen",
    "UPN_dwg": "UPN-profielen",
    "W_Sections_dwg": "W-profielen",
}


# ── Halfen top-level product mapping ──────────────────────────────────────
HALFEN_SERIES = {
    "ba_dxf": "Bodyanker-BA",
    "hcw_dxf": "Curtain-Wall-HCW",
    "hit_sp_dxf": "HIT-Verbindungen",
    "hta_dxf": "Ankerschienen-HTA",
    "sof_dxf": "Deckenanker-SOF",
    "uk_dxf": "Konsolen-UK",
    "zub_a_dxf": "Zubehoer-A",
    "zub_b_dxf": "Zubehoer-B",
    "zub_m_dxf": "Zubehoer-M",
}


# ── Empty download folders (failed scrapes) to skip ──────────────────────
EMPTY_DOWNLOADS = {
    "Fischer", "Gyproc", "Hilti", "Kawneer", "Kingspan",
    "Knauf", "Reynaers", "Rockwool", "Schueco", "TataSteel", "Wavin",
    "Wienerberger",
}


def find_cad_files(directory, extensions=('.dxf',)):
    """Find all CAD files in a directory tree."""
    files = []
    if not directory.is_dir():
        return files
    for root, _dirs, filenames in os.walk(directory):
        for f in filenames:
            if any(f.lower().endswith(ext) for ext in extensions):
                files.append(Path(root) / f)
    return sorted(files)


def infer_product_name(filename):
    """Extract product name from a DXF/DWG filename."""
    name = Path(filename).stem
    # Remove common prefixes/suffixes
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)  # trailing (1), (2)
    return name


def import_componenten(dry_run=False):
    """Import existing Componenten/ files as Generic manufacturer."""
    if not COMPONENTEN.is_dir():
        print("  SKIP: Componenten/ not found")
        return 0

    count = 0
    folders = sorted([
        d for d in os.listdir(COMPONENTEN)
        if os.path.isdir(COMPONENTEN / d) and re.match(r'^\d{2}\s', d)
    ])

    for folder in folders:
        cat_id = folder[:2]
        serie_name = NLSFB_CATEGORIES.get(cat_id, safe_name(folder))
        folder_path = COMPONENTEN / folder

        dxf_files = sorted([
            f for f in os.listdir(folder_path)
            if f.lower().endswith('.dxf')
        ])

        for dxf_file in dxf_files:
            src = folder_path / dxf_file
            product_name = infer_product_name(dxf_file)

            # For Generic: serie = NL-SfB category, product = filename
            # Remove leading "NN x " prefix from product name (e.g. "00 g ")
            clean_name = re.sub(r'^\d{2}\s+[a-z]\s+', '', product_name)
            if not clean_name:
                clean_name = product_name

            product_dir = safe_name(clean_name)
            variant_name = safe_filename(clean_name)

            dst = COMPONENTS_DIR / "Generic" / serie_name / product_dir / f"{variant_name}.dxf"
            copy_file(src, dst, dry_run)
            count += 1

    return count


def import_arcelormittal(dry_run=False):
    """Import ArcelorMittal downloads."""
    am_dir = DOWNLOADS / "ArcelorMittal"
    if not am_dir.is_dir():
        print("  SKIP: Downloads/ArcelorMittal not found")
        return 0

    count = 0
    for series_folder in sorted(os.listdir(am_dir)):
        if series_folder.endswith('.zip'):
            continue
        series_path = am_dir / series_folder
        if not series_path.is_dir():
            continue

        serie_name = ARCELOR_SERIES.get(series_folder, safe_name(series_folder))

        # Find all DWG and DXF files (may be in subdirs)
        cad_files = find_cad_files(series_path, extensions=('.dwg', '.dxf'))

        # Also check staging for converted files
        staging_series = STAGING / "Downloads" / "ArcelorMittal" / series_folder
        if staging_series.is_dir():
            cad_files.extend(find_cad_files(staging_series, extensions=('.dxf',)))

        for cad_file in cad_files:
            product_name = infer_product_name(cad_file.name)
            # Normalize: "HE 100 A" -> "HE100A"
            compact_name = re.sub(r'\s+', '', product_name).upper()
            product_dir = compact_name
            variant_name = compact_name.lower()

            ext = cad_file.suffix.lower()
            if ext == '.dwg':
                # Check if a converted DXF exists in staging
                dxf_name = cad_file.stem + '.dxf'
                staging_file = staging_series
                if staging_series.is_dir():
                    # Walk staging to find the converted file
                    for root, _dirs, files in os.walk(staging_series):
                        for f in files:
                            if f.lower() == dxf_name.lower():
                                cad_file = Path(root) / f
                                ext = '.dxf'
                                break
                if ext == '.dwg':
                    continue  # Skip unconverted DWG files

            dst = COMPONENTS_DIR / "ArcelorMittal" / serie_name / product_dir / f"{variant_name}.dxf"
            copy_file(cad_file, dst, dry_run)
            count += 1

    return count


def import_halfen(dry_run=False):
    """Import Halfen downloads (deeply nested structure)."""
    halfen_dir = DOWNLOADS / "Halfen"
    if not halfen_dir.is_dir():
        print("  SKIP: Downloads/Halfen not found")
        return 0

    count = 0
    for top_folder in sorted(os.listdir(halfen_dir)):
        if top_folder.endswith('.zip'):
            continue
        top_path = halfen_dir / top_folder
        if not top_path.is_dir():
            continue

        serie_name = HALFEN_SERIES.get(top_folder, safe_name(top_folder))

        # Find all DXF files recursively
        dxf_files = find_cad_files(top_path, extensions=('.dxf',))

        for dxf_file in dxf_files:
            product_name = infer_product_name(dxf_file.name)
            # Use the parent folder name as product group
            parent_dir = dxf_file.parent.name

            # Clean up the product name
            clean_product = safe_name(product_name)
            product_dir = safe_name(parent_dir) if parent_dir != top_folder else clean_product
            variant_name = safe_filename(product_name)

            dst = COMPONENTS_DIR / "Halfen" / serie_name / product_dir / f"{variant_name}.dxf"
            copy_file(dxf_file, dst, dry_run)
            count += 1

    return count


def import_dxf_library(dry_run=False):
    """Import DXF-library (interior/exterior blocks)."""
    lib_dir = DOWNLOADS / "DXF-library" / "DXF-library-master"
    if not lib_dir.is_dir():
        print("  SKIP: Downloads/DXF-library not found")
        return 0

    count = 0
    for category in sorted(os.listdir(lib_dir)):
        cat_path = lib_dir / category
        if not cat_path.is_dir():
            continue

        serie_name = safe_name(category)
        dxf_files = find_cad_files(cat_path, extensions=('.dxf',))

        for dxf_file in dxf_files:
            product_name = infer_product_name(dxf_file.name)
            product_dir = safe_name(product_name)
            variant_name = safe_filename(product_name)

            dst = COMPONENTS_DIR / "Community" / "DXF-library" / serie_name / product_dir / f"{variant_name}.dxf"
            copy_file(dxf_file, dst, dry_run)
            count += 1

    return count


def import_dxfblocks(dry_run=False):
    """Import dxfBlocks (architecture blocks, CC-BY-NC-SA 4.0)."""
    blocks_dir = DOWNLOADS / "dxfBlocks" / "dxfBlocks-master"
    if not blocks_dir.is_dir():
        print("  SKIP: Downloads/dxfBlocks not found")
        return 0

    count = 0
    for category in sorted(os.listdir(blocks_dir)):
        cat_path = blocks_dir / category
        if not cat_path.is_dir():
            continue

        serie_name = safe_name(category)
        dxf_files = find_cad_files(cat_path, extensions=('.dxf',))

        for dxf_file in dxf_files:
            product_name = infer_product_name(dxf_file.name)
            product_dir = safe_name(product_name)
            variant_name = safe_filename(product_name)

            dst = COMPONENTS_DIR / "Community" / "dxfBlocks" / serie_name / product_dir / f"{variant_name}.dxf"
            copy_file(dxf_file, dst, dry_run)
            count += 1

    return count


def import_dwgmodels(dry_run=False):
    """Import DwgModels downloads."""
    models_dir = DOWNLOADS / "DwgModels"
    if not models_dir.is_dir():
        print("  SKIP: Downloads/DwgModels not found")
        return 0

    count = 0
    # These are mostly .dwg files - check staging for converted versions
    for f in sorted(os.listdir(models_dir)):
        fpath = models_dir / f
        if not fpath.is_file():
            continue

        stem = Path(f).stem
        ext = Path(f).suffix.lower()

        # Try staging first for DWG files
        if ext == '.dwg':
            staging_file = STAGING / "Downloads" / "DwgModels" / (stem + '.dxf')
            if staging_file.is_file():
                fpath = staging_file
                ext = '.dxf'
            else:
                continue  # Skip unconverted DWG

        if ext != '.dxf':
            continue

        product_name = safe_name(stem)
        variant_name = safe_filename(stem)

        dst = COMPONENTS_DIR / "DwgModels" / "Diverse" / product_name / f"{variant_name}.dxf"
        copy_file(fpath, dst, dry_run)
        count += 1

    return count


def import_geberit(dry_run=False):
    """Import Geberit downloads."""
    geb_dir = DOWNLOADS / "Geberit"
    if not geb_dir.is_dir():
        print("  SKIP: Downloads/Geberit not found")
        return 0

    count = 0
    cad_files = find_cad_files(geb_dir, extensions=('.dwg', '.dxf'))

    # Check staging
    staging_geb = STAGING / "Downloads" / "Geberit"
    if staging_geb.is_dir():
        cad_files.extend(find_cad_files(staging_geb, extensions=('.dxf',)))

    for cad_file in cad_files:
        ext = cad_file.suffix.lower()
        if ext == '.dwg':
            # Check staging
            dxf_name = cad_file.stem + '.dxf'
            if staging_geb.is_dir():
                for f in os.listdir(staging_geb):
                    if f.lower() == dxf_name.lower():
                        cad_file = staging_geb / f
                        ext = '.dxf'
                        break
            if ext == '.dwg':
                continue

        stem = cad_file.stem
        product_name = safe_name(stem)
        variant_name = safe_filename(stem)

        dst = COMPONENTS_DIR / "Geberit" / "Sanitair" / product_name / f"{variant_name}.dxf"
        copy_file(cad_file, dst, dry_run)
        count += 1

    return count


def print_summary(results, dry_run=False):
    """Print import summary."""
    total = sum(results.values())
    action = "Would import" if dry_run else "Imported"

    print()
    print(f"{'=' * 50}")
    print(f"  {action} {total} files total")
    print(f"{'=' * 50}")
    for source, count in sorted(results.items()):
        if count > 0:
            print(f"  {source:30s} {count:>6d}")
    print(f"{'=' * 50}")
    print()
    if not dry_run:
        print(f"  Components: {COMPONENTS_DIR}")
        print(f"  Details:    {DETAILS_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Import files into manufacturer hierarchy")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview file sorting without copying")
    parser.add_argument("--clean", action="store_true",
                        help="Remove existing components/ and details/ before importing")
    parser.add_argument("--source", type=str, default=None,
                        help="Only import from specific source (e.g. 'ArcelorMittal')")
    args = parser.parse_args()

    if args.clean and not args.dry_run:
        print("Cleaning existing output directories...")
        if COMPONENTS_DIR.is_dir():
            shutil.rmtree(COMPONENTS_DIR)
            print(f"  Removed {COMPONENTS_DIR}")
        if DETAILS_DIR.is_dir():
            shutil.rmtree(DETAILS_DIR)
            print(f"  Removed {DETAILS_DIR}")
        print()

    if not args.dry_run:
        os.makedirs(COMPONENTS_DIR, exist_ok=True)
        os.makedirs(DETAILS_DIR, exist_ok=True)

    print("Importing files into manufacturer hierarchy...")
    if args.dry_run:
        print("(DRY RUN - no files will be copied)")
    print()

    results = {}

    importers = {
        "Componenten (Generic)": import_componenten,
        "ArcelorMittal": import_arcelormittal,
        "Halfen": import_halfen,
        "DXF-library": import_dxf_library,
        "dxfBlocks": import_dxfblocks,
        "DwgModels": import_dwgmodels,
        "Geberit": import_geberit,
    }

    for name, importer in importers.items():
        if args.source and args.source.lower() not in name.lower():
            continue
        print(f"  [{name}]")
        results[name] = importer(dry_run=args.dry_run)
        print(f"    -> {results[name]} files")

    print_summary(results, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
