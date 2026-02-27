"""
Rename all exported block DXF files in the Componenten folder.

Removes:
- Prefix numbers (00, 28, etc.)
- Suffix codes (-1234567-00_0 Basismaterialen)
- Underscores and dashes (replaced by spaces)
- View abbreviations: 's e', 'a e', 's l' (CAD view designations)
- Inconsistent capitalization (everything lowercase)
- Deduplication of repeated description/variant parts
"""
import re
from pathlib import Path


def clean_name(name: str) -> str:
    """Clean a block name for use as a readable filename."""

    # 1. Remove leading two-digit category prefix + space or underscore
    name = re.sub(r'^\d{2}\s+', '', name)
    name = re.sub(r'^\d{2}_', '', name)

    # 2. Remove suffix: -DIGITS_DIGITS WORD at end (e.g. -00_0 Basismaterialen)
    name = re.sub(r'-\d+_\d+\s+\w+$', '', name)
    name = re.sub(r'-\d+_\d+$', '', name)

    # 3. Split on ' - ' to separate description from variant+id
    if ' - ' in name:
        desc, variant = name.split(' - ', 1)

        # Remove trailing numeric ID from variant (6+ digit codes)
        variant = re.sub(r'-\d{6,}$', '', variant)

        # Remove leading category prefix from variant:
        # - 'NN DI ...' pattern
        # - 'NN_...' pattern (category prefix with underscore)
        # - 'NNWord...' pattern (digits glued to capitalized word, e.g. '31Solarlux')
        # But NOT dimensions like '40x40', '12x55', '70mm'
        variant = re.sub(r'^\d{2}\s+DI\s+', '', variant)
        variant = re.sub(r'^\d{2}_', '', variant)
        variant = re.sub(r'^\d{2}(?=[A-Z][a-z])', '', variant)

        # Remove view abbreviations from desc and variant ends
        desc = re.sub(r'\s+[aesl]\s+[aesl]\s*$', '', desc)
        variant = re.sub(r'\s+[aesl]\s+[aesl]\s*$', '', variant)

        # Normalize for deduplication
        def norm(s):
            return re.sub(r'[\s_\-]+', '', s).lower()

        d_norm = norm(desc)
        v_norm = norm(variant)

        if not v_norm or v_norm == d_norm:
            combined = desc
        elif v_norm in d_norm or d_norm in v_norm:
            combined = variant if len(v_norm) > len(d_norm) else desc
        else:
            combined = f'{desc} {variant}'
    else:
        combined = re.sub(r'-\d{6,}$', '', name)

    # 4. Replace underscores and dashes with spaces
    combined = combined.replace('_', ' ').replace('-', ' ')

    # 5. Remove remaining view abbreviation patterns anywhere
    #    Patterns like ' s l ', ' a e ', ' s e ' (two single letters from [aesl])
    combined = re.sub(r'\s+[aesl]\s+[aesl]\s*$', '', combined)
    combined = re.sub(r'\s+[aesl]\s+[aesl]\s+', ' ', combined)

    # 6. Lowercase everything
    combined = combined.lower()

    # 7. Clean up whitespace
    combined = re.sub(r'\s+', ' ', combined).strip()

    return combined


def main():
    componenten_dir = Path(r"C:\Users\rickd\Documents\GitHub\Project-Ocondat\DXF Library\Componenten")

    if not componenten_dir.exists():
        print("Componenten folder not found!")
        return

    total = 0
    renamed = 0
    skipped = 0
    collisions = 0

    for cat_dir in sorted(componenten_dir.iterdir()):
        if not cat_dir.is_dir():
            continue

        print(f"\n[{cat_dir.name}]")
        dxf_files = sorted(cat_dir.glob("*.dxf"))

        # First pass: compute all new names and check for collisions
        rename_map = {}
        new_names_seen = {}

        for dxf_file in dxf_files:
            old_name = dxf_file.stem
            new_name = clean_name(old_name)

            # Handle collisions by appending a number
            if new_name in new_names_seen:
                new_names_seen[new_name] += 1
                new_name = f"{new_name} ({new_names_seen[new_name]})"
                collisions += 1
            else:
                new_names_seen[new_name] = 0

            rename_map[dxf_file] = cat_dir / f"{new_name}.dxf"

        # Second pass: actually rename
        for old_path, new_path in rename_map.items():
            total += 1
            if old_path == new_path:
                skipped += 1
                continue

            try:
                old_path.rename(new_path)
                renamed += 1
            except Exception as e:
                print(f"  ERROR: {old_path.name} -> {new_path.name}: {e}")

    print(f"\nDone!")
    print(f"  Total:      {total}")
    print(f"  Renamed:    {renamed}")
    print(f"  Unchanged:  {skipped}")
    print(f"  Collisions: {collisions} (resolved with numbering)")


if __name__ == "__main__":
    main()
