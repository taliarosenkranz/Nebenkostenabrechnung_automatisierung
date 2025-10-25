"""
═══════════════════════════════════════════════════════════════
PDF EXTRACTOR - WEG, Mietvertrag, Kontoauszug
═══════════════════════════════════════════════════════════════
"""

import pdfplumber
import re
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import config


def extract_weg_data(pdf_path: str, year: int) -> Dict[str, Any]:
    """
    Extrahiert umlagefähige Kosten aus WEG-Hausgeldabrechnung
    
    Returns nur die reinen Kosten - keine Kategorien oder Flags nötig!
    
    Returns:
        {
            'costs': [{'name': str, 'amount': float}, ...],
            'total': float,
            'period': {'start': date, 'end': date}
        }
    """
    costs = []
    
    # Use pdfplumber fruor reliable extraction
    try:
        costs = _extract_weg_fallback(pdf_path, year)
    except Exception as e:
        print(f"Extraction failed: {e}")
        raise
    
    return {
        'costs': costs,
        'total': sum(c['amount'] for c in costs),
        'period': {
            'start': datetime(year, 1, 1).date(),
            'end': datetime(year, 12, 31).date()
        }
    }


def _extract_weg_fallback(pdf_path: str, year: int) -> List[Dict[str, Any]]:
    """
    Fallback extraction using pdfplumber
    
    Strategy: Extract ALL costs BEFORE "Umlagefähige Kosten:" or "Sonstige betriebliche" row
    Everything after those rows is summary/not relevant
    """
    costs = []
    costs_dict = {}  # To track duplicates and keep highest amount
    found_summary = False  # Flag to stop when we hit "Umlagefähige Kosten:" or "Sonstige betriebliche"
    found_text_summary = False  # Separate flag for text extraction
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if found_summary:
                break  # Stop processing once we've seen the summary
            
            text = page.extract_text()
            
            # FIRST: Extract text-based costs (like Niederschlagsentwässerung, Hausnebenkosten, etc.)
            # These appear in green sections and are not in tables
            if text and not found_text_summary:
                lines = text.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Stop ONLY at "Umlagefähige Kosten:" - this is the summary row
                    if 'umlagefähige kosten:' in line.lower():
                        found_text_summary = True
                        break  # Stop text extraction, but let table extraction continue
                    
                    # Skip "Nicht umlagefähige Kosten:" section
                    if 'nicht umlagefähige kosten:' in line.lower() or 'nicht umlagefaehige kosten:' in line.lower():
                        found_text_summary = True
                        break  # Stop text extraction, but let table extraction continue
                    
                    # MULTI-ROW PATTERN: "Cost Name ... number Der Betrag wurde wie folgt aufgeteilt:"
                    # Next lines: May have "=> Objekt WEG...", "=> UG1 ...", "=> UG2 ... AMOUNT"
                    # WICHTIG: Wir müssen BEIDE nehmen: WEG Anteil + UG2 Anteil
                    if 'der betrag wurde wie folgt aufgeteilt:' in line.lower():
                        # Extract cost name (remove total amount and the text at end)
                        cost_name = line.split('Der Betrag')[0].strip()
                        # Remove trailing number (total building amount)
                        cost_name = re.sub(r'\s+[-]?\d{1,3}(?:\.\d{3})*,\d{2}\s*$', '', cost_name)
                        cost_name = cost_name.strip()
                        
                        # Search for WEG Anteil AND UG2 lines in next lines
                        # STOP when we hit another "Der Betrag wurde wie folgt aufgeteilt" or other cost line
                        weg_amount = None
                        ug2_amount = None
                        
                        for j in range(1, 10):  # Check more lines
                            if i + j >= len(lines):
                                break
                            
                            check_line = lines[i + j].strip()
                            
                            # Stop if we hit another multi-row marker or a single-line cost
                            if 'der betrag wurde wie folgt aufgeteilt' in check_line.lower():
                                break
                            
                            # WEG Anteil (Objekt WEG Lietzenburger Straße 1-9)
                            if 'Objekt WEG' in check_line or 'objekt weg' in check_line.lower():
                                parts = check_line.split()
                                if parts:
                                    last_part = parts[-1]
                                    amount_match = re.match(r'^([-]?\d{1,3}(?:\.\d{3})*,\d{2})$', last_part)
                                    if amount_match:
                                        try:
                                            weg_amount = float(amount_match.group(1).replace('.', '').replace(',', '.'))
                                        except:
                                            pass
                            
                            # UG2 Anteil
                            if ('UG2' in check_line or 'ug2' in check_line.lower()) and 'Lietzenburger Straße 3-9' in check_line:
                                parts = check_line.split()
                                if parts:
                                    last_part = parts[-1]
                                    amount_match = re.match(r'^([-]?\d{1,3}(?:\.\d{3})*,\d{2})$', last_part)
                                    if amount_match:
                                        try:
                                            ug2_amount = float(amount_match.group(1).replace('.', '').replace(',', '.'))
                                        except:
                                            pass
                        
                        # Addiere WEG Anteil + UG2 Anteil
                        total_amount = (weg_amount or 0) + (ug2_amount or 0)
                        
                        # Speichere den Kostenpunkt wenn mindestens einer der Beträge vorhanden ist
                        if (weg_amount is not None or ug2_amount is not None) and len(cost_name) >= 3:
                            name_key = cost_name.lower().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                            
                            # Immer den neuen Wert überschreiben (nicht vergleichen, da wir jetzt beide Anteile haben)
                            costs_dict[name_key] = {
                                'name': cost_name,
                                'amount': total_amount
                            }
                        
                        # NICHT skip_lines verwenden - verarbeite Zeile für Zeile
                        i += 1
                        continue
                    
                    # SINGLE-LINE PATTERN: "Cost Name ... numbers ... 365/365 AMOUNT"
                    # The final amount is after "365/365" or at the end
                    # Example: "Niederschlagsentwässerung 3.840,51 10.000,00 Miteigentumsanteile 57,00 365/365 21,89"
                    
                    # Extract cost name (first word(s) before numbers start)
                    parts = line.split()
                    if len(parts) >= 2:
                        # The last part should be the amount
                        last_part = parts[-1]
                        amount_match = re.match(r'^(\d{1,3}(?:\.\d{3})*,\d{2})$', last_part)
                        
                        if amount_match:
                            amount_str = amount_match.group(1)
                            
                            # Find where the cost name ends (before first number)
                            cost_name_parts = []
                            for part in parts:
                                # Stop at first number or keyword
                                if re.search(r'\d', part) or part.lower() in ['miteigentumsanteile', 'festbetrag', 'anzahl']:
                                    break
                                cost_name_parts.append(part)
                            
                            if cost_name_parts:
                                cost_name = ' '.join(cost_name_parts).strip()
                                
                                # Skip non-cost lines
                                if len(cost_name) >= 3 and not any(skip in cost_name.lower() for skip in [
                                    'gesamt betrag', 'basis', 'verteilung', 'hausgeld', 'betrag',
                                    'kostenart', 'objekt weg', 'einheitennr', 'abrechnungszeitraum',
                                    'vorauszahlung', 'abrechnungsspitze', 'datum', 'debitorennr',
                                    'nutzungszeitraum', 'abrechnung', 'berech.tage', 'wohnung'
                                ]):
                                    # Parse amount
                                    try:
                                        amount = float(amount_str.replace('.', '').replace(',', '.'))
                                        if amount > 0:
                                            name_key = cost_name.lower().replace(' ', '').replace('-', '')
                                            
                                            if name_key in costs_dict:
                                                if amount > costs_dict[name_key]['amount']:
                                                    costs_dict[name_key] = {
                                                        'name': cost_name,
                                                        'amount': amount
                                                    }
                                            else:
                                                costs_dict[name_key] = {
                                                    'name': cost_name,
                                                    'amount': amount
                                                }
                                    except:
                                        pass
                    
                    i += 1
            
            # SECOND: Extract tables
            tables = page.extract_tables()
            
            for table in tables:
                if not table or found_summary:
                    continue
                
                # Check if this is a multi-row table with "=>" rows
                # Pattern: Row 0 = Cost name, Row 1 = "=> UG1 ...", Row 2 = "=> UG2 ..."
                has_ug2_rows = any(
                    row and len(row) > 1 and row[0] and 
                    ('=>' in str(row[0]) or 'UG2 Lietzenburger Straße 3-9' in str(row[1] if len(row) > 1 else ''))
                    for row in table[1:] if row
                )
                
                if has_ug2_rows:
                    # MULTI-ROW TABLE: Extract from UG2 row
                    cost_name = None
                    amount = None
                    
                    # First row should have the cost name
                    if table[0] and table[0][0]:
                        cost_name = str(table[0][0]).strip()
                    
                    # Find the UG2 row (should be row 2 typically)
                    for row in table[1:]:
                        if not row or len(row) < 2:
                            continue
                        
                        # Check if this is the UG2 row
                        if (row[0] and '=>' in str(row[0])) and (row[1] and 'UG2 Lietzenburger Straße 3-9' in str(row[1])):
                            # Extract amount from column [-2]
                            if len(row) >= 3:
                                cell = row[-2]
                                if cell and str(cell).strip():
                                    cell_str = str(cell).strip()
                                    
                                    # Parse German number format
                                    amount_match = re.search(r'(-?\d{1,3}(?:\.\d{3})*,\d{2})', cell_str)
                                    if not amount_match:
                                        amount_match = re.search(r'(-?\d{1,3}(?:\.\d{3})*)', cell_str)
                                    
                                    if amount_match:
                                        try:
                                            amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                            parsed = float(amount_str)
                                            if abs(parsed) > 0.01 and abs(parsed) < 10000:
                                                amount = parsed
                                        except:
                                            pass
                            break
                    
                    # Add this cost if we found both name and amount
                    # ABER: Nicht überschreiben wenn bereits ein Text-basierter Wert existiert
                    # (Text-basierte Multi-Row-Werte haben WEG + UG2, Tabellen haben nur UG2)
                    if cost_name and amount:
                        cost_name_lower = cost_name.lower()
                        
                        # Skip if this is a summary row
                        if 'umlagefähige kosten:' in cost_name_lower or 'nicht umlagefähige' in cost_name_lower:
                            found_summary = True
                            break
                        
                        name_key = cost_name_lower.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                        
                        # Nur hinzufügen wenn noch nicht vorhanden (Text-Extraktion hat Vorrang)
                        if name_key not in costs_dict:
                            costs_dict[name_key] = {
                                'name': cost_name,
                                'amount': amount
                            }
                    
                    continue  # Skip normal row processing for this table
                
                # NORMAL SINGLE-ROW TABLES
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    
                    # Try to find cost items
                    cost_name = str(row[0]).strip() if row[0] else ""
                    
                    # Skip empty or very short names
                    if not cost_name or len(cost_name) < 3:
                        continue
                    
                    cost_name_lower = cost_name.lower()
                    
                    # STOP if we hit "Umlagefähige Kosten:" - everything after this is summary
                    if 'umlagefähige kosten:' in cost_name_lower or 'umlagefaehige kosten:' in cost_name_lower:
                        found_summary = True
                        break
                    
                    # Also stop at "Nicht umlagefähige Kosten:" or "Sonstige betriebliche"
                    if any(marker in cost_name_lower for marker in [
                        'nicht umlagefähige kosten:', 'nicht umlagefaehige kosten:',
                        'sonstige betriebliche', 'eigentümerversammlung', 
                        'verwaltung', 'gutachten', 'laufende reparaturen'
                    ]):
                        found_summary = True
                        break
                    
                    # STRICT FILTER: Skip all non-cost rows
                    if any(skip in cost_name_lower for skip in [
                        'kostenart', 'gesamt betrag', 'summe:', 'total',
                        'anfangsbestand', 'endbestand', 'entnahmen',  # Balance rows
                        'gesamtkosten:', 'hausgeld',  # Headers (but NOT hausnebenkosten!)
                        'abrechnungszeitraum', 'objekt:', 'eigentümernr',  # Metadata
                        'vertragsnr', 'einheitennr', 'sehr geehrte',  # Metadata
                        'anbei erhalten', 'mit freundlichen',  # Text
                        'wir freuen uns', 'bitte teilen',  # Text
                        '=>', 'ug1 ', 'ug2 ', 'untergruppe',  # Subgroups markers
                        'abrechnungsspitze',  # Summary
                        'ungezieferbekämpfung (nicht'  # Specifically "nicht umlagefähig"
                    ]):
                        continue
                    
                    # SPECIAL: Skip "Anlagen" (attachments) but ALLOW "Außenanlagen", "Aufzugsanlagen", etc.
                    if cost_name_lower == 'anlagen':
                        continue
                    
                    # SPECIAL: Skip "Hausgeldabrechnung" but ALLOW "Hausnebenkosten"
                    if 'hausgeld' in cost_name_lower and 'neben' not in cost_name_lower:
                        continue
                    
                    # SPECIAL: Skip generic "abrechnung" but ALLOW "Heiz- und Wasserkostenabrechnung"
                    if 'abrechnung' in cost_name_lower and not any(keep in cost_name_lower for keep in 
                        ['heiz', 'wasser', 'kosten']):
                        continue
                    
                    # Find "Betrag" column 
                    # In this PDF format, the amount is typically in the SECOND-TO-LAST column
                    # (last column is often empty)
                    amount = None
                    found_in_primary_column = False
                    
                    # Try second-to-last column first (this is where "Betrag" usually is)
                    if len(row) >= 3:  # Need at least 3 columns
                        # Try column [-2] (second from right)
                        cell = row[-2] if len(row) > 1 else None
                        if cell and str(cell).strip():
                            cell_str = str(cell).strip()
                            
                            # Skip if it's text, not a number
                            if not any(skip in cell_str.lower() for skip in 
                                ['miteigentumsanteile', 'festbetrag', 'tage', 'verteilung', 'ug1', 'ug2']):
                                
                                # Parse German number format
                                amount_match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', cell_str)
                                if not amount_match:
                                    amount_match = re.search(r'(\d{1,3}(?:\.\d{3})*)', cell_str)
                                
                                if amount_match:
                                    try:
                                        amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                        parsed = float(amount_str)
                                        # Accept ANY value including 0.00 from primary column
                                        if -10000 < parsed < 10000:
                                            amount = parsed
                                            found_in_primary_column = True
                                    except:
                                        pass
                    
                    # If not found in [-2], try searching from right to left
                    # But ONLY if we didn't find a valid number in the primary column
                    if not found_in_primary_column:
                        for cell in reversed(row[1:]):  # Skip first column (name)
                            if not cell or not str(cell).strip():
                                continue
                            
                            cell_str = str(cell).strip()
                            
                            # Skip text cells
                            if any(skip in cell_str.lower() for skip in 
                                ['miteigentumsanteile', 'festbetrag', 'aufgeteilt', 'direkt',
                                 'tage', 'der betrag wurde', 'verteilung', 'ug1', 'ug2']):
                                continue
                            
                            # Skip MEA values
                            if cell_str in ['5424.00', '5.424,00', '5424,00', '4504,00', '10000,00', '57,00', '57.00']:
                                continue
                            
                            # Parse number
                            amount_match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', cell_str)
                            if not amount_match:
                                amount_match = re.search(r'(\d{1,3}(?:\.\d{3})*)', cell_str)
                            
                            if amount_match:
                                try:
                                    amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                    parsed = float(amount_str)
                                    if 0.01 < parsed < 10000:
                                        amount = parsed
                                        break
                                except:
                                    pass
                    
                    # Check if this is a valid cost item
                    # Note: amount can be 0.00 (from primary column), but we only add if > 0
                    if cost_name and amount is not None and amount > 0:
                        # Normalize name for duplicate detection
                        name_key = cost_name_lower.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                        
                        # If duplicate, keep the HIGHER amount (main table usually has higher values)
                        if name_key in costs_dict:
                            if amount > costs_dict[name_key]['amount']:
                                costs_dict[name_key] = {
                                    'name': cost_name,
                                    'amount': amount
                                }
                        else:
                            costs_dict[name_key] = {
                                'name': cost_name,
                                'amount': amount
                            }
    
    # Convert dict back to list
    return list(costs_dict.values())


def extract_rental_contract(pdf_path: str) -> Dict[str, Any]:
    """
    Extrahiert Mieter-Informationen aus Mietvertrag
    
    Returns:
        {
            'name': str,
            'start_date': date,
            'monthly_rent': float,
            'betriebskosten_voraus': float,
            'heizkosten_voraus': float,
            'monthly_prepayment': float  # Total: Betriebskosten + Heizkosten
        }
    """
    result = {
        'name': None,
        'start_date': None,
        'monthly_rent': None,
        'betriebskosten_voraus': None,
        'heizkosten_voraus': None,
        'monthly_prepayment': None
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        # Extract text from all pages
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
        
        # Extract tenant name
        for pattern in config.RENTAL_CONTRACT_PATTERNS['mieter_name']:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                result['name'] = match.group(1).strip()
                break
        
        # Extract rental start date
        for pattern in config.RENTAL_CONTRACT_PATTERNS['mietbeginn']:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Try to parse date
                for fmt in ['%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%y']:
                    try:
                        result['start_date'] = datetime.strptime(date_str, fmt).date()
                        break
                    except:
                        pass
                if result['start_date']:
                    break
        
        # Extract Grundmiete/Kaltmiete
        for pattern in config.RENTAL_CONTRACT_PATTERNS['kaltmiete']:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace('.', '').replace(',', '.').replace('--', '')
                    result['monthly_rent'] = float(amount_str)
                    break
                except:
                    pass
        
        # Extract Betriebskostenvorauszahlung
        for pattern in config.RENTAL_CONTRACT_PATTERNS['nebenkosten_voraus']:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace('.', '').replace(',', '.').replace('--', '')
                    result['betriebskosten_voraus'] = float(amount_str)
                    break
                except:
                    pass
        
        # Extract Heizkosten/Heizung Vorauszahlung
        for pattern in config.RENTAL_CONTRACT_PATTERNS['heizkosten_voraus']:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace('.', '').replace(',', '.').replace('--', '')
                    result['heizkosten_voraus'] = float(amount_str)
                    break
                except:
                    pass
        
        # Calculate total monthly prepayment (Betriebskosten + Heizkosten)
        betriebskosten = result['betriebskosten_voraus'] or 0
        heizkosten = result['heizkosten_voraus'] or 0
        if betriebskosten > 0 or heizkosten > 0:
            result['monthly_prepayment'] = betriebskosten + heizkosten
    
    return result


def extract_bank_statement(pdf_path: str, year: int) -> Dict[str, Any]:
    """
    Extrahiert Mietzahlungen aus Kontoauszug
    
    Format: 
    Zeile 1: Emanuela Mingo +1.100,00 EUR
    Zeile 2: MIETE LIETZENBURGER STR 3 EREF: ... 24.08.2023
    
    Returns:
        {
            'payments': [{'date': date, 'amount': float}, ...],
            'payment_count': int,
            'avg_payment': float,
            'first_payment_date': date,
            'last_payment_date': date,
            'months_covered': [1, 2, 3, ...],
            'missing_months': [10, 11, 12],
            'is_full_year': bool
        }
    """
    payments = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            
            # Process lines in pairs (name+amount, then description+date)
            for i in range(len(lines) - 1):
                current_line = lines[i]
                next_line = lines[i + 1]
                
                # Check if current line has name and amount
                has_name = any(
                    keyword.lower() in current_line.lower() 
                    for keyword in config.BANK_STATEMENT_PATTERNS['mietzahlung']
                )
                
                if has_name and 'EUR' in current_line:
                    # Extract amount from current line
                    amount_match = re.search(r'([+-]?\s*[\d.,]+)\s*EUR', current_line)
                    
                    if not amount_match:
                        continue
                    
                    # Parse amount
                    try:
                        amt_str = amount_match.group(1).replace('+', '').replace(' ', '').replace('.', '').replace(',', '.')
                        amount = abs(float(amt_str))
                    except:
                        continue
                    
                    payment_date = None
                    
                    # FORMAT 1: Check if next line has payment description (Emanuela Mingo format)
                    # "MIETE LIETZENBURGER STR 3 EREF: ... 24.08.2023"
                    has_payment_desc = any(
                        keyword.lower() in next_line.lower() 
                        for keyword in ['miete', 'rent', 'lietzenburger']
                    )
                    
                    if has_payment_desc:
                        # Extract date from next line (rightmost date)
                        date_matches = re.findall(r'(\d{2}\.\d{2}\.\d{4})', next_line)
                        
                        if date_matches:
                            # Parse date (take last/rightmost date)
                            try:
                                payment_date = datetime.strptime(date_matches[-1], '%d.%m.%Y').date()
                            except:
                                pass
                    
                    # FORMAT 2: Check if next line has MM/YY format (Vinayak Gopi format)
                    # "miete10/24                           Valuta 03.10.2024 - 04.10.2024"
                    # OR "12/24                                    03.12.2024"
                    if not payment_date:
                        # Try to find date in DD.MM.YYYY format
                        date_matches = re.findall(r'(\d{2}\.\d{2}\.\d{4})', next_line)
                        if date_matches:
                            try:
                                # Take the FIRST date (not last, as in Format 1)
                                payment_date = datetime.strptime(date_matches[0], '%d.%m.%Y').date()
                            except:
                                pass
                        
                        # If still no date, try to parse MM/YY at start of line
                        if not payment_date:
                            month_year_match = re.search(r'^(\d{1,2})/(\d{2})', next_line)
                            if month_year_match:
                                try:
                                    month = int(month_year_match.group(1))
                                    year_short = int(month_year_match.group(2))
                                    # Assume 20XX for year
                                    full_year = 2000 + year_short
                                    # Use first day of month as payment date
                                    payment_date = datetime(full_year, month, 1).date()
                                except:
                                    pass
                    
                    # Add payment if we found a date and it's in the requested year
                    if payment_date and payment_date.year == year and amount > 0:
                        payments.append({
                            'date': payment_date,
                            'amount': amount
                        })
    
    # Sort by date
    payments.sort(key=lambda x: x['date'])
    
    # Determine which months are covered
    months_covered = sorted(list(set(p['date'].month for p in payments))) if payments else []
    all_months = list(range(1, 13))
    missing_months = [m for m in all_months if m not in months_covered]
    is_full_year = len(missing_months) == 0
    
    # Calculate stats
    result = {
        'payments': payments,
        'payment_count': len(payments),
        'avg_payment': sum(p['amount'] for p in payments) / len(payments) if payments else 0,
        'first_payment_date': payments[0]['date'] if payments else None,
        'last_payment_date': payments[-1]['date'] if payments else None,
        'months_covered': months_covered,
        'missing_months': missing_months,
        'is_full_year': is_full_year
    }
    
    return result
