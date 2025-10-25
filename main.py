"""
═══════════════════════════════════════════════════════════════
NEBENKOSTENABRECHNUNG - MAIN CLI
═══════════════════════════════════════════════════════════════

Alternative CLI-Version (falls Streamlit nicht gewünscht)
Für Web-UI nutze: streamlit run app.py
"""

import sys
from pathlib import Path
from datetime import datetime, date

from src.pdf_extractor import extract_weg_data, extract_rental_contract, extract_bank_statement
from src.cost_calculator import calculate_tenant_costs
from src.excel_generator import create_nebenkostenabrechnung
from src.pdf_converter import convert_excel_to_pdf
from src.email_generator import generate_email_text
import config


def main():
    print("=" * 60)
    print("  NEBENKOSTENABRECHNUNG - AUTOMATISIERUNG")
    print("=" * 60)
    print()
    
    # Year
    year = int(input("Abrechnungsjahr (z.B. 2023): ") or datetime.now().year)
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: WEG-Abrechnung (OBLIGATORISCH)
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 1: WEG-Abrechnung (PFLICHT)")
    print("=" * 60)
    
    weg_pdf = input("WEG-Abrechnung PDF (Pfad): ").strip()
    if not weg_pdf:
        print("❌ WEG-Abrechnung ist obligatorisch!")
        sys.exit(1)
    
    try:
        weg_data = extract_weg_data(weg_pdf, year)
        print(f"✅ {len(weg_data['costs'])} Kostenposten gefunden")
        print(f"✅ Gesamtsumme: {weg_data['total']:.2f} €")
    except Exception as e:
        print(f"❌ Fehler beim Lesen der WEG-Abrechnung: {e}")
        sys.exit(1)
    
    # ═══════════════════════════════════════════════════════════
    # STEP 2: Mietvertrag (OPTIONAL)
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 2: Mietvertrag (Optional)")
    print("=" * 60)
    
    rental_pdf = input("Mietvertrag PDF (Pfad, Enter = überspringen): ").strip()
    
    rental_data = {}
    if rental_pdf:
        try:
            rental_data = extract_rental_contract(rental_pdf)
            print(f"✅ Mieter: {rental_data.get('name', 'NICHT GEFUNDEN')}")
            print(f"✅ Vorauszahlung: {rental_data.get('nebenkosten_voraus', 'NICHT GEFUNDEN')} €")
        except Exception as e:
            print(f"⚠️  Warnung: Konnte Mietvertrag nicht lesen: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: Kontoauszug (OPTIONAL)
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 3: Kontoauszug (Optional)")
    print("=" * 60)
    
    bank_pdf = input("Kontoauszug PDF (Pfad, Enter = überspringen): ").strip()
    
    bank_data = {}
    if bank_pdf:
        try:
            bank_data = extract_bank_statement(bank_pdf, year)
            print(f"✅ Zahlungen: {bank_data['payment_count']} Monate")
            print(f"✅ Durchschnitt: {bank_data['avg_payment']:.2f} €/Monat")
        except Exception as e:
            print(f"⚠️  Warnung: Konnte Kontoauszug nicht lesen: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 4: Manuelle Eingaben
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("EINGABEN ÜBERPRÜFEN/ERGÄNZEN")
    print("=" * 60)
    
    # Tenant name
    default_name = rental_data.get('name', '')
    tenant_name = input(f"Mieter-Name [{default_name or 'Eingabe erforderlich'}]: ").strip()
    if not tenant_name:
        tenant_name = default_name
    if not tenant_name:
        print("❌ Mieter-Name ist erforderlich!")
        sys.exit(1)
    
    # Period
    period_start = date(year, 1, 1)
    period_end = date(year, 12, 31)
    
    custom_period = input("Eigenen Zeitraum verwenden? (j/n) [n]: ").strip().lower()
    if custom_period == 'j':
        period_start_str = input(f"Abrechnungsstart (JJJJ-MM-TT) [{year}-01-01]: ") or f"{year}-01-01"
        period_end_str = input(f"Abrechnungsende (JJJJ-MM-TT) [{year}-12-31]: ") or f"{year}-12-31"
        period_start = datetime.strptime(period_start_str, '%Y-%m-%d').date()
        period_end = datetime.strptime(period_end_str, '%Y-%m-%d').date()
    
    # Payment months
    default_months = bank_data.get('payment_count', 12)
    months_input = input(f"Anzahl Monate die Miete gezahlt wurde [{default_months}]: ").strip()
    payment_months = int(months_input) if months_input else default_months
    
    # Monthly prepayment
    default_prepay = rental_data.get('nebenkosten_voraus') or bank_data.get('avg_payment', 0)
    prepay_input = input(f"Monatliche Nebenkostenvorauszahlung in € [{default_prepay:.2f if default_prepay else 'Eingabe erforderlich'}]: ").strip()
    
    if prepay_input:
        monthly_prepayment = float(prepay_input.replace(',', '.'))
    elif default_prepay:
        monthly_prepayment = float(default_prepay)
    else:
        print("❌ Monatliche Vorauszahlung ist erforderlich!")
        sys.exit(1)
    
    # ═══════════════════════════════════════════════════════════
    # STEP 5: Berechnung
    # ═══════════════════════════════════════════════════════════
    print("\n🔢 Berechne Kosten...")
    print(f"   Formel: (Jahreskosten {weg_data['total']:.2f} € / 12) * {payment_months} Monate")
    
    result = calculate_tenant_costs(
        weg_costs=weg_data['costs'],
        payment_months=payment_months,
        monthly_prepayment=monthly_prepayment,
        period_start=period_start,
        period_end=period_end
    )
    
    # Display result
    print("\n" + "=" * 60)
    print("ERGEBNIS")
    print("=" * 60)
    print(f"Jahreskosten:     {result['total_annual']:>10.2f} €")
    print(f"Pro Monat:        {result['total_monthly']:>10.2f} €")
    print(f"Für {payment_months} Monate:    {result['total_costs']:>10.2f} €")
    print(f"Vorauszahlungen: -{result['prepayments']:>10.2f} €")
    print("-" * 60)
    
    balance = result['balance']
    label = "Nachzahlung" if balance > 0 else "Guthaben"
    print(f"{label}:        {abs(balance):>10.2f} €")
    print("=" * 60)
    
    # Generate documents
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    excel_path = output_dir / f"Nebenkostenabrechnung_{tenant_name.split()[-1]}_{year}.xlsx"
    pdf_path = excel_path.with_suffix('.pdf')
    email_path = output_dir / f"Email_Text_{tenant_name.split()[-1]}_{year}.txt"
    
    print("\n📝 Erstelle Dokumente...")
    
    create_nebenkostenabrechnung(result, tenant_name, str(excel_path), year)
    print(f"✅ Excel: {excel_path}")
    
    convert_excel_to_pdf(str(excel_path), str(pdf_path))
    print(f"✅ PDF: {pdf_path}")
    
    email_text = generate_email_text(tenant_name, year, period_start, period_end, balance)
    with open(email_path, 'w', encoding='utf-8') as f:
        f.write(email_text)
    print(f"✅ E-Mail: {email_path}")
    
    print("\n🎉 Fertig!")


if __name__ == "__main__":
    main()
