"""
═══════════════════════════════════════════════════════════════
EMAIL GENERATOR - E-Mail-Text für Mieter
═══════════════════════════════════════════════════════════════
"""

from datetime import date
from typing import Optional
import config


def generate_email_text(
    tenant_name: str,
    year: int,
    period_start: date,
    period_end: date,
    balance: float,
    custom_message: Optional[str] = None
) -> str:
    """
    Generiert E-Mail-Text für Mieter
    """
    
    # Determine balance type
    is_nachzahlung = balance > 0
    balance_label = "Nachzahlung" if is_nachzahlung else "Guthaben"
    
    # Format dates
    start_str = period_start.strftime('%d.%m.%Y')
    end_str = period_end.strftime('%d.%m.%Y')
    
    # Email text
    email = f"""Betreff: Nebenkostenabrechnung {year} - {config.PROPERTY['address']}

Sehr geehrte/r {tenant_name},

anbei erhalten Sie die Nebenkostenabrechnung für den Zeitraum {start_str} bis {end_str}.

"""
    
    if is_nachzahlung:
        email += f"""Aus der Verrechnung Ihrer geleisteten Vorauszahlungen mit den tatsächlichen Kosten ergibt sich eine Nachzahlung in Höhe von {abs(balance):.2f} EUR.

Bitte überweisen Sie den Betrag innerhalb von 30 Tagen auf das folgende Konto:

[Kontoinhaber]
[IBAN]
[BIC]
Verwendungszweck: Nebenkostenabrechnung {year}
"""
    else:
        email += f"""Aus der Verrechnung Ihrer geleisteten Vorauszahlungen mit den tatsächlichen Kosten ergibt sich ein Guthaben in Höhe von {abs(balance):.2f} EUR.

Bitte teilen Sie mir Ihre Bankverbindung mit, damit ich Ihnen den Betrag überweisen kann.
"""
    
    if custom_message:
        email += f"\n{custom_message}\n"
    
    email += f"""
Die detaillierte Abrechnung sowie eine Kopie der Hausgeldabrechnung der Wohnungseigentümergemeinschaft finden Sie im Anhang.

Bei Fragen stehe ich Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen,

{config.LANDLORD['name']}
"""
    
    return email


def generate_whatsapp_text(
    tenant_name: str,
    year: int,
    balance: float
) -> str:
    """
    Generiert kurzen WhatsApp/SMS-Text
    """
    
    first_name = tenant_name.split()[0]
    is_nachzahlung = balance > 0
    
    if is_nachzahlung:
        return f"""Hallo {first_name},

die Nebenkostenabrechnung {year} ist fertig. Es ergibt sich eine Nachzahlung von {abs(balance):.2f} EUR.

Ich schicke dir die Abrechnung gleich per E-Mail zu.

VG, {config.LANDLORD['name'].split()[0]}"""
    else:
        return f"""Hallo {first_name},

gute Nachrichten! Die Nebenkostenabrechnung {year} zeigt ein Guthaben von {abs(balance):.2f} EUR.

Details kommen per E-Mail.

VG, {config.LANDLORD['name'].split()[0]}"""
