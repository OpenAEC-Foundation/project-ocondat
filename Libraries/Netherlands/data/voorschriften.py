# -*- coding: utf-8 -*-
"""
Nederlandse Bouwvoorschriften - Historisch Overzicht
====================================================
Tijdlijn van Nederlandse constructieve voorschriften en normen.
"""

# Betonvoorschriften Nederland
# Historisch overzicht van geldende normen per jaar
BETONVOORSCHRIFTEN = {
    1800: None,  # Geen voorschriften
    1912: "GBV 1912",
    1918: "GBV 1918",
    1930: "GBV 1930",
    1940: "GBV 1940",
    1950: "GBV 1950",
    1962: "GBV 1962",
    1974: "VB 1974",
    1984: "VB 1984",
    1990: "TGB 1990",
    2012: "Eurocodes",
}

# Als lijst met periodes
BETONVOORSCHRIFTEN_PERIODES = [
    {"start": 1800, "eind": 1911, "norm": None, "beschrijving": "Geen voorschriften"},
    {"start": 1912, "eind": 1917, "norm": "GBV 1912", "beschrijving": "Gewapend Beton Voorschriften 1912"},
    {"start": 1918, "eind": 1929, "norm": "GBV 1918", "beschrijving": "Gewapend Beton Voorschriften 1918"},
    {"start": 1930, "eind": 1939, "norm": "GBV 1930", "beschrijving": "Gewapend Beton Voorschriften 1930"},
    {"start": 1940, "eind": 1949, "norm": "GBV 1940", "beschrijving": "Gewapend Beton Voorschriften 1940"},
    {"start": 1950, "eind": 1961, "norm": "GBV 1950", "beschrijving": "Gewapend Beton Voorschriften 1950"},
    {"start": 1962, "eind": 1973, "norm": "GBV 1962", "beschrijving": "Gewapend Beton Voorschriften 1962"},
    {"start": 1974, "eind": 1983, "norm": "VB 1974", "beschrijving": "Voorschriften Beton 1974"},
    {"start": 1984, "eind": 1989, "norm": "VB 1984", "beschrijving": "Voorschriften Beton 1984"},
    {"start": 1990, "eind": 2011, "norm": "TGB 1990", "beschrijving": "Technische Grondslagen voor Bouwconstructies 1990"},
    {"start": 2012, "eind": None, "norm": "Eurocodes", "beschrijving": "Europese constructienormen (NEN-EN 1992 e.v.)"},
]


def get_voorschrift(jaar: int) -> str | None:
    """
    Geeft het geldende betonvoorschrift voor een gegeven jaar.

    Args:
        jaar: Het jaar waarvoor het voorschrift gezocht wordt

    Returns:
        De naam van het geldende voorschrift, of None indien niet bekend
    """
    for periode in BETONVOORSCHRIFTEN_PERIODES:
        if periode["start"] <= jaar:
            if periode["eind"] is None or jaar <= periode["eind"]:
                return periode["norm"]
    return None


def get_voorschrift_info(jaar: int) -> dict | None:
    """
    Geeft volledige informatie over het geldende voorschrift voor een gegeven jaar.

    Args:
        jaar: Het jaar waarvoor het voorschrift gezocht wordt

    Returns:
        Dictionary met norm, start, eind en beschrijving
    """
    for periode in BETONVOORSCHRIFTEN_PERIODES:
        if periode["start"] <= jaar:
            if periode["eind"] is None or jaar <= periode["eind"]:
                return periode
    return None
