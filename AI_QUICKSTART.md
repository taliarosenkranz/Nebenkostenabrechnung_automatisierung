# 🤖 AI-Extraktion - Schnellstart

## 1. Installation

```bash
pip install openai python-dotenv
```

## 2. API Key einrichten

1. Gehe zu https://platform.openai.com/api-keys
2. Erstelle einen neuen API Key
3. Öffne die `.env` Datei und trage ein:

```
OPENAI_API_KEY=sk-proj-DEIN_KEY_HIER
```

## 3. Testen

```bash
# Test AI-Extraktion
python3 -m src.ai_extractor
```

## 4. In Streamlit verwenden

```bash
streamlit run app.py
```

In der App:
1. Sidebar → "🤖 AI (OpenAI)" wählen
2. WEG-Abrechnung hochladen
3. "Dokumente analysieren" klicken

## Fertig! 🎉

**Kosten:** ~$0.001-0.003 pro Abrechnung (sehr günstig!)

---

### Problemlösung

**API Key nicht gefunden?**
→ Stelle sicher, dass `.env` im Projektverzeichnis liegt

**OpenAI-Fehler?**
→ Überprüfe ob dein API Key gültig ist: https://platform.openai.com/api-keys

**Zu langsam?**
→ Normal! AI braucht 5-15 Sekunden. Für schnellere Ergebnisse: Standard-Methode verwenden
