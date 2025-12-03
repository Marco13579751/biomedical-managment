"""
Medical Device Dashboard - Sistema di Gestione Dispositivi Medici
Modularizzato dalla pipeline originale di 4000 righe

Struttura aggiornata:
- config.py: Configurazioni
- database.py: Connessioni e operazioni DB PostgreSQL (con nuove funzioni maintenance)
- fuzzy_logic.py: Sistema fuzzy logic per calcolo punteggi
- authentication.py: Sistema di autenticazione utenti
- pages.py: Gestione pagine dispositivi
- scoring_admin.py: Pagine scoring e amministrazione
- preventive_maintenance.py: Pagina manutenzione preventiva e calibrazione
- incidents_corrective.py: Pagina incidenti e manutenzione correttiva  
- main.py: File principale (questo file)
"""
import streamlit as st
from streamlit_option_menu import option_menu
from config import setup_page_config
from authentication import init_user_state, show_login_page
from pages import show_wards_rooms_page, show_devices_page
from scoring_admin import show_prioritization_score_page, show_admin_panel
from preventive_maintenance import show_preventive_maintenance_page
from incidents_corrective import show_incidents_corrective_page
from cybersecurity import show_cybersecurity_page

def show_sidebar_navigation():
    # CSS styling per sidebar migliorata
    st.markdown("""
    <style>
    /* Sfondo sidebar COLORE SOLIDO */
    .stSidebar > div:first-child {
        background: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1;
    }
    
    /* Menu con STESSO colore solido */
    .stSidebar nav {
        background: #f1f5f9 !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .stSidebar nav > div {
        background: transparent !important;
    }
    
    /* FORZA tutti gli altri elementi */
    .stSidebar div {
        background: transparent !important;
    }
    
    .stSidebar [data-testid="stVerticalBlock"],
    .stSidebar [data-testid="stVerticalBlock"] > div,
    .stSidebar .element-container,
    .stSidebar .stMarkdown {
        background: transparent !important;
    }
    
    /* Leggero pattern texture per più eleganza */
    .stSidebar > div:first-child::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            radial-gradient(circle at 25px 25px, rgba(14, 165, 233, 0.02) 2px, transparent 2px),
            radial-gradient(circle at 75px 75px, rgba(6, 182, 212, 0.02) 2px, transparent 2px);
        background-size: 100px 100px;
        pointer-events: none;
    }
    
    /* Ombra interna per profondità */
    .stSidebar > div:first-child {
        box-shadow: inset -2px 0 4px rgba(148, 163, 184, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation con option-menu
    with st.sidebar:
        st.markdown("### Selection Menu")
        
        selected = option_menu(
            menu_title=None,
            options=[
                "Device Inventory", 
                "Risk Assessment", 
                "Wards & Rooms", 
                "Preventive Maintenance", 
                "Incidents & Repairs",
                "Cybersecurity",  
                "Admin Panel"
            ],
            icons=[
                "laptop", 
                "graph-up-arrow", 
                "hospital", 
                "tools",
                "exclamation-triangle-fill",
                "shield-lock",
                "gear-fill"
            ],
            menu_icon="hospital",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {
                    "padding": "0!important", 
                    "background-color": "#f1f5f9",  # ← STESSO COLORE
                    "box-shadow": "none",
                    "border": "none"
                },
                "icon": {
                    "color": "#0284c7",
                    "font-size": "18px"
                }, 
                "nav-link": {
                    "font-size": "16px", 
                    "text-align": "left", 
                    "margin": "2px 0px",
                    "padding": "12px 16px",
                    "border-radius": "8px",
                    "color": "#1e40af",
                    "font-weight": "500",
                    "background-color": "transparent",
                    "--hover-color": "#ecfeff"
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)",
                    "color": "white",
                    "font-weight": "600"
                },
            }
        )
        
        # Separator
        st.sidebar.divider()
        
        # User info con stato manutenzione
        if "user" in st.session_state and st.session_state["user"]:
            current_user = st.session_state["user"]
            user_role = st.session_state.get("user_role", "Current User:")
            st.sidebar.markdown(f"""
                **👤 {user_role}**  
                *{current_user}*
                """)
                
                
            
           
           
            
            # Separator prima del logout
            st.sidebar.markdown("---")
            
            # Logout button
            col1, col2 = st.sidebar.columns([1, 1])
            with col2:
                if st.button("Logout", type="secondary", use_container_width=True):
                    st.session_state["user"] = None
                    st.sidebar.success("Logout successful!")
                    st.rerun()
    
    return selected

def main():
    """Funzione principale dell'applicazione"""
    # Configura la pagina Streamlit
    setup_page_config()
    
    # Inizializza stato utente
    init_user_state()
    
    # Se l'utente non è loggato, mostra la pagina di login
    if st.session_state["user"] is None:
        show_login_page()
        st.stop()
    
    # Mostra la navigazione nella sidebar e ottieni la pagina selezionata
    page = show_sidebar_navigation()
    
    # Router delle pagine aggiornato
    try:
        if page == "Wards & Rooms":
            show_wards_rooms_page()
        
        elif page == "Device Inventory":
            show_devices_page()
            
        elif page == "Risk Assessment":
            show_prioritization_score_page()
            
        elif page == "Preventive Maintenance":
             show_preventive_maintenance_page()
            
        elif page == "Incidents & Repairs":
            show_incidents_corrective_page()

        elif page == "Cybersecurity":              # <-- AGGIUNGI QUESTO BLOCCO
            show_cybersecurity_page()
            
        elif page == "Admin Panel":
            show_admin_panel()
            
    except ImportError as e:
        st.error(f"""
        ❌ **Errore Import Modulo**
        
        Modulo mancante: {str(e)}
        
        **Istruzioni:**
        1. Assicurati che tutti i file delle pagine siano presenti:
           - `preventive_maintenance.py`
           - `incidents_corrective.py`
           
        2. Verifica che le funzioni nel database.py siano state aggiunte
        
        3. Esegui le query SQL per creare le nuove tabelle
        """)
        
        # Fallback al vecchio sistema
        st.title("Maintenance Management")
        st.info("🚧 This section is under development")
        st.write("Future features:")
        st.write("• Maintenance scheduling")
        st.write("• Work order management") 
        st.write("• Maintenance history tracking")
        st.write("• Preventive maintenance planning")
        st.write("• Incident management")
        st.write("• Corrective maintenance tracking")
        
    except Exception as e:
        st.error(f"""
        ❌ **Errore Generale**
        
        {str(e)}
        
        Contatta l'amministratore di sistema.
        """)

if __name__ == "__main__":
    import streamlit as st
    main()