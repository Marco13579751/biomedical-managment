from asyncio.windows_events import NULL
from math import floor
import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pandas as pd
import datetime
import psycopg2
import bcrypt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.express as px
import plotly.graph_objects as go


# --- Configurazione pagina ---
st.set_page_config(
    page_title="Medical Device Dashboard",
    page_icon="🏥",
    layout="wide"
)

# --- Connessione PostgreSQL ---
conn = psycopg2.connect(
    dbname="blood_bank",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# --- Stato utente ---
if "user" not in st.session_state:
    st.session_state["user"] = None

# --- Funzioni DB Utenti ---
def db_signin(email, password):
    cur.execute("SELECT password_hash, approved FROM utenti_autorizzati WHERE email=%s", (email,))
    row = cur.fetchone()
    if row is None:
        return {"error": "USER_NOT_FOUND"}
    pw_hash, approved = row
    if not bcrypt.checkpw(password.encode(), pw_hash.encode()):
        return {"error": "INVALID_PASSWORD"}
    return {"email": email, "approved": approved}

def db_register(email, password):
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        cur.execute("INSERT INTO utenti_autorizzati (email, password_hash) VALUES (%s, %s)", (email, pw_hash))
        conn.commit()
        return {"email": email, "approved": False}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"error": "USER_EXISTS"}

def approve_user(email):
    cur.execute("UPDATE utenti_autorizzati SET approved=TRUE WHERE email=%s", (email,))
    conn.commit()

def get_all_users():
    cur.execute("SELECT email, approved FROM utenti_autorizzati")
    return cur.fetchall()

def log_action(user_id, action, target_table, target_id=None):
    cur.execute("""
        INSERT INTO audit_log (user_id, action, target_table, target_id)
        VALUES (%s, %s, %s, %s)
    """, (user_id, action, target_table, target_id))
    conn.commit()


# --- UI Autenticazione ---
if st.session_state["user"] is None:
    st.title("Login / Registration")

    mode = st.radio("Select modality", ["Login", "Registration"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Login":
        if st.button("Login"):
            result = db_signin(email, password)
            if "error" in result:
                st.error(f"Errore: {result['error']}")
            else:
                if not result["approved"]:
                    st.error("⛔ Utente non approvato. Attendere approvazione admin.")
                else:
                    st.session_state["user"] = email
                    st.success("✅ Accesso effettuato")
                    st.rerun()
    else:
        if st.button("Register"):
            result = db_register(email, password)
            if "error" in result:
                st.error(f"Errore: {result['error']}")
            else:
                st.success("✅ Registrazione completata. Attendere approvazione admin.")

    st.stop()

# --- Sidebar Navigation ---
st.sidebar.title("Medical Device Dashboard")
st.sidebar.markdown(f"**Logged in as:** {st.session_state['user']}")

# Logout button in sidebar
if st.sidebar.button("Logout", type="secondary"):
    st.session_state["user"] = None
    st.rerun()

# Navigation menu
page = st.sidebar.radio(
    "Navigate to:",
    ["Devices","Prioritization Score","Wards/Rooms", "Maintenance Management", "Admin Panel"]
)

# --- Funzioni DB Dispositivi ---
def insert_device(nome, normalized_age, eq_function, cost_levels,cumulative_maintenance, failure_rate, up_time, stanza=None):
    cur.execute("""
        INSERT INTO dispositivi (nome, normalized_age, eq_function, cost_levels, cumulative_maintenance, failure_rate, up_time, stanza)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (nome, normalized_age, eq_function, cost_levels,cumulative_maintenance, failure_rate, up_time, stanza))
    conn.commit()

def insert_ward(ward_name):
    """Inserisce un nuovo ward"""
    cur.execute("""
        INSERT INTO ward (ward_name)
        VALUES (%s)
        RETURNING ward_id
    """, (ward_name,))
    ward_id = cur.fetchone()[0]
    conn.commit()
    return ward_id

def insert_room(floor_id, room_name, ward_id):
    """Inserisce un nuovo room"""
    cur.execute("""
        INSERT INTO room (floor_id,room_name, ward_id)
        VALUES (%s,%s, %s)
        RETURNING ward_id
    """, (floor_id, room_name, ward_id))
    room_id = cur.fetchone()[0]
    conn.commit()
    return room_id

def insert_medical_device(description, room_id, device_class, usage_type, cost_inr, 
                         brand, model, installation_date, serial_number, manufacturer_date,udi_number):
    """Inserisce un nuovo dispositivo medico"""
    cur.execute("""
        INSERT INTO Medical_Device (Room_ID, Description, Class, Usage_Type, 
                                  Cost_INR, Present, Brand, Model, Installation_Date, serial_number, manufacturer_date, udi_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING Device_ID
    """, (room_id, description, device_class, usage_type, cost_inr, 
          True, brand, model, installation_date, serial_number, manufacturer_date, udi_number))
    device_id = cur.fetchone()[0]
    conn.commit()
    return device_id
def insert_scoring_parameters(device_id,assessment_date,spare_parts_available,age_years,backup_device_available,
                          failure_rate,downtime_hours,cost_ratio,uptime_percentage,equipment_function_score,vulnerabilities_present,notes,end_of_life,end_of_support,mis_score,supp_score, criticity):
    """Inserisce parametri obsolescenza """
    cur.execute("""
        INSERT INTO scoring_parameters (device_id,assessment_date,spare_parts_available,age_years,backup_device_available,failure_rate,downtime_hours,cost_ratio,uptime_percentage,equipment_function_score,vulnerabilities_present,notes,end_of_life,end_of_support ,mis_score,supp_score, criticity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )
        RETURNING parameter_id
    """, (device_id,assessment_date,spare_parts_available,age_years,backup_device_available,
          failure_rate,downtime_hours,cost_ratio,uptime_percentage,equipment_function_score,vulnerabilities_present,notes,end_of_life,end_of_support,mis_score,supp_score, criticity ))
    parameter_id = cur.fetchone()[0]
    conn.commit()
    return parameter_id


def delete_scoring_parameters(device_id):
    cur.execute("""
            DELETE FROM scoring_parameters 
            WHERE device_id = %s
            RETURNING device_id
        """, (device_id,))
    conn.commit()

def delete_wards(ward_id):
    cur.execute("""
            DELETE FROM ward
            WHERE ward_id = %s
            RETURNING ward_id
        """, (ward_id,))

    deleted = cur.fetchone()  # prende la riga eliminata, se c'è
    conn.commit()

    return deleted is not None

def delete_room(room_id):
    cur.execute("""
        DELETE FROM room
        WHERE room_id = %s
        RETURNING room_id
    """, (room_id,))
    
    deleted = cur.fetchone()  # prende la riga eliminata, se c'è
    conn.commit()
    
    return deleted is not None  # True se almeno una riga è stata eliminata

def get_all_devices():
    cur.execute("SELECT * FROM medical_device ORDER BY device_id")
    return cur.fetchall()

def get_all_wards():
    """Recupera tutti  i ward"""
    cur.execute("SELECT ward_id, ward_name FROM ward")
    return cur.fetchall()

def get_all_rooms():
    """Recupera tutte le stanze"""
    cur.execute("SELECT Room_ID, Floor_ID, room_name, ward_id FROM Room ORDER BY Room_ID, Floor_ID")
    return cur.fetchall()

def get_all_scores():
    cur.execute("SELECT * FROM scoring_parameters")
    return cur.fetchall()

def get_ward_name_by_device(device_id):
    cur.execute("""
        SELECT w.ward_name
        FROM medical_device d
        JOIN room r ON d.room_id = r.room_id
        JOIN ward w ON r.ward_id = w.ward_id
        WHERE d.device_id = %s
    """, (device_id,))
    result = cur.fetchone()
    return result[0] if result else None

def update_criticity(dev_id, criticity_score):
    criticity_score = float(criticity_score)
    try:
        cur.execute("""
            UPDATE dispositivi
            SET criticity = %s
            WHERE id = %s
        """, (criticity_score, dev_id))
        conn.commit()
    except psycopg2.errors.DatatypeMismatch:
        conn.rollback()
        cur.execute("""
            UPDATE dispositivi
            SET criticity = %s
            WHERE id = %s
        """, ([criticity_score], dev_id))
        conn.commit()

def update_device(Device_ID, Description, Class, Usage_Type, Cost_INR, Brand, Model, Installation_Date, serial_number, manufacturer_date, udi_number, present):
    cur.execute("""
        UPDATE medical_device 
        SET description=%s, class=%s, usage_type=%s, cost_inr=%s, Brand=%s, Model=%s, installation_date=%s, serial_number=%s, manufacturer_date=%s, udi_number=%s, present=%s
        WHERE device_id=%s
    """, (Description, Class, Usage_Type, Cost_INR, Brand, Model, Installation_Date, serial_number, manufacturer_date, udi_number, present, Device_ID))
    conn.commit()
def get_device_by_id(dev_id):
    cur.execute("SELECT device_id, parent_id, room_id, description, class, usage_type, cost_inr, present, brand, model, installation_date, udi_number, serial_number, manufacturer_date FROM medical_device WHERE Device_ID=%s", (dev_id,))
    return cur.fetchone()

def get_scores_by_device_id(dev_id):
    cur.execute("SELECT * FROM scoring_parameters WHERE device_id=%s", (dev_id,))
    return cur.fetchone()

def delete_device(dev_id):
    cur.execute("DELETE FROM medical_device WHERE device_id = %s", (dev_id,))
    conn.commit()

def calculate_all_devices_scores():
    """
    Calcola i punteggi fuzzy per tutti i dispositivi che hanno parametri completi
    """
    try:
        # Ottieni tutti i dispositivi
        all_devices = get_all_devices()
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        error_details = []
        
        # Setup del sistema fuzzy
        setup_fuzzy_system()
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, device in enumerate(all_devices):
            device_id = device[0]
            cost_inr = device[6]  # Costo del dispositivo
            install_date = device[10]  # Data installazione
            
            try:
                # Aggiorna progress bar
                progress = (i + 1) / len(all_devices)
                progress_bar.progress(progress)
                status_text.text(f'Processing Device ID: {device_id} ({i+1}/{len(all_devices)})')
                
                # Recupera i parametri esistenti
                existing_params = get_scores_by_device_id(device_id)
                
                # Controlla se esistono tutti i parametri necessari
                if not existing_params or len(existing_params) < 14:
                    skipped_count += 1
                    continue
                
                # Estrai i parametri necessari
                spare_parts_available = existing_params[3]
                backup_device_available = existing_params[5]
                cost_ratio = existing_params[8]
                uptime_percentage = existing_params[9]
                equipment_function_score = existing_params[10]
                notes = existing_params[12]
                end_of_life_numeric = existing_params[13]
                
                # Calcola età del dispositivo
                today = dt.date.today()
                age_years = (today - install_date).days / 365
                
                # Parametri fissi per il calcolo
                failure_rate = 0
                end_of_support_numeric = 0
                
                # Calcola il costo normalizzato
                if cost_inr and cost_inr > 0:
                    cost = (float(cost_ratio) / float(cost_inr)) * 100
                else:
                    cost = 1.0
                
                # Controlla che tutti i parametri necessari siano validi
                required_params = [
                    spare_parts_available, backup_device_available, cost_ratio,
                    uptime_percentage, equipment_function_score, end_of_life_numeric
                ]
                
                if any(param is None for param in required_params):
                    skipped_count += 1
                    continue
                
                # Calcola i punteggi fuzzy
                mis_score, supp_score, crit_score = calculate_fuzzy_scores(
                    age_years,                    # normalized_age
                    equipment_function_score,     # eq_function
                    cost,                        # cost_levels
                    failure_rate,                # failure_rate
                    uptime_percentage,           # up_time
                    end_of_life_numeric,         # end_life
                    end_of_support_numeric,      # end_support
                    spare_parts_available,       # import_availability
                    backup_device_available      # backup
                )
                
                # Verifica che i punteggi siano validi
                if mis_score is None or supp_score is None or crit_score is None:
                    error_count += 1
                    error_details.append(f"Device {device_id}: Invalid fuzzy scores calculated")
                    continue
                
                # Aggiorna i punteggi nel database
                # Elimina i parametri esistenti e inserisci quelli nuovi con i punteggi aggiornati
                delete_scoring_parameters(device_id)
                
                assessment_date = dt.date.today()
                n_failure = 0
                
                
                insert_scoring_parameters(
                    device_id, assessment_date, spare_parts_available, age_years, 
                    backup_device_available, n_failure, 0, cost_ratio, uptime_percentage, 
                    equipment_function_score, 0, notes, end_of_life_numeric, False, 
                    mis_score, supp_score, crit_score
                )
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_details.append(f"Device {device_id}: {str(e)}")
                continue
        
        # Pulisci la progress bar
        progress_bar.empty()
        status_text.empty()
        
        # Mostra i risultati
        st.success(f"✅ Calculation completed!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Successfully Updated", success_count, delta=None)
        with col2:
            st.metric("Skipped (Missing Params)", skipped_count, delta=None)
        with col3:
            st.metric("Errors", error_count, delta=None)
        
        # Mostra dettagli errori se ci sono
        if error_details:
            st.error("Error Details:")
            for error in error_details[:10]:  # Mostra solo i primi 10 errori
                st.text(error)
            if len(error_details) > 10:
                st.text(f"... and {len(error_details) - 10} more errors")
        
        if skipped_count > 0:
            st.warning(f"{skipped_count} devices were skipped because they don't have complete scoring parameters. Use the 'Add score parameters' tab to set them up first.")
        
    except Exception as e:
        st.error(f"❌ Error during bulk calculation: {str(e)}")
# --- Setup Fuzzy Logic ---
def setup_fuzzy_system():
    #end_support=ctrl.Antecedent(np.arange(0,4,0.1), 'end_support')
    end_life = ctrl.Antecedent(np.arange(0, 3, 0.5), 'end_life')
    import_availability=ctrl.Antecedent(np.arange(0,6,0.1),'import_availability')
    normalized_age = ctrl.Antecedent(np.arange(0, 16, 0.1), 'normalized_age')
    #failure_rate = ctrl.Antecedent(np.arange(0, 10, 0.01), 'failure_rate')
    backup=ctrl.Antecedent(np.arange(0,7,1), 'backup')
    eq_function = ctrl.Antecedent(np.arange(0, 5, 0.01), 'eq_function')
    up_time = ctrl.Antecedent(np.arange(0, 36, 0.01), 'up_time')
    cost_levels = ctrl.Antecedent(np.arange(0, 201, 0.5), 'cost_levels')
    support=ctrl.Consequent(np.arange(0,10.1,0.01),'support')
    reliability = ctrl.Consequent(np.arange(0, 10.1, 0.01), 'reliability')
    mission = ctrl.Consequent(np.arange(0, 10.1, 0.01), 'mission')
    support_result=ctrl.Antecedent(np.arange(0,10.1,0.01),'support_result')
    reliability_result = ctrl.Antecedent(np.arange(0, 10.1, 0.01), 'reliability_result')
    mission_result = ctrl.Antecedent(np.arange(0, 10.1, 0.01), 'mission_result')
    criticity = ctrl.Consequent(np.arange(0, 10.1, 0.01), 'criticity')

    # Membership functions
    #end_support['Support']=fuzz.trimf(end_support.universe,[0,0,0.5])
    #end_support['End']=fuzz.trimf(end_support.universe,[0,1,2])
    end_life['Life'] = fuzz.trimf(end_life.universe, [0, 0, 0.5])
    end_life['End'] = fuzz.trimf(end_life.universe, [0.5, 1, 1.5])
    end_life['End of support and end of life']= fuzz.trimf(end_life.universe, [1.5,2,2.5])
    import_availability['Local production and availability of spare parts']=fuzz.trimf(import_availability.universe,[0.1,1,1.9])
    import_availability['Import and availability of spare parts']=fuzz.trimf(import_availability.universe,[1.1,2,2.9])
    import_availability['Local production and NO availability of spare parts']=fuzz.trimf(import_availability.universe,[2.1,3,3.9])
    import_availability['Import and NO availability of spare parts']=fuzz.trimf(import_availability.universe,[3.1,4,4.9])
    #normalized_age['New'] = fuzz.trapmf(normalized_age.universe, [0, 0, 2, 5])
    #normalized_age['Middle'] = fuzz.trimf(normalized_age.universe, [3, 5, 7])
    #normalized_age['Old'] = fuzz.trapmf(normalized_age.universe, [5, 8, 10, 10])
    normalized_age['New'] = fuzz.gaussmf(normalized_age.universe, mean=2, sigma=1.0)
    normalized_age['Middle'] = fuzz.gaussmf(normalized_age.universe, mean=5.5, sigma=1.2)
    normalized_age['Old'] = fuzz.gaussmf(normalized_age.universe, mean=10, sigma=2.0)
    #failure_rate['Low'] = fuzz.trapmf(failure_rate.universe, [0, 0, 0.1, 0.3])
    #failure_rate['Medium'] = fuzz.trimf(failure_rate.universe, [0.2, 0.75, 1.5])
    #failure_rate['High']= fuzz.trapmf(failure_rate.universe, [1.0, 2.0, 10, 10])
    backup['0'] = fuzz.trimf(backup.universe, [0, 0, 0.5])
    backup['1-2'] = fuzz.trapmf(backup.universe, [0.5, 1, 2, 2.5])
    backup['>=3']= fuzz.trapmf(backup.universe, [2.5, 3, 6, 6])
    eq_function['Analytical/Support'] = fuzz.gaussmf(eq_function.universe, 1, 0.1)
    eq_function['Diagnostic'] = fuzz.gaussmf(eq_function.universe, 2, 0.1)
    eq_function['Therapeutic'] = fuzz.gaussmf(eq_function.universe, 3, 0.1)
    eq_function['Life saving/Life support']= fuzz.gaussmf(eq_function.universe,4,0.1)
    up_time['Low'] = fuzz.trapmf(up_time.universe, [0, 0, 8, 16])
    up_time['Middle'] = fuzz.trimf(up_time.universe, [8, 18, 28])
    up_time['High'] = fuzz.trapmf(up_time.universe, [20, 28, 36, 36])
    cost_levels['Low'] = fuzz.trapmf(cost_levels.universe, [0, 0, 3, 5])
    cost_levels['Medium'] = fuzz.trimf(cost_levels.universe, [4, 20, 50])
    cost_levels['High'] = fuzz.trapmf(cost_levels.universe, [40, 50, 200,200])
    support['Low'] = fuzz.trapmf(support.universe, [0, 0, 2, 5])
    support['Medium'] = fuzz.trimf(support.universe, [3, 5, 7])
    support['High'] = fuzz.trapmf(support.universe, [5, 8, 10, 10])
    support_result['Low'] = fuzz.trapmf(support_result.universe, [0, 0, 2, 5])
    support_result['Medium'] = fuzz.trimf(support_result.universe, [3, 5, 7])
    support_result['High'] = fuzz.trapmf(support_result.universe, [5, 8, 10, 10])
    #reliability['Low'] = fuzz.trapmf(reliability.universe, [0, 0, 2, 5])
    #reliability['Medium'] = fuzz.trimf(reliability.universe, [3, 5, 7])
    #reliability['High'] = fuzz.trapmf(reliability.universe, [5, 8, 10, 10])
    #reliability_result['Low'] = fuzz.trapmf(reliability_result.universe, [0, 0, 2, 5])
    #reliability_result['Medium'] = fuzz.trimf(reliability_result.universe, [3, 5, 7])
    #reliability_result['High'] = fuzz.trapmf(reliability_result.universe, [5, 8, 10, 10])
    mission['Low'] = fuzz.trapmf(mission.universe, [0, 0, 2, 5])
    mission['Medium'] = fuzz.trimf(mission.universe, [3, 5, 7])
    mission['High'] = fuzz.trapmf(mission.universe, [5, 8, 10, 10])
    mission_result['Low'] = fuzz.trapmf(mission_result.universe, [0, 0, 2, 5])
    mission_result['Medium'] = fuzz.trimf(mission_result.universe, [3, 5, 7])
    mission_result['High'] = fuzz.trapmf(mission_result.universe, [5, 8, 10, 10])
    criticity['VeryLow'] = fuzz.gaussmf(criticity.universe, 1, 0.7)
    criticity['Low'] = fuzz.gaussmf(criticity.universe, 3, 0.7)
    criticity['Medium'] = fuzz.gaussmf(criticity.universe, 5, 0.7)
    criticity['High'] = fuzz.gaussmf(criticity.universe, 7, 0.7)
    criticity['VeryHigh'] = fuzz.gaussmf(criticity.universe, 9, 0.7)

    # Define fuzzy rules
    rule_s = [
        ## === GRUPPO 1: end_support & end_life (4 regole) ===
        #ctrl.Rule(end_support['Support'] & end_life['Life'], support['High']),
        #ctrl.Rule(end_support['End'] & end_life['Life'], support['Medium']),
        #ctrl.Rule(end_support['End'] & end_life['End'], support['Low']),

        ## === GRUPPO 2: end_support & import_availability (8 regole) ===
        #ctrl.Rule(end_support['Support'] & import_availability['Local production and availability of spare parts'], support['High']),
        #ctrl.Rule(end_support['Support'] & import_availability['Local production and NO availability of spare parts'], support['Low']),
        #ctrl.Rule(end_support['Support'] & import_availability['Import and availability of spare parts'], support['Medium']),
        #ctrl.Rule(end_support['Support'] & import_availability['Import and NO availability of spare parts'], support['Low']),

        #ctrl.Rule(end_support['End'] & import_availability['Local production and availability of spare parts'], support['Medium']),
        #ctrl.Rule(end_support['End'] & import_availability['Local production and NO availability of spare parts'], support['Low']),
        #ctrl.Rule(end_support['End'] & import_availability['Import and availability of spare parts'], support['Low']),
        #ctrl.Rule(end_support['End'] & import_availability['Import and NO availability of spare parts'], support['Low']),

       
        ctrl.Rule(end_life['Life'] & import_availability['Local production and availability of spare parts'], support['High']),
        ctrl.Rule(end_life['Life'] & import_availability['Local production and NO availability of spare parts'], support['Low']),
        ctrl.Rule(end_life['Life'] & import_availability['Import and availability of spare parts'], support['Medium']),
        ctrl.Rule(end_life['Life'] & import_availability['Import and NO availability of spare parts'], support['Low']),

        ctrl.Rule(end_life['End'] & import_availability['Local production and availability of spare parts'], support['Medium']),
        ctrl.Rule(end_life['End'] & import_availability['Local production and NO availability of spare parts'], support['Low']),
        ctrl.Rule(end_life['End'] & import_availability['Import and availability of spare parts'], support['Medium']),
        ctrl.Rule(end_life['End'] & import_availability['Import and NO availability of spare parts'], support['Low']),

        ctrl.Rule( end_life['End of support and end of life'] & import_availability['Local production and availability of spare parts'], support['Low']),
        ctrl.Rule( end_life['End of support and end of life'] & import_availability['Local production and NO availability of spare parts'], support['Low']),
        ctrl.Rule( end_life['End of support and end of life'] & import_availability['Import and availability of spare parts'], support['Low']),
        ctrl.Rule( end_life['End of support and end of life'] & import_availability['Import and NO availability of spare parts'], support['Low']),
    ]

    #rule_r = [

        #failure_rate con normalized_age
        #ctrl.Rule(failure_rate['High'] & normalized_age['New'], reliability['Medium']),
        #ctrl.Rule(failure_rate['High'] & normalized_age['Middle'], reliability['Medium']),
        #ctrl.Rule(failure_rate['High'] & normalized_age['Old'], reliability['Low']),
        #ctrl.Rule(failure_rate['Medium'] & normalized_age['New'], reliability['High']),
        #ctrl.Rule(failure_rate['Medium'] & normalized_age['Middle'], reliability['High']),
        #ctrl.Rule(failure_rate['Medium'] & normalized_age['Old'], reliability['Medium']),
        #ctrl.Rule(failure_rate['Low'] & normalized_age['New'], reliability['High']),
        #ctrl.Rule(failure_rate['Low'] & normalized_age['Middle'], reliability['High']),
        #ctrl.Rule(failure_rate['Low'] & normalized_age['Old'], reliability['Medium']),

        #backup con failure_rate
        #ctrl.Rule(backup['0'] & failure_rate['High'], reliability['Low']),
        #ctrl.Rule(backup['0'] & failure_rate['Medium'], reliability['Medium']),
        #ctrl.Rule(backup['0'] & failure_rate['Low'], reliability['Medium']),
        #ctrl.Rule(backup['1-2'] & failure_rate['High'], reliability['Medium']),
        #ctrl.Rule(backup['1-2'] & failure_rate['Medium'], reliability['High']),
        #ctrl.Rule(backup['1-2'] & failure_rate['Low'], reliability['High']),
        #ctrl.Rule(backup['>=3'] & failure_rate['High'], reliability['High']),
        #ctrl.Rule(backup['>=3'] & failure_rate['Medium'], reliability['High']),
        #ctrl.Rule(backup['>=3'] & failure_rate['Low'], reliability['High']),
    
    #    #backup con normalized_age
    #    ctrl.Rule(backup['0'] & normalized_age['New'], reliability['High']),
    #    ctrl.Rule(backup['0'] & normalized_age['Middle'], reliability['Medium']),
    #    ctrl.Rule(backup['0'] & normalized_age['Old'], reliability['Low']),
    #    ctrl.Rule(backup['1-2'] & normalized_age['New'], reliability['High']),
    #    ctrl.Rule(backup['1-2'] & normalized_age['Middle'], reliability['High']),
    #    ctrl.Rule(backup['1-2'] & normalized_age['Old'], reliability['Medium']),
    #    ctrl.Rule(backup['>=3'] & normalized_age['New'], reliability['High']),
    #    ctrl.Rule(backup['>=3'] & normalized_age['Middle'], reliability['High']),
    #    ctrl.Rule(backup['>=3'] & normalized_age['Old'], reliability['High']),
    #]

    rule_m = [
        ctrl.Rule(backup["0"] & eq_function['Therapeutic'] & up_time['Low'], mission['Medium']),
        ctrl.Rule(backup["0"] & eq_function['Therapeutic'] & up_time['Middle'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Therapeutic'] & up_time['High'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Diagnostic'] & up_time['Low'], mission['Low']),
        ctrl.Rule(backup["0"] & eq_function['Diagnostic'] & up_time['Middle'], mission['Medium']),
        ctrl.Rule(backup["0"] & eq_function['Diagnostic'] & up_time['High'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Analytical/Support'] & up_time['Low'], mission['Low']),
        ctrl.Rule(backup["0"] & eq_function['Analytical/Support'] & up_time['Middle'], mission['Medium']),
        ctrl.Rule(backup["0"] & eq_function['Analytical/Support'] & up_time['High'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Life saving/Life support'] & up_time['Low'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Life saving/Life support'] & up_time['Middle'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Life saving/Life support'] & up_time['High'], mission['High']),

        ctrl.Rule(backup["1-2"] & eq_function['Therapeutic'] & up_time['Low'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Therapeutic'] & up_time['Middle'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Therapeutic'] & up_time['High'], mission['High']),
        ctrl.Rule(backup["1-2"] & eq_function['Diagnostic'] & up_time['Low'], mission['Low']),
        ctrl.Rule(backup["1-2"] & eq_function['Diagnostic'] & up_time['Middle'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Diagnostic'] & up_time['High'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Analytical/Support'] & up_time['Low'], mission['Low']),
        ctrl.Rule(backup["1-2"] & eq_function['Analytical/Support'] & up_time['Middle'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Analytical/Support'] & up_time['High'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Life saving/Life support'] & up_time['Low'], mission['High']),
        ctrl.Rule(backup["1-2"] & eq_function['Life saving/Life support'] & up_time['Middle'], mission['High']),
        ctrl.Rule(backup["1-2"] & eq_function['Life saving/Life support'] & up_time['High'], mission['High']),

        ctrl.Rule(backup[">=3"] & eq_function['Therapeutic'] & up_time['Low'], mission['Medium']),
        ctrl.Rule(backup[">=3"] & eq_function['Therapeutic'] & up_time['Middle'], mission['Medium']),
        ctrl.Rule(backup[">=3"] & eq_function['Therapeutic'] & up_time['High'], mission['High']),
        ctrl.Rule(backup[">=3"] & eq_function['Diagnostic'] & up_time['Low'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Diagnostic'] & up_time['Middle'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Diagnostic'] & up_time['High'], mission['Medium']),
        ctrl.Rule(backup[">=3"] & eq_function['Analytical/Support'] & up_time['Low'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Analytical/Support'] & up_time['Middle'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Analytical/Support'] & up_time['High'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Life saving/Life support'] & up_time['Low'], mission['High']),
        ctrl.Rule(backup[">=3"] & eq_function['Life saving/Life support'] & up_time['Middle'], mission['High']),
        ctrl.Rule(backup[">=3"] & eq_function['Life saving/Life support'] & up_time['High'], mission['High']),
    ]

    rule_f = [
    # Tutte le 81 combinazioni complete (cost_levels & mission_result & support_result & normalized_age)
    
    # ================= cost_levels['Low'] =================
    
    # cost_levels['Low'] & mission_result['Low'] & support_result['Low']
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['Low'] & normalized_age['New'], criticity['Low']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['Low'] & normalized_age['Middle'], criticity['Low']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['Low'] & normalized_age['Old'], criticity['Medium']),

    # cost_levels['Low'] & mission_result['Low'] & support_result['Medium']
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['Medium'] & normalized_age['New'], criticity['VeryLow']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['Medium'] & normalized_age['Middle'], criticity['Low']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['Medium'] & normalized_age['Old'], criticity['Medium']),

    # cost_levels['Low'] & mission_result['Low'] & support_result['High']
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['High'] & normalized_age['New'], criticity['VeryLow']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['High'] & normalized_age['Middle'], criticity['Low']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Low'] & support_result['High'] & normalized_age['Old'], criticity['Medium']),

    # cost_levels['Low'] & mission_result['Medium'] & support_result['Low']
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['Low'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['Low'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['Low'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Low'] & mission_result['Medium'] & support_result['Medium']
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['New'], criticity['Low']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Low'] & mission_result['Medium'] & support_result['High']
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['High'] & normalized_age['New'], criticity['VeryLow']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['High'] & normalized_age['Middle'], criticity['Low']),
    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'] & support_result['High'] & normalized_age['Old'], criticity['Medium']),

    # cost_levels['Low'] & mission_result['High'] & support_result['Low']
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['Low'] & normalized_age['New'], criticity['High']),
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['Low'] & normalized_age['Middle'], criticity['VeryHigh']),
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['Low'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['Low'] & mission_result['High'] & support_result['Medium']
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['Medium'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['Medium'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['Medium'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Low'] & mission_result['High'] & support_result['High']
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['High'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['High'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Low'] & mission_result['High'] & support_result['High'] & normalized_age['Old'], criticity['High']),

    # ================= cost_levels['Medium'] =================

    # cost_levels['Medium'] & mission_result['Low'] & support_result['Low']
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['Low'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['Low'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['Low'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Medium'] & mission_result['Low'] & support_result['Medium']
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['Medium'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['Medium'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['Medium'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Medium'] & mission_result['Low'] & support_result['High']
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['High'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['High'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'] & support_result['High'] & normalized_age['Old'], criticity['Medium']),

    # cost_levels['Medium'] & mission_result['Medium'] & support_result['Low']
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['Low'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['Low'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['Low'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Medium'] & mission_result['Medium'] & support_result['Medium']
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Medium'] & mission_result['Medium'] & support_result['High']
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['High'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['High'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'] & support_result['High'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Medium'] & mission_result['High'] & support_result['Low']
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['Low'] & normalized_age['New'], criticity['High']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['Low'] & normalized_age['Middle'], criticity['VeryHigh']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['Low'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['Medium'] & mission_result['High'] & support_result['Medium']
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['Medium'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['Medium'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['Medium'] & normalized_age['Old'], criticity['High']),

    # cost_levels['Medium'] & mission_result['High'] & support_result['High']
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['High'] & normalized_age['New'], criticity['Low']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['High'] & normalized_age['Middle'], criticity['Medium']),
    ctrl.Rule(cost_levels['Medium'] & mission_result['High'] & support_result['High'] & normalized_age['Old'], criticity['High']),

    # ================= cost_levels['High'] =================

    # cost_levels['High'] & mission_result['Low'] & support_result['Low']
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['Low'] & normalized_age['New'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['Low'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['Low'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['High'] & mission_result['Low'] & support_result['Medium']
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['Medium'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['Medium'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['Medium'] & normalized_age['Old'], criticity['High']),

    # cost_levels['High'] & mission_result['Low'] & support_result['High']
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['High'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['High'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['Low'] & support_result['High'] & normalized_age['Old'], criticity['High']),

    # cost_levels['High'] & mission_result['Medium'] & support_result['Low']
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['Low'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['Low'] & normalized_age['Middle'], criticity['VeryHigh']),
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['Low'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['High'] & mission_result['Medium'] & support_result['Medium']
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['Medium'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['High'] & mission_result['Medium'] & support_result['High']
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['High'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['High'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['Medium'] & support_result['High'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['High'] & mission_result['High'] & support_result['Low']
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['Low'] & normalized_age['New'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['Low'] & normalized_age['Middle'], criticity['VeryHigh']),
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['Low'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['High'] & mission_result['High'] & support_result['Medium']
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['Medium'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['Medium'] & normalized_age['Middle'], criticity['VeryHigh']),
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['Medium'] & normalized_age['Old'], criticity['VeryHigh']),

    # cost_levels['High'] & mission_result['High'] & support_result['High']
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['High'] & normalized_age['New'], criticity['Medium']),
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['High'] & normalized_age['Middle'], criticity['High']),
    ctrl.Rule(cost_levels['High'] & mission_result['High'] & support_result['High'] & normalized_age['Old'], criticity['VeryHigh']),
]

#    rule_f = [
#    # cost_levels & mission_result (già presenti)
#    ctrl.Rule(cost_levels['Low'] & mission_result['High'], criticity['High']),     
#    ctrl.Rule(cost_levels['Low'] & mission_result['Medium'], criticity['Low']),  
#    ctrl.Rule(cost_levels['Low'] & mission_result['Low'], criticity['VeryLow']),   
#    ctrl.Rule(cost_levels['Medium'] & mission_result['High'], criticity['High']),  
#    ctrl.Rule(cost_levels['Medium'] & mission_result['Medium'], criticity['Medium']),
#    ctrl.Rule(cost_levels['Medium'] & mission_result['Low'], criticity['Low']),    
#    ctrl.Rule(cost_levels['High'] & mission_result['High'], criticity['VeryHigh']),
#    ctrl.Rule(cost_levels['High'] & mission_result['Medium'], criticity['High']),   
#    ctrl.Rule(cost_levels['High'] & mission_result['Low'], criticity['High']),
        
#    # support_result & mission_result (già presenti)
#    ctrl.Rule(support_result['High'] & mission_result['High'], criticity['Medium']),       
#    ctrl.Rule(support_result['High'] & mission_result['Medium'], criticity['Low']),       
#    ctrl.Rule(support_result['High'] & mission_result['Low'], criticity['VeryLow']),      
#    ctrl.Rule(support_result['Medium'] & mission_result['High'], criticity['High']),      
#    ctrl.Rule(support_result['Medium'] & mission_result['Medium'], criticity['Medium']),  
#    ctrl.Rule(support_result['Medium'] & mission_result['Low'], criticity['Low']),        
#    ctrl.Rule(support_result['Low'] & mission_result['High'], criticity['VeryHigh']),     
#    ctrl.Rule(support_result['Low'] & mission_result['Medium'], criticity['High']),       
#    ctrl.Rule(support_result['Low'] & mission_result['Low'], criticity['Medium']),        

#    # support_result & cost_levels (già presenti)
#    ctrl.Rule(support_result['High'] & cost_levels['High'], criticity['VeryHigh']),         
#    ctrl.Rule(support_result['High'] & cost_levels['Medium'], criticity['Medium']),          
#    ctrl.Rule(support_result['High'] & cost_levels['Low'], criticity['VeryLow']),         
#    ctrl.Rule(support_result['Medium'] & cost_levels['High'], criticity['VeryHigh']),         
#    ctrl.Rule(support_result['Medium'] & cost_levels['Medium'], criticity['Medium']),     
#    ctrl.Rule(support_result['Medium'] & cost_levels['Low'], criticity['Low']),          
#    ctrl.Rule(support_result['Low'] & cost_levels['High'], criticity['VeryHigh']),       
#    ctrl.Rule(support_result['Low'] & cost_levels['Medium'], criticity['High']),          
#    ctrl.Rule(support_result['Low'] & cost_levels['Low'], criticity['High']),

#    # backup & normalized_age (già presenti)
#    ctrl.Rule(backup['0'] & normalized_age['New'], criticity['High']),
#    ctrl.Rule(backup['0'] & normalized_age['Middle'], criticity['Medium']),
#    ctrl.Rule(backup['0'] & normalized_age['Old'], criticity['Low']),
#    ctrl.Rule(backup['1-2'] & normalized_age['New'], criticity['High']),
#    ctrl.Rule(backup['1-2'] & normalized_age['Middle'], criticity['High']),
#    ctrl.Rule(backup['1-2'] & normalized_age['Old'], criticity['Medium']),
#    ctrl.Rule(backup['>=3'] & normalized_age['New'], criticity['High']),
#    ctrl.Rule(backup['>=3'] & normalized_age['Middle'], criticity['High']),
#    ctrl.Rule(backup['>=3'] & normalized_age['Old'], criticity['High']),

    
#    # cost_levels & normalized_age
#    ctrl.Rule(cost_levels['Low'] & normalized_age['New'], criticity['Low']),
#    ctrl.Rule(cost_levels['Low'] & normalized_age['Middle'], criticity['VeryLow']),
#    ctrl.Rule(cost_levels['Low'] & normalized_age['Old'], criticity['VeryLow']),
#    ctrl.Rule(cost_levels['Medium'] & normalized_age['New'], criticity['Medium']),
#    ctrl.Rule(cost_levels['Medium'] & normalized_age['Middle'], criticity['Low']),
#    ctrl.Rule(cost_levels['Medium'] & normalized_age['Old'], criticity['VeryLow']),
#    ctrl.Rule(cost_levels['High'] & normalized_age['New'], criticity['VeryHigh']),
#    ctrl.Rule(cost_levels['High'] & normalized_age['Middle'], criticity['High']),
#    ctrl.Rule(cost_levels['High'] & normalized_age['Old'], criticity['Medium']),

#    # cost_levels & backup
#    ctrl.Rule(cost_levels['Low'] & backup['0'], criticity['Medium']),
#    ctrl.Rule(cost_levels['Low'] & backup['1-2'], criticity['Low']),
#    ctrl.Rule(cost_levels['Low'] & backup['>=3'], criticity['VeryLow']),
#    ctrl.Rule(cost_levels['Medium'] & backup['0'], criticity['High']),
#    ctrl.Rule(cost_levels['Medium'] & backup['1-2'], criticity['Medium']),
#    ctrl.Rule(cost_levels['Medium'] & backup['>=3'], criticity['Low']),
#    ctrl.Rule(cost_levels['High'] & backup['0'], criticity['VeryHigh']),
#    ctrl.Rule(cost_levels['High'] & backup['1-2'], criticity['VeryHigh']),
#    ctrl.Rule(cost_levels['High'] & backup['>=3'], criticity['High']),

#    # mission_result & normalized_age  
#    ctrl.Rule(mission_result['High'] & normalized_age['New'], criticity['High']),
#    ctrl.Rule(mission_result['High'] & normalized_age['Middle'], criticity['Medium']),
#    ctrl.Rule(mission_result['High'] & normalized_age['Old'], criticity['Low']),
#    ctrl.Rule(mission_result['Medium'] & normalized_age['New'], criticity['Medium']),
#    ctrl.Rule(mission_result['Medium'] & normalized_age['Middle'], criticity['Low']),
#    ctrl.Rule(mission_result['Medium'] & normalized_age['Old'], criticity['VeryLow']),
#    ctrl.Rule(mission_result['Low'] & normalized_age['New'], criticity['Low']),
#    ctrl.Rule(mission_result['Low'] & normalized_age['Middle'], criticity['VeryLow']),
#    ctrl.Rule(mission_result['Low'] & normalized_age['Old'], criticity['VeryLow']),

#    # mission_result & backup
#    ctrl.Rule(mission_result['High'] & backup['0'], criticity['VeryHigh']),
#    ctrl.Rule(mission_result['High'] & backup['1-2'], criticity['High']),
#    ctrl.Rule(mission_result['High'] & backup['>=3'], criticity['Medium']),
#    ctrl.Rule(mission_result['Medium'] & backup['0'], criticity['High']),
#    ctrl.Rule(mission_result['Medium'] & backup['1-2'], criticity['Medium']),
#    ctrl.Rule(mission_result['Medium'] & backup['>=3'], criticity['Low']),
#    ctrl.Rule(mission_result['Low'] & backup['0'], criticity['Medium']),
#    ctrl.Rule(mission_result['Low'] & backup['1-2'], criticity['Low']),
#    ctrl.Rule(mission_result['Low'] & backup['>=3'], criticity['VeryLow']),

#    # support_result & normalized_age
#    ctrl.Rule(support_result['High'] & normalized_age['New'], criticity['Low']),
#    ctrl.Rule(support_result['High'] & normalized_age['Middle'], criticity['VeryLow']),
#    ctrl.Rule(support_result['High'] & normalized_age['Old'], criticity['VeryLow']),
#    ctrl.Rule(support_result['Medium'] & normalized_age['New'], criticity['Medium']),
#    ctrl.Rule(support_result['Medium'] & normalized_age['Middle'], criticity['Low']),
#    ctrl.Rule(support_result['Medium'] & normalized_age['Old'], criticity['VeryLow']),
#    ctrl.Rule(support_result['Low'] & normalized_age['New'], criticity['VeryHigh']),
#    ctrl.Rule(support_result['Low'] & normalized_age['Middle'], criticity['High']),
#    ctrl.Rule(support_result['Low'] & normalized_age['Old'], criticity['Medium']),

#    # support_result & backup
#    ctrl.Rule(support_result['High'] & backup['0'], criticity['Medium']),
#    ctrl.Rule(support_result['High'] & backup['1-2'], criticity['Low']),
#    ctrl.Rule(support_result['High'] & backup['>=3'], criticity['VeryLow']),
#    ctrl.Rule(support_result['Medium'] & backup['0'], criticity['High']),
#    ctrl.Rule(support_result['Medium'] & backup['1-2'], criticity['Medium']),
#    ctrl.Rule(support_result['Medium'] & backup['>=3'], criticity['Low']),
#    ctrl.Rule(support_result['Low'] & backup['0'], criticity['VeryHigh']),
#    ctrl.Rule(support_result['Low'] & backup['1-2'], criticity['VeryHigh']),
#    ctrl.Rule(support_result['Low'] & backup['>=3'], criticity['High']),
#]
    #ctrl.Rule(support_result['High'] & reliability_result['High'], criticity['VeryLow']),      
        #ctrl.Rule(support_result['High'] & reliability_result['Medium'], criticity['Low']),    
        #ctrl.Rule(support_result['High'] & reliability_result['Low'], criticity['High']),    
        #ctrl.Rule(support_result['Medium'] & reliability_result['High'], criticity['VeryLow']), 
        #ctrl.Rule(support_result['Medium'] & reliability_result['Medium'], criticity['Medium']), 
        #ctrl.Rule(support_result['Medium'] & reliability_result['Low'], criticity['High']),   
        #ctrl.Rule(support_result['Low'] & reliability_result['High'], criticity['Medium']),    
        #ctrl.Rule(support_result['Low'] & reliability_result['Medium'], criticity['High']),    
        #ctrl.Rule(support_result['Low'] & reliability_result['Low'], criticity['VeryHigh']),   

         #ctrl.Rule(mission_result['High'] & reliability_result['High'], criticity['Medium']),
        #ctrl.Rule(mission_result['High'] & reliability_result['Medium'], criticity['High']),
        #ctrl.Rule(mission_result['High'] & reliability_result['Low'], criticity['VeryHigh']),
        #ctrl.Rule(mission_result['Medium'] & reliability_result['High'], criticity['Low']),
        #ctrl.Rule(mission_result['Medium'] & reliability_result['Medium'], criticity['Medium']),
        #ctrl.Rule(mission_result['Medium'] & reliability_result['Low'], criticity['High']),
        #ctrl.Rule(mission_result['Low'] & reliability_result['High'], criticity['VeryLow']),
        #ctrl.Rule(mission_result['Low'] & reliability_result['Medium'], criticity['Low']),
        #ctrl.Rule(mission_result['Low'] & reliability_result['Low'], criticity['Medium']),
    
     
        #ctrl.Rule(cost_levels['Low'] & reliability_result['High'], criticity['VeryLow']),     
        #ctrl.Rule(cost_levels['Low'] & reliability_result['Medium'], criticity['Low']),   
        #ctrl.Rule(cost_levels['Low'] & reliability_result['Low'], criticity['Medium']),  
        #ctrl.Rule(cost_levels['Medium'] & reliability_result['High'], criticity['Low']),
        #ctrl.Rule(cost_levels['Medium'] & reliability_result['Medium'], criticity['Medium']), 
        #ctrl.Rule(cost_levels['Medium'] & reliability_result['Low'], criticity['High']), 
        #ctrl.Rule(cost_levels['High'] & reliability_result['High'], criticity['Medium']),
        #ctrl.Rule(cost_levels['High'] & reliability_result['Medium'], criticity['High']),
        #ctrl.Rule(cost_levels['High'] & reliability_result['Low'], criticity['VeryHigh']), 
    

    mission_ctrl = ctrl.ControlSystem(rule_m)
    #reliability_ctrl = ctrl.ControlSystem(rule_r)
    support_ctrl=ctrl.ControlSystem(rule_s)
    criticity_ctrl = ctrl.ControlSystem(rule_f)

    mission_simulation = ctrl.ControlSystemSimulation(mission_ctrl)
    #reliability_simulation = ctrl.ControlSystemSimulation(reliability_ctrl)
    support_simulation=ctrl.ControlSystemSimulation(support_ctrl)
    criticity_simulation = ctrl.ControlSystemSimulation(criticity_ctrl)

    return {
        'mission_simulation': mission_simulation,
        #'reliability_simulation': reliability_simulation,
        'support_simulation' : support_simulation,
        'criticity_simulation': criticity_simulation
    }

# --- Funzione calcolo fuzzy ---
def calculate_fuzzy_scores(n_age, eqf, cost, fr, uptime, e_l, e_s, imp, backup):
    try:
        fuzzy_system = setup_fuzzy_system()
        
        n_age = float(n_age)
        fr = float(fr)
        uptime = float(uptime)
        eqf = float(eqf)
        e_l=float(e_l)
        e_s=float(e_s)
        imp=float(imp)
        backup=float(backup)
        
        #fuzzy_system['reliability_simulation'].input['normalized_age'] = n_age
        #fuzzy_system['reliability_simulation'].input['failure_rate'] = fr
        #fuzzy_system['reliability_simulation'].input['backup']=backup
        fuzzy_system['mission_simulation'].input['up_time'] = uptime
        fuzzy_system['mission_simulation'].input['eq_function'] = eqf
        fuzzy_system['mission_simulation'].input['backup']=backup
        fuzzy_system['support_simulation'].input['end_life']=e_l
        #fuzzy_system['support_simulation'].input['end_support']=e_s
        fuzzy_system['support_simulation'].input['import_availability']=imp
        
        #fuzzy_system['reliability_simulation'].compute()
        fuzzy_system['mission_simulation'].compute()
        fuzzy_system['support_simulation'].compute()
        
        #if 'reliability' not in fuzzy_system['reliability_simulation'].output:
        #    return None, None, None, None
        if 'mission' not in fuzzy_system['mission_simulation'].output:
            return None, None, None
        if 'support' not in fuzzy_system['support_simulation'].output:
            return None, None, None
        
        #rel_score = float(fuzzy_system['reliability_simulation'].output['reliability'])
        mis_score = float(fuzzy_system['mission_simulation'].output['mission'])
        supp_score=float(fuzzy_system['support_simulation'].output['support'])
        
        #fuzzy_system['criticity_simulation'].input['reliability_result'] = rel_score
        fuzzy_system['criticity_simulation'].input['mission_result'] = mis_score
        fuzzy_system['criticity_simulation'].input['support_result']=supp_score
        fuzzy_system['criticity_simulation'].input['cost_levels'] = cost
        fuzzy_system['criticity_simulation'].input['normalized_age']=n_age
        fuzzy_system['criticity_simulation'].compute()
        
        if 'criticity' not in fuzzy_system['criticity_simulation'].output:
            return mis_score, supp_score, None
            
        crit_score = float(fuzzy_system['criticity_simulation'].output['criticity'])
        return mis_score, supp_score, crit_score
        
    except Exception as e:
        return None, None, None


# =============================================================================
# PAGINA ADD WARD/ROOM
# =============================================================================
if page=="Wards/Rooms":
    tab1, tab2, tab3, tab4 = st.tabs(["Add Room", "Remove Room", "Add Ward", "Remove Ward"])
    with tab3:

        

        wards=get_all_wards()
        ward_options = {f"{r[0]}": f"Ward {r[1]}" for r in wards}

        with st.form("Add Ward",clear_on_submit=True):
          
             ward_name = st.text_input("Ward Name", placeholder="e.g., Intensive Care Unit")
         
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
        
        # Mostra tabella
        st.dataframe(df, use_container_width=True)

    with tab4:
        with st.form("Remove Ward",clear_on_submit=True):
            ward_id = st.selectbox("Ward", options=list(ward_options.keys()), 
                                     format_func=lambda x: ward_options[x])
       
            submitted = st.form_submit_button("Remove Ward")
        
            if submitted: 
                # PRIMA controlla se il ward ha delle room
                cur.execute("SELECT COUNT(*) FROM room WHERE ward_id = %s", (ward_id,))
                room_count = cur.fetchone()[0]
    
                if room_count > 0:
                    # Se ci sono room, mostra il messaggio personalizzato
                    st.error(f"Remove all the rooms of the ward first({room_count} rooms found)")
                else:
                    # Se non ci sono room, procedi con l'eliminazione
                    if delete_wards(ward_id):
                        st.success("Ward removed successfully!")
                        ward_options = {f"{r[0]}": f"{r[1]}" for r in wards}
                        log_action(1, 'DELETE WARD', ward_options.get(str(ward_id), 'N/A'), ward_id)
                        st.rerun()  # Ricarica la pagina per aggiornare la lista
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
        
        # Mostra tabella
        st.dataframe(df, use_container_width=True)

    with tab2: 
          # FUORI dal form - selezione ward e room

        ward_id = st.selectbox("Ward", options=list(ward_options.keys()), 
                               format_func=lambda x: ward_options[x], key="remove_ward_select")

        # Query per le room del ward selezionato
        cur.execute("SELECT room_id, room_name FROM room WHERE ward_id = %s", (ward_id,))
        rooms = cur.fetchall()
        room_options = {r[0]: r[1] for r in rooms}

        if room_options:
            # Selezione room (ancora fuori dal form)
            room_id = st.selectbox(
                "Room",
                options=list(room_options.keys()),
                format_func=lambda x: room_options[x],
                key="remove_room_select"
            )
           
    
            # Form solo per il pulsante di rimozione
            with st.form("Remove Room", clear_on_submit=True):
                submitted = st.form_submit_button("Remove Room")


                if submitted: 
                # PRIMA controlla se il ward ha delle room
                    cur.execute("SELECT COUNT(*) FROM medical_device WHERE room_id = %s", (room_id,))
                    device_count = cur.fetchone()[0]
    
                    if device_count > 0:
                        # Se ci sono room, mostra il messaggio personalizzato
                        st.error(f"Remove all the devices of the room first ({device_count} devices found)")
                    else:
                        # Se non ci sono room, procedi con l'eliminazione
                        if delete_room(room_id):
                            st.success("Room removed successfully!")
                            #st.rerun()  # Ricarica la pagina per aggiornare la lista
                        else:
                            st.error("Failed to remove room. Please try again.")


                #if submitted: 
                #    if delete_room(room_id):
                #        st.success("Room removed successfully!")
                #        st.rerun()  # Ricarica la pagina per aggiornare la lista
                #    else:
                #        st.error("Failed to remove room. Please try again.")
        else:
            st.warning("Nessuna room disponibile per questo ward")
            # Form disabilitato se non ci sono room
            with st.form("Remove Room Disabled", clear_on_submit=True):
                st.form_submit_button("Remove Room", disabled=True)







# =============================================================================
# PAGINA 1: DEVICES
# =============================================================================

if page == "Devices":
    tab1, tab2, tab3, tab4= st.tabs(["View medical devices", "Add medical devices", "Edit medical devices", "Delete medical device"])

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
                serial_number = st.text_input("Serial number*", placeholder="Serial number")
                model = st.text_input("Model*", placeholder="e.g., V60")
                installation_date = st.date_input(
                    "Installation Date", 
                    value=None,  min_value=dt.date(2000, 1, 1),
                    help="Leave it empty if you don't want to specify a date"
                )
                udi_number= st.text_input("Instrument Code", placeholder="e.g., 12345678901234")
                #nome_dispositivo = st.text_input("Device name", placeholder="e.g., Ventilator Model X")           
                #data_acquisto = st.date_input("Date of purchase", value=dt.date.today())
                #oggi = dt.date.today()
                #eta = (oggi - data_acquisto).days / 365
                ##st.info(f"Calculated age: {eta:.2f} years")
        
            with col2:
                description = st.text_input("Device Description*", placeholder="e.g., Ventilator Model X")
                device_class = st.selectbox("Device Class*", 
                                          options=["Class A", "Class B", "Class C", "Class D"])
                manufacturer_date = st.date_input("Manufacturer date", value=None, min_value=dt.date(2000, 1, 1),
                                                   help="Leave it empty if you don't want to specify a date")
                #usage_type = st.selectbox("Usage Type*", 
                #                        options=["Life Saving/Life Support", "Therapeutic", "Diagnostic", 
                #                               "Analytical/Support"])
            
                #eq_function_labels = {
                #    1: "1 - Under threshold", 
                #    2: "2 - Around threshold", 
                #    3: "3 - Above threshold",
                #    4: "4 - Critical function"
                #}
                #eq_function = st.selectbox("Equipment function", options=[1,2,3,4], 
                #                         format_func=lambda x: eq_function_labels[x])
            
                #cost= st.number_input("Cost (Laks)", min_value=0.0, max_value=200.0, 
                #                            step=1.0, format="%.2f", value=10.0)
                #maintenance= st.number_input("Last three years maintenance cost (Laks)", min_value=0.0, max_value=200.0, 
                #                            step=0.5, format="%.2f", value=1.0)
                #cost_levels=(maintenance/cost)*100 
                #st.info(f"Calculated: {cost_levels:.2f} %")
        
            with col3:
                brand = st.text_input("Brand*", placeholder="e.g., Philips")
                cost_inr = st.number_input("Cost (INR)*", min_value=0.0, step=1000.0, value=100000.0)
                room_id = st.selectbox("Room*", options=list(room_options.keys()), 
                                     format_func=lambda x: room_options[x])
           
                #n_failure = st.number_input("Number of failures", min_value=0.0, max_value=30.0, 
                #                             step=1.0, format="%.2f", value=0.0)
                #etax=eta
                #if etax<1: etax=1
                #if n_failure is None or n_failure == 0:
                #    failure_rate = 0.1
                #else:
                #    failure_rate = n_failure / etax
            
                #up_time = st.number_input("Uptime (hours/week)", min_value=0.0, max_value=36.0, 
                #                        step=1.0, format="%.1f", value=20.0)
        
            ## Location field (separate row)
            #st.markdown("**Location**")
            #stanza = st.text_input("Room / Department", placeholder="e.g., ICU, OR-1")
        
            # Preview calculation
            #check = st.form_submit_button("Computation preview", type="secondary")
            #if check:
            #    rel_score, mis_score, crit_score = calculate_fuzzy_scores(eta, eq_function, cost_levels, failure_rate, up_time)
            #    if rel_score is not None:
            #        prev_col1, prev_col2, prev_col3 = st.columns(3)
            #        with prev_col1:
            #            st.metric("Reliability", f"{rel_score:.2f}")
            #        with prev_col2:
            #            st.metric("Mission Critical", f"{mis_score:.2f}")
            #        with prev_col3:
            #            st.metric("Criticity", f"{crit_score:.2f}")
        
            # Submit button
            submitted = st.form_submit_button("Add Device to Database", type="primary")
        
            if submitted:
                if description and room_id:
                    try:
                        # Insert device
                        device_id = insert_medical_device(
                            description, room_id, device_class, None, cost_inr,
                            brand, model, installation_date, serial_number, manufacturer_date, udi_number
                        )
                        st.success(f"✅ Device successfully added! Device ID: {device_id}")
                        
                    except Exception as e:
                        st.error(f"❌ Error adding device: {str(e)}")
                else:
                    st.error("❌ Please fill all required fields marked with *")
         
    with tab3:
        
       
    
         

        all_devices = get_all_devices()

        # Filtra se c'è una ricerca
        # Prima ottieni tutti i dati necessari

        rooms = get_all_rooms()
        wards = get_all_wards()  # Assumendo che questa funzione esista

        # Crea le opzioni per i filtri
        ward_options = {"All": "All Wards"}
        ward_options.update({str(w[0]): w[1] for w in wards})  # ID: Nome Ward

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
            # Filtra le room in base al ward selezionato
            if selected_ward != "All":
                filtered_rooms = [r for r in rooms if r[3] == int(selected_ward)]  # Assumendo che r[3] sia ward_id
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
            # Barra di ricerca aggiuntiva
            search = st.text_input("🔍 Search devices:", placeholder="Search by ID, description, brand...")

        # APPLICA I FILTRI
        filtered_devices = []

        for d in all_devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial,manufacturer_date = d
    
            # Ottieni info room per questo device
            device_room = next((r for r in rooms if r[0] == room_id), None)
    
            # Filtro Ward
            if selected_ward != "All":
                if not device_room or device_room[3] != int(selected_ward):  # r[3] = ward_id
                    continue
    
            # Filtro Room
            if selected_room != "All":
                if str(room_id) != selected_room:
                    continue
    
            # Filtro Search
            if search:
                search_lower = search.lower()
                room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                search_text = f"{device_id} {description} {brand} {model} {room_info}".lower()
                if search_lower not in search_text:
                    continue
    
            filtered_devices.append(d)

        # MESSAGGIO SE NESSUN RISULTATO
        if not filtered_devices:
            st.info("No devices found with the selected filters")
            st.stop()

        # SELECTBOX FINALE CON DISPOSITIVI FILTRATI
       

        device_options = {}
        for d in filtered_devices:
            device_id = d[0]
            room_id = d[2]
            description = d[3] or "No Description"
            brand = d[8] or "No Brand"
            model = d[9] or "No Model"

            # Trova room info
            device_room = next((r for r in rooms if r[0] == room_id), None)
            if device_room:
                ward_id = device_room[3]  # Assumendo che r[3] sia ward_id
                ward_info = next((w for w in wards if w[0] == ward_id), None)

                if ward_info:
                    ward_name = ward_info[1]  # Nome del ward
                    room_display = f"Floor {device_room[1]} - {device_room[2]}"
                    full_location = f"{ward_name} | {room_display}"
                else:
                    full_location = f"Floor {device_room[1]} - {device_room[2]}"
            else:
                full_location = "❌ No Location"
    
            label = f"ID:{device_id} | {description} | {brand} {model} | {full_location}"
            device_options[device_id] = label  # AGGIUNGI AL DIZIONARIO

        # CREA UNA SOLA SELECTBOX FUORI DAL LOOP
        selected_device_id = st.selectbox(
            "Choose device to edit:",
            options=list(device_options.keys()),
            format_func=lambda x: device_options[x],
            key="device_selector"  # Aggiungi una key unica
        )

        if selected_device_id:
            device_data = get_device_by_id(selected_device_id)
            if device_data:
                Device_ID, Parent_ID, Room_ID, Description, Class, Usage_Type, Cost_INR, Present, Brand, Model, Installation_Date, UDI_Number, serial_number, manufacturer_date = device_data
    
                st.subheader(f"Edit Device ")
                rooms = get_all_rooms()
                room_options = {f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms}
    
                with st.form("edit_device_form"):
                    col1, col2, col3 = st.columns(3)
        
                    with col1:
                        serial_number = st.text_input("Serial number", 
                                                 value=serial_number or "",
                                                 placeholder="Serial Number")
                        model = st.text_input("Model*", 
                                            value=Model or "", 
                                            placeholder="e.g., V60")
                
                        # Trova l'indice della classe corrente
                        class_options = ["Class A", "Class B", "Class C", "Class D"]
                        current_class_index = 0
                        if Class in class_options:
                            current_class_index = class_options.index(Class)

                       
                    
                       
                
                        # Converti la data dal database se necessario
                        if Installation_Date:
                            if isinstance(Installation_Date, str):
                                installation_date_value = dt.datetime.strptime(Installation_Date, '%Y-%m-%d').date()
                            else:
                                installation_date_value = Installation_Date
                        else:
                            installation_date_value = None
                    
                        installation_date = st.date_input("Installation Date*", min_value=dt.date(2000, 1, 1),
                                                        value=installation_date_value)
                        present=st.checkbox("Present in the hospital", value=bool(Present))

                        udi_number=st.text_input("Instrument Code", value=UDI_Number or "", placeholder="AMTZ/ARC/EQP/...")
        
                    with col2:
                         # Usa value=Description per pre-riempire
                        description = st.text_input("Device Description*", 
                                                  value=Description or "", 
                                                  placeholder="e.g., Ventilator Model X")
                        
                
                        # Trova l'indice del tipo di utilizzo corrente
                        device_class = st.selectbox("Device Class*", 
                                                  options=class_options,
                                                  index=current_class_index)
                        if manufacturer_date:
                            if isinstance(manufacturer_date, str):
                                manufacturer_date_value = dt.datetime.strptime(manufacturer_date, '%Y-%m-%d').date()
                            else:
                                manufacturer_date_value = manufacturer_date
                        else:
                            manufacturer_date_value = None
                    
                        manufacturer_date = st.date_input("Manufacturer Date*", min_value=dt.date(2000, 1, 1),
                                                        value=manufacturer_date_value)
        
                    with col3:
                        brand = st.text_input("Brand*", 
                                            value=Brand or "", 
                                            placeholder="e.g., Philips")
                        
                
                        cost_inr = st.number_input("Cost (INR)*", 
                                                 min_value=0.0, 
                                                 step=1000.0, 
                                                 value=float(Cost_INR) if Cost_INR else 100000.0)
                
                         # Trova l'indice della stanza corrente
                        room_keys = list(room_options.keys())
                        current_room_index = 0
                        if str(Room_ID) in room_keys:
                            current_room_index = room_keys.index(str(Room_ID))
                    
                        room_id = st.selectbox("Room*", 
                                             options=room_keys,
                                             index=current_room_index,
                                             format_func=lambda x: room_options[x])

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

                                update_device(selected_device_id, description, device_class, 1, cost_inr, brand, model, installation_date, serial_number, manufacturer_date, udi_number, present)
                                st.success("Updated!")
                            except Exception as e:
                                st.error(f"Error: {e}")
                           
    with tab4:
        all_devices = get_all_devices()

        # Filtra se c'è una ricerca
        # Prima ottieni tutti i dati necessari

        rooms = get_all_rooms()
        wards = get_all_wards()  # Assumendo che questa funzione esista

        # Crea le opzioni per i filtri
        ward_options = {"All": "All Wards"}
        ward_options.update({str(w[0]): w[1] for w in wards})  # ID: Nome Ward

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
            # Filtra le room in base al ward selezionato
            if selected_ward != "All":
                filtered_rooms = [r for r in rooms if r[3] == int(selected_ward)]  # Assumendo che r[3] sia ward_id
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
            # Barra di ricerca aggiuntiva
            search = st.text_input("🔍 Search devices:", placeholder="Search by ID, description, brand....")

        # APPLICA I FILTRI
        filtered_devices = []

        for d in all_devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial, manufacturer_date = d
    
            # Ottieni info room per questo device
            device_room = next((r for r in rooms if r[0] == room_id), None)
    
            # Filtro Ward
            if selected_ward != "All":
                if not device_room or device_room[3] != int(selected_ward):  # r[3] = ward_id
                    continue
    
            # Filtro Room
            if selected_room != "All":
                if str(room_id) != selected_room:
                    continue
    
            # Filtro Search
            if search:
                search_lower = search.lower()
                room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                search_text = f"{device_id} {description} {brand} {model} {room_info}".lower()
                if search_lower not in search_text:
                    continue
    
            filtered_devices.append(d)

        # MESSAGGIO SE NESSUN RISULTATO
        if not filtered_devices:
            st.info("No devices found with the selected filters")
            st.stop()

        # SELECTBOX FINALE CON DISPOSITIVI FILTRATI
       

        device_options = {}
        for d in filtered_devices:
            device_id = d[0]
            room_id = d[2]
            description = d[3] or "No Description"
            brand = d[8] or "No Brand"
            model = d[9] or "No Model"

            # Trova room info
            device_room = next((r for r in rooms if r[0] == room_id), None)
            if device_room:
                ward_id = device_room[3]  # Assumendo che r[3] sia ward_id
                ward_info = next((w for w in wards if w[0] == ward_id), None)

                if ward_info:
                    ward_name = ward_info[1]  # Nome del ward
                    room_display = f"Floor {device_room[1]} - {device_room[2]}"
                    full_location = f"{ward_name} | {room_display}"
                else:
                    full_location = f"Floor {device_room[1]} - {device_room[2]}"
            else:
                full_location = "❌ No Location"
    
            label = f"ID:{device_id} | {description} | {brand} {model} | {full_location}"
            device_options[device_id] = label  # AGGIUNGI AL DIZIONARIO

        # CREA UNA SOLA SELECTBOX FUORI DAL LOOP
        device_to_delete = st.selectbox(
            "Choose device to edit:",
            options=list(device_options.keys()),
            format_func=lambda x: device_options[x],
            key="device_selector1"  # Aggiungi una key unica
        )
    
        if st.button("Delete Selected Device", type="secondary"):
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
        #Get available rooms
        rooms = get_all_rooms()
        if not rooms:
            st.error("No rooms found! Please add rooms in the Admin Panel first.")
            st.stop()
        
        room_options = {f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms}
        

        if not devices:
            st.info("No devices found in database. Go to 'Add Devices' page to add some devices first.")
            st.stop()
        #Barra di ricerca
        # FILTRI PER LA TABELLA
        col1, col2, col3 = st.columns(3)

        with col1:
            # Filtro Ward
            wards = get_all_wards()  # Assumendo che questa funzione esista
            ward_options = {"All": "All Wards"}
            ward_options.update({str(w[0]): w[1] for w in wards})
    
            selected_ward_filter = st.selectbox(
                "Filter by Ward:",
                options=list(ward_options.keys()),
                format_func=lambda x: ward_options[x],
                key="table_ward_filter"
            )

        with col2:
            # Filtro Room (cascading dal ward)
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
            # Barra di ricerca
            search = st.text_input(
                "🔍 Search devices:", 
                placeholder="Brand, model, description or ID...", 
                key="view_search_input"
            )

        # APPLICA TUTTI I FILTRI
        filtered_devices = []

        for d in devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial, manufacturer_date = d
    
            # Ottieni info room per questo device
            device_room = next((r for r in rooms if r[0] == room_id), None)
    
            # Filtro Ward
            if selected_ward_filter != "All":
                if not device_room or device_room[3] != int(selected_ward_filter):
                    continue
    
            # Filtro Room  
            if selected_room_filter != "All":
                if str(room_id) != selected_room_filter:
                    continue
    
            # Filtro Search
            if search:
                search_lower = search.lower()
                room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                search_text = f"{device_id} {description} {brand} {model} {room_info} {serial} ".lower()
                if search_lower not in search_text:
                    continue
    
            filtered_devices.append(d)

        # RISULTATI E ANALISI
        if filtered_devices:
            # Messaggio con info sui filtri
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
                # Trova info room e ward per questo device
                device_room = next((r for r in rooms if r[0] == d[2]), None)
        
                if device_room:
                    room_name = f"Floor {device_room[1]} - {device_room[2]}"
                    ward_id = device_room[3] if len(device_room) > 3 else None
            
                    # Trova ward info
                    if ward_id:
                        ward_info = next((w for w in wards if w[0] == ward_id), None)
                        ward_name = ward_info[1] if ward_info else "Unknown Ward"
                    else:
                        ward_name = "No Ward"
                else:
                    room_name = "No Room"
                    ward_name = "No Ward"
        
                row = [
                    d[12], #seial number
                    d[3],   # Description
                    d[8],   # Brand
                    d[9],   # Model
                    d[4],   # Class
                    ward_name,  # Ward
                    room_name,  # Room
                    d[6],   # Cost_INR
                    d[10],  # Installation_Date
                    d[13],  # Manufacturer_Date
                    d[11], #instrument code
                    #d[11] if len(d) > 11 else None,  # UDI_Number
                    "Yes" if d[7] else "No"   # Present
                ]
                df_display.append(row)

            df = pd.DataFrame(df_display, columns=['Seial number',
                'Description', 'Brand', 'Model', 'Class', 'Ward', 'Room',
                'Cost_INR', 'Installation_Date','Manufacturer date' ,'Intrument Code', 'Present'
            ])
    
            st.dataframe(df)
            # Statistiche rapide
            st.subheader("Quick Statistics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Devices", len(filtered_devices))

            with col2:
                ages = []
                for d in filtered_devices:
                    install_date = d[10]  # Installation_Date direttamente dalla tupla
                    if install_date:  # evita errori se è NULL
                        try:
                            from datetime import datetime, date
                    
                            # Convert to datetime object
                            if isinstance(install_date, str):
                                # Try different date formats
                                try:
                                    # Try YYYY-MM-DD format first
                                    install_date_obj = datetime.strptime(install_date, "%Y-%m-%d")
                                except ValueError:
                                    try:
                                        # Try DD/MM/YYYY format
                                        install_date_obj = datetime.strptime(install_date, "%d/%m/%Y")
                                    except ValueError:
                                        # Try MM/DD/YYYY format
                                        install_date_obj = datetime.strptime(install_date, "%m/%d/%Y")
                            elif isinstance(install_date, date):
                                install_date_obj = datetime.combine(install_date, datetime.min.time())
                            else:
                                install_date_obj = install_date
                    
                            age_years = (datetime.now() - install_date_obj).days / 365.25
                            if age_years >= 0:  # Only add positive ages
                                ages.append(age_years)
                        
                        except Exception as e:
                            # Debug: mostra l'errore (rimuovi dopo aver risolto)
                            # st.write(f"Date parsing error for {install_date}: {e}")
                            pass

                if ages:  # se ci sono date valide
                    avg_age = sum(ages) / len(ages)
                    st.metric("Avg Age", f"{avg_age:.1f} years")
                else:
                    st.metric("Avg Age", "N/A")

            with col3:
                total_cost = sum([float(d[6]) if d[6] else 0 for d in filtered_devices])  # cost_inr
                st.metric("Total Value", f"₹{total_cost:,.0f}")

            with col4:
                present_count = sum([1 for d in filtered_devices if d[7]])  # present
                st.metric("Present", f"{present_count}/{len(filtered_devices)}")

            # Grafici
            st.subheader("Analysis Charts")

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.write("**Devices by Class**")
                # Grafico per classe
                class_counts = {}
                for d in filtered_devices:
                    device_class = d[4] or 'Unknown'
                    class_counts[device_class] = class_counts.get(device_class, 0) + 1
        
                if class_counts:
                    st.bar_chart(class_counts)

            with chart_col2:
                st.write("**Devices by Age**")
                # Grafico per età
                age_ranges = {
                    "0-1 years": 0,
                    "1-3 years": 0, 
                    "3-5 years": 0,
                    "5-10 years": 0,
                    ">10 years": 0
                }
        
                for d in filtered_devices:
                    install_date = d[10]  # Installation_Date
            
                    # Calcola età
                    if install_date:
                        from datetime import date
                        try:
                            if isinstance(install_date, str):
                                if "/" in install_date:
                                    install_date_obj = dt.datetime.strptime(install_date, "%d/%m/%Y").date()
                                else:
                                    install_date_obj = date.fromisoformat(str(install_date))
                            else:
                                install_date_obj = install_date
                    
                            age_years = (date.today() - install_date_obj).days / 365.25
                        except:
                            age_years = 0
                    else:
                        age_years = 0
            
                    # Assegna alla fascia di età
                    if age_years <= 1:
                        age_ranges["0-1 years"] += 1
                    elif age_years <= 3:
                        age_ranges["1-3 years"] += 1
                    elif age_years <= 5:
                        age_ranges["3-5 years"] += 1
                    elif age_years <= 10:
                        age_ranges["5-10 years"] += 1
                    else:
                        age_ranges[">10 years"] += 1
        
                if any(age_ranges.values()):
                    st.bar_chart(age_ranges)

            

            # Esporta risultati
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
    
            # Suggerimenti per l'utente
            st.info("**Try:**")
            st.write("• Removing some filters")
            st.write("• Using different search terms") 
            st.write("• Selecting 'All' in the dropdown filters")
        #with st.spinner("Calculating fuzzy scores for all devices..."):
        #    results_data = []
        #    calculation_errors = []
        
        #    for d in devices:
        #        dev_id, nome, n_age, eqf, cost ,maint, fr, uptime, stanza = d
            
        #        rel_score, mis_score, crit_score = calculate_fuzzy_scores(n_age, eqf, cost, fr, uptime)
            
        #        if rel_score is not None and mis_score is not None and crit_score is not None:
        #            try:
        #                update_criticity(dev_id, crit_score)
        #                status = "✅"
        #            except Exception as e:
        #                status = f"❌ DB Error"
        #                calculation_errors.append(f"Device {dev_id}: {str(e)}")
                
        #            results_data.append({
        #                "ID": dev_id,
        #                "Name": nome or "N/A",
        #                "Room": stanza or "N/A",
        #                "Age (years)": f"{n_age:.2f}",
        #                "Reliability": rel_score,
        #                "Mission Critical": mis_score,
        #                "Criticity Score": crit_score,
        #                "Status": status
        #            })
        #        else:
        #            calculation_errors.append(f"Device {dev_id}: Fuzzy calculation failed")
        #            results_data.append({
        #                "ID": dev_id,
        #                "Name": nome or "N/A",
        #                "Room": stanza or "N/A", 
        #                "Age (years)": f"{n_age:.2f}",
        #                "Reliability": None,
        #                "Mission Critical": None,
        #                "Criticity Score": None,
        #                "Status": "❌ Error"
        #            })
    
        ## Display errors if any
        #if calculation_errors:
        #    with st.expander("⚠️ Calculation Errors", expanded=False):
        #        for error in calculation_errors:
        #            st.warning(error)
    
        ## Results display
        #if results_data:
        #    st.subheader(f"Analysis Results ({len(results_data)} devices)")
        
        #    results_df = pd.DataFrame(results_data)
        
            # Filter and sort options
            #col1, col2, col3 = st.columns(3)
            #with col1:
            #    sort_by = st.selectbox("Sort by:", 
            #                         ["Criticity Score", "Reliability", "Mission Critical", "ID"])
            #with col2:
            #    sort_order = st.radio("Order:", ["Descending", "Ascending"])
            #with col3:
            #    show_only_valid = st.checkbox("Show only valid results", value=True)
        
            ## Apply filters
            #display_df = results_df.copy()
            #if show_only_valid:
            #    display_df = display_df[display_df['Status'] == '✅']
        
            ## Apply sorting
            #if not display_df.empty and sort_by in display_df.columns:
            #    ascending = sort_order == "Ascending"
            #    if display_df[sort_by].dtype in ['float64', 'int64']:
            #        display_df = display_df.sort_values(sort_by, ascending=ascending, na_position='last')
        
            ## Display results table
            #st.dataframe(display_df, use_container_width=True)
        
            ## Summary statistics
            #if not display_df.empty:
            #    st.subheader("Summary Statistics Criticity Distribution")
            #    valid_results = display_df[display_df['Status'] == '✅']
            
            #    if not valid_results.empty:
            #        col1, col2, col3, col4, col5 = st.columns(5)
                
            #        with col1:
            #            avg_rel = valid_results['Reliability'].mean()
            #            st.metric("Avg Reliability", f"{avg_rel:.2f}")
                
            #        with col2:
            #            avg_mis = valid_results['Mission Critical'].mean()
            #            st.metric("Avg Mission Critical", f"{avg_mis:.2f}")
                
            #        with col3:
            #            avg_crit = valid_results['Criticity Score'].mean()
            #            st.metric("Avg Criticity", f"{avg_crit:.2f}")

            #        with col4:
            #            max_crit = valid_results['Criticity Score'].max()
            #            st.metric("Max Criticity", f"{max_crit:.2f}")

            #        with col5:
            #            High_criticity = len(valid_results[valid_results['Criticity Score'] > 7])
            #            st.metric("High Criticity Devices", High_criticity)


            #    criticity_ranges = {
            #        "Very Low (0-2)": len(valid_results[(valid_results['Criticity Score'] >= 0) & (valid_results['Criticity Score'] <= 2)]),
            #        "Low (2-4)": len(valid_results[(valid_results['Criticity Score'] > 2) & (valid_results['Criticity Score'] <= 4)]),
            #        "Medium (4-6)": len(valid_results[(valid_results['Criticity Score'] > 4) & (valid_results['Criticity Score'] <= 6)]),
            #        "High (6-8)": len(valid_results[(valid_results['Criticity Score'] > 6) & (valid_results['Criticity Score'] <= 8)]),
            #        "Very High (8-10)": len(valid_results[(valid_results['Criticity Score'] > 8) & (valid_results['Criticity Score'] <= 10)])
            #    }

            #    dist_df = pd.DataFrame(list(criticity_ranges.items()), columns=['Range', 'Count'])

            #    # Forzo l’ordine desiderato
            #    order = ["Very Low (0-2)", "Low (2-4)", "Medium (4-6)", "High (6-8)", "Very High (8-10)"]
            #    dist_df['Range'] = pd.Categorical(dist_df['Range'], categories=order, ordered=True)

            #    # Riordino il dataframe
            #    dist_df = dist_df.sort_values('Range')

            #    st.bar_chart(dist_df.set_index('Range'))    

        
            # Export functionality
            st.subheader("Export Results")
            if st.button("Download Results as CSV"):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"device_analysis_{dt.date.today()}.csv",
                    mime="text/csv"
                )

# =============================================================================
# PAGINA 2 Scoring Assessment
# =============================================================================

       
if page == "Prioritization Score":
    tab1,tab2=st.tabs(["Analysis Dashboard","Add score parameters"])
    with tab2:
        # Get available rooms
        all_devices = get_all_devices()

        # Filtra se c'è una ricerca
        # Prima ottieni tutti i dati necessari

        rooms = get_all_rooms()
        wards = get_all_wards()  # Assumendo che questa funzione esista

        # Crea le opzioni per i filtri
        ward_options = {"All": "All Wards"}
        ward_options.update({str(w[0]): w[1] for w in wards})  # ID: Nome Ward

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
            # Filtra le room in base al ward selezionato
            if selected_ward != "All":
                filtered_rooms = [r for r in rooms if r[3] == int(selected_ward)]  # Assumendo che r[3] sia ward_id
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
            # Barra di ricerca aggiuntiva
            search = st.text_input("🔍 Search devices:", placeholder="Search by ID, description, brand...")

        # APPLICA I FILTRI
        filtered_devices = []

        for d in all_devices:
            device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial_number, manufacturer_date = d
    
            # Ottieni info room per questo device
            device_room = next((r for r in rooms if r[0] == room_id), None)
    
            # Filtro Ward
            if selected_ward != "All":
                if not device_room or device_room[3] != int(selected_ward):  # r[3] = ward_id
                    continue
    
            # Filtro Room
            if selected_room != "All":
                if str(room_id) != selected_room:
                    continue
    
            # Filtro Search
            if search:
                search_lower = search.lower()
                room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                search_text = f"{device_id} {description} {brand} {model} {room_info}".lower()
                if search_lower not in search_text:
                    continue
    
            filtered_devices.append(d)

        # MESSAGGIO SE NESSUN RISULTATO
        if not filtered_devices:
            st.info("No devices found with the selected filters")
            st.stop()

        # SELECTBOX FINALE CON DISPOSITIVI FILTRATI

        device_options = {}
        for d in filtered_devices:
            device_id = d[0]
            room_id = d[2]
            description = d[3] or "No Description"
            brand = d[8] or "No Brand"
            model = d[9] or "No Model"

            # Trova room info
            device_room = next((r for r in rooms if r[0] == room_id), None)
            if device_room:
                ward_id = device_room[3]  # Assumendo che r[3] sia ward_id
                ward_info = next((w for w in wards if w[0] == ward_id), None)

                if ward_info:
                    ward_name = ward_info[1]  # Nome del ward
                    room_display = f"Floor {device_room[1]} - {device_room[2]}"
                    full_location = f"{ward_name} | {room_display}"
                else:
                    full_location = f"Floor {device_room[1]} - {device_room[2]}"
            else:
                full_location = "❌ No Location"
    
            label = f"ID:{device_id} | {description} | {brand} {model} | {full_location}"
            device_options[device_id] = label  # AGGIUNGI AL DIZIONARIO

        # CREA UNA SOLA SELECTBOX FUORI DAL LOOP
        selected_device_id = st.selectbox(
            "Choose device to edit:",
            options=list(device_options.keys()),
            format_func=lambda x: device_options[x],
            key="device_selector"  # Aggiungi una key unica
        )

        if selected_device_id:

       
    
            with st.form("add_device_form", clear_on_submit=True):
                # Recupera i dati del dispositivo selezionato
                data_device = get_device_by_id(selected_device_id)
    
                # Recupera eventuali parametri di scoring esistenti
                existing_params = get_scores_by_device_id(selected_device_id)
    
                
                col1, col2, col3, col4 = st.columns(4)
    
                with col1:
                    st.subheader("Age")
                    age_installation = data_device[10]
                    age_man=data_device[13]
                    oggi = dt.date.today()
                    age_years=0
                    if age_man is not None:
                        age_years = (oggi - age_man).days / 365
                    elif age_installation is not None:
                        age_years = (oggi - age_installation).days / 365
                    etax = age_years
                    st.info(f"Age: {age_years:.2f} years")


                with col2:
                    st.subheader("Mission Criticality")
        
                    # Determina il valore di default per usage_type
                    default_usage_type = "Analytical/Support"  # Default
                    if existing_params and len(existing_params) > 10:  # Assumendo che equipment_function_score sia all'indice 10
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
                        "Usage Type*", 
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

                    # Precompila uptime_percentage
                    default_uptime = 1.0  # Default
                    if existing_params and len(existing_params) > 9:  # Assumendo che uptime_percentage sia all'indice 9
                        default_uptime = existing_params[9]
        
                    uptime_percentage = st.number_input(
                        "Uptime hours per week", 
                        min_value=0.0, 
                        max_value=40.0, 
                        step=1.0,
                        value=float(default_uptime)
                    )
                    if uptime_percentage is None or uptime_percentage == 0:
                        uptime_percentage = 1

                    # Determina il valore di default per backup devices
                    default_backup_option = "0 backup devices"  # Default
                    if existing_params and len(existing_params) > 5:  # Assumendo che backup_device_available sia all'indice 5
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
                    st.subheader("Maintenance cost")
        
                    # Precompila cost_ratio
                    default_cost = 1.0  # Default
                    if existing_params and len(existing_params) > 8:  # Assumendo che cost_ratio sia all'indice 8
                        default_cost = existing_params[8]
        
                    cost_ratio = st.number_input(
                        "Cumulative maintenance cost over last three years (Laks)", 
                        min_value=0.0, 
                        max_value=100000000.0, 
                        step=10000.0,
                        value=float(default_cost)
                    )
                    if cost_ratio is None or cost_ratio == 0:
                        cost_ratio = 1

                with col4:
                    st.subheader("Support")
        
                    # Precompila end_of_life e end_of_support
                    default_end_of_life = False
                    default_end_of_support = False
        
                    if existing_params and len(existing_params) > 13:
                        eol_val = existing_params[13]  # Assumendo che end_of_life sia all'indice 13
                        if eol_val == 1:
                            default_end_of_life = True
                        elif eol_val == 2:
                            default_end_of_support = True
        
                    end_of_life = st.checkbox("End of Life", value=default_end_of_life)
                    end_of_support = st.checkbox("End of Support", value=default_end_of_support)
        
                    if end_of_support:
                        end_of_life_numeric = 2  # End of support
                    elif end_of_life:
                        end_of_life_numeric = 1  # End of life
                    else:
                        end_of_life_numeric = 0  # Life (attivo)

                    # Determina il valore di default per spare parts
                    default_spare_parts_option = "Import and NO availability of spare parts"  # Default
                    if existing_params and len(existing_params) > 3:  # Assumendo che spare_parts_available sia all'indice 3
                        spare_val = existing_params[3]
                        if spare_val == 1:
                            default_spare_parts_option = "Local production and availability of spare parts"
                        elif spare_val == 2:
                            default_spare_parts_option = "Import and availability of spare parts"
                        elif spare_val == 3:
                            default_spare_parts_option = "Local production and NO availability of spare parts"
                        elif spare_val == 4:
                            default_spare_parts_option = "Import and NO availability of spare parts"
        
                    spare_parts_options = [
                        "Local production and availability of spare parts", 
                        "Import and availability of spare parts", 
                        "Local production and NO availability of spare parts", 
                        "Import and NO availability of spare parts"
                    ]
                    default_spare_parts_index = spare_parts_options.index(default_spare_parts_option)
        
                    checkbox_spare_parts = st.selectbox(
                        "Choose one option", 
                        options=spare_parts_options,
                        index=default_spare_parts_index
                    )
        
                    if checkbox_spare_parts == "Local production and availability of spare parts":
                        spare_parts_available = 1
                    elif checkbox_spare_parts == "Import and availability of spare parts":
                        spare_parts_available = 2
                    elif checkbox_spare_parts == "Local production and NO availability of spare parts":
                        spare_parts_available = 3
                    elif checkbox_spare_parts == "Import and NO availability of spare parts":
                        spare_parts_available = 4

                # Precompila le note
                default_notes = ''  # Default
                if existing_params and len(existing_params) > 12:  # Assumendo che notes sia all'indice 12
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
                        # Delete existing parameters and insert new ones
                        delete_scoring_parameters(selected_device_id)
                        assessment_date = dt.date.today()
                        n_failure = 0

                        setup_fuzzy_system()
                        cost = (float(cost_ratio) / float(data_device[6])) * 100
                        end_of_support_numeric = 0

                        # Debug: stampa tutti i valori di input
                        st.write("DEBUG - Input values:")
                        st.write(f"age_years: {age_years}")
                        st.write(f"equipment_function_score: {equipment_function_score}")
                        st.write(f"cost: {cost}")
                        st.write(f"failure_rate: {failure_rate}")
                        st.write(f"uptime_percentage: {uptime_percentage}")
                        st.write(f"end_of_life_numeric: {end_of_life_numeric}")
                        st.write(f"end_of_support_numeric: {end_of_support_numeric}")
                        st.write(f"spare_parts_available: {spare_parts_available}")
                        st.write(f"backup_device_available: {backup_device_available}")

                        try:
                            mis_score, supp_score, crit_score = calculate_fuzzy_scores(
                                age_years,                    # normalized_age
                                equipment_function_score,     # eq_function
                                cost,                        # cost_levels
                                failure_rate,                # failure_rate
                                uptime_percentage,           # up_time
                                end_of_life_numeric,         # end_life
                                end_of_support_numeric,      # end_support
                                spare_parts_available,       # import_availability
                                backup_device_available      # backup
                            )
                            st.write(f"DEBUG - Output values:")
                            st.write(f"mis_score: {mis_score}")
                            st.write(f"supp_score: {supp_score}")
                            st.write(f"crit_score: {crit_score}")
                        except Exception as e:
                            st.error(f"Error in calculate_fuzzy_scores: {str(e)}")
                            mis_score, supp_score, crit_score = None, None, None

                        # Controlla i valori prima di formattarli
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
                            insert_scoring_parameters(
                                selected_device_id, assessment_date, spare_parts_available, age_years, 
                                backup_device_available, n_failure, 0, cost_ratio, uptime_percentage, 
                                equipment_function_score, 0, notes, end_of_life_numeric, end_of_support, 
                                mis_score, supp_score, crit_score
                            )
                            st.success(f"✅ Device parameters successfully updated! Device ID: {selected_device_id}")
                        else:
                            st.error("Error calculating Criticality Score")
                    except Exception as e:
                        st.error(f"❌ Error updating device: {str(e)}")

            # Conteggio dispositivi
            try:
                all_devices = get_all_devices()
                total_devices = len(all_devices)
            
                # Conta quanti dispositivi hanno parametri completi
                devices_with_params = 0
                for device in all_devices:
                    device_id = device[0]
                    existing_params = get_scores_by_device_id(device_id)
                    if existing_params and len(existing_params) >= 14:
                        devices_with_params += 1
            
                devices_without_params = total_devices - devices_with_params
            
                # Mostra statistiche
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Devices", total_devices)
                with col2:
                    st.metric("Ready for Calculation", devices_with_params, delta=None)
                with col3:
                    st.metric("Missing Parameters", devices_without_params, delta=None)
            
                st.divider()
            
                # Pulsante per calcolare tutti i punteggi (FUORI DAL FORM)
                if st.button("Calculate All Scores", type="secondary", use_container_width=True):
                    if devices_with_params > 0:
                        with st.spinner('Calculating scores for all devices...'):
                            calculate_all_devices_scores()
                    else:
                        st.warning("No devices found with complete parameters. Please add parameters first using the 'Add score parameters' tab.")
            
            
            except Exception as e:
                st.error(f"Error loading device information: {str(e)}")

    with tab1:
        
    
    
                    all_devices = get_all_devices()

                    # Filtra se c'è una ricerca
                    # Prima ottieni tutti i dati necessari

                    rooms = get_all_rooms()
                    wards = get_all_wards()  # Assumendo che questa funzione esista

                    # Crea le opzioni per i filtri
                    ward_options = {"All": "All Wards"}
                    ward_options.update({str(w[0]): w[1] for w in wards})  # ID: Nome Ward

                    room_options = {"All": "All Rooms"}
                    room_options.update({f"{r[0]}": f"Floor {r[1]} - {r[2]}" for r in rooms})

                    # FILTRI DROPDOWN
  
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        selected_ward = st.selectbox(
                            "Filter by Ward:",
                            options=list(ward_options.keys()),
                            format_func=lambda x: ward_options[x],key='c'
                        )

                    with col2:
                        # Filtra le room in base al ward selezionato
                        if selected_ward != "All":
                            filtered_rooms = [r for r in rooms if r[3] == int(selected_ward)]  # Assumendo che r[3] sia ward_id
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
                        # Barra di ricerca aggiuntiva
                        search = st.text_input("🔍 Search devices:", placeholder="Search by ID, description, brand....")

                    # APPLICA I FILTRI
                    filtered_devices = []

                    for d in all_devices:
                        device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial_number, manufacturer_date = d
    
                        # Ottieni info room per questo device
                        device_room = next((r for r in rooms if r[0] == room_id), None)
    
                        # Filtro Ward
                        if selected_ward != "All":
                            if not device_room or device_room[3] != int(selected_ward):  # r[3] = ward_id
                                continue
    
                        # Filtro Room
                        if selected_room != "All":
                            if str(room_id) != selected_room:
                                continue
    
                        # Filtro Search
                        if search:
                            search_lower = search.lower()
                            room_info = f"Floor {device_room[1]} - {device_room[2]}" if device_room else ""
        
                            search_text = f"{device_id} {description} {brand} {model} {room_info}".lower()
                            if search_lower not in search_text:
                                continue
    
                        filtered_devices.append(d)

                    # MESSAGGIO SE NESSUN RISULTATO
                    if not filtered_devices:
                        st.info("No devices found with the selected filters")
                        st.stop()

   
                    # TABELLA PRINCIPALE CON TUTTI I DATI

                    if filtered_devices:
                    # Messaggio con info sui filtri
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
    
                        # TABELLA DEI DISPOSITIVI - VERSIONE SEMPLIFICATA
                        #st.subheader(f"{len(filtered_devices)} Devices ")
    
                    tab1, tab2, tab3, tab4 = st.tabs(["Overview Table", "Score Analytics", "Operational Metrics", "Financial Analysis"])

                    # LOGICA UNIFICATA - Creazione dati una sola volta
                    df_data = []
                    valid_scores = []
                    device_lookup = {}  # Per lookup rapido nei tab successivi

                    for d in filtered_devices:
                        device_id, parent_id, room_id, description, device_class, usage_type, cost_inr, present, brand, model, install_date, udi, serial_number, manufacturer_date = d

                        # MEMORIZZA nel dizionario di lookup per i tab successivi
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

                        # Get score data
                        score = get_scores_by_device_id(device_id)

                        # Calcola età
                        age_years = 0
                      
                        if manufacturer_date is not None:
                           age_years = (oggi - manufacturer_date).days / 365
                        elif install_date is not None:
                            age_years = (oggi - install_date).days / 365
                        # Logica per backup
                        back = 'N/A'
                        if score and score[5] is not None:
                            if score[5] == 2:
                                back = ">=3"
                            elif score[5] == 1:
                                back = "1-2"
                            elif score[5] == 0:
                                back = "0"
    
                        # Logica per end of life/support
                        life = 'N/A'
                        if score and score[13] is not None:
                            if score[13] == 0:
                                life = "0"
                            elif score[13] == 1:
                                life = "End of Life"
                            else:
                                life = "End of Support"
    
                        # Logica per spare parts
                        parts = 'N/A'
                        if score and score[3] is not None:
                            if score[3] == 1:
                                parts = "Local production and avalability of spare parts"
                            elif score[3] == 2:
                                parts = "Imported and avalability of spare parts"
                            elif score[3] == 3:
                                parts = "Local production and NO avalability of spare parts"
                            elif score[3] == 4:
                                parts = "Imported and NO avalability of spare parts"

                        eq1='N/A'
                        if score and score[10] is not None:
                            if score[10]==1:
                                eq1="Analytical/Support"
                            elif score[10]==2:
                                eq1="Diagnostic"
                            elif score[10]==3:
                                eq1="Therapeutic"
                            elif score[10]==4:
                                eq1="Life Saving/Life Support"

                        # Aggiungi a valid_scores se ha dati di scoring
                        if score:
                            valid_scores.append((device_id, score, age_years, cost_inr))

                        # Crea row con ordine richiesto
                        row_data = {
                            'Description': description or 'N/A',
                            'Brand': brand or 'N/A',
                            'Model': model or 'N/A',
                            'Criticity': round(score[17], 2) if score and score[17] is not None else 'N/A',
                            'Mission Score': round(score[15], 2) if score and score[15] is not None else 'N/A',
                            'Support Score': round(score[16], 2) if score and score[16] is not None else 'N/A',
                            'Age (years)': round(age_years, 1),
                            'Maintenance  %': round((score[8]/cost_inr)*100, 2) if score and score[8] and cost_inr is not None else 'N/A',
                            'Usage Types': eq1 or "N/A" ,
                            'Uptime (hr)': round(score[9], 1) if score and score[9] is not None else 'N/A',
                            'Backup Available': back,
                            'End of Life/Support': life,
                            'Import and availability od spare parts': parts,
                            'Ward': ward_options.get(str(next((r[3] for r in rooms if r[0] == room_id), None)), 'N/A') if room_id else 'N/A',
                            'Room': room_options.get(str(room_id), 'N/A') if room_id else 'N/A'
                        }

                        df_data.append(row_data)

                    df = pd.DataFrame(df_data)

                    with tab1:
                        # SEZIONE FUZZY LOGIC RESULTS (mantenuta e migliorata)
                        try:
                            cur.execute("SELECT COUNT(*) FROM scoring_parameters")
                            scoring_count = cur.fetchone()[0]

                            if scoring_count > 0:
                                # Statistiche rapide sui risultati fuzzy
                                col1, col2 = st.columns(2)

                                with col1:
                                    high_risk_count = 0
                                    for d in filtered_devices:
                                        device_id = d[0]
                                        score = get_scores_by_device_id(device_id)
                                        if score and score[17] is not None and score[17] > 6:
                                            high_risk_count += 1
                
                                    st.metric("High Risk Devices", high_risk_count, 
                                                delta="⚠️ Need Action" if high_risk_count > 0 else "✅ All Good")

                                with col2:
                                    analyzed_devices = len(valid_scores)
                                    total_devices = len(filtered_devices)
                                    coverage = (analyzed_devices / total_devices) * 100 if total_devices > 0 else 0
                                    st.metric("Analysis Coverage", f"{coverage:.1f}%", 
                                                delta=f"{analyzed_devices}/{total_devices} devices")

                            else:
                                st.warning("⚠️ No fuzzy logic results found. Run analysis in 'Scoring Assessment' page first.")

                        except Exception as e:
                            st.error(f"Error checking scoring data: {e}")
    
                        st.dataframe(df)

                        # Export functionality
                        if st.button("📥 Export to CSV"):
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"device_analysis_{dt.date.today()}.csv",
                                mime="text/csv"
                            )

                    with tab2:
                        # Controlla se ci sono valid_scores PRIMA di procedere
                        if valid_scores:
                            # Metriche principali
                            col1, col2, col3 = st.columns(3)

                            # Calcola metriche usando la logica filtered_devices + score
                            criticities = []
                            mission_scores = []
                            support_scores = []
        
                            for d in filtered_devices:
                                device_id = d[0]
                                score = get_scores_by_device_id(device_id)
                                if score:
                                    if score[17] is not None:
                                        criticities.append(score[17])
                                    if score[15] is not None:
                                        mission_scores.append(score[15])
                                    if score[16] is not None:
                                        support_scores.append(score[16])

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

                            # Grafici
                            chart_col1, chart_col2 = st.columns(2)

                            with chart_col1:
                                st.write("**Criticity Distribution**")
    
                                # Raccoglie criticity scores usando la nuova logica
                                criticities = []
                                for d in filtered_devices:
                                    device_id = d[0]
                                    score = get_scores_by_device_id(device_id)
                                    if score and score[17] is not None:
                                        criticities.append(score[17])
    
                                if criticities:
                                    # Crea ranges per una visualizzazione più bella
                                    criticity_ranges = {
                                        "Very Low (0-2)": sum(1 for c in criticities if 0 <= c <= 2),
                                        "Low (2-4)": sum(1 for c in criticities if 2 <= c <= 4),
                                        "Medium (4-6)": sum(1 for c in criticities if 4 < c <= 6),
                                        "High (6-8)": sum(1 for c in criticities if 6 < c <= 8),
                                        "Very High (8-10)": sum(1 for c in criticities if 8 < c <= 10)
                                    }
        
                                    # Grafico a barre con colori graduali
                                    fig = go.Figure(data=[
                                        go.Bar(
                                            x=list(criticity_ranges.keys()), 
                                            y=list(criticity_ranges.values()),
                                            marker_color=['#28a745', '#ffc107', '#fd7e14', '#dc3545'],
                                            text=list(criticity_ranges.values()),
                                            textposition='auto'
                                        )
                                    ])
        
                                    fig.update_layout(
                                        xaxis_title="Criticity Level",
                                        yaxis_title="Number of Devices",
                                        height=400,
                                        showlegend=False
                                    )
        
                                    st.plotly_chart(fig, use_container_width=True)
        
                       
                                else:
                                    st.info("No criticity data available")

                            with chart_col2:
                                st.write("**High Risk Devices**")
                                high_risk_devices = []
            
                                for d in filtered_devices:
                                    device_id = d[0]
                                    score = get_scores_by_device_id(device_id)
                                    if score and score[17] is not None and score[17] > 6.5:
                                        device_info = device_lookup.get(device_id, {})
                                        device_name = device_info.get('description', 'Unknown Device')
                    
                                        high_risk_devices.append({
                                            'Serial Number': device_info.get('serial_number','N/A'),
                                            'Device description': device_name,
                                            'Criticity': round(score[17], 2),
                                            'Mission Score': round(score[15], 2) if score[15] is not None else 'N/A',
                                            'Support Score': round(score[16], 2) if score[16] is not None else 'N/A'
                                        })

                                if high_risk_devices:
                                    risk_df = pd.DataFrame(high_risk_devices)
                                    st.dataframe(risk_df, use_container_width=True)
                                    st.warning(f"⚠️ {len(high_risk_devices)} devices require attention!")
                                else:
                                    st.success("✅ No high-risk devices found!")
                        else:
                            st.warning("No scoring data available. Please run fuzzy logic analysis first.")

                    with tab3:
                        if valid_scores:
                            # Metriche operative usando la logica filtered_devices + score
                            col1, col2, col3, col4 = st.columns(4)

                            spare_parts_count = 0
                            downtime_values = []
                            eol_devices = 0
                            eos_devices = 0
                            imports=0
        
                            for d in filtered_devices:
                                device_id = d[0]
                                score = get_scores_by_device_id(device_id)
                                if score:
                                    if score[3] ==3 or score[3]==4:
                                        imports+=1
                                    if score[3] == 1 or score[3]==2 :
                                        spare_parts_count += 1
                                    if score[7] is not None:
                                        downtime_values.append(score[7])
                                    if score[13] and score[13] == 1:
                                        eol_devices += 1
                                    if score[13] and score[13] == 2:
                                        eos_devices += 1

                            with col1:
                                avg_downtime = sum(downtime_values) / len(downtime_values) if downtime_values else 0
                                st.metric("Avg Downtime", f"{avg_downtime:.1f} hrs")


                            with col2:
                                spare_percentage = (spare_parts_count / len(valid_scores)) * 100
                                st.metric("Spare Parts Available", f"{spare_parts_count}/{len(valid_scores)}", 
                                            delta=f"{spare_percentage:.1f}%")

                            with col3:
                                st.metric("End of Life Devices",  f"{eol_devices}/{len(valid_scores)}", 
                                            delta="⚠️ Need Attention" if eol_devices > 0 else "✅ All Good")

                            with col4:
                                st.metric("End of Support Devices",  f"{eos_devices}/{len(valid_scores)}", 
                                            delta="⚠️ Need Attention" if eos_devices > 0 else "✅ All Good")

                            # Grafici operativi
                            op_col1, op_col2 = st.columns(2)
        
                            uptimes = []
                            backup_available = 0
                            imports1=0
        
                            for d in filtered_devices:
                                device_id = d[0]
                                score = get_scores_by_device_id(device_id)
                                if score:
                                    if score[3] ==2:
                                        imports1+=1
                                    if score[3]==4:
                                        imports1+=1
                                    if score[9] is not None:
                                        uptimes.append(score[9])
                                    if score[5] ==2:
                                        backup_available += 1
                                    if score[5] ==1:
                                        backup_available += 1

                            with op_col1:
                                if uptimes:
                                    uptime_ranges = {
                                        "Low": sum(1 for u in uptimes if 0 <= u < 14),
                                        "Medium": sum(1 for u in uptimes if 14 <= u < 24),
                                        "High": sum(1 for u in uptimes if u >= 24),
                                    }

                                    fig = go.Figure(data=[
                                        go.Bar(x=list(uptime_ranges.keys()), y=list(uptime_ranges.values()),
                                                marker_color=['#dc3545', '#ffc107', '#28a745'])
                                    ])
                                    fig.update_layout(title="Device Uptime Distribution", height=400)
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("No uptime data available")

                            with op_col2:
                                fig = go.Figure(data=[
                                    go.Bar(name='Available', x=['Backup', 'Devices Imported'], 
                                            y=[backup_available, imports1], marker_color='#28a745'),
                                    go.Bar(name='Not Available', x=['Backup', 'Devices Imported'], 
                                            y=[len(valid_scores) - backup_available, len(valid_scores) - imports1], 
                                            marker_color='#dc3545')
                                ])
                                fig.update_layout(barmode='stack', title="Backup & Imported devices", height=400)
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No operational data available for analysis.")

                    with tab4:
                        if valid_scores:
                            # Metriche finanziarie usando la logica filtered_devices + score
                            costs = []
                            maintenance_costs = []
                            cost_ratio = []
        
                            for d in filtered_devices:
                                device_id = d[0]
                                cost_inr = d[6]  # cost from filtered_devices
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

                            # Grafici finanziari
                            fin_chart1, fin_chart2 = st.columns(2)
                            with fin_chart1:
                                class_costs = {}
                                for d in filtered_devices:
                                    ward_name = get_ward_name_by_device(d[0])
                                    cost = d[6] or 0  # cost_inr from filtered_devices

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

                                    # Divisione elemento per elemento (gestisce automaticamente divisione per zero)
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

                            # Analisi per età
                            age_cost_data = []
                            for d in filtered_devices:
                                device_id = d[0]
                                install_date = d[10]  # install_date from filtered_devices
                                cost_inr = d[6]  # cost_inr from filtered_devices
                                score = get_scores_by_device_id(device_id)
            
                                # Calcola età
                                age_years = 0
                                if install_date:
                                    try:
                                        age_years = (dt.date.today() - install_date).days / 365.25
                                    except:
                                        age_years = 0
            
                                if age_years > 0 and cost_inr is not None and score:
                                    age_range = "0-2 years" if age_years <= 2 else "3-5 years" if age_years <= 5 else "6-10 years" if age_years <= 10 else ">10 years"
                                    age_cost_data.append({
                                        'Age Range': age_range,
                                        'Asset Value': cost_inr,
                                        'Maintenance Cost': score[8] if score[8] is not None else 0,
                                        'Device Age': age_years
                                    })

                            if age_cost_data:
                                age_df = pd.DataFrame(age_cost_data)
                                fig = px.box(age_df, x='Age Range', y='Asset Value',
                                            title="Asset Value Distribution by Age")
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No financial data available for analysis.")

                    # Sezione export finale (se non ci sono dispositivi che matchano i filtri)
                    if not filtered_devices:
                        st.info("No devices match the current filters. Please adjust your search criteria.")
    
                    # Esporta risultati
                    st.subheader("Export Results")

                    if st.button("📥 Export Final Results"):
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"devices_analysis_{dt.date.today()}.csv",
                            mime="text/csv"
                        )
  
                    #with st.spinner("Calculating fuzzy scores for all devices..."):
                    #    results_data = []
                    #    calculation_errors = []
        
                    #    for d in devices:
                    #        dev_id, nome, n_age, eqf, cost ,maint, fr, uptime, stanza = d
            
                    #        rel_score, mis_score, crit_score = calculate_fuzzy_scores(n_age, eqf, cost, fr, uptime)
            
                    #        if rel_score is not None and mis_score is not None and crit_score is not None:
                    #            try:
                    #                update_criticity(dev_id, crit_score)
                    #                status = "✅"
                    #            except Exception as e:
                    #                status = f"❌ DB Error"
                    #                calculation_errors.append(f"Device {dev_id}: {str(e)}")
                
                    #            results_data.append({
                    #                "ID": dev_id,
                    #                "Name": nome or "N/A",
                    #                "Room": stanza or "N/A",
                    #                "Age (years)": f"{n_age:.2f}",
                    #                "Reliability": rel_score,
                    #                "Mission Critical": mis_score,
                    #                "Criticity Score": crit_score,
                    #                "Status": status
                    #            })
                    #        else:
                    #            calculation_errors.append(f"Device {dev_id}: Fuzzy calculation failed")
                    #            results_data.append({
                    #                "ID": dev_id,
                    #                "Name": nome or "N/A",
                    #                "Room": stanza or "N/A", 
                    #                "Age (years)": f"{n_age:.2f}",
                    #                "Reliability": None,
                    #                "Mission Critical": None,
                    #                "Criticity Score": None,
                    #                "Status": "❌ Error"
                    #            })
    
                    ## Display errors if any
                    #if calculation_errors:
                    #    with st.expander("⚠️ Calculation Errors", expanded=False):
                    #        for error in calculation_errors:
                    #            st.warning(error)
    
                    ## Results display
                    #if results_data:
                    #    st.subheader(f"Analysis Results ({len(results_data)} devices)")
        
                    #    results_df = pd.DataFrame(results_data)
        
                        # Filter and sort options
                        #col1, col2, col3 = st.columns(3)
                        #with col1:
                        #    sort_by = st.selectbox("Sort by:", 
                        #                         ["Criticity Score", "Reliability", "Mission Critical", "ID"])
                        #with col2:
                        #    sort_order = st.radio("Order:", ["Descending", "Ascending"])
                        #with col3:
                        #    show_only_valid = st.checkbox("Show only valid results", value=True)
        
                        ## Apply filters
                        #display_df = results_df.copy()
                        #if show_only_valid:
                        #    display_df = display_df[display_df['Status'] == '✅']
        
                        ## Apply sorting
                        #if not display_df.empty and sort_by in display_df.columns:
                        #    ascending = sort_order == "Ascending"
                        #    if display_df[sort_by].dtype in ['float64', 'int64']:
                        #        display_df = display_df.sort_values(sort_by, ascending=ascending, na_position='last')
        
                        ## Display results table
                        #st.dataframe(display_df, use_container_width=True)
        
                        ## Summary statistics
                        #if not display_df.empty:
                        #    st.subheader("Summary Statistics Criticity Distribution")
                        #    valid_results = display_df[display_df['Status'] == '✅']
            
                        #    if not valid_results.empty:
                        #        col1, col2, col3, col4, col5 = st.columns(5)
                
                        #        with col1:
                        #            avg_rel = valid_results['Reliability'].mean()
                        #            st.metric("Avg Reliability", f"{avg_rel:.2f}")
                
                        #        with col2:
                        #            avg_mis = valid_results['Mission Critical'].mean()
                        #            st.metric("Avg Mission Critical", f"{avg_mis:.2f}")
                
                        #        with col3:
                        #            avg_crit = valid_results['Criticity Score'].mean()
                        #            st.metric("Avg Criticity", f"{avg_crit:.2f}")

                        #        with col4:
                        #            max_crit = valid_results['Criticity Score'].max()
                        #            st.metric("Max Criticity", f"{max_crit:.2f}")

                        #        with col5:
                        #            High_criticity = len(valid_results[valid_results['Criticity Score'] > 7])
                        #            st.metric("High Criticity Devices", High_criticity)


                        #    criticity_ranges = {
                        #        "Very Low (0-2)": len(valid_results[(valid_results['Criticity Score'] >= 0) & (valid_results['Criticity Score'] <= 2)]),
                        #        "Low (2-4)": len(valid_results[(valid_results['Criticity Score'] > 2) & (valid_results['Criticity Score'] <= 4)]),
                        #        "Medium (4-6)": len(valid_results[(valid_results['Criticity Score'] > 4) & (valid_results['Criticity Score'] <= 6)]),
                        #        "High (6-8)": len(valid_results[(valid_results['Criticity Score'] > 6) & (valid_results['Criticity Score'] <= 8)]),
                        #        "Very High (8-10)": len(valid_results[(valid_results['Criticity Score'] > 8) & (valid_results['Criticity Score'] <= 10)])
                        #    }

                        #    dist_df = pd.DataFrame(list(criticity_ranges.items()), columns=['Range', 'Count'])

                        #    # Forzo l’ordine desiderato
                        #    order = ["Very Low (0-2)", "Low (2-4)", "Medium (4-6)", "High (6-8)", "Very High (8-10)"]
                        #    dist_df['Range'] = pd.Categorical(dist_df['Range'], categories=order, ordered=True)

                        #    # Riordino il dataframe
                        #    dist_df = dist_df.sort_values('Range')

                        #    st.bar_chart(dist_df.set_index('Range'))    

        
                        # Export functionality
                        st.subheader("Export Results")
                        if st.button("Download Results as CSV"):
                            csv = display_df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"device_analysis_{dt.date.today()}.csv",
                                mime="text/csv"
                            )

  



# =============================================================================
# PAGINA 4: ADMIN PANEL
# =============================================================================

elif page == "Admin Panel":
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
    
