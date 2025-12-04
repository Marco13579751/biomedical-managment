import streamlit as st
import pandas as pd
import datetime as dtm
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt

from database import *
from fuzzy_logic import setup_fuzzy_system, calculate_fuzzy_scores, calculate_all_devices_scores

def show_prioritization_score_page():
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

    """Pagina per il sistema di scoring e prioritizzazione"""
    tab1,tab2,tab3=st.tabs(["Analysis Dashboard","Add score parameters","Configure parameters"])
    
# ============================================================
# TAB3 - FUZZY CONFIGURATION (VERSIONE RIDISEGNATA)
# UI pulita: no emoji, parametri sotto grafici, update individuali
# ============================================================

    with tab3:
        # CSS to make number input controls visible
        st.markdown("""
        <style>
        /* Make number input spinners visible */
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button {
            opacity: 1;
            height: 30px;
        }
        
        /* Firefox */
        input[type=number] {
            -moz-appearance: textfield;
        }
        
        /* Ensure the input has enough width */
        div[data-testid="stNumberInput"] input {
            padding-right: 20px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Import functions
        from database import (
            get_active_fuzzy_config, 
            get_all_fuzzy_configs,
            insert_fuzzy_config,
            update_fuzzy_config,
            set_active_fuzzy_config,
            reset_to_default_fuzzy_config,
            delete_fuzzy_config,
            conn
        )
        import skfuzzy as fuzz
        import matplotlib.pyplot as plt
        
        # Helper function per evitare problemi con cursori
        def safe_get_config_by_name(config_name):
            """Recupera configurazione in modo sicuro"""
            temp_cur = conn.cursor()
            try:
                temp_cur.execute("""
                    SELECT * FROM fuzzy_config 
                    WHERE config_name = %s
                """, (config_name,))
                
                row = temp_cur.fetchone()
                if not row:
                    return None
                
                return {
                    'config_id': row[0],
                    'config_name': row[1],
                    'is_active': row[2],
                    'age': {
                        'new': [float(row[3]), float(row[4]), float(row[5]), float(row[6])],
                        'middle': [float(row[7]), float(row[8]), float(row[9]), float(row[10])],
                        'old': [float(row[11]), float(row[12]), float(row[13]), float(row[14])]
                    },
                    'downtime': {
                        'low': [float(row[15]), float(row[16]), float(row[17]), float(row[18])],
                        'middle': [float(row[19]), float(row[20]), float(row[21]), float(row[22])],
                        'high': [float(row[23]), float(row[24]), float(row[25]), float(row[26])]
                    }
                }
            except Exception as e:
                st.error(f"Error loading config: {str(e)}")
                return None
            finally:
                temp_cur.close()
        
        # ===== CONFIGURATION MANAGEMENT =====
        
        # Carica configurazione attiva
        try:
            active_config = get_active_fuzzy_config()
            all_configs = get_all_fuzzy_configs()
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            st.stop()
        
        # Row per gestione configurazioni
        col_status, col_select, col_btn1, col_btn2, col_btn3 = st.columns([2, 3, 1.2, 1.2, 1.2])
        
        with col_status:
            if active_config:
                st.success(f"Active: {active_config['config_name']}")
            else:
                st.error("No active configuration")
        
        with col_select:
            config_names = [c['config_name'] for c in all_configs]
            selected_config_name = st.selectbox(
                "Select Configuration",
                options=config_names,
                index=config_names.index(active_config['config_name']) if active_config else 0,
                key='config_selector'
            )
        
        with col_btn1:
            st.write("")
            if st.button("Load", use_container_width=True, help="Load this configuration into editor"):
                try:
                    selected_config = safe_get_config_by_name(selected_config_name)
                    if selected_config:
                        st.session_state.fuzzy_age_params = selected_config['age']
                        st.session_state.fuzzy_downtime_params = selected_config['downtime']
                        st.success(f"Loaded: {selected_config_name}")
                        st.rerun()
                    else:
                        st.error("Configuration not found!")
                except Exception as e:
                    st.error(f"Error loading: {str(e)}")
        
        with col_btn2:
            st.write("")
            if st.button("Activate", use_container_width=True, type="primary"):
                try:
                    if set_active_fuzzy_config(selected_config_name):
                        st.success(f"Activated: {selected_config_name}")
                        st.rerun()
                    else:
                        st.error("Failed to activate")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col_btn3:
            st.write("")
            if st.button("Reset", use_container_width=True):
                try:
                    if reset_to_default_fuzzy_config():
                        st.success("Reset to default")
                        st.rerun()
                    else:
                        st.error("Failed")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Show all configurations
        with st.expander("View All Configurations", expanded=False):
            for cfg in all_configs:
                status = "ACTIVE" if cfg['is_active'] else ""
                updated = cfg['updated_at'].strftime('%Y-%m-%d %H:%M') if cfg['updated_at'] else 'N/A'
                st.text(f"{status:8} {cfg['config_name']:30} Updated: {updated}")
        
        st.markdown("---")
        
        # Initialize session state
        if 'fuzzy_age_params' not in st.session_state:
            if active_config:
                st.session_state.fuzzy_age_params = active_config['age']
                st.session_state.fuzzy_downtime_params = active_config['downtime']
            else:
                st.session_state.fuzzy_age_params = {
                    'new': [0.0, 0.0, 3.0, 5.0],
                    'middle': [4.0, 5.0, 10.0, 11.0],
                    'old': [10.0, 12.0, 20.0, 20.0]
                }
                st.session_state.fuzzy_downtime_params = {
                    'low': [0.0, 0.0, 1.0, 2.0],
                    'middle': [1.0, 2.0, 3.0, 4.0],
                    'high': [3.0, 4.0, 365.0, 365.0]
                }
        
        # ===== AGE CONFIGURATION =====
        
        col_spacer1, col_graph_age, col_spacer_mid1, col_params_age = st.columns([0.2, 1.3, 0.15, 1.5])
        
        with col_graph_age:
            st.markdown("**Age Membership Functions**")
        
        with col_graph_age:
            # Age plot
            try:
                fig_age, ax_age = plt.subplots(figsize=(6.5, 4))
                
                age_universe = np.arange(0, 20, 0.1)
                
                age_new = fuzz.trapmf(age_universe, st.session_state.fuzzy_age_params['new'])
                age_middle = fuzz.trapmf(age_universe, st.session_state.fuzzy_age_params['middle'])
                age_old = fuzz.trapmf(age_universe, st.session_state.fuzzy_age_params['old'])
                
                ax_age.plot(age_universe, age_new, 'b-', linewidth=2.5, label='New')
                ax_age.plot(age_universe, age_middle, 'orange', linewidth=2.5, label='Middle')
                ax_age.plot(age_universe, age_old, 'r-', linewidth=2.5, label='Old')
                
                ax_age.fill_between(age_universe, 0, age_new, alpha=0.2, color='blue')
                ax_age.fill_between(age_universe, 0, age_middle, alpha=0.2, color='orange')
                ax_age.fill_between(age_universe, 0, age_old, alpha=0.2, color='red')
                
                ax_age.set_xlabel('Years', fontsize=9)
                ax_age.set_ylabel('Membership', fontsize=9)
                ax_age.legend(loc='upper right', fontsize=9)
                ax_age.grid(True, alpha=0.3, linestyle='--')
                ax_age.set_ylim([-0.05, 1.1])
                ax_age.tick_params(axis='both', labelsize=8)
                
                st.pyplot(fig_age)
                plt.close(fig_age)
            except Exception as e:
                st.error(f"Error plotting: {str(e)}")
        
        with col_params_age:
            # Age parameters
            st.markdown("**New Equipment**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                age_new_a = st.number_input("a", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_age_params['new'][0]), step=0.5, key='age_new_a', label_visibility="visible")
            with col_b:
                age_new_b = st.number_input("b", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_age_params['new'][1]), step=0.5, key='age_new_b', label_visibility="visible")
            with col_c:
                age_new_c = st.number_input("c", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_age_params['new'][2]), step=0.5, key='age_new_c', label_visibility="visible")
            with col_d:
                age_new_d = st.number_input("d", min_value=0.0, max_value=15.0, value=float(st.session_state.fuzzy_age_params['new'][3]), step=0.5, key='age_new_d', label_visibility="visible")
            
            st.markdown("**Middle Age**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                age_mid_a = st.number_input("a", min_value=0.0, max_value=15.0, value=float(st.session_state.fuzzy_age_params['middle'][0]), step=0.5, key='age_mid_a', label_visibility="visible")
            with col_b:
                age_mid_b = st.number_input("b", min_value=0.0, max_value=15.0, value=float(st.session_state.fuzzy_age_params['middle'][1]), step=0.5, key='age_mid_b', label_visibility="visible")
            with col_c:
                age_mid_c = st.number_input("c", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_age_params['middle'][2]), step=0.5, key='age_mid_c', label_visibility="visible")
            with col_d:
                age_mid_d = st.number_input("d", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_age_params['middle'][3]), step=0.5, key='age_mid_d', label_visibility="visible")
            
            st.markdown("**Old Equipment**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                age_old_a = st.number_input("a", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_age_params['old'][0]), step=0.5, key='age_old_a', label_visibility="visible")
            with col_b:
                age_old_b = st.number_input("b", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_age_params['old'][1]), step=0.5, key='age_old_b', label_visibility="visible")
            with col_c:
                age_old_c = st.number_input("c", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_age_params['old'][2]), step=0.5, key='age_old_c', label_visibility="visible")
            with col_d:
                age_old_d = st.number_input("d", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_age_params['old'][3]), step=0.5, key='age_old_d', label_visibility="visible")
            
            st.markdown("")
            # Update age button
            if st.button("Update Graph", type="primary", use_container_width=True, key='update_age_btn'):
                st.session_state.fuzzy_age_params = {
                    'new': [age_new_a, age_new_b, age_new_c, age_new_d],
                    'middle': [age_mid_a, age_mid_b, age_mid_c, age_mid_d],
                    'old': [age_old_a, age_old_b, age_old_c, age_old_d]
                }
                st.success("Age updated")
                st.rerun()
        
        st.markdown("---")
        
        # ===== DOWNTIME CONFIGURATION =====
        
        col_spacer3, col_graph_dt, col_spacer_mid2, col_params_dt = st.columns([0.2, 1.3, 0.15, 1.5])
        
        with col_graph_dt:
            st.markdown("**Downtime Membership Functions**")
        
        with col_graph_dt:
            # Downtime plot
            try:
                fig_dt, ax_dt = plt.subplots(figsize=(6.5, 4))
                
                downtime_universe = np.arange(0, 365, 1)
                x_limit = min(30, len(downtime_universe))
                
                dt_low = fuzz.trapmf(downtime_universe, st.session_state.fuzzy_downtime_params['low'])
                dt_middle = fuzz.trapmf(downtime_universe, st.session_state.fuzzy_downtime_params['middle'])
                dt_high = fuzz.trapmf(downtime_universe, st.session_state.fuzzy_downtime_params['high'])
                
                ax_dt.plot(downtime_universe[:x_limit], dt_low[:x_limit], 'b-', linewidth=2.5, label='Low')
                ax_dt.plot(downtime_universe[:x_limit], dt_middle[:x_limit], 'orange', linewidth=2.5, label='Middle')
                ax_dt.plot(downtime_universe[:x_limit], dt_high[:x_limit], 'r-', linewidth=2.5, label='High')
                
                ax_dt.fill_between(downtime_universe[:x_limit], 0, dt_low[:x_limit], alpha=0.2, color='blue')
                ax_dt.fill_between(downtime_universe[:x_limit], 0, dt_middle[:x_limit], alpha=0.2, color='orange')
                ax_dt.fill_between(downtime_universe[:x_limit], 0, dt_high[:x_limit], alpha=0.2, color='red')
                
                ax_dt.set_xlabel('Days', fontsize=9)
                ax_dt.set_ylabel('Membership', fontsize=9)
                ax_dt.legend(loc='upper right', fontsize=9)
                ax_dt.grid(True, alpha=0.3, linestyle='--')
                ax_dt.set_ylim([-0.05, 1.1])
                ax_dt.set_xlim([0, 30])
                ax_dt.tick_params(axis='both', labelsize=8)
                
                st.pyplot(fig_dt)
                plt.close(fig_dt)
            except Exception as e:
                st.error(f"Error plotting: {str(e)}")
        
        with col_params_dt:
            # Downtime parameters
            st.markdown("**Low Downtime**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                dt_low_a = st.number_input("a", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_downtime_params['low'][0]), step=0.5, key='dt_low_a', label_visibility="visible")
            with col_b:
                dt_low_b = st.number_input("b", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_downtime_params['low'][1]), step=0.5, key='dt_low_b', label_visibility="visible")
            with col_c:
                dt_low_c = st.number_input("c", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_downtime_params['low'][2]), step=0.5, key='dt_low_c', label_visibility="visible")
            with col_d:
                dt_low_d = st.number_input("d", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_downtime_params['low'][3]), step=0.5, key='dt_low_d', label_visibility="visible")
            
            st.markdown("**Middle Downtime**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                dt_mid_a = st.number_input("a", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_downtime_params['middle'][0]), step=0.5, key='dt_mid_a', label_visibility="visible")
            with col_b:
                dt_mid_b = st.number_input("b", min_value=0.0, max_value=10.0, value=float(st.session_state.fuzzy_downtime_params['middle'][1]), step=0.5, key='dt_mid_b', label_visibility="visible")
            with col_c:
                dt_mid_c = st.number_input("c", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_downtime_params['middle'][2]), step=0.5, key='dt_mid_c', label_visibility="visible")
            with col_d:
                dt_mid_d = st.number_input("d", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_downtime_params['middle'][3]), step=0.5, key='dt_mid_d', label_visibility="visible")
            
            st.markdown("**High Downtime**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                dt_high_a = st.number_input("a", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_downtime_params['high'][0]), step=0.5, key='dt_high_a', label_visibility="visible")
            with col_b:
                dt_high_b = st.number_input("b", min_value=0.0, max_value=20.0, value=float(st.session_state.fuzzy_downtime_params['high'][1]), step=0.5, key='dt_high_b', label_visibility="visible")
            with col_c:
                dt_high_c = st.number_input("c", min_value=0.0, max_value=365.0, value=float(st.session_state.fuzzy_downtime_params['high'][2]), step=1.0, key='dt_high_c', label_visibility="visible")
            with col_d:
                dt_high_d = st.number_input("d", min_value=0.0, max_value=365.0, value=float(st.session_state.fuzzy_downtime_params['high'][3]), step=1.0, key='dt_high_d', label_visibility="visible")
            
            st.markdown("")
            # Update downtime button
            if st.button("Update Graph", type="primary", use_container_width=True, key='update_dt_btn'):
                st.session_state.fuzzy_downtime_params = {
                    'low': [dt_low_a, dt_low_b, dt_low_c, dt_low_d],
                    'middle': [dt_mid_a, dt_mid_b, dt_mid_c, dt_mid_d],
                    'high': [dt_high_a, dt_high_b, dt_high_c, dt_high_d]
                }
                st.success("Downtime updated")
                st.rerun()
        
        st.markdown("---")
        
        # ===== SAVE CONFIGURATION =====
        st.markdown("##### Save Configuration")
        
        new_config_name = st.text_input("Configuration name:", placeholder="e.g., my_hospital_config", key='new_config_name_input')
        
        col_save1, col_save2, col_save3 = st.columns(3)
        
        with col_save1:
            if st.button("Save as New", use_container_width=True):
                if new_config_name:
                    try:
                        result = insert_fuzzy_config(
                            new_config_name,
                            st.session_state.fuzzy_age_params,
                            st.session_state.fuzzy_downtime_params
                        )
                        if result:
                            st.success(f"Saved: {new_config_name}")
                            st.rerun()
                        else:
                            st.error("Name already exists")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Enter a name first")
        
        with col_save2:
            if st.button("Update Active Config", use_container_width=True):
                if active_config and active_config['config_name'] != 'default':
                    try:
                        if update_fuzzy_config(
                            active_config['config_name'],
                            st.session_state.fuzzy_age_params,
                            st.session_state.fuzzy_downtime_params
                        ):
                            st.success(f"Updated: {active_config['config_name']}")
                            st.rerun()
                        else:
                            st.error("Update failed")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Cannot update default config")
        
        with col_save3:
            if selected_config_name != 'default' and (not active_config or selected_config_name != active_config['config_name']):
                if st.button("Delete Selected", use_container_width=True, type="secondary"):
                    try:
                        if delete_fuzzy_config(selected_config_name):
                            st.success(f"Deleted: {selected_config_name}")
                            st.rerun()
                        else:
                            st.error("Cannot delete")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # FINE TAB3 - VERSIONE RIDISEGNATA
    with tab2:
        # Get available rooms
        all_devices = get_all_devices()

        # Prima ottieni tutti i dati necessari
        rooms = get_all_rooms()
        wards = get_all_wards()

        # Crea le opzioni per i filtri
        ward_options = {"All": "All Wards"}
        ward_options.update({str(w[0]): w[1] for w in wards})

        room_options = {"All": "All Rooms"}
        room_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms})

        # FILTRI DROPDOWN
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_ward = st.selectbox(
                "Filter by Ward:",
                options=list(ward_options.keys()),
                format_func=lambda x: ward_options[x]
            )

        with col2:
            if selected_ward != "All":
                filtered_rooms = [r for r in rooms if r[3] == int(selected_ward)]
                room_filter_options = {"All": "All Rooms in Ward"}
                room_filter_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in filtered_rooms})
            else:
                room_filter_options = room_options
        
            selected_room = st.selectbox(
                "Filter by Room:",
                options=list(room_filter_options.keys()),
                format_func=lambda x: room_filter_options[x]
            )

        with col3:
            search = st.text_input("🔍 Search devices:", placeholder="Search by ID, description, brand...")

        # APPLICA I FILTRI
        filtered_devices = []

        for d in all_devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial_number, manufacturer_date, gmdn = d
    
            device_room = next((r for r in rooms if r[0] == room_id), None)
    
            if selected_ward != "All":
                if not device_room or device_room[3] != int(selected_ward):
                    continue
    
            if selected_room != "All":
                if str(room_id) != selected_room:
                    continue
    
            if search:
                search_lower = search.lower()
                room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                search_text = f"{serial_number} {description} {brand} {model} {room_info}".lower()
                if search_lower not in search_text:
                    continue
    
            filtered_devices.append(d)

        # MESSAGGIO SE NESSUN RISULTATO
        if not filtered_devices:
            st.info("No devices found with the selected filters")
            st.stop()

        device_options = {}
        for d in filtered_devices:
            device_id = d[0]
            room_id = d[2]
            description = d[3] or "No Description"
            brand = d[8] or "No Brand"
            model = d[9] or "No Model"
            serial_number=d[12] or "No Serial Number"
    

            device_room = next((r for r in rooms if r[0] == room_id), None)
            if device_room:
                ward_id = device_room[3]
                ward_info = next((w for w in wards if w[0] == ward_id), None)

                if ward_info:
                    ward_name = ward_info[1]
                    room_display = f"Floor {device_room[1]} - {device_room[2]}"
                    full_location = f"{ward_name} | {room_display}"
                else:
                    full_location = f"Floor {device_room[1]} - {device_room[2]}"
            else:
                full_location = "❌ No Location"
    
            label = f"Serial Number: {serial_number} | {description} | {brand} {model} | {full_location}"
            device_options[device_id] = label

        selected_device_id = st.selectbox(
            "Choose device to edit:",
            options=list(device_options.keys()),
            format_func=lambda x: device_options[x],
            key="device_selector"
        )

        if selected_device_id:
            with st.form("add_device_form", clear_on_submit=True):
                data_device = get_device_by_id(selected_device_id)
                existing_params = get_scores_by_device_id(selected_device_id)
                
                # *** CONTROLLO NULL - Se existing_params è None, usa valori di default ***
                if existing_params is None:
                    st.info("ℹ️ No existing scoring parameters found for this device. Setting default values.")
                
                col1, col2, col3= st.columns(3)
    
                with col1:
                    st.subheader("Age")
                    age_installation = data_device[10]
                    age_man=data_device[13]
                    oggi = dtm.date.today()
                    age_years=0
                    if age_man is not None:
                        age_years = (oggi - age_man).days / 365
                    elif age_installation is not None:
                        age_years = (oggi - age_installation).days / 365
                    etax = age_years
                    
                    # Mostra age da existing_params se esiste, altrimenti da calcolo
                    if existing_params and existing_params[3] is not None:
                        st.info(f"Age: {existing_params[3]:.1f} years")
                    elif age_years > 0:
                        st.info(f"Age (calculated): {age_years:.1f} years")
                    else:
                        st.warning("Age: Not available (no installation/manufacture date)")

                with col2:
                    st.subheader("Mission Criticality")
        
                    default_usage_type = "Analytical/Support"
                    if existing_params and len(existing_params) > 10:
                        score = existing_params[10]
                        if score == 4:
                            default_usage_type = "Life Saving/Life Support"
                        elif score == 3:
                            default_usage_type = "Therapeutic"
                        elif score == 2:
                            default_usage_type = "Diagnostic"
                        elif score == 1:
                            default_usage_type = "Analytical/Support"
        
                    usage_type_options = ["Life Saving/Life Support", "Therapeutic", "Diagnostic", "Analytical/Support"]
                    default_usage_index = usage_type_options.index(default_usage_type)
        
                    usage_type = st.selectbox(
                        "Usage Type", 
                        options=usage_type_options,
                        index=default_usage_index
                    )
        
                    if usage_type == "Life Saving/Life Support":
                        equipment_function_score = 4
                    elif usage_type == "Therapeutic":
                        equipment_function_score = 3
                    elif usage_type == "Diagnostic":
                        equipment_function_score = 2
                    elif usage_type == "Analytical/Support":
                        equipment_function_score = 1

                    downtime=calculate_downtime_hours(selected_device_id)
                    st.info(f"Breakdown: {downtime} days")

                    default_backup_option = "0 backup devices"
                    if existing_params and len(existing_params) > 5:
                        backup_val = existing_params[5]
                        if backup_val == 0:
                            default_backup_option = "0 backup devices"
                        elif backup_val == 1:
                            default_backup_option = "1-2 backup devices"
                        elif backup_val == 2:
                            default_backup_option = ">=3 backup devices"
        
                    backup_options = ["0 backup devices", "1-2 backup devices", ">=3 backup devices"]
                    default_backup_index = backup_options.index(default_backup_option)
        
                    checkbox_backup = st.selectbox(
                        "How many backup devices", 
                        options=backup_options,
                        index=default_backup_index
                    )
        
                    if checkbox_backup == "0 backup devices":
                        backup_device_available = 0
                    elif checkbox_backup == "1-2 backup devices":
                        backup_device_available = 1
                    elif checkbox_backup == ">=3 backup devices":
                        backup_device_available = 2

                    failure_rate = 0


                with col3:
                    st.subheader("Support")
        
                    default_end_of_life = False
                    default_end_of_support = False
        
                    if existing_params and len(existing_params) > 13:
                        eol_val = existing_params[13]
                        if eol_val == 1:
                            default_end_of_life = True
                        elif eol_val == 2:
                            default_end_of_support = True
        
                    service_availability = st.checkbox("Service Availability", value=default_end_of_life)
                    spare_parts_availability = st.checkbox("Spare parts availability", value=default_end_of_support)
        
                    if service_availability:
                        service_availability_numeric = 1
                    else:
                        service_availability_numeric  = 0.1

        
                    if spare_parts_availability:
                        spare_parts_availability_numeric = 1
                    else:
                        spare_parts_availability_numeric = 0.1

                 

                default_notes = ''
                if existing_params and len(existing_params) > 12:
                    default_notes = existing_params[12] if existing_params[12] is not None else ''

                notes = st.text_area(
                    "Additional notes", 
                    placeholder="Add any additional notes here...", 
                    key="notes", 
                    height=100,
                    value=str(default_notes)
                )

                submitted = st.form_submit_button("Update device parameters", type="primary")

                if submitted:
                    try:
                        assessment_date = dtm.date.today()
                        
                        # *** IMPORTANTE: Usa age_years da existing_params, NON quello calcolato! ***
                        # Se existing_params esiste, usa l'age salvato nel database
                        # Altrimenti usa quello calcolato dalle date (per dispositivi nuovi)
                        age_to_use = None
                        if existing_params and existing_params[3] is not None:
                            age_to_use = existing_params[3]
                        elif age_years > 0:
                            age_to_use = age_years
                        
                        # Ora fai delete DOPO aver salvato age_to_use
                        delete_scoring_parameters(selected_device_id)
                        
                        # Check se possiamo calcolare gli score
                        if age_to_use is None or age_to_use == 0:
                            st.warning(f"⚠️ Cannot calculate scores: Age parameter is missing for Device ID {selected_device_id}")
                            st.info("Please ensure the device has a valid installation date or manufacturer date.")
                            
                            # Update database with NULL scores
                            insert_scoring_parameters(
                                selected_device_id,
                                assessment_date,
                                service_availability_numeric,
                                spare_parts_availability_numeric,
                                backup_device_available,
                                equipment_function_score,
                                0,  # vulnerability_score
                                None,  # miss_score
                                None,  # supp_score
                                None   # criticity_score
                            )
                            st.info(f"✅ Device parameters saved with NULL scores due to missing age")
                        else:
                            setup_fuzzy_system()

                            st.write("DEBUG - Input values:")
                            st.write(f"age_years (from database): {age_to_use}")
                            st.write(f"Downtime: {downtime}")
                            st.write(f"equipment_function_score: {equipment_function_score}")
                            st.write(f"service available: {service_availability_numeric}")
                            st.write(f"spare parts available: {spare_parts_availability_numeric}")
                            st.write(f"backup_device_available: {backup_device_available}")

                            try:
                                mis_score, supp_score, crit_score = calculate_fuzzy_scores(
                                    age_to_use,                            # usa age dal database, NON quello calcolato
                                    equipment_function_score,              # eq_function                  
                                    downtime,                              # downtime
                                    service_availability_numeric,          # end_support
                                    spare_parts_availability_numeric,      # import_availability
                                    backup_device_available                # backup
                                )
                                st.write(f"DEBUG - Output values:")
                                st.write(f"mis_score: {mis_score}")
                                st.write(f"supp_score: {supp_score}")
                                st.write(f"crit_score: {crit_score}")
                            except Exception as e:
                                st.error(f"Error in calculate_fuzzy_scores: {str(e)}")
                                mis_score, supp_score, crit_score = None, None, None

                            if mis_score is not None:
                                st.info(f"Mission Score: {mis_score:.2f}")
                            else:
                                st.error("Error calculating Mission Score")

                            if supp_score is not None:
                                st.info(f"Support Score: {supp_score:.2f}")
                            else:
                                st.error("Error calculating Support Score")

                            if crit_score is not None:
                                st.info(f"Criticality Score: {crit_score:.2f}")
                            else:
                                st.error("Error calculating Criticality Score")
                            
                            # Save to database regardless of whether scores are None or not
                            insert_scoring_parameters(
                                selected_device_id,
                                assessment_date,
                                service_availability_numeric,
                                spare_parts_availability_numeric,
                                backup_device_available,
                                equipment_function_score,
                                0,  # vulnerability_score
                                mis_score,
                                supp_score,
                                crit_score
                            )
                            
                            if mis_score is not None and supp_score is not None and crit_score is not None:
                                st.success(f"✅ Device parameters successfully updated! Device ID: {selected_device_id}")
                            else:
                                st.warning(f"⚠️ Device parameters saved but some scores could not be calculated")
                                
                    except Exception as e:
                        st.error(f"❌ Error updating device: {str(e)}")

            # Conteggio dispositivi
            try:
                all_devices = get_all_devices()
                total_devices = len(all_devices)
            
                devices_ready = 0  # Dispositivi con tutti i parametri validi
                devices_missing = 0  # Dispositivi con parametri mancanti o NULL
                
                for device in all_devices:
                    device_id = device[0]
                    existing_params = get_scores_by_device_id(device_id)
                    
                    if not existing_params or len(existing_params) < 9:
                        # Nessun parametro salvato
                        devices_missing += 1
                        continue
                    
                    # Controlla se i parametri necessari sono tutti validi (non None e non 0 per age)
                    age_years = existing_params[3]
                    downtime = existing_params[4]
                    service_availability = existing_params[5]
                    spare_parts_availability = existing_params[6]
                    backup = existing_params[7]
                    eq_function = existing_params[8]
                    
                    # Age deve essere valido (non None e non 0)
                    if age_years is None or age_years == 0:
                        devices_missing += 1
                        continue
                    
                    # Altri parametri devono essere non None
                    required_params = [downtime, service_availability, spare_parts_availability, backup, eq_function]
                    if any(param is None for param in required_params):
                        devices_missing += 1
                        continue
                    
                    # Se arriviamo qui, il dispositivo ha tutti i parametri validi
                    devices_ready += 1
            
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Devices", total_devices)
                with col2:
                    st.metric("Ready for Calculation", devices_ready)
                with col3:
                    st.metric("Missing Parameters", devices_missing)
            
                st.divider()
            
                if st.button("Calculate All Scores", type="secondary", use_container_width=True):
                    if devices_ready > 0:
                        with st.spinner('Calculating scores for all devices...'):
                            calculate_all_devices_scores()
                    else:
                        st.warning("No devices found with complete parameters. Please add parameters first using the 'Add score parameters' tab.")
            
            except Exception as e:
                st.error(f"Error loading device information: {str(e)}")

    with tab1:
        
        all_devices = get_all_devices()
        rooms = get_all_rooms()
        wards = get_all_wards()

        ward_options = {"All": "All Wards"}
        ward_options.update({str(w[0]): w[1] for w in wards})

        room_options = {"All": "All Rooms"}
        room_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms})

        col1, col2, col3 = st.columns(3)

        with col1:
            selected_ward = st.selectbox(
                "Filter by Ward:",
                options=list(ward_options.keys()),
                format_func=lambda x: ward_options[x],key='c'
            )

        with col2:
            if selected_ward != "All":
                filtered_rooms = [r for r in rooms if r[3] == int(selected_ward)]
                room_filter_options = {"All": "All Rooms in Ward"}
                room_filter_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in filtered_rooms})
            else:
                room_filter_options = room_options
        
            selected_room = st.selectbox(
                "Filter by Room:",
                options=list(room_filter_options.keys()),
                format_func=lambda x: room_filter_options[x], key='d'
            )

        with col3:
            search = st.text_input("🔍 Search devices:", placeholder="Search by ID, description, brand....")

        filtered_devices = []

        for d in all_devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial_number, manufacturer_date, gmdn = d
    
            device_room = next((r for r in rooms if r[0] == room_id), None)
    
            if selected_ward != "All":
                if not device_room or device_room[3] != int(selected_ward):
                    continue
    
            if selected_room != "All":
                if str(room_id) != selected_room:
                    continue
    
            if search:
                search_lower = search.lower()
                room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                search_text = f"{serial_number} {description} {brand} {model} {room_info}".lower()
                if search_lower not in search_text:
                    continue
    
            filtered_devices.append(d)

        if not filtered_devices:
            st.info("No devices found with the selected filters")
            st.stop()

        if filtered_devices:
            if search or selected_ward != "All" or selected_room != "All":
                active_filters = []
                if selected_ward != "All":
                    active_filters.append(f"Ward: {ward_options[selected_ward]}")
                if selected_room!= "All":
                    active_filters.append(f"Room: {room_filter_options[selected_room]}")
                if search:
                    active_filters.append(f"Search: '{search}'")
        
                filter_text = " | ".join(active_filters)
                st.success(f"Showing {len(filtered_devices)} device(s) with filters: {filter_text}")
    
        tab1, tab2, tab3 = st.tabs(["Overview Table", "Score Analytics", "Financial Analysis"])

        # LOGICA UNIFICATA - Creazione dati una sola volta
        df_data = []
        valid_scores = []
        device_lookup = {}

        for d in filtered_devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial_number, manufacturer_date, gmdn = d

            device_lookup[device_id] = {
                'description': description,
                'brand': brand,
                'model': model,
                'usage_type': usage_type,
                'room_id': room_id,
                'cost_inr': cost_inr,
                'device_class': device_class,
                'serial_number': serial_number
            }

            score = get_scores_by_device_id(device_id)
            breakd=get_breakdown_by_id_last(device_id)

            # Calculate age_years
            oggi = dtm.date.today()
            age_years = None
            if manufacturer_date is not None:
                age_years = (oggi - manufacturer_date).days / 365
            elif install_date is not None:
                age_years = (oggi - install_date).days / 365

            # *** CONTROLLO NULL PRINCIPALE - Se score è None, salta i calcoli complessi ***
            if score is None:
                # Dispositivo senza scoring parameters - crea row con valori N/A
                row_data = {
                    'Description': description or 'N/A',
                    'Brand': brand or 'N/A',
                    'Model': model or 'N/A',
                    'Fuzzy Criticity': 'N/A',
                    'RPV1 Criticity': 'N/A',
                    'Mission Score': 'N/A',
                    'Support Score': 'N/A',
                    'Age (years)': f"{age_years:.1f}" if age_years is not None else 'N/A',
                    'Usage Types': 'N/A',
                    'Current downtime (days)': 'N/A',
                    'Type of service': breakd[14] if breakd and breakd[14] is not None else 'N/A',
                    'Service supoprt': 'N/A',
                    'Spare parts availability': 'N/A',
                    'Backup Available': 'N/A',
                    'Ward': ward_options.get(str(next((r[3] for r in rooms if r[0] == room_id), None)), 'N/A') if room_id else 'N/A',
                    'Room': room_options.get(str(room_id), 'N/A') if room_id else 'N/A'
                }
                df_data.append(row_data)
                continue  # Skip to next device

            # *** SE ARRIVIAMO QUI, score NON è None ***
            back = 'N/A'
            if score[7] is not None:
                if score[7] == 2:
                    back = ">=3"
                elif score[7] == 1:
                    back = "1-2"
                elif score[7] == 0:
                    back = "0"
    
            life = 'N/A'

    
            parts = 'N/A'
            if score[6] is not None:
                if score[6] == 0:
                    parts = "No"
                elif score[6] == 1:
                    parts = "Yes"

            eq1='N/A'
            if score[8] is not None:
                if score[8]==1:
                    eq1="Analytical/Support"
                elif score[8]==2:
                    eq1="Diagnostic"
                elif score[8]==3:
                    eq1="Therapeutic"
                elif score[8]==4:
                    eq1="Life Saving/Life Support"
            
            # Calculate RPV only if all required values are not None
            rpv = None
            if score[4] is not None and score[3] is not None and score[8] is not None and score[5] is not None:
                x2 = 1 if score[4] > 3 else 0
                x1 = 1 if score[3] > 10 else 0
                x3 = int(score[8])
                x4 = 0 if score[5] == 1 else 1
                rpv = 9*(x1+x2) + 7.5*x3 + 25*x4

            # Aggiungi a valid_scores se ha score record (anche con NULL)
            # Questo serve per le altre analisi (operational, financial)
            valid_scores.append((device_id, score, age_years, cost_inr))

            row_data = {
                'Description': description or 'N/A',
                'Brand': brand or 'N/A',
                'Model': model or 'N/A',
                'Serial number': serial_number or 'N/A',
                'Fuzzy Criticity': round(score[12], 2) if score[12] is not None else 'N/A',
                'RPV1 Criticity': rpv if rpv is not None else 'N/A',
                'Mission Score': round(score[10], 2) if score[10] is not None else 'N/A',
                'Support Score': round(score[11], 2) if score[11] is not None else 'N/A',
                'Age (years)': f"{score[3]:.1f}" if score[3] is not None else 'N/A',
                'Usage Types': eq1 or "N/A",
                'Current downtime (days)': round(score[4], 1) if score[4] is not None else 'N/A',
                'Type of service': breakd[14] if breakd and breakd[14] is not None else 'N/A',
                'Service supoprt': 'Yes' if score[5] == 1 else 'No' if score[5] is not None else 'N/A',
                'Spare parts availability': 'Yes' if score[6] == 1 else 'No' if score[6] is not None else 'N/A',
                'Backup Available': back,
                'Ward': ward_options.get(str(next((r[3] for r in rooms if r[0] == room_id), None)), 'N/A') if room_id else 'N/A',
                'Room': room_options.get(str(room_id), 'N/A') if room_id else 'N/A'
            }

            df_data.append(row_data)


        with tab1:
            try:
                cur.execute("SELECT COUNT(*) FROM scoring_parameters")
                scoring_count = cur.fetchone()[0]

                if scoring_count > 0:
                    

                    # Ora crea le colonne - il CSS si applicherà alle metriche
                    col1, col2 = st.columns(2)

                    with col1:
                        high_risk_count = 0
                        for d in filtered_devices:
                            device_id = d[0]
                            score = get_scores_by_device_id(device_id)
                            if score and score[12] is not None and score[12] > 6:
                                high_risk_count += 1
    
                        st.metric("High Risk Devices", value=high_risk_count,
                                   delta="⚠️ Need Action" if high_risk_count > 0 else "✅ All Good",delta_color="inverse")

                    with col2:
                        # Conta solo dispositivi con score effettivamente calcolati (criticity_score non NULL)
                        analyzed_devices = 0
                        for d in filtered_devices:
                            device_id = d[0]
                            score = get_scores_by_device_id(device_id)
                            if score and score[12] is not None:  # criticity_score non NULL
                                analyzed_devices += 1
                        
                        total_devices = len(filtered_devices)
                        coverage = (analyzed_devices / total_devices) * 100 if total_devices > 0 else 0
                        st.metric("Analysis Coverage", f"{coverage:.1f}%", 
                                    delta=f"{analyzed_devices}/{total_devices} devices")

                else:
                    st.warning("⚠️ No fuzzy logic results found. Run analysis in 'Scoring Assessment' page first.")

            except Exception as e:
                st.error(f"Error checking scoring data: {e}")
                
            df = pd.DataFrame(df_data)
            # Converti i valori numerici da string a float per il coloring
            # Helper function per conversione sicura a float
            def safe_float(val):
                """Converte in float solo se possibile, altrimenti ritorna None"""
                if val == 'N/A' or val is None:
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            styled_df = df.style.map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if safe_float(val) is not None and safe_float(val) >= 8 else
                    'background-color: #fff2e6' if safe_float(val) is not None and safe_float(val) >= 6 else
                    'background-color: #fffff0' if safe_float(val) is not None and safe_float(val) >= 4 else
                    'background-color: #f0fff0' if safe_float(val) is not None and safe_float(val) >= 2 else
                    'background-color: #e6ffe6' if safe_float(val) is not None and safe_float(val) >= 0 else
                    ''  # Per 'N/A'
                ),
                subset=['Fuzzy Criticity']
            ).map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if safe_float(val) is not None and safe_float(val) >= 50 else
                    'background-color: #fff2e6' if safe_float(val) is not None and safe_float(val) >= 40 else
                    'background-color: #fffff0' if safe_float(val) is not None and safe_float(val) >= 30 else
                    'background-color: #e6ffe6' if safe_float(val) is not None and safe_float(val) >= 0 else
                    ''  # Per 'N/A'
                ),
                subset=['RPV1 Criticity']
            ).map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if safe_float(val) is not None and safe_float(val) >= 20 else
                    'background-color: #fffff0' if safe_float(val) is not None and safe_float(val) >= 10 else
                    'background-color: #e6ffe6' if safe_float(val) is not None and safe_float(val) >= 0 else
                    ''  # Per 'N/A'
                ),
                subset=['Mission Score']
            ).map(
                lambda val: (
                    'background-color: #e6ffe6' if safe_float(val) is not None and safe_float(val) >= 6.5 else
                    'background-color: #fffff0' if safe_float(val) is not None and safe_float(val) >= 3.5 else
                    'background-color: #ffe6e6; color: #cc0000' if safe_float(val) is not None and safe_float(val) >= 0 else
                    ''  # Per 'N/A'
                ),
                subset=['Support Score']
            ).map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if safe_float(val) is not None and safe_float(val) >= 10 else      
                    'background-color: #fffff0' if safe_float(val) is not None and safe_float(val) >= 5 else
                    'background-color: #e6ffe6' if safe_float(val) is not None and safe_float(val) >= 0 else
                    ''  # Per 'N/A'
                ),
                subset=['Age (years)']
            ).map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if val != 'N/A' and val == 'End of Support' else                
                    'background-color: #fffff0' if val != 'N/A' and val == 'End of Life' else
                    'background-color: #e6ffe6' if val != 'N/A' and val == '0' else
                    ''  # Per 'N/A'
                ),
                subset=['Usage Types']
            ).map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if safe_float(val) is not None and safe_float(val) > 3 else      
                    'background-color: #fffff0' if safe_float(val) is not None and safe_float(val) > 1 else
                    'background-color: #e6ffe6' if safe_float(val) is not None and safe_float(val) >= 0 else
                    ''  # Per 'N/A'
                ),
                subset=['Current downtime (days)']
            ).map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if val != 'N/A' and val == '0' else                
                    'background-color: #f0fff0' if val != 'N/A' and val == '1-2' else
                    'background-color: #e6ffe6' if val != 'N/A' and val == '>=3' else
                    ''  # Per 'N/A'
                ),
                subset=['Backup Available']
            ).map(
                lambda val: (
                    'background-color: #ffe6e6; color: #cc0000' if val != 'N/A' and val == 'Imported and NO avalability of spare parts' else                
                    'background-color: #fffff0' if val != 'N/A' and val == 'Local production and NO avalability of spare parts' else
                    'background-color: #f0fff0' if val != 'N/A' and val == 'Imported and avalability of spare parts' else
                    'background-color: #e6ffe6' if val != 'N/A' and val == 'Local production and avalability of spare parts' else
                    ''  # Per 'N/A'
                ),
            )


            st.dataframe(styled_df, hide_index=True, width="stretch")


            # Crea un buffer in memoria
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Device Analysis')
            buffer.seek(0)
            
            st.download_button(
                label="📥 Export to Excel",
                data=buffer.getvalue(),
                file_name=f"device_analysis_{dtm.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with tab2:
            if valid_scores:
                col1, col2, col3 = st.columns(3)

                criticities = []
                mission_scores = []
                support_scores = []
        
                for d in filtered_devices:
                    device_id = d[0]
                    score = get_scores_by_device_id(device_id)
                    if score:
                        if score[12] is not None:
                            criticities.append(score[12])
                        if score[10] is not None:
                            mission_scores.append(score[10])
                        if score[11] is not None:
                            support_scores.append(score[11])

                with col1:
                    if criticities:
                        avg_criticality = sum(criticities) / len(criticities)
                        st.metric("Average Criticity", f"{avg_criticality:.2f}")
                    else:
                        st.metric("Average Criticity", "N/A")

                with col2:
                    if mission_scores:
                        avg_mission = sum(mission_scores) / len(mission_scores)
                        st.metric("Average Mission Score", f"{avg_mission:.2f}")
                    else:
                        st.metric("Average Mission Score", "N/A")

                with col3:
                    if support_scores:
                        avg_support = sum(support_scores) / len(support_scores)
                        st.metric("Average Support Score", f"{avg_support:.2f}")
                    else:
                        st.metric("Average Support Score", "N/A")
                st.divider()
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
    
                    criticities = []
                    for d in filtered_devices:
                        device_id = d[0]
                        score = get_scores_by_device_id(device_id)
                        if score and score[12] is not None:
                            criticities.append(score[12])
    
                    if criticities:
                        criticity_ranges = {
                            "Very Low (0-2)": sum(1 for c in criticities if 0 <= c <= 2),
                            "Low (2-4)": sum(1 for c in criticities if 2 <= c <= 4),
                            "Medium (4-6)": sum(1 for c in criticities if 4 < c <= 6),
                            "High (6-8)": sum(1 for c in criticities if 6 < c <= 8),
                            "Very High (8-10)": sum(1 for c in criticities if 8 < c <= 10)
                        }
        
                        # Rimuovi categorie con valore 0 per il grafico a torta
                        criticity_ranges = {k: v for k, v in criticity_ranges.items() if v > 0}
        
                        fig = go.Figure(data=[
                            go.Pie(
                                labels=list(criticity_ranges.keys()),
                                values=list(criticity_ranges.values()),
                                marker_colors=['#1a9641','#a6d96a', '#ffffbf', '#fdae61', '#d7191c'][:len(criticity_ranges)],
                                textinfo='label+value+percent',
                                textposition='auto',
                                hovertemplate='<b>%{label}</b><br>Devices: %{value}<br>Percentage: %{percent}<extra></extra>'
                            )
                        ])
        
                        fig.update_layout(
                            title="Criticity Distribution",
                            height=400,
                            showlegend=True,
                            legend=dict(
                                orientation="v",
                                yanchor="middle",
                                y=0.5,
                                xanchor="left",
                                x=1.01
                            )
                        )
        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No criticity data available")

                with chart_col2:
                    st.write("**High & Very High Risk Devices**")
                    high_risk_devices = []
            
                    for d in filtered_devices:
                        device_id = d[0]
                        score = get_scores_by_device_id(device_id)
                        roomname=get_room_name_by_device(device_id)
                        wardname=get_ward_name_by_device(device_id)
                        if score and score[12] is not None and score[12] > 6.0:
                            device_info = device_lookup.get(device_id, {})
                            device_name = device_info.get('description', 'Unknown Device')
                    
                            high_risk_devices.append({
                                'Device description': device_name,
                                'Serial Number': device_info.get('serial_number','N/A'),
                                'Criticity': round(score[12], 2),                              
                                'Location': f"{roomname} - {wardname}"
                            })

                    if high_risk_devices:
                        risk_df = pd.DataFrame(high_risk_devices)

                        def highlight_criticity(val):
                            if val == "N/A":
                                return ''
                            try:
                                v = float(val)
                            except:
                                return ''
                            if v >= 8:
                                return 'background-color: #ffe6e6; color: #cc0000'  # rosso
                            elif v >= 6:
                                return 'background-color: #fff2e6'  # arancio
                            elif v >= 4:
                                return 'background-color: #fffff0'  # giallo
                            elif v >= 2:
                                return 'background-color: #f0fff0'  # verde chiaro
                            elif v >= 0:
                                return 'background-color: #e6ffe6'  # verde scuro
                            return ''
                        
                        styled_df = risk_df.style.map(highlight_criticity, subset=['Criticity'])
                        
                        st.dataframe(styled_df, hide_index=True, use_container_width=True)
                        st.warning(f"⚠️ {len(high_risk_devices)} devices require attention!")

                    else:
                        st.success("✅ No high-risk devices found!")


                
            st.divider()

            def categorize_device_by_type(description):
                if not description:
                    return 'Other'

                desc_lower = description.lower()

                if any(keyword in desc_lower for keyword in ['monitor', 'monitoring', 'display', 'screen']):
                    return 'Monitor'
                elif any(keyword in desc_lower for keyword in ['ecg', 'ekg', 'electrocardiogram', 'cardiac']):
                    return 'ECG'
                elif any(keyword in desc_lower for keyword in ['ventilator', 'ventilation', 'breathing', 'respiratory']):
                    return 'Ventilator'
                elif any(keyword in desc_lower for keyword in ['light', 'lamp', 'illumination', 'surgical light', 'ot light', 'operating']):
                    return 'OT Light'
                elif any(keyword in desc_lower for keyword in ['pump', 'infusion', 'syringe']):
                    return 'Pump'
                elif any(keyword in desc_lower for keyword in ['ultrasound', 'echo', 'doppler']):
                    return 'Ultrasound'
                elif any(keyword in desc_lower for keyword in ['xray', 'x-ray', 'radiograph']):
                    return 'X-Ray'
                elif any(keyword in desc_lower for keyword in ['defibrillator', 'defib']):
                    return 'Defibrillator'
                else:
                    return 'Other'


            # INIZIALIZZA LE VARIABILI
            detailed_device_data = {}
            device_data = {}

            # Raccogli dati dettagliati per dispositivo
            for d in filtered_devices:
                device_id = d[0]
                description = d[3] or 'Unknown'
                brand = d[8] or 'N/A'
                model = d[9] or 'N/A'
                serial_number=d[12] or 'N/A'
                score = get_scores_by_device_id(device_id)

                device_type = categorize_device_by_type(description)

                if device_type not in device_data:
                    device_data[device_type] = {
                        'total': 0, 'very_low': 0, 'low': 0,
                        'medium': 0, 'high': 0, 'very_high': 0
                    }
                    detailed_device_data[device_type] = {
                        'very_low': [], 'low': [], 'medium': [], 'high': [], 'very_high': []
                    }

                device_data[device_type]['total'] += 1

                if score and score[12] is not None:
                    roomname = get_room_name_by_device(device_id)
                    wardname = get_ward_name_by_device(device_id)
                    criticity_score = score[12]
                    device_info = {
                        'id': device_id,
                        'description': description,
                        'serial number': serial_number,
                        'brand': brand,
                        'room': roomname,
                        'ward': wardname,
                        'model': model,
                        'criticity': round(criticity_score, 2)
                    }

                    if 0 <= criticity_score <= 2:
                        device_data[device_type]['very_low'] += 1
                        detailed_device_data[device_type]['very_low'].append(device_info)
                    elif 2 < criticity_score <= 4:
                        device_data[device_type]['low'] += 1
                        detailed_device_data[device_type]['low'].append(device_info)
                    elif 4 < criticity_score <= 6:
                        device_data[device_type]['medium'] += 1
                        detailed_device_data[device_type]['medium'].append(device_info)
                    elif 6 < criticity_score <= 8:
                        device_data[device_type]['high'] += 1
                        detailed_device_data[device_type]['high'].append(device_info)
                    elif 8 < criticity_score <= 10:
                        device_data[device_type]['very_high'] += 1
                        detailed_device_data[device_type]['very_high'].append(device_info)


            # VISUALIZZAZIONE
            if device_data:
                risk_levels = ['very_high', 'high', 'medium', 'low', 'very_low']
                risk_names = {
                    'very_high': 'Very High Risk (8-10)',
                    'high': 'High Risk (6-8)',
                    'medium': 'Medium Risk (4-6)',
                    'low': 'Low Risk (2-4)',
                    'very_low': 'Very Low Risk (0-2)'
                }
                colors = {
                    'very_high': '#d7191c',   # rosso intenso
                    'high': '#fdae61',        # arancio
                    'medium': "#ffffbf",      # giallo chiaro
                    'low': '#a6d96a',         # verde chiaro
                    'very_low': '#1a9641'     # verde scuro
                }

                device_types = list(device_data.keys())

                fig = go.Figure()

                for risk_level in risk_levels:
                    # Prepara hover con lista dispositivi
                    hover_texts = []
                    for dt in device_types:
                        devices = detailed_device_data[dt][risk_level]
                        if devices:
                            details = "<br>".join([f"- {dev['description']} ({dev['brand']} {dev['model']})"
                                                for dev in devices[:5]])  # max 5 per non fare muro di testo
                            if len(devices) > 5:
                                details += f"<br>...and {len(devices)-5} more"
                            hover_texts.append(details)
                        else:
                            hover_texts.append("No devices")

                    fig.add_trace(go.Bar(
                        name=risk_names[risk_level],
                        y=device_types,
                        x=[device_data[dt][risk_level] for dt in device_types],
                        orientation='h',
                        marker_color=colors[risk_level],
                        text=[device_data[dt][risk_level] if device_data[dt][risk_level] > 0 else '' for dt in device_types],
                        textposition="inside",
                        hovertext=hover_texts,
                        hoverinfo="text+x+name"
                    ))

                fig.update_layout(
                    title="Criticity Analysis by Device Type",
                    barmode='stack',
                    height=600,
                    yaxis=dict(title="Device Type", automargin=True),
                    xaxis=dict(title="Number of Devices"),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    ),
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )

                st.plotly_chart(fig, use_container_width=True)

                # --- Dettagli con selectbox
                st.write("### Explore Device Details")

                col1, col2 = st.columns(2)
                with col1:
                    selected_type = st.selectbox(
                        "Select Device Type:",
                        options=list(device_data.keys()),
                        key="device_type_select_chart1"
                    )

                with col2:
                    selected_risk = st.selectbox(
                        "Select Risk Level:",
                        options=risk_levels,
                        format_func=lambda x: risk_names[x],
                        key="risk_level_select_chart1"
                    )

                if selected_type and selected_risk:
                    devices = detailed_device_data[selected_type][selected_risk]
                    if selected_type and selected_risk:
                        devices = detailed_device_data[selected_type][selected_risk]
                        if devices:
                            st.write(f"**{risk_names[selected_risk]} {selected_type} Devices ({len(devices)} total):**")
                            
                        
                            
                            df_details = pd.DataFrame([
                                {
                                    'Serial number': dev['serial number'],  # Potrebbe essere 'serial_number' o 'udi_number'?
                                    'Description': dev['description'],
                                    'Brand': dev['brand'],
                                    'Model': dev['model'],
                                    'Location': f"{dev['room']} - {dev['ward']}",
                                    'Criticity Score': dev['criticity']
                                }
                                for dev in devices
                            ])
                            st.dataframe(df_details, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"No {selected_type} devices in {risk_names[selected_risk]} category")

                else:
                    st.info("No device data available for risk analysis")
            else:
                st.warning("No scoring data available. Please run fuzzy logic analysis first.")


        with tab3:
            if valid_scores:
                costs = []
                maintenance_costs = []
                cost_ratio = []
        
                for d in filtered_devices:
                    device_id = d[0]
                    cost_inr = d[6]
                    score = get_scores_by_device_id(device_id)
            
                    if score and cost_inr is not None:
                        costs.append(cost_inr)
                        if score[8] is not None:
                            maintenance_costs.append(score[8])
                            cost_ratio.append(score[8])

                fin_col1, fin_col2, fin_col3 = st.columns(3)

                with fin_col1:
                    total_value = sum(costs) if costs else 0
                    st.metric("Total Asset Value", f"₹{total_value:,.0f}")

                with fin_col2:
                    avg_cost = sum(costs) / len(costs) if costs else 0
                    st.metric("Avg Device Value", f"₹{avg_cost:,.0f}")

                with fin_col3:
                    if cost_ratio:
                        devices_above_15 = sum(1 for u in cost_ratio if u > 15)
                        st.metric("High Maintenance Ratio Devices", f"{devices_above_15}", 
                                    delta="⚠️ More than usual" if devices_above_15 > 0 else "✅ All Good")
                    else:
                        st.metric("High Maintenance Ratio Devices", "N/A")

                fin_chart1, fin_chart2 = st.columns(2)
                with fin_chart1:
                    class_costs = {}
                    for d in filtered_devices:
                        ward_name = get_ward_name_by_device(d[0])
                        cost = d[6] or 0

                        if ward_name in class_costs:
                            class_costs[ward_name] += cost
                        else:
                            class_costs[ward_name] = cost

                    if class_costs:
                        fig = px.pie(
                            values=list(class_costs.values()), 
                            names=list(class_costs.keys()),
                            title="Asset Value by Ward"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                with fin_chart2:
                    if costs and maintenance_costs and len(costs) == len(maintenance_costs):
                        maintenance_array = np.array(maintenance_costs)
                        costs_array = np.array(costs)

                        ratios = np.divide(maintenance_array, costs_array, out=np.zeros_like(maintenance_array), where=costs_array!=0)
                        scatter_df = pd.DataFrame({
                            'Asset Value': costs,
                            'Maintenance Cost %': ratios*100,
                            'Device ID': [d[0] for d in filtered_devices if d[6] is not None and get_scores_by_device_id(d[0]) and get_scores_by_device_id(d[0])[8] is not None]
                        })

                        fig = px.scatter(scatter_df, x='Asset Value', y='Maintenance Cost %',
                                        hover_data=['Device ID'],
                                        title="Maintenance Cost Ratio vs Asset Value")
                        st.plotly_chart(fig, use_container_width=True)


            else:
                st.warning("No financial data available for analysis.")

        if not filtered_devices:
            st.info("No devices match the current filters. Please adjust your search criteria.")
    



def show_admin_panel():
    st.markdown("""
    <style>
    /* Cambia solo la linea sotto il tab attivo */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #3b82f6 !important;
    }
    
    /* Opzionale: cambia colore testo tab attivo */
    .stTabs [aria-selected="true"] {
        color: #3b82f6 !important;
    }
    </style>
""", unsafe_allow_html=True)

    """Pagina di amministrazione"""
    st.title("Administration Panel")
    
    if st.session_state["user"] != "andreolimarco01@gmail.com":
        st.error("❌ Access denied. Admin privileges required.")
        st.info("Please contact the system administrator for access.")
        st.stop()
    
    # User management
    st.subheader("User Management")
    utenti = get_all_users()
    
    if utenti:
        st.write(f"**Total registered users:** {len(utenti)}")
        
        for u in utenti:
            email, approved = u
            col1, col2 = st.columns([3,1])
            
            with col1:
                status_icon = "✅" if approved else "❌"
                status_text = "Approved" if approved else "Pending approval"
                st.write(f"{status_icon} **{email}** - {status_text}")
            
            with col2:
                if not approved:
                    if st.button("✅ Approve", key=f"approve_{email}"):
                        approve_user(email)
                        st.success(f"{email} approved ✅")
                        st.rerun()
    else:
        st.info("No registered users found.")
    
    # Database management
    st.subheader("Database Management")
    
    device_count = len(get_all_devices())
    st.metric("Total Devices", device_count)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Delete All Devices", type="secondary"):
            if st.checkbox("I understand this will delete all device data"):
                cur.execute("DELETE FROM dispositivi")
                conn.commit()
                st.success("All devices deleted from database")
                st.rerun()
