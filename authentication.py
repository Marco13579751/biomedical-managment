import streamlit as st
from database import db_signin, db_register

# --- Gestione stato utente ---
def init_user_state():
    if "user" not in st.session_state:
        st.session_state["user"] = None

# --- UI Autenticazione ---
def show_login_page():
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


