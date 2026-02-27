# -*- coding: utf-8 -*-
"""
Staalprofielen Database
=======================
Nederlandse staalprofielenbibliotheek volgens Europese normen.
Alle afmetingen in mm, oppervlaktes in cm², gewichten in kg/m.

Bronnen:
- NEN-EN 10025 (Warmgewalst constructiestaal)
- NEN-EN 10210 (Warmgevormde constructiebuizen)
- NEN-EN 10219 (Koudgevormde constructiebuizen)
- Staaltabellen (ArcelorMittal, Tata Steel, etc.)
"""

# =============================================================================
# PROFIELVORM DEFINITIES
# =============================================================================

PROFIELVORMEN = {
    "I-shape parallel flange": {
        "beschrijving": "I-profiel met evenwijdige flenzen",
        "params": ["h", "b", "tw", "tf", "r"],
        "param_namen": {
            "h": "hoogte",
            "b": "flensbrredte",
            "tw": "lijfdikte",
            "tf": "flensdikte",
            "r": "afrondingsstraal"
        },
        "ifc_type": "IfcIShapeProfileDef"
    },
    "I-shape sloped flange": {
        "beschrijving": "I-profiel met schuine flenzen",
        "params": ["h", "b", "tw", "tf", "r"],
        "param_namen": {
            "h": "hoogte",
            "b": "flensbreedte",
            "tw": "lijfdikte",
            "tf": "flensdikte",
            "r": "afrondingsstraal"
        },
        "ifc_type": "IfcIShapeProfileDef"
    },
    "C-channel parallel flange": {
        "beschrijving": "U-profiel met evenwijdige flenzen",
        "params": ["h", "b", "tw", "tf", "r", "ey"],
        "param_namen": {
            "h": "hoogte",
            "b": "flensbreedte",
            "tw": "lijfdikte",
            "tf": "flensdikte",
            "r": "afrondingsstraal",
            "ey": "zwaartepunt afstand"
        },
        "ifc_type": "IfcUShapeProfileDef"
    },
    "C-channel sloped flange": {
        "beschrijving": "U-profiel met schuine flenzen",
        "params": ["h", "b", "tw", "tf", "r1", "r2", "ey", "slope", "ey2"],
        "param_namen": {
            "h": "hoogte",
            "b": "flensbreedte",
            "tw": "lijfdikte",
            "tf": "flensdikte",
            "r1": "binnenstraal",
            "r2": "flensteenstraal"
        },
        "ifc_type": "IfcUShapeProfileDef"
    },
    "Rectangle Hollow Section": {
        "beschrijving": "Rechthoekige koker (RHS/SHS)",
        "params": ["h", "b", "t", "ro", "ri"],
        "param_namen": {
            "h": "hoogte",
            "b": "breedte",
            "t": "wanddikte",
            "ro": "buitenstraal",
            "ri": "binnenstraal"
        },
        "ifc_type": "IfcRectangleHollowProfileDef"
    },
    "Round tube profile": {
        "beschrijving": "Ronde buis (CHS)",
        "params": ["d", "t"],
        "param_namen": {
            "d": "buitendiameter",
            "t": "wanddikte"
        },
        "ifc_type": "IfcCircleHollowProfileDef"
    },
    "Rectangle": {
        "beschrijving": "Vlakstaal",
        "params": ["b", "t"],
        "param_namen": {
            "b": "breedte",
            "t": "dikte"
        },
        "ifc_type": "IfcRectangleProfileDef"
    },
    "TProfile": {
        "beschrijving": "T-profiel",
        "params": ["h", "b", "tw", "tf", "r1", "r2", "r3", "ey", "A"],
        "param_namen": {
            "h": "hoogte",
            "b": "flensbreedte",
            "tw": "lijfdikte",
            "tf": "flensdikte"
        },
        "ifc_type": "IfcTShapeProfileDef"
    },
    "LProfile": {
        "beschrijving": "Hoeklijn (gelijkzijdig of ongelijkzijdig)",
        "params": ["h", "b", "t", "r1", "r2"],
        "param_namen": {
            "h": "hoogte",
            "b": "breedte",
            "t": "dikte",
            "r1": "binnenstraal",
            "r2": "teenstraal"
        },
        "ifc_type": "IfcLShapeProfileDef"
    }
}


# =============================================================================
# LOCALISATIE - GANGBARE PROFIELEN IN NEDERLAND
# =============================================================================

NL_GANGBARE_PROFIELEN = {
    "I-profielen": {
        "beschrijving": "Standaard I-profielen gangbaar in Nederlandse bouw",
        "series": ["HEA", "HEB", "HEM", "IPE"],
        "opmerking": "HEA/HEB/IPE zijn de meest toegepaste profielen in NL constructies"
    },
    "U-profielen": {
        "beschrijving": "Standaard U-profielen gangbaar in Nederlandse bouw",
        "series": ["UNP", "UPE", "UAP"],
        "opmerking": "UNP met schuine flenzen, UPE met evenwijdige flenzen"
    },
    "Kokerprofielen": {
        "beschrijving": "Vierkante en rechthoekige kokers",
        "series": ["SHS", "RHS", "K"],
        "opmerking": "K-aanduiding is Nederlandse notatie (Koker)"
    },
    "Buisprofielen": {
        "beschrijving": "Ronde buizen (CHS)",
        "series": ["B", "CHS", "Buis"],
        "opmerking": "B-aanduiding is Nederlandse notatie (Buis)"
    },
    "Historisch": {
        "beschrijving": "Oudere profielen die nog in bestaande bouw voorkomen",
        "series": ["INP", "NP", "DIL", "DIE", "DIN"],
        "opmerking": "Differdinger profielen (DIL/DIE/DIN) uit Luxemburg, historisch veel toegepast in NL"
    }
}


# =============================================================================
# PROFIELSERIES MET EIGENSCHAPPEN
# =============================================================================

# HEA - Europees breed flens profiel (licht)
HEA_PROFIELEN = {
    "HEA100": {"h": 96, "b": 100, "tw": 5, "tf": 8, "r": 12, "A": 21.2, "G": 16.7, "Iy": 349, "Iz": 134},
    "HEA120": {"h": 114, "b": 120, "tw": 5, "tf": 8, "r": 12, "A": 25.3, "G": 19.9, "Iy": 606, "Iz": 231},
    "HEA140": {"h": 133, "b": 140, "tw": 5.5, "tf": 8.5, "r": 12, "A": 31.4, "G": 24.7, "Iy": 1030, "Iz": 389},
    "HEA160": {"h": 152, "b": 160, "tw": 6, "tf": 9, "r": 15, "A": 38.8, "G": 30.4, "Iy": 1670, "Iz": 616},
    "HEA180": {"h": 171, "b": 180, "tw": 6, "tf": 9.5, "r": 15, "A": 45.3, "G": 35.5, "Iy": 2510, "Iz": 925},
    "HEA200": {"h": 190, "b": 200, "tw": 6.5, "tf": 10, "r": 18, "A": 53.8, "G": 42.3, "Iy": 3690, "Iz": 1340},
    "HEA220": {"h": 210, "b": 220, "tw": 7, "tf": 11, "r": 18, "A": 64.3, "G": 50.5, "Iy": 5410, "Iz": 1950},
    "HEA240": {"h": 230, "b": 240, "tw": 7.5, "tf": 12, "r": 21, "A": 76.8, "G": 60.3, "Iy": 7760, "Iz": 2770},
    "HEA260": {"h": 250, "b": 260, "tw": 7.5, "tf": 12.5, "r": 24, "A": 86.8, "G": 68.2, "Iy": 10450, "Iz": 3670},
    "HEA280": {"h": 270, "b": 280, "tw": 8, "tf": 13, "r": 24, "A": 97.3, "G": 76.4, "Iy": 13670, "Iz": 4760},
    "HEA300": {"h": 290, "b": 300, "tw": 8.5, "tf": 14, "r": 27, "A": 112.5, "G": 88.3, "Iy": 18260, "Iz": 6310},
    "HEA320": {"h": 310, "b": 300, "tw": 9, "tf": 15.5, "r": 27, "A": 124.4, "G": 97.6, "Iy": 22930, "Iz": 6990},
    "HEA340": {"h": 330, "b": 300, "tw": 9.5, "tf": 16.5, "r": 27, "A": 133.5, "G": 104.8, "Iy": 27690, "Iz": 7440},
    "HEA360": {"h": 350, "b": 300, "tw": 10, "tf": 17.5, "r": 27, "A": 142.8, "G": 112.1, "Iy": 33090, "Iz": 7890},
    "HEA400": {"h": 390, "b": 300, "tw": 11, "tf": 19, "r": 27, "A": 159.0, "G": 124.8, "Iy": 45070, "Iz": 8560},
    "HEA450": {"h": 440, "b": 300, "tw": 11.5, "tf": 21, "r": 27, "A": 178.0, "G": 139.7, "Iy": 63720, "Iz": 9470},
    "HEA500": {"h": 490, "b": 300, "tw": 12, "tf": 23, "r": 27, "A": 197.5, "G": 155.1, "Iy": 86970, "Iz": 10370},
    "HEA550": {"h": 540, "b": 300, "tw": 12.5, "tf": 24, "r": 27, "A": 211.8, "G": 166.2, "Iy": 111900, "Iz": 10820},
    "HEA600": {"h": 590, "b": 300, "tw": 13, "tf": 25, "r": 27, "A": 226.5, "G": 177.8, "Iy": 141200, "Iz": 11270},
    "HEA650": {"h": 640, "b": 300, "tw": 13.5, "tf": 26, "r": 27, "A": 241.6, "G": 189.6, "Iy": 175200, "Iz": 11720},
    "HEA700": {"h": 690, "b": 300, "tw": 14.5, "tf": 27, "r": 27, "A": 260.5, "G": 204.5, "Iy": 215300, "Iz": 12180},
    "HEA800": {"h": 790, "b": 300, "tw": 15, "tf": 28, "r": 30, "A": 285.8, "G": 224.4, "Iy": 303400, "Iz": 12640},
    "HEA900": {"h": 890, "b": 300, "tw": 16, "tf": 30, "r": 30, "A": 320.5, "G": 251.6, "Iy": 422100, "Iz": 13550},
    "HEA1000": {"h": 990, "b": 300, "tw": 16.5, "tf": 31, "r": 30, "A": 346.8, "G": 272.2, "Iy": 553800, "Iz": 14010},
}

# HEB - Europees breed flens profiel (standaard)
HEB_PROFIELEN = {
    "HEB100": {"h": 100, "b": 100, "tw": 6, "tf": 10, "r": 12, "A": 26.0, "G": 20.4, "Iy": 450, "Iz": 167},
    "HEB120": {"h": 120, "b": 120, "tw": 6.5, "tf": 11, "r": 12, "A": 34.0, "G": 26.7, "Iy": 864, "Iz": 318},
    "HEB140": {"h": 140, "b": 140, "tw": 7, "tf": 12, "r": 12, "A": 43.0, "G": 33.7, "Iy": 1510, "Iz": 550},
    "HEB160": {"h": 160, "b": 160, "tw": 8, "tf": 13, "r": 15, "A": 54.3, "G": 42.6, "Iy": 2490, "Iz": 889},
    "HEB180": {"h": 180, "b": 180, "tw": 8.5, "tf": 14, "r": 15, "A": 65.3, "G": 51.2, "Iy": 3830, "Iz": 1360},
    "HEB200": {"h": 200, "b": 200, "tw": 9, "tf": 15, "r": 18, "A": 78.1, "G": 61.3, "Iy": 5700, "Iz": 2000},
    "HEB220": {"h": 220, "b": 220, "tw": 9.5, "tf": 16, "r": 18, "A": 91.0, "G": 71.5, "Iy": 8090, "Iz": 2840},
    "HEB240": {"h": 240, "b": 240, "tw": 10, "tf": 17, "r": 21, "A": 106.0, "G": 83.2, "Iy": 11260, "Iz": 3920},
    "HEB260": {"h": 260, "b": 260, "tw": 10, "tf": 17.5, "r": 24, "A": 118.4, "G": 93.0, "Iy": 14920, "Iz": 5130},
    "HEB280": {"h": 280, "b": 280, "tw": 10.5, "tf": 18, "r": 24, "A": 131.4, "G": 103.1, "Iy": 19270, "Iz": 6590},
    "HEB300": {"h": 300, "b": 300, "tw": 11, "tf": 19, "r": 27, "A": 149.1, "G": 117.0, "Iy": 25170, "Iz": 8560},
    "HEB320": {"h": 320, "b": 300, "tw": 11.5, "tf": 20.5, "r": 27, "A": 161.3, "G": 126.6, "Iy": 30820, "Iz": 9240},
    "HEB340": {"h": 340, "b": 300, "tw": 12, "tf": 21.5, "r": 27, "A": 170.9, "G": 134.2, "Iy": 36660, "Iz": 9690},
    "HEB360": {"h": 360, "b": 300, "tw": 12.5, "tf": 22.5, "r": 27, "A": 180.6, "G": 141.8, "Iy": 43190, "Iz": 10140},
    "HEB400": {"h": 400, "b": 300, "tw": 13.5, "tf": 24, "r": 27, "A": 197.8, "G": 155.3, "Iy": 57680, "Iz": 10820},
    "HEB450": {"h": 450, "b": 300, "tw": 14, "tf": 26, "r": 27, "A": 218.0, "G": 171.1, "Iy": 79890, "Iz": 11720},
    "HEB500": {"h": 500, "b": 300, "tw": 14.5, "tf": 28, "r": 27, "A": 238.6, "G": 187.3, "Iy": 107200, "Iz": 12620},
    "HEB550": {"h": 550, "b": 300, "tw": 15, "tf": 29, "r": 27, "A": 254.1, "G": 199.5, "Iy": 136700, "Iz": 13080},
    "HEB600": {"h": 600, "b": 300, "tw": 15.5, "tf": 30, "r": 27, "A": 270.0, "G": 212.0, "Iy": 171000, "Iz": 13530},
    "HEB650": {"h": 650, "b": 300, "tw": 16, "tf": 31, "r": 27, "A": 286.3, "G": 224.8, "Iy": 210600, "Iz": 13980},
    "HEB700": {"h": 700, "b": 300, "tw": 17, "tf": 32, "r": 27, "A": 306.4, "G": 240.5, "Iy": 256900, "Iz": 14440},
    "HEB800": {"h": 800, "b": 300, "tw": 17.5, "tf": 33, "r": 30, "A": 334.2, "G": 262.4, "Iy": 359100, "Iz": 14900},
    "HEB900": {"h": 900, "b": 300, "tw": 18.5, "tf": 35, "r": 30, "A": 371.3, "G": 291.5, "Iy": 494100, "Iz": 15820},
    "HEB1000": {"h": 1000, "b": 300, "tw": 19, "tf": 36, "r": 30, "A": 400.0, "G": 314.0, "Iy": 644700, "Iz": 16280},
}

# IPE - Europees I-profiel
IPE_PROFIELEN = {
    "IPE80": {"h": 80, "b": 46, "tw": 3.8, "tf": 5.2, "r": 5, "A": 7.64, "G": 6.0, "Iy": 80.1, "Iz": 8.49},
    "IPE100": {"h": 100, "b": 55, "tw": 4.1, "tf": 5.7, "r": 7, "A": 10.3, "G": 8.1, "Iy": 171, "Iz": 15.9},
    "IPE120": {"h": 120, "b": 64, "tw": 4.4, "tf": 6.3, "r": 7, "A": 13.2, "G": 10.4, "Iy": 318, "Iz": 27.7},
    "IPE140": {"h": 140, "b": 73, "tw": 4.7, "tf": 6.9, "r": 7, "A": 16.4, "G": 12.9, "Iy": 541, "Iz": 44.9},
    "IPE160": {"h": 160, "b": 82, "tw": 5.0, "tf": 7.4, "r": 9, "A": 20.1, "G": 15.8, "Iy": 869, "Iz": 68.3},
    "IPE180": {"h": 180, "b": 91, "tw": 5.3, "tf": 8.0, "r": 9, "A": 23.9, "G": 18.8, "Iy": 1320, "Iz": 101},
    "IPE200": {"h": 200, "b": 100, "tw": 5.6, "tf": 8.5, "r": 12, "A": 28.5, "G": 22.4, "Iy": 1940, "Iz": 142},
    "IPE220": {"h": 220, "b": 110, "tw": 5.9, "tf": 9.2, "r": 12, "A": 33.4, "G": 26.2, "Iy": 2770, "Iz": 205},
    "IPE240": {"h": 240, "b": 120, "tw": 6.2, "tf": 9.8, "r": 15, "A": 39.1, "G": 30.7, "Iy": 3890, "Iz": 284},
    "IPE270": {"h": 270, "b": 135, "tw": 6.6, "tf": 10.2, "r": 15, "A": 45.9, "G": 36.1, "Iy": 5790, "Iz": 420},
    "IPE300": {"h": 300, "b": 150, "tw": 7.1, "tf": 10.7, "r": 15, "A": 53.8, "G": 42.2, "Iy": 8360, "Iz": 604},
    "IPE330": {"h": 330, "b": 160, "tw": 7.5, "tf": 11.5, "r": 18, "A": 62.6, "G": 49.1, "Iy": 11770, "Iz": 788},
    "IPE360": {"h": 360, "b": 170, "tw": 8.0, "tf": 12.7, "r": 18, "A": 72.7, "G": 57.1, "Iy": 16270, "Iz": 1040},
    "IPE400": {"h": 400, "b": 180, "tw": 8.6, "tf": 13.5, "r": 21, "A": 84.5, "G": 66.3, "Iy": 23130, "Iz": 1320},
    "IPE450": {"h": 450, "b": 190, "tw": 9.4, "tf": 14.6, "r": 21, "A": 98.8, "G": 77.6, "Iy": 33740, "Iz": 1680},
    "IPE500": {"h": 500, "b": 200, "tw": 10.2, "tf": 16.0, "r": 21, "A": 116.0, "G": 90.7, "Iy": 48200, "Iz": 2140},
    "IPE550": {"h": 550, "b": 210, "tw": 11.1, "tf": 17.2, "r": 24, "A": 134.4, "G": 105.5, "Iy": 67120, "Iz": 2670},
    "IPE600": {"h": 600, "b": 220, "tw": 12.0, "tf": 19.0, "r": 24, "A": 156.0, "G": 122.4, "Iy": 92080, "Iz": 3390},
}

# UNP - U-profiel met schuine flenzen
UNP_PROFIELEN = {
    "UNP80": {"h": 80, "b": 45, "tw": 6, "tf": 8, "r": 8, "A": 11.0, "G": 8.64, "Iy": 106, "Iz": 19.4, "ey": 14.5},
    "UNP100": {"h": 100, "b": 50, "tw": 6, "tf": 8.5, "r": 8.5, "A": 13.5, "G": 10.6, "Iy": 206, "Iz": 29.3, "ey": 15.5},
    "UNP120": {"h": 120, "b": 55, "tw": 7, "tf": 9, "r": 9, "A": 17.0, "G": 13.4, "Iy": 364, "Iz": 43.2, "ey": 16.0},
    "UNP140": {"h": 140, "b": 60, "tw": 7, "tf": 10, "r": 10, "A": 20.4, "G": 16.0, "Iy": 605, "Iz": 62.7, "ey": 17.5},
    "UNP160": {"h": 160, "b": 65, "tw": 7.5, "tf": 10.5, "r": 10.5, "A": 24.0, "G": 18.8, "Iy": 925, "Iz": 85.3, "ey": 18.4},
    "UNP180": {"h": 180, "b": 70, "tw": 8, "tf": 11, "r": 11, "A": 28.0, "G": 22.0, "Iy": 1350, "Iz": 114, "ey": 19.2},
    "UNP200": {"h": 200, "b": 75, "tw": 8.5, "tf": 11.5, "r": 11.5, "A": 32.2, "G": 25.3, "Iy": 1910, "Iz": 148, "ey": 20.1},
    "UNP220": {"h": 220, "b": 80, "tw": 9, "tf": 12.5, "r": 12.5, "A": 37.4, "G": 29.4, "Iy": 2690, "Iz": 197, "ey": 21.4},
    "UNP240": {"h": 240, "b": 85, "tw": 9.5, "tf": 13, "r": 13, "A": 42.3, "G": 33.2, "Iy": 3600, "Iz": 248, "ey": 22.3},
    "UNP260": {"h": 260, "b": 90, "tw": 10, "tf": 14, "r": 14, "A": 48.3, "G": 37.9, "Iy": 4820, "Iz": 317, "ey": 23.6},
    "UNP280": {"h": 280, "b": 95, "tw": 10, "tf": 15, "r": 15, "A": 53.3, "G": 41.8, "Iy": 6280, "Iz": 399, "ey": 25.3},
    "UNP300": {"h": 300, "b": 100, "tw": 10, "tf": 16, "r": 16, "A": 58.8, "G": 46.2, "Iy": 8030, "Iz": 495, "ey": 27.0},
    "UNP320": {"h": 320, "b": 100, "tw": 14, "tf": 17.5, "r": 17.5, "A": 75.8, "G": 59.5, "Iy": 10870, "Iz": 597, "ey": 26.0},
    "UNP350": {"h": 350, "b": 100, "tw": 14, "tf": 16, "r": 16, "A": 77.3, "G": 60.6, "Iy": 12840, "Iz": 570, "ey": 24.0},
    "UNP380": {"h": 380, "b": 102, "tw": 13.5, "tf": 16, "r": 16, "A": 80.4, "G": 63.1, "Iy": 15760, "Iz": 615, "ey": 23.8},
    "UNP400": {"h": 400, "b": 110, "tw": 14, "tf": 18, "r": 18, "A": 91.5, "G": 71.8, "Iy": 20350, "Iz": 846, "ey": 26.5},
}

# Vierkante kokers (SHS)
SHS_PROFIELEN = {
    "SHS40x3": {"h": 40, "b": 40, "t": 3, "A": 4.24, "G": 3.33, "I": 8.92},
    "SHS40x4": {"h": 40, "b": 40, "t": 4, "A": 5.35, "G": 4.20, "I": 10.6},
    "SHS50x3": {"h": 50, "b": 50, "t": 3, "A": 5.44, "G": 4.27, "I": 18.6},
    "SHS50x4": {"h": 50, "b": 50, "t": 4, "A": 6.95, "G": 5.46, "I": 22.8},
    "SHS50x5": {"h": 50, "b": 50, "t": 5, "A": 8.36, "G": 6.56, "I": 26.0},
    "SHS60x3": {"h": 60, "b": 60, "t": 3, "A": 6.64, "G": 5.21, "I": 33.2},
    "SHS60x4": {"h": 60, "b": 60, "t": 4, "A": 8.55, "G": 6.71, "I": 41.4},
    "SHS60x5": {"h": 60, "b": 60, "t": 5, "A": 10.4, "G": 8.13, "I": 48.1},
    "SHS70x4": {"h": 70, "b": 70, "t": 4, "A": 10.2, "G": 7.97, "I": 67.9},
    "SHS70x5": {"h": 70, "b": 70, "t": 5, "A": 12.4, "G": 9.70, "I": 80.1},
    "SHS80x4": {"h": 80, "b": 80, "t": 4, "A": 11.8, "G": 9.22, "I": 103},
    "SHS80x5": {"h": 80, "b": 80, "t": 5, "A": 14.4, "G": 11.3, "I": 123},
    "SHS80x6": {"h": 80, "b": 80, "t": 6, "A": 16.9, "G": 13.2, "I": 140},
    "SHS90x5": {"h": 90, "b": 90, "t": 5, "A": 16.4, "G": 12.9, "I": 178},
    "SHS90x6": {"h": 90, "b": 90, "t": 6, "A": 19.3, "G": 15.1, "I": 204},
    "SHS100x4": {"h": 100, "b": 100, "t": 4, "A": 15.0, "G": 11.8, "I": 214},
    "SHS100x5": {"h": 100, "b": 100, "t": 5, "A": 18.4, "G": 14.5, "I": 257},
    "SHS100x6": {"h": 100, "b": 100, "t": 6, "A": 21.7, "G": 17.0, "I": 296},
    "SHS100x8": {"h": 100, "b": 100, "t": 8, "A": 27.9, "G": 21.9, "I": 360},
    "SHS120x5": {"h": 120, "b": 120, "t": 5, "A": 22.4, "G": 17.6, "I": 462},
    "SHS120x6": {"h": 120, "b": 120, "t": 6, "A": 26.5, "G": 20.8, "I": 538},
    "SHS120x8": {"h": 120, "b": 120, "t": 8, "A": 34.3, "G": 26.9, "I": 667},
    "SHS140x5": {"h": 140, "b": 140, "t": 5, "A": 26.4, "G": 20.7, "I": 746},
    "SHS140x6": {"h": 140, "b": 140, "t": 6, "A": 31.3, "G": 24.6, "I": 871},
    "SHS140x8": {"h": 140, "b": 140, "t": 8, "A": 40.7, "G": 32.0, "I": 1100},
    "SHS150x5": {"h": 150, "b": 150, "t": 5, "A": 28.4, "G": 22.3, "I": 926},
    "SHS150x6": {"h": 150, "b": 150, "t": 6, "A": 33.7, "G": 26.4, "I": 1080},
    "SHS150x8": {"h": 150, "b": 150, "t": 8, "A": 43.9, "G": 34.5, "I": 1370},
    "SHS160x5": {"h": 160, "b": 160, "t": 5, "A": 30.4, "G": 23.9, "I": 1130},
    "SHS160x6": {"h": 160, "b": 160, "t": 6, "A": 36.1, "G": 28.3, "I": 1320},
    "SHS160x8": {"h": 160, "b": 160, "t": 8, "A": 47.1, "G": 37.0, "I": 1680},
    "SHS180x6": {"h": 180, "b": 180, "t": 6, "A": 40.9, "G": 32.1, "I": 1920},
    "SHS180x8": {"h": 180, "b": 180, "t": 8, "A": 53.5, "G": 42.0, "I": 2450},
    "SHS180x10": {"h": 180, "b": 180, "t": 10, "A": 65.3, "G": 51.2, "I": 2910},
    "SHS200x6": {"h": 200, "b": 200, "t": 6, "A": 45.7, "G": 35.8, "I": 2700},
    "SHS200x8": {"h": 200, "b": 200, "t": 8, "A": 59.9, "G": 47.0, "I": 3470},
    "SHS200x10": {"h": 200, "b": 200, "t": 10, "A": 73.5, "G": 57.7, "I": 4150},
    "SHS250x6": {"h": 250, "b": 250, "t": 6, "A": 57.7, "G": 45.3, "I": 5430},
    "SHS250x8": {"h": 250, "b": 250, "t": 8, "A": 75.9, "G": 59.6, "I": 7030},
    "SHS250x10": {"h": 250, "b": 250, "t": 10, "A": 93.5, "G": 73.4, "I": 8500},
    "SHS300x8": {"h": 300, "b": 300, "t": 8, "A": 91.9, "G": 72.1, "I": 12400},
    "SHS300x10": {"h": 300, "b": 300, "t": 10, "A": 114, "G": 89.2, "I": 15100},
    "SHS300x12.5": {"h": 300, "b": 300, "t": 12.5, "A": 139, "G": 109, "I": 18000},
}

# Ronde buizen (CHS)
CHS_PROFIELEN = {
    "CHS42.4x3": {"d": 42.4, "t": 3, "A": 3.71, "G": 2.91, "I": 7.62},
    "CHS48.3x3": {"d": 48.3, "t": 3, "A": 4.27, "G": 3.35, "I": 11.6},
    "CHS48.3x4": {"d": 48.3, "t": 4, "A": 5.57, "G": 4.37, "I": 14.4},
    "CHS60.3x3": {"d": 60.3, "t": 3, "A": 5.40, "G": 4.24, "I": 23.5},
    "CHS60.3x4": {"d": 60.3, "t": 4, "A": 7.07, "G": 5.55, "I": 29.6},
    "CHS60.3x5": {"d": 60.3, "t": 5, "A": 8.69, "G": 6.82, "I": 34.9},
    "CHS76.1x3": {"d": 76.1, "t": 3, "A": 6.89, "G": 5.41, "I": 48.8},
    "CHS76.1x4": {"d": 76.1, "t": 4, "A": 9.06, "G": 7.11, "I": 62.1},
    "CHS76.1x5": {"d": 76.1, "t": 5, "A": 11.2, "G": 8.77, "I": 74.1},
    "CHS88.9x4": {"d": 88.9, "t": 4, "A": 10.7, "G": 8.38, "I": 100},
    "CHS88.9x5": {"d": 88.9, "t": 5, "A": 13.2, "G": 10.3, "I": 120},
    "CHS88.9x6.3": {"d": 88.9, "t": 6.3, "A": 16.3, "G": 12.8, "I": 144},
    "CHS114.3x4": {"d": 114.3, "t": 4, "A": 13.9, "G": 10.9, "I": 220},
    "CHS114.3x5": {"d": 114.3, "t": 5, "A": 17.2, "G": 13.5, "I": 266},
    "CHS114.3x6.3": {"d": 114.3, "t": 6.3, "A": 21.4, "G": 16.8, "I": 322},
    "CHS139.7x5": {"d": 139.7, "t": 5, "A": 21.2, "G": 16.6, "I": 493},
    "CHS139.7x6.3": {"d": 139.7, "t": 6.3, "A": 26.4, "G": 20.7, "I": 600},
    "CHS139.7x8": {"d": 139.7, "t": 8, "A": 33.1, "G": 26.0, "I": 726},
    "CHS168.3x5": {"d": 168.3, "t": 5, "A": 25.7, "G": 20.1, "I": 871},
    "CHS168.3x6.3": {"d": 168.3, "t": 6.3, "A": 32.1, "G": 25.2, "I": 1070},
    "CHS168.3x8": {"d": 168.3, "t": 8, "A": 40.3, "G": 31.6, "I": 1300},
    "CHS168.3x10": {"d": 168.3, "t": 10, "A": 49.7, "G": 39.0, "I": 1560},
    "CHS219.1x6.3": {"d": 219.1, "t": 6.3, "A": 42.1, "G": 33.1, "I": 2410},
    "CHS219.1x8": {"d": 219.1, "t": 8, "A": 53.1, "G": 41.6, "I": 2970},
    "CHS219.1x10": {"d": 219.1, "t": 10, "A": 65.7, "G": 51.6, "I": 3600},
    "CHS273x6.3": {"d": 273, "t": 6.3, "A": 52.8, "G": 41.4, "I": 4770},
    "CHS273x8": {"d": 273, "t": 8, "A": 66.6, "G": 52.3, "I": 5940},
    "CHS273x10": {"d": 273, "t": 10, "A": 82.6, "G": 64.8, "I": 7240},
    "CHS323.9x8": {"d": 323.9, "t": 8, "A": 79.4, "G": 62.3, "I": 10000},
    "CHS323.9x10": {"d": 323.9, "t": 10, "A": 98.6, "G": 77.4, "I": 12200},
    "CHS323.9x12.5": {"d": 323.9, "t": 12.5, "A": 122, "G": 96.0, "I": 14900},
    "CHS355.6x8": {"d": 355.6, "t": 8, "A": 87.4, "G": 68.6, "I": 13300},
    "CHS355.6x10": {"d": 355.6, "t": 10, "A": 109, "G": 85.2, "I": 16300},
    "CHS355.6x12.5": {"d": 355.6, "t": 12.5, "A": 135, "G": 106, "I": 19800},
    "CHS406.4x10": {"d": 406.4, "t": 10, "A": 125, "G": 97.8, "I": 24600},
    "CHS406.4x12.5": {"d": 406.4, "t": 12.5, "A": 155, "G": 121, "I": 30100},
    "CHS406.4x16": {"d": 406.4, "t": 16, "A": 196, "G": 154, "I": 37300},
}


# =============================================================================
# HULPFUNCTIES
# =============================================================================

def get_profiel(naam: str) -> dict | None:
    """
    Zoekt een profiel op basis van naam.

    Args:
        naam: Profielnaam (bijv. 'HEA200', 'IPE300', 'SHS100x5')

    Returns:
        Dictionary met profieleigenschappen of None
    """
    naam = naam.upper().replace(" ", "").replace("X", "x")

    # Zoek in alle profielcollecties
    for serie_naam, serie_data in [
        ("HEA", HEA_PROFIELEN),
        ("HEB", HEB_PROFIELEN),
        ("IPE", IPE_PROFIELEN),
        ("UNP", UNP_PROFIELEN),
        ("SHS", SHS_PROFIELEN),
        ("CHS", CHS_PROFIELEN),
    ]:
        if naam in serie_data:
            return {"serie": serie_naam, "naam": naam, **serie_data[naam]}

    return None


def get_beschikbare_series() -> list:
    """Geeft lijst van beschikbare profielseries."""
    return ["HEA", "HEB", "IPE", "UNP", "SHS", "CHS"]


def get_profielen_in_serie(serie: str) -> list:
    """
    Geeft alle profielen in een serie.

    Args:
        serie: Serienaam (bijv. 'HEA', 'IPE')

    Returns:
        Lijst van profielnamen
    """
    serie = serie.upper()

    serie_map = {
        "HEA": HEA_PROFIELEN,
        "HEB": HEB_PROFIELEN,
        "IPE": IPE_PROFIELEN,
        "UNP": UNP_PROFIELEN,
        "SHS": SHS_PROFIELEN,
        "CHS": CHS_PROFIELEN,
    }

    if serie in serie_map:
        return list(serie_map[serie].keys())
    return []


def is_nl_gangbaar(serie: str) -> bool:
    """
    Controleert of een profielserie gangbaar is in Nederland.

    Args:
        serie: Serienaam

    Returns:
        True als gangbaar in NL
    """
    nl_series = set()
    for cat in NL_GANGBARE_PROFIELEN.values():
        nl_series.update(cat["series"])

    return serie.upper() in nl_series


# Eenheden voor documentatie
EENHEDEN = {
    "h": "mm",
    "b": "mm",
    "tw": "mm",
    "tf": "mm",
    "t": "mm",
    "d": "mm",
    "r": "mm",
    "A": "cm²",
    "G": "kg/m",
    "Iy": "cm⁴",
    "Iz": "cm⁴",
    "I": "cm⁴",
    "ey": "mm",
}

BESCHRIJVINGEN = {
    "h": "Profielhoogte",
    "b": "Flensbreedte",
    "tw": "Lijfdikte (webdikte)",
    "tf": "Flensdikte",
    "t": "Wanddikte",
    "d": "Buitendiameter",
    "r": "Afrondingsstraal",
    "A": "Doorsnede-oppervlak",
    "G": "Gewicht per strekkende meter",
    "Iy": "Traagheidsmoment om sterke as",
    "Iz": "Traagheidsmoment om zwakke as",
    "I": "Traagheidsmoment",
    "ey": "Zwaartepuntafstand",
}
