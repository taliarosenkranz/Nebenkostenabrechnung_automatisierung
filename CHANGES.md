# ÄNDERUNGEN - Optionale PDFs & Neue Berechnung

## 1. Berechnung korrigiert ✅

### Vorher (FALSCH)
```python
# Tagesbasierte Berechnung
tenant_days = (period_end - period_start).days + 1
pro_rata_factor = tenant_days / 365
tenant_share = annual_amount * pro_rata_factor
```

### Nachher (KORREKT)
```python
# Monatsbasierte Berechnung
monthly_amount = annual_amount / 12
tenant_share = monthly_amount * payment_months
```

### Formel
```
(Summe umlagefähige Kosten / 12) * Anzahl Monate
```

**Beispiel:**
- Jahreskosten: 2198.47 €
- Pro Monat: 2198.47 € / 12 = 183.21 €
- Für 6 Monate: 183.21 € * 6 = 1099.24 €

---

## 2. Optionale PDF-Uploads ✅

### Streamlit App (`app.py`)

#### Vorher
- **Alle 3 PDFs waren Pflicht:**
  - WEG-Abrechnung
  - Mietvertrag
  - Kontoauszug

#### Nachher
- **Nur WEG-Abrechnung ist Pflicht**
- **Mietvertrag & Kontoauszug sind optional**
- **Manuelle Eingabe möglich:**
  - Mieter-Name
  - Monatliche Vorauszahlung
  - Anzahl Monate

#### UI-Änderungen
```python
# WEG-Abrechnung
st.subheader("WEG-Abrechnung ⚠️ PFLICHT")
st.warning("⚠️ Erforderlich")

# Mietvertrag (Optional)
st.subheader("Mietvertrag (Optional)")
st.info("Optional - kann manuell eingegeben werden")

# Kontoauszug (Optional)
st.subheader("Kontoauszüge (Optional)")
st.info("Optional - kann manuell eingegeben werden")
```

#### Eingabefelder
```python
# Mieter-Name - immer editierbar
tenant_name = st.text_input(
    "Name des Mieters *",
    value=extracted_name_or_empty,
    placeholder="Vorname Nachname"
)

# Vorauszahlung - immer editierbar
monthly_prepayment = st.number_input(
    "Monatliche Nebenkostenvorauszahlung (€) *",
    min_value=0.0,
    value=extracted_or_0,
    step=10.0
)

# Anzahl Monate - immer editierbar
payment_months = st.number_input(
    "Anzahl Monate mit Mietzahlung *",
    min_value=1,
    max_value=12,
    value=extracted_or_12,
    step=1
)
```

---

## 3. CLI (`main.py`)

### Änderungen
- **Schritt 1:** WEG-Abrechnung (PFLICHT)
- **Schritt 2:** Mietvertrag (Optional - kann übersprungen werden)
- **Schritt 3:** Kontoauszug (Optional - kann übersprungen werden)
- **Schritt 4:** Manuelle Eingaben mit Defaultwerten
  - Mieter-Name
  - Vorauszahlung
  - Anzahl Monate

### Beispiel-Ablauf
```bash
STEP 1: WEG-Abrechnung (PFLICHT)
WEG-Abrechnung PDF (Pfad): data/input/Jahresabrechnung_BeB_2023.pdf
✅ 25 Kostenposten gefunden

STEP 2: Mietvertrag (Optional)
Mietvertrag PDF (Pfad, Enter = überspringen): [ENTER]

STEP 3: Kontoauszug (Optional)
Kontoauszug PDF (Pfad, Enter = überspringen): [ENTER]

EINGABEN ÜBERPRÜFEN/ERGÄNZEN
Mieter-Name [Eingabe erforderlich]: Emanuela Mingo
Anzahl Monate die Miete gezahlt wurde [12]: 12
Monatliche Nebenkostenvorauszahlung in € [Eingabe erforderlich]: 200

🔢 Berechne Kosten...
   Formel: (Jahreskosten 2198.47 € / 12) * 12 Monate
```

---

## 4. cost_calculator.py - Neue Signatur

### Vorher
```python
def calculate_tenant_costs(
    weg_costs: List[Dict[str, Any]],
    period_start: date,  # Required
    period_end: date,    # Required
    payment_months: int,
    monthly_prepayment: float
)
```

### Nachher
```python
def calculate_tenant_costs(
    weg_costs: List[Dict[str, Any]],
    payment_months: int,            # Now first!
    monthly_prepayment: float,      # Now second!
    period_start: date = None,      # Optional
    period_end: date = None         # Optional
)
```

### Return-Werte erweitert
```python
{
    'items': [...],
    'total_annual': 2198.47,      # NEU
    'total_monthly': 183.21,      # NEU
    'total_costs': 2198.47,
    'prepayments': 2400.00,
    'balance': -201.53,
    'payment_months': 12,
    'period_start': date(2023, 1, 1),  # Optional
    'period_end': date(2023, 12, 31)   # Optional
}
```

---

## 5. Gelöschte Funktionen

- ❌ `filter_umlagefaehige_kosten()` - nicht mehr nötig
- ❌ `calculate_mea_share()` - wird in Extraktion angewendet
- ❌ `period_days` und `pro_rata_factor` aus Berechnung

---

## 6. Config-Patterns erweitert

### Neue Patterns für Mietvertrag
```python
RENTAL_CONTRACT_PATTERNS = {
    'nebenkosten_voraus': [
        r'Betriebskostenvorauszahlung[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Nebenkosten[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Betriebskosten[:\s]+(?:EUR\s*)?([\d.,]+)',
    ],
    'heizkosten_voraus': [
        r'Heizung[:\s]+(?:EUR\s*)?([\d.,]+)',
        r'Heizkosten[:\s]+(?:EUR\s*)?([\d.,]+)',
    ]
}
```

### Neue Patterns für Kontoauszug
```python
BANK_STATEMENT_PATTERNS = {
    'mietzahlung': [
        'miete', 'rent', 'lietzenburger', 'rosenkranz',
        'mingo', 'Vinayak', 'Gopi'  # NEU
    ]
}
```

---

## Tests

### Test der neuen Berechnung
```bash
python3 test_new_calculation.py
```

### Ergebnisse
```
TEST 1: GANZES JAHR (12 Monate)
  Jahreskosten:     2198.47 €
  / 12 Monate =      183.21 €/Monat
  * 12 Monate =     2198.47 €
  ✅ KORREKT!

TEST 2: HALBES JAHR (6 Monate)
  * 6 Monate =      1099.24 €
  ✅ KORREKT!

TEST 3: QUARTAL (3 Monate)
  * 3 Monate =       549.62 €
  ✅ KORREKT!
```

---

## Zusammenfassung

✅ **Berechnung korrigiert:** Monatsbasiert statt tagesbasiert  
✅ **Optionale PDFs:** Nur WEG-Abrechnung Pflicht  
✅ **Manuelle Eingabe:** Alle Werte können manuell eingegeben werden  
✅ **Bessere UX:** Klarere Labels und Hilfe-Texte  
✅ **Flexibler:** Funktioniert auch ohne Mietvertrag & Kontoauszug  

