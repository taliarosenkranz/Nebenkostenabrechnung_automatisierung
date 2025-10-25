"""
═══════════════════════════════════════════════════════════════
COST CALCULATOR - Kostenberechnung & Umlage
═══════════════════════════════════════════════════════════════
"""

from datetime import date
from typing import List, Dict, Any


def calculate_tenant_costs(
    weg_costs: List[Dict[str, Any]],
    payment_months: int,
    monthly_prepayment: float,
    period_start: date = None,
    period_end: date = None
) -> Dict[str, Any]:
    """
    Berechnet die Mieterkosten basierend auf WEG-Abrechnung
    
    WICHTIG: Berechnung = (Jahreskosten / 12) * Anzahl Monate
    
    Args:
        weg_costs: Liste der Kostenposten aus WEG-Abrechnung
        payment_months: Anzahl Monate die der Mieter Miete gezahlt hat
        monthly_prepayment: Monatliche Vorauszahlung (Nebenkosten)
        period_start: Optional - Start des Abrechnungszeitraums (für Dokumentation)
        period_end: Optional - Ende des Abrechnungszeitraums (für Dokumentation)
    
    Returns:
        {
            'items': [{'name': str, 'annual_amount': float, 'monthly_amount': float, 'tenant_share': float}, ...],
            'total_annual': float,
            'total_monthly': float,
            'total_costs': float,
            'prepayments': float,
            'balance': float,
            'payment_months': int
        }
    """
    
    # Calculate costs per item
    items = []
    
    for cost in weg_costs:
        cost_name = cost['name']
        annual_amount = cost['amount']
        
        # Monatliche Kosten = Jahreskosten / 12
        monthly_amount = annual_amount / 12
        
        # Mieter-Anteil = Monatliche Kosten * Anzahl Monate
        tenant_share = monthly_amount * payment_months
        
        items.append({
            'name': cost_name,
            'annual_amount': annual_amount,
            'monthly_amount': round(monthly_amount, 2),
            'tenant_share': round(tenant_share, 2)
        })
    
    # Calculate totals
    total_annual = sum(item['annual_amount'] for item in items)
    total_monthly = total_annual / 12
    total_costs = sum(item['tenant_share'] for item in items)
    prepayments = monthly_prepayment * payment_months
    balance = total_costs - prepayments
    
    return {
        'items': items,
        'total_annual': round(total_annual, 2),
        'total_monthly': round(total_monthly, 2),
        'total_costs': round(total_costs, 2),
        'prepayments': round(prepayments, 2),
        'balance': round(balance, 2),
        'payment_months': payment_months,
        'period_start': period_start,
        'period_end': period_end
    }


def calculate_pro_rata(
    annual_cost: float, 
    start_date: date, 
    end_date: date
) -> float:
    """
    Berechnet anteilige Kosten für Zeitraum
    """
    days = (end_date - start_date).days + 1
    factor = days / 365
    
    return round(annual_cost * factor, 2)
