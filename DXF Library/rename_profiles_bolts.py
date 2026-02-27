"""
Rename steel profiles and capitalize bolt/nut M-sizes.

Steel profiles: 'staalprofielen ipe hea heb 2d heb700.dxf' -> 'HEB700.dxf'
Bolts/nuts: 'bout m10.dxf' -> 'bout M10.dxf', 'moer m6.dxf' -> 'moer M6.dxf'
"""
import re
from pathlib import Path


def rename_steel_profile(name: str) -> str | None:
    """Try to simplify a steel profile filename. Returns None if not a profile."""

    # IPE / HEA / HEB profiles
    m = re.match(r'staalprofielen ipe hea heb 2d (hea|heb|ipe)(\d+)', name)
    if m:
        return f'{m.group(1).upper()}{m.group(2)}'

    # UNP profiles
    m = re.match(r'staalprofielen unp 2d unp(\d+)', name)
    if m:
        return f'UNP{m.group(1)}'

    # UPE profiles
    m = re.match(r'staalprofielen upe 2d upe(\d+)', name)
    if m:
        return f'UPE{m.group(1)}'

    # NP profiles
    m = re.match(r'staalprofielen np profiel np (.+)', name)
    if m:
        dims = m.group(1).replace(' ', 'x')
        return f'NP{dims}'

    # SHS kokerprofielen (square): 'staalprofielen koker shs 2d k80 5'
    m = re.match(r'staalprofielen koker shs 2d k(.+)', name)
    if m:
        dims = m.group(1).strip()
        # Version suffix like 'v5' at end
        dims = re.sub(r'\s*v\d+$', '', dims)
        dims = dims.replace(' ', 'x')
        return f'SHS K{dims}'

    # RHS kokerprofielen (rectangular): 'staalprofielen koker rhs 2d k100 50 4'
    m = re.match(r'staalprofielen koker rhs 2d k(.+)', name)
    if m:
        dims = m.group(1).strip()
        dims = re.sub(r'\s*v\d+$', '', dims)
        dims = dims.replace(' ', 'x')
        return f'RHS K{dims}'

    # L profiles: 'staalprofielen l 2d l100 10'
    m = re.match(r'staalprofielen l 2d l(.+)', name)
    if m:
        dims = m.group(1).strip()
        dims = re.sub(r'\s*v\d+$', '', dims)
        dims = dims.replace(' ', 'x')
        return f'L{dims}'

    # Standalone L profile: 'staalprofielen l90 60 8'
    m = re.match(r'staalprofielen l(\d.+)', name)
    if m:
        dims = m.group(1).strip()
        dims = dims.replace(' ', 'x')
        return f'L{dims}'

    # DIN/DIE/DIL profiles: 'staalprofielen din die dill 2d die40'
    m = re.match(r'staalprofielen din die dill 2d (din|die|dil)(.+)', name)
    if m:
        ptype = m.group(1).upper()
        dims = m.group(2).strip()
        dims = re.sub(r'\s*v\d+$', '', dims)
        dims = dims.replace(' ', 'x')
        return f'{ptype}{dims}'

    # B profile: 'staalprofielen b profiel b 100'
    m = re.match(r'staalprofielen b profiel b (.+)', name)
    if m:
        return f'B{m.group(1).strip()}'

    return None


def capitalize_bolt_sizes(name: str) -> str:
    """Capitalize M in bolt/nut size designations: m6 -> M6, m10 -> M10."""
    return re.sub(r'\bm(\d+)', r'M\1', name)


def main():
    componenten_dir = Path(r"C:\Users\rickd\Documents\GitHub\Project-Ocondat\DXF Library\Componenten")
    staal_dir = componenten_dir / "28 Staalconstructie"

    renamed = 0
    errors = 0

    # --- 1. Rename steel profiles ---
    print("=== Staalprofielen hernoemen ===")
    dxf_files = sorted(staal_dir.glob("*.dxf"))

    # First pass: compute new names and handle collisions
    rename_map = {}
    new_names_seen = {}

    for f in dxf_files:
        old_stem = f.stem
        new_stem = rename_steel_profile(old_stem)

        if new_stem is None:
            continue  # Not a profile, skip

        # Handle collisions
        if new_stem in new_names_seen:
            new_names_seen[new_stem] += 1
            new_stem = f"{new_stem} ({new_names_seen[new_stem]})"
        else:
            new_names_seen[new_stem] = 0

        rename_map[f] = f.parent / f"{new_stem}.dxf"

    for old_path, new_path in rename_map.items():
        print(f"  {old_path.name:<60} -> {new_path.name}")
        try:
            old_path.rename(new_path)
            renamed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1

    print(f"\n  Profielen hernoemd: {renamed}")

    # --- 2. Capitalize M in bolt/nut sizes across ALL folders ---
    print("\n=== Bout/moer M-maten capitaliseren ===")
    bolt_renamed = 0

    for cat_dir in sorted(componenten_dir.iterdir()):
        if not cat_dir.is_dir():
            continue

        for f in sorted(cat_dir.glob("*.dxf")):
            old_stem = f.stem
            new_stem = capitalize_bolt_sizes(old_stem)

            if new_stem != old_stem:
                new_path = f.parent / f"{new_stem}.dxf"
                print(f"  {old_stem}.dxf -> {new_stem}.dxf")
                try:
                    f.rename(new_path)
                    bolt_renamed += 1
                except Exception as e:
                    print(f"  ERROR: {e}")
                    errors += 1

    print(f"\n  Bout/moer hernoemd: {bolt_renamed}")
    print(f"\nTotaal hernoemd: {renamed + bolt_renamed}, Fouten: {errors}")


if __name__ == "__main__":
    main()
