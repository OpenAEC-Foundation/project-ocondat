"""Generate component library: DXF -> SVG + components.json

Scans DXF files from components/ hierarchy (Fabrikant/Serie/Product/Variant),
generates SVG files using ezdxf, and builds the
components.json + data.js database for the component-library website.

Also supports legacy Componenten/ folder as fallback.

Usage:
    python tools/gen_library.py                  # Use components/ (new structure)
    python tools/gen_library.py --legacy          # Use Componenten/ (old structure)
"""

import argparse
import json
import os
import re
import math
import sys
from datetime import date

import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.svg import SVGBackend
from ezdxf.addons.drawing import layout as drawing_layout

# Paths
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP_DIR = os.path.join(BASE, "Componenten")       # Legacy
COMP_NEW = os.path.join(BASE, "components")         # New hierarchy
OUT_SVG = os.path.join(BASE, "component-library", "svg")
OUT_DATA = os.path.join(BASE, "component-library", "data")
OUT_JS = os.path.join(BASE, "component-library", "js")

os.makedirs(OUT_SVG, exist_ok=True)
os.makedirs(OUT_DATA, exist_ok=True)
os.makedirs(OUT_JS, exist_ok=True)

# ── Category metadata ─────────────────────────────────────────────
# Maps category prefix -> (name_nl, name_en, ifc_class, ifc_predefined_type, nl_standard)
CATEGORIES = {
    "00": ("Basismaterialen",          "Basic Materials",          "IfcMechanicalFastener", "USERDEFINED", "NEN-EN 1993-1-8"),
    "16": ("Funderingspalen",          "Foundation Piles",         "IfcPile",               "DRIVEN",      "NEN-EN 1997"),
    "17": ("Palen",                    "Piles",                    "IfcPile",               "DRIVEN",      "NEN-EN 1997"),
    "20": ("Ankers en verbindingen",   "Anchors & Connections",    "IfcMechanicalFastener", "USERDEFINED", "NEN-EN 1993-1-8"),
    "21": ("Wanden - metselwerk",      "Walls - Masonry",          "IfcWall",               "STANDARD",    "NEN-EN 1996"),
    "22": ("Wanden - blokken",         "Walls - Blocks",           "IfcWall",               "STANDARD",    "NEN-EN 1996"),
    "23": ("Vloeren",                  "Floors",                   "IfcSlab",               "FLOOR",       "NEN-EN 1992"),
    "27": ("Dakbedekking",             "Roof Covering",            "IfcRoof",               "FLAT_ROOF",   "NEN-EN 1993-1-3"),
    "28": ("Staalconstructie",         "Steel Construction",       "IfcMember",             "MEMBER",      "NEN-EN 1993"),
    "30": ("Glas en gevelbekleding",   "Glass & Facade Cladding",  "IfcPlate",              "CURTAIN_PANEL","NEN-EN 1279"),
    "31": ("Ramen en deuren",          "Windows & Doors",          "IfcWindow",             "WINDOW",      "NEN-EN 14351-1"),
    "32": ("Kozijnen",                 "Frames",                   "IfcWindow",             "WINDOW",      "NEN-EN 14351-1"),
    "33": ("Sparingen",                "Openings",                 "IfcOpeningElement",     "OPENING",     ""),
    "34": ("Diversen - bent",          "Miscellaneous - Bent",     "IfcBuildingElementProxy","USERDEFINED", ""),
    "35": ("Kantlatten",               "Edge Strips",              "IfcMember",             "MULLION",     ""),
    "37": ("Diversen - DI",            "Miscellaneous - DI",       "IfcBuildingElementProxy","USERDEFINED", ""),
    "40": ("Vloerplaten en afwerking", "Floor Panels & Finishing",  "IfcCovering",          "CLADDING",    "NEN-EN 520"),
    "41": ("Gevelafwerking",           "Facade Finishing",         "IfcCurtainWall",        "USERDEFINED", "NEN-EN 1999"),
    "42": ("Afwerkprofielen",          "Finishing Profiles",       "IfcMember",             "MULLION",     "NEN-EN 14195"),
    "43": ("Vloer- en wandafwerking",  "Floor & Wall Finishing",   "IfcCovering",           "CLADDING",    ""),
    "45": ("Plafonds",                 "Ceilings",                 "IfcCovering",           "CEILING",     "NEN-EN 13964"),
    "47": ("Dakdetails",               "Roof Details",             "IfcRoof",               "USERDEFINED", "NEN-EN 1304"),
    "52": ("Hemelwaterafvoer",         "Rainwater Drainage",       "IfcPipeSegment",        "USERDEFINED", "NEN-EN 12056"),
    "90": ("Bestrating",               "Paving",                   "IfcSlab",               "PAVING",      ""),
    "91": ("Overig",                   "Other",                    "IfcBuildingElementProxy","USERDEFINED", ""),
}

# ── IFC Classes (primary classification system) ──────────────────
# Per class: name_nl, group, pset
IFC_CLASSES = {
    "IfcMember":              {"name_nl": "Staaf/Profiel",           "group": "Structure",   "pset": "Pset_MemberCommon"},
    "IfcColumn":              {"name_nl": "Kolom",                   "group": "Structure",   "pset": "Pset_ColumnCommon"},
    "IfcBeam":                {"name_nl": "Balk",                    "group": "Structure",   "pset": "Pset_BeamCommon"},
    "IfcPile":                {"name_nl": "Paal/Heipaal",            "group": "Structure",   "pset": "Pset_PileCommon"},
    "IfcPlate":               {"name_nl": "Plaat",                   "group": "Structure",   "pset": "Pset_PlateCommon"},
    "IfcWall":                {"name_nl": "Wand/Muur",               "group": "Enclosure",   "pset": "Pset_WallCommon"},
    "IfcSlab":                {"name_nl": "Vloerplaat",              "group": "Enclosure",   "pset": "Pset_SlabCommon"},
    "IfcRoof":                {"name_nl": "Dak",                     "group": "Enclosure",   "pset": "Pset_RoofCommon"},
    "IfcCurtainWall":         {"name_nl": "Vliesgevel",              "group": "Enclosure",   "pset": "Pset_CurtainWallCommon"},
    "IfcWindow":              {"name_nl": "Raam/Venster",            "group": "Opening",     "pset": "Pset_WindowCommon"},
    "IfcDoor":                {"name_nl": "Deur",                    "group": "Opening",     "pset": "Pset_DoorCommon"},
    "IfcOpeningElement":      {"name_nl": "Sparing",                 "group": "Opening",     "pset": None},
    "IfcCovering":            {"name_nl": "Afwerking/Bekleding",     "group": "Finishing",   "pset": "Pset_CoveringCommon"},
    "IfcMechanicalFastener":  {"name_nl": "Mechanische verbinding",  "group": "Fastener",    "pset": "Pset_MechanicalFastenerCommon"},
    "IfcElementAssembly":     {"name_nl": "Samengesteld element",    "group": "Fastener",    "pset": None},
    "IfcPipeSegment":         {"name_nl": "Buissegment",             "group": "MEP",         "pset": "Pset_PipeSegmentCommon"},
    "IfcSanitaryTerminal":    {"name_nl": "Sanitair element",        "group": "MEP",         "pset": "Pset_SanitaryTerminalCommon"},
    "IfcElectricAppliance":   {"name_nl": "Elektrisch apparaat",     "group": "MEP",         "pset": None},
    "IfcFurniture":           {"name_nl": "Meubilair",               "group": "Furnishing",  "pset": "Pset_FurnitureCommon"},
    "IfcGeographicElement":   {"name_nl": "Geografisch element",     "group": "Site",        "pset": None},
    "IfcTransportElement":    {"name_nl": "Transportelement",        "group": "Site",        "pset": None},
    "IfcAnnotation":          {"name_nl": "Annotatie/Symbool",       "group": "Annotation",  "pset": None},
    "IfcBuildingElementProxy":{"name_nl": "Proxy (onbekend)",        "group": "Other",       "pset": None},
}

# ── Series -> IFC mapping (auto-classification) ─────────────────
# Maps serie name -> (ifc_class, predefined_type)
SERIES_IFC_MAP = {
    # Halfen series
    "Ankerschienen-HTA":   ("IfcMechanicalFastener", "ANCHORBOLT"),
    "Bodyanker-BA":        ("IfcMechanicalFastener", "ANCHORBOLT"),
    "Curtain-Wall-HCW":   ("IfcElementAssembly",     "ACCESSORY_ASSEMBLY"),
    "Deckenanker-SOF":     ("IfcMechanicalFastener", "ANCHORBOLT"),
    "HIT-Verbindungen":   ("IfcMechanicalFastener",  "SHEARCONNECTOR"),
    "Konsolen-UK":         ("IfcElementAssembly",     "ACCESSORY_ASSEMBLY"),
    "Zubehoer-A":          ("IfcMechanicalFastener", "USERDEFINED"),
    "Zubehoer-B":          ("IfcMechanicalFastener", "USERDEFINED"),
    "Zubehoer-M":          ("IfcMechanicalFastener", "USERDEFINED"),
    # Community/DXF-library series
    "appliances":          ("IfcElectricAppliance",   "USERDEFINED"),
    "basins":              ("IfcSanitaryTerminal",    "WASHHANDBASIN"),
    "bathtubs":            ("IfcSanitaryTerminal",    "BATH"),
    "beds":                ("IfcFurniture",           "BED"),
    "cars":                ("IfcTransportElement",    "USERDEFINED"),
    "chairs":              ("IfcFurniture",           "CHAIR"),
    "lounge":              ("IfcFurniture",           "SOFA"),
    "office":              ("IfcFurniture",           "DESK"),
    "people":              ("IfcAnnotation",          "USERDEFINED"),
    "tables":              ("IfcFurniture",           "TABLE"),
    "vegetation":          ("IfcGeographicElement",   "VEGETATION"),
    "wc":                  ("IfcSanitaryTerminal",    "TOILETPAN"),
    # Community/dxfBlocks series
    "Architecture":        ("IfcFurniture",           "USERDEFINED"),
    "DrawingSymbols":      ("IfcAnnotation",          "USERDEFINED"),
    "Fasteners":           ("IfcMechanicalFastener",  "BOLT"),
    "InfoTech":            ("IfcElectricAppliance",   "USERDEFINED"),
}

# ── IFC Property Set definitions (IFC4) ──────────────────────────
IFC_PSETS = {
    "Pset_MemberCommon": {
        "description_nl": "Algemene eigenschappen van een staaf/profiel",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "LoadBearing",      "type": "IfcBoolean",         "description_nl": "Dragend element"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
            {"name": "Span",             "type": "IfcPositiveLengthMeasure", "description_nl": "Overspanning"},
        ],
    },
    "Pset_ColumnCommon": {
        "description_nl": "Algemene eigenschappen van een kolom",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "LoadBearing",      "type": "IfcBoolean",         "description_nl": "Dragend element"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
        ],
    },
    "Pset_BeamCommon": {
        "description_nl": "Algemene eigenschappen van een balk",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "LoadBearing",      "type": "IfcBoolean",         "description_nl": "Dragend element"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
            {"name": "Span",             "type": "IfcPositiveLengthMeasure", "description_nl": "Overspanning"},
        ],
    },
    "Pset_PileCommon": {
        "description_nl": "Algemene eigenschappen van een paal",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "Length",           "type": "IfcPositiveLengthMeasure", "description_nl": "Lengte"},
        ],
    },
    "Pset_PlateCommon": {
        "description_nl": "Algemene eigenschappen van een plaat",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "LoadBearing",      "type": "IfcBoolean",         "description_nl": "Dragend element"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
        ],
    },
    "Pset_WallCommon": {
        "description_nl": "Algemene eigenschappen van een wand",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "LoadBearing",      "type": "IfcBoolean",         "description_nl": "Dragend element"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
            {"name": "ThermalTransmittance", "type": "IfcThermalTransmittanceMeasure", "description_nl": "Warmtedoorgangscoëfficiënt (U-waarde)"},
        ],
    },
    "Pset_SlabCommon": {
        "description_nl": "Algemene eigenschappen van een vloerplaat",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "LoadBearing",      "type": "IfcBoolean",         "description_nl": "Dragend element"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
        ],
    },
    "Pset_RoofCommon": {
        "description_nl": "Algemene eigenschappen van een dak",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
        ],
    },
    "Pset_CurtainWallCommon": {
        "description_nl": "Algemene eigenschappen van een vliesgevel",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
            {"name": "ThermalTransmittance", "type": "IfcThermalTransmittanceMeasure", "description_nl": "Warmtedoorgangscoëfficiënt (U-waarde)"},
        ],
    },
    "Pset_WindowCommon": {
        "description_nl": "Algemene eigenschappen van een raam",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
            {"name": "ThermalTransmittance", "type": "IfcThermalTransmittanceMeasure", "description_nl": "Warmtedoorgangscoëfficiënt (U-waarde)"},
        ],
    },
    "Pset_DoorCommon": {
        "description_nl": "Algemene eigenschappen van een deur",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
        ],
    },
    "Pset_CoveringCommon": {
        "description_nl": "Algemene eigenschappen van een afwerking",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",       "description_nl": "Referentie-aanduiding"},
            {"name": "IsExternal",       "type": "IfcBoolean",         "description_nl": "Buitenzijde"},
            {"name": "FireRating",       "type": "IfcLabel",           "description_nl": "Brandwerendheid"},
        ],
    },
    "Pset_MechanicalFastenerCommon": {
        "description_nl": "Algemene eigenschappen van een mechanische verbinding",
        "properties": [
            {"name": "Reference",        "type": "IfcIdentifier",          "description_nl": "Referentie-aanduiding"},
            {"name": "NominalDiameter",  "type": "IfcPositiveLengthMeasure","description_nl": "Nominale diameter"},
            {"name": "NominalLength",    "type": "IfcPositiveLengthMeasure","description_nl": "Nominale lengte"},
            {"name": "FinishColor",      "type": "IfcLabel",               "description_nl": "Afwerkkleur"},
        ],
    },
    "Pset_PipeSegmentCommon": {
        "description_nl": "Algemene eigenschappen van een buissegment",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",           "description_nl": "Referentie-aanduiding"},
            {"name": "NominalDiameter",  "type": "IfcPositiveLengthMeasure","description_nl": "Nominale diameter"},
        ],
    },
    "Pset_SanitaryTerminalCommon": {
        "description_nl": "Algemene eigenschappen van een sanitair element",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",           "description_nl": "Referentie-aanduiding"},
            {"name": "NominalLength",    "type": "IfcPositiveLengthMeasure","description_nl": "Nominale lengte"},
            {"name": "NominalWidth",     "type": "IfcPositiveLengthMeasure","description_nl": "Nominale breedte"},
            {"name": "Color",            "type": "IfcLabel",               "description_nl": "Kleur"},
        ],
    },
    "Pset_FurnitureCommon": {
        "description_nl": "Algemene eigenschappen van meubilair",
        "properties": [
            {"name": "Reference",       "type": "IfcIdentifier",           "description_nl": "Referentie-aanduiding"},
            {"name": "NominalLength",    "type": "IfcPositiveLengthMeasure","description_nl": "Nominale lengte"},
            {"name": "NominalWidth",     "type": "IfcPositiveLengthMeasure","description_nl": "Nominale breedte"},
            {"name": "NominalHeight",    "type": "IfcPositiveLengthMeasure","description_nl": "Nominale hoogte"},
        ],
    },
}

# ── Series -> Material mapping ───────────────────────────────────
SERIES_MATERIALS = {
    "Damwandprofielen":     {"material": "Steel S240GP/S270GP",       "category": "Steel"},
    "HE-profielen":         {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "HD-profielen":         {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "HL-profielen":         {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "IPE-profielen":        {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "IPN-profielen":        {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "L-profielen":          {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "UPE-profielen":        {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "UB-profielen":         {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "UC-profielen":         {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "UPN-profielen":        {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "W-profielen":          {"material": "Steel S235/S275/S355",      "category": "Steel"},
    "Ankerschienen-HTA":    {"material": "Hot-dip galvanized steel",  "category": "Steel"},
    "Bodyanker-BA":         {"material": "Stainless steel A4",        "category": "Steel"},
    "Wanden-metselwerk":    {"material": "Clay brick",                "category": "Masonry"},
    "Wanden-blokken":       {"material": "Concrete block",            "category": "Concrete"},
    "Vloeren":              {"material": "Concrete C20/25-C45/55",    "category": "Concrete"},
}

# ── IFC Profile parameters (from IFC4 schema) ───────────────────
# Maps IfcProfileDef subtypes to their parameter names
IFC_PROFILE_PARAMS = {
    "IfcIShapeProfileDef": {
        "params": [
            "OverallWidth",       # Flange width (mm)
            "OverallDepth",       # Total height (mm)
            "WebThickness",       # Web thickness (mm)
            "FlangeThickness",    # Flange thickness (mm)
            "FilletRadius",       # Fillet radius (mm, optional)
            "FlangeEdgeRadius",   # Flange edge radius (mm, optional, IFC4)
            "FlangeSlope",        # Flange slope (rad, optional, IFC4)
        ],
        "description": "I-shape with parallel or tapered flanges (HEA, HEB, HEM, IPE, HD, HL, UB, UC, W)",
    },
    "IfcUShapeProfileDef": {
        "params": [
            "Depth",              # Overall depth (mm)
            "FlangeWidth",        # Flange width (mm)
            "WebThickness",       # Web thickness (mm)
            "FlangeThickness",    # Flange thickness (mm)
            "FilletRadius",       # Fillet radius (mm, optional)
            "EdgeRadius",         # Edge radius (mm, optional)
            "FlangeSlope",        # Flange slope (rad, optional)
        ],
        "description": "U-shape / channel section (UPN, UPE)",
    },
    "IfcLShapeProfileDef": {
        "params": [
            "Depth",              # Vertical leg length (mm)
            "Width",              # Horizontal leg length (mm, optional = Depth)
            "Thickness",          # Leg thickness (mm)
            "FilletRadius",       # Fillet radius (mm, optional)
            "EdgeRadius",         # Edge radius (mm, optional)
            "LegSlope",           # Leg slope (rad, optional)
        ],
        "description": "Angle section, equal or unequal leg (L)",
    },
    "IfcTShapeProfileDef": {
        "params": [
            "Depth",              # Overall depth (mm)
            "FlangeWidth",        # Flange width (mm)
            "WebThickness",       # Web thickness (mm)
            "FlangeThickness",    # Flange thickness (mm)
            "FilletRadius",       # Fillet radius (mm, optional)
            "FlangeEdgeRadius",   # Flange edge radius (mm, optional)
            "WebSlope",           # Web slope (rad, optional)
            "FlangeSlope",        # Flange slope (rad, optional)
        ],
        "description": "T-shape section",
    },
    "IfcCircleHollowProfileDef": {
        "params": [
            "Radius",             # Outer radius (mm)
            "WallThickness",      # Wall thickness (mm)
        ],
        "description": "Circular hollow section (CHS)",
    },
    "IfcRectangleHollowProfileDef": {
        "params": [
            "XDim",               # Width (mm)
            "YDim",               # Height (mm)
            "WallThickness",      # Wall thickness (mm)
            "InnerFilletRadius",  # Inner corner radius (mm, optional)
            "OuterFilletRadius",  # Outer corner radius (mm, optional)
        ],
        "description": "Rectangular hollow section (SHS, RHS)",
    },
    "IfcArbitraryClosedProfileDef": {
        "params": [
            "OuterCurve",         # Boundary curve (geometry)
        ],
        "description": "Arbitrary closed profile (sheet piles, special sections)",
    },
}

# Words to skip when generating tags (too generic)
SKIP_TAGS = {"dxf", "type", "mm", "d", "b", "h", "nr", "std", "gen", "ask",
             "ver", "hor", "bu", "bi", "e1", "s", "a", "v2", "v3", "f", "g",
             "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}


def safe_filename(name):
    """Create a filesystem-safe filename."""
    s = name.lower().replace(' ', '-').replace('&', '-')
    return re.sub(r'[^a-zA-Z0-9_\-]', '', s).strip('-')


# Steel profile prefixes that should always be uppercase
PROFILE_PREFIXES = (
    'hea', 'heb', 'hem', 'ipe', 'ipn', 'inp',
    'upe', 'upn', 'hd', 'hl', 'he', 'ip',
    'ub', 'uc', 'shs', 'rhs', 'chs',
    'l', 'w',
)

def make_display_name(filename):
    """Create a human-readable display name from a DXF filename."""
    name = filename.replace('.dxf', '').replace('.DXF', '')
    # Remove leading category digits like "00 g " or "31 f "
    name = re.sub(r'^\d{2}\s+[a-z]\s+', '', name)
    # Remove trailing duplicate markers like " (1)" " (2)"
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    # Uppercase steel profile names: heb300 -> HEB300, ipe200 -> IPE200
    for prefix in sorted(PROFILE_PREFIXES, key=len, reverse=True):
        pat = re.compile(r'\b(' + prefix + r')(\d)', re.IGNORECASE)
        name = pat.sub(lambda m: m.group(1).upper() + m.group(2), name)
    # Title-case but keep uppercase sequences (HEB300, IPE200, SHS, M12)
    words = name.split()
    result = []
    for w in words:
        if re.match(r'^[A-Z0-9]+$', w) or re.match(r'^[A-Z]+\d', w):
            result.append(w)  # keep as-is: HEB300, IPE200, M12
        else:
            result.append(w.capitalize() if w == w.lower() else w)
    return ' '.join(result)


def make_tags(filename, cat_name_nl):
    """Generate search tags from filename and category."""
    name = filename.replace('.dxf', '').replace('.DXF', '')
    # Remove leading category prefix
    name = re.sub(r'^\d{2}\s+[a-z]\s+', '', name)
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    # Split into words
    words = re.split(r'[\s_\-+&]+', name.lower())
    # Add category words
    cat_words = re.split(r'[\s_\-+&]+', cat_name_nl.lower())
    tags = []
    seen = set()
    for w in words + cat_words:
        w = re.sub(r'[^a-z0-9]', '', w)
        if w and w not in SKIP_TAGS and len(w) > 1 and w not in seen:
            tags.append(w)
            seen.add(w)
    return tags[:8]  # max 8 tags per component


def make_component_id(cat_id, filename, seen_ids):
    """Generate a unique component ID."""
    name = filename.replace('.dxf', '').replace('.DXF', '')
    name = re.sub(r'^\d{2}\s+[a-z]\s+', '', name)
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    base = safe_filename(name)
    if not base:
        base = 'component'
    cid = f"{cat_id}-{base}"
    # Ensure uniqueness
    if cid in seen_ids:
        n = 2
        while f"{cid}-{n}" in seen_ids:
            n += 1
        cid = f"{cid}-{n}"
    seen_ids.add(cid)
    return cid


def get_extents(msp):
    """Calculate bounding box of all entities in modelspace."""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    for entity in msp:
        try:
            bbox = ezdxf.bbox.extents([entity])
            if bbox.has_data:
                min_x = min(min_x, bbox.extmin.x)
                min_y = min(min_y, bbox.extmin.y)
                max_x = max(max_x, bbox.extmax.x)
                max_y = max(max_y, bbox.extmax.y)
        except Exception:
            pass

    if min_x == float('inf'):
        return 0, 0, 100, 100
    return min_x, min_y, max_x, max_y


def _collect_hatches(doc):
    """Collect all HATCH entities from modelspace, recursing into blocks.
    Returns list of (hatch_entity, transform_matrix) tuples."""
    from ezdxf.math import Matrix44
    hatches = []

    def _walk(entities, transform=None):
        for entity in entities:
            if entity.dxftype() == "INSERT":
                block = doc.blocks.get(entity.dxf.name)
                if block is None:
                    continue
                try:
                    m = entity.matrix44()
                except Exception:
                    m = Matrix44()
                if transform:
                    m = transform @ m
                _walk(block, m)
            elif entity.dxftype() == "HATCH":
                hatches.append((entity, transform))

    _walk(doc.modelspace())
    return hatches


def _hatch_boundary_to_svg(hatch, matrix):
    """Convert HATCH boundary paths to SVG path strings with fill.
    Returns list of SVG path data strings."""
    from ezdxf.math import Vec3
    svg_paths = []
    for boundary in hatch.paths:
        if not hasattr(boundary, 'edges') or not boundary.edges:
            continue
        parts = []
        for i, edge in enumerate(boundary.edges):
            if hasattr(edge, 'start') and hasattr(edge, 'end'):
                # LineEdge
                sx, sy = edge.start.x, edge.start.y
                ex, ey = edge.end.x, edge.end.y
                if matrix:
                    sp = matrix.transform(Vec3(sx, sy, 0))
                    ep = matrix.transform(Vec3(ex, ey, 0))
                    sx, sy = sp.x, sp.y
                    ex, ey = ep.x, ep.y
                if i == 0:
                    parts.append(f"M{sx:.3f} {-sy:.3f}")
                parts.append(f"L{ex:.3f} {-ey:.3f}")
            elif hasattr(edge, 'center') and hasattr(edge, 'radius'):
                # ArcEdge
                cx, cy = edge.center.x, edge.center.y
                r = edge.radius
                sa = math.radians(edge.start_angle)
                ea = math.radians(edge.end_angle)
                s_x = cx + r * math.cos(sa)
                s_y = cy + r * math.sin(sa)
                e_x = cx + r * math.cos(ea)
                e_y = cy + r * math.sin(ea)
                if matrix:
                    sp = matrix.transform(Vec3(s_x, s_y, 0))
                    ep = matrix.transform(Vec3(e_x, e_y, 0))
                    cp = matrix.transform(Vec3(cx, cy, 0))
                    rp = matrix.transform(Vec3(cx + r, cy, 0))
                    r = abs(rp.x - cp.x)
                    s_x, s_y = sp.x, sp.y
                    e_x, e_y = ep.x, ep.y
                angle_diff = (edge.end_angle - edge.start_angle) % 360
                la = 1 if angle_diff > 180 else 0
                ccw = 1 if getattr(edge, 'ccw', True) else 0
                sf = 0 if ccw else 1
                if i == 0:
                    parts.append(f"M{s_x:.3f} {-s_y:.3f}")
                parts.append(f"A{r:.3f} {r:.3f} 0 {la} {sf} {e_x:.3f} {-e_y:.3f}")
        if parts:
            parts.append("Z")
            svg_paths.append(" ".join(parts))
    return svg_paths


def generate_svg_ezdxf(dxf_path, svg_path):
    """Generate SVG from DXF using ezdxf drawing addon.
    Returns (width_mm, height_mm) of the component."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    min_x, min_y, max_x, max_y = get_extents(msp)
    width_mm = round(max_x - min_x, 1)
    height_mm = round(max_y - min_y, 1)

    # Collect hatch boundaries for solid fill rendering
    hatches = _collect_hatches(doc)
    fill_paths = []
    for h, m in hatches:
        fill_paths.extend(_hatch_boundary_to_svg(h, m))

    ctx = RenderContext(doc)
    backend = SVGBackend()
    frontend = Frontend(ctx, backend)
    frontend.draw_layout(msp)

    page = drawing_layout.Page(
        width=max(width_mm, 10),
        height=max(height_mm, 10),
        margins=drawing_layout.Margins.all(2),
    )
    svg_string = backend.get_string(page)

    # Post-process: responsive, remove dark background, fix colors
    svg_string = re.sub(
        r'width="[^"]*"\s*height="[^"]*"',
        'width="100%" height="100%"',
        svg_string,
        count=1
    )
    svg_string = re.sub(
        r'<rect fill="#[0-9a-fA-F]+" x="0" y="0" width="[^"]*" height="[^"]*"[^/]*/>\s*',
        '', svg_string
    )
    svg_string = svg_string.replace('#00a500', '#333333')
    svg_string = svg_string.replace('#ffffff', '#333333')

    if fill_paths:
        # Remove ezdxf-rendered hatch pattern lines (thinnest stroke class)
        # and replace with solid filled boundaries
        svg_string = re.sub(
            r'<style>\.C1 \{[^}]*stroke-width:\s*\d+;[^}]*\}</style>',
            '<style>.C1 {display: none;}</style>',
            svg_string,
            count=1
        )
        # Hide all C1-class elements (hatch pattern lines)
        svg_string = svg_string.replace('class="C1"', 'class="C1" style="display:none"')
        # Insert filled paths before the closing </g>
        fill_elements = '\n'.join(
            f'<path d="{d}" fill="#333333" stroke="#333333" stroke-width="200"/>'
            for d in fill_paths
        )
        svg_string = svg_string.replace('</g>', fill_elements + '\n</g>')
    else:
        # No hatches: increase stroke-width for better visibility
        svg_string = re.sub(
            r'stroke-width:\s*(\d+)',
            lambda m: f'stroke-width: {max(int(m.group(1)) * 2, 1200)}',
            svg_string
        )

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_string)

    return width_mm, height_mm


def flatten_entities(msp, doc):
    """Recursively flatten INSERT references into basic entities."""
    from ezdxf.math import Matrix44

    def _collect(entities, transform=None):
        result = []
        for entity in entities:
            if entity.dxftype() == "INSERT":
                block = doc.blocks.get(entity.dxf.name)
                if block is None:
                    continue
                try:
                    m = entity.matrix44()
                except Exception:
                    m = Matrix44()
                if transform:
                    m = transform @ m
                result.extend(_collect(block, m))
            else:
                result.append((entity, transform))
        return result

    return _collect(msp)


def transform_point(x, y, matrix):
    """Apply a Matrix44 transform to a 2D point."""
    if matrix is None:
        return x, y
    from ezdxf.math import Vec3
    p = matrix.transform(Vec3(x, y, 0))
    return p.x, p.y


def generate_svg_manual(dxf_path, svg_path):
    """Fallback: generate SVG manually, flattening INSERT entities."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    min_x, min_y, max_x, max_y = get_extents(msp)
    width_mm = round(max_x - min_x, 1)
    height_mm = round(max_y - min_y, 1)
    if width_mm == 0: width_mm = 1
    if height_mm == 0: height_mm = 1

    pad = max(width_mm, height_mm) * 0.05
    ny_min, ny_max = -max_y, -min_y
    vx = min_x - pad
    vy = ny_min - pad
    vw = (max_x - min_x) + 2 * pad
    vh = (ny_max - ny_min) + 2 * pad

    # Collect hatches for solid fill
    hatches = _collect_hatches(doc)
    fill_paths = []
    for h, m in hatches:
        fill_paths.extend(_hatch_boundary_to_svg(h, m))

    # Use thicker stroke for non-hatched (thinner lines are less visible)
    sw = max(vw, vh) * (0.006 if not fill_paths else 0.004)

    ACI_COLORS = {
        1: "#ff0000", 2: "#ffff00", 3: "#00ff00", 4: "#00ffff",
        5: "#0000ff", 6: "#ff00ff", 7: "#333333", 8: "#808080", 9: "#c0c0c0",
    }

    def get_color(entity):
        try:
            ci = entity.dxf.color
            if ci in ACI_COLORS: return ACI_COLORS[ci]
            if ci == 256:
                layer = doc.layers.get(entity.dxf.layer)
                if layer: return ACI_COLORS.get(layer.color, "#333333")
        except Exception: pass
        return "#333333"

    def get_dash(entity):
        try:
            lt = (entity.dxf.linetype or "").upper()
            if "HIDDEN" in lt or "VERBORGEN" in lt: return ' stroke-dasharray="2 1.5"'
            if "CENTER" in lt or "HART" in lt: return ' stroke-dasharray="4 1.5 1 1.5"'
            if "DASH" in lt: return ' stroke-dasharray="3 2"'
        except Exception: pass
        return ""

    elements = []
    # Add solid fill paths first (behind outlines)
    for d in fill_paths:
        elements.append(f'<path d="{d}" fill="#333333" stroke="none"/>')

    for entity, matrix in flatten_entities(msp, doc):
        dxf_type = entity.dxftype()
        # Skip HATCH entities in line rendering (already handled as fills)
        if dxf_type == "HATCH":
            continue
        color = get_color(entity)
        dash = get_dash(entity)
        try:
            if dxf_type == "LINE":
                x0, y0 = transform_point(entity.dxf.start.x, entity.dxf.start.y, matrix)
                x1, y1 = transform_point(entity.dxf.end.x, entity.dxf.end.y, matrix)
                elements.append(f'<line x1="{x0:.3f}" y1="{-y0:.3f}" x2="{x1:.3f}" y2="{-y1:.3f}" stroke="{color}"{dash}/>')

            elif dxf_type == "CIRCLE":
                cx, cy = transform_point(entity.dxf.center.x, entity.dxf.center.y, matrix)
                r = entity.dxf.radius
                if matrix:
                    from ezdxf.math import Vec3
                    p0 = matrix.transform(Vec3(entity.dxf.center.x, entity.dxf.center.y, 0))
                    p1 = matrix.transform(Vec3(entity.dxf.center.x + r, entity.dxf.center.y, 0))
                    r = abs(p1.x - p0.x)
                elements.append(f'<circle cx="{cx:.3f}" cy="{-cy:.3f}" r="{r:.3f}" stroke="{color}"{dash}/>')

            elif dxf_type == "ARC":
                ocx, ocy = entity.dxf.center.x, entity.dxf.center.y
                r = entity.dxf.radius
                sa, ea = math.radians(entity.dxf.start_angle), math.radians(entity.dxf.end_angle)
                sx, sy = transform_point(ocx + r * math.cos(sa), ocy + r * math.sin(sa), matrix)
                ex, ey = transform_point(ocx + r * math.cos(ea), ocy + r * math.sin(ea), matrix)
                if matrix:
                    from ezdxf.math import Vec3
                    p0 = matrix.transform(Vec3(ocx, ocy, 0))
                    p1 = matrix.transform(Vec3(ocx + r, ocy, 0))
                    r = p0.distance(p1)
                la = 1 if (entity.dxf.end_angle - entity.dxf.start_angle) % 360 > 180 else 0
                elements.append(f'<path d="M{sx:.3f} {-sy:.3f} A{r:.3f} {r:.3f} 0 {la} 0 {ex:.3f} {-ey:.3f}" stroke="{color}"{dash}/>')

            elif dxf_type == "LWPOLYLINE":
                points = list(entity.get_points(format="xyseb"))
                if len(points) < 2: continue
                tpts = [(transform_point(p[0], p[1], matrix) + (p[4],)) for p in points]
                parts = [f"M{tpts[0][0]:.3f} {-tpts[0][1]:.3f}"]
                for i in range(len(tpts) - 1):
                    x0, y0, bulge = tpts[i]
                    x1, y1, _ = tpts[i + 1]
                    if abs(bulge) < 1e-6:
                        parts.append(f"L{x1:.3f} {-y1:.3f}")
                    else:
                        d = math.sqrt((x1-x0)**2 + (y1-y0)**2)
                        if d < 1e-10: continue
                        r = abs(d / (2 * math.sin(2 * math.atan(abs(bulge)))))
                        la = 1 if abs(bulge) > 1 else 0
                        sf = 0 if bulge > 0 else 1
                        parts.append(f"A{r:.3f} {r:.3f} 0 {la} {sf} {x1:.3f} {-y1:.3f}")
                if entity.closed: parts.append("Z")
                elements.append(f'<path d="{" ".join(parts)}" stroke="{color}"{dash}/>')

            elif dxf_type in ("SPLINE", "ELLIPSE"):
                pts = list(entity.flattening(0.5))
                if len(pts) < 2: continue
                tx0, ty0 = transform_point(pts[0].x, pts[0].y, matrix)
                d = f"M{tx0:.3f} {-ty0:.3f}"
                for pt in pts[1:]:
                    tx, ty = transform_point(pt.x, pt.y, matrix)
                    d += f" L{tx:.3f} {-ty:.3f}"
                elements.append(f'<path d="{d}" stroke="{color}"{dash}/>')

        except Exception:
            pass

    if not elements:
        return width_mm, height_mm

    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.3f} {vy:.3f} {vw:.3f} {vh:.3f}"\n'
           f'     width="100%" height="100%" preserveAspectRatio="xMidYMid meet">\n'
           f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="{sw:.4f}">\n'
           + '\n'.join(elements) + '\n</g>\n</svg>')

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg)

    return width_mm, height_mm


def extract_o2d_shapes(dxf_path):
    """Extract O2D-compatible shape dicts from a DXF file.
    Returns (layers_dict, shapes_list) for Open 2D Studio import."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    ACI_COLORS = {
        1: "#ff0000", 2: "#ffff00", 3: "#00ff00", 4: "#00ffff",
        5: "#0000ff", 6: "#ff00ff", 7: "#333333", 8: "#808080", 9: "#c0c0c0",
    }

    # Build layer color map
    layers = {}
    for layer in doc.layers:
        ln = layer.dxf.name
        aci = layer.dxf.get("color", 7)
        layers[ln] = ACI_COLORS.get(aci, "#333333")

    def get_color(entity):
        try:
            ci = entity.dxf.color
            if ci in ACI_COLORS: return ACI_COLORS[ci]
            if ci == 256:
                l = doc.layers.get(entity.dxf.layer)
                if l: return ACI_COLORS.get(l.color, "#333333")
        except Exception: pass
        return "#333333"

    def get_layer(entity):
        try: return entity.dxf.layer
        except Exception: return "0"

    shapes = []
    for entity, matrix in flatten_entities(msp, doc):
        dxf_type = entity.dxftype()
        color = get_color(entity)
        layer = get_layer(entity)
        try:
            if dxf_type == "LINE":
                x0, y0 = transform_point(entity.dxf.start.x, entity.dxf.start.y, matrix)
                x1, y1 = transform_point(entity.dxf.end.x, entity.dxf.end.y, matrix)
                shapes.append({
                    "type": "line",
                    "x1": round(x0, 3), "y1": round(y0, 3),
                    "x2": round(x1, 3), "y2": round(y1, 3),
                    "layer": layer,
                    "style": {"stroke": color}
                })
            elif dxf_type == "CIRCLE":
                cx, cy = transform_point(entity.dxf.center.x, entity.dxf.center.y, matrix)
                r = entity.dxf.radius
                if matrix:
                    from ezdxf.math import Vec3
                    p0 = matrix.transform(Vec3(entity.dxf.center.x, entity.dxf.center.y, 0))
                    p1 = matrix.transform(Vec3(entity.dxf.center.x + r, entity.dxf.center.y, 0))
                    r = abs(p1.x - p0.x)
                shapes.append({
                    "type": "circle",
                    "cx": round(cx, 3), "cy": round(cy, 3),
                    "radius": round(r, 3),
                    "layer": layer,
                    "style": {"stroke": color, "fill": "none"}
                })
            elif dxf_type == "ARC":
                ocx, ocy = entity.dxf.center.x, entity.dxf.center.y
                r = entity.dxf.radius
                cx, cy = transform_point(ocx, ocy, matrix)
                if matrix:
                    from ezdxf.math import Vec3
                    p0 = matrix.transform(Vec3(ocx, ocy, 0))
                    p1 = matrix.transform(Vec3(ocx + r, ocy, 0))
                    r = p0.distance(p1)
                shapes.append({
                    "type": "arc",
                    "cx": round(cx, 3), "cy": round(cy, 3),
                    "radius": round(r, 3),
                    "startAngle": entity.dxf.start_angle,
                    "endAngle": entity.dxf.end_angle,
                    "layer": layer,
                    "style": {"stroke": color, "fill": "none"}
                })
            elif dxf_type == "LWPOLYLINE":
                points = list(entity.get_points(format="xyseb"))
                if len(points) < 2: continue
                pts = []
                for p in points:
                    tx, ty = transform_point(p[0], p[1], matrix)
                    pts.append([round(tx, 3), round(ty, 3)])
                shapes.append({
                    "type": "polyline",
                    "points": pts,
                    "closed": bool(entity.closed),
                    "layer": layer,
                    "style": {"stroke": color, "fill": "none"}
                })
            elif dxf_type == "POLYLINE":
                pts = []
                for vertex in entity.vertices:
                    loc = vertex.dxf.location
                    tx, ty = transform_point(loc.x, loc.y, matrix)
                    pts.append([round(tx, 3), round(ty, 3)])
                if len(pts) < 2: continue
                shapes.append({
                    "type": "polyline",
                    "points": pts,
                    "closed": bool(entity.is_closed),
                    "layer": layer,
                    "style": {"stroke": color, "fill": "none"}
                })
            elif dxf_type in ("SPLINE", "ELLIPSE"):
                pts = list(entity.flattening(0.5))
                if len(pts) < 2: continue
                tpts = []
                for pt in pts:
                    tx, ty = transform_point(pt.x, pt.y, matrix)
                    tpts.append([round(tx, 3), round(ty, 3)])
                shapes.append({
                    "type": "polyline",
                    "points": tpts,
                    "closed": False,
                    "layer": layer,
                    "style": {"stroke": color, "fill": "none"}
                })
            elif dxf_type == "TEXT":
                x, y = transform_point(entity.dxf.insert.x, entity.dxf.insert.y, matrix)
                shapes.append({
                    "type": "text",
                    "x": round(x, 3), "y": round(y, 3),
                    "text": entity.dxf.text,
                    "fontSize": round(entity.dxf.height, 3) if entity.dxf.height else 12,
                    "layer": layer,
                    "style": {"stroke": color}
                })
            elif dxf_type == "MTEXT":
                x, y = transform_point(entity.dxf.insert.x, entity.dxf.insert.y, matrix)
                shapes.append({
                    "type": "text",
                    "x": round(x, 3), "y": round(y, 3),
                    "text": entity.plain_text(),
                    "fontSize": round(entity.dxf.char_height, 3) if entity.dxf.char_height else 12,
                    "layer": layer,
                    "style": {"stroke": color}
                })
            elif dxf_type == "POINT":
                x, y = transform_point(entity.dxf.location.x, entity.dxf.location.y, matrix)
                shapes.append({
                    "type": "point",
                    "x": round(x, 3), "y": round(y, 3),
                    "layer": layer,
                    "style": {"stroke": color}
                })
        except Exception:
            pass

    return layers, shapes


def parse_yaml_frontmatter(md_path):
    """Parse YAML frontmatter from an MD file. Returns dict or {}.
    Also extracts body text (after YAML) into key 'description' if present."""
    if not os.path.isfile(md_path):
        return {}
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {}

    # Extract YAML between --- markers
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    # Simple YAML parser for flat key: value pairs
    result = {}
    for line in match.group(1).split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
        m = re.match(r'^(\w[\w_]*)\s*:\s*"?([^"]*)"?\s*$', line)
        if m:
            result[m.group(1)] = m.group(2)

    # Extract body text (after second ---) as description if not already set
    body = content[match.end():].strip()
    # Remove markdown heading
    body = re.sub(r'^#[^\n]*\n*', '', body).strip()
    if body and 'description' not in result:
        result['description'] = body

    return result


def scan_new_hierarchy():
    """Scan components/ hierarchy and return list of DXF file entries.

    Each entry is a dict with: dxf_path, fabrikant, serie, product, variant,
    and metadata from MD files if available.
    """
    entries = []
    if not os.path.isdir(COMP_NEW):
        return entries

    for fab_name in sorted(os.listdir(COMP_NEW)):
        fab_dir = os.path.join(COMP_NEW, fab_name)
        if not os.path.isdir(fab_dir) or fab_name.startswith('.'):
            continue

        fab_meta = parse_yaml_frontmatter(os.path.join(fab_dir, "_fabrikant.md"))

        # Walk series (or sub-sources for Community)
        for serie_name in sorted(os.listdir(fab_dir)):
            serie_dir = os.path.join(fab_dir, serie_name)
            if not os.path.isdir(serie_dir) or serie_name.startswith('_'):
                continue

            # Handle Community/{sub-source}/{serie}/{product}
            if fab_name == "Community":
                sub_source = serie_name
                for actual_serie in sorted(os.listdir(serie_dir)):
                    actual_serie_dir = os.path.join(serie_dir, actual_serie)
                    if not os.path.isdir(actual_serie_dir) or actual_serie.startswith('_'):
                        continue
                    serie_meta = parse_yaml_frontmatter(
                        os.path.join(actual_serie_dir, "_serie.md"))
                    for product_name in sorted(os.listdir(actual_serie_dir)):
                        product_dir = os.path.join(actual_serie_dir, product_name)
                        if not os.path.isdir(product_dir) or product_name.startswith('_'):
                            continue
                        product_meta = parse_yaml_frontmatter(
                            os.path.join(product_dir, "_product.md"))
                        for f in sorted(os.listdir(product_dir)):
                            if f.lower().endswith('.dxf'):
                                entries.append({
                                    "dxf_path": os.path.join(product_dir, f),
                                    "fabrikant": f"{fab_name}/{sub_source}",
                                    "serie": actual_serie,
                                    "product": product_name,
                                    "variant": os.path.splitext(f)[0],
                                    "fab_meta": fab_meta,
                                    "serie_meta": serie_meta,
                                    "product_meta": product_meta,
                                })
                continue

            serie_meta = parse_yaml_frontmatter(os.path.join(serie_dir, "_serie.md"))

            for product_name in sorted(os.listdir(serie_dir)):
                product_dir = os.path.join(serie_dir, product_name)
                if not os.path.isdir(product_dir) or product_name.startswith('_'):
                    continue

                product_meta = parse_yaml_frontmatter(
                    os.path.join(product_dir, "_product.md"))

                for f in sorted(os.listdir(product_dir)):
                    if f.lower().endswith('.dxf'):
                        entries.append({
                            "dxf_path": os.path.join(product_dir, f),
                            "fabrikant": fab_name,
                            "serie": serie_name,
                            "product": product_name,
                            "variant": os.path.splitext(f)[0],
                            "fab_meta": fab_meta,
                            "serie_meta": serie_meta,
                            "product_meta": product_meta,
                        })

    return entries


def main_new():
    """Main function for new components/ hierarchy."""
    print("Scanning components/ hierarchy...")
    entries = scan_new_hierarchy()
    total_dxf = len(entries)
    print(f"Found {total_dxf} DXF files")
    print(f"Source: {COMP_NEW}")
    print(f"Output: {OUT_SVG}")
    print()

    if not entries:
        print("No DXF files found in components/. Run import_manufacturers.py first.")
        return

    seen_ids = set()
    cat_counts = {}
    fab_counts = {}
    components_json = []
    all_shapes = {}
    errors = []
    count = 0

    for entry in entries:
        count += 1
        dxf_path = entry["dxf_path"]
        fab_name = entry["fabrikant"]
        serie_name = entry["serie"]
        product_name = entry["product"]
        variant_name = entry["variant"]
        serie_meta = entry.get("serie_meta", {})
        product_meta = entry.get("product_meta", {})

        # 4-tier IFC classification resolution:
        # 1. Product-level metadata (_product.md)
        # 2. Serie-level metadata (_serie.md)
        # 3. SERIES_IFC_MAP lookup by serie name
        # 4. Fallback: IfcBuildingElementProxy / USERDEFINED
        ifc_class = product_meta.get("ifc_class") or ""
        ifc_pred = product_meta.get("ifc_predefined_type") or ""
        if not ifc_class:
            ifc_class = serie_meta.get("ifc_class") or ""
            ifc_pred = serie_meta.get("ifc_predefined_type") or ifc_pred
        if not ifc_class and serie_name in SERIES_IFC_MAP:
            ifc_class, ifc_pred = SERIES_IFC_MAP[serie_name]
        if not ifc_class:
            ifc_class = "IfcBuildingElementProxy"
        if not ifc_pred:
            ifc_pred = "USERDEFINED"

        # NL-SfB from metadata
        nl_sfb = product_meta.get("nl_sfb") or serie_meta.get("nl_sfb") or ""
        cat_id = nl_sfb if nl_sfb else "91"  # Default to "Overig"

        # Category name
        cat_meta = CATEGORIES.get(cat_id)
        if cat_meta:
            name_nl, name_en = cat_meta[0], cat_meta[1]
            nl_standard = cat_meta[4]
        else:
            name_nl = serie_name
            name_en = serie_name
            nl_standard = ""

        # Pset from IFC class
        ifc_cls_info = IFC_CLASSES.get(ifc_class, {})
        ifc_pset = ifc_cls_info.get("pset")
        pset_template = []
        if ifc_pset and ifc_pset in IFC_PSETS:
            pset_template = [p["name"] for p in IFC_PSETS[ifc_pset]["properties"]]

        # Material from serie
        material_info = SERIES_MATERIALS.get(serie_name)
        # Also check NL-SfB category name for Generic components
        if not material_info:
            for sfb_name, sfb_id in [("Wanden-metselwerk","21"),("Wanden-blokken","22"),("Vloeren","23")]:
                if cat_id == sfb_id:
                    material_info = SERIES_MATERIALS.get(sfb_name)
                    break

        # Generate component ID
        dxf_file = os.path.basename(dxf_path)
        id_prefix = safe_filename(fab_name.split('/')[0][:3])
        comp_id = make_component_id(id_prefix, dxf_file, seen_ids)
        display_name = make_display_name(dxf_file)
        svg_filename = f"{comp_id}.svg"
        svg_path = os.path.join(OUT_SVG, svg_filename)

        # Progress
        sys.stdout.write(f"\r  {count}/{total_dxf} [{fab_name}] {dxf_file[:40]:40s}")
        sys.stdout.flush()

        # Generate SVG
        try:
            width_mm, height_mm = generate_svg_ezdxf(dxf_path, svg_path)
        except Exception:
            try:
                width_mm, height_mm = generate_svg_manual(dxf_path, svg_path)
            except Exception as e2:
                errors.append(f"{fab_name}/{serie_name}/{dxf_file}: {e2}")
                continue

        # Extract O2D shapes
        try:
            _layers, o2d_shapes = extract_o2d_shapes(dxf_path)
            if o2d_shapes:
                all_shapes[comp_id] = o2d_shapes
        except Exception:
            pass

        cat_counts[cat_id] = cat_counts.get(cat_id, 0) + 1
        fab_counts[fab_name] = fab_counts.get(fab_name, 0) + 1
        tags = make_tags(dxf_file, name_nl)
        # Add manufacturer and serie as tags
        for extra_tag in [fab_name.split('/')[-1].lower(), serie_name.lower()]:
            extra_tag = re.sub(r'[^a-z0-9]', '', extra_tag)
            if extra_tag and len(extra_tag) > 1 and extra_tag not in tags:
                tags.append(extra_tag)
        tags = tags[:10]

        nl_props = {}
        if nl_standard:
            nl_props["standard"] = nl_standard

        # Relative DXF source path
        try:
            dxf_source = os.path.relpath(dxf_path, BASE).replace('\\', '/')
        except ValueError:
            dxf_source = dxf_path

        # IFC profile definition (from serie metadata)
        ifc_profile = serie_meta.get("ifc_profile", "")
        ifc_profile_data = {}
        if ifc_profile and ifc_profile in IFC_PROFILE_PARAMS:
            pdef = IFC_PROFILE_PARAMS[ifc_profile]
            ifc_profile_data = {
                "type": ifc_profile,
                "description": pdef["description"],
                "params": pdef["params"],
            }

        comp_entry = {
            "id": comp_id,
            "name": display_name,
            "manufacturer": fab_name,
            "serie": serie_name,
            "product": product_name,
            "ifc_class": ifc_class,
            "ifc_predefined_type": ifc_pred,
            "classification": {
                "nl_sfb": nl_sfb,
                "description_nl": name_nl,
                "description_en": name_en,
            },
            "geometry": {
                "width_mm": width_mm,
                "height_mm": height_mm,
                "svg": f"svg/{svg_filename}",
            },
            "properties": {
                "NL": nl_props,
            },
            "dxf_source": dxf_source,
            "tags": tags,
        }
        if ifc_pset:
            comp_entry["ifc_pset"] = ifc_pset
            comp_entry["pset_values"] = {}
            comp_entry["pset_template"] = pset_template
        if ifc_profile_data:
            comp_entry["ifc_profile"] = ifc_profile_data
        if material_info:
            comp_entry["material"] = material_info
        components_json.append(comp_entry)

    print()
    print()

    # Build IFC classes list (grouped by group)
    ifc_class_counts = {}
    for comp in components_json:
        cls = comp["ifc_class"]
        ifc_class_counts[cls] = ifc_class_counts.get(cls, 0) + 1

    ifc_classes_json = []
    for cls_name, cls_info in IFC_CLASSES.items():
        if cls_name in ifc_class_counts:
            ifc_classes_json.append({
                "id": cls_name,
                "name_nl": cls_info["name_nl"],
                "group": cls_info["group"],
                "pset": cls_info["pset"],
                "count": ifc_class_counts[cls_name],
            })

    # Build categories list (NL-SfB as secondary)
    categories_json = []
    for cat_id in sorted(cat_counts.keys()):
        meta = CATEGORIES.get(cat_id)
        if meta:
            categories_json.append({
                "id": cat_id,
                "name_nl": meta[0],
                "name_en": meta[1],
                "ifc_class": meta[2],
                "count": cat_counts[cat_id],
            })
        else:
            categories_json.append({
                "id": cat_id,
                "name_nl": cat_id,
                "name_en": cat_id,
                "ifc_class": "IfcBuildingElementProxy",
                "count": cat_counts[cat_id],
            })

    # Build series per manufacturer: {fab_name: {serie_name: count}}
    fab_series = {}
    for comp in components_json:
        fn = comp["manufacturer"]
        sn = comp["serie"]
        if fn not in fab_series:
            fab_series[fn] = {}
        fab_series[fn][sn] = fab_series[fn].get(sn, 0) + 1

    # Build manufacturers list (enriched with metadata + series)
    manufacturers_json = []
    for fab_name in sorted(fab_counts.keys()):
        # Read _fabrikant.md for extra metadata
        fab_dir = os.path.join(COMP_NEW, fab_name)
        fab_meta = parse_yaml_frontmatter(os.path.join(fab_dir, "_fabrikant.md"))

        series_list = []
        for sname in sorted(fab_series.get(fab_name, {}).keys()):
            serie_dir = os.path.join(fab_dir, sname)
            serie_meta = parse_yaml_frontmatter(os.path.join(serie_dir, "_serie.md"))
            serie_entry = {
                "name": sname,
                "count": fab_series[fab_name][sname],
                "ifc_class": serie_meta.get("ifc_class", ""),
            }
            ifc_prof = serie_meta.get("ifc_profile", "")
            if ifc_prof:
                serie_entry["ifc_profile"] = ifc_prof
            series_list.append(serie_entry)

        manufacturers_json.append({
            "id": safe_filename(fab_name),
            "name": fab_name,
            "count": fab_counts[fab_name],
            "status": fab_meta.get("status", "active"),
            "country": fab_meta.get("country", ""),
            "founded": fab_meta.get("founded", ""),
            "website": fab_meta.get("website", ""),
            "description": fab_meta.get("description", ""),
            "series": series_list,
        })

    # Build database
    db = {
        "$schema": "component-library-v3",
        "metadata": {
            "version": "3.0",
            "generated": str(date.today()),
            "total": len(components_json),
            "project": "Project OconDat",
        },
        "ifc_classes": ifc_classes_json,
        "pset_definitions": IFC_PSETS,
        "categories": categories_json,
        "manufacturers": manufacturers_json,
        "components": components_json,
    }

    write_output(db, all_shapes, total_dxf, components_json, errors)


def main_legacy():
    """Main function for legacy Componenten/ structure."""
    # Scan all category folders
    folders = sorted([
        d for d in os.listdir(COMP_DIR)
        if os.path.isdir(os.path.join(COMP_DIR, d)) and re.match(r'^\d{2}\s', d)
    ])

    # Count total DXFs
    total_dxf = 0
    for folder in folders:
        total_dxf += len([f for f in os.listdir(os.path.join(COMP_DIR, folder))
                          if f.lower().endswith('.dxf')])

    print(f"Scanning {len(folders)} categories, {total_dxf} DXF files... (legacy mode)")
    print(f"Source: {COMP_DIR}")
    print(f"Output: {OUT_SVG}")
    print()

    seen_ids = set()
    cat_counts = {}
    components_json = []
    all_shapes = {}
    errors = []
    count = 0

    for folder in folders:
        cat_id = folder[:2]
        cat_meta = CATEGORIES.get(cat_id)
        if not cat_meta:
            print(f"  SKIP: Unknown category '{folder}'")
            continue

        name_nl, name_en, ifc_class, ifc_pred, nl_standard = cat_meta
        folder_path = os.path.join(COMP_DIR, folder)
        dxf_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.dxf')])

        # Pset from IFC class
        ifc_cls_info = IFC_CLASSES.get(ifc_class, {})
        ifc_pset = ifc_cls_info.get("pset")
        pset_template = []
        if ifc_pset and ifc_pset in IFC_PSETS:
            pset_template = [p["name"] for p in IFC_PSETS[ifc_pset]["properties"]]

        print(f"  [{cat_id}] {name_nl} ({len(dxf_files)} files)")

        for dxf_file in dxf_files:
            count += 1
            dxf_path = os.path.join(folder_path, dxf_file)
            comp_id = make_component_id(cat_id, dxf_file, seen_ids)
            display_name = make_display_name(dxf_file)
            svg_filename = f"{comp_id}.svg"
            svg_path = os.path.join(OUT_SVG, svg_filename)

            sys.stdout.write(f"\r    {count}/{total_dxf} {dxf_file[:50]:50s}")
            sys.stdout.flush()

            try:
                width_mm, height_mm = generate_svg_ezdxf(dxf_path, svg_path)
            except Exception:
                try:
                    width_mm, height_mm = generate_svg_manual(dxf_path, svg_path)
                except Exception as e2:
                    errors.append(f"{folder}/{dxf_file}: {e2}")
                    continue

            try:
                _layers, o2d_shapes = extract_o2d_shapes(dxf_path)
                if o2d_shapes:
                    all_shapes[comp_id] = o2d_shapes
            except Exception:
                pass

            cat_counts[cat_id] = cat_counts.get(cat_id, 0) + 1
            tags = make_tags(dxf_file, name_nl)

            nl_props = {}
            if nl_standard:
                nl_props["standard"] = nl_standard

            comp_entry = {
                "id": comp_id,
                "name": display_name,
                "manufacturer": "Generic",
                "serie": name_nl,
                "product": display_name,
                "ifc_class": ifc_class,
                "ifc_predefined_type": ifc_pred,
                "classification": {
                    "nl_sfb": cat_id,
                    "description_nl": name_nl,
                    "description_en": name_en,
                },
                "geometry": {
                    "width_mm": width_mm,
                    "height_mm": height_mm,
                    "svg": f"svg/{svg_filename}",
                },
                "properties": {
                    "NL": nl_props,
                },
                "dxf_source": f"Componenten/{folder}/{dxf_file}",
                "tags": tags,
            }
            if ifc_pset:
                comp_entry["ifc_pset"] = ifc_pset
                comp_entry["pset_values"] = {}
                comp_entry["pset_template"] = pset_template
            components_json.append(comp_entry)

        print()

    # Build IFC classes list
    ifc_class_counts = {}
    for comp in components_json:
        cls = comp["ifc_class"]
        ifc_class_counts[cls] = ifc_class_counts.get(cls, 0) + 1

    ifc_classes_json = []
    for cls_name, cls_info in IFC_CLASSES.items():
        if cls_name in ifc_class_counts:
            ifc_classes_json.append({
                "id": cls_name,
                "name_nl": cls_info["name_nl"],
                "group": cls_info["group"],
                "pset": cls_info["pset"],
                "count": ifc_class_counts[cls_name],
            })

    # Build categories list (NL-SfB as secondary)
    categories_json = []
    for cat_id in sorted(cat_counts.keys()):
        meta = CATEGORIES[cat_id]
        categories_json.append({
            "id": cat_id,
            "name_nl": meta[0],
            "name_en": meta[1],
            "ifc_class": meta[2],
            "count": cat_counts[cat_id],
        })

    # Build manufacturers list (just "Generic" in legacy mode)
    manufacturers_json = [{
        "id": "generic",
        "name": "Generic",
        "count": len(components_json),
    }]

    # Build database
    db = {
        "$schema": "component-library-v3",
        "metadata": {
            "version": "3.0",
            "generated": str(date.today()),
            "total": len(components_json),
            "project": "Project OconDat",
        },
        "ifc_classes": ifc_classes_json,
        "pset_definitions": IFC_PSETS,
        "categories": categories_json,
        "manufacturers": manufacturers_json,
        "components": components_json,
    }

    write_output(db, all_shapes, total_dxf, components_json, errors)


def write_output(db, all_shapes, total_dxf, components_json, errors):
    """Write all output files (shared between legacy and new modes)."""
    # Write components.json
    json_path = os.path.join(OUT_DATA, "components.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    # Write data.js
    js_path = os.path.join(OUT_JS, "data.js")
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write("/* Auto-generated by gen_library.py - do not edit */\n")
        f.write("var DB = ")
        json.dump(db, f, ensure_ascii=False)
        f.write(";\n")

    # Write shapes.js
    shapes_path = os.path.join(OUT_JS, "shapes.js")
    with open(shapes_path, 'w', encoding='utf-8') as f:
        f.write("/* Auto-generated by gen_library.py - O2D shapes for Open 2D Studio export */\n")
        f.write("var SHAPES = ")
        json.dump(all_shapes, f, ensure_ascii=False, separators=(',', ':'))
        f.write(";\n")

    shapes_mb = os.path.getsize(shapes_path) / (1024 * 1024)
    fab_count = len(db.get("manufacturers", []))

    print()
    print(f"Done: {len(components_json)} / {total_dxf} components generated")
    print(f"Manufacturers: {fab_count}")
    print(f"SVGs: {OUT_SVG}")
    print(f"Database: {json_path}")
    print(f"Data.js: {js_path}")
    print(f"Shapes.js: {shapes_path} ({shapes_mb:.1f} MB, {len(all_shapes)} components with shapes)")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
    else:
        print("No errors.")


def main():
    parser = argparse.ArgumentParser(description="Generate component library")
    parser.add_argument("--legacy", action="store_true",
                        help="Use legacy Componenten/ folder structure")
    args = parser.parse_args()

    if args.legacy or not os.path.isdir(COMP_NEW):
        if not os.path.isdir(COMP_NEW) and not args.legacy:
            print("components/ not found, falling back to legacy Componenten/ mode")
            print()
        main_legacy()
    else:
        main_new()


if __name__ == "__main__":
    main()
