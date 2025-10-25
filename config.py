"""
═══════════════════════════════════════════════════════════════
NEBENKOSTENABRECHNUNG - KONFIGURATION
═══════════════════════════════════════════════════════════════
"""

# ════════════════════════════════════════════════════════
#  IMMOBILIEN-DATEN
# ════════════════════════════════════════════════════════
PROPERTY = {
    'address': 'Lietzenburger Str 3, 10789 Berlin',
    'einheit': '01080/05',
    'bezeichnung': 'Wohnung, 1. OG, links',
    'untergruppe': 'UG2',  # Lietzenburger Str. 3-9
}

# ════════════════════════════════════════════════════════
#  MITEIGENTUMSANTEIL (MEA)
# ════════════════════════════════════════════════════════
MEA = {
    'anteile': 57,           # Deine MEA-Anteile
    'basis_gesamt': 10000,   # Gesamtobjekt
    'basis_ug2': 4504,       # Untergruppe 2
    'ratio_gesamt': 57 / 10000,   # 0,57%
    'ratio_ug2': 57 / 4504,        # 1,265%
}

# ════════════════════════════════════════════════════════
#  EIGENTÜMER-DATEN
# ════════════════════════════════════════════════════════
LANDLORD = {
    'name': 'Talia Rosenkranz',
    'address': 'Arysallee 10\n14055 Berlin',
    'email': '',  # Optional
}

# ════════════════════════════════════════════════════════
#  PDF-EXTRAKTION PATTERNS
# ════════════════════════════════════════════════════════

# Regex-Patterns für Mietvertrag-Extraktion
RENTAL_CONTRACT_PATTERNS = {
    'mieter_name': [
        r'Mieter[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)',
        r'Mieterin[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)',
        r'Name[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)',
    ],
    'mietbeginn': [
        r'Mietbeginn[:\s]+(\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4})',
        r'ab dem[:\s]+(\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4})',
        r'Beginn[:\s]+(\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4})',
    ],
    'kaltmiete': [
        r'Grundmiete[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Kaltmiete[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Nettomiete[:\s]+(?:EUR\s*)?([\d.,]+)',
    ],
    'nebenkosten_voraus': [
        r'Betriebskostenvorauszahlung[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Nebenkosten[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Betriebskosten[:\s]+(?:EUR\s*)?([\d.,]+)',
    ],
    'heizkosten_voraus': [
        r'Heizung[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Heizkosten[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Heizkostenvorauszahlung[:\s]+(?:EUR\s*)?([\d.,]+)',
    ]
}

# Regex-Patterns für Kontoauszug-Extraktion
BANK_STATEMENT_PATTERNS = {
    'mietzahlung': [
        'miete',
        'rent',
        'lietzenburger',
        'rosenkranz',
        'mingo',
        'Vinayak',
        'Gopi',
    ],
    'betrag': [
        r'([\d.,]+)\s*€',
        r'€\s*([\d.,]+)',
    ],
    'datum': [
        r'(\d{2}\.\d{2}\.\d{4})',  # DD.MM.YYYY
    ]
}
