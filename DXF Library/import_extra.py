"""
Import DXF components from folders 001-004 into the Componenten structure.

001 Vloeren            -> Componenten/23 Vloeren/
002 Aluminium kozijnen -> Componenten/32 Kozijnen/
003 Kunststeen onderdorpel -> Componenten/32 Kozijnen/
004 Sandwichpanelen    -> Componenten/41 Gevelafwerking/
"""
import shutil
from pathlib import Path

BASE = Path(r"C:\Users\rickd\Documents\GitHub\Project-Ocondat\DXF Library")
COMP = BASE / "Componenten"


def clean_vloer_name(filepath: Path) -> str:
    """Clean VBI vloer filenames to lowercase, consistent style."""
    name = filepath.stem.lower()
    # "vbi isolatieplaatvloer h200 standaard" -> keep as is, already clean
    # Fix typo "randoplogging" -> "randoplegging"
    name = name.replace("randoplogging", "randoplegging")
    return name


def clean_kozijn_name(filepath: Path) -> str:
    """Clean Reynaers kozijn filenames."""
    name = filepath.stem.lower()
    # Remove "reynaers aluminium " prefix - redundant since they're in kozijnen folder
    name = name.replace("reynaers aluminium ", "reynaers ")
    return name


def clean_sandwichpaneel_name(filepath: Path) -> str:
    """Clean sandwichpaneel filenames."""
    name = filepath.stem.lower()
    return f"sandwichpaneel {name}"


def copy_files(source_dir: Path, dest_dir: Path, clean_func, recursive=True):
    """Copy DXF files from source to dest, applying name cleaning."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    if recursive:
        files = sorted(source_dir.rglob("*.dxf"))
    else:
        files = sorted(source_dir.glob("*.dxf"))

    copied = 0
    seen = {}

    for f in files:
        new_name = clean_func(f)

        # Handle collisions
        if new_name in seen:
            seen[new_name] += 1
            new_name = f"{new_name} ({seen[new_name]})"
        else:
            seen[new_name] = 0

        dest_path = dest_dir / f"{new_name}.dxf"
        shutil.copy2(str(f), str(dest_path))
        print(f"  {f.name:<65} -> {new_name}.dxf")
        copied += 1

    return copied


def main():
    total = 0

    # 001 Vloeren -> 23 Vloeren
    print("=== 001 Vloeren -> 23 Vloeren ===")
    total += copy_files(
        BASE / "001 Vloeren",
        COMP / "23 Vloeren",
        clean_vloer_name,
    )

    # 002 Aluminium kozijnen -> 32 Kozijnen
    print("\n=== 002 Aluminium kozijnen -> 32 Kozijnen ===")
    total += copy_files(
        BASE / "002 Aluminium kozijnen",
        COMP / "32 Kozijnen",
        clean_kozijn_name,
    )

    # 003 Kunststeen onderdorpel -> 32 Kozijnen
    print("\n=== 003 Kunststeen onderdorpel -> 32 Kozijnen ===")
    total += copy_files(
        BASE / "003 Kunststeen onderdorpel",
        COMP / "32 Kozijnen",
        lambda f: f.stem.lower(),
    )

    # 004 Sandwichpanelen -> 41 Gevelafwerking
    print("\n=== 004 Sandwichpanelen -> 41 Gevelafwerking ===")
    total += copy_files(
        BASE / "004 Sandwichpanelen",
        COMP / "41 Gevelafwerking",
        clean_sandwichpaneel_name,
    )

    print(f"\nKlaar! {total} bestanden gekopieerd.")


if __name__ == "__main__":
    main()
