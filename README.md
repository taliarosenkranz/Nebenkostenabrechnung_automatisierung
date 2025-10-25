# Nebenkostenabrechnung Automatisierung 🏠

Automatische Erstellung von Nebenkostenabrechnungen für Mieter basierend auf WEG-Hausgeldabrechnungen.

## 🎯 Features

- ✅ **PDF-Extraktion** aus WEG-Abrechnungen, Mietverträgen und Kontoauszügen
- ✅ **Automatische Kostenberechnung** mit MEA-Anteil und anteiliger Zeitraum-Berechnung
- ✅ **Excel-Generierung** mit professionellem Layout
- ✅ **PDF-Konvertierung** (via LibreOffice)
- ✅ **E-Mail-Text-Generierung** für Mieter-Kommunikation
- ✅ **Web-UI** (Streamlit) für einfache Bedienung

## 🚀 Installation

### 1. Repository klonen / Navigieren
```bash
cd Nebenkostenabrechnung_automatisierung
```

### 2. Virtual Environment erstellen
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. LibreOffice installieren (für PDF-Konvertierung)
```bash
# macOS
brew install --cask libreoffice

# Linux
sudo apt-get install libreoffice  # Ubuntu/Debian
```

## 📖 Verwendung

### Web-UI (Empfohlen)

```bash
streamlit run app.py
```

Browser öffnet sich automatisch auf `http://localhost:8501`

### Workflow:
1. **Dokumente hochladen:**
   - WEG-Abrechnung (PDF)
   - Mietvertrag (PDF)
   - Kontoauszüge (PDF)

2. **Daten extrahieren:**
   - Automatische Erkennung von Kostenposten, Mieter-Name, Mietbeginn, Zahlungen

3. **Überprüfen & Anpassen:**
   - Extrahierte Daten kontrollieren
   - Zeitraum anpassen (bei Mieterwechsel)

4. **Abrechnung generieren:**
   - Excel wird erstellt
   - PDF konvertiert
   - E-Mail-Text generiert

5. **Download:**
   - Alle Dateien herunterladen und an Mieter versenden

## ⚙️ Konfiguration

Passe `config.py` an deine Daten an:

```python
# Immobilie
PROPERTY = {
    'address': 'Deine Adresse',
    'einheit': '...',
    'untergruppe': 'UG2',
}

# Miteigentumsanteil
MEA = {
    'anteile': 57,
    'basis_ug2': 4504,
}

# Eigentümer
LANDLORD = {
    'name': 'Dein Name',
    'address': 'Deine Adresse',
}
```

## 📁 Projektstruktur

```
Nebenkostenabrechnung_automatisierung/
├── app.py                      # Streamlit Web-UI
├── config.py                   # Konfiguration
├── requirements.txt            # Dependencies
├── src/
│   ├── pdf_extractor.py       # PDF-Verarbeitung
│   ├── cost_calculator.py     # Kostenberechnung
│   ├── excel_generator.py     # Excel-Erstellung
│   ├── pdf_converter.py       # PDF-Konvertierung
│   └── email_generator.py     # E-Mail-Text
├── data/
│   ├── input/                 # Hochgeladene PDFs
│   └── output/                # Generierte Abrechnungen
└── README.md
```

## 🔧 Technologie-Stack

- **Python 3.10+**
- **Streamlit** - Web-UI
- **pdfplumber** - PDF-Extraktion
- **openpyxl** - Excel-Generierung
- **pandas** - Datenverarbeitung
- **LibreOffice** - PDF-Konvertierung

## 📝 Beispiel-Output

```
Betriebskostenabrechnung 2023

Kostenart                           Betrag
─────────────────────────────────────────
Niederschlagsentwässerung         16,42 €
Trinkwasseruntersuchung          25,69 €
Heiz- und Wasserkostenabrechnung 681,60 €
...
Grundsteuer                      251,07 €
─────────────────────────────────────────
Gesamtkosten                   1.863,98 €

abzgl. Vorauszahlungen        -2.250,00 €
─────────────────────────────────────────
Guthaben                         386,02 €
```

## ⚠️ Hinweise

- **Mieterwechsel:** Zeitraum wird automatisch angepasst
- **Untergruppen:** Nur relevante UG2-Kosten werden berücksichtigt
- **MEA-Berechnung:** Automatisch für alle Kostenposten
- **Umlagefähigkeit:** Automatische Filterung nach deutschem Mietrecht

## 📧 Support

Bei Fragen oder Problemen:
- Issue auf GitHub erstellen
- Code überprüfen und anpassen

## 📄 Lizenz

Private Nutzung

---

**Erstellt mit ❤️ für automatisierte Nebenkostenabrechnungen**
