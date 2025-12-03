import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import (
    get_all_devices, get_all_breakdowns, get_breakdown_by_id,
    get_open_breakdowns, get_critical_breakdowns, get_breakdown_statistics,
    insert_breakdown, update_breakdown, delete_breakdown, get_breakdowns_by_device, get_device_by_id
)

def show_incidents_corrective_page():
    """
    Incidents & Corrective Maintenance System
    Modern hospital interface with comprehensive breakdown management
    """
    
    # CSS MODERNO PER INTERFACCIA OSPEDALIERA
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
    

    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "View All", "Register New", "Edit/Delete"])
    
    with tab1:
        show_dashboard()
    
    with tab2:
        show_view_all()
    
    with tab3:
        show_register_new()
    
    with tab4:
        show_edit_delete()


def show_dashboard():
    """Dashboard with statistics and visualizations"""
    
    # Get statistics
    stats = get_breakdown_statistics()
    if stats:
        total, open_count, closed, critical = stats
    else:
        total = open_count = closed = critical = 0
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Incidents", total)
    
    with col2:
        st.metric("Open", open_count, delta=f"{open_count} pending", delta_color="inverse")
    
    with col3:
        st.metric("Closed", closed, delta=f"{(closed/total*100) if total > 0 else 0:.1f}% resolved")
    
    with col4:
        st.metric("Critical", critical, delta="Urgent", delta_color="inverse" if critical > 0 else "off")
    
    st.divider()
    
    # Charts
    all_incidents = get_all_breakdowns()
    if all_incidents and len(all_incidents) > 0:
        df = pd.DataFrame(all_incidents, columns=[
            'breakdown_id', 'device_id', 'description', 'brand', 'model',
            'nature_of_complaint', 'called_by', 'call_received_date', 'call_received_time',
            'attended_by', 'attended_date', 'time_of_attendance', 'action_taken',
            'rectified_date', 'rectified_time', 'call_priority', 'remark', 'type_of_service'
        ])
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            priority_counts = df['call_priority'].value_counts()
            fig = px.pie(
                title='Priority Distribution',
                values=priority_counts.values,
                names=priority_counts.index,
                color=priority_counts.index,
                color_discrete_map={
                    'Critical': '#7f1d1d',
                    'High': '#dc2626',
                    'Medium': '#f59e0b',
                    'Low': '#3b82f6'
                },
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            df['status'] = df['rectified_date'].apply(lambda x: 'Closed' if pd.notna(x) else 'Open')
            status_counts = df['status'].value_counts()
            fig = px.bar(
                title='Status Distribution',
                x=status_counts.index,
                y=status_counts.values,
                color=status_counts.index,
                color_discrete_map={'Open': '#ef4444', 'Closed': '#22c55e'},
                labels={'x': 'Status', 'y': 'Count'}
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Timeline chart
        df['call_received_date'] = pd.to_datetime(df['call_received_date'])
        timeline_data = df.groupby(df['call_received_date'].dt.to_period('M')).size().reset_index()
        timeline_data.columns = ['Month', 'Count']
        timeline_data['Month'] = timeline_data['Month'].astype(str)
        
        fig = px.line(
            timeline_data,
            x='Month',
            y='Count',
            markers=True,
            title= 'Monthly Incident Trend',
            
           
        )
        fig.update_traces(line_color='#ef4444', line_width=3, marker=dict(size=10, color='#dc2626'))
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 No incidents data available for visualization")


def show_view_all():
    """View all incidents with filters"""
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox("Status", ["All", "Open", "Closed"])
    
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"])
    
    with col3:
        # Get unique devices
        devices = get_all_devices()
        device_options = ["All"] + [f"{d[3]} - {d[8]} {d[9]}" for d in devices if len(d) > 9]
        device_filter = st.selectbox("Device", device_options)
    
    with col4:
        date_filter = st.date_input("From Date", value=None, help="Filter incidents from this date")
    
    # Get all incidents
    all_incidents = get_all_breakdowns()
    
    if not all_incidents:
        st.warning("No incidents found")
        return
    
    # Apply filters
    filtered_incidents = []
    for incident in all_incidents:
        # Status filter
        if status_filter == "Open" and incident[13] is not None:
            continue
        if status_filter == "Closed" and incident[13] is None:
            continue
        
        # Priority filter
        if priority_filter != "All" and incident[15] != priority_filter:
            continue
        
        # Device filter
        if device_filter != "All":
            device_desc = device_filter.split(" - ")[0]
            if incident[2] != device_desc:
                continue
        
        # Date filter
        if date_filter and incident[7]:
            if incident[7] < date_filter:
                continue
        
        filtered_incidents.append(incident)
    
    if not filtered_incidents:
        st.warning("🔍 No incidents found with selected filters")
        return
    
    # Create DataFrame for display
    df_data = []
    for inc in filtered_incidents:
        status = "Closed" if inc[13] else "Open"
        device_name = f"{inc[2] or 'Unknown'} {inc[3] or ''} {inc[4] or ''}".strip()
        
        # Calculate days since call
        days_since = (datetime.now().date() - inc[7]).days if inc[7] else 0
        
        # Calculate resolution time if closed
        resolution_time = ""
        if inc[13] and inc[7]:
            days = (inc[13] - inc[7]).days
            resolution_time = f"{days} days"
        
        # Handle complaint text safely
        complaint_text = inc[5] if inc[5] else "No description"
        complaint_display = complaint_text[:50] + "..." if len(complaint_text) > 50 else complaint_text
        
        x = get_device_by_id(inc[1])
        
        df_data.append({
            'Device': device_name,
            'Serial number': x[12] if x else 'Unknown',
            'Complaint': complaint_display,
            'Called By': inc[6] if inc[6] else 'Unknown',
            'Call Date': inc[7] if inc[7] else None,
            'Call Time': str(inc[8]) if len(inc) > 8 and inc[8] else 'N/A',  # ✅ Converti in stringa
            'Days Since': days_since,
            'Priority': inc[15] if inc[15] else 'Unknown',
            'Status': status,
            'Service Type': inc[17] if len(inc) > 17 and inc[17] else 'N/A',
            'Attended By': inc[9] if inc[9] else 'Unassigned',
            'Attended Date': inc[10] if len(inc) > 10 and inc[10] else None,  # ✅ Lascia come date
            'Attended Time': str(inc[11]) if len(inc) > 11 and inc[11] else 'N/A',  # ✅ Converti in stringa
            'Action Taken': (inc[12][:50] + '...' if inc[12] and len(str(inc[12])) > 50 else inc[12]) if len(inc) > 12 else 'N/A',
            'Rectified Date': inc[13] if inc[13] else None,  # ✅ Lascia come date
            'Rectified Time': str(inc[14]) if len(inc) > 14 and inc[14] else 'N/A',  # ✅ Converti in stringa
            'Remark': (inc[16][:50] + '...' if inc[16] and len(str(inc[16])) > 50 else inc[16]) if len(inc) > 16 else 'N/A',
            'Resolution Time': resolution_time if resolution_time else 'N/A'
        })
    
    df = pd.DataFrame(df_data)
    
    # ✅ Funzione per colorare le righe in base allo status
    def color_rows(row):
        days = row['Status']
        
        if days =='Open':
            color = 'background-color: #ffe6e6'  # Rosso - Scaduto
        else:
            color = 'background-color: #e6ffe6'  # Giallo - Urgente (0-7 giorni)
        
        # Applica il colore SOLO alla colonna Days
        return [color if col == 'Status' else '' for col in row.index]
    
    # Applica lo stile
    styled_df = df.style.apply(color_rows, axis=1)
    
    # Display table
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Device": st.column_config.TextColumn(
                "Device",
                help="Device information",
                width="medium"
            ),
            "Serial number": st.column_config.TextColumn(
                "Serial number",
                help="Device serial number",
                width="small"
            ),
            "Complaint": st.column_config.TextColumn(
                "Complaint",
                help="Nature of complaint (truncated)",
                width="large"
            ),
            "Called By": st.column_config.TextColumn(
                "Called By",
                help="Person who called",
                width="small"
            ),
            "Call Date": st.column_config.DateColumn(
                "Call Date",
                help="Date call was received",
                width="small"
            ),
            "Call Time": st.column_config.TextColumn(
                "Call Time",
                help="Time call was received",
                width="small"
            ),
            "Days Since": st.column_config.NumberColumn(
                "Days Since",
                help="Days since call",
                width="small"
            ),
            "Priority": st.column_config.TextColumn(
                "Priority",
                help="Priority level",
                width="small"
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                help="Open or Closed",
                width="small"
            ),
            "Service Type": st.column_config.TextColumn(
                "Service Type",
                help="Type of service",
                width="small"
            ),
            "Attended By": st.column_config.TextColumn(
                "Attended By",
                help="Technician who attended",
                width="small"
            ),
            "Attended Date": st.column_config.DateColumn(
                "Attended Date",
                help="Date attended",
                width="small"
            ),
            "Attended Time": st.column_config.TextColumn(
                "Attended Time",
                help="Time of attendance",
                width="small"
            ),
            "Action Taken": st.column_config.TextColumn(
                "Action Taken",
                help="Action taken (truncated)",
                width="medium"
            ),
            "Rectified Date": st.column_config.DateColumn(
                "Rectified Date",
                help="Date rectified",
                width="small"
            ),
            "Rectified Time": st.column_config.TextColumn(
                "Rectified Time",
                help="Time rectified",
                width="small"
            ),
            "Remark": st.column_config.TextColumn(
                "Remark",
                help="Additional remarks (truncated)",
                width="medium"
            ),
            "Resolution Time": st.column_config.TextColumn(
                "Resolution Time",
                help="Time taken to resolve",
                width="small"
            )
        }
    )
def show_register_new():
    """Register new incident"""
    
    # Get all devices
    devices = get_all_devices()
    if not devices:
        st.error("❌ No devices found. Please add devices first.")
        return
    
    device_options = {f"{d[1]} - {d[2]} {d[3]}": d[0] for d in devices}
    
    with st.form("new_incident_form"):
        st.markdown("#### Device Information")
        selected_device = st.selectbox("Select Device *", options=list(device_options.keys()))
        
        st.markdown("#### 📞 Call Information")
        col1, col2 = st.columns(2)
        with col1:
            called_by = st.text_input("Called By *", placeholder="Name of person who called")
            call_date = st.date_input("Call Received Date *", value=datetime.now().date())
        with col2:
            call_priority = st.selectbox("Priority *", ["Low", "Medium", "High", "Critical"])
            call_time = st.time_input("Call Received Time *", value=datetime.now().time())
        
        nature_of_complaint = st.text_area(
            "Nature of Complaint *",
            placeholder="Describe the issue...",
            height=100
        )
        
        st.markdown("#### Attendance Information")
        col3, col4 = st.columns(2)
        with col3:
            attended_by = st.text_input("Attended By", placeholder="Technician name")
            attended_date = st.date_input("Attended Date", value=None)
        with col4:
            time_of_attendance = st.time_input("Time of Attendance", value=None)
        
        action_taken = st.text_area(
            "Action Taken",
            placeholder="Describe the action taken...",
            height=100
        )
        
        st.markdown("#### Rectification Information")
        col5, col6 = st.columns(2)
        with col5:
            rectified_date = st.date_input("Rectified Date", value=None)
        with col6:
            rectified_time = st.time_input("Rectified Time", value=None)
        
        st.markdown("#### Additional Information")
        type_of_service = st.text_input("Type of Service", placeholder="e.g., Emergency, Scheduled")
        remark = st.text_area("Remarks", placeholder="Additional notes...", height=80)
        
        submitted = st.form_submit_button("Register Incident", use_container_width=True)
        
        if submitted:
            # Validation
            if not called_by or not nature_of_complaint:
                st.error("❌ Please fill in all required fields (*)")
            else:
                try:
                    device_id = device_options[selected_device]
                    
                    # Insert breakdown
                    breakdown_id = insert_breakdown(
                        device_id=device_id,
                        nature_of_complaint=nature_of_complaint,
                        called_by=called_by,
                        call_received_date=call_date,
                        call_received_time=call_time,
                        attended_by=attended_by if attended_by else None,
                        attended_date=attended_date if attended_date else None,
                        time_of_attendance=time_of_attendance if time_of_attendance else None,
                        action_taken=action_taken if action_taken else None,
                        rectified_date=rectified_date if rectified_date else None,
                        rectified_time=rectified_time if rectified_time else None,
                        call_priority=call_priority,
                        remark=remark if remark else None,
                        type_of_service=type_of_service if type_of_service else None
                    )
                    
                    st.success(f"✅ Incident registered successfully! ID: #{breakdown_id}")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error registering incident: {str(e)}")


def show_edit_delete():
    """Edit or delete incidents"""
    
    # Get all incidents
    all_incidents = get_all_breakdowns()
    
    if not all_incidents:
        st.warning("No incidents found")
        return
    
    # Create incident selector
    incident_options = {
        f"{inc[2]} - {inc[3]} {inc[4]} | {inc[7]}": inc[0]
        for inc in all_incidents
    }
    
    selected_incident = st.selectbox("Select Incident", options=list(incident_options.keys()))
    breakdown_id = incident_options[selected_incident]
    
    # Get incident details
    incident = get_breakdown_by_id(breakdown_id)
    
    if not incident:
        st.error("❌ Incident not found")
        return
    
    # Show current details
    st.markdown("#### Current Details")
    col1, col2 = st.columns(2)
    
    with col1:
        device_name = f"{incident[2]} - {incident[3]} {incident[4]}"
        status = "Closed" if incident[13] else "Open"
        st.info(f"**Device:** {device_name}")
        st.info(f"**Status:** {status}")
        st.info(f"**Priority:** {incident[15]}")
    
    with col2:
        st.info(f"**Called by:** {incident[6]}")
        st.info(f"**Call Date:** {incident[7]}")
        st.info(f"**Attended by:** {incident[9] or 'Not attended'}")
    
    st.divider()
    
    # Edit form
    st.markdown("#### Edit Incident")
    
    # Get all devices
    devices = get_all_devices()
    device_options = {f"{d[1]} - {d[2]} {d[3]}": d[0] for d in devices}
    
    # Find current device index
    current_device = f"{incident[2]} - {incident[3]} {incident[4]}"
    device_list = list(device_options.keys())
    current_device_idx = device_list.index(current_device) if current_device in device_list else 0
    
    with st.form("edit_incident_form"):
        st.markdown("##### Device Information")
        selected_device = st.selectbox("Device *", options=device_list, index=current_device_idx)
        
        st.markdown("##### 📞 Call Information")
        col1, col2 = st.columns(2)
        with col1:
            called_by = st.text_input("Called By *", value=incident[6] or "")
            call_date = st.date_input("Call Date *", value=incident[7] if incident[7] else datetime.now().date())
        with col2:
            priority_options = ["Low", "Medium", "High", "Critical"]
            priority_idx = priority_options.index(incident[15]) if incident[15] in priority_options else 0
            call_priority = st.selectbox("Priority *", options=priority_options, index=priority_idx)
            call_time = st.time_input("Call Time *", value=incident[8] if incident[8] else datetime.now().time())
        
        nature_of_complaint = st.text_area("Nature of Complaint *", value=incident[5] or "", height=100)
        
        st.markdown("##### Attendance Information")
        col3, col4 = st.columns(2)
        with col3:
            attended_by = st.text_input("Attended By", value=incident[9] or "")
            attended_date = st.date_input("Attended Date", value=incident[10] if incident[10] else None)
        with col4:
            time_of_attendance = st.time_input("Time of Attendance", value=incident[11] if incident[11] else None)
        
        action_taken = st.text_area("Action Taken", value=incident[12] or "", height=100)
        
        st.markdown("##### Rectification Information")
        col5, col6 = st.columns(2)
        with col5:
            rectified_date = st.date_input("Rectified Date", value=incident[13] if incident[13] else None)
        with col6:
            rectified_time = st.time_input("Rectified Time", value=incident[14] if incident[14] else None)
        
        st.markdown("##### Additional Information")
        type_of_service = st.text_input("Type of Service", value=incident[17] or "")
        remark = st.text_area("Remarks", value=incident[16] or "", height=80)
        
      

        update_btn = st.form_submit_button("Update Incident", use_container_width=True)
        
        
        if update_btn:
            if not called_by or not nature_of_complaint:
                st.error("❌ Please fill in all required fields (*)")
            else:
                try:
                    device_id = device_options[selected_device]
                    
                    update_breakdown(
                        breakdown_id=breakdown_id,
                        device_id=device_id,
                        nature_of_complaint=nature_of_complaint,
                        called_by=called_by,
                        call_received_date=call_date,
                        call_received_time=call_time,
                        attended_by=attended_by if attended_by else None,
                        attended_date=attended_date if attended_date else None,
                        time_of_attendance=time_of_attendance if time_of_attendance else None,
                        action_taken=action_taken if action_taken else None,
                        rectified_date=rectified_date if rectified_date else None,
                        rectified_time=rectified_time if rectified_time else None,
                        call_priority=call_priority,
                        remark=remark if remark else None,
                        type_of_service=type_of_service if type_of_service else None
                    )
                    
                    st.success("✅ Incident updated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error updating incident: {str(e)}")
    col1, col2 = st.columns([1, 5])
    with col1:
        delete_btn = st.button("Delete Maintenance", type="primary", use_container_width=True)
    
    if delete_btn:
        success = delete_breakdown(breakdown_id)
        if success:
            st.success(f"✅ Incident deleted successfully!")
            st.rerun()
        else:
            st.error("❌ Failed to delete incident")    

