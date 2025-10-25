# AI-basierte PDF-Extraktion

## Setup

### 1. Installiere zusätzliche Dependencies

```bash
pip install openai python-dotenv
```

Oder update alle Dependencies:

```bash
pip install -r requirements.txt
```

### 2. OpenAI API Key einrichten

1. Erstelle einen OpenAI Account auf https://platform.openai.com
2. Generiere einen API Key unter https://platform.openai.com/api-keys
3. Füge den API Key in die `.env` Datei ein:

```bash
# .env
OPENAI_API_KEY=sk-proj-...
```

**Wichtig:** Die `.env` Datei ist in `.gitignore` und wird nicht ins Git-Repository committed!

### 3. Verwendung

#### In Streamlit App

1. Starte die App: `streamlit run app.py`
2. In der Sidebar unter "Extraktionsmethode" wähle **🤖 AI (OpenAI)**
3. Lade die WEG-Abrechnung hoch
4. Klicke auf "Dokumente analysieren"

#### Als Standalone-Test

```bash
python3 -m src.ai_extractor
```

## Funktionsweise

Die AI-Extraktion verwendet **GPT-4o-mini** (oder GPT-4 für bessere Qualität) um:

1. Den gesamten PDF-Text zu lesen
2. Intelligente Identifizierung von umlagefähigen Kosten
3. Automatische Unterscheidung zwischen Gesamtbeträgen und Einheiten-spezifischen Beträgen
4. Rückgabe als strukturiertes JSON

### Vorteile gegenüber regelbasierter Extraktion

✅ **Flexibler:** Funktioniert auch mit verschiedenen PDF-Formaten  
✅ **Intelligenter:** Versteht Kontext und Bedeutung  
✅ **Weniger Fehleranfällig:** Keine starren Regex-Patterns nötig  
✅ **Selbstlernend:** Bessere Ergebnisse durch Training

### Nachteile

❌ **Kosten:** ~$0.01-0.05 pro Extraktion (je nach PDF-Länge)  
❌ **Langsamer:** 5-15 Sekunden pro Extraktion  
❌ **API-Abhängig:** Benötigt Internet und OpenAI-Account

## Kosten

**GPT-4o-mini Pricing (Stand 2024):**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Beispiel:** Eine 10-seitige WEG-Abrechnung ≈ 5,000 tokens
- Kosten: ~$0.001 - $0.003 pro Extraktion
- **Sehr günstig!**

## Modell wechseln

In `src/ai_extractor.py` kannst du das Modell ändern:

```python
response = client.chat.completions.create(
    model="gpt-4o",  # Statt "gpt-4o-mini" für bessere Qualität
    ...
)
```

**Verfügbare Modelle:**
- `gpt-4o-mini` - Schnell & günstig (empfohlen)
- `gpt-4o` - Bessere Qualität, etwas teurer
- `gpt-4-turbo` - Höchste Qualität, teuerster

## Troubleshooting

### Fehler: "OPENAI_API_KEY nicht gefunden"

→ Stelle sicher, dass `.env` Datei existiert und `OPENAI_API_KEY` enthält

### Fehler: "OpenAI-Paket nicht installiert"

→ Führe aus: `pip install openai python-dotenv`

### Fehler: "Rate limit exceeded"

→ Zu viele Anfragen. Warte 1 Minute oder upgrade deinen OpenAI Plan

### AI liefert falsche Ergebnisse

1. Überprüfe das PDF (ist es lesbar?)
2. Verwende `gpt-4o` statt `gpt-4o-mini` für bessere Qualität
3. Passe den Prompt in `_build_extraction_prompt()` an

## Datenschutz

**Wichtig:** Der PDF-Inhalt wird an OpenAI gesendet!

- OpenAI speichert keine Daten für Modell-Training (bei API-Nutzung)
- Trotzdem: Sensible Daten sollten vorher anonymisiert werden
- Mehr Infos: https://openai.com/policies/privacy-policy

## Vergleich der Methoden

| Feature | Standard | AI |
|---------|----------|-----|
| **Kosten** | Kostenlos | ~$0.001-0.003 |
| **Geschwindigkeit** | <1 Sekunde | 5-15 Sekunden |
| **Genauigkeit** | Gut (bei bekanntem Format) | Sehr gut (flexibel) |
| **Offline** | ✅ Ja | ❌ Nein |
| **API Key nötig** | ❌ Nein | ✅ Ja |
| **Neue PDF-Formate** | ⚠️ Anpassung nötig | ✅ Funktioniert meist |

## Empfehlung

- **Standard-Extraktion:** Für regelmäßige Abrechnungen vom gleichen Format
- **AI-Extraktion:** Für neue/unbekannte Formate oder bei Problemen mit Standard-Extraktion
