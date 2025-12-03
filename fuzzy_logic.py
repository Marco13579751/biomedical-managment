import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import streamlit as st
import datetime
from database import get_all_devices, get_scores_by_device_id, delete_scoring_parameters, insert_scoring_parameters, auto_update_scoring_parameters, get_active_fuzzy_config
from database import conn, cur

# --- Setup Fuzzy Logic ---
def setup_fuzzy_system(fuzzy_config=None):
    """
    Setup fuzzy system con parametri configurabili da database
    
    Args:
        fuzzy_config: Dict con parametri age e downtime (opzionale)
                      Se None, carica la configurazione attiva dal database
    """
    # Se non fornita configurazione, carica quella attiva dal database
    if fuzzy_config is None:
        from database import get_active_fuzzy_config
        fuzzy_config = get_active_fuzzy_config()
    
    # Se ancora None, usa valori di default hardcoded
    if fuzzy_config is None:
        fuzzy_config = {
            'age': {
                'new': [0.0, 0.0, 3.0, 5.0],
                'middle': [4.0, 5.0, 10.0, 11.0],
                'old': [10.0, 12.0, 20.0, 20.0]
            },
            'downtime': {
                'low': [0.0, 0.0, 1.0, 2.0],
                'middle': [1.0, 2.0, 3.0, 4.0],
                'high': [3.0, 4.0, 365.0, 365.0]
            }
        }

    service=ctrl.Antecedent(np.arange(0,5,0.1), 'service')
    spare_parts = ctrl.Antecedent(np.arange(0, 5, 0.1), 'spare_parts')
    age = ctrl.Antecedent(np.arange(0, 20, 0.1), 'age')
    backup=ctrl.Antecedent(np.arange(0,7,1), 'backup')
    eq_function = ctrl.Antecedent(np.arange(0, 5, 0.01), 'eq_function')
    downtime = ctrl.Antecedent(np.arange(0, 365, 1), 'downtime')
    support=ctrl.Consequent(np.arange(0,10.1,0.01),'support')
    mission = ctrl.Consequent(np.arange(0, 10.1, 0.01), 'mission')
    support_result=ctrl.Antecedent(np.arange(0,10.1,0.01),'support_result')
    mission_result = ctrl.Antecedent(np.arange(0, 10.1, 0.01), 'mission_result')
    criticity = ctrl.Consequent(np.arange(0, 10.1, 0.01), 'criticity')

    # Membership functions
    # service['No'] = fuzz.trapmf(service.universe, [0,0,0.5,0.7])
    # service['Yes']=fuzz.trimf(service.universe,[0.5,1,2])

    # spare_parts['No'] = fuzz.trapmf(spare_parts.universe, [0,0, 0.5,0.7])
    # spare_parts['Yes']=fuzz.trimf(spare_parts.universe,[0.5,1,2])

    service['No'] = fuzz.gaussmf(service.universe, mean=0, sigma=0.1)
    service['Yes'] = fuzz.gaussmf(service.universe, mean=1, sigma=0.1)

    # Spare Parts (valori discreti: 0=No, 1=Yes)
    spare_parts['No'] = fuzz.gaussmf(spare_parts.universe, mean=0, sigma=0.1)
    spare_parts['Yes'] = fuzz.gaussmf(spare_parts.universe, mean=1, sigma=0.1)


    age['New'] = fuzz.trapmf(age.universe, fuzzy_config['age']['new'])
    age['Middle'] = fuzz.trapmf(age.universe, fuzzy_config['age']['middle'])
    age['Old'] = fuzz.trapmf(age.universe, fuzzy_config['age']['old'])
    # age['New'] = fuzz.trapmf(age.universe, [0, 0, 3, 5])
    # age['Middle'] = fuzz.trapmf(age.universe, [4,5,10,11])
    # age['Old'] = fuzz.trapmf(age.universe, [10, 12, 20, 20])
    # age['New'] = fuzz.gaussmf(age.universe, mean=2, sigma=1.0)
    # age['Middle'] = fuzz.gaussmf(age.universe, mean=5.5, sigma=1.2)
    # age['Old'] = fuzz.gaussmf(age.universe, mean=10, sigma=2.0)

    backup['0'] = fuzz.trimf(backup.universe, [0, 0, 0.5])
    backup['1-2'] = fuzz.trapmf(backup.universe, [0.5, 1, 2, 2.5])
    backup['>=3']= fuzz.trapmf(backup.universe, [2.5, 3, 6, 6])

    eq_function['Analytical/Support'] = fuzz.gaussmf(eq_function.universe, 1, 0.1)
    eq_function['Diagnostic'] = fuzz.gaussmf(eq_function.universe, 2, 0.1)
    eq_function['Therapeutic'] = fuzz.gaussmf(eq_function.universe, 3, 0.1)
    eq_function['Life saving/Life support']= fuzz.gaussmf(eq_function.universe,4,0.1)


    downtime['Low'] = fuzz.trapmf(downtime.universe, fuzzy_config['downtime']['low'])
    downtime['Middle'] = fuzz.trapmf(downtime.universe, fuzzy_config['downtime']['middle'])
    downtime['High'] = fuzz.trapmf(downtime.universe, fuzzy_config['downtime']['high'])
    # downtime['Low'] = fuzz.trapmf(downtime.universe, [0, 0,1, 2])
    # downtime['Middle'] = fuzz.trapmf(downtime.universe, [1, 2, 3, 4])
    # downtime['High'] = fuzz.trapmf(downtime.universe, [3, 4, 365, 365])

    support['Low'] = fuzz.trapmf(support.universe, [0, 0, 2, 5])
    support['Medium'] = fuzz.trimf(support.universe, [3, 5, 7])
    support['High'] = fuzz.trapmf(support.universe, [5, 8, 10, 10])

    support_result['Low'] = fuzz.trapmf(support_result.universe, [0, 0, 2, 5])
    support_result['Medium'] = fuzz.trimf(support_result.universe, [3, 5, 7])
    support_result['High'] = fuzz.trapmf(support_result.universe, [5, 8, 10, 10])

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
        ctrl.Rule(spare_parts['Yes'] & service['Yes'], support['High']),
        ctrl.Rule(spare_parts['No'] & service['Yes'], support['Medium']),
        ctrl.Rule(spare_parts['Yes'] & service['No'], support['Low']),
        ctrl.Rule(spare_parts['No'] & service['No'], support['Low']),
    ]

    rule_m = [
        ctrl.Rule(backup["0"] & eq_function['Analytical/Support'] & downtime['Low'], mission['Low']),
        ctrl.Rule(backup["0"] & eq_function['Analytical/Support'] & downtime['Middle'], mission['Medium']),
        ctrl.Rule(backup["0"] & eq_function['Analytical/Support'] & downtime['High'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Diagnostic'] & downtime['Low'], mission['Low']),
        ctrl.Rule(backup["0"] & eq_function['Diagnostic'] & downtime['Middle'], mission['Medium']),
        ctrl.Rule(backup["0"] & eq_function['Diagnostic'] & downtime['High'], mission['High']),        
        ctrl.Rule(backup["0"] & eq_function['Therapeutic'] & downtime['Low'], mission['Medium']),
        ctrl.Rule(backup["0"] & eq_function['Therapeutic'] & downtime['Middle'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Therapeutic'] & downtime['High'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Life saving/Life support'] & downtime['Low'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Life saving/Life support'] & downtime['Middle'], mission['High']),
        ctrl.Rule(backup["0"] & eq_function['Life saving/Life support'] & downtime['High'], mission['High']),

        ctrl.Rule(backup["1-2"] & eq_function['Therapeutic'] & downtime['Low'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Therapeutic'] & downtime['Middle'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Therapeutic'] & downtime['High'], mission['High']),
        ctrl.Rule(backup["1-2"] & eq_function['Diagnostic'] & downtime['Low'], mission['Low']),
        ctrl.Rule(backup["1-2"] & eq_function['Diagnostic'] & downtime['Middle'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Diagnostic'] & downtime['High'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Analytical/Support'] & downtime['Low'], mission['Low']),
        ctrl.Rule(backup["1-2"] & eq_function['Analytical/Support'] & downtime['Middle'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Analytical/Support'] & downtime['High'], mission['Medium']),
        ctrl.Rule(backup["1-2"] & eq_function['Life saving/Life support'] & downtime['Low'], mission['High']),
        ctrl.Rule(backup["1-2"] & eq_function['Life saving/Life support'] & downtime['Middle'], mission['High']),
        ctrl.Rule(backup["1-2"] & eq_function['Life saving/Life support'] & downtime['High'], mission['High']),

        ctrl.Rule(backup[">=3"] & eq_function['Therapeutic'] & downtime['Low'], mission['Medium']),
        ctrl.Rule(backup[">=3"] & eq_function['Therapeutic'] & downtime['Middle'], mission['Medium']),
        ctrl.Rule(backup[">=3"] & eq_function['Therapeutic'] & downtime['High'], mission['High']),
        ctrl.Rule(backup[">=3"] & eq_function['Diagnostic'] & downtime['Low'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Diagnostic'] & downtime['Middle'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Diagnostic'] & downtime['High'], mission['Medium']),
        ctrl.Rule(backup[">=3"] & eq_function['Analytical/Support'] & downtime['Low'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Analytical/Support'] & downtime['Middle'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Analytical/Support'] & downtime['High'], mission['Low']),
        ctrl.Rule(backup[">=3"] & eq_function['Life saving/Life support'] & downtime['Low'], mission['High']),
        ctrl.Rule(backup[">=3"] & eq_function['Life saving/Life support'] & downtime['Middle'], mission['High']),
        ctrl.Rule(backup[">=3"] & eq_function['Life saving/Life support'] & downtime['High'], mission['High']),
    ]

    rule_f = [

    ctrl.Rule(mission_result['Low'] & support_result['Low'] & age['New'], criticity['Medium']),
    ctrl.Rule(mission_result['Low'] & support_result['Low'] & age['Middle'], criticity['Medium']),
    ctrl.Rule(mission_result['Low'] & support_result['Low'] & age['Old'], criticity['High']),
    ctrl.Rule(mission_result['Low'] & support_result['Medium'] & age['New'], criticity['VeryLow']),
    ctrl.Rule(mission_result['Low'] & support_result['Medium'] & age['Middle'], criticity['Medium']),
    ctrl.Rule(mission_result['Low'] & support_result['Medium'] & age['Old'], criticity['High']),
    ctrl.Rule(mission_result['Low'] & support_result['High'] & age['New'], criticity['VeryLow']),
    ctrl.Rule(mission_result['Low'] & support_result['High'] & age['Middle'], criticity['Low']),
    ctrl.Rule(mission_result['Low'] & support_result['High'] & age['Old'], criticity['Medium']),

    ctrl.Rule(mission_result['Medium'] & support_result['Low'] & age['New'], criticity['Medium']),
    ctrl.Rule(mission_result['Medium'] & support_result['Low'] & age['Middle'], criticity['High']),
    ctrl.Rule(mission_result['Medium'] & support_result['Low'] & age['Old'], criticity['VeryHigh']),
    ctrl.Rule(mission_result['Medium'] & support_result['Medium'] & age['New'], criticity['Low']),
    ctrl.Rule(mission_result['Medium'] & support_result['Medium'] & age['Middle'], criticity['Medium']),
    ctrl.Rule(mission_result['Medium'] & support_result['Medium'] & age['Old'], criticity['High']),
    ctrl.Rule(mission_result['Medium'] & support_result['High'] & age['New'], criticity['VeryLow']),
    ctrl.Rule(mission_result['Medium'] & support_result['High'] & age['Middle'], criticity['Low']),
    ctrl.Rule(mission_result['Medium'] & support_result['High'] & age['Old'], criticity['High']),

    ctrl.Rule(mission_result['High'] & support_result['Low'] & age['New'], criticity['Medium']),
    ctrl.Rule(mission_result['High'] & support_result['Low'] & age['Middle'], criticity['VeryHigh']),
    ctrl.Rule(mission_result['High'] & support_result['Low'] & age['Old'], criticity['VeryHigh']),
    ctrl.Rule(mission_result['High'] & support_result['Medium'] & age['New'], criticity['Medium']),
    ctrl.Rule(mission_result['High'] & support_result['Medium'] & age['Middle'], criticity['Medium']),
    ctrl.Rule(mission_result['High'] & support_result['Medium'] & age['Old'], criticity['High']),
    ctrl.Rule(mission_result['High'] & support_result['High'] & age['New'], criticity['Low']),
    ctrl.Rule(mission_result['High'] & support_result['High'] & age['Middle'], criticity['Medium']),
    ctrl.Rule(mission_result['High'] & support_result['High'] & age['Old'], criticity['High']),

   
]

    mission_ctrl = ctrl.ControlSystem(rule_m)
    support_ctrl=ctrl.ControlSystem(rule_s)
    criticity_ctrl = ctrl.ControlSystem(rule_f)

    mission_simulation = ctrl.ControlSystemSimulation(mission_ctrl)
    support_simulation=ctrl.ControlSystemSimulation(support_ctrl)
    criticity_simulation = ctrl.ControlSystemSimulation(criticity_ctrl)

    return {
        'mission_simulation': mission_simulation,
        'support_simulation' : support_simulation,
        'criticity_simulation': criticity_simulation
    }

# --- Funzione calcolo fuzzy ---
def calculate_fuzzy_scores(age,eq_f,downtime,service,spare_parts,backup):     
    try:
        fuzzy_system = setup_fuzzy_system()
        
        age = float(age)
        downtime = float(downtime)
        eq_f = float(eq_f)
        service=float(service)
        spare_parts=float(spare_parts)
        backup=float(backup)
        
        fuzzy_system['mission_simulation'].input['downtime'] = downtime
        fuzzy_system['mission_simulation'].input['eq_function'] = eq_f
        fuzzy_system['mission_simulation'].input['backup']=backup
        fuzzy_system['support_simulation'].input['service']=service
        fuzzy_system['support_simulation'].input['spare_parts']=spare_parts
        
        fuzzy_system['mission_simulation'].compute()
        fuzzy_system['support_simulation'].compute()
        
        if 'mission' not in fuzzy_system['mission_simulation'].output:
            return None, None, None
        if 'support' not in fuzzy_system['support_simulation'].output:
            return None, None, None
        
        mis_score = float(fuzzy_system['mission_simulation'].output['mission'])
        supp_score=float(fuzzy_system['support_simulation'].output['support'])
        
        fuzzy_system['criticity_simulation'].input['mission_result'] = mis_score
        fuzzy_system['criticity_simulation'].input['support_result']=supp_score
        fuzzy_system['criticity_simulation'].input['age']=age
        fuzzy_system['criticity_simulation'].compute()
        
        if 'criticity' not in fuzzy_system['criticity_simulation'].output:
            return mis_score, supp_score, None
            
        crit_score = float(fuzzy_system['criticity_simulation'].output['criticity'])
        return mis_score, supp_score, crit_score
        
    except Exception as e:
        return None, None, None

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
        from fuzzy_logic import setup_fuzzy_system, calculate_fuzzy_scores
        setup_fuzzy_system()
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, device in enumerate(all_devices):
            device_id = device[0]
            
            try:
                # Aggiorna progress bar
                progress = (i + 1) / len(all_devices)
                progress_bar.progress(progress)
                status_text.text(f'Processing Device ID: {device_id} ({i+1}/{len(all_devices)})')
                
                # Recupera i parametri esistenti
                existing_params = get_scores_by_device_id(device_id)
                
                # Controlla se esistono i parametri
                if not existing_params or len(existing_params) < 9:
                    skipped_count += 1
                    continue
                
                # Estrai i parametri dalla tabella scoring_parameters
                # Struttura: parameter_id, device_id, assessment_date, age_years, downtime,
                #           service_availability, spare_parts_availability, backup, eq_function,
                #           vulnerability_score, miss_score, supp_score, criticity_score
                
                age_years = existing_params[3]  # age_years
                downtime = existing_params[4]   # downtime
                service_availability = existing_params[5]  # service_availability
                spare_parts_availability = existing_params[6]  # spare_parts_availability
                backup = existing_params[7]  # backup
                equipment_function_score = existing_params[8]  # eq_function
                
                # *** CONTROLLO NULL e ZERO - Age deve essere valido (non None e non 0) ***
                # Gli altri parametri vengono controllati solo per None
                if age_years is None or age_years == 0:
                    # Age non valido - aggiorna con score NULL
                    delete_scoring_parameters(device_id)
                    assessment_date = datetime.date.today()
                    vulnerability_score = 0
                    
                    insert_scoring_parameters(
                        device_id, 
                        assessment_date, 
                        service_availability,
                        spare_parts_availability, 
                        backup, 
                        equipment_function_score,
                        vulnerability_score,
                        None,  # miss_score
                        None,  # supp_score
                        None   # criticity_score
                    )
                    skipped_count += 1
                    continue
                
                # Controlla che anche gli altri parametri necessari non siano None
                other_required_params = [
                    downtime, service_availability,
                    spare_parts_availability, backup, equipment_function_score
                ]
                
                if any(param is None for param in other_required_params):
                    # Altri parametri mancanti - aggiorna con score NULL
                    delete_scoring_parameters(device_id)
                    assessment_date = datetime.date.today()
                    vulnerability_score = 0
                    
                    insert_scoring_parameters(
                        device_id, 
                        assessment_date, 
                        service_availability,
                        spare_parts_availability, 
                        backup, 
                        equipment_function_score,
                        vulnerability_score,
                        None,  # miss_score
                        None,  # supp_score
                        None   # criticity_score
                    )
                    skipped_count += 1
                    continue
                
                # Calcola i punteggi fuzzy con i 6 parametri corretti
                mis_score, supp_score, crit_score = calculate_fuzzy_scores(
                    age_years,                      # age
                    equipment_function_score,       # eq_function
                    downtime,                       # downtime
                    service_availability,           # service
                    spare_parts_availability,       # spare_parts
                    backup                          # backup
                )
                
                # Verifica che i punteggi siano validi
                if mis_score is None or supp_score is None or crit_score is None:
                    # Calcolo fallito - aggiorna con score NULL
                    delete_scoring_parameters(device_id)
                    assessment_date = datetime.date.today()
                    vulnerability_score = 0
                    
                    insert_scoring_parameters(
                        device_id, 
                        assessment_date, 
                        service_availability,
                        spare_parts_availability, 
                        backup, 
                        equipment_function_score,
                        vulnerability_score,
                        None,  # miss_score
                        None,  # supp_score
                        None   # criticity_score
                    )
                    error_count += 1
                    error_details.append(f"Device {device_id}: Invalid fuzzy scores calculated, saved with NULL scores")
                    continue
                
                # Aggiorna i punteggi nel database
                delete_scoring_parameters(device_id)
                
                assessment_date = datetime.date.today()
                vulnerability_score = 0
                
                insert_scoring_parameters(
                    device_id, 
                    assessment_date, 
                    service_availability,
                    spare_parts_availability, 
                    backup, 
                    equipment_function_score,
                    vulnerability_score,
                    mis_score, 
                    supp_score, 
                    crit_score
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
        
        
        # Mostra dettagli errori se ci sono
        if error_details:
            st.error("Error Details:")
            for error in error_details[:10]:  # Mostra solo i primi 10 errori
                st.text(error)
            if len(error_details) > 10:
                st.text(f"... and {len(error_details) - 10} more errors")
            st.info("Note: Devices with errors were saved with NULL scores in the database.")
        
        if skipped_count > 0:
            st.warning(f"{skipped_count} devices were saved with NULL scores due to missing parameters. Complete the missing data in 'Edit Medical Device' in 'Device Inventory' to calculate valid scores.")
        
    except Exception as e:
        st.error(f"❌ Error during bulk calculation: {str(e)}")






