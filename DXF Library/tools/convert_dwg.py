"""Convert DWG files to DXF using ODA File Converter.

Scans Downloads/ and 3BM/ directories for .dwg files and converts
them to .dxf format in a staging directory.

Requirements:
    - ODA File Converter (free): https://www.opendesign.com/guestfiles/oda_file_converter
    - Must be installed and accessible via command line or at default location

Usage:
    python tools/convert_dwg.py                    # Convert all DWG files
    python tools/convert_dwg.py --dry-run           # Preview without converting
    python tools/convert_dwg.py --source Downloads   # Convert only from Downloads/
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
STAGING = BASE / "_staging_dxf"

# Directories to scan for DWG files
SCAN_DIRS = [
    BASE / "Downloads",
]

# Common ODA File Converter locations
ODA_PATHS = [
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter 25.12\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter 26.1\ODAFileConverter.exe",
    "/usr/bin/ODAFileConverter",
    "/usr/local/bin/ODAFileConverter",
]


def find_oda_converter():
    """Find ODA File Converter executable."""
    # Check PATH first
    oda = shutil.which("ODAFileConverter")
    if oda:
        return oda

    # Check common locations
    for path in ODA_PATHS:
        if os.path.isfile(path):
            return path

    return None


def find_dwg_files(scan_dirs):
    """Recursively find all .dwg files in scan directories."""
    dwg_files = []
    for scan_dir in scan_dirs:
        if not scan_dir.is_dir():
            print(f"  SKIP: {scan_dir} (not found)")
            continue
        for root, _dirs, files in os.walk(scan_dir):
            for f in files:
                if f.lower().endswith('.dwg'):
                    dwg_files.append(Path(root) / f)
    return sorted(dwg_files)


def convert_batch_oda(oda_exe, input_dir, output_dir):
    """Convert all DWG files in input_dir to DXF in output_dir using ODA.

    ODA File Converter works on directories, not individual files.
    Arguments: InputFolder OutputFolder OutputVersion OutputType RecurseFlag AuditFlag
    OutputVersion: "ACAD2018" for R2018 DXF
    OutputType: "DXF" for ASCII DXF, "DXB" for binary
    """
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        oda_exe,
        str(input_dir),
        str(output_dir),
        "ACAD2018",   # Output version
        "DXF",        # Output type (ASCII DXF)
        "0",          # Recurse into subdirs: 0=no, 1=yes
        "1",          # Audit: 1=yes
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout per batch
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT: Conversion timed out for {input_dir}")
        return False
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def convert_all(scan_dirs, dry_run=False):
    """Main conversion pipeline."""
    oda_exe = find_oda_converter()

    if not oda_exe and not dry_run:
        print("ERROR: ODA File Converter not found.")
        print("Download from: https://www.opendesign.com/guestfiles/oda_file_converter")
        print("Install and ensure it's in PATH or at a standard location.")
        print()
        print("Run with --dry-run to see which files would be converted.")
        sys.exit(1)

    if oda_exe:
        print(f"ODA File Converter: {oda_exe}")
    else:
        print("ODA File Converter: NOT FOUND (dry-run mode)")
    print()

    # Find all DWG files
    print("Scanning for DWG files...")
    dwg_files = find_dwg_files(scan_dirs)
    print(f"Found {len(dwg_files)} DWG files")
    print()

    if not dwg_files:
        print("No DWG files to convert.")
        return

    # Group by parent directory (ODA works on directories)
    dir_groups = {}
    for dwg in dwg_files:
        parent = dwg.parent
        if parent not in dir_groups:
            dir_groups[parent] = []
        dir_groups[parent].append(dwg)

    if dry_run:
        print("DRY RUN - Files that would be converted:")
        print("-" * 60)
        for dir_path, files in sorted(dir_groups.items()):
            rel = dir_path.relative_to(BASE) if dir_path.is_relative_to(BASE) else dir_path
            print(f"\n  {rel}/ ({len(files)} files)")
            for f in files[:5]:
                print(f"    {f.name}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")
        print()
        print(f"Total: {len(dwg_files)} DWG files in {len(dir_groups)} directories")
        print(f"Output would go to: {STAGING}")
        return

    # Create staging directory
    os.makedirs(STAGING, exist_ok=True)
    converted = 0
    failed = 0

    for dir_path, files in sorted(dir_groups.items()):
        rel = dir_path.relative_to(BASE) if dir_path.is_relative_to(BASE) else dir_path
        # Create matching output directory structure
        out_dir = STAGING / rel
        os.makedirs(out_dir, exist_ok=True)

        print(f"Converting {rel}/ ({len(files)} files)...")

        # ODA converts entire directories, so we use it directly
        success = convert_batch_oda(oda_exe, str(dir_path), str(out_dir))

        if success:
            # Count actually created DXF files
            created = [f for f in os.listdir(out_dir) if f.lower().endswith('.dxf')]
            converted += len(created)
            print(f"  -> {len(created)} DXF files created")
        else:
            failed += len(files)
            print(f"  -> FAILED ({len(files)} files)")

    print()
    print(f"Conversion complete:")
    print(f"  Converted: {converted}")
    print(f"  Failed: {failed}")
    print(f"  Output: {STAGING}")


def main():
    parser = argparse.ArgumentParser(description="Convert DWG files to DXF")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview files without converting")
    parser.add_argument("--source", type=str, default=None,
                        help="Only convert from specific source directory")
    parser.add_argument("--output", type=str, default=None,
                        help="Override output staging directory")
    args = parser.parse_args()

    global STAGING
    if args.output:
        STAGING = Path(args.output)

    if args.source:
        source_path = BASE / args.source
        if not source_path.is_dir():
            print(f"ERROR: Source directory not found: {source_path}")
            sys.exit(1)
        scan_dirs = [source_path]
    else:
        scan_dirs = [d for d in SCAN_DIRS if d.is_dir()]

    convert_all(scan_dirs, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
