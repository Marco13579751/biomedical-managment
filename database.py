import psycopg2
from psycopg2 import pool
import bcrypt
import datetime
import os
import streamlit as st

# --- Connessione PostgreSQL ---


def get_db_connection():
    # Se esiste "streamlit secrets" (quando online), usa quello
        # if hasattr(st, 'secrets') and 'postgres' in st.secrets:
         return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"]
        )

    
    # # Altrimenti usa locale (per quando sviluppi sul tuo PC)
    # return psycopg2.connect(
    #     # dbname="blood_bank",
    #     dbname="homibaba",
    #     user="postgres",
    #     password="123456",
    #     host="localhost",
    #     port="5432"
    # )
    # Connection Pooler - porta 6543 (bypassa firewall)
# ============================================
# POOL DI CONNESSIONI (nuovo - aggiungere)
# ============================================
conn = get_db_connection()
cur = conn.cursor()

@st.cache_resource
def get_connection_pool():
    """Crea un pool di connessioni riutilizzabili"""
    return psycopg2.pool.SimpleConnectionPool(
        1, 20,  # min 1, max 20 connessioni
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )

def get_db_conn():
    """Ottieni connessione dal pool"""
    pool = get_connection_pool()
    return pool.getconn()

def release_db_connection(conn):
    """Rilascia connessione al pool"""
    pool = get_connection_pool()
    pool.putconn(conn)

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

# --- Funzioni DB Dispositivi ---
# def insert_device(nome, normalized_age, eq_function, cost_levels,cumulative_maintenance, failure_rate, up_time, stanza=None):
#     cur.execute("""
#         INSERT INTO dispositivi (nome, normalized_age, eq_function, cost_levels, cumulative_maintenance, failure_rate, up_time, stanza)
#         VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
#     """, (nome, normalized_age, eq_function, cost_levels,cumulative_maintenance, failure_rate, up_time, stanza))
#     conn.commit()

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
# =============================================================================
# AGGIUNGI QUESTE FUNZIONI AL TUO database.py
# =============================================================================

# Fuzzy matching (opzionale)
try:
    from thefuzz import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

def classify_device_eq_function(description):
    """
    Classifica automaticamente un dispositivo e restituisce eq_function
    
    Args:
        description: string - descrizione del dispositivo
        
    Returns:
        int: 1-4 (1=Support, 2=Diagnostic, 3=Therapeutic, 4=Life Saving)
    """
    if not description:
        return 1
    
    desc = description.lower().replace('_', '').replace('-', '').replace(' ', '')
    
    # Life Saving (4)
    life_saving = [# Ventilators
    'ventilator', 'ventilator machine', 'mechanical ventilator',
    'respirator', 'breathing machine',
    
    # Defibrillators
    'defibrillator', 'defibrilator',  # include common typo
    'aed', 'automated external defibrillator',
    'cardiac defibrillator',
    
    # Anesthesia
    'anesthesia', 'anaesthesia', 'anesthesia machine', 'anaesthesia machine',
    'anesthesia workstation', 'anaesthesia workstation',
    'anesthesia gas module', 'anaesthesia gas module',
    'gas anesthesia', 'gas anaesthesia',
    
    # ICU/Critical Care Monitors
    'icu monitor', 'icu patient monitor',
    'intensive care monitor', 'critical care monitor',
    'bedside monitor icu', 'icu bedside monitor',
    'multi parameter monitor icu', 'multiparameter monitor icu',
    
    # Cardiac Monitors (Critical)
    'cardiac monitor', 'heart monitor',
    'ecg monitor critical', 'ekg monitor critical',
    'telemetry monitor', 'cardiac telemetry',
    
    # Life Support
    'life support', 'life support system',
    'ecmo', 'extracorporeal membrane oxygenation',
    'heart lung machine', 'cardiopulmonary bypass',
    
    # Oxygen/Respiratory Support
    'oxygen concentrator', 'o2 concentrator',
    'oxygen therapy', 'high flow oxygen',
    
    # Pacemakers
    'pacemaker', 'cardiac pacemaker',
    'temporary pacemaker', 'external pacemaker',
    
    # Emergency Equipment
    'emergency ventilator', 'emergency defibrillator',
    'crash cart monitor', 'resuscitation monitor',
    'code blue equipment',
    
    # Neonatal Critical
    'neonatal ventilator', 'infant ventilator',
    'nicu monitor', 'neonatal icu monitor',]
    for keyword in life_saving:
        if keyword in desc:
            return 4
    
    # Therapeutic (3)
    therapeutic = [# Infusion Pumps
    'infusion pump', 'infusion device', 'iv pump',
    'volumetric pump', 'volumetric infusion pump',
    'smart pump', 'infusion therapy',
    
    # Syringe Pumps
    'syringe pump', 'syringe driver',
    'micro syringe pump', 'microsyringe pump',
    
    # Dialysis
    'dialysis', 'dialysis machine', 'hemodialysis', 'hemodialysis machine',
    'peritoneal dialysis', 'renal dialysis',
    'dialyzer', 'kidney machine',
    
    # Surgical Equipment
    'surgical unit', 'surgery system',
    'electrosurgical unit', 'esu', 'electrosurgical generator',
    'diathermy', 'diathermy unit', 'electrocautery',
    'argon plasma coagulation', 'apc unit',
    
    # Surgical Tools
    'cusa', 'cavitron ultrasonic surgical aspirator',
    'harmonic scalpel', 'ultrasonic surgical',
    'surgical drill', 'powered surgical', 'surgical saw',
    'pulse lavage', 'pulsed lavage', 'wound irrigation',
    'reciprocating saw', 'oscillating saw', 'bone saw',
    'dermatome', 'skin graft',
    'micro drill', 'microdrill', 'drilling system',
    
    # Lasers (Therapeutic)
    'laser', 'surgical laser', 'laser therapy',
    'co2 laser', 'yag laser', 'excimer laser',
    'diode laser', 'argon laser',
    
    # Respiratory Therapy
    'nebulizer', 'nebuliser', 'aerosol therapy',
    'cpap', 'cpap machine', 'continuous positive airway',
    'bipap', 'bipap machine', 'bilevel positive airway',
    'bpap', 'bpap apparatus', 'bp apparatus', 'breathing therapy',
    
    # Incubators (Neonatal)
    'infant incubator', 'baby incubator', 'neonatal incubator',
    'infant warmer', 'radiant warmer', 'overhead warmer',
    
    # Blood/Platelet Equipment
    'platelet incubator', 'platelet agitator',
    'platelet incubator with agitator', 'platelet incubator and agitator',
    'platelleteincubator', 'platelleteagitator',  # typo versions
    'blood warmer', 'blood warming',
    
    # Phototherapy
    'phototherapy', 'phototherapy unit', 'bilirubin light',
    'blue light therapy', 'jaundice light',
    
    # Radiotherapy
    'linear accelerator', 'linac', 'radiotherapy unit',
    'cobalt unit', 'telecobalt', 'telecobalt machine',
    'bhabhatrone', 'radiation therapy',
    'ct simulator', 'ct simulation',
    
    # Body Temperature Management
    'body warmer', 'patient warmer', 'warming blanket',
    'hypothermia machine', 'cooling blanket',
    
    # Irrigation
    'irrigation pump', 'arthroscopy pump',
    'hysteroscopy pump', 'surgical irrigation',
    
    # NICU/Pediatric
    'pediatric ventilator', 'paediatric ventilator',
    'pediatric cpap', 'paediatric cpap',]
    for keyword in therapeutic:
        if keyword in desc:
            return 3
    
    # Diagnostic (2)
    diagnostic = [ # X-Ray
    'x ray', 'x-ray', 'xray', 'x ray machine', 'xray machine',
    'radiography', 'radiograph', 'radiography system',
    'digital radiography', 'dr system', 'digital xray',
    'portable xray', 'mobile xray', 'portable x ray',
    
    # CT Scan
    'ct', 'ct scan', 'ct scanner', 'cat scan',
    'computed tomography', 'computerized tomography',
    'multislice ct', 'multi slice ct', 'spiral ct',
    
    # MRI
    'mri', 'mri machine', 'mri scanner',
    'magnetic resonance imaging', 'magnetic resonance',
    'nmr', 'nuclear magnetic resonance',
    
    # Ultrasound
    'ultrasound', 'ultrasound machine', 'ultrasound scanner',
    'sonography', 'sonograph', 'ultrasonography',
    'doppler', 'doppler ultrasound', 'color doppler',
    'echo', 'echocardiography', 'cardiac ultrasound',
    
    # Echo Specific
    '2d echo', '2d echocardiography', 'two d echo',
    '3d echo', '3d echocardiography', 'three d echo',
    '4d echo', '4d echocardiography',
    'tee', 'transesophageal echo', 'transoesophageal echo',
    
    # Nuclear Medicine
    'pet', 'pet scan', 'pet scanner',
    'pet ct', 'pet ct scanner',
    'spect', 'spect scanner', 'spect ct',
    'gamma camera', 'nuclear medicine camera',
    
    # Mammography
    'mammography', 'mammograph', 'mammo',
    'digital mammography', 'breast imaging',
    
    # Fluoroscopy
    'c arm', 'c-arm', 'carm', 'fluoroscopy',
    'image intensifier', 'mobile c arm',
    'mini c arm', 'mini carm',
    
    # Dental Imaging
    'opg', 'opg machine', 'orthopantomogram',
    'dental xray', 'dental x ray', 'panoramic xray',
    'cbct', 'cone beam ct', 'dental ct',
    
    # Endoscopy (All Types)
    'endoscope', 'endoscopy', 'endoscopy system',
    'video endoscope', 'flexible endoscope',
    
    # GI Endoscopy
    'gastroscope', 'gastroscopy',
    'colonoscope', 'colonoscopy',
    'sigmoidoscope', 'sigmoidoscopy',
    'enteroscope', 'enteroscopy',
    'capsule endoscopy', 'pill camera',
    
    # Bronchoscopy
    'bronchoscope', 'bronchoscopy',
    'flexible bronchoscope', 'video bronchoscope',
    'pediatric bronchoscope', 'paediatric bronchoscope',
    'video bronchoscope intubation', 'intubation endoscope',
    
    # Gynecology
    'colposcope', 'colposcopy',
    'hysteroscope', 'hysteroscopy', 'hysteroscopy cart',
    
    # Urology
    'cystoscope', 'cystoscopy', 'ureteroscope',
    'nephroscope', 'percutaneous nephroscope',
    
    # ENT
    'rhinolaryngoscope', 'laryngoscope', 'nasopharyngoscope',
    'ent endoscope', 'sinus endoscope',
    
    # Laparoscopy
    'laparoscope', 'laparoscopy', 'laparoscopy system',
    'laparoscopy cart', 'laproscopy cart',  # common typo
    'laparoscopic tower', 'minimally invasive surgery',
    'insufflator', 'laparoscopy insufflator', 'insufflation',
    
    # Arthroscopy
    'arthroscope', 'arthroscopy', 'arthroscopy system',
    'joint scope',
    
    # ECG/EKG
    'ecg', 'ecg machine', 'electrocardiograph',
    'ekg', 'ekg machine', 'electrocardiogram machine',
    '12 lead ecg', '12 lead ekg', 'resting ecg',
    'holter monitor', 'ambulatory ecg',
    'stress test', 'treadmill ecg', 'exercise ecg',
    
    # Patient Monitoring (Diagnostic)
    'patient monitor', 'vital signs monitor', 'bedside monitor',
    'multi parameter monitor', 'multiparameter monitor',
    'physiological monitor', 'physiologic monitor',
    
    # Oximetry
    'pulse oximeter', 'pulse oxymeter',  # include typo
    'oximeter', 'spo2 monitor', 'oxygen saturation monitor',
    
    # Blood Pressure
    'blood pressure monitor', 'bp monitor', 'bp apparatus',
    'sphygmomanometer', 'nibp', 'noninvasive blood pressure',
    'ambulatory blood pressure', 'abpm',
    
    # Blood Gas
    'abg', 'abg machine', 'blood gas analyzer',
    'abl', 'arterial blood gas', 'blood gas system',
    
    # Microscopy
    'microscope', 'binocular microscope', 'compound microscope',
    'zeiss microscope', 'surgical microscope', 'operating microscope',
    'phase contrast microscope', 'fluorescence microscope',
    'inverted microscope', 'stereo microscope',
    
    # Lab Diagnostics
    'hemoglobinometer', 'haemoglobinometer', 'hb meter',
    'glucometer', 'glucose meter', 'blood glucose monitor',
    
    # Gel Documentation
    'gel documentation', 'gel doc', 'gel imaging system',
    'gel documentation system',
    
    # Thermometry
    'thermometer', 'digital thermometer', 'infrared thermometer',
    'tympanic thermometer', 'temporal thermometer',
    
    # Audiometry
    'audiometer', 'audiometry', 'hearing test',
    'tympanometer', 'impedance audiometer',
    
    # Vision Testing
    'autorefractor', 'auto refractor', 'refractometer',
    'keratometer', 'corneal topographer',
    'tonometer', 'applanation tonometer',
    'slit lamp', 'biomicroscope',
    
    # Pulmonary Function
    'spirometer', 'spirometry', 'lung function test',
    'peak flow meter', 'pulmonary function test',
    
    # Fetal Monitoring
    'fetal monitor', 'ctg', 'cardiotocography',
    'fetal doppler', 'baby doppler',]

    for keyword in diagnostic:
        if keyword in desc:
            return 2
    
    # Fuzzy matching per typo
    if FUZZY_AVAILABLE:
        all_keywords = {
            4: life_saving,
            3: therapeutic,
            2: diagnostic
        }
        
        best_score = 0
        best_category = 1
        
        for category, keywords in all_keywords.items():
            for kw in keywords:
                score = fuzz.ratio(desc, kw)
                if score > best_score and score >= 85:
                    best_score = score
                    best_category = category
        
        if best_score >= 85:
            return best_category
    
    # Default: Analytical/Support (1)
    return 1


def auto_create_scoring_parameters(device_id, description, installation_date):
    """
    Crea automaticamente scoring_parameters con regole basate su type_of_service dalla tabella breakdown
    """
    eq_function = classify_device_eq_function(description)
    age_years = calculate_age_years(installation_date) if installation_date else 0
    downtime = calculate_downtime_hours(device_id)
    
    # Recupera type_of_service dalla tabella breakdown (più recente)
    cur.execute("""
        SELECT type_of_service 
        FROM breakdown 
        WHERE device_id = %s 
        ORDER BY call_received_date DESC 
        LIMIT 1
    """, (device_id,))
    
    result = cur.fetchone()
    type_of_service = result[0] if result and result[0] else 'none'
    type_lower = str(type_of_service).lower().strip()
    
    # Regole spare_parts_availability
    if type_lower in ['warranty', 'w', 'camc', 'c','inhouse', 'in house','amc','a','cmc']:
        spare_parts_availability = 1
    else:  # amc, a, none
        spare_parts_availability = 0.1
    
    # Regole service_availability
    if type_lower in ['none', '']:
        service_availability = 0.1
    else:
        service_availability = 1
    
    assessment_date = dt.date.today()
    backup = 0
    vulnerability_score = 0
    miss_score = 0
    supp_score = 0
    criticity_score = 0
    
    cur.execute("""
        INSERT INTO scoring_parameters (
            device_id, assessment_date, age_years, downtime,
            service_availability, spare_parts_availability, backup, eq_function,
            vulnerability_score, miss_score, supp_score, criticity_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING parameter_id
    """, (
        device_id, assessment_date, age_years, downtime,
        service_availability, spare_parts_availability, backup, eq_function,
        vulnerability_score, miss_score, supp_score, criticity_score
    ))
    
    parameter_id = cur.fetchone()[0]
    conn.commit()
    
    return parameter_id

def auto_update_scoring_parameters(device_id, description, installation_date):
    """
    Aggiorna automaticamente scoring_parameters con regole basate su type_of_service dalla tabella breakdown
    """
    cur.execute("SELECT parameter_id FROM scoring_parameters WHERE device_id = %s", (device_id,))
    exists = cur.fetchone()
    
    if not exists:
        auto_create_scoring_parameters(device_id, description, installation_date)
        return True
    
    eq_function = classify_device_eq_function(description)
    age_years = calculate_age_years(installation_date) if installation_date else 0
    downtime = calculate_downtime_hours(device_id)
    
    # Recupera type_of_service dalla tabella breakdown (più recente)
    cur.execute("""
        SELECT type_of_service 
        FROM breakdown 
        WHERE device_id = %s 
        ORDER BY call_received_date DESC 
        LIMIT 1
    """, (device_id,))
    
    result = cur.fetchone()
    type_of_service = result[0] if result and result[0] else 'none'
    type_lower = str(type_of_service).lower().strip()
    
    # Regole spare_parts_availability
    if type_lower in ['warranty', 'w', 'camc', 'c','inhouse', 'in house','amc','a','cmc']:
        spare_parts_availability = 1
    else:  # amc, a, none
        spare_parts_availability = 0.1
    
    # Regole service_availability
    if type_lower in ['none', '']:
        service_availability = 0.1
    else:
        service_availability = 1
    
    cur.execute("""
        UPDATE scoring_parameters 
        SET 
            eq_function = %s,
            age_years = %s,
            downtime = %s,
            spare_parts_availability = %s,
            service_availability = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE device_id = %s
    """, (eq_function, age_years, downtime, spare_parts_availability, service_availability, device_id))
    
    conn.commit()
    return True



# =============================================================================
# MODIFICA LA FUNZIONE insert_medical_device ESISTENTE
# =============================================================================

def insert_medical_device(description, room_id, device_class, usage_type, cost_inr, 
                         brand, model, installation_date, serial_number, manufacturer_date, 
                         udi_number, mode_of_service=None):
    """
    Inserisce dispositivo E crea scoring_parameters con regole mode_of_service
    """
    cur.execute("""
        INSERT INTO Medical_Device (Room_ID, Description, Class, Usage_Type, 
                                  Cost_INR, Present, Brand, Model, Installation_Date, 
                                  serial_number, manufacturer_date, udi_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING Device_ID
    """, (room_id, description, device_class, usage_type, cost_inr, 
          True, brand, model, installation_date, serial_number, manufacturer_date, udi_number))
    
    device_id = cur.fetchone()[0]
    conn.commit()
    
    try:
        auto_create_scoring_parameters(device_id, description, installation_date, mode_of_service)
    except Exception as e:
        print(f"⚠ Warning: {e}")
    
    return device_id



# =============================================================================
# MODIFICA LA FUNZIONE update_device ESISTENTE
# =============================================================================

def update_device(Device_ID, Description, Class, Usage_Type, Cost_INR, Brand, Model, 
                 Installation_Date, serial_number, manufacturer_date, udi_number, present):
    """
    Aggiorna dispositivo E scoring_parameters automaticamente
    """
    cur.execute("""
        UPDATE medical_device 
        SET description=%s, class=%s, usage_type=%s, cost_inr=%s, Brand=%s, Model=%s, 
            installation_date=%s, serial_number=%s, manufacturer_date=%s, udi_number=%s, present=%s
        WHERE device_id=%s
    """, (Description, Class, Usage_Type, Cost_INR, Brand, Model, Installation_Date, 
          serial_number, manufacturer_date, udi_number, present, Device_ID))
    
    conn.commit()
    
    try:
        auto_update_scoring_parameters(Device_ID, Description, Installation_Date)
    except Exception as e:
        print(f"⚠ Warning: {e}")

def update_device_normal(Device_ID, Description, Class, Usage_Type, Cost_INR, Brand, Model, 
                 Installation_Date, serial_number, manufacturer_date, udi_number,gmdn, present):
    """
    Aggiorna dispositivo E scoring_parameters automaticamente
    """
    cur.execute("""
        UPDATE medical_device 
        SET description=%s, class=%s, usage_type=%s, cost_inr=%s, Brand=%s, Model=%s, 
            installation_date=%s, serial_number=%s, manufacturer_date=%s, udi_number=%s, present=%s, gmdn=%s
        WHERE device_id=%s
    """, (Description, Class, Usage_Type, Cost_INR, Brand, Model, Installation_Date, 
          serial_number, manufacturer_date, udi_number, present,gmdn, Device_ID))
    
    conn.commit()
    







# =============================================================================
# NUOVA FUNZIONE PER BOTTONE IN RISK ASSESSMENT
# =============================================================================

def update_scoring_manual(device_id, spare_parts_availability, service_availability, backup):
    """
    Aggiorna manualmente i parametri scoring da Risk Assessment
    
    Args:
        device_id: ID del dispositivo
        spare_parts_availability: int 0-2
        service_availability: int 0-100
        backup: int 0-2
        
    Returns:
        bool: True se successo
    """
    # Verifica se esiste
    cur.execute("SELECT parameter_id FROM scoring_parameters WHERE device_id = %s", (device_id,))
    exists = cur.fetchone()
    
    if not exists:
        # Se non esiste, recupera info dispositivo e crealo
        cur.execute("""
            SELECT description, installation_date 
            FROM medical_device 
            WHERE device_id = %s
        """, (device_id,))
        result = cur.fetchone()
        
        if result:
            description, installation_date = result
            auto_create_scoring_parameters(device_id, description, installation_date)
    
    # Aggiorna i parametri configurabili
    cur.execute("""
        UPDATE scoring_parameters 
        SET 
            spare_parts_availability = %s,
            service_availability = %s,
            backup = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE device_id = %s
    """, (spare_parts_availability, service_availability, backup, device_id))
    
    conn.commit()
    return cur.rowcount > 0


# def insert_scoring_parameters(device_id,assessment_date,spare_parts_available,age_years,backup_device_available,
#                           failure_rate,downtime_hours,cost_ratio,uptime_percentage,equipment_function_score,vulnerabilities_present,notes,end_of_life,end_of_support,mis_score,supp_score, criticity):
#     """Inserisce parametri obsolescenza """
#     cur.execute("""
#         INSERT INTO scoring_parameters (device_id,assessment_date,spare_parts_available,age_years,backup_device_available,failure_rate,downtime_hours,cost_ratio,uptime_percentage,equipment_function_score,vulnerabilities_present,notes,end_of_life,end_of_support ,mis_score,supp_score, criticity)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )
#         RETURNING parameter_id
#     """, (device_id,assessment_date,spare_parts_available,age_years,backup_device_available,
#           failure_rate,downtime_hours,cost_ratio,uptime_percentage,equipment_function_score,vulnerabilities_present,notes,end_of_life,end_of_support,mis_score,supp_score, criticity ))
#     parameter_id = cur.fetchone()[0]
#     conn.commit()
#     return parameter_id

# def delete_scoring_parameters(device_id):
#     cur.execute("""
#             DELETE FROM scoring_parameters 
#             WHERE device_id = %s
#             RETURNING device_id
#         """, (device_id,))
#     conn.commit()

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

@st.cache_data(ttl=60)
def get_all_devices():
    cur.execute("SELECT * FROM medical_device ORDER BY device_id")
    return cur.fetchall()
@st.cache_data(ttl=60)
def get_all_devices_with_scores_optimized():
    """
    Prende TUTTI i dispositivi con scores e ward in UNA SOLA QUERY
    Usa JOIN invece di query multiple - OTTIMIZZATO!
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        
        query = """
        SELECT 
            md.device_id,
            md.parent_id,
            md.room_id,
            md.description,
            md.class,
            md.usage_type,
            md.cost_inr,
            md.present,
            md.brand,
            md.model,
            md.installation_date,
            md.udi_number,
            md.serial_number,
            md.manufacturer_date,
            md.gmdn,
            r.room_name,
            w.ward_name,
            sp.criticity_score,
            sp.supp_score,
            sp.miss_score,
            sp.vulnerability_score,
            sp.eq_function,
            sp.age_years,
            sp.downtime,
            sp.assessment_date
        FROM medical_device md
        LEFT JOIN room r ON md.room_id = r.room_id
        LEFT JOIN ward w ON r.ward_id = w.ward_id
        LEFT JOIN LATERAL (
            SELECT *
            FROM scoring_parameters
            WHERE device_id = md.device_id
            ORDER BY assessment_date DESC
            LIMIT 1
        ) sp ON true
        ORDER BY md.device_id
        """
        
        cur.execute(query)
        results = cur.fetchall()
        
        return results
        
    finally:
        release_db_connection(conn)

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


def get_room_name_by_device(device_id):
    cur.execute("""
        SELECT r.room_name
        FROM medical_device d
        JOIN room r ON d.room_id = r.room_id
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



def get_device_by_id(dev_id):
    cur.execute("SELECT * FROM medical_device WHERE device_id=%s", (dev_id,))
    return cur.fetchone()

def get_scores_by_device_id(dev_id):
    cur.execute("SELECT * FROM scoring_parameters WHERE device_id=%s", (dev_id,))
    return cur.fetchone()

def delete_device(dev_id):
    cur.execute("DELETE FROM medical_device WHERE device_id = %s", (dev_id,))
    conn.commit()

# Aggiungi queste funzioni al file database.py esistente

# --- Funzione di compatibilità ---
def get_all_medical_devices():
    """Alias per get_all_devices() per compatibilità"""
    return get_all_devices()

# --- Funzioni per Manutenzione Preventiva ---

# ================== COMPANIES ==================

def get_all_companies():
    """Recupera tutte le aziende di manutenzione"""
    cur.execute("""
        SELECT company_id, company_name, contact_person, phone, email, 
               address, specializations, created_at, updated_at
        FROM companies
        ORDER BY company_name
    """)
    return cur.fetchall()


def get_company_by_id(company_id):
    """Recupera una singola azienda per ID"""
    cur.execute("""
        SELECT company_id, company_name, contact_person, phone, email,
               address, specializations, created_at, updated_at
        FROM companies
        WHERE company_id = %s
    """, (company_id,))
    return cur.fetchone()


# ================== PREVENTIVE MAINTENANCE (SEMPLIFICATO - SENZA COMPANIES) ==================

def insert_preventive_maintenance(device_id, maintenance_type, scheduled_date, due_date, 
                                 priority='Medium', technician_name=None, technician_email=None,
                                 description=None, cost_inr=None, duration_hours=None,
                                 next_maintenance_date=None, compliance_standard=None,
                                 created_by='system'):
    """Inserisce una nuova manutenzione preventiva/calibrazione"""
    cur.execute("""
        INSERT INTO preventive_maintenance 
        (device_id, maintenance_type, scheduled_date, due_date, priority, 
         technician_name, technician_email, description, cost_inr, duration_hours,
         next_maintenance_date, compliance_standard, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING maintenance_id
    """, (device_id, maintenance_type, scheduled_date, due_date, priority,
          technician_name, technician_email, description, cost_inr, duration_hours,
          next_maintenance_date, compliance_standard, created_by))
    maintenance_id = cur.fetchone()[0]
    conn.commit()
    return maintenance_id


def update_preventive_maintenance(maintenance_id, **kwargs):
    """Aggiorna una manutenzione preventiva esistente"""
    allowed_fields = [
        'maintenance_type', 'scheduled_date', 'completed_date', 'due_date',
        'status', 'priority', 'technician_name', 'technician_email',
        'description', 'procedures_followed', 'parts_used', 'cost_inr',
        'duration_hours', 'next_maintenance_date', 'compliance_standard',
        'calibration_certificate', 'notes', 'updated_by'
    ]
    
    update_fields = [f"{k} = %s" for k in kwargs.keys() if k in allowed_fields]
    if not update_fields:
        return False
    
    update_fields.append("updated_date = NOW()")
    values = [v for k, v in kwargs.items() if k in allowed_fields]
    values.append(maintenance_id)
    
    cur.execute(f"""
        UPDATE preventive_maintenance
        SET {', '.join(update_fields)}
        WHERE maintenance_id = %s
    """, values)
    conn.commit()
    return cur.rowcount > 0


def delete_preventive_maintenance(maintenance_id):
    """Elimina una manutenzione preventiva"""
    cur.execute("""
        DELETE FROM preventive_maintenance
        WHERE maintenance_id = %s
    """, (maintenance_id,))
    conn.commit()
    return cur.rowcount > 0


def get_all_preventive_maintenance():
    """Recupera tutte le manutenzioni preventive con info device"""
    cur.execute("""
        SELECT 
            pm.maintenance_id, pm.device_id, d.description, d.brand, d.model,
            pm.maintenance_type, pm.scheduled_date, pm.completed_date, pm.due_date,
            pm.status, pm.priority, pm.technician_name, pm.technician_email,
            pm.description, pm.procedures_followed, pm.parts_used, pm.cost_inr,
            pm.duration_hours, pm.next_maintenance_date, pm.compliance_standard,
            pm.calibration_certificate, pm.notes, pm.created_by, pm.created_date
        FROM preventive_maintenance pm
        JOIN medical_device d ON pm.device_id = d.device_id
        ORDER BY pm.scheduled_date DESC
    """)
    return cur.fetchall()


def get_preventive_maintenance_by_id(maintenance_id):
    """Recupera una singola manutenzione per ID"""
    cur.execute("""
        SELECT 
            pm.maintenance_id, pm.device_id, d.description, d.brand, d.model,
            pm.maintenance_type, pm.scheduled_date, pm.completed_date, pm.due_date,
            pm.status, pm.priority, pm.technician_name, pm.technician_email,
            pm.description, pm.procedures_followed, pm.parts_used, pm.cost_inr,
            pm.duration_hours, pm.next_maintenance_date, pm.compliance_standard,
            pm.calibration_certificate, pm.notes, pm.created_by, pm.created_date
        FROM preventive_maintenance pm
        JOIN medical_device d ON pm.device_id = d.device_id
        WHERE pm.maintenance_id = %s
    """, (maintenance_id,))
    return cur.fetchone()


def get_preventive_maintenance_by_device(device_id):
    """Recupera tutte le manutenzioni di un dispositivo specifico"""
    cur.execute("""
        SELECT 
            pm.maintenance_id, pm.device_id, d.description, d.brand, d.model,
            pm.maintenance_type, pm.scheduled_date, pm.completed_date, pm.due_date,
            pm.status, pm.priority, pm.technician_name, pm.technician_email,
            pm.description
        FROM preventive_maintenance pm
        JOIN medical_device d ON pm.device_id = d.device_id
        WHERE pm.device_id = %s
        ORDER BY pm.scheduled_date DESC
    """, (device_id,))
    return cur.fetchall()


def get_overdue_maintenance():
    """Recupera manutenzioni scadute"""
    cur.execute("""
        SELECT 
            pm.maintenance_id, pm.device_id, d.description, d.brand, d.model,
            pm.maintenance_type, pm.scheduled_date, pm.priority, pm.technician_name,
            pm.status
        FROM preventive_maintenance pm
        JOIN medical_device d ON pm.device_id = d.device_id
        WHERE pm.status = 'Scheduled' AND pm.scheduled_date < CURRENT_DATE
        ORDER BY pm.scheduled_date ASC
    """)
    return cur.fetchall()


def get_upcoming_maintenance(days=30):
    """Recupera manutenzioni programmate nei prossimi X giorni"""
    cur.execute("""
        SELECT 
            pm.maintenance_id, pm.device_id, d.description, d.brand, d.model,
            pm.maintenance_type, pm.scheduled_date, pm.due_date, pm.priority,
            pm.technician_name, pm.status
        FROM preventive_maintenance pm
        JOIN medical_device d ON pm.device_id = d.device_id
        WHERE pm.status = 'Scheduled'
          AND pm.scheduled_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
        ORDER BY pm.scheduled_date ASC
    """, (days,))
    return cur.fetchall()

def insert_breakdown(device_id, nature_of_complaint, called_by, call_received_date, 
                     call_received_time, attended_by, attended_date, time_of_attendance,
                     action_taken, rectified_date, rectified_time, call_priority, 
                     remark, type_of_service):
    """Inserisce un nuovo breakdown/incident"""
    cur.execute("""
        INSERT INTO breakdown (
            device_id, nature_of_complaint, called_by, call_received_date,
            call_received_time, attended_by, attended_date, time_of_attendance,
            action_taken, rectified_date, rectified_time, call_priority,
            remark, type_of_service
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING breakdown_id
    """, (device_id, nature_of_complaint, called_by, call_received_date,
          call_received_time, attended_by, attended_date, time_of_attendance,
          action_taken, rectified_date, rectified_time, call_priority,
          remark, type_of_service))
    breakdown_id = cur.fetchone()[0]
    conn.commit()
    return breakdown_id


def get_all_breakdowns():
    """Recupera tutti i breakdown con informazioni dispositivo"""
    cur.execute("""
        SELECT 
            b.breakdown_id,
            b.device_id,
            md.description,
            md.brand,
            md.model,
            b.nature_of_complaint,
            b.called_by,
            b.call_received_date,
            b.call_received_time,
            b.attended_by,
            b.attended_date,
            b.time_of_attendance,
            b.action_taken,
            b.rectified_date,
            b.rectified_time,
            b.call_priority,
            b.remark,
            b.type_of_service
        FROM breakdown b
        JOIN medical_device md ON b.device_id = md.device_id
        ORDER BY b.call_received_date DESC, b.call_received_time DESC
    """)
    return cur.fetchall()


def get_breakdown_by_id(breakdown_id):
    """Recupera un breakdown specifico per ID"""
    cur.execute("""
        SELECT 
            b.breakdown_id,
            b.device_id,
            md.description,
            md.brand,
            md.model,
            b.nature_of_complaint,
            b.called_by,
            b.call_received_date,
            b.call_received_time,
            b.attended_by,
            b.attended_date,
            b.time_of_attendance,
            b.action_taken,
            b.rectified_date,
            b.rectified_time,
            b.call_priority,
            b.remark,
            b.type_of_service
        FROM breakdown b
        JOIN medical_device md ON b.device_id = md.device_id
        WHERE b.breakdown_id = %s
    """, (breakdown_id,))
    return cur.fetchone()


def get_breakdowns_by_device(device_id):
    """Recupera tutti i breakdown per un dispositivo specifico"""
    cur.execute("""
        SELECT 
            b.breakdown_id,
            b.device_id,
            md.description,
            md.brand,
            md.model,
            b.nature_of_complaint,
            b.called_by,
            b.call_received_date,
            b.call_received_time,
            b.attended_by,
            b.attended_date,
            b.time_of_attendance,
            b.action_taken,
            b.rectified_date,
            b.rectified_time,
            b.call_priority,
            b.remark,
            b.type_of_service
        FROM breakdown b
        JOIN medical_device md ON b.device_id = md.device_id
        WHERE b.device_id = %s
        ORDER BY b.call_received_date DESC, b.call_received_time DESC
    """, (device_id,))
    return cur.fetchall()

def get_breakdown_by_id_last(device_id):
    cur.execute("""
        SELECT * FROM breakdown 
        WHERE device_id = %s 
        ORDER BY call_received_date DESC 
        LIMIT 1
    """, (device_id,))
    return cur.fetchone()
    
def get_open_breakdowns():
    """Recupera tutti i breakdown non ancora risolti (senza rectified_date)"""
    cur.execute("""
        SELECT 
            b.breakdown_id,
            b.device_id,
            md.description,
            md.brand,
            md.model,
            b.nature_of_complaint,
            b.called_by,
            b.call_received_date,
            b.call_received_time,
            b.attended_by,
            b.attended_date,
            b.time_of_attendance,
            b.action_taken,
            b.rectified_date,
            b.rectified_time,
            b.call_priority,
            b.remark,
            b.type_of_service
        FROM breakdown b
        JOIN medical_device md ON b.device_id = md.device_id
        WHERE b.rectified_date IS NULL
        ORDER BY b.call_priority DESC, b.call_received_date ASC
    """)
    return cur.fetchall()


def get_critical_breakdowns():
    """Recupera tutti i breakdown con priorità critica e non risolti"""
    cur.execute("""
        SELECT 
            b.breakdown_id,
            b.device_id,
            md.description,
            md.brand,
            md.model,
            b.nature_of_complaint,
            b.called_by,
            b.call_received_date,
            b.call_received_time,
            b.attended_by,
            b.attended_date,
            b.time_of_attendance,
            b.action_taken,
            b.rectified_date,
            b.rectified_time,
            b.call_priority,
            b.remark,
            b.type_of_service
        FROM breakdown b
        JOIN medical_device md ON b.device_id = md.device_id
        WHERE b.call_priority = 'Critical' AND b.rectified_date IS NULL
        ORDER BY b.call_received_date ASC
    """)
    return cur.fetchall()


def update_breakdown(breakdown_id, device_id, nature_of_complaint, called_by, 
                     call_received_date, call_received_time, attended_by, 
                     attended_date, time_of_attendance, action_taken, 
                     rectified_date, rectified_time, call_priority, 
                     remark, type_of_service):
    """Aggiorna un breakdown esistente"""
    cur.execute("""
        UPDATE breakdown SET
            device_id = %s,
            nature_of_complaint = %s,
            called_by = %s,
            call_received_date = %s,
            call_received_time = %s,
            attended_by = %s,
            attended_date = %s,
            time_of_attendance = %s,
            action_taken = %s,
            rectified_date = %s,
            rectified_time = %s,
            call_priority = %s,
            remark = %s,
            type_of_service = %s
        WHERE breakdown_id = %s
    """, (device_id, nature_of_complaint, called_by, call_received_date,
          call_received_time, attended_by, attended_date, time_of_attendance,
          action_taken, rectified_date, rectified_time, call_priority,
          remark, type_of_service, breakdown_id))
    conn.commit()


def delete_breakdown(breakdown_id):
    """Elimina un breakdown"""
    cur.execute("DELETE FROM breakdown WHERE breakdown_id = %s", (breakdown_id,))
    conn.commit()


def get_breakdown_statistics():
    """Recupera statistiche sui breakdown"""
    cur.execute("""
        SELECT 
            COUNT(*) as total_breakdowns,
            COUNT(CASE WHEN rectified_date IS NULL THEN 1 END) as open_breakdowns,
            COUNT(CASE WHEN rectified_date IS NOT NULL THEN 1 END) as closed_breakdowns,
            COUNT(CASE WHEN call_priority = 'Critical' AND rectified_date IS NULL THEN 1 END) as critical_open
        FROM breakdown
    """)
    return cur.fetchone()


def get_breakdown_by_priority(priority):
    """Recupera tutti i breakdown con una specifica priorità"""
    cur.execute("""
        SELECT 
            b.breakdown_id,
            b.device_id,
            md.description,
            md.brand,
            md.model,
            b.nature_of_complaint,
            b.called_by,
            b.call_received_date,
            b.call_received_time,
            b.attended_by,
            b.attended_date,
            b.time_of_attendance,
            b.action_taken,
            b.rectified_date,
            b.rectified_time,
            b.call_priority,
            b.remark,
            b.type_of_service
        FROM breakdown b
        JOIN medical_device md ON b.device_id = md.device_id
        WHERE b.call_priority = %s
        ORDER BY b.call_received_date DESC
    """, (priority,))
    return cur.fetchall()


def get_breakdown_by_date_range(start_date, end_date):
    """Recupera breakdown in un intervallo di date"""
    cur.execute("""
        SELECT 
            b.breakdown_id,
            b.device_id,
            md.description,
            md.brand,
            md.model,
            b.nature_of_complaint,
            b.called_by,
            b.call_received_date,
            b.call_received_time,
            b.attended_by,
            b.attended_date,
            b.time_of_attendance,
            b.action_taken,
            b.rectified_date,
            b.rectified_time,
            b.call_priority,
            b.remark,
            b.type_of_service
        FROM breakdown b
        JOIN medical_device md ON b.device_id = md.device_id
        WHERE b.call_received_date BETWEEN %s AND %s
        ORDER BY b.call_received_date DESC
    """, (start_date, end_date))
    return cur.fetchall()


def get_average_resolution_time():
    """Calcola il tempo medio di risoluzione dei breakdown"""
    cur.execute("""
        SELECT 
            AVG(EXTRACT(EPOCH FROM (rectified_date + rectified_time - call_received_date - call_received_time))/3600) as avg_hours
        FROM breakdown
        WHERE rectified_date IS NOT NULL AND rectified_time IS NOT NULL
    """)
    result = cur.fetchone()
    return result[0] if result and result[0] else 0

# --- Funzioni per Allegati ---

def insert_attachment(record_id, record_type, file_name, file_path, 
                     file_type=None, file_size=None, description=None, uploaded_by='system'):
    """Inserisce un allegato"""
    cur.execute("""
        INSERT INTO maintenance_attachments
        (record_id, record_type, file_name, file_path, file_type, 
         file_size, description, uploaded_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING attachment_id
    """, (record_id, record_type, file_name, file_path, file_type,
          file_size, description, uploaded_by))
    attachment_id = cur.fetchone()[0]
    conn.commit()
    return attachment_id

def get_attachments_by_record(record_id, record_type):
    """Recupera allegati per un record specifico"""
    cur.execute("""
        SELECT * FROM maintenance_attachments 
        WHERE record_id = %s AND record_type = %s
        ORDER BY upload_date DESC
    """, (record_id, record_type))
    return cur.fetchall()

# --- Funzioni per Dashboard/Report ---

def get_maintenance_overview():
    """Recupera overview maintenance per dashboard"""
    cur.execute("SELECT * FROM maintenance_overview ORDER BY device_description")
    return cur.fetchall()

def get_maintenance_statistics():
    """Recupera statistiche per dashboard"""
    stats = {}
    
    # Manutenzioni preventive
    cur.execute("SELECT COUNT(*) FROM preventive_maintenance WHERE status = 'Scheduled'")
    stats['scheduled_maintenance'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM preventive_maintenance WHERE due_date < CURRENT_DATE AND status IN ('Scheduled', 'Overdue')")
    stats['overdue_maintenance'] = cur.fetchone()[0]
    
    # Incidenti
    cur.execute("SELECT COUNT(*) FROM incidents_corrective_maintenance WHERE status IN ('Open', 'In Progress')")
    stats['open_incidents'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM incidents_corrective_maintenance WHERE severity = 'Critical' AND status IN ('Open', 'In Progress')")
    stats['critical_incidents'] = cur.fetchone()[0]
    
    # Costi ultimo anno
    cur.execute("""
        SELECT COALESCE(SUM(cost_inr), 0) FROM preventive_maintenance 
        WHERE completed_date >= CURRENT_DATE - INTERVAL '1 year'
    """)
    stats['preventive_costs_year'] = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COALESCE(SUM(repair_cost_inr + COALESCE(parts_cost_inr, 0) + COALESCE(labor_cost_inr, 0)), 0)
        FROM incidents_corrective_maintenance 
        WHERE incident_date >= CURRENT_DATE - INTERVAL '1 year'
    """)
    stats['corrective_costs_year'] = cur.fetchone()[0]
    
    return stats

def get_device_maintenance_history(device_id):
    """Recupera storico completo manutenzioni per un dispositivo"""
    # Manutenzioni preventive
    cur.execute("""
        SELECT 'Preventive' as type, maintenance_type as subtype, scheduled_date as date,
               status, cost_inr, technician_name, description
        FROM preventive_maintenance 
        WHERE device_id = %s
        UNION ALL
        SELECT 'Incident' as type, incident_type as subtype, incident_date as date,
               status, repair_cost_inr as cost_inr, technician_name, description
        FROM incidents_corrective_maintenance
        WHERE device_id = %s
        ORDER BY date DESC
    """, (device_id, device_id))
    return cur.fetchall()


# --- Funzioni per versioni_software ---

def insert_software(device_id, vendor, product, version, model, ip):
    """Inserisce una nuova versione software"""
    cur.execute("""
        INSERT INTO versioni_software (device_id, vendor, product, version, model, ip)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING software_id
    """, (device_id, vendor, product, version, model, ip))
    software_id = cur.fetchone()[0]
    conn.commit()
    return software_id

def get_all_software():
    """Recupera tutti i software"""
    cur.execute("SELECT * FROM versioni_software ORDER BY software_id")
    return cur.fetchall()

def get_software_by_device(device_id):
    """Recupera tutti i software per un dispositivo"""
    cur.execute("""
        SELECT * FROM versioni_software 
        WHERE device_id = %s 
        ORDER BY software_id
    """, (device_id,))
    return cur.fetchall()

def get_software_by_id(software_id):
    """Recupera un software specifico"""
    cur.execute("SELECT * FROM versioni_software WHERE software_id = %s", (software_id,))
    return cur.fetchone()

def update_software(software_id, device_id=None, vendor=None, product=None, version=None, model=None, ip=None):
    """Aggiorna un software"""
    fields = []
    values = []
    
    if device_id is not None:
        fields.append("device_id = %s")
        values.append(device_id)
    if vendor is not None:
        fields.append("vendor = %s")
        values.append(vendor)
    if product is not None:
        fields.append("product = %s")
        values.append(product)
    if version is not None:
        fields.append("version = %s")
        values.append(version)
    if model is not None:
        fields.append("model = %s")
        values.append(model)
    if ip is not None:
        fields.append("ip = %s")
        values.append(ip)
    
    if not fields:
        return False
    
    values.append(software_id)
    query = f"UPDATE versioni_software SET {', '.join(fields)} WHERE software_id = %s"
    cur.execute(query, values)
    conn.commit()
    return True

def delete_software(software_id):
    """Elimina un software (elimina anche i CVE associati)"""
    try:
        # Prima elimina i CVE associati
        cur.execute("DELETE FROM cve WHERE software_id = %s", (software_id,))
        
        # Poi elimina il software
        cur.execute("DELETE FROM versioni_software WHERE software_id = %s", (software_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()  # ✅ Importante in caso di errore
        raise Exception(f"Error deleting software: {str(e)}")

# --- Funzioni per CVE ---

def insert_cve(software_id, cve, cvss, description):
    """Inserisce un nuovo CVE"""
    cur.execute("""
        INSERT INTO cve (software_id, cve, cvss, description)
        VALUES (%s, %s, %s, %s)
        RETURNING cve_id
    """, (software_id, cve, cvss, description))
    cve_id = cur.fetchone()[0]
    conn.commit()
    return cve_id

def get_all_cves():
    """Recupera tutti i CVE"""
    cur.execute("SELECT * FROM cve ORDER BY cvss DESC NULLS LAST")
    return cur.fetchall()

def get_cves_by_software(software_id):
    """Recupera tutti i CVE per un software"""
    try:
        cur.execute("""
            SELECT * FROM cve 
            WHERE software_id = %s 
            ORDER BY cvss DESC NULLS LAST
        """, (software_id,))
        return cur.fetchall()
    except Exception as e:
        st.error(f"Error fetching CVEs: {str(e)}")
        return []  # ✅ Ritorna lista vuota se errore

def get_cve_by_id(cve_id):
    """Recupera un CVE specifico"""
    cur.execute("SELECT * FROM cve WHERE cve_id = %s", (cve_id,))
    return cur.fetchone()

def update_cve(cve_id, software_id=None, cve=None, cvss=None):
    """Aggiorna un CVE"""
    fields = []
    values = []
    
    if software_id is not None:
        fields.append("software_id = %s")
        values.append(software_id)
    if cve is not None:
        fields.append("cve = %s")
        values.append(cve)
    if cvss is not None:
        fields.append("cvss = %s")
        values.append(cvss)
    
    if not fields:
        return False
    
    values.append(cve_id)
    query = f"UPDATE cve SET {', '.join(fields)} WHERE cve_id = %s"
    cur.execute(query, values)
    conn.commit()
    return True

def delete_cve(cve_id):
    """Elimina un CVE"""
    cur.execute("DELETE FROM cve WHERE cve_id = %s", (cve_id,))
    conn.commit()

def delete_all_cves_for_software(software_id):
    """Elimina tutti i CVE di un software"""
    cur.execute("DELETE FROM cve WHERE software_id = %s", (software_id,))
    conn.commit()

# --- Funzioni aggregate ---

def get_device_vulnerability_summary():
    """Recupera il riepilogo vulnerabilità per dispositivo"""
    cur.execute("""
        SELECT 
            md.device_id,
            md.description as device_name,
            md.brand,
            md.model as device_model,
            vs.software_id,
            vs.vendor,
            vs.product,
            vs.version,
            vs.model as software_model,
            vs.ip,
            COUNT(c.cve_id) as total_cve,
            MAX(c.cvss) as max_cvss,
            AVG(c.cvss) as avg_cvss,
            SUM(CASE WHEN c.cvss >= 9.0 THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN c.cvss >= 7.0 AND c.cvss < 9.0 THEN 1 ELSE 0 END) as high_count,
            SUM(CASE WHEN c.cvss >= 4.0 AND c.cvss < 7.0 THEN 1 ELSE 0 END) as medium_count,
            SUM(CASE WHEN c.cvss < 4.0 THEN 1 ELSE 0 END) as low_count
        FROM medical_device md
        LEFT JOIN versioni_software vs ON md.device_id = vs.device_id
        LEFT JOIN cve c ON vs.software_id = c.software_id
        GROUP BY md.device_id, md.description, md.brand, md.model, 
                 vs.software_id, vs.vendor, vs.product, vs.version, vs.model, vs.ip
        ORDER BY max_cvss DESC NULLS LAST, total_cve DESC
    """)
    return cur.fetchall()

def get_software_with_cve_count():
    """Recupera tutti i software con conteggio CVE"""
    cur.execute("""
        SELECT 
            vs.*,
            COUNT(c.cve_id) as cve_count,
            MAX(c.cvss) as max_cvss,
            AVG(c.cvss) as avg_cvss
        FROM versioni_software vs
        LEFT JOIN cve c ON vs.software_id = c.software_id
        GROUP BY vs.software_id
        ORDER BY max_cvss DESC NULLS LAST, cve_count DESC
    """)
    return cur.fetchall()# ==============================================================================
# NUOVE FUNZIONI PER scoring_parameters - DA SOSTITUIRE IN database.py
# ==============================================================================


# ------------------- FUNZIONI HELPER -------------------

def calculate_age_years(installation_date):
    """
    Calcola l'etร  in anni del dispositivo dalla data di installazione
    
    Args:
        installation_date: datetime.date object
        
    Returns:
        float: Etร  in anni (con decimali)
    """
    if not installation_date:
        return None

    
    today = datetime.date.today() 
    age_days = (today - installation_date).days
    age_years = round(age_days / 365.25, 2)  # 365.25 per considerare anni bisestili


    
    return age_years


def calculate_downtime_hours(device_id):
    """
    Calcola il downtime totale in ore per un dispositivo dagli incidents
    
    Args:
        device_id: ID del dispositivo
        
    Returns:
        float: Ore totali di downtime
    """
    cur.execute("""
        SELECT 
            (CURRENT_DATE - call_received_date) AS downtime_days
        FROM breakdown
        WHERE device_id = %s
        AND rectified_date IS NULL
        AND call_received_date IS NOT NULL
        ORDER BY call_received_date DESC
        LIMIT 1;
    """, (device_id,))

    
    result = cur.fetchone()
    downtime = result[0] if result and result[0] else 0.0
    
    return round(downtime)


# ------------------- FUNZIONI CRUD -------------------

def insert_scoring_parameters(
    device_id,
    assessment_date,
    service_availability,
    spare_parts_availability,
    backup,
    eq_function,
    vulnerability_score,
    miss_score,
    supp_score,
    criticity_score
):
    """
    Inserisce nuovi parametri di scoring per un dispositivo.
    age_years e downtime vengono calcolati automaticamente.
    
    Args:
        device_id: ID del dispositivo
        assessment_date: Data valutazione
        service_availability: Disponibilitร  servizio (0-100)
        spare_parts_availability: 'Available', 'Limited', 'Unavailable'
        backup: 'Yes', 'No', 'Partial'
        eq_function: Punteggio funzione (0-100)
        vulnerability_score: Punteggio vulnerabilitร 
        miss_score: Punteggio missione critica
        supp_score: Punteggio supporto
        criticity_score: Punteggio criticitร  finale
        
    Returns:
        int: parameter_id del record inserito
    """
    # Recupera installation_date del dispositivo
    cur.execute("SELECT installation_date FROM medical_device WHERE device_id = %s", (device_id,))
    result = cur.fetchone()
    installation_date = result[0] if result else None
    
    # Calcola age_years e downtime
    age_years = calculate_age_years(installation_date)
    downtime = calculate_downtime_hours(device_id)
    
    # Inserimento
    cur.execute("""
        INSERT INTO scoring_parameters (
            device_id, assessment_date, age_years, downtime,
            service_availability, spare_parts_availability, backup, eq_function,
            vulnerability_score, miss_score, supp_score, criticity_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING parameter_id
    """, (
        device_id, assessment_date, age_years, downtime,
        service_availability, spare_parts_availability, backup, eq_function,
        vulnerability_score, miss_score, supp_score, criticity_score
    ))
    
    parameter_id = cur.fetchone()[0]
    conn.commit()
    
    return parameter_id


def update_scoring_parameters(
    device_id,
    assessment_date,
    service_availability,
    spare_parts_availability,
    backup,
    eq_function,
    vulnerability_score,
    miss_score,
    supp_score,
    criticity_score
):
    """
    Aggiorna i parametri di scoring per un dispositivo.
    age_years e downtime vengono ricalcolati automaticamente.
    
    Args:
        Stessi argomenti di insert_scoring_parameters
        
    Returns:
        bool: True se aggiornamento riuscito
    """
    # Recupera installation_date
    cur.execute("SELECT installation_date FROM medical_device WHERE device_id = %s", (device_id,))
    result = cur.fetchone()
    installation_date = result[0] if result else None
    
    # Ricalcola age_years e downtime
    age_years = calculate_age_years(installation_date)
    downtime = calculate_downtime_hours(device_id)
    
    # Update
    cur.execute("""
        UPDATE scoring_parameters 
        SET 
            age_years = %s,
            downtime = %s,
            service_availability = %s,
            spare_parts_availability = %s,
            backup = %s,
            eq_function = %s,
            vulnerability_score = %s,
            miss_score = %s,
            supp_score = %s,
            criticity_score = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE device_id = %s AND assessment_date = %s
    """, (
        age_years, downtime,
        service_availability, spare_parts_availability, backup, eq_function,
        vulnerability_score, miss_score, supp_score, criticity_score,
        device_id, assessment_date
    ))
    
    conn.commit()
    return cur.rowcount > 0


def get_scores_by_device_id(device_id):
    """
    Recupera i parametri di scoring piรน recenti per un dispositivo
    
    Args:
        device_id: ID del dispositivo
        
    Returns:
        tuple: Record scoring_parameters o None
    """
    cur.execute("""
        SELECT * FROM scoring_parameters 
        WHERE device_id = %s 
        ORDER BY assessment_date DESC 
        LIMIT 1
    """, (device_id,))
    
    return cur.fetchone()


def get_all_scores():
    """Recupera tutti i parametri di scoring"""
    cur.execute("SELECT * FROM scoring_parameters ORDER BY assessment_date DESC")
    return cur.fetchall()


def delete_scoring_parameters(device_id):
    """
    Elimina tutti i parametri di scoring per un dispositivo
    
    Args:
        device_id: ID del dispositivo
        
    Returns:
        bool: True se eliminazione riuscita
    """
    cur.execute("""
        DELETE FROM scoring_parameters 
        WHERE device_id = %s
        RETURNING device_id
    """, (device_id,))
    
    deleted = cur.fetchone()
    conn.commit()
    
    return deleted is not None


def get_scoring_history(device_id):

    """
    Recupera lo storico delle valutazioni per un dispositivo
    
    Args:
        device_id: ID del dispositivo
        
    Returns:
        list: Lista di tuple con tutti i record di scoring per il device
    """
    cur.execute("""
        SELECT * FROM scoring_parameters 
        WHERE device_id = %s 
        ORDER BY assessment_date DESC
    """, (device_id,))
    
    return cur.fetchall()
# ============================================================
# FUNZIONI PER FUZZY CONFIGURATION
# Aggiungi queste funzioni al tuo database.py
# ============================================================

def get_active_fuzzy_config():
    """
    Recupera la configurazione fuzzy attiva
    
    Returns:
        dict: Dizionario con tutti i parametri fuzzy o None se non trovata
    """
    cur.execute("""
        SELECT * FROM fuzzy_config 
        WHERE is_active = TRUE 
        LIMIT 1
    """)
    
    row = cur.fetchone()
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
        },
        'created_at': row[27],
        'updated_at': row[28]
    }


def get_fuzzy_config_by_name(config_name):
    """
    Recupera una configurazione fuzzy per nome
    
    Args:
        config_name: Nome della configurazione (es. 'default', 'custom')
        
    Returns:
        dict: Dizionario con tutti i parametri o None
    """
    cur.execute("""
        SELECT * FROM fuzzy_config 
        WHERE config_name = %s
    """, (config_name,))
    
    row = cur.fetchone()
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
        },
        'created_at': row[27],
        'updated_at': row[28]
    }


def get_all_fuzzy_configs():
    """
    Recupera tutte le configurazioni fuzzy
    
    Returns:
        list: Lista di dizionari con le configurazioni
    """
    cur.execute("""
        SELECT config_name, is_active, updated_at 
        FROM fuzzy_config 
        ORDER BY is_active DESC, config_name
    """)
    
    rows = cur.fetchall()
    return [{'config_name': r[0], 'is_active': r[1], 'updated_at': r[2]} for r in rows]


def insert_fuzzy_config(config_name, age_params, downtime_params):
    """
    Inserisce una nuova configurazione fuzzy
    
    Args:
        config_name: Nome della configurazione (deve essere unico)
        age_params: Dict con 'new', 'middle', 'old' (ciascuno lista di 4 float)
        downtime_params: Dict con 'low', 'middle', 'high' (ciascuno lista di 4 float)
        
    Returns:
        int: config_id del record inserito o None se errore
    """
    try:
        cur.execute("""
            INSERT INTO fuzzy_config (
                config_name, is_active,
                age_new_a, age_new_b, age_new_c, age_new_d,
                age_middle_a, age_middle_b, age_middle_c, age_middle_d,
                age_old_a, age_old_b, age_old_c, age_old_d,
                downtime_low_a, downtime_low_b, downtime_low_c, downtime_low_d,
                downtime_middle_a, downtime_middle_b, downtime_middle_c, downtime_middle_d,
                downtime_high_a, downtime_high_b, downtime_high_c, downtime_high_d
            ) VALUES (
                %s, FALSE,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING config_id
        """, (
            config_name,
            *age_params['new'], *age_params['middle'], *age_params['old'],
            *downtime_params['low'], *downtime_params['middle'], *downtime_params['high']
        ))
        
        config_id = cur.fetchone()[0]
        conn.commit()
        return config_id
        
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None


def update_fuzzy_config(config_name, age_params, downtime_params):
    """
    Aggiorna una configurazione fuzzy esistente
    
    Args:
        config_name: Nome della configurazione da aggiornare
        age_params: Dict con 'new', 'middle', 'old'
        downtime_params: Dict con 'low', 'middle', 'high'
        
    Returns:
        bool: True se aggiornamento riuscito
    """
    cur.execute("""
        UPDATE fuzzy_config
        SET
            age_new_a = %s, age_new_b = %s, age_new_c = %s, age_new_d = %s,
            age_middle_a = %s, age_middle_b = %s, age_middle_c = %s, age_middle_d = %s,
            age_old_a = %s, age_old_b = %s, age_old_c = %s, age_old_d = %s,
            downtime_low_a = %s, downtime_low_b = %s, downtime_low_c = %s, downtime_low_d = %s,
            downtime_middle_a = %s, downtime_middle_b = %s, downtime_middle_c = %s, downtime_middle_d = %s,
            downtime_high_a = %s, downtime_high_b = %s, downtime_high_c = %s, downtime_high_d = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE config_name = %s
    """, (
        *age_params['new'], *age_params['middle'], *age_params['old'],
        *downtime_params['low'], *downtime_params['middle'], *downtime_params['high'],
        config_name
    ))
    
    conn.commit()
    return cur.rowcount > 0


def set_active_fuzzy_config(config_name):
    """
    Imposta una configurazione come attiva (disattiva tutte le altre)
    
    Args:
        config_name: Nome della configurazione da attivare
        
    Returns:
        bool: True se operazione riuscita
    """
    # Disattiva tutte
    cur.execute("UPDATE fuzzy_config SET is_active = FALSE")
    
    # Attiva quella richiesta
    cur.execute("""
        UPDATE fuzzy_config 
        SET is_active = TRUE 
        WHERE config_name = %s
    """, (config_name,))
    
    conn.commit()
    return cur.rowcount > 0


def reset_to_default_fuzzy_config():
    """
    Ripristina la configurazione di default come attiva
    
    Returns:
        bool: True se operazione riuscita
    """
    return set_active_fuzzy_config('default')


def delete_fuzzy_config(config_name):
    """
    Elimina una configurazione fuzzy (solo se non è 'default' e non è attiva)
    
    Args:
        config_name: Nome della configurazione da eliminare
        
    Returns:
        bool: True se eliminazione riuscita, False altrimenti
    """
    if config_name == 'default':
        return False
    
    # Verifica che non sia attiva
    cur.execute("""
        SELECT is_active FROM fuzzy_config 
        WHERE config_name = %s
    """, (config_name,))
    
    result = cur.fetchone()
    if result and result[0]:  # Se è attiva
        return False
    
    cur.execute("""
        DELETE FROM fuzzy_config 
        WHERE config_name = %s AND config_name != 'default'
    """, (config_name,))
    
    conn.commit()
    return cur.rowcount > 0


# ============================================================
# ESEMPIO DI UTILIZZO:
# ============================================================
"""
# Recupera configurazione attiva
config = get_active_fuzzy_config()
print(config['age']['new'])  # [0.0, 0.0, 3.0, 5.0]

# Crea nuova configurazione custom
age_params = {
    'new': [0.0, 0.0, 2.0, 4.0],
    'middle': [3.0, 4.0, 8.0, 10.0],
    'old': [9.0, 11.0, 20.0, 20.0]
}
downtime_params = {
    'low': [0.0, 0.0, 0.5, 1.5],
    'middle': [0.5, 1.0, 3.0, 4.0],
    'high': [3.0, 5.0, 365.0, 365.0]
}
insert_fuzzy_config('small_hospital', age_params, downtime_params)

# Attiva la nuova configurazione
set_active_fuzzy_config('small_hospital')

# Reset a default
reset_to_default_fuzzy_config()
"""


