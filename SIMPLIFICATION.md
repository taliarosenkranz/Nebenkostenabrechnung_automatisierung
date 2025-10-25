# VEREINFACHUNG DER KOSTENBERECHNUNG

## Problem
Die bisherige Implementierung war überkompliziert:
- Unnötige `umlagefaehig` Flags in den extrahierten Daten
- Unnötige `category` Felder
- Komplexe Kategorieprüfungen im cost_calculator
- Unterscheidung zwischen "direkt zugeordnet" und "MEA-basiert"

## Lösung
Die WEG-Extraktion liefert **bereits die korrekten, fertigen Werte**:
- Alle extrahierten Kosten sind bereits umlagefähig
- Die Beträge sind bereits der Eigentümer-Anteil (MEA wurde schon angewendet)
- Keine weitere Kategorisierung notwendig

## Änderungen

### 1. `src/pdf_extractor.py`
**Vorher:**
```python
{
    'name': 'Hausnebenkosten',
    'amount': 258.61,
    'category': 'Sonstige',
    'umlagefaehig': True
}
```

**Nachher:**
```python
{
    'name': 'Hausnebenkosten',
    'amount': 258.61
}
```

### 2. `src/cost_calculator.py`
**Vorher:**
- Prüfung auf `umlagefaehig` Flag
- Unterscheidung zwischen direkt zugeordneten Kosten und MEA-basierten Kosten
- Komplexe Kategorieprüfungen

**Nachher:**
```python
def calculate_tenant_costs(...):
    """
    SIMPLIFIED: WEG extraction already provides only umlagefähige costs
    with correct amounts. Just apply pro-rata for partial year.
    """
    for cost in weg_costs:
        cost_name = cost['name']
        annual_amount = cost['amount']
        
        # Simply apply pro-rata to get tenant's share
        tenant_share = annual_amount * pro_rata_factor
```

### 3. `config.py`
**Entfernt:**
- `COST_CATEGORIES` Dictionary (nicht mehr benötigt)
- Keine Unterscheidung zwischen umlagefähig/nicht-umlagefähig
- Keine "direkt_zugeordnet" Liste

## Ergebnis

### Datenfluss (vereinfacht)

```
PDF-Extraktion
    ↓
25 Kostenposten mit Namen + Betrag
    ↓
Pro-Rata Berechnung (Zeitanteil)
    ↓
Fertige Abrechnung
```

### Vorteile
1. **Einfacher Code**: Weniger Logik, weniger Fehlerquellen
2. **Klarer Datenfluss**: Ein Schritt = eine Verantwortung
3. **Wartbarer**: Keine komplexen Kategorisierungsregeln
4. **Schneller**: Weniger Prüfungen und Berechnungen

### Test-Ergebnisse
```
✓ 25 Kostenposten extrahiert
✓ Gesamtsumme: 2198.47 €
✓ Pro-Rata funktioniert korrekt
✓ Excel-Export funktioniert
```

## Funktionen entfernt
- `filter_umlagefaehige_kosten()` - nicht mehr nötig
- `calculate_mea_share()` - wird bereits in der Extraktion angewendet

## Nächste Schritte
Die Berechnung ist jetzt korrekt und einfach. Alle Tests laufen erfolgreich.
