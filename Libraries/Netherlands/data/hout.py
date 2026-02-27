# -*- coding: utf-8 -*-
"""
Hout Sterkteklassen volgens Eurocode 5
======================================
NEN-EN 338 (gezaagd hout) en NEN-EN 14080 (gelamineerd hout)
Alle sterktes in N/mm², E-moduli in N/mm², volumieke massa in kN/m³
"""

# =============================================================================
# NAALDHOUT EN POPULIEREN (NEN-EN 338)
# Sterkteklassen C14 t/m C35
# =============================================================================

NAALDHOUT = {
    "C14": {
        "fm_k": 14,        # buigsterkte [N/mm²]
        "rho_k": 2.9,      # volumieke massa [kN/m³]
        "ft_0_k": 8,       # treksterkte evenwijdig [N/mm²]
        "ft_90_k": 0.4,    # treksterkte loodrecht [N/mm²]
        "fc_0_k": 16,      # druksterkte evenwijdig [N/mm²]
        "fc_90_k": 2.0,    # druksterkte loodrecht [N/mm²]
        "fv_k": 3.0,       # schuifsterkte [N/mm²]
        "E_0_u_k": 4700,   # E-modulus UGT [N/mm²]
        "E_0_mean": 7000,  # E-modulus BGT gemiddeld [N/mm²]
        "E_90_mean": 230,  # E-modulus loodrecht gemiddeld [N/mm²]
        "G_mean": 440,     # afschuivingsmodulus [N/mm²]
    },
    "C16": {
        "fm_k": 16,
        "rho_k": 3.1,
        "ft_0_k": 10,
        "ft_90_k": 0.5,
        "fc_0_k": 17,
        "fc_90_k": 2.2,
        "fv_k": 3.2,
        "E_0_u_k": 5400,
        "E_0_mean": 8000,
        "E_90_mean": 270,
        "G_mean": 500,
    },
    "C18": {
        "fm_k": 18,
        "rho_k": 3.0,
        "ft_0_k": 11,
        "ft_90_k": 0.5,
        "fc_0_k": 18,
        "fc_90_k": 2.2,
        "fv_k": 3.4,
        "E_0_u_k": 6000,
        "E_0_mean": 9000,
        "E_90_mean": 300,
        "G_mean": 560,
    },
    "C20": {
        "fm_k": 20,
        "rho_k": 3.3,
        "ft_0_k": 12,
        "ft_90_k": 0.5,
        "fc_0_k": 19,
        "fc_90_k": 2.3,
        "fv_k": 3.6,
        "E_0_u_k": 6400,
        "E_0_mean": 9500,
        "E_90_mean": 320,
        "G_mean": 590,
    },
    "C22": {
        "fm_k": 22,
        "rho_k": 3.4,
        "ft_0_k": 13,
        "ft_90_k": 0.5,
        "fc_0_k": 20,
        "fc_90_k": 2.4,
        "fv_k": 3.8,
        "E_0_u_k": 6700,
        "E_0_mean": 10000,
        "E_90_mean": 330,
        "G_mean": 630,
    },
    "C24": {
        "fm_k": 24,
        "rho_k": 3.5,
        "ft_0_k": 14,
        "ft_90_k": 0.5,
        "fc_0_k": 21,
        "fc_90_k": 2.5,
        "fv_k": 4.0,
        "E_0_u_k": 7400,
        "E_0_mean": 11000,
        "E_90_mean": 370,
        "G_mean": 690,
    },
    "C27": {
        "fm_k": 27,
        "rho_k": 3.7,
        "ft_0_k": 16,
        "ft_90_k": 0.6,
        "fc_0_k": 22,
        "fc_90_k": 2.6,
        "fv_k": 4.0,
        "E_0_u_k": 7700,
        "E_0_mean": 11500,
        "E_90_mean": 380,
        "G_mean": 720,
    },
    "C30": {
        "fm_k": 30,
        "rho_k": 3.8,
        "ft_0_k": 18,
        "ft_90_k": 0.6,
        "fc_0_k": 23,
        "fc_90_k": 2.7,
        "fv_k": 4.0,
        "E_0_u_k": 8000,
        "E_0_mean": 12000,
        "E_90_mean": 400,
        "G_mean": 750,
    },
    "C35": {
        "fm_k": 35,
        "rho_k": 4.0,
        "ft_0_k": 21,
        "ft_90_k": 0.6,
        "fc_0_k": 25,
        "fc_90_k": 2.8,
        "fv_k": 4.0,
        "E_0_u_k": 8700,
        "E_0_mean": 13000,
        "E_90_mean": 430,
        "G_mean": 810,
    },
}


# =============================================================================
# LOOFHOUT (NEN-EN 338)
# Sterkteklassen D30 t/m D70
# =============================================================================

LOOFHOUT = {
    "D30": {
        "fm_k": 30,        # buigsterkte [N/mm²]
        "rho_k": 5.3,      # volumieke massa [kN/m³]
        "ft_0_k": 18,      # treksterkte evenwijdig [N/mm²]
        "ft_90_k": 0.6,    # treksterkte loodrecht [N/mm²]
        "fc_0_k": 23,      # druksterkte evenwijdig [N/mm²]
        "fc_90_k": 4.00,   # druksterkte loodrecht [N/mm²]
        "fv_k": 3.0,       # schuifsterkte [N/mm²]
        "E_0_u_k": 8000,   # E-modulus UGT [N/mm²]
        "E_0_mean": 10000, # E-modulus BGT gemiddeld [N/mm²]
        "E_90_mean": 640,  # E-modulus loodrecht gemiddeld [N/mm²]
        "G_mean": 600,     # afschuivingsmodulus [N/mm²]
    },
    "D35": {
        "fm_k": 35,
        "rho_k": 5.6,
        "ft_0_k": 21,
        "ft_90_k": 0.6,
        "fc_0_k": 25,
        "fc_90_k": 4.20,
        "fv_k": 3.4,
        "E_0_u_k": 8700,
        "E_0_mean": 10000,
        "E_90_mean": 690,
        "G_mean": 650,
    },
    "D40": {
        "fm_k": 40,
        "rho_k": 5.9,
        "ft_0_k": 24,
        "ft_90_k": 0.6,
        "fc_0_k": 26,
        "fc_90_k": 8.80,
        "fv_k": 3.8,
        "E_0_u_k": 9400,
        "E_0_mean": 11000,
        "E_90_mean": 750,
        "G_mean": 700,
    },
    "D50": {
        "fm_k": 50,
        "rho_k": 6.5,
        "ft_0_k": 30,
        "ft_90_k": 0.6,
        "fc_0_k": 29,
        "fc_90_k": 4.85,
        "fv_k": 4.6,
        "E_0_u_k": 11800,
        "E_0_mean": 14000,
        "E_90_mean": 930,
        "G_mean": 880,
    },
    "D60": {
        "fm_k": 60,
        "rho_k": 7.0,
        "ft_0_k": 36,
        "ft_90_k": 0.6,
        "fc_0_k": 32,
        "fc_90_k": 10.50,
        "fv_k": 5.3,
        "E_0_u_k": 14300,
        "E_0_mean": 17000,
        "E_90_mean": 1130,
        "G_mean": 1060,
    },
    "D70": {
        "fm_k": 70,
        "rho_k": 9.0,
        "ft_0_k": 42,
        "ft_90_k": 0.6,
        "fc_0_k": 34,
        "fc_90_k": 13.50,
        "fv_k": 6.0,
        "E_0_u_k": 16800,
        "E_0_mean": 20000,
        "E_90_mean": 1330,
        "G_mean": 1250,
    },
}


# =============================================================================
# GELAMINEERD HOUT (NEN-EN 14080)
# Sterkteklassen GL24h t/m GL36h (homogeen)
# =============================================================================

GELAMINEERD_HOUT = {
    "GL24h": {
        "fm_k": 24,           # buigsterkte [N/mm²]
        "rho_k": 3.80,        # volumieke massa [kN/m³]
        "ft_0_k": 17,         # treksterkte evenwijdig [N/mm²]
        "ft_90_k": 0.4,       # treksterkte loodrecht [N/mm²]
        "fc_0_k": 24.0,       # druksterkte evenwijdig [N/mm²]
        "fc_90_k": 2.7,       # druksterkte loodrecht [N/mm²]
        "fv_k": 2.7,          # schuifsterkte [N/mm²]
        "E_0_u_k": 9400,      # E-modulus UGT [N/mm²]
        "E_0_mean": 11600,    # E-modulus BGT gemiddeld [N/mm²]
        "E_90_mean": 390,     # E-modulus loodrecht gemiddeld [N/mm²]
        "G_mean": 720,        # afschuivingsmodulus [N/mm²]
    },
    "GL28h": {
        "fm_k": 28,
        "rho_k": 4.10,
        "ft_0_k": 20,
        "ft_90_k": 0.5,
        "fc_0_k": 26.5,
        "fc_90_k": 3.0,
        "fv_k": 3.2,
        "E_0_u_k": 10200,
        "E_0_mean": 12600,
        "E_90_mean": 420,
        "G_mean": 780,
    },
    "GL32h": {
        "fm_k": 32,
        "rho_k": 4.30,
        "ft_0_k": 23,
        "ft_90_k": 0.5,
        "fc_0_k": 29.0,
        "fc_90_k": 3.3,
        "fv_k": 3.8,
        "E_0_u_k": 11100,
        "E_0_mean": 13700,
        "E_90_mean": 460,
        "G_mean": 850,
    },
    "GL36h": {
        "fm_k": 36,
        "rho_k": 4.50,
        "ft_0_k": 26,
        "ft_90_k": 0.6,
        "fc_0_k": 31.0,
        "fc_90_k": 3.6,
        "fv_k": 4.3,
        "E_0_u_k": 11900,
        "E_0_mean": 14700,
        "E_90_mean": 490,
        "G_mean": 910,
    },
}


# =============================================================================
# HULPFUNCTIES
# =============================================================================

def get_hout_eigenschappen(klasse: str) -> dict | None:
    """
    Geeft de eigenschappen voor een houtsterkteklasse.

    Args:
        klasse: Sterkteklasse (bijv. 'C24', 'D40', 'GL28h')

    Returns:
        Dictionary met alle eigenschappen of None indien niet gevonden
    """
    klasse = klasse.upper()

    if klasse in NAALDHOUT:
        return {"type": "naaldhout", "klasse": klasse, **NAALDHOUT[klasse]}
    elif klasse in LOOFHOUT:
        return {"type": "loofhout", "klasse": klasse, **LOOFHOUT[klasse]}
    elif klasse in GELAMINEERD_HOUT:
        return {"type": "gelamineerd", "klasse": klasse, **GELAMINEERD_HOUT[klasse]}
    else:
        return None


def get_beschikbare_klassen(hout_type: str = None) -> list:
    """
    Geeft een lijst van beschikbare sterkteklassen.

    Args:
        hout_type: 'naaldhout', 'loofhout', 'gelamineerd' of None voor alles

    Returns:
        Lijst van sterkteklassen
    """
    if hout_type == "naaldhout":
        return list(NAALDHOUT.keys())
    elif hout_type == "loofhout":
        return list(LOOFHOUT.keys())
    elif hout_type == "gelamineerd":
        return list(GELAMINEERD_HOUT.keys())
    else:
        return (
            list(NAALDHOUT.keys()) +
            list(LOOFHOUT.keys()) +
            list(GELAMINEERD_HOUT.keys())
        )


# Symbool beschrijvingen voor documentatie
SYMBOLEN = {
    "fm_k": "Karakteristieke buigsterkte",
    "rho_k": "Karakteristieke volumieke massa",
    "ft_0_k": "Karakteristieke treksterkte evenwijdig aan de vezel",
    "ft_90_k": "Karakteristieke treksterkte loodrecht op de vezel",
    "fc_0_k": "Karakteristieke druksterkte evenwijdig aan de vezel",
    "fc_90_k": "Karakteristieke druksterkte loodrecht op de vezel",
    "fv_k": "Karakteristieke schuifsterkte",
    "E_0_u_k": "Karakteristieke E-modulus (UGT)",
    "E_0_mean": "Gemiddelde E-modulus evenwijdig (BGT)",
    "E_90_mean": "Gemiddelde E-modulus loodrecht",
    "G_mean": "Gemiddelde afschuivingsmodulus",
}

EENHEDEN = {
    "fm_k": "N/mm²",
    "rho_k": "kN/m³",
    "ft_0_k": "N/mm²",
    "ft_90_k": "N/mm²",
    "fc_0_k": "N/mm²",
    "fc_90_k": "N/mm²",
    "fv_k": "N/mm²",
    "E_0_u_k": "N/mm²",
    "E_0_mean": "N/mm²",
    "E_90_mean": "N/mm²",
    "G_mean": "N/mm²",
}
