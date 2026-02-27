import os, json

base = 'C:\\Users\\rickd\\Documents\\GitHub\\Project-Ocondat\\Drawing Standards\\Netherlands\\Working Directory\\NL-Drawing-Standards'
target = os.path.join(base, "generate_svg_from_geometry.py")

# Script content stored as list of lines
script_lines = json.loads(open(os.path.join(base, "_script_lines.json"), "r", encoding="utf-8").read())

with open(target, "w", encoding="utf-8") as f:
    f.write(chr(10).join(script_lines))

print(f"Written {os.path.getsize(target)} bytes")