"""
═══════════════════════════════════════════════════════════════
AI EXTRACTOR - OpenAI-basierte PDF-Extraktion
═══════════════════════════════════════════════════════════════
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pdfplumber

# Load environment variables
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


def extract_weg_data_ai(pdf_path: str, year: int, einheit: str = None) -> Dict[str, Any]:
    """
    Extrahieif __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "bank":
        test_bank_extraction()
    elif len(sys.argv) > 1 and sys.argv[1] == "rental":
        test_rental_extraction()
    elif len(sys.argv) > 1 and sys.argv[1] == "full":
        test_full_ai_workflow()
    else:
        test_ai_extraction()fähige Kosten aus WEG-Hausgeldabrechnung mit OpenAI
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        year: Abrechnungsjahr
        einheit: Einheit (z.B. "01080/05") - optional
    
    Returns:
        {
            'costs': [{'name': str, 'amount': float}, ...],
            'total': float,
            'period': {'start': date, 'end': date},
            'extraction_method': 'ai'
        }
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI-Paket nicht installiert. Bitte installieren mit: pip install openai"
        )
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nicht gefunden. Bitte in .env Datei eintragen."
        )
    
    # Extract text from PDF
    print("📄 Extrahiere PDF-Text...")
    pdf_text = _extract_pdf_text(pdf_path)
    print(f"✓ {len(pdf_text)} Zeichen extrahiert")
    
    # Prepare prompt
    prompt = _build_extraction_prompt(einheit)
    
    # Call OpenAI API
    print("🤖 Sende Anfrage an OpenAI...")
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Latest GPT-4 model
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Nebenkostenabrechnungen und Wirtschaftspläne von Wohnungseigentümergemeinschaften."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\n\nPDF-Inhalt:\n{pdf_text}"
                }
            ],
            temperature=0.1,  # Niedrig für konsistente Ergebnisse
            response_format={"type": "json_object"}  # JSON-Modus
        )
        
        print("✓ OpenAI Antwort erhalten")
        
        # Parse response
        result_text = response.choices[0].message.content
        
        # DEBUG: Print raw response
        print("\n" + "=" * 80)
        print("🤖 OPENAI RAW OUTPUT:")
        print("=" * 80)
        print(result_text)
        print("=" * 80 + "\n")
        
        result_json = json.loads(result_text)
        
        print(f"✓ JSON erfolgreich geparst")
        print(f"  - Kosten gefunden: {len(result_json.get('umlagefaehige_kosten', []))}")
        print(f"  - Gesamtsumme: {result_json.get('gesamt_summe', 0)}")
        
        # Convert to our format
        costs = []
        excluded_keywords = [
            'instandhaltung', 'reparatur', 'rücklage', 
            'versicherungsschaden', 'schaden', 'schadensbehebung',
            'verwaltung', 'hausverwaltung', 'aufwand versicherung'
        ]
        
        for item in result_json.get('umlagefaehige_kosten', []):
            for name, amount in item.items():
                # Filter out non-umlagefähig costs
                name_lower = name.lower()
                if any(keyword in name_lower for keyword in excluded_keywords):
                    print(f"  ⚠️  Übersprungen (nicht umlagefähig): {name}")
                    continue
                
                costs.append({
                    'name': name,
                    'amount': float(amount)
                })
                print(f"  + {name}: {amount} €")
        
        total = result_json.get('gesamt_summe', sum(c['amount'] for c in costs))
        
        print(f"\n✅ Extraktion abgeschlossen: {len(costs)} Kosten, Total: {total:.2f} €")
        
        return {
            'costs': costs,
            'total': float(total),
            'period': {
                'start': datetime(year, 1, 1).date(),
                'end': datetime(year, 12, 31).date()
            },
            'extraction_method': 'ai',
            'model_used': 'gpt-4-turbo'
        }
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"Raw output: {result_text[:500]}...")
        raise ValueError(f"AI-Antwort konnte nicht als JSON geparst werden: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise RuntimeError(f"Fehler bei AI-Extraktion: {e}")


def _extract_pdf_text(pdf_path: str, max_pages: int = 30) -> str:
    """
    Extrahiert Text aus PDF (erste max_pages Seiten)
    """
    text_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        pages_to_process = min(total_pages, max_pages)
        
        print(f"  📖 PDF hat {total_pages} Seiten, verarbeite {pages_to_process}")
        
        for i, page in enumerate(pdf.pages[:max_pages]):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Seite {i+1} ---\n{page_text}")
    
    return "\n\n".join(text_parts)


def _build_extraction_prompt(einheit: str = None) -> str:
    """
    Erstellt den Extraction-Prompt für OpenAI
    """
    einheit_info = f" für die Einheit {einheit}" if einheit else ""
    
    return f"""Make a copyable list of values and costs of the so called 'umlagefähigekosten' which are in the column of 'betrag'.

Return the results as JSON in this format:
{{
    "umlagefaehige_kosten": [{{"cost_name": amount}}, ...],
    "gesamt_summe": total_amount
}}
"""


def extract_bank_statement_ai(pdf_path: str, tenant_name: str = None) -> Dict[str, Any]:
    """
    Extrahiert Mietzahlungen aus Kontoauszug mit OpenAI
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        tenant_name: Name des Mieters (optional, für bessere Filterung)
    
    Returns:
        {
            'payments': [{'month': str, 'amount_eur': float, 'payment_date': str}, ...],
            'total_months': int,
            'total_rent_paid_eur': float,
            'period': str,
            'extraction_method': 'ai'
        }
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI-Paket nicht installiert. Bitte installieren mit: pip install openai"
        )
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nicht gefunden. Bitte in .env Datei eintragen."
        )
    
    # Extract text from PDF
    print("📄 Extrahiere Kontoauszug-Text...")
    pdf_text = _extract_pdf_text(pdf_path)
    print(f"✓ {len(pdf_text)} Zeichen extrahiert")
    
    # Prepare prompt
    prompt = _build_bank_extraction_prompt(tenant_name)
    
    # Call OpenAI API
    print("🤖 Sende Anfrage an OpenAI...")
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Bankkontoauszüge und Mietzahlungsanalyse."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\n\nKontoauszug:\n{pdf_text}"
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        print("✓ OpenAI Antwort erhalten")
        
        # Parse response
        result_text = response.choices[0].message.content
        
        # DEBUG: Print raw response
        print("\n" + "=" * 80)
        print("🤖 OPENAI RAW OUTPUT:")
        print("=" * 80)
        print(result_text)
        print("=" * 80 + "\n")
        
        result_json = json.loads(result_text)
        
        print(f"✓ JSON erfolgreich geparst")
        print(f"  - Zahlungen gefunden: {result_json.get('total_months', 0)}")
        print(f"  - Gesamtmiete: {result_json.get('total_rent_paid_eur', 0)} €")
        print(f"  - Zeitraum: {result_json.get('period', 'N/A')}")
        
        # Print each payment
        for payment in result_json.get('payments', []):
            print(f"  + {payment.get('month')}: {payment.get('amount_eur')} € (am {payment.get('payment_date')})")
        
        print(f"\n✅ Extraktion abgeschlossen: {result_json.get('total_months', 0)} Mietzahlungen")
        
        return {
            'payments': result_json.get('payments', []),
            'total_months': result_json.get('total_months', 0),
            'total_rent_paid_eur': result_json.get('total_rent_paid_eur', 0.0),
            'period': result_json.get('period', ''),
            'extraction_method': 'ai',
            'model_used': 'gpt-4-turbo'
        }
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"Raw output: {result_text[:500]}...")
        raise ValueError(f"AI-Antwort konnte nicht als JSON geparst werden: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise RuntimeError(f"Fehler bei AI-Extraktion: {e}")


def _build_bank_extraction_prompt(tenant_name: str = None) -> str:
    """
    Erstellt den Extraction-Prompt für Kontoauszug
    """
    tenant_info = f" vom Mieter {tenant_name}" if tenant_name else ""
    
    return f"""Mach eine Liste von wie viel Miete{tenant_info} jeden Monat gezahlt wurde. Nimm nur die Miete, keine anderen Zahlungen. Am Ende summier wie viel Miete gezahlt wurde und wie viele Monate und schreib den Zeitraum von wann bis wann die Miete überwiesen wurde.

Achte drauf das wenn die Miete Anfang des Monats überwiesen wurde dann ist sie für den selben Monat. Wenn die Miete am Ende des Monats überwiesen wurde dann ist es für den nächsten Monat. Achte auf das Datum unter dem Betrag.

Return the results as JSON in this format:
{{
  "payments": [
    {{
      "month": "November 2024",
      "amount_eur": 1510,
      "payment_date": "05.11.2024"
    }},
    {{
      "month": "December 2024",
      "amount_eur": 1510,
      "payment_date": "03.12.2024"
    }}
  ],
  "total_months": 5,
  "total_rent_paid_eur": 7510,
  "period": "08 2024 - 12 2024"
}}
"""


def extract_rental_contract_ai(pdf_path: str) -> Dict[str, Any]:
    """
    Extrahiert Mieter-Name und Kaltmiete aus Mietvertrag mit OpenAI
    
    Args:
        pdf_path: Pfad zur PDF-Datei
    
    Returns:
        {
            'tenant_name': str,
            'base_rent_eur': float,
            'extraction_method': 'ai'
        }
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI-Paket nicht installiert. Bitte installieren mit: pip install openai"
        )
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nicht gefunden. Bitte in .env Datei eintragen."
        )
    
    # Extract text from PDF
    print("📄 Extrahiere Mietvertrag-Text...")
    pdf_text = _extract_pdf_text(pdf_path)
    print(f"✓ {len(pdf_text)} Zeichen extrahiert")
    
    # Prepare prompt
    prompt = _build_rental_extraction_prompt()
    
    # Call OpenAI API
    print("🤖 Sende Anfrage an OpenAI...")
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Mietverträge und Mietrecht."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\n\nMietvertrag:\n{pdf_text}"
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        print("✓ OpenAI Antwort erhalten")
        
        # Parse response
        result_text = response.choices[0].message.content
        
        # DEBUG: Print raw response
        print("\n" + "=" * 80)
        print("🤖 OPENAI RAW OUTPUT:")
        print("=" * 80)
        print(result_text)
        print("=" * 80 + "\n")
        
        result_json = json.loads(result_text)
        
        print(f"✓ JSON erfolgreich geparst")
        print(f"  - Mieter: {result_json.get('tenant_name', 'N/A')}")
        print(f"  - Kaltmiete: {result_json.get('base_rent_eur', 0)} €")
        
        print(f"\n✅ Extraktion abgeschlossen")
        
        return {
            'tenant_name': result_json.get('tenant_name', ''),
            'base_rent_eur': float(result_json.get('base_rent_eur', 0.0)),
            'extraction_method': 'ai',
            'model_used': 'gpt-4-turbo'
        }
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"Raw output: {result_text[:500]}...")
        raise ValueError(f"AI-Antwort konnte nicht als JSON geparst werden: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise RuntimeError(f"Fehler bei AI-Extraktion: {e}")


def _build_rental_extraction_prompt() -> str:
    """
    Erstellt den Extraction-Prompt für Mietvertrag
    """
    return """Lies den Mietvertrag und extrahiere ausschließlich den Namen des Mieters und die Grundmiete.

Der gesuchte Name steht im Abschnitt „Zwischen Mieter:" bzw. bei der Zeile „Vorname, Nachname". Verwende genau diesen Namen.

Gib **keinen anderen Namen** aus dem Dokument aus (z. B. nicht den Vermieter oder Personen aus anderen Textteilen). Es darf nur der tatsächliche Mietername ausgegeben werden.

Gib das Ergebnis ausschließlich in folgendem JSON-Format zurück, ohne zusätzlichen Text:

{
  "tenant_name": "Emanu Mingo",
  "base_rent_eur": 1100
}
"""


def calculate_monthly_prepayment_from_ai(
    bank_data: Dict[str, Any],
    rental_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Berechnet die monatliche Nebenkostenvorauszahlung aus AI-extrahierten Daten
    
    Neue Berechnungslogik:
    - Gesamtmiete (total_rent_paid_eur) - (Kaltmiete * Anzahl Monate) = Gesamt-Nebenkosten
    - Gesamt-Nebenkosten / Anzahl Monate = Monatliche Vorauszahlung
    
    Args:
        bank_data: Ergebnis von extract_bank_statement_ai()
        rental_data: Ergebnis von extract_rental_contract_ai()
    
    Returns:
        {
            'payment_months': int,
            'monthly_prepayment': float,
            'total_rent_paid': float,
            'total_base_rent': float,
            'total_nebenkosten': float
        }
    """
    total_months = bank_data.get('total_months', 0)
    total_rent_paid = bank_data.get('total_rent_paid_eur', 0.0)
    base_rent = rental_data.get('base_rent_eur', 0.0)
    
    # Berechne Gesamt-Kaltmiete für alle Monate
    total_base_rent = base_rent * total_months
    
    # Berechne Gesamt-Nebenkosten
    total_nebenkosten = total_rent_paid - total_base_rent
    
    # Berechne monatliche Vorauszahlung
    monthly_prepayment = total_nebenkosten / total_months if total_months > 0 else 0.0
    
    return {
        'payment_months': total_months,
        'monthly_prepayment': round(monthly_prepayment, 2),
        'total_rent_paid': total_rent_paid,
        'total_base_rent': total_base_rent,
        'total_nebenkosten': round(total_nebenkosten, 2)
    }


def test_ai_extraction():
    """
    Test-Funktion für AI-Extraktion
    """
    from pathlib import Path
    
    pdf_path = Path("data/input/Wirtschaftsplan_2024.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF nicht gefunden: {pdf_path}")
        return
    
    print("🤖 Teste AI-Extraktion...")
    print(f"📄 PDF: {pdf_path}")
    
    try:
        result = extract_weg_data_ai(str(pdf_path), 2024, "01080/05")
        
        print(f"\n✅ Erfolgreich extrahiert!")
        print(f"📊 Anzahl Kosten: {len(result['costs'])}")
        print(f"💰 Gesamtsumme: {result['total']:.2f} €")
        print(f"🤖 Modell: {result.get('model_used', 'unknown')}")
        
        print("\n📋 Kosten:")
        for i, cost in enumerate(result['costs'][:10], 1):
            print(f"  {i:2d}. {cost['name']:50s} {cost['amount']:>10.2f} €")
        
        if len(result['costs']) > 10:
            print(f"  ... und {len(result['costs']) - 10} weitere")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


def test_bank_extraction():
    """
    Test-Funktion für Kontoauszug AI-Extraktion
    """
    from pathlib import Path
    
    # Test with Gopi's bank statement
    pdf_path = Path("data/input/Gopi_miete_kontoauszüge.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF nicht gefunden: {pdf_path}")
        print("Verfügbare PDFs in data/input:")
        for p in Path("data/input").glob("*.pdf"):
            print(f"  - {p.name}")
        return
    
    print("🤖 Teste Kontoauszug AI-Extraktion...")
    print(f"📄 PDF: {pdf_path}")
    
    try:
        result = extract_bank_statement_ai(str(pdf_path), tenant_name="Vinayak Gopi")
        
        print(f"\n✅ Erfolgreich extrahiert!")
        print(f"📊 Anzahl Zahlungen: {result['total_months']}")
        print(f"💰 Gesamtmiete: {result['total_rent_paid_eur']:.2f} €")
        print(f"📅 Zeitraum: {result['period']}")
        print(f"🤖 Modell: {result.get('model_used', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


def test_rental_extraction():
    """
    Test-Funktion für Mietvertrag AI-Extraktion
    """
    from pathlib import Path
    
    # Test with Gopi's rental contract
    pdf_path = Path("data/input/Mietvertrag Vinayak Gopsi.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF nicht gefunden: {pdf_path}")
        print("Verfügbare PDFs in data/input:")
        for p in Path("data/input").glob("*.pdf"):
            print(f"  - {p.name}")
        return
    
    print("🤖 Teste Mietvertrag AI-Extraktion...")
    print(f"📄 PDF: {pdf_path}")
    
    try:
        result = extract_rental_contract_ai(str(pdf_path))
        
        print(f"\n✅ Erfolgreich extrahiert!")
        print(f"👤 Mieter: {result['tenant_name']}")
        print(f"💰 Kaltmiete: {result['base_rent_eur']:.2f} €")
        print(f"🤖 Modell: {result.get('model_used', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


def test_full_ai_workflow():
    """
    Test-Funktion für den kompletten AI-Workflow
    Zeigt wie Bank + Mietvertrag Daten zusammen verwendet werden
    """
    from pathlib import Path
    
    print("=" * 80)
    print("🤖 KOMPLETTER AI-WORKFLOW TEST")
    print("=" * 80)
    
    # 1. Extract rental contract
    print("\n📋 Schritt 1: Mietvertrag extrahieren...")
    rental_pdf = Path("data/input/Mietvertrag Vinayak Gopsi.pdf")
    if not rental_pdf.exists():
        print(f"❌ Mietvertrag nicht gefunden: {rental_pdf}")
        return
    
    try:
        rental_data = extract_rental_contract_ai(str(rental_pdf))
        print(f"✅ Mieter: {rental_data['tenant_name']}")
        print(f"✅ Kaltmiete: {rental_data['base_rent_eur']:.2f} €")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return
    
    # 2. Extract bank statement
    print("\n💰 Schritt 2: Kontoauszug extrahieren...")
    bank_pdf = Path("data/input/Gopi_miete_kontoauszüge.pdf")
    if not bank_pdf.exists():
        print(f"❌ Kontoauszug nicht gefunden: {bank_pdf}")
        return
    
    try:
        bank_data = extract_bank_statement_ai(
            str(bank_pdf), 
            tenant_name=rental_data['tenant_name']
        )
        print(f"✅ Anzahl Zahlungen: {bank_data['total_months']}")
        print(f"✅ Gesamtmiete bezahlt: {bank_data['total_rent_paid_eur']:.2f} €")
        print(f"✅ Zeitraum: {bank_data['period']}")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return
    
    # 3. Calculate monthly prepayment
    print("\n🧮 Schritt 3: Vorauszahlung berechnen...")
    calculation = calculate_monthly_prepayment_from_ai(bank_data, rental_data)
    
    print(f"  📊 Anzahl Monate: {calculation['payment_months']}")
    print(f"  💰 Gesamtmiete bezahlt: {calculation['total_rent_paid']:.2f} €")
    print(f"  🏠 Gesamt-Kaltmiete ({calculation['payment_months']} × {rental_data['base_rent_eur']:.2f} €): {calculation['total_base_rent']:.2f} €")
    print(f"  📈 Gesamt-Nebenkosten: {calculation['total_nebenkosten']:.2f} €")
    print(f"  💵 Monatliche Vorauszahlung: {calculation['monthly_prepayment']:.2f} €")
    
    print("\n" + "=" * 80)
    print("✅ WORKFLOW ERFOLGREICH")
    print("=" * 80)
    print(f"\n🎯 Verwende diese Werte für die Nebenkostenabrechnung:")
    print(f"   - Mieter: {rental_data['tenant_name']}")
    print(f"   - Anzahl Monate: {calculation['payment_months']}")
    print(f"   - Monatliche Vorauszahlung: {calculation['monthly_prepayment']:.2f} €")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "bank":
        test_bank_extraction()
    elif len(sys.argv) > 1 and sys.argv[1] == "rental":
        test_rental_extraction()
    else:
        test_full_ai_workflow()
