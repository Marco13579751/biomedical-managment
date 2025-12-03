
from math import floor
import streamlit as st
import numpy as np
import pandas as pd
import datetime as dt  # Cambiato qui per evitare conflitti
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.express as px
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
import altair as alt
from streamlit_elements import elements, nivo
from streamlit_elements import elements, mui


from database import *
from fuzzy_logic import setup_fuzzy_system, calculate_fuzzy_scores, calculate_all_devices_scores

def show_wards_rooms_page():
     # CSS MODERNO PER INTERFACCIA OSPEDALIERA - SOLO GRAFICA
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
    
    /* Plotly charts styling */
    .js-plotly-plot {
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* Container spacing ottimizzato */
    .element-container {
        margin-bottom: 12px !important;
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

    """Pagina per la gestione di Ward e Room"""
    tab1, tab2, tab3, tab4 = st.tabs(["Add Room", "Remove Room", "Add Ward", "Remove Ward"])
    
    with tab3:
        wards=get_all_wards()
        ward_options = {f"{r[0]}": f"Ward {r[1]}" for r in wards}

        with st.form("Add Ward",clear_on_submit=True):
            ward_name = st.text_input("Ward Name", placeholder="e.g., Intensive Care Unit")
            st.markdown("""
    <style>
    /* Pulsante con gradiente blu coordinato con sidebar */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #1e3a8a, #3b82f6) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #1e40af, #2563eb) !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    .stFormSubmitButton > button:active {
        background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
        transform: translateY(0px) !important;
    }
    </style>
""", unsafe_allow_html=True)
            submitted = st.form_submit_button("Add Ward")
        
            if submitted:
                if not ward_name:
                    st.error("Please fill in the ward.")
                else:
                    ward_id = insert_ward(ward_name)
                    if ward_id:
                        st.success(f"Ward '{ward_name}' added successfully!")
                        wards = get_all_wards()
                        ward_options = {f"{r[0]}": f"Ward {r[1]}" for r in wards}
                    else:
                        st.error(f"Failed to add ward '{ward_name}'. It may already exist.")

        if not wards:
            st.error("No wards found! Please add wards first.")
            st.stop()

        df_data = []
        for d in wards:
            ward_id, ward_name= d
            df_data.append({
                'Ward': ward_name or 'N/A',
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True,hide_index=True)

    with tab4:
        
            ward_id = st.selectbox("Ward", options=list(ward_options.keys()), 
                                     format_func=lambda x: ward_options[x])
            submitted = st.button("Delete Ward", type="primary")
        
            if submitted: 
                cur.execute("SELECT COUNT(*) FROM room WHERE ward_id = %s", (ward_id,))
                room_count = cur.fetchone()[0]
    
                if room_count > 0:
                    st.error(f"Remove all the rooms of the ward first({room_count} rooms found)")
                else:
                    if delete_wards(ward_id):
                        st.success("Ward removed successfully!")
                        ward_options = {f"{r[0]}": f"{r[1]}" for r in wards}
                        log_action(1, 'DELETE WARD', ward_options.get(str(ward_id), 'N/A'), ward_id)
                        st.rerun()
                    else:
                        st.error("Failed to remove ward. Please try again.")

    with tab1:
        ward_options = {f"{r[0]}": f"Ward {r[1]}" for r in wards}

        with st.form("add_room_form", clear_on_submit=True):
            st.subheader("Room Information")
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                ward_id = st.selectbox("Ward", options=list(ward_options.keys()), 
                                     format_func=lambda x: ward_options[x])
        
            with col2:
                room_name = st.text_input("Room Name*", placeholder="e.g., ICU-101")

            with col3:
                floor_number = st.number_input("Floor Number*", min_value=0, step=1, placeholder="e.g., 1")
                if floor_number is None:
                    floor_number=0
        
            submitted = st.form_submit_button("Add Room")
        
            if submitted:
                if not room_name or floor_number is None:
                    st.error("Please fill in all required fields.")
                else:
                    success = insert_room(floor_number, room_name, ward_id)
                    if success:
                        st.success(f"Room '{room_name}' added successfully!")
                    else:
                        st.error(f"Failed to add room '{room_name}'. It may already exist.")

        rooms=get_all_rooms()

        df_data = []
        for t in rooms:
            room_id, floor_id, room_name, ward_id= t
            ward_options = {f"{r[0]}": f"{r[1]}" for r in wards}
            df_data.append({
                'Room name': room_name or 'N/A',
                'Floor number': floor_id or 'N/A',
                'Ward': ward_options.get(str(ward_id), ward_id or 'N/A'),
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        ward_id = st.selectbox("Ward", options=list(ward_options.keys()), 
                               format_func=lambda x: ward_options[x], key="remove_ward_select")

        cur.execute("SELECT room_id, room_name FROM room WHERE ward_id = %s", (ward_id,))
        rooms = cur.fetchall()
        room_options = {r[0]: r[1] for r in rooms}

        if room_options:
            room_id = st.selectbox(
                "Room",
                options=list(room_options.keys()),
                format_func=lambda x: room_options[x],
                key="remove_room_select"
            )
    
           
            submitted = st.button("Delete Room", type="primary")

            if submitted: 
                cur.execute("SELECT COUNT(*) FROM medical_device WHERE room_id = %s", (room_id,))
                device_count = cur.fetchone()[0]
    
                if device_count > 0:
                    st.error(f"Remove all the devices of the room first ({device_count} devices found)")
                else:
                    if delete_room(room_id):
                        st.success("Room removed successfully!")
                    else:
                        st.error("Failed to remove room. Please try again.")
        else:
            st.warning("Nessuna room disponibile per questo ward")
            with st.form("Remove Room Disabled", clear_on_submit=True):
                st.form_submit_button("Remove Room", disabled=True)

def show_devices_page():
   
    # CSS MODERNO PER INTERFACCIA OSPEDALIERA - SOLO GRAFICA
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
    """Pagina per la gestione dei dispositivi medici"""
    
    tab1, tab2, tab3, tab4= st.tabs(["View medical devices", "Add medical devices", "Edit medical devices", "Delete medical device"])

# ============================================
# TAB 2 - ADD MEDICAL DEVICE (COMPLETO)
# ============================================

# TAB 2 - ADD MEDICAL DEVICE (MODIFICATO)

# ============================================
# TAB 2 - ADD MEDICAL DEVICE (COMPLETO)
# ============================================

# ============================================
# TAB 2 - ADD MEDICAL DEVICE
# ============================================

    with tab2:
        # Get available rooms
        rooms = get_all_rooms()
        if not rooms:
            st.error("No rooms found! Please add rooms in the Admin Panel first.")
            st.stop()
        
        room_options = {f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms}

        with st.form("add_device_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
        
            with col1:
                description = st.text_input("Description*", placeholder="e.g., Ventilator Model X")
                model = st.text_input("Model*", placeholder="e.g., V60")
                brand = st.text_input("Brand*", placeholder="e.g., Philips")
        
            with col2:
                cost_inr = st.number_input("Cost (INR)*", min_value=0.0, step=1000.0, value=100000.0)
                room_id = st.selectbox("Room*", options=list(room_options.keys()), 
                                    format_func=lambda x: room_options[x])
            
            with col3:
                installation_date = st.date_input(
                    "Installation Date", 
                    value=None,  
                    min_value=dt.date(2000, 1, 1),
                    help="Leave empty if unknown"
                )
                manufacturer_date = st.date_input(
                    "Manufacturer Date", 
                    value=None, 
                    min_value=dt.date(2000, 1, 1),
                    help="Leave empty if unknown"
                )
                
            col4, col5 = st.columns(2)
            
            with col4:
                serial_number = st.text_input("Serial Number", placeholder="Serial number")
                instrument_code = st.text_input("Instrument Code", placeholder="e.g., AMTZ/ARC/EQP/...")
                
            with col5:
                udi_number = st.text_input("UDI Number", placeholder="Unique Device Identifier")
                gmdn = st.text_input("GMDN", placeholder="Global Medical Device Nomenclature")
                
            st.markdown("""
    <style>
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #1e3a8a, #3b82f6) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3) !important;
    }

    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #1e40af, #2563eb) !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-1px) !important;
    }

    .stFormSubmitButton > button:active {
        background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
        transform: translateY(0px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
            submitted = st.form_submit_button("Add Device to Database", type="primary")
        
            if submitted:
                if description and room_id and brand and model:
                    try:
                        device_id = insert_medical_device(
                            description, room_id, "Class B", None, cost_inr,
                            brand, model, installation_date, serial_number, manufacturer_date, udi_number, gmdn
                        )
                        st.success(f"✅ Device successfully added! Device ID: {device_id}")
                        
                    except Exception as e:
                        st.error(f"❌ Error adding device: {str(e)}")
                else:
                    st.error("❌ Please fill all required fields marked with *")


    # ============================================
    # TAB 3 - EDIT MEDICAL DEVICE
    # ============================================

    with tab3:
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

        filtered_devices = []

        for d in all_devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial, manufacturer_date, gmdn = d

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
        
                search_text = f"{device_id} {description} {brand} {model} {room_info}".lower()
                if search_lower not in search_text:
                    continue

            filtered_devices.append(d)

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
            serial_number= d[12] or "No Serial Number"


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
            device_data = get_device_by_id(selected_device_id)
            if device_data:
                Device_ID, Parent_ID, Room_ID, Description, Class, Usage_Type, Cost_INR, Present, Brand, Model, Installation_Date, UDI_Number, serial_number, manufacturer_date, gmdn = device_data

                st.subheader(f"Edit Device")
                rooms = get_all_rooms()
                room_options = {f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms}

                with st.form("edit_device_form"):
                    col1, col2, col3 = st.columns(3)
        
                    with col1:
                        description = st.text_input("Description*", 
                                                value=Description or "", 
                                                placeholder="e.g., Ventilator Model X")
                        model = st.text_input("Model*", 
                                            value=Model or "", 
                                            placeholder="e.g., V60")
                        brand = st.text_input("Brand*", 
                                            value=Brand or "", 
                                            placeholder="e.g., Philips")
        
                    with col2:
                        cost_inr = st.number_input("Cost (INR)*", 
                                                min_value=0.0, 
                                                step=1000.0, 
                                                value=float(Cost_INR) if Cost_INR else 100000.0)
                        
                        room_keys = list(room_options.keys())
                        current_room_index = 0
                        if str(Room_ID) in room_keys:
                            current_room_index = room_keys.index(str(Room_ID))
                    
                        room_id = st.selectbox("Room*", 
                                            options=room_keys,
                                            index=current_room_index,
                                            format_func=lambda x: room_options[x])
        
                    with col3:
                        if Installation_Date:
                            if isinstance(Installation_Date, str):
                                installation_date_value = dt.datetime.strptime(Installation_Date, '%Y-%m-%d').date()
                            else:
                                installation_date_value = Installation_Date
                        else:
                            installation_date_value = None
                    
                        installation_date = st.date_input("Installation Date", 
                                                        min_value=dt.date(2000, 1, 1),
                                                        value=installation_date_value)
                        
                        if manufacturer_date:
                            if isinstance(manufacturer_date, str):
                                manufacturer_date_value = dt.datetime.strptime(manufacturer_date, '%Y-%m-%d').date()
                            else:
                                manufacturer_date_value = manufacturer_date
                        else:
                            manufacturer_date_value = None
                    
                        manufacturer_date = st.date_input("Manufacturer Date", 
                                                        min_value=dt.date(2000, 1, 1),
                                                        value=manufacturer_date_value)
                    
                    col4, col5 = st.columns(2)
                    
                    with col4:
                        serial_number = st.text_input("Serial Number", 
                                                value=serial_number or "",
                                                placeholder="Serial Number")
                        instrument_code = st.text_input("Instrument Code", 
                                                    value="",  # Questo campo non esiste nel DB attualmente
                                                    placeholder="e.g., AMTZ/ARC/EQP/...")
                        
                    with col5:
                        udi_number = st.text_input("UDI Number", 
                                                value=UDI_Number or "", 
                                                placeholder="Unique Device Identifier")
                        gmdn = st.text_input("GMDN", 
                                        value=gmdn or "",
                                        placeholder="Global Medical Device Nomenclature")
                    
                    col_check1, col_check2 = st.columns(2)
                    
                    with col_check1:
                        present = st.checkbox("Present in the hospital", value=bool(Present))
                    
                    with col_check2:
                        auto_update = st.checkbox("Auto-update scoring values", value=False)

                    col_save, col_cancel = st.columns(2)
                
                    with col_save:
                        submitted = st.form_submit_button("Update Device", type="primary")
                
                    if submitted:
                        if not selected_device_id:
                            st.error("Select a device")
                        elif not description.strip():
                            st.error("Description required")
                        else:
                            try:
                                if auto_update==True:                                 
                                    update_device(selected_device_id, description, Class, 1, cost_inr, 
                                                brand, model, installation_date, serial_number, 
                                                manufacturer_date, udi_number, gmdn, present)
                                    st.success("Updated!")
                                else:
                                    update_device_normal(selected_device_id, description, Class, 1, cost_inr, 
                                                    brand, model, installation_date, serial_number, 
                                                    manufacturer_date, udi_number, gmdn, present)
                                    st.success("Updated!")
                            except Exception as e:
                                st.error(f"Error: {e}")
    with tab4:
        all_devices = get_all_devices()
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
                format_func=lambda x: ward_options[x], key='ward'
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
                format_func=lambda x: room_filter_options[x], key='room'
            )

        with col3:
            search = st.text_input("🔍 Search devices:", placeholder="Search by ID, description, brand....", key="search_delete")

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
            serial_number= d[12] or "No Serial Number"


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

        device_to_delete = st.selectbox(
            "Choose device to delete:",
            options=list(device_options.keys()),
            format_func=lambda x: device_options[x],
            key="device_selector1"
        )
        

        if st.button("Delete Selected Device", type="primary"):
            if device_to_delete:
                try:
                    delete_device(device_to_delete)
                    st.success(f"✅ Device {device_to_delete} deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error deleting device: {str(e)}")
            else:
                st.error("Please select a device to delete")

    with tab1:
        devices = get_all_devices()
        rooms = get_all_rooms()
        if not rooms:
            st.error("No rooms found! Please add rooms in the Admin Panel first.")
            st.stop()
        
        room_options = {f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms}
        

        if not devices:
            st.info("No devices found in database. Go to 'Add Devices' page to add some devices first.")
            st.stop()

        # FILTRI PER LA TABELLA
        col1, col2, col3 = st.columns(3)

        with col1:
            wards = get_all_wards()
            ward_options = {"All": "All Wards"}
            ward_options.update({str(w[0]): w[1] for w in wards})
    
            selected_ward_filter = st.selectbox(
                "Filter by Ward:",
                options=list(ward_options.keys()),
                format_func=lambda x: ward_options[x],
                key="table_ward_filter"
            )

        with col2:
            rooms = get_all_rooms()
            if selected_ward_filter != "All":
                filtered_rooms = [r for r in rooms if r[3] == int(selected_ward_filter)]
                room_filter_options = {"All": "All Rooms in Ward"}
                room_filter_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in filtered_rooms})
            else:
                room_filter_options = {"All": "All Rooms"}
                room_filter_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms})
    
            selected_room_filter = st.selectbox(
                "Filter by Room:",
                options=list(room_filter_options.keys()),
                format_func=lambda x: room_filter_options[x],
                key="table_room_filter"
            )

        with col3:
            search = st.text_input(
                "🔍 Search devices:", 
                placeholder="Brand, model, description or ID...", 
                key="view_search_input"
            )

        # APPLICA TUTTI I FILTRI
        filtered_devices = []

        for d in devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial, manufacturer_date, gmdn = d
    
            device_room = next((r for r in rooms if r[0] == room_id), None)
    
            if selected_ward_filter != "All":
                if not device_room or device_room[3] != int(selected_ward_filter):
                    continue
    
            if selected_room_filter != "All":
                if str(room_id) != selected_room_filter:
                    continue
    
            if search:
                search_lower = search.lower()
                room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                search_text = f"{serial} {description} {brand} {model} {room_info} {serial} ".lower()
                if search_lower not in search_text:
                    continue
    
            filtered_devices.append(d)

        # RISULTATI E ANALISI
        if filtered_devices:
            if search or selected_ward_filter != "All" or selected_room_filter != "All":
                active_filters = []
                if selected_ward_filter != "All":
                    active_filters.append(f"Ward: {ward_options[selected_ward_filter]}")
                if selected_room_filter != "All":
                    active_filters.append(f"Room: {room_filter_options[selected_room_filter]}")
                if search:
                    active_filters.append(f"Search: '{search}'")
        
                filter_text = " | ".join(active_filters)
                st.success(f"Showing {len(filtered_devices)} device(s) with filters: {filter_text}")
    
            # TABELLA DEI DISPOSITIVI
            df_display = []
            for d in filtered_devices:
                device_room = next((r for r in rooms if r[0] == d[2]), None)
        
                if device_room:
                    room_name = f"Floor {device_room[1]} - {device_room[2]}"
                    ward_id = device_room[3] if len(device_room) > 3 else None
            
                    if ward_id:
                        ward_info = next((w for w in wards if w[0] == ward_id), None)
                        ward_name = ward_info[1] if ward_info else "Unknown Ward"
                    else:
                        ward_name = "No Ward"
                else:
                    room_name = "No Room"
                    ward_name = "No Ward"
        
                row = [
                    d[3],   # Description
                    d[8],   # Brand
                    d[9],   # Model
                    d[12], #seial number
                    ward_name,  # Ward
                    room_name,  # Room
                    d[10],  # Installation_Date
                    d[13],  # Manufacturer_Date
                    d[11], #instrument code
                    d[14], #gmdn
                    "Yes" if d[7] else "No"   # Present
                ]
                df_display.append(row)

            df = pd.DataFrame(df_display, columns=[
                'Description', 'Brand', 'Model','Seial number', 'Ward', 'Room',
                  'Installation_Date','Manufacturer date' ,'UDI number', 'GMDN', 'Present'
            ])
    
            st.dataframe(df, hide_index=True)
            


            # Calcola i dati una volta
            total_devices = len(filtered_devices)
            present_count = sum([1 for d in filtered_devices if d[7]])
            total_cost = sum([float(d[6]) if d[6] else 0 for d in filtered_devices])
            
            # Calcola età media
            ages = []
            for d in filtered_devices:
                install_date = d[10]
                if install_date:
                    try:
                        from datetime import datetime, date
                        if isinstance(install_date, str):
                            try:
                                install_date_obj = datetime.strptime(install_date, "%Y-%m-%d")
                            except ValueError:
                                try:
                                    install_date_obj = datetime.strptime(install_date, "%d/%m/%Y")
                                except ValueError:
                                    install_date_obj = datetime.strptime(install_date, "%m/%d/%Y")
                        elif isinstance(install_date, date):
                            install_date_obj = datetime.combine(install_date, datetime.min.time())
                        else:
                            install_date_obj = install_date
                        age_years = (datetime.now() - install_date_obj).days / 365.25
                        if age_years >= 0:
                            ages.append(age_years)
                    except:
                        pass
            
            avg_age = sum(ages) / len(ages) if ages else 0
            
            # Formato costi
            if total_cost >= 1000000:
                cost_display = f"{total_cost/1000000:.1f}M"
            elif total_cost >= 1000:
                cost_display = f"{total_cost/1000:.0f}K"
            else:
                cost_display = f"{total_cost:,.0f}"

# SOSTITUISCI la sezione "Quick Statistics" con questo:

            # CSS per rendere le metriche più piccole
            st.markdown("""
            <style>
            div[data-testid="metric-container"] {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            div[data-testid="metric-container"] > div:first-child {
                font-size: 24px !important;
                font-weight: 600 !important;
                color: #1e40af !important;
            }
            
            div[data-testid="metric-container"] > div:last-child {
                font-size: 11px !important;
                color: #64748b !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            </style>
            """, unsafe_allow_html=True)

# SOSTITUISCI la sezione "Quick Statistics" con questo CENTRATO:

            # CSS per rendere le metriche più piccole e centrate
            st.markdown("""
            <style>
            div[data-testid="metric-container"] {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            div[data-testid="metric-container"] > div:first-child {
                font-size: 24px !important;
                font-weight: 600 !important;
                color: #1e40af !important;
            }
            
            div[data-testid="metric-container"] > div:last-child {
                font-size: 11px !important;
                color: #64748b !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            </style>
            """, unsafe_allow_html=True)



           
            # Grafici


            # chart_col1, chart_col2 = st.columns(2)

            # with chart_col1:
            #     st.write("**Devices by Type**")
    
            #     def categorize_device_by_type(description):
            #         if not description:
            #             return 'Other'
            #         desc_lower = description.lower()
            #         if any(keyword in desc_lower for keyword in ['monitor', 'monitoring', 'display', 'screen']):
            #             return 'Monitor'
            #         elif any(keyword in desc_lower for keyword in ['ecg', 'ekg', 'electrocardiogram', 'cardiac']):
            #             return 'ECG'
            #         elif any(keyword in desc_lower for keyword in ['ventilator', 'ventilation', 'breathing', 'respiratory']):
            #             return 'Ventilator'
            #         elif any(keyword in desc_lower for keyword in ['light', 'lamp', 'illumination', 'surgical light', 'ot light', 'operating']):
            #             return 'OT Light'
            #         elif any(keyword in desc_lower for keyword in ['pump', 'infusion', 'syringe']):
            #             return 'Pump'
            #         elif any(keyword in desc_lower for keyword in ['ultrasound', 'echo', 'doppler']):
            #             return 'Ultrasound'
            #         elif any(keyword in desc_lower for keyword in ['xray', 'x-ray', 'radiograph']):
            #             return 'X-Ray'
            #         elif any(keyword in desc_lower for keyword in ['defibrillator', 'defib']):
            #             return 'Defibrillator'
            #         else:
            #             return 'Other'
    
            #     type_counts = {}
            #     for d in filtered_devices:
            #         description = d[3] or 'Unknown'
            #         device_type = categorize_device_by_type(description)
            #         type_counts[device_type] = type_counts.get(device_type, 0) + 1

            #     if type_counts:
            #         # ECHARTS COMPATTO
            #         options = {
            #             "tooltip": {"trigger": "axis"},
            #             "grid": {"left": "10%", "right": "10%", "bottom": "15%", "top": "10%"},
            #             "xAxis": {
            #                 "type": "category",
            #                 "data": list(type_counts.keys()),
            #                 "axisLabel": {"fontSize": 10, "rotate": 30}
            #             },
            #             "yAxis": {"type": "value", "axisLabel": {"fontSize": 10}},
            #             "series": [{
            #                 "type": "bar",
            #                 "data": list(type_counts.values()),
            #                 "itemStyle": {"color": "#3b82f6", "borderRadius": [4, 4, 0, 0]}
            #             }]
            #         }
            #         st_echarts(options=options, height="280px")
            #     else:
            #         st.info("No device data available for classification")

            # with chart_col2:
            #     st.write("**Devices by Age**")
            #     age_ranges = {"0-1 years": 0, "1-3 years": 0, "3-5 years": 0, "5-10 years": 0, ">10 years": 0}
        
            #     for d in filtered_devices:
            #         install_date = d[10]
            #         if install_date:
            #             from datetime import date
            #             try:
            #                 if isinstance(install_date, str):
            #                     if "/" in install_date:
            #                         install_date_obj = dt.datetime.strptime(install_date, "%d/%m/%Y").date()
            #                     else:
            #                         install_date_obj = date.fromisoformat(str(install_date))
            #                 else:
            #                     install_date_obj = install_date
            #                 age_years = (date.today() - install_date_obj).days / 365.25
            #             except:
            #                 age_years = 0
            #         else:
            #             age_years = 0
            
            #         if age_years <= 1:
            #             age_ranges["0-1 years"] += 1
            #         elif age_years <= 3:
            #             age_ranges["1-3 years"] += 1
            #         elif age_years <= 5:
            #             age_ranges["3-5 years"] += 1
            #         elif age_years <= 10:
            #             age_ranges["5-10 years"] += 1
            #         else:
            #             age_ranges[">10 years"] += 1
        
            #     if any(age_ranges.values()):
            #         # PIE CHART COMPATTO
            #         colors = ["#22c55e", "#84cc16", "#eab308", "#f97316", "#ef4444"]
            #         pie_data = [{"value": count, "name": age, "itemStyle": {"color": colors[i]}} 
            #                    for i, (age, count) in enumerate(age_ranges.items()) if count > 0]
                    
            #         options = {
            #             "tooltip": {"trigger": "item"},
            #             "series": [{
            #                 "type": "pie",
            #                 "radius": "70%",
            #                 "center": ["50%", "50%"],
            #                 "data": pie_data,
            #                 "label": {"fontSize": 10}
            #             }]
            #         }
            #         st_echarts(options=options, height="280px")
            #     else:
            #         st.info("No age data available for analysis")
            # .

            # MAPPA INTERATTIVA OSPEDALE - SUNBURST CHART
            # Titolo centrato con stile coordinato
            st.markdown("""
            <h3 style="
                text-align: center; 
                color: #334155; 
                font-weight: 600; 
                margin-bottom: 1rem; 
                font-family: Inter, sans-serif;
                font-size: 20px;
            ">
                Hospital Device Map - Interactive View
            </h3>
            """, unsafe_allow_html=True)
            
            # Prepara i dati per Sunburst - RAGGRUPPATI PER FLOOR
            sunburst_data = []
            
            # Prima raggruppa per Floor, poi per Ward
            floor_structure = {}
            
            for d in filtered_devices:
                device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial, manufacturer_date, gmdn = d
                
                # Trova room info
                device_room = next((r for r in rooms if r[0] == room_id), None)
                if not device_room:
                    continue
                    
                floor_id, room_name, ward_id = device_room[1], device_room[2], device_room[3]
                
                # Trova ward info
                ward_info = next((w for w in wards if w[0] == ward_id), None)
                ward_name = ward_info[1] if ward_info else f"Ward {ward_id}"
                
                # Calcola età per colore
                age_years = 0
                if install_date:
                    try:
                        from datetime import datetime, date
                        if isinstance(install_date, str):
                            try:
                                install_date_obj = datetime.strptime(install_date, "%Y-%m-%d")
                            except ValueError:
                                try:
                                    install_date_obj = datetime.strptime(install_date, "%d/%m/%Y")
                                except ValueError:
                                    install_date_obj = datetime.strptime(install_date, "%m/%d/%Y")
                        elif isinstance(install_date, date):
                            install_date_obj = datetime.combine(install_date, datetime.min.time())
                        else:
                            install_date_obj = install_date
                        age_years = (datetime.now() - install_date_obj).days / 365.25
                    except:
                        pass
                
                # NUOVA STRUTTURA: Floor -> Ward -> Room
                floor_key = f"Floor {floor_id}"
                ward_key = f"Floor {floor_id} - {ward_name}"
                room_key = f"Floor {floor_id} - {ward_name} - {room_name}"
                
                if floor_key not in floor_structure:
                    floor_structure[floor_key] = {'wards': {}, 'device_count': 0, 'total_cost': 0}
                
                if ward_key not in floor_structure[floor_key]['wards']:
                    floor_structure[floor_key]['wards'][ward_key] = {'rooms': {}, 'device_count': 0, 'total_cost': 0}
                
                if room_key not in floor_structure[floor_key]['wards'][ward_key]['rooms']:
                    floor_structure[floor_key]['wards'][ward_key]['rooms'][room_key] = {'devices': [], 'device_count': 0, 'total_cost': 0}
                
                # Aggiungi device
                device_info = {
                    'id': device_id,
                    'description': description or 'Unknown',
                    'brand': brand or 'Unknown',
                    'model': model or 'Unknown', 
                    'class': device_class or 'Unknown',
                    'cost': cost_inr or 0,
                    'present': present,
                    'age': age_years,
                    'serial': serial or 'N/A'
                }
                
                floor_structure[floor_key]['wards'][ward_key]['rooms'][room_key]['devices'].append(device_info)
                floor_structure[floor_key]['wards'][ward_key]['rooms'][room_key]['device_count'] += 1
                floor_structure[floor_key]['wards'][ward_key]['rooms'][room_key]['total_cost'] += cost_inr or 0
                
                floor_structure[floor_key]['wards'][ward_key]['device_count'] += 1
                floor_structure[floor_key]['wards'][ward_key]['total_cost'] += cost_inr or 0
                
                floor_structure[floor_key]['device_count'] += 1
                floor_structure[floor_key]['total_cost'] += cost_inr or 0
            
            # Costruisci dati Sunburst con nuova struttura
            ids = ["Hospital"]
            labels = ["Hospital"]
            parents = [""]
            values = [len(filtered_devices)]
            colors = [0.5]  # Neutral color for hospital root
            hover_texts = [f"<b>Hospital Total</b><br>Devices: {len(filtered_devices)}<br>Total Value: ₹{sum([d[6] or 0 for d in filtered_devices]):,.0f}"]
            
            # Livello 1: Floors (ordinati numericamente)
            sorted_floors = sorted(floor_structure.keys(), key=lambda x: int(x.split()[1]))
            for floor_name in sorted_floors:
                floor_data = floor_structure[floor_name]
                floor_id_clean = floor_name.replace(" ", "_")
                ids.append(floor_id_clean)
                labels.append(floor_name)
                parents.append("Hospital")
                values.append(floor_data['device_count'])
                colors.append(0.2 + (floor_data['device_count'] / len(filtered_devices)) * 0.6)
                hover_texts.append(f"<b>{floor_name}</b><br>Devices: {floor_data['device_count']}<br>Value: ₹{floor_data['total_cost']:,.0f}")
                
                # Livello 2: Wards (raggruppati per floor)
                for ward_name, ward_data in floor_data['wards'].items():
                    ward_id_clean = ward_name.replace(" ", "_").replace("-", "_")
                    ward_display = ward_name.split(" - ")[1]  # Solo il nome del ward
                    ids.append(ward_id_clean)
                    labels.append(ward_display)
                    parents.append(floor_id_clean)
                    values.append(ward_data['device_count'])
                    colors.append(0.3 + (ward_data['device_count'] / floor_data['device_count']) * 0.7)
                    hover_texts.append(f"<b>{ward_display}</b><br>Floor: {floor_name}<br>Devices: {ward_data['device_count']}<br>Value: ₹{ward_data['total_cost']:,.0f}")
                    
                    # Livello 3: Rooms
                    for room_name, room_data in ward_data['rooms'].items():
                        room_id_clean = room_name.replace(" ", "_").replace("-", "_").replace(".", "_")
                        room_display = room_name.split(" - ")[-1]  # Solo il nome della room
                        ids.append(room_id_clean)
                        labels.append(room_display)
                        parents.append(ward_id_clean)
                        values.append(room_data['device_count'])
                        colors.append(0.1 + (room_data['device_count'] / ward_data['device_count']) * 0.9)
                        
                        # Dettagli devices per hover
                        device_details = []
                        for device in room_data['devices'][:3]:  # Max 3 devices per hover
                            status = "🟢" if device['present'] else "🔴"
                            age_display = f"{device['age']:.1f}y" if device['age'] > 0 else "New"
                            device_details.append(f"{status} {device['description']} ({device['brand']})")
                        
                        if room_data['device_count'] > 3:
                            device_details.append(f"... +{room_data['device_count']-3} more")
                            
                        hover_texts.append(
                            f"<b>{room_display}</b><br>" +
                            f"Floor: {floor_name}<br>" +
                            f"Ward: {ward_display}<br>" +
                            f"Devices: {room_data['device_count']}<br>" +
                            f"Value: ₹{room_data['total_cost']:,.0f}<br>" +
                            f"<br>Devices:<br>" + "<br>".join(device_details)
                        )
                        
                        # Livello 4: Dispositivi individuali
                        for device in room_data['devices']:
                            device_id_clean = f"device_{device['id']}"
                            device_name = f"{device['description'][:15]}..." if len(device['description']) > 15 else device['description']
                            
                            ids.append(device_id_clean)
                            labels.append(device_name)
                            parents.append(room_id_clean)
                            values.append(1)  # Ogni device vale 1
                            
                            # Colore basato su età e status
                            if not device['present']:
                                color_val = 0.1  # Rosso per inattivo
                            elif device['age'] < 2:
                                color_val = 0.9  # Verde per nuovo
                            elif device['age'] < 5:
                                color_val = 0.6  # Giallo per medio
                            else:
                                color_val = 0.3  # Arancione per vecchio
                            
                            colors.append(color_val)
                            
                            # Hover dettagliato per singolo device
                            status_icon = "🟢 Active" if device['present'] else "🔴 Inactive"
                            age_display = f"{device['age']:.1f} years" if device['age'] > 0 else "New"
                            cost_display = f"₹{device['cost']:,.0f}" if device['cost'] > 0 else "No cost data"
                            
                            hover_texts.append(
                                f"<b>{device['description']}</b><br>" +
                                f"ID: {device['id']}<br>" +
                                f"Brand: {device['brand']}<br>" +
                                f"Model: {device['model']}<br>" +
                                f"Class: {device['class']}<br>" +
                                f"Serial: {device['serial']}<br>" +
                                f"Age: {age_display}<br>" +
                                f"Cost: {cost_display}<br>" +
                                f"Status: {status_icon}"
                            )
            
            # Crea Sunburst Chart
            if len(ids) > 1:  # Solo se abbiamo dati
                fig = go.Figure(go.Sunburst(
                    ids=ids,
                    labels=labels,
                    parents=parents,
                    values=values,
                    hovertemplate='%{hovertext}<extra></extra>',
                    hovertext=hover_texts,
                    marker=dict(
                        colorscale=[[0, '#f0f9ff'],    # Azzurro chiarissimo
                                   [0.3, '#bae6fd'],   # Azzurro chiaro
                                   [0.6, '#7dd3fc'],   # Azzurro medio
                                   [1.0, '#0ea5e9']],  # Azzurro vivace (coordinato con tema)
                        cmin=0,  # Inizia da 0
                        colorbar=dict(
                            title=dict(text="Device Density", font=dict(size=12, color='#64748b')),
                            tickfont=dict(size=10, color='#64748b'),
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor='#e5e7eb',
                            borderwidth=1,
                            x=1.02,
                            len=0.8
                        ),
                        line=dict(width=2, color='white')  # Bordi bianchi spessi
                    ),
                    textfont=dict(
                        size=11,
                        color='#1e293b',  # Testo scuro per contrasto
                        family='Inter'
                    ),
                    insidetextorientation='auto',  # Orienta il testo per leggibilità
                    branchvalues="total",
                    maxdepth=5,  # Aumentato per includere devices individuali
                ))
                
                fig.update_layout(
                    
                    font=dict(size=11, family="Inter"),
                    height=650,
                    width=800,
                    margin=dict(l=50, r=50, t=80, b=50),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    # Centra il sunburst
                    xaxis=dict(domain=[0.1, 0.9]),
                    yaxis=dict(domain=[0.1, 0.9])
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Legenda interattiva
                
                
            else:
                st.info("No location data available for mapping")

            #esporta i risultati
            st.subheader("Export Results")

            if st.button("📥 Export to CSV"):
                csv = df.to_csv(index=False)
                from datetime import date
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"devices_analysis_{date.today()}.csv",
                    mime="text/csv"
                )

        else:
            st.warning("No devices found matching the selected filters")
    
            st.info("**Try:**")
            st.write("• Removing some filters")
            st.write("• Using different search terms") 
            st.write("• Selecting 'All' in the dropdown filters")