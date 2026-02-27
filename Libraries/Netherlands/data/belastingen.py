# -*- coding: utf-8 -*-
"""
Nederlandse Belastingen volgens Eurocode
========================================
Voorgeschreven belastingen voor gebouwen en constructies.
Gebaseerd op NEN-EN 1991 en Nationale Bijlage.
"""

# =============================================================================
# VERANDERLIJKE BELASTINGEN IN GEBOUWEN (NEN-EN 1991-1-1)
# =============================================================================

# Combinatiefactoren en karakteristieke waarden per gebruikscategorie
# ψ0 = combinatiewaarde
# ψ1 = frequente waarde
# ψ2 = quasi-blijvende waarde
# q = gelijkmatig verdeelde belasting [kN/m²]
# F = geconcentreerde belasting [kN]

GEBRUIKSCATEGORIEEN = {
    "A": {
        "naam": "Woon- en verblijfsruimtes",
        "psi_0": 0.40,
        "psi_1": 0.50,
        "psi_2": 0.30,
        "q": 1.75,  # kN/m²
        "F": 3.00,  # kN
    },
    "B": {
        "naam": "Kantoorruimtes",
        "psi_0": 0.50,
        "psi_1": 0.50,
        "psi_2": 0.30,
        "q": 2.50,  # kN/m²
        "F": 3.00,  # kN
    },
    "C": {
        "naam": "Bijeenkomstruimtes",
        "psi_0": 0.60,  # of 0.40 afhankelijk van subcategorie
        "psi_0_alt": 0.40,
        "psi_1": 0.70,
        "psi_2": 0.60,
        "q": 5.00,  # kN/m²
        "F": 7.00,  # kN
        "opmerking": "ψ0 = 0,6 of 0,4 afhankelijk van subcategorie",
    },
    "D": {
        "naam": "Winkelruimtes",
        "psi_0": 0.40,
        "psi_1": 0.70,
        "psi_2": 0.60,
        "q": 4.00,  # kN/m²
        "F": 7.00,  # kN
    },
    "E": {
        "naam": "Opslagruimtes",
        "psi_0": 1.00,
        "psi_1": 0.90,
        "psi_2": 0.80,
        "q": 10.00,  # kN/m² (minimum, afhankelijk van opslag)
        "F": 40.00,  # kN
    },
    "F": {
        "naam": "Verkeersruimte, voertuiggewicht ≤ 30 kN",
        "psi_0": 0.70,
        "psi_1": 0.70,
        "psi_2": 0.60,
        "q": None,  # Afhankelijk van voertuig
        "F": None,
    },
    "G": {
        "naam": "Verkeersruimte, 30 kN < voertuiggewicht ≤ 160 kN",
        "psi_0": 0.70,
        "psi_1": 0.50,
        "psi_2": 0.30,
        "q": None,  # Afhankelijk van voertuig
        "F": None,
    },
    "H": {
        "naam": "Daken",
        "psi_0": 0.00,
        "psi_1": 0.00,
        "psi_2": 0.00,
        "q": None,  # Afhankelijk van daktype
        "F": None,
    },
}

# Klimatologische en overige belastingen
KLIMAAT_BELASTINGEN = {
    "sneeuw": {
        "naam": "Sneeuwbelasting",
        "psi_0": 0.00,
        "psi_1": 0.20,
        "psi_2": 0.00,
    },
    "regen": {
        "naam": "Belasting door regenwater",
        "psi_0": 0.00,
        "psi_1": 0.00,
        "psi_2": 0.00,
    },
    "wind": {
        "naam": "Windbelasting",
        "psi_0": 0.00,
        "psi_1": 0.20,
        "psi_2": 0.00,
    },
    "temperatuur": {
        "naam": "Temperatuurbelasting (geen brand)",
        "psi_0": 0.00,
        "psi_1": 0.50,
        "psi_2": 0.00,
    },
}


# =============================================================================
# WINDBELASTING (NEN-EN 1991-1-4 + NB)
# =============================================================================

# Basiswindsnelheden per windgebied [m/s]
WINDGEBIEDEN = {
    1: {"v_b0": 29.5, "beschrijving": "Kustgebied"},
    2: {"v_b0": 27.0, "beschrijving": "Midden Nederland"},
    3: {"v_b0": 24.5, "beschrijving": "Binnenland"},
}

# Terreinruwheid categorieën
TERREINRUWHEID = {
    "kust": "Zee of kustgebied blootgesteld aan open zee",
    "onbebouwd": "Open terrein met weinig obstakels",
    "bebouwd": "Bebouwd gebied, voorsteden, bossen",
}

# Hoogtes voor winddruk tabel [m]
WIND_HOOGTES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120, 130, 140,
                150, 160, 170, 180, 190, 200]

# Stuwdruk qp(z) in kN/m² per windgebied, terreinruwheid en hoogte
# Formaat: WINDDRUK[gebied][terrein][hoogte_index] = qp
WINDDRUK = {
    1: {
        "kust": [1.11, 1.22, 1.30, 1.37, 1.42, 1.47, 1.51, 1.55, 1.58, 1.71, 1.80, 1.88, 1.94, 2.00, 2.04, 2.09, 2.12, 2.16, 2.19, 2.22, 2.25, 2.27, 2.30, 2.32, 2.34, 2.36, 2.38, 2.42, 2.45, 2.48, 2.51, 2.54, 2.56, 2.59, 2.61, 2.63, 2.65],
        "onbebouwd": [0.71, 0.71, 0.71, 0.78, 0.84, 0.89, 0.94, 0.98, 1.02, 1.16, 1.27, 1.36, 1.43, 1.50, 1.55, 1.60, 1.65, 1.69, 1.73, 1.76, 1.80, 1.83, 1.86, 1.88, 1.91, 1.93, 1.96, 2.00, 2.04, 2.08, 2.12, 2.15, 2.18, 2.21, 2.24, 2.27, 2.29],
        "bebouwd": [0.69, 0.69, 0.69, 0.69, 0.69, 0.69, 0.73, 0.77, 0.81, 0.96, 1.07, 1.16, 1.23, 1.30, 1.35, 1.40, 1.45, 1.49, 1.53, 1.57, 1.60, 1.63, 1.66, 1.69, 1.72, 1.74, 1.77, 1.81, 1.85, 1.89, 1.93, 1.96, 2.00, 2.03, 2.06, 2.08, 2.11],
    },
    2: {
        "kust": [0.93, 1.02, 1.09, 1.14, 1.19, 1.23, 1.26, 1.29, 1.32, 1.43, 1.51, 1.57, 1.63, 1.67, 1.71, 1.75, 1.78, 1.81, 1.83, 1.86, 1.88, 1.90, 1.92, 1.94, 1.96, 1.98, 1.99, 2.03, 2.05, 2.08, 2.10, 2.13, 2.15, 2.17, 2.19, 2.20, 2.22],
        "onbebouwd": [0.60, 0.60, 0.60, 0.66, 0.71, 0.75, 0.79, 0.82, 0.85, 0.98, 1.07, 1.14, 1.20, 1.25, 1.30, 1.34, 1.38, 1.42, 1.45, 1.48, 1.50, 1.53, 1.55, 1.58, 1.60, 1.62, 1.64, 1.68, 1.71, 1.74, 1.77, 1.80, 1.83, 1.85, 1.88, 1.90, 1.92],
        "bebouwd": [0.58, 0.58, 0.58, 0.58, 0.58, 0.58, 0.62, 0.65, 0.68, 0.80, 0.90, 0.97, 1.03, 1.09, 1.13, 1.17, 1.21, 1.25, 1.28, 1.31, 1.34, 1.37, 1.39, 1.42, 1.44, 1.46, 1.48, 1.52, 1.55, 1.59, 1.62, 1.65, 1.67, 1.70, 1.72, 1.75, 1.77],
    },
    3: {
        "onbebouwd": [0.49, 0.49, 0.49, 0.54, 0.58, 0.62, 0.65, 0.68, 0.70, 0.80, 0.88, 0.94, 0.99, 1.03, 1.07, 1.11, 1.14, 1.17, 1.19, 1.22, 1.24, 1.26, 1.28, 1.30, 1.32, 1.33, 1.35, 1.38, 1.41, 1.44, 1.46, 1.48, 1.50, 1.52, 1.54, 1.56, 1.58],
        "bebouwd": [0.48, 0.48, 0.48, 0.48, 0.48, 0.48, 0.51, 0.53, 0.56, 0.66, 0.74, 0.80, 0.85, 0.89, 0.93, 0.97, 1.00, 1.03, 1.05, 1.08, 1.10, 1.13, 1.15, 1.17, 1.18, 1.20, 1.22, 1.25, 1.28, 1.31, 1.33, 1.35, 1.38, 1.40, 1.42, 1.44, 1.46],
    },
}


def get_winddruk(gebied: int, terrein: str, hoogte: float) -> float:
    """
    Bereken de stuwdruk qp(z) voor een gegeven windgebied, terreinruwheid en hoogte.

    Args:
        gebied: Windgebied (1, 2 of 3)
        terrein: Terreinruwheid ('kust', 'onbebouwd' of 'bebouwd')
        hoogte: Hoogte boven maaiveld in meters

    Returns:
        Stuwdruk qp in kN/m² (lineair geïnterpoleerd)
    """
    if gebied not in WINDDRUK:
        raise ValueError(f"Ongeldig windgebied: {gebied}. Kies 1, 2 of 3.")
    if terrein not in WINDDRUK[gebied]:
        raise ValueError(f"Ongeldige terreinruwheid: {terrein} voor gebied {gebied}")

    waarden = WINDDRUK[gebied][terrein]

    # Zoek interpolatie indices
    if hoogte <= WIND_HOOGTES[0]:
        return waarden[0]
    if hoogte >= WIND_HOOGTES[-1]:
        return waarden[-1]

    for i, h in enumerate(WIND_HOOGTES[:-1]):
        if h <= hoogte < WIND_HOOGTES[i + 1]:
            # Lineaire interpolatie
            h1, h2 = h, WIND_HOOGTES[i + 1]
            q1, q2 = waarden[i], waarden[i + 1]
            return q1 + (q2 - q1) * (hoogte - h1) / (h2 - h1)

    return waarden[-1]


def get_belasting_categorie(categorie: str) -> dict | None:
    """
    Geeft de belastinggegevens voor een gebruikscategorie.

    Args:
        categorie: Letter van de categorie (A t/m H)

    Returns:
        Dictionary met psi-factoren, q en F waarden
    """
    return GEBRUIKSCATEGORIEEN.get(categorie.upper())
