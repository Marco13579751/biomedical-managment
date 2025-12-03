"""
cybersecurity.py
Pagina per la gestione delle vulnerabilità CVE dei dispositivi medici
"""

import streamlit as st
import pandas as pd
import subprocess
import json
import os
from datetime import datetime
import plotly.graph_objects as go
from database import (
    get_all_devices, get_all_software, get_software_by_device,
    insert_software, update_software, delete_software,
    get_all_cves, get_cves_by_software, insert_cve, delete_cve,
    get_device_vulnerability_summary, get_software_with_cve_count,
    delete_all_cves_for_software, get_device_by_id, get_software_by_id
)

def show_cybersecurity_page():
    st.markdown("""
    <style>
    /* ========== TEMA OSPEDALIERO MODERNO ========== */
    
    /* Container principale più compatto */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Header e titoli più compatti */
    .stMarkdown h1 {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-bottom: 0.5rem !important;
        padding: 16px 24px !important;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border-left: 5px solid #0ea5e9 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
    }
    
    .stMarkdown h2, .stMarkdown h3 {
        color: #334155 !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Tabs stile ospedaliero moderno */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px !important;
        background: #f1f5f9 !important;
        border-radius: 12px !important;
        padding: 6px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #64748b !important;
        background: transparent !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 12px 20px !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.8) !important;
        color: #1e40af !important;
        transform: translateY(-1px) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #1e40af !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-2px) !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        background: transparent !important;
    }
    
    /* Filtri compatti e moderni */
    .stSelectbox > div > div > div {
        font-size: 14px !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        background: white !important;
        transition: all 0.2s ease !important;
    }
    
    .stSelectbox > div > div > div:hover {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    .stSelectbox > div > div > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Input search moderno */
    .stTextInput > div > div > input {
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        background: white !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #9ca3af !important;
        font-style: italic !important;
    }
    
    /* Tabelle ultra compatte stile medical software */
    .stDataFrame {
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        font-size: 12px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
        background: white !important;
    }
    
    .stDataFrame thead tr th {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        padding: 12px 10px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        border: none !important;
        border-bottom: 2px solid #0ea5e9 !important;
    }
    
    .stDataFrame tbody tr td {
        padding: 8px 10px !important;
        border-bottom: 1px solid #f1f5f9 !important;
        font-size: 11px !important;
        line-height: 1.3 !important;
        vertical-align: middle !important;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: #f8fafc !important;
        transform: scale(1.002) !important;
        transition: all 0.2s ease !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #fafbfc !important;
    }
    
    /* Colonne più responsive */
    .element-container .stColumns {
        gap: 16px !important;
    }
    
    .element-container .stColumns > div {
        background: white !important;
        border-radius: 8px !important;
        padding: 16px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
        border: 1px solid #f1f5f9 !important;
    }
    
    /* Form elements più compatti */
    .stForm {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
        margin: 16px 0 !important;
    }
    
    .stForm > div {
        gap: 16px !important;
    }
    
    /* Submit buttons moderni */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    .stFormSubmitButton > button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Buttons normali */
    .stButton > button {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border: 1px solid #d1d5db !important;
        color: #374151 !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        border-color: #9ca3af !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%) !important;
        box-shadow: 0 6px 16px rgba(220, 38, 38, 0.3) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
    }
    
    /* Alert messaggi più moderni */
    .element-container .stAlert {
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
    }
    
    .element-container .stAlert[data-baseweb="notification"] {
        margin: 8px 0 !important;
    }
    
    /* Success messages */
    .stSuccess {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important;
        color: #166534 !important;
        border-left: 4px solid #22c55e !important;
    }
    
    /* Error messages */
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%) !important;
        color: #991b1b !important;
        border-left: 4px solid #ef4444 !important;
    }
    
    /* Info messages */
    .stInfo {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
        color: #1e40af !important;
        border-left: 4px solid #3b82f6 !important;
    }
    
    /* Warning messages */
    .stWarning {
        background: linear-gradient(135deg, #fffbeb 0%, #fed7aa 100%) !important;
        color: #92400e !important;
        border-left: 4px solid #f59e0b !important;
    }
    
    /* Sidebar styling (se necessario) */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
    }
    
    /* Metrics compatti */
    .metric-value {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #1e40af !important;
        line-height: 1 !important;
    }
    
    .metric-label {
        font-size: 12px !important;
        color: #64748b !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Nascondere elementi Streamlit non necessari */
    .css-10trblm {
        margin-top: -80px !important;
    }
    
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    
    /* Custom medical cards */
    .medical-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        border-left: 4px solid #3b82f6;
    }
    
    .medical-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        border-left-color: #1e40af;
    }
    
    .device-id-badge {
        background: #1e40af;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Status indicators */
    .status-active {
        background: linear-gradient(135deg, #dcfce7, #bbf7d0);
        color: #166534;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid #22c55e;
    }
    
    .status-inactive {
        background: linear-gradient(135deg, #fef2f2, #fecaca);
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid #ef4444;
    }
    
    /* Loading e placeholder migliorati */
    .stSpinner > div {
        border-color: #3b82f6 !important;
        border-top-color: transparent !important;
    }
    
    /* Data editor styling */
    .stDataEditor {
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    /* Plotly charts styling - SENZA effetto rialzato */
    .js-plotly-plot {
        border-radius: 0px !important;
        box-shadow: none !important;
    }

    /* Colonne SENZA effetto rialzato */
    .element-container .stColumns > div {
        background: transparent !important;
        border-radius: 0px !important;
        padding: 0px !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .stDataFrame {
            font-size: 10px !important;
        }
        
        .stDataFrame thead tr th {
            padding: 8px 6px !important;
            font-size: 10px !important;
        }
        
        .stDataFrame tbody tr td {
            padding: 6px 6px !important;
            font-size: 10px !important;
        }
        
        .element-container .stColumns {
            gap: 8px !important;
        }
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Tabs principali
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dashboard", 
        "Search Vulnerabilities", 
        "Edit CVE",
        "Delete Software/Firmware/CVE",
        "All CVE"
     
    ])
    
    with tab1:
        show_dashboard()
    
    with tab2:
        show_vulnerability_search()
    
    with tab4:
        show_delete_page()
    
    with tab5:
        show_all_cves()

    with tab3:
        show_edit_page()

def show_dashboard():
    """Dashboard con riepilogo vulnerabilità"""

    
    # Recupera dati
    summary = get_device_vulnerability_summary()
    all_cves = get_all_cves()
    
    # Metriche generali
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_devices_with_vuln = len(set([s[0] for s in summary if s[10] > 0]))
        st.metric("Devices with Vulnerabilities", total_devices_with_vuln)
    
    with col2:
        total_cves = len(all_cves)
        st.metric("Total CVEs", total_cves)
    
    with col3:
        critical_total = sum([s[13] or 0 for s in summary])
        st.metric("Critical CVEs", int(critical_total), delta="CVSS ≥ 9.0", delta_color="inverse")
    
    with col4:
        max_cvss = max([s[11] for s in summary if s[11] is not None], default=0)
        st.metric("Max CVSS", f"{max_cvss:.1f}" if max_cvss else "N/A")
    
    st.markdown("---")
    
    # Tabella dispositivi più critici
    st.subheader("Most Critical Devices")
    
    if summary:
        critical_devices = [s for s in summary if s[10] > 0]
        
        if critical_devices:
            df_critical = pd.DataFrame(critical_devices, columns=[
                'Device ID', 'Device Name', 'Brand', 'Device Model', 'Software ID',
                'Vendor', 'Product', 'Version', 'Software Model', 'IP',
                'Total CVE', 'Max CVSS', 'Avg CVSS', 'Critical', 'High', 'Medium', 'Low'
            ])
            
            df_critical = df_critical.sort_values(['Max CVSS', 'Critical', 'High'], 
                                                   ascending=[False, False, False])
            
            display_cols = ['Device Name', 'Brand', 'Product', 'Version', 
                           'Total CVE', 'Max CVSS', 'Critical', 'High', 'Medium', 'Low']
            
            st.dataframe(
                df_critical[display_cols].head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("✅ No deviced with vulnerabilities found")
    else:
        st.info("🔭 No available data. Add a software and start the research.")
    
    # Grafico distribuzione severità
    if all_cves:

        
        cvss_scores = [c[3] for c in all_cves if c[3] is not None]
        
    if cvss_scores:
        critical = sum(1 for s in cvss_scores if s >= 9.0)
        high = sum(1 for s in cvss_scores if 7.0 <= s < 9.0)
        medium = sum(1 for s in cvss_scores if 4.0 <= s < 7.0)
        low = sum(1 for s in cvss_scores if s < 4.0)
        
        severity_data = pd.DataFrame({
            'Severity': ['Critical', 'High', 'Medium', 'Low'],
            'Count': [critical, high, medium, low],
            'Color': ['#d32f2f', '#f57c00', '#fbc02d', '#388e3c']
        })
        
        fig = go.Figure(data=[
            go.Bar(
                x=severity_data['Count'],
                y=severity_data['Severity'],
                orientation='h',
                marker=dict(color=severity_data['Color'])
            )
        ])
        
        fig.update_layout(
            title="Distribution of CVEs by Severity",
            yaxis=dict(
                showticklabels=False  # Nascondi i tick originali
            ),
            xaxis_title="Number of Vulnerabilities",
            showlegend=False,
            height=300,
            margin=dict(l=100)  # Spazio a sinistra per le label
        )
        
        # Aggiungi le label colorate come annotazioni
        for i, row in severity_data.iterrows():
            fig.add_annotation(
                x=-0.5,  # Posizione a sinistra del grafico
                y=row['Severity'],
                text=f"<b>{row['Severity']}</b>",
                showarrow=False,
                font=dict(color=row['Color'], size=14),
                xref='x',
                yref='y',
                xanchor='right'
            )
        
        st.plotly_chart(fig, use_container_width=True)

def show_vulnerability_search():
    """Search for vulnerabilities using vuln_lookup_real.py"""
    
    st.info("""
    💡 **How it works:**
    1. Select a device 
    2. Fill out the text boxes and click on "Add software and search CVE"
    3. Results will be automatically saved to the database
    4. Clicking on "Search CVE" in the last section you can look for the CVE of a software/firmware again 
    """)
    
    # Device selection
    devices = get_all_devices()
    
    if not devices:
        st.warning("⚠️ No devices available. Add at least one device first.")
        return
    
    device_options = {d[0]: f"{d[3]} - {d[8]} - {d[9]} - {d[12]}" for d in devices}
    selected_device_id = st.selectbox(
        "Select Device",
        options=list(device_options.keys()),
        format_func=lambda x: device_options[x]
    )
    
    if selected_device_id:
        
        # Form to add new software
        st.markdown("### Add new Software/Firmware and search vulnerabilities")
        
        with st.form("add_software_search"):
            col1, col2 = st.columns(2)
            
            with col1:
                vendor = st.text_input("Vendor", placeholder="e.g.: Microsoft, Siemens")
                product = st.text_input("Product *", placeholder="e.g.: Windows, SIMATIC")
                version = st.text_input("Version", placeholder="e.g.: 10.0.19041, 5.2")
            
            with col2:
                model = None
                ip = st.text_input("IP Address", placeholder="e.g.: 192.168.1.100")
            
            submitted = st.form_submit_button("Add Software and Search CVE")
            
            if submitted:
                if not product:
                    st.error("Product field is required!")
                else:
                    try:
                        # Insert software
                        software_id = insert_software(
                            device_id=selected_device_id,
                            vendor=vendor or None,
                            product=product,
                            version=version or None,
                            model=model or None,
                            ip=ip or None
                        )
                        
                        st.success(f"✅ Software/Firmware added")
                    
                        # Prepare data for search
                        sw_data = (software_id, selected_device_id, vendor, product, version, model, ip)
                        st.session_state.search_software = sw_data
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        # Show existing software for this device
        existing_software = get_software_by_device(selected_device_id)
        
        st.markdown("### Device Software/Firmware")
        
        if existing_software:
            for sw in existing_software:
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    device = get_device_by_id(sw[1])
                    st.write(f"**{sw[2] or 'N/A'}** - {sw[3]} v{sw[4] or 'N/A'} (Device's serial number: {device[12] or 'N/A'})")
                     
                with col2:
                    if st.button("Search CVE", key=f"search_{sw[0]}"):
                        st.session_state.search_software = sw
                        st.rerun()  # ✅ Forza il rerun per eseguire la ricerca
        else:
            st.info("No Software/Firmware registered for this device")
        
        st.markdown("---")
        
        # ✅ ESEGUI LA RICERCA SE È STATA RICHIESTA
        if 'search_software' in st.session_state and st.session_state.search_software:
            search_vulnerabilities_for_software(st.session_state.search_software)
            st.session_state.search_software = None  # Reset dopo la ricerca
def search_vulnerabilities_for_software(software_tuple):


    """
    Cerca vulnerabilità per un software specifico - VERSIONE SEMPLIFICATA
    Usa direttamente i risultati già processati da vuln_lookup_real.py
    """
    software_id, device_id, vendor, product, version, model, ip = software_tuple
    
    
    # Prepara comando per vuln_lookup_real.py
    cmd = ["python", "vuln_lookup_real.py"]
    
    if vendor:
        cmd.extend(["--vendor", vendor])
    cmd.extend(["--product", product])
    if version:
        cmd.extend(["--version", version])
    
    json_file = "vuln_results.json"
    
    # Rimuovi vecchio file se esiste
    if os.path.exists(json_file):
        try:
            os.remove(json_file)
        except:
            pass
    
    try:
        # Esegui script
        with st.spinner("Interrogazione database CVE..."):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90
            )
        
        if result.returncode == 0:
            # Leggi JSON generato
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # ✅ PRENDI DIRETTAMENTE I RISULTATI GIÀ PROCESSATI
                if 'results' in data and data['results']:
                    result_data = data['results'][0]
                    
                    # Estrai dati già calcolati da vuln_lookup_real.py
                    cve_ids = result_data.get('cve_ids', [])
                    cvss_scores = result_data.get('cvss_scores', [])
                    cve_descriptions= result_data.get('cve_descriptions',[])
                    top_cvss = result_data.get('top_cvss')
                    avg_cvss = result_data.get('avg_cvss')
                    critical_count = result_data.get('critical_count', 0)
                    high_count = result_data.get('high_count', 0)
                    medium_count = result_data.get('medium_count', 0)
                    low_count = result_data.get('low_count', 0)
                    cve_count = result_data.get('cve_count', len(cve_ids))
                                      
                    
                    # ✅ SALVA NEL DATABASE (senza riprocessare)
                    delete_all_cves_for_software(software_id)
                    
                    inserted_count = 0
                    skipped_count = 0
                    
                    for idx, cve_code in enumerate(cve_ids):
                        cvss = cvss_scores[idx] if idx < len(cvss_scores) else None
                        descriptions = cve_descriptions[idx] if idx < len(cve_descriptions) else None
                        
                        try:
                            insert_cve(software_id, cve_code, cvss, descriptions)
                            inserted_count += 1
                        except Exception as e:
                            skipped_count += 1
                            st.warning(f"⚠️ Errore inserimento {cve_code}: {str(e)}")
                    
                    # ✅ MOSTRA STATISTICHE (già calcolate)
                    st.success(f"{inserted_count} CVE salvati nel database")
                    
                    if skipped_count > 0:
                        st.warning(f"⚠️ {skipped_count} CVE saltati (già esistenti o errore)")
                    
                    
                    
                    # Warning se nessuna versione
                    if not version:
                        st.warning(
                            "⚠️ Nessuna versione specificata: i risultati potrebbero "
                            "includere falsi positivi. Raccomandazione: specifica la "
                            "versione del software."
                        )
                
                else:
                    st.warning("⚠️ Nessuna vulnerabilità trovata")
                
                # Elimina file temporaneo
                try:
                    os.remove(json_file)
                except:
                    pass
            
            else:
                st.error("❌ File dei risultati non generato")
                st.code(result.stdout)
        
        else:
            st.error(f"Errore nell'esecuzione dello script:")
            st.code(result.stderr)
    
    except subprocess.TimeoutExpired:
        st.error("⏱️ Timeout: la ricerca ha impiegato troppo tempo (>90s)")
    except FileNotFoundError:
        st.error("❌ Script vuln_lookup_real.py non trovato nella directory corrente")
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def show_delete_page():

    """Pagina per eliminare software e CVE"""
    
    tab1, tab2 = st.tabs(["Delete Software/Firmware", "Delete CVE"])
    
    # ========== TAB 1: Elimina Software ==========
    with tab1:
        
        all_software = get_all_software()
        all_devices = get_all_devices()
        
        if not all_software:
            st.warning("No software available")
        else:
            # Estrai valori unici per i filtri
            products = sorted(set([sw[3] for sw in all_software if sw[3]]))
            versions = sorted(set([sw[4] for sw in all_software if sw[4]]))
            
            # FILTRI DROPDOWN
            col1, col2, col3 = st.columns(3)
            
            with col1:
                product_options = {"All": "All Products"}
                product_options.update({p: p for p in products})
                
                selected_product = st.selectbox(
                    "Filter by Product:",
                    options=list(product_options.keys()),
                    format_func=lambda x: product_options[x],
                    key='product_filter'
                )
            
            with col2:
                version_options = {"All": "All Versions"}
                version_options.update({v: v for v in versions})
                
                selected_version = st.selectbox(
                    "Filter by Version:",
                    options=list(version_options.keys()),
                    format_func=lambda x: version_options[x],
                    key='version_filter'
                )
            
            with col3:
                search_device = st.text_input(
                    "🔍 Search Device:", 
                    placeholder="Search by description, brand, serial...",
                    key="search_device_delete"
                )
            
            # APPLICA I FILTRI
            filtered_software = []
            
            for sw in all_software:
                software_id, device_id, vendor, product, version, model, ip = sw
                
                # Filtro Product
                if selected_product != "All":
                    if product != selected_product:
                        continue
                
                # Filtro Version
                if selected_version != "All":
                    if version != selected_version:
                        continue
                
                # Filtro Device
                if search_device:
                    device = get_device_by_id(device_id)
                    if device:
                        search_lower = search_device.lower()
                        device_description = (device[3] or "").lower()
                        device_brand = (device[8] or "").lower()
                        device_model = (device[9] or "").lower()
                        serial_number = (device[12] or "").lower()
                        
                        search_text = f"{device_description} {device_brand} {device_model} {serial_number}"
                        if search_lower not in search_text:
                            continue
                    else:
                        continue
                
                filtered_software.append(sw)
            
            if not filtered_software:
                st.info("No software found with the selected filters")
            else:
                # Crea dizionario per selectbox
                software_options = {}
                for sw in filtered_software:
                    software_id, device_id, vendor, product, version, model, ip = sw
                    
                    device = get_device_by_id(device_id)
                    if device:
                        device_name = device[3] or "No Description"
                        device_brand = device[8] or "N/A"
                        device_model = device[9] or "N/A"
                        serial_number = device[12] or "N/A"
                        device_info = f"{device_name} | {device_brand} {device_model} | Serial number: {serial_number}"
                    else:
                        device_info = f"Device ID:{device_id}"
                    
                    label = f"{vendor or 'N/A'} {product} v{version or 'N/A'} | {device_info}"
                    software_options[software_id] = label
                
                selected_software = st.selectbox(
                    "Choose software to delete:",
                    options=list(software_options.keys()),
                    format_func=lambda x: software_options[x],
                    key="software_selector"
                )
                
                if selected_software:
                    # Mostra info software selezionato
                    cves = get_cves_by_software(selected_software)
                    st.warning(f"⚠️ This software has **{len(cves)} CVE(s)** that will be deleted")
                    
                    if st.button("Delete Selected Software", type="primary"):
                        try:
                            delete_software(selected_software)
                            st.success(f"✅ Software {selected_software} deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting software: {str(e)}")
    
    # ========== TAB 2: Elimina CVE specifico da TUTTI i software ==========
    with tab2:
      
        
        all_cves = get_all_cves()
        
        if not all_cves:
            st.warning("No CVE available")
        else:
            # Raggruppa CVE per codice (stesso CVE può essere su più software)
            cve_dict = {}
            for cve in all_cves:
                cve_id, software_id, cve_code, cvss, description = cve
                
                if cve_code not in cve_dict:
                    cve_dict[cve_code] = {
                        'ids': [],
                        'cvss': cvss,
                        'description': description,
                        'software_ids': []
                    }
                
                cve_dict[cve_code]['ids'].append(cve_id)
                cve_dict[cve_code]['software_ids'].append(software_id)
                
                # Aggiorna CVSS se presente e migliore
                if cvss and (not cve_dict[cve_code]['cvss'] or cvss > cve_dict[cve_code]['cvss']):
                    cve_dict[cve_code]['cvss'] = cvss
                
                # Aggiorna descrizione se più lunga
                if description and len(description) > len(cve_dict[cve_code]['description'] or ''):
                    cve_dict[cve_code]['description'] = description
            
            # FILTRI DROPDOWN
            
            search_cve = st.text_input(
                    "🔍 Search CVE:", 
                    placeholder="CVE-2024-...",
                    key="search_cve_delete"
                )
            
            
            # APPLICA I FILTRI
            filtered_cve_codes = []
            
            for cve_code, info in cve_dict.items():
                # Filtro CVE code
                if search_cve:
                    if search_cve.upper() not in cve_code.upper():
                        continue
                
                
                filtered_cve_codes.append(cve_code)
            
            else:
                # Crea dizionario per selectbox
                cve_options = {}
                for cve_code in sorted(filtered_cve_codes):
                    info = cve_dict[cve_code]
                    count = len(info['ids'])
                    cvss = info['cvss']
                    
                    cvss_str = f"CVSS:{cvss:.1f}" if cvss else "No CVSS"
                    label = f"{cve_code} | {cvss_str} | Found in {count} software"
                    cve_options[cve_code] = label
                
                selected_cve_code = st.selectbox(
                    "Choose CVE to delete:",
                    options=list(cve_options.keys()),
                    format_func=lambda x: cve_options[x],
                    key="cve_selector"
                )
                
                if selected_cve_code:
                    info = cve_dict[selected_cve_code]
                    count = len(info['ids'])
                    
                    # Mostra software affetti
                    st.warning(f"⚠️ This CVE is present in **{count} software**. All occurrences will be deleted.")
                    
                    
                    if st.button("Delete CVE from ALL software", type="primary"):
                        try:
                            deleted_count = 0
                            for cve_id in info['ids']:
                                delete_cve(cve_id)
                                deleted_count += 1
                            
                            st.success(f"✅ {selected_cve_code} deleted from {deleted_count} software!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting CVE: {str(e)}")

def show_edit_page():
    """Pagina per editare software"""
    
    all_software = get_all_software()
    
    if not all_software:
        st.warning("No software available")
        return
    
    # Estrai valori unici per i filtri
    products = sorted(set([sw[3] for sw in all_software if sw[3]]))
    versions = sorted(set([sw[4] for sw in all_software if sw[4]]))
    
    # FILTRI DROPDOWN
    col1, col2, col3 = st.columns(3)
    
    with col1:
        product_options = {"All": "All Products"}
        product_options.update({p: p for p in products})
        
        selected_product = st.selectbox(
            "Filter by Product:",
            options=list(product_options.keys()),
            format_func=lambda x: product_options[x],
            key='product_filter_edit'
        )
    
    with col2:
        version_options = {"All": "All Versions"}
        version_options.update({v: v for v in versions})
        
        selected_version = st.selectbox(
            "Filter by Version:",
            options=list(version_options.keys()),
            format_func=lambda x: version_options[x],
            key='version_filter_edit'
        )
    
    with col3:
        search_device = st.text_input(
            "🔍 Search Device:", 
            placeholder="Search by description, brand, serial...",
            key="search_device_edit"
        )
    
    # APPLICA I FILTRI
    filtered_software = []
    
    for sw in all_software:
        software_id, device_id, vendor, product, version, model, ip = sw
        
        # Filtro Product
        if selected_product != "All":
            if product != selected_product:
                continue
        
        # Filtro Version
        if selected_version != "All":
            if version != selected_version:
                continue
        
        # Filtro Device
        if search_device:
            device = get_device_by_id(device_id)
            if device:
                search_lower = search_device.lower()
                device_description = (device[3] or "").lower()
                device_brand = (device[8] or "").lower()
                device_model = (device[9] or "").lower()
                serial_number = (device[12] or "").lower()
                
                search_text = f"{device_description} {device_brand} {device_model} {serial_number}"
                if search_lower not in search_text:
                    continue
            else:
                continue
        
        filtered_software.append(sw)
    
    if not filtered_software:
        st.info("No software found with the selected filters")
        return
    
    # Crea dizionario per selectbox
    software_options = {}
    for sw in filtered_software:
        software_id, device_id, vendor, product, version, model, ip = sw
        
        device = get_device_by_id(device_id)
        if device:
            device_name = device[3] or "No Description"
            device_brand = device[8] or "N/A"
            device_model = device[9] or "N/A"
            serial_number = device[12] or "N/A"
            device_info = f"{device_name} | {device_brand} {device_model} | S/N:{serial_number}"
        else:
            device_info = f"Device ID:{device_id}"
        
        label = f"{vendor or 'N/A'} {product} v{version or 'N/A'} | {device_info}"
        software_options[software_id] = label
    
    selected_software = st.selectbox(
        "Choose software to edit:",
        options=list(software_options.keys()),
        format_func=lambda x: software_options[x],
        key="software_selector_edit"
    )
    
    if selected_software:
        # Recupera dati software selezionato
        software_data = get_software_by_id(selected_software)
        
        if software_data:
            software_id, device_id, vendor, product, version, model, ip = software_data
            
        
            
            # Mostra device associato (non editabile)
            device = get_device_by_id(device_id)
            
            # Form di modifica
            with st.form("edit_software_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_vendor = st.text_input(
                        "Vendor", 
                        value=vendor or "",
                        placeholder="e.g.: Microsoft, Siemens"
                    )
                    new_product = st.text_input(
                        "Product *", 
                        value=product or "",
                        placeholder="e.g.: Windows, SIMATIC"
                    )
                    new_version = st.text_input(
                        "Version", 
                        value=version or "",
                        placeholder="e.g.: 10.0.19041, 5.2"
                    )
                
                with col2:
                   
                    
                    new_ip = st.text_input(
                        "IP Address", 
                        value=ip or "",
                        placeholder="e.g.: 192.168.1.100"
                    )
                
                # Mostra CVE associati (info)
                cves = get_cves_by_software(selected_software)
                new_model = "g"
                if cves:
                    st.info(f"This software has {len(cves)} associated CVE(s)")
                
                col_btn1, col_btn2 = st.columns([1, 3])
                
                with col_btn1:
                    submitted = st.form_submit_button("Save & Search CVE", type="primary")
                
                with col_btn2:
                    st.write("")  # Spacing
                
                if submitted:
                    if not new_product:
                        st.error("❌ Product field is required!")
                    else:
                        try:
                            # Verifica se ci sono stati cambiamenti
                            has_changes = (
                                new_vendor != (vendor or "") or
                                new_product != (product or "") or
                                new_version != (version or "") or
                                new_model != (model or "") or
                                new_ip != (ip or "")
                            )
                            
                            if not has_changes:
                                st.warning("⚠️ No changes detected")
                            else:
                                # Aggiorna software
                                update_software(
                                    software_id=selected_software,
                                    vendor=new_vendor or None,
                                    product=new_product,
                                    version=new_version or None,
                                    model=new_model or None,
                                    ip=new_ip or None
                                )
                                
                                st.success("✅ Software updated successfully!")
                                
                                # Prepara dati per la ricerca
                                sw_data = (
                                    selected_software,
                                    device_id,
                                    new_vendor or None,
                                    new_product,
                                    new_version or None,
                                    new_model or None,
                                    new_ip or None
                                )
                                
                                # Salva in session_state per evitare problemi con form
                                st.session_state.search_after_edit = sw_data
                                st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error updating software: {str(e)}")
            
            # Esegui ricerca CVE se richiesto (fuori dal form)
            if 'search_after_edit' in st.session_state:
                sw_data = st.session_state.search_after_edit
                del st.session_state.search_after_edit
                
                search_vulnerabilities_for_software(sw_data)

def show_all_cves():
    """Mostra tutti i CVE in una tabella con info complete"""
    
    all_cves = get_all_cves()
    
    if not all_cves:
        st.info("📭 No CVE in the database")
        return
    
    # Filtri
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_cve = st.text_input("🔍 Search CVE", placeholder="CVE-2024-...")
    
    with col2:
        search_software = st.text_input("🔍 Search Software", placeholder="vendor, product, version...")
    
    with col3:
        search_device = st.text_input("🔍 Search Device", placeholder="brand, model, serial...")
    
    with col4:
        show_only_with_cve = st.checkbox("Show only software with CVE", value=False)
    
    # Crea DataFrame con info aggiuntive - SEMPRE tutti i CVE
    rows = []
    
    for cve in all_cves:
        cve_id, software_id, cve_code, cvss, cve_description = cve
        
        # Ottieni info software
        software = get_software_by_id(software_id)
        if software:
            vendor = software[2] or 'N/A'
            product = software[3] or 'N/A'
            software_version = software[4] or 'N/A'
            device_id = software[1]
            
            # Ottieni info dispositivo
            device = get_device_by_id(device_id)
            if device:
                device_description = device[3] or 'N/A'
                device_brand = device[8] or 'N/A'
                device_model = device[9] or 'N/A'
                serial_number = device[12] or 'N/A'
            else:
                device_description = 'N/A'
                device_brand = 'N/A'
                device_model = 'N/A'
                serial_number = 'N/A'
        else:
            vendor = 'N/A'
            product = 'N/A'
            software_version = 'N/A'
            device_description = 'N/A'
            device_brand = 'N/A'
            device_model = 'N/A'
            serial_number = 'N/A'
        
        rows.append({
            'CVE': cve_code,
            'CVSS': cvss,
            'CVE Description': cve_description or 'N/A',
            'Vendor': vendor,
            'Product': product,
            'Software Version': software_version,
            'Device Description': device_description,
            'Device Brand': device_brand,
            'Device Model': device_model,
            'Serial Number': serial_number,
            'Software ID': software_id
        })
    
    # Se checkbox NON selezionata, aggiungi anche software SENZA CVE
    if not show_only_with_cve:
        all_software = get_all_software()
        software_ids_with_cve = set(r['Software ID'] for r in rows)
        
        for software in all_software:
            software_id, device_id, vendor, product, version, model, ip = software
            
            # Salta se questo software ha già CVE (già presente in rows)
            if software_id in software_ids_with_cve:
                continue
            
            # Ottieni info dispositivo
            device = get_device_by_id(device_id)
            if device:
                device_description = device[3] or 'N/A'
                device_brand = device[8] or 'N/A'
                device_model = device[9] or 'N/A'
                serial_number = device[12] or 'N/A'
            else:
                device_description = 'N/A'
                device_brand = 'N/A'
                device_model = 'N/A'
                serial_number = 'N/A'
            
            rows.append({
                'CVE': "No CVE",
                'CVSS': None,
                'CVE Description': "No vulnerabilities",
                'Vendor': vendor or 'N/A',
                'Product': product or 'N/A',
                'Software Version': version or 'N/A',
                'Device Description': device_description,
                'Device Brand': device_brand,
                'Device Model': device_model,
                'Serial Number': serial_number,
                'Software ID': software_id
            })
    
    # Applica filtri CVE
    if search_cve:
        search_cve_lower = search_cve.lower()
        rows = [r for r in rows if search_cve_lower in (r['CVE'] or '').lower()]
    
    # Applica filtri software
    if search_software:
        search_soft_lower = search_software.lower()
        rows = [
            r for r in rows 
            if (search_soft_lower in (r['Vendor'] or '').lower() or 
                search_soft_lower in (r['Product'] or '').lower() or
                search_soft_lower in (r['Software Version'] or '').lower())
        ]
    
    # Applica filtri device
    if search_device:
        search_dev_lower = search_device.lower()
        rows = [
            r for r in rows 
            if (search_dev_lower in (r['Device Description'] or '').lower() or 
                search_dev_lower in (r['Device Brand'] or '').lower() or
                search_dev_lower in (r['Device Model'] or '').lower() or
                search_dev_lower in (r['Serial Number'] or '').lower())
        ]
    
    st.write(f"**Found {len(rows)} records**")
    
    if rows:
        df = pd.DataFrame(rows)
        
        # Aggiungi colonna severità
        def get_severity(cvss):
            if cvss is None:
                return "UNKNOWN"
            elif cvss >= 9.0:
                return "🔴 CRITICAL"
            elif cvss >= 7.0:
                return "🟠 HIGH"
            elif cvss >= 4.0:
                return "🟡 MEDIUM"
            else:
                return "🟢 LOW"
        
        df['Severity'] = df['CVSS'].apply(get_severity)
        
        # Mostra tabella
        st.dataframe(
            df[[
                'CVE', 'CVSS', 'Severity', 'CVE Description',
                'Vendor', 'Product', 'Software Version',
                'Device Description', 'Device Brand', 'Device Model', 'Serial Number'
            ]].sort_values('CVSS', ascending=False),
            use_container_width=True,
            hide_index=True
        )