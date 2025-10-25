"""
═══════════════════════════════════════════════════════════════
STREAMLIT UI - NEBENKOSTENABRECHNUNG
═══════════════════════════════════════════════════════════════
"""

import streamlit as st
from datetime import datetime, date
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.pdf_extractor import extract_weg_data, extract_rental_contract, extract_bank_statement
from src.ai_extractor import extract_weg_data_ai, extract_rental_contract_ai, extract_bank_statement_ai, calculate_monthly_prepayment_from_ai, OPENAI_AVAILABLE
from src.cost_calculator import calculate_tenant_costs
from src.excel_generator import create_nebenkostenabrechnung
from src.pdf_converter import convert_excel_to_pdf
from src.email_generator import generate_email_text
import config

# ════════════════════════════════════════════════════════
#  PAGE CONFIG
# ════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Nebenkostenabrechnung",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════
#  CUSTOM CSS
# ════════════════════════════════════════════════════════
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-header {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #155724;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
#  MAIN APP
# ════════════════════════════════════════════════════════

def main():
    # Header
    st.markdown('<div class="main-header">🏠 Nebenkostenabrechnung Automatisierung</div>', 
                unsafe_allow_html=True)
    
    # Initialize session state
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'generated_files' not in st.session_state:
        st.session_state.generated_files = None
    if 'calculation_result' not in st.session_state:
        st.session_state.calculation_result = None
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Konfiguration")
        
        # Year selection
        current_year = datetime.now().year
        year = st.selectbox(
            "Abrechnungsjahr",
            options=list(range(current_year - 5, current_year + 1)),
            index=5
        )
        
        st.divider()
        
        # Extraction method selection
        st.subheader("🔧 Extraktionsmethode")
        
        if OPENAI_AVAILABLE:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            has_api_key = bool(os.getenv('OPENAI_API_KEY'))
            
            extraction_method = st.radio(
                "WEG-Abrechnung Extraktion",
                options=["🤖 AI (OpenAI)", "Standard (Regelbasiert)"],
                index=0,  # AI is default
                help="AI: GPT-4-turbo für intelligente Extraktion\nStandard: Schnell, kostenlos, regelbasiert"
            )
            
            if extraction_method == "🤖 AI (OpenAI)":
                if not has_api_key:
                    st.warning("⚠️ OPENAI_API_KEY nicht in .env gefunden!")
                    st.caption("Bitte API Key in .env eintragen:")
                    st.code("OPENAI_API_KEY=sk-...", language="bash")
                else:
                    st.success("✅ OpenAI API Key gefunden")
                    st.info("💡 Lade alle 3 PDFs hoch für vollautomatische Extraktion!")
        else:
            extraction_method = "Standard (Regelbasiert)"
            st.info("💡 AI-Extraktion nicht verfügbar")
            st.caption("Installiere: pip install openai python-dotenv")
        
        st.divider()
        
        # Property info
        st.subheader("📍 Immobilie")
        st.text(config.PROPERTY['address'])
        st.caption(f"Einheit: {config.PROPERTY['einheit']}")
        st.caption(f"MEA: {config.MEA['anteile']}/{config.MEA['basis_ug2']}")
        
        st.divider()
        
        # Landlord info
        st.subheader("👤 Eigentümer")
        st.text(config.LANDLORD['name'])
    
    # ════════════════════════════════════════════════════════
    #  STEP 1: UPLOAD FILES
    # ════════════════════════════════════════════════════════
    st.markdown('<div class="step-header"><h2>📤 Schritt 1: Dokumente hochladen</h2></div>', 
                unsafe_allow_html=True)
    
    st.info("ℹ️ **Nur die WEG-Abrechnung ist Pflicht.** Mietvertrag und Kontoauszug sind optional - fehlende Daten können Sie manuell eingeben.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("WEG-Abrechnung ⚠️ PFLICHT")
        weg_pdf = st.file_uploader(
            "Jahresabrechnung (PDF)",
            type=['pdf'],
            key='weg',
            help="Hausgeldabrechnung von der Hausverwaltung - ERFORDERLICH"
        )
        if weg_pdf:
            st.success(f"✓ {weg_pdf.name}")
        else:
            st.warning("⚠️ Erforderlich")
    
    with col2:
        st.subheader("Mietvertrag (Optional)")
        rental_pdf = st.file_uploader(
            "Mietvertrag (PDF)",
            type=['pdf'],
            key='rental',
            help="Optional: Zur Extraktion von Mieter-Name und Vorauszahlung"
        )
        if rental_pdf:
            st.success(f"✓ {rental_pdf.name}")
        else:
            st.info("Optional - kann manuell eingegeben werden")
    
    with col3:
        st.subheader("Kontoauszüge (Optional)")
        bank_pdf = st.file_uploader(
            "Mietzahlungen (PDF)",
            type=['pdf'],
            key='bank',
            help="Optional: Zur Berechnung der gezahlten Monate"
        )
        if bank_pdf:
            st.success(f"✓ {bank_pdf.name}")
        else:
            st.info("Optional - kann manuell eingegeben werden")
    
    # ════════════════════════════════════════════════════════
    #  STEP 2: EXTRACT & PREVIEW
    # ════════════════════════════════════════════════════════
    #  STEP 2: EXTRACT & PREVIEW
    # ════════════════════════════════════════════════════════
    if weg_pdf:  # Only WEG is required
        st.markdown('<div class="step-header"><h2>🔍 Schritt 2: Daten extrahieren</h2></div>', 
                    unsafe_allow_html=True)
        
        analyze_button = st.button("📊 Dokumente analysieren", type="primary", use_container_width=True)
        
        if analyze_button:
            with st.spinner("🔄 PDFs werden verarbeitet..."):
                
                # Save uploaded files temporarily
                temp_dir = Path("data/input")
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                weg_path = temp_dir / weg_pdf.name
                with open(weg_path, 'wb') as f:
                    f.write(weg_pdf.getbuffer())
                
                # Extract WEG data (required)
                try:
                    # Choose extraction method
                    if extraction_method == "🤖 AI (OpenAI)":
                        st.info("🤖 Verwende AI-Extraktion (OpenAI)...")
                        weg_data = extract_weg_data_ai(
                            str(weg_path), 
                            year, 
                            einheit=config.PROPERTY['einheit']
                        )
                        st.success(f"✅ WEG (AI): {len(weg_data.get('costs', []))} Kostenposten extrahiert")
                        st.caption(f"🤖 Modell: {weg_data.get('model_used', 'gpt-4o-mini')}")
                    else:
                        st.info("⚙️ Verwende Standard-Extraktion (regelbasiert)...")
                        weg_data = extract_weg_data(str(weg_path), year)
                        st.success(f"✅ WEG: {len(weg_data.get('costs', []))} Kostenposten extrahiert")
                        
                except Exception as e:
                    st.error(f"❌ Fehler beim Lesen der WEG-Abrechnung: {str(e)}")
                    st.exception(e)
                    st.stop()
                
                # Extract rental data (optional)
                rental_data = {}
                if rental_pdf:
                    rental_path = temp_dir / rental_pdf.name
                    with open(rental_path, 'wb') as f:
                        f.write(rental_pdf.getbuffer())
                    
                    try:
                        if extraction_method == "🤖 AI (OpenAI)":
                            st.info("🤖 Verwende AI-Extraktion für Mietvertrag...")
                            rental_data = extract_rental_contract_ai(str(rental_path))
                            st.success(f"✅ Mietvertrag (AI): {rental_data.get('tenant_name', 'Name nicht gefunden')}")
                        else:
                            rental_data = extract_rental_contract(str(rental_path))
                            st.success(f"✅ Mietvertrag: {rental_data.get('name', 'Name nicht gefunden')}")
                    except Exception as e:
                        st.warning(f"⚠️ Mietvertrag konnte nicht vollständig gelesen werden: {str(e)}")
                
                # Extract bank data (optional)
                bank_data = {'payment_count': 0, 'avg_payment': 0}
                if bank_pdf:
                    bank_path = temp_dir / bank_pdf.name
                    with open(bank_path, 'wb') as f:
                        f.write(bank_pdf.getbuffer())
                    
                    try:
                        if extraction_method == "🤖 AI (OpenAI)":
                            st.info("🤖 Verwende AI-Extraktion für Kontoauszug...")
                            # Get tenant name from rental data if available
                            tenant_name = rental_data.get('tenant_name', rental_data.get('name', None))
                            bank_data = extract_bank_statement_ai(str(bank_path), tenant_name=tenant_name)
                            st.success(f"✅ Kontoauszug (AI): {bank_data['total_months']} Monate, {bank_data['total_rent_paid_eur']:.2f} €")
                        else:
                            bank_data = extract_bank_statement(str(bank_path), year)
                            st.success(f"✅ Kontoauszug: {bank_data['payment_count']} Zahlungen gefunden")
                    except Exception as e:
                        st.warning(f"⚠️ Kontoauszug konnte nicht gelesen werden: {str(e)}")
                
                # Calculate prepayment if AI mode and all data available
                ai_calculation = None
                if extraction_method == "🤖 AI (OpenAI)" and rental_pdf and bank_pdf:
                    if rental_data and bank_data and 'total_months' in bank_data:
                        ai_calculation = calculate_monthly_prepayment_from_ai(bank_data, rental_data)
                        st.success(f"🧮 Berechnung: {ai_calculation['monthly_prepayment']:.2f} € Vorauszahlung über {ai_calculation['payment_months']} Monate")
                
                st.session_state.processed_data = {
                    'weg': weg_data,
                    'rental': rental_data,
                    'bank': bank_data,
                    'year': year,
                    'extraction_method': extraction_method,
                    'ai_calculation': ai_calculation
                }
                
                st.success("✅ Extraktion abgeschlossen!")
    
        # ════════════════════════════════════════════════════════
        #  STEP 3: MANUAL INPUT & REVIEW
        # ════════════════════════════════════════════════════════
        if st.session_state.processed_data:
            st.markdown('<div class="step-header"><h2>✏️ Schritt 3: Daten eingeben & überprüfen</h2></div>', 
                        unsafe_allow_html=True)
            
            data = st.session_state.processed_data
            is_ai_mode = data.get('extraction_method') == "🤖 AI (OpenAI)"
            ai_calc = data.get('ai_calculation')
            
            # Check if we need manual input (missing PDFs)
            need_manual_input = not rental_pdf or not bank_pdf
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👤 Mieter-Information")
                
                # Tenant name - use AI extracted value or standard extraction
                if is_ai_mode:
                    default_name = data['rental'].get('tenant_name', '')
                else:
                    default_name = data['rental'].get('name', '')
                
                if need_manual_input or not default_name:
                    tenant_name = st.text_input(
                        "Name des Mieters *",
                        value=default_name,
                        key='tenant_name',
                        placeholder="Vorname Nachname",
                        help="Aus Mietvertrag extrahiert" if default_name else "Bitte eingeben"
                    )
                    
                    if not tenant_name:
                        st.error("⚠️ Mieter-Name ist erforderlich!")
                else:
                    # Show extracted name as read-only info
                    st.info(f"✅ **{default_name}**")
                    st.caption("Aus Mietvertrag extrahiert (AI)" if is_ai_mode else "Aus Mietvertrag extrahiert")
                    tenant_name = default_name
            
            with col2:
                st.subheader("💰 Zahlungsinformationen")
                
                # For AI mode with all PDFs: use calculated prepayment
                if is_ai_mode and ai_calc:
                    # Use AI-calculated values
                    monthly_prepayment = ai_calc['monthly_prepayment']
                    payment_months = ai_calc['payment_months']
                    
                    # Show as read-only info
                    st.info(f"✅ **{monthly_prepayment:.2f} €**")
                    st.caption(f"Berechnet aus Kontoauszug (AI)")
                    
                    st.info(f"✅ **{payment_months} Monate**")
                    st.caption(f"Aus Kontoauszug extrahiert (AI)")
                    
                else:
                    # Standard mode or manual input needed
                    # Monthly prepayment
                    default_prepay = data['rental'].get('nebenkosten_voraus', 0)
                    if not default_prepay:
                        default_prepay = data['rental'].get('heizkosten_voraus', 0)
                    if not default_prepay and data['bank'].get('avg_payment'):
                        default_prepay = data['bank'].get('avg_payment')
                    
                    if need_manual_input or not default_prepay:
                        monthly_prepayment = st.number_input(
                            "Monatliche Nebenkostenvorauszahlung (€) *",
                            min_value=0.0,
                            value=float(default_prepay) if default_prepay else 0.0,
                            step=10.0,
                            key='monthly_prepayment',
                            help="Aus Mietvertrag oder Kontoauszug extrahiert" if default_prepay else "Bitte eingeben"
                        )
                        
                        if monthly_prepayment == 0:
                            st.error("⚠️ Vorauszahlung ist erforderlich!")
                    else:
                        # Show extracted prepayment as read-only info
                        st.info(f"✅ **{default_prepay:.2f} €**")
                        st.caption("Aus Mietvertrag/Kontoauszug extrahiert")
                        monthly_prepayment = default_prepay
                    
                    # Payment months
                    default_months = data['bank'].get('payment_count', data['bank'].get('total_months', 12))
                    # Ensure default_months is at least 1 (when no bank data available)
                    if default_months == 0:
                        default_months = 12
                    
                    if need_manual_input or default_months == 12:
                        payment_months = st.number_input(
                            "Anzahl Monate mit Mietzahlung *",
                            min_value=1,
                            max_value=12,
                            value=default_months,
                            step=1,
                            key='payment_months',
                            help="Aus Kontoauszug extrahiert" if data['bank'].get('payment_count', data['bank'].get('total_months', 0)) > 0 else "Standard: 12 Monate"
                        )
                    else:
                        # Show extracted months as read-only info
                        st.info(f"✅ **{default_months} Monate**")
                        st.caption("Aus Kontoauszug extrahiert")
                        payment_months = default_months
            
            
            st.divider()
            
            # Calculation formula explanation
            st.info(
                f"📊 **Berechnungsformel:** "
                f"(Jahreskosten {data['weg']['total']:.2f} € / 12 Monate) × {payment_months} Monate = "
                f"{(data['weg']['total'] / 12 * payment_months):.2f} €"
            )
            
            # Cost preview
            st.subheader("💰 Extrahierte Kosten (Vorschau)")
            
            if 'costs' in data['weg']:
                # Show first 10 costs
                preview_data = [{
                    'Kostenart': cost['name'],
                    'Betrag (€)': f"{cost['amount']:.2f}"
                } for cost in data['weg']['costs'][:10]]
                
                st.dataframe(preview_data, use_container_width=True)
                st.caption(f"Zeige 10 von {len(data['weg']['costs'])} Kostenposten | Gesamt: {data['weg']['total']:.2f} €")
            
            # ════════════════════════════════════════════════════════
            #  STEP 4: GENERATE DOCUMENTS
            # ════════════════════════════════════════════════════════
            st.markdown('<div class="step-header"><h2>📄 Schritt 4: Abrechnung erstellen</h2></div>', 
                        unsafe_allow_html=True)
            
            # Validation
            can_generate = tenant_name and monthly_prepayment > 0
            
            if not tenant_name:
                st.error("❌ Bitte Mieter-Name eingeben")
            if monthly_prepayment == 0:
                st.error("❌ Bitte Vorauszahlung eingeben")
            
            if can_generate and st.button("🚀 Abrechnung generieren", type="primary", use_container_width=True):
                with st.spinner("📝 Abrechnung wird erstellt..."):
                    try:
                        # Calculate tenant costs
                        result = calculate_tenant_costs(
                            weg_costs=data['weg']['costs'],
                            payment_months=payment_months,
                            monthly_prepayment=monthly_prepayment,
                            period_start=date(year, 1, 1),
                            period_end=date(year, 12, 31)
                        )
                        
                        # Determine period dates for display
                        # Use AI bank statement period if available, otherwise use full year
                        if is_ai_mode and ai_calc and data['bank'].get('period'):
                            # Parse period string like "08 2024 - 12 2024" to dates
                            period_str = data['bank']['period']
                            try:
                                parts = period_str.split(' - ')
                                start_parts = parts[0].strip().split()
                                end_parts = parts[1].strip().split()
                                period_start = date(int(start_parts[1]), int(start_parts[0]), 1)
                                # Last day of end month
                                end_month = int(end_parts[0])
                                end_year = int(end_parts[1])
                                if end_month == 12:
                                    period_end = date(end_year, 12, 31)
                                else:
                                    period_end = date(end_year, end_month + 1, 1)
                                    from datetime import timedelta
                                    period_end = period_end - timedelta(days=1)
                            except:
                                period_start = date(year, 1, 1)
                                period_end = date(year, 12, 31)
                        else:
                            period_start = date(year, 1, 1)
                            period_end = date(year, 12, 31)
                        
                        # Generate Excel
                        output_dir = Path("data/output")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        excel_path = output_dir / f"Nebenkostenabrechnung_{tenant_name.split()[-1]}_{year}.xlsx"
                        create_nebenkostenabrechnung(
                            result,
                            tenant_name,
                            str(excel_path),
                            year,
                            period_start=period_start,
                            period_end=period_end
                        )
                        
                        # Generate PDF
                        pdf_path = excel_path.with_suffix('.pdf')
                        convert_excel_to_pdf(str(excel_path), str(pdf_path))
                        
                        # Generate email text
                        email_path = output_dir / f"Email_Text_{tenant_name.split()[-1]}_{year}.txt"
                        email_text = generate_email_text(
                            tenant_name,
                            year,
                            period_start,
                            period_end,
                            result['balance']
                        )
                        
                        with open(email_path, 'w', encoding='utf-8') as f:
                            f.write(email_text)
                        
                        # Store in session state for persistent download buttons
                        st.session_state.generated_files = {
                            'excel': excel_path,
                            'pdf': pdf_path,
                            'email': email_path
                        }
                        st.session_state.calculation_result = result
                        
                        # Success message
                        st.success("✅ Abrechnung erfolgreich erstellt!")
                        
                    except Exception as e:
                        st.error(f"❌ Fehler beim Erstellen: {str(e)}")
                        st.exception(e)
            
            # Display results and download buttons if files have been generated
            if st.session_state.generated_files:
                result = st.session_state.calculation_result
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Jahreskosten", f"{result['total_annual']:.2f} €")
                with col2:
                    st.metric(f"Für {payment_months} Monate", f"{result['total_costs']:.2f} €")
                with col3:
                    balance = result['balance']
                    label = "Nachzahlung" if balance > 0 else "Guthaben"
                    st.metric(label, f"{abs(balance):.2f} €")
                
                # Download buttons
                st.subheader("📥 Downloads")
                
                col1, col2, col3 = st.columns(3)
                
                excel_path = st.session_state.generated_files['excel']
                pdf_path = st.session_state.generated_files['pdf']
                email_path = st.session_state.generated_files['email']
                
                with col1:
                    with open(excel_path, 'rb') as f:
                        st.download_button(
                            "📊 Excel herunterladen",
                            f,
                            file_name=excel_path.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_excel"
                        )
                
                with col2:
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            "📄 PDF herunterladen",
                            f,
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            key="download_pdf"
                        )
                
                with col3:
                    with open(email_path, 'r', encoding='utf-8') as f:
                        st.download_button(
                            "📧 E-Mail-Text",
                            f.read(),
                            file_name=email_path.name,
                            mime="text/plain",
                            key="download_email"
                        )

# ════════════════════════════════════════════════════════
#  RUN APP
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
