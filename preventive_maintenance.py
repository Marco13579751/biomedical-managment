import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import (
    get_all_devices, insert_preventive_maintenance, get_all_preventive_maintenance,
    get_overdue_maintenance, get_upcoming_maintenance, update_preventive_maintenance,
    delete_preventive_maintenance, get_preventive_maintenance_by_device,
    insert_attachment, get_attachments_by_record
)


"""
Preventive Maintenance System - Essential Version
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from database import (
    get_all_devices, insert_preventive_maintenance, get_all_preventive_maintenance,
    update_preventive_maintenance, get_all_wards, get_all_rooms,
    delete_preventive_maintenance
)

def show_preventive_maintenance_page():
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
    
    /* Pulsante Delete rosso - targeting specifico per pulsanti dopo Danger Zone */
    div[data-testid="stHorizontalBlock"] button[kind="primary"]:disabled {
        background: linear-gradient(135deg, #9ca3af 0%, #d1d5db 100%) !important;
        color: #6b7280 !important;
        cursor: not-allowed !important;
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
  
    
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Managment" ,"Schedule", "Edit"])
    
    with tab1:
        show_dashboard()
    
    with tab2:
        show_management()
        
    
    with tab3:
        show_schedule_form()
        
    
    with tab4:
        show_edit_maintenance()

def show_dashboard():
    
    all_maintenance = get_all_preventive_maintenance()
    if not all_maintenance:
        st.info("📭 No maintenance data found")
        return
    
    # Simple counters - CALCOLO OVERDUE COME IN MANAGEMENT
    # Overdue = scheduled_date passata (days < 0) E non Completed/Cancelled
    overdue = [m for m in all_maintenance if len(m) > 6 and m[6] and m[9] in ['Scheduled', 'In Progress'] and (datetime.fromisoformat(str(m[6])).date() - datetime.now().date()).days < 0]
    upcoming = [m for m in all_maintenance if len(m) > 9 and m[9] in ['Scheduled', 'In Progress'] and len(m) > 6 and m[6] and 0 <= (datetime.fromisoformat(str(m[6])).date() - datetime.now().date()).days <= 30]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
     st.metric("Total", len(all_maintenance), delta=None)

    with col2:
        # Delta inverso: meno overdue = meglio (verde)
        st.metric("Overdue", len(overdue), delta=len(overdue), delta_color="inverse")

    with col3:
        st.metric("Upcoming (30d)", len(upcoming), delta=None)

    with col4:
        # Solo manutenzioni con scheduled_date nel passato
        past_maintenance = [m for m in all_maintenance if len(m) > 6 and m[6] and datetime.fromisoformat(str(m[6])).date() < datetime.now().date()]
        
        # Di quelle passate, quante sono Completed
        completed = len([m for m in past_maintenance if len(m) > 9 and m[9] == 'Completed'])
        
        # Calcolo rate solo sulle manutenzioni che dovevano essere già fatte
        rate = (completed / len(past_maintenance) * 100) if past_maintenance else 0
        delta_color = "normal" if rate >= 80 else "inverse"
        st.metric("Completion %", f"{rate:.1f}%", delta=f"{rate:.1f}%", delta_color=delta_color)
    
    # Overdue table - SOLO Days <= 7, ESCLUDO Completed/Cancelled
    if overdue or upcoming:
        
        # Combino overdue + upcoming per avere sia scaduti che urgenti
        critical_maintenance = []
        

    
    # Charts
    if all_maintenance:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart for maintenance types - conta ogni tipo separatamente
            maintenance_types = {}
            for m in all_maintenance:
                if len(m) >= 6 and m[5]:
                    # Split dei tipi multipli separati da virgola
                    types = [t.strip() for t in m[5].split(',')]
                    for mtype in types:
                        if mtype:  # Ignora stringhe vuote
                            maintenance_types[mtype] = maintenance_types.get(mtype, 0) + 1
            
            if maintenance_types:
                fig = px.pie(
                    values=list(maintenance_types.values()),
                    names=list(maintenance_types.keys()),
                    title="Maintenance Types"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Bar chart per Completed vs Overdue con colori specifici
            # Calcolo Completed
            completed_count = len([m for m in all_maintenance if len(m) >= 10 and m[9] == 'Completed'])
            
            # Calcolo Overdue (scheduled_date passata E non completed/cancelled)
            overdue_count = len([m for m in all_maintenance 
                                if len(m) > 6 and m[6] 
                                and m[9] in ['Scheduled', 'In Progress']
                                and datetime.fromisoformat(str(m[6])).date() < datetime.now().date()])
            
            # Dati per il grafico
            status_data = {
                'Status': ['Completed', 'Overdue'],
                'Count': [completed_count, overdue_count]
            }
            
            df_status = pd.DataFrame(status_data)
            
            # Grafico con colori personalizzati
            fig = px.bar(
                df_status,
                x='Status',
                y='Count',
                title="Completed vs Overdue",
                color='Status',
                color_discrete_map={
                    'Completed': '#22c55e',  # Verde
                    'Overdue': '#ef4444'      # Rosso
                }
            )
            
            # Rimuovi la legenda (è ridondante)
            fig.update_layout(showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True)

def show_schedule_form():

    
    devices = get_all_devices()
    rooms = get_all_rooms()
    wards = get_all_wards()
    
    if not devices:
        st.error("⚠️ No devices found")
        return

    # Simple device filtering
    col1, col2, col3 = st.columns(3)

    with col1:
        ward_options = {"All": "All Wards"}
        ward_options.update({str(w[0]): w[1] for w in wards})
        selected_ward = st.selectbox("Filter by Ward:", list(ward_options.keys()), format_func=lambda x: ward_options[x])

    with col2:
        if selected_ward != "All":
            filtered_rooms = [r for r in rooms if len(r) >= 4 and r[3] == int(selected_ward)]
            room_options = {"All": "All Rooms in Ward"}
            room_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in filtered_rooms if len(r) >= 3})
        else:
            room_options = {"All": "All Rooms"}
            room_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms if len(r) >= 3})
        
        selected_room = st.selectbox("Filter by Room:", list(room_options.keys()), format_func=lambda x: room_options[x])

    with col3:
        search = st.text_input("🔍 Search devices:")

    # Filter devices
    filtered_devices = []
    for d in devices:
        if len(d) < 10:
            continue
            
        device_room = next((r for r in rooms if r[0] == d[2]), None)
        
        # Ward filter
        if selected_ward != "All" and (not device_room or len(device_room) < 4 or device_room[3] != int(selected_ward)):
            continue
            
        # Room filter
        if selected_room != "All" and str(d[2]) != selected_room:
            continue
            
        # Search filter
        if search and search.lower() not in f"{d[0]} {d[3]} {d[8]} {d[9]}".lower():
            continue
            
        filtered_devices.append(d)

    if not filtered_devices:
        st.warning("No devices found")
        return

    # Device selection OUTSIDE form
    device_options = []
    for d in filtered_devices:
        device_room = next((r for r in rooms if r[0] == d[2]), None)
        ward_name = "No Ward"
        if device_room and len(device_room) >= 4:
            ward_info = next((w for w in wards if w[0] == device_room[3]), None)
            ward_name = ward_info[1] if ward_info else "Unknown Ward"
            room_display = f"Floor {device_room[1]} - {device_room[2]}"
            location = f"{ward_name} | {room_display}"
        else:
            location = "No Location"
        
        option = f"{'Serial number: '} {d[12]} | {d[3] or 'No Description'} | {d[8] or 'No Brand'} {d[9] or 'No Model'} | {location}"
        device_options.append((option, d[0]))
    
    selected_device = st.selectbox("Choose device to schedule:", [opt[0] for opt in device_options])
    selected_device_id = next(opt[1] for opt in device_options if opt[0] == selected_device)

    # Form
    with st.form("schedule_maintenance"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Multiselect per permettere selezione multipla
            maintenance_types = st.multiselect(
                "Type:", 
                ["Preventive", "Calibration", "Inspection", "Cleaning", "Software Update", "Parts Replacement"],
                default=["Preventive"],
                help="You can select multiple maintenance types"
            )
            # Converto la lista in stringa separata da virgole
            maintenance_type = ", ".join(maintenance_types) if maintenance_types else "Preventive"
            
            scheduled_date = st.date_input("Scheduled Date:", value=date.today())
            
        with col2:
            priority = st.selectbox("Priority:", ["Critical", "High", "Medium", "Low"])
            technician_name = st.text_input("Technician Name:")
            technician_email = st.text_input("Technician Email:")

        with col3:
            recurring = st.checkbox("🔄 Enable Recurring Maintenance")
            frequency_days = st.number_input("Frequency (days):", min_value=0, value=0, help="How many days between maintenance cycles")
            max_recurrences = st.number_input("Max Recurrences:", min_value=0, value=0, help="Maximum number of recurring maintenances")

            # I valori vengono usati solo se recurring è True
            if not recurring:
                frequency_days = None
                max_recurrences = 0
        
        description = st.text_area("Description:")
        
        if st.form_submit_button("Schedule", type="primary"):
            due_date = scheduled_date + timedelta(days=frequency_days if frequency_days else 30)
            
            maintenance_ids = []
            if recurring and frequency_days:
                for i in range(max_recurrences):
                    current_scheduled = scheduled_date + timedelta(days=frequency_days * i)
                    current_due = current_scheduled + timedelta(days=frequency_days)
                    
                    maintenance_id = insert_preventive_maintenance(
                        device_id=selected_device_id,
                        maintenance_type=maintenance_type,
                        scheduled_date=current_scheduled,
                        due_date=current_due,
                        priority=priority,
                        technician_name=technician_name or None,
                        technician_email=technician_email or None,
                        description=f"{description} (Recurrence {i+1}/{max_recurrences})" if description else f"Recurrence {i+1}/{max_recurrences}"
                    )
                    maintenance_ids.append(maintenance_id)
            else:
                maintenance_id = insert_preventive_maintenance(
                    device_id=selected_device_id,
                    maintenance_type=maintenance_type,
                    scheduled_date=scheduled_date,
                    due_date=due_date,
                    priority=priority,
                    technician_name=technician_name or None,
                    technician_email=technician_email or None,
                    description=description or None
                )
                maintenance_ids.append(maintenance_id)
            
            if len(maintenance_ids) > 1:
                st.success(f"✅ {len(maintenance_ids)} recurring maintenances scheduled!")
            else:
                st.success(f"✅ Maintenance scheduled! ID: {maintenance_ids[0]}")

def show_management():
    
    all_maintenance = get_all_preventive_maintenance()
    
    if not all_maintenance:
        st.info("📭 No maintenance found")
        return
    
    # Simple filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        types = list(set([m[5] for m in all_maintenance if len(m) > 5 and m[5]]))
        selected_types = st.multiselect("Type:", types, default=types)
    
    with col2:
        statuses = list(set([m[9] for m in all_maintenance if len(m) > 9 and m[9]]))
        selected_statuses = st.multiselect("Status:", statuses, default=statuses)
    
    with col3:
        priorities = list(set([m[10] for m in all_maintenance if len(m) > 10 and m[10]]))
        selected_priorities = st.multiselect("Priority:", priorities, default=priorities)
    
    # Apply filters
    filtered_maintenance = []
    for m in all_maintenance:
        if (len(m) > 10 and 
            (not selected_types or (len(m) > 5 and m[5] in selected_types)) and
            (not selected_statuses or (len(m) > 9 and m[9] in selected_statuses)) and 
            (not selected_priorities or (len(m) > 10 and m[10] in selected_priorities))):
            filtered_maintenance.append(m)
    
    if filtered_maintenance:
        st.write(f"**{len(filtered_maintenance)} items found**")
        
        table_data = []
        for m in filtered_maintenance:
            if len(m) < 13:
                continue
                
            scheduled_date = datetime.fromisoformat(str(m[6])).date() if m[6] else datetime.now().date()
            days_diff = (scheduled_date - datetime.now().date()).days
            
            table_data.append({
                
                'Device': f"{m[2] or 'Unknown'} - {m[3] or 'Unknown'} {m[4] or 'Unknown'}",
                'Type': m[5] or "Unknown",
                'Scheduled': m[6] or "No Date",
                'Days': days_diff,
                'Status': m[9] or "Unknown",
                'Priority': m[10] or "Unknown",
                'Technician': m[11] or 'Unassigned',
                'Description': m[13] if len(m) > 13 and m[13] else 'No description'
            })
        
        if table_data:
            df = pd.DataFrame(table_data)
            
            # Funzione per colorare le righe
            def highlight_rows(row):
                status = row['Status']
                days = row['Days']
                
                # Verde se Completed o Cancelled
                if status in ['Completed', 'Cancelled']:
                    color = 'background-color: #e6ffe6'  # Verde
                # Rosso se scaduto
                elif days < 0:
                    color = 'background-color: #ffe6e6'  # Rosso - Scaduto
                # Giallo se urgente (0-7 giorni)
                elif 0 <= days <= 7:
                    color = 'background-color: #fff2e6'  # Giallo - Urgente
                else:
                    color = ''  # Nessun colore
                
                # Applica il colore a Days E Status
                return [color if col in ['Days', 'Status'] else '' for col in row.index]
            
            # Applica lo styling
            styled_df = df.style.apply(highlight_rows, axis=1)
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No maintenance found with filters")

def show_edit_maintenance():
    
    all_maintenance = get_all_preventive_maintenance()
    devices = get_all_devices()
    rooms = get_all_rooms()
    wards = get_all_wards()
    
    if not all_maintenance:
        st.info("📭 No maintenance found")
        return

    # Filtering system like in schedule
    col1, col2, col3 = st.columns(3)

    with col1:
        ward_options = {"All": "All Wards"}
        ward_options.update({str(w[0]): w[1] for w in wards})
        selected_ward = st.selectbox("Filter by Ward:", list(ward_options.keys()), format_func=lambda x: ward_options[x], key="edit_ward")

    with col2:
        if selected_ward != "All":
            filtered_rooms = [r for r in rooms if len(r) >= 4 and r[3] == int(selected_ward)]
            room_options = {"All": "All Rooms in Ward"}
            room_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in filtered_rooms if len(r) >= 3})
        else:
            room_options = {"All": "All Rooms"}
            room_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms if len(r) >= 3})
        
        selected_room = st.selectbox("Filter by Room:", list(room_options.keys()), format_func=lambda x: room_options[x], key="edit_room")

    with col3:
        search = st.text_input("🔍 Search devices:", key="edit_search")

    # Apply filters to maintenance based on device location
    filtered_maintenance = []
    
    for m in all_maintenance:
        if len(m) < 10:
            continue
            
        device_id = m[1]
        device = next((d for d in devices if len(d) > 0 and d[0] == device_id), None)
        if not device or len(device) < 10:
            continue
            
        device_room = next((r for r in rooms if r[0] == device[2]), None) if len(device) > 2 else None

        # Ward filter
        if selected_ward != "All" and (not device_room or len(device_room) < 4 or device_room[3] != int(selected_ward)):
            continue

        # Room filter  
        if selected_room != "All" and str(device[2]) != selected_room:
            continue

        # Search filter
        if search and search.lower() not in f"{device_id} {device[3]} {device[8]} {device[9]}".lower():
            continue

        filtered_maintenance.append(m)

    if not filtered_maintenance:
        st.warning("No maintenance found with filters")
        return

    # Maintenance selection
    maintenance_options = []
    for m in filtered_maintenance:
        if len(m) < 10:
            continue
            
        device = next((d for d in devices if d[0] == m[1]), None)
        if device:
            device_room = next((r for r in rooms if r[0] == device[2]), None)
            
            if device_room and len(device_room) >= 4:
                ward_info = next((w for w in wards if w[0] == device_room[3]), None)
                ward_name = ward_info[1] if ward_info else "Unknown Ward"
                room_display = f"Floor {device_room[1]} - {device_room[2]}"
                location = f"{ward_name} | {room_display}"
            else:
                location = "No Location"

            option = f"{'Serial number: '} {device[12]} | {device[3] or 'Unknown'} | {device[8] or 'Unknown'} {device[9] or 'No model'} | {location} | {m[5] or 'Unknown'} ({m[9] or 'Unknown'})"
            maintenance_options.append((option, m[0]))

    if not maintenance_options:
        st.warning("No maintenance records found")
        return

    selected_maintenance = st.selectbox("Choose device to edit:", [opt[0] for opt in maintenance_options])
    maintenance_id = next(opt[1] for opt in maintenance_options if opt[0] == selected_maintenance)
    
    current_maintenance = next(m for m in filtered_maintenance if m[0] == maintenance_id)

    # FORM con tutti gli input e pulsante UPDATE
    with st.form("edit_maintenance"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Multiselect per tipi multipli
            current_types = []
            if len(current_maintenance) > 5 and current_maintenance[5]:
                current_types = [t.strip() for t in str(current_maintenance[5]).split(",")]
            
            all_types = ["Preventive", "Calibration", "Inspection", "Cleaning", "Software Update", "Parts Replacement"]
            
            edit_types = st.multiselect(
                "Type:", 
                all_types,
                default=[t for t in current_types if t in all_types] if current_types else ["Preventive"],
                help="You can select multiple maintenance types"
            )
            
            current_scheduled = datetime.fromisoformat(str(current_maintenance[6])).date() if len(current_maintenance) > 6 and current_maintenance[6] else datetime.now().date()
            edit_scheduled = st.date_input("Scheduled Date:", value=current_scheduled)
            
            edit_priority = st.selectbox("Priority:", ["Critical", "High", "Medium", "Low"],
                                       index=2 if len(current_maintenance) <= 10 or not current_maintenance[10] else
                                       ["Critical", "High", "Medium", "Low"].index(current_maintenance[10])
                                       if current_maintenance[10] in ["Critical", "High", "Medium", "Low"] else 2)
        
        with col2:
            current_status = current_maintenance[9] if len(current_maintenance) > 9 and current_maintenance[9] else "Scheduled"
            
            edit_status = st.selectbox("Status:", 
                                     ["Scheduled", "In Progress", "Cancelled", "Completed"],
                                     index=["Scheduled", "In Progress", "Cancelled", "Completed"].index(current_status) 
                                     if current_status in ["Scheduled", "In Progress", "Cancelled", "Completed"] else 0)
            
            edit_technician = st.text_input("Technician:", value=current_maintenance[11] if len(current_maintenance) > 11 and current_maintenance[11] else "")
            
            edit_technician_email = st.text_input("Technician Email:", value=current_maintenance[12] if len(current_maintenance) > 12 and current_maintenance[12] else "")

        edit_description = st.text_area("Description:", value=current_maintenance[13] if len(current_maintenance) > 13 and current_maintenance[13] else "")

        # Pulsante UPDATE dentro il form
        update_btn = st.form_submit_button("Update Maintenance", type="primary", use_container_width=True)

        if update_btn:
            edit_type = ", ".join(edit_types) if edit_types else "Preventive"
            
            update_data = {
                'maintenance_type': edit_type,
                'scheduled_date': edit_scheduled,
                'status': edit_status,
                'priority': edit_priority,
                'technician_name': edit_technician or None,
                'technician_email': edit_technician_email or None,
                'description': edit_description or None
            }
            
            if edit_status == "Completed":
                update_data['completed_date'] = datetime.now().date()
            
            success = update_preventive_maintenance(maintenance_id, **update_data)
            
            if success:
                st.success(f"✅ Maintenance ID {maintenance_id} updated!")
                st.rerun()
            else:
                st.error("❌ Failed to update")
    
    # PULSANTE DELETE fuori dal form, subito sotto

    
    col1, col2 = st.columns([1, 5])
    with col1:
        delete_btn = st.button("Delete Maintenance ", type="primary", use_container_width=True)
    
    if delete_btn:
        success = delete_preventive_maintenance(maintenance_id)
        if success:
            st.success(f"✅ Maintenance ID {maintenance_id} deleted successfully!")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Failed to delete maintenance")

def show_schedule_maintenance():
    
    # Get dispositivi disponibili
    devices = get_all_devices()
    if not devices:
        st.error("❌ Nessun dispositivo trovato. Aggiungi prima dei dispositivi.")
        return
    
    # Form per nuova manutenzione
    with st.form("new_maintenance_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Selezione dispositivo
            device_options = {f"{d[0]} - {d[1]} ({d[8] or 'N/A'} {d[9] or 'N/A'})": d[0] for d in devices}
            selected_device = st.selectbox(
                "Seleziona Dispositivo",
                options=list(device_options.keys()),
                help="Scegli il dispositivo per cui programmare la manutenzione"
            )
            device_id = device_options[selected_device]
            
            # Tipo manutenzione
            maintenance_type = st.selectbox(
                "Tipo Manutenzione",
                options=["Preventive", "Calibration"],
                help="Seleziona il tipo di manutenzione"
            )
            
            # Date
            scheduled_date = st.date_input(
                "Data Programmata",
                value=datetime.now().date(),
                help="Quando è programmata la manutenzione"
            )
            
            due_date = st.date_input(
                "Data Scadenza",
                value=datetime.now().date() + timedelta(days=30),
                help="Entro quando deve essere completata"
            )
            
            # Priorità
            priority = st.selectbox(
                "Priorità",
                options=["Low", "Medium", "High", "Critical"],
                index=1,
                help="Priorità della manutenzione"
            )
        
        with col2:
            # Tecnico
            technician_name = st.text_input(
                "Nome Tecnico",
                help="Nome del tecnico responsabile"
            )
            
            technician_email = st.text_input(
                "Email Tecnico",
                help="Email del tecnico per notifiche"
            )
            
            # Costi stimati
            cost_inr = st.number_input(
                "Costo Stimato (₹)",
                min_value=0.0,
                step=100.0,
                help="Costo stimato in Rupie Indiane"
            )
            
            # Durata stimata
            duration_hours = st.number_input(
                "Durata Stimata (ore)",
                min_value=0.0,
                step=0.5,
                help="Durata stimata in ore"
            )
            
            # Prossima manutenzione
            if maintenance_type == "Preventive":
                next_maintenance_date = st.date_input(
                    "Prossima Manutenzione",
                    value=None,
                    help="Quando programmare la prossima manutenzione preventiva"
                )
            else:
                next_maintenance_date = None
            
            # Standard di conformità
            compliance_standard = st.text_input(
                "Standard di Conformità",
                placeholder="es. ISO 13485, FDA 21 CFR 820",
                help="Standard di riferimento per la manutenzione"
            )
        
        # Descrizione
        description = st.text_area(
            "Descrizione e Note",
            help="Descrizione dettagliata della manutenzione da eseguire"
        )
        
        # Submit
        submitted = st.form_submit_button("📅 Pianifica Manutenzione", type="primary")
        
        if submitted:
            try:
                # Validazioni
                if scheduled_date > due_date:
                    st.error("❌ La data programmata non può essere successiva alla scadenza")
                    return
                
                # Inserisci manutenzione
                maintenance_id = insert_preventive_maintenance(
                    device_id=device_id,
                    maintenance_type=maintenance_type,
                    scheduled_date=scheduled_date,
                    due_date=due_date,
                    priority=priority,
                    technician_name=technician_name if technician_name else None,
                    technician_email=technician_email if technician_email else None,
                    description=description if description else None,
                    cost_inr=cost_inr if cost_inr > 0 else None,
                    duration_hours=duration_hours if duration_hours > 0 else None,
                    next_maintenance_date=next_maintenance_date,
                    compliance_standard=compliance_standard if compliance_standard else None,
                    created_by=st.session_state.get("user", "system")
                )
                
                st.success(f"✅ Manutenzione pianificata con successo! ID: {maintenance_id}")
                
                # Mostra riepilogo
                st.info(f"""
                **Riepilogo Manutenzione Pianificata:**
                - **Dispositivo:** {selected_device}
                - **Tipo:** {maintenance_type}
                - **Data Programmata:** {scheduled_date}
                - **Scadenza:** {due_date}
                - **Priorità:** {priority}
                - **Tecnico:** {technician_name or 'Non assegnato'}
                """)
                
            except Exception as e:
                st.error(f"❌ Errore durante la pianificazione: {str(e)}")

def show_all_maintenance():
    """Visualizza tutte le manutenzioni con filtri"""
    st.header(" Tutte le Manutenzioni")

    st.write("🔍 Inizio debug...")
    
    try:
        from database import get_all_preventive_maintenance
        st.write("✅ Import OK")
        
        all_maintenance = get_all_preventive_maintenance()
        st.write(f"✅ Query OK - Trovati: {len(all_maintenance)} record")
        
        if all_maintenance:
            st.write(f"✅ Campi per record: {len(all_maintenance[0])}")
            st.write(" Primo record:")
            st.write(all_maintenance[0])
        
    except Exception as e:
        st.error(f"❌ ERRORE: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    # Recupera dati
    all_maintenance = get_all_preventive_maintenance()
    
    if not all_maintenance:
        st.info("📭 Nessuna manutenzione trovata")
        return
    
    # Filtri
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filtro per tipo
        maintenance_types = list(set([m[5] for m in all_maintenance]))
        selected_types = st.multiselect(
            "Filtra per Tipo",
            options=maintenance_types,
            default=maintenance_types
        )
    
    with col2:
        # Filtro per stato
        statuses = list(set([m[9] for m in all_maintenance]))
        selected_statuses = st.multiselect(
            "Filtra per Stato",
            options=statuses,
            default=statuses
        )
    
    with col3:
        # Filtro per priorità
        priorities = list(set([m[10] for m in all_maintenance]))
        selected_priorities = st.multiselect(
            "Filtra per Priorità",
            options=priorities,
            default=priorities
        )
    
    with col4:
        # Filtro per periodo
        date_range = st.date_input(
            "Periodo",
            value=(datetime.now().date() - timedelta(days=90), datetime.now().date()),
            help="Filtra per periodo date programmate"
        )
    
    # Applica filtri
    filtered_maintenance = []
    for m in all_maintenance:
        # Controllo filtri
        if (m[5] in selected_types and 
            m[9] in selected_statuses and 
            m[10] in selected_priorities):
            
            # Controllo periodo
            if len(date_range) == 2:
                maintenance_date = datetime.fromisoformat(str(m[6])).date()
                if date_range[0] <= maintenance_date <= date_range[1]:
                    filtered_maintenance.append(m)
            else:
                filtered_maintenance.append(m)
    
    # Crea DataFrame per visualizzazione
    if filtered_maintenance:
        df_data = []
        for m in filtered_maintenance:
            df_data.append({
                'ID': m[0],
                'Dispositivo': f"{m[2]} - {m[3]} {m[4]}",
                'Tipo': m[5],
                'Data Programmata': m[6],
                'Data Completamento': m[7] if m[7] else 'Non completata',
                'Scadenza': m[8],
                'Stato': m[9],
                'Priorità': m[10],
                'Tecnico': m[11] if m[11] else 'Non assegnato',
                'Costo (₹)': f"₹{m[13]:,.0f}" if m[13] else 'N/A',
                'Durata (h)': f"{m[14]}h" if m[14] else 'N/A'
            })
        
        df = pd.DataFrame(df_data)
        
        # Visualizza tabella
        st.subheader(f"Risultati: {len(filtered_maintenance)} manutenzioni")
        
        # Configurazione editor
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "Stato": st.column_config.SelectboxColumn(
                    "Stato",
                    options=["Scheduled", "In Progress", "Completed", "Overdue", "Cancelled"]
                ),
                "Priorità": st.column_config.SelectboxColumn(
                    "Priorità",
                    options=["Low", "Medium", "High", "Critical"]
                )
            },
            key="maintenance_editor"
        )
        
        # Azioni rapide
        st.subheader("🔧 Azioni Rapide")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Segna come Completata", help="Segna manutenzioni selezionate come completate"):
                st.info("Seleziona le righe da aggiornare nella tabella sopra")
        
        with col2:
            if st.button("⏸️ Metti in Pausa", help="Metti in pausa manutenzioni selezionate"):
                st.info("Funzione disponibile nella prossima versione")
        
        with col3:
            if st.button("❌ Cancella", help="Cancella manutenzioni selezionate"):
                st.info("Seleziona le righe da cancellare")
    
    else:
        st.warning("🔍 Nessuna manutenzione trovata con i filtri selezionati")

def show_maintenance_deadlines():
    """Mostra scadenze e alert manutenzioni"""
    st.header("⏰ Scadenze e Alert")
    
    # Recupera dati scadenze
    overdue = get_overdue_maintenance()
    upcoming_7 = get_upcoming_maintenance(7)
    upcoming_30 = get_upcoming_maintenance(30)
    
    # Alert critici
    if overdue:
        st.error(f"🚨 **SCADUTE**: {len(overdue)} manutenzioni")
        
        # Tabella manutenzioni scadute
        overdue_data = []
        for m in overdue:
            days_overdue = (datetime.now().date() - datetime.fromisoformat(str(m[6])).date()).days
            overdue_data.append({
                'ID': m[0],
                'Dispositivo': f"{m[2]} - {m[3]} {m[4]}",
                'Tipo': m[5],
                'Scadenza': m[6],
                'Giorni di Ritardo': days_overdue,
                'Priorità': m[7],
                'Tecnico': m[8] if m[8] else 'Non assegnato'
            })
        
        df_overdue = pd.DataFrame(overdue_data)
        st.dataframe(df_overdue, use_container_width=True)
    
    # Warning prossime scadenze
    if upcoming_7:
        st.warning(f"⚠️ **URGENTI** (7 giorni): {len(upcoming_7)} manutenzioni")
        
        for m in upcoming_7:
            days_left = (datetime.fromisoformat(str(m[7])).date() - datetime.now().date()).days
            st.markdown(f"""
            <div class="maintenance-card">
                <h4>{m[2]} - {m[3]} {m[4]}</h4>
                <p><strong>Tipo:</strong> {m[5]} | <strong>Scadenza:</strong> {m[7]} ({days_left} giorni) | <strong>Priorità:</strong> {m[8]}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Info prossime 30 giorni
    upcoming_30_not_7 = [m for m in upcoming_30 if m not in upcoming_7]
    if upcoming_30_not_7:
        st.info(f"📅 **PROSSIME** (8-30 giorni): {len(upcoming_30_not_7)} manutenzioni")
        
        # Calendario visuale
        calendar_data = []
        for m in upcoming_30:
            calendar_data.append({
                'Dispositivo': f"{m[2]} - {m[3]}",
                'Tipo': m[5],
                'Data': datetime.fromisoformat(str(m[6])).date(),
                'Scadenza': datetime.fromisoformat(str(m[7])).date(),
                'Priorità': m[8]
            })
        
        if calendar_data:
            df_calendar = pd.DataFrame(calendar_data)
            st.subheader("📅 Vista Calendario")
            st.dataframe(df_calendar, use_container_width=True)

def show_maintenance_reports():
    """Report e analisi manutenzioni"""
    st.header("📈 Report e Analisi")
    
    # Recupera tutti i dati
    all_maintenance = get_all_preventive_maintenance()
    
    if not all_maintenance:
        st.info("📊 Nessun dato disponibile per i report")
        return
    
    # KPI principali
    st.subheader("📊 KPI Principali")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcola metriche
    total_maintenance = len(all_maintenance)
    completed = len([m for m in all_maintenance if m[9] == 'Completed'])
    overdue_count = len(get_overdue_maintenance())
    
    # Costi totali
    total_cost = sum([m[13] for m in all_maintenance if m[13]])
    avg_cost = total_cost / len([m for m in all_maintenance if m[13]]) if [m for m in all_maintenance if m[13]] else 0
    
    with col1:
        completion_rate = (completed / total_maintenance * 100) if total_maintenance > 0 else 0
        st.metric("Tasso Completamento", f"{completion_rate:.1f}%")
    
    with col2:
        st.metric("Costo Totale", f"₹{total_cost:,.0f}")
    
    with col3:
        st.metric("Costo Medio", f"₹{avg_cost:,.0f}")
    
    with col4:
        st.metric("Scadute", overdue_count, delta=f"-{overdue_count}" if overdue_count > 0 else "0")
    
    # Grafici analitici
    col1, col2 = st.columns(2)
    
    with col1:
        # Trend manutenzioni per mese
        monthly_data = {}
        for m in all_maintenance:
            if m[6]:  # scheduled_date
                month_key = datetime.fromisoformat(str(m[6])).strftime('%Y-%m')
                monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
        
        if monthly_data:
            fig = px.line(
                x=list(monthly_data.keys()),
                y=list(monthly_data.values()),
                title="Trend Manutenzioni per Mese",
                markers=True
            )
            fig.update_layout(xaxis_title="Mese", yaxis_title="Numero Manutenzioni")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribuzione per priorità
        priority_count = {}
        for m in all_maintenance:
            priority = m[10]  # priority
            priority_count[priority] = priority_count.get(priority, 0) + 1
        
        if priority_count:
            fig = px.bar(
                x=list(priority_count.keys()),
                y=list(priority_count.values()),
                title="Distribuzione per Priorità",
                color=list(priority_count.values()),
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabella riepilogo per dispositivo
    st.subheader("📋 Riepilogo per Dispositivo")
    
    device_summary = {}
    for m in all_maintenance:
        device_key = f"{m[2]} - {m[3]} {m[4]}"
        if device_key not in device_summary:
            device_summary[device_key] = {
                'Totale': 0,
                'Completate': 0,
                'In Corso': 0,
                'Scadute': 0,
                'Costo Totale': 0
            }
        
        device_summary[device_key]['Totale'] += 1
        
        if m[9] == 'Completed':
            device_summary[device_key]['Completate'] += 1
        elif m[9] in ['Scheduled', 'In Progress']:
            device_summary[device_key]['In Corso'] += 1
        elif m[9] == 'Overdue':
            device_summary[device_key]['Scadute'] += 1
        
        if m[13]:  # cost_inr
            device_summary[device_key]['Costo Totale'] += m[13]
    
    # Converti in DataFrame
    summary_data = []
    for device, stats in device_summary.items():
        completion_rate = (stats['Completate'] / stats['Totale'] * 100) if stats['Totale'] > 0 else 0
        summary_data.append({
            'Dispositivo': device,
            'Totale Manutenzioni': stats['Totale'],
            'Completate': stats['Completate'],
            'In Corso': stats['In Corso'],
            'Scadute': stats['Scadute'],
            'Tasso Completamento (%)': f"{completion_rate:.1f}%",
            'Costo Totale (₹)': f"₹{stats['Costo Totale']:,.0f}"
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True)
    
    # Export dei dati
    st.subheader("💾 Esporta Dati")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Esporta Report Completo"):
            # Crea CSV completo
            export_data = []
            for m in all_maintenance:
                export_data.append({
                    'ID Manutenzione': m[0],
                    'ID Dispositivo': m[1],
                    'Dispositivo': f"{m[2]} - {m[3]} {m[4]}",
                    'Tipo Manutenzione': m[5],
                    'Data Programmata': m[6],
                    'Data Completamento': m[7],
                    'Data Scadenza': m[8],
                    'Stato': m[9],
                    'Priorità': m[10],
                    'Tecnico': m[11],
                    'Descrizione': m[12],
                    'Costo (₹)': m[13],
                    'Durata (ore)': m[14],
                    'Prossima Manutenzione': m[15],
                    'Standard Conformità': m[16],
                    'Data Creazione': m[17]
                })
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            
            st.download_button(
                label="📥 Scarica CSV",
                data=csv,
                file_name=f"maintenance_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📈 Esporta KPI Dashboard"):
            st.info("Funzione di export KPI disponibile nella prossima versione")

if __name__ == "__main__":
    show_preventive_maintenance_page()