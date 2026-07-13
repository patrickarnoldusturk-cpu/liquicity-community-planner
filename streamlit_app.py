import streamlit as st
import pandas as pd
import json

# App configuratie
st.set_page_config(page_title="Liquicity Community Planner 2026", page_icon="👨‍🚀", layout="wide")
st.title("👨‍🚀 De Universele Liquicity Community Planner")
st.write("Maak een crew aan of log in met jullie unieke groepscode!")

# ==========================================
# 🔐 MULTI-GROUP DATABASE CONNECTIE
# ==========================================
# Hier koppelen we later Supabase om de data live op te slaan per groeps-ID.
# Voor nu start de app op met een kogelvrije lokale scheiding.

if 'groeps_id' not in st.session_state:
    st.session_state.groeps_id = ""

# --- INLOGSCHERM VOOR OPENBAAR GEBRUIK ---
if st.session_state.groeps_id == "":
    st.info("👋 Welkom! Deze app is bruikbaar voor alle Liquicity-gangers. Vul hieronder een unieke naam/code in voor jouw vriendengroep om te starten.")
    
    with st.form(key="login_form"):
        gekozen_id = st.text_input("Vul jullie unieke Groepscode in (bijv. 'tent-crew-langedijk'):").strip().lower()
        submit_login = st.form_submit_button("🚀 Start Onze Planner")
        
        if submit_login:
            if gekozen_id != "":
                st.session_state.groeps_id = gekozen_id
                
                # Maak een schone, lege template aan specifiek voor deze nieuwe groep
                st.session_state.groeps_data = {
                    "vrienden": [],  # Begint helemaal leeg zodat groepen zichzelf toevoegen
                    "datums": {},
                    "uitgaven": [],
                    "timetable": {},
                    "paklijst": [  # Universele start-paklijst voor iedereen
                        {"Item": "Partytent", "Wie": "Niemand", "Ingepakt": False},
                        {"Item": "Koelbox + Koelementen", "Wie": "Niemand", "Ingepakt": False},
                        {"Item": "Bluetooth Speaker", "Wie": "Niemand", "Ingepakt": False},
                        {"Item": "Ducttape", "Wie": "Niemand", "Ingepakt": False},
                        {"Item": "Haringen & Hamer", "Wie": "Niemand", "Ingepakt": False},
                        {"Item": "Vuilniszakken", "Wie": "Niemand", "Ingepakt": False}
                    ]
                }
                st.success(f"Planner succesvol opgestart voor groep: {gekozen_id}!")
                st.rerun()
            else:
                st.error("Vul een geldige code in!")

# --- ALS DE GROEP IS INLOGGD ---
else:
    g_data = st.session_state.groeps_data
    
    # Hulpbalk bovenaan voor mobiel en groepsidentificatie
    st.success(f"🔒 Ingelogd als crew: **{st.session_state.groeps_id}**")
    st.info("📱 **Gebruik je een telefoon?** Klik op het pijltje **> linksboven** om het menu te openen!")
    
    # --- SIDEBAR: DYNAMISCHE NAMEN TOEVOEGEN ---
    st.sidebar.header("👥 Wie gaan er mee?")
    nieuwe_naam = st.sidebar.text_input("Voeg een vriend(in) toe aan de crew:", key="sb_add_user_input")
    
    if st.sidebar.button("➕ Voeg toe", key="sb_add_user_btn"):
        if nieuwe_naam and nieuwe_naam.strip() != "":
            s_naam = nieuwe_naam.strip()
            if s_naam not in g_data["vrienden"]:
                g_data["vrienden"].append(s_naam)
                st.sidebar.success(f"{s_naam} toegevoegd!")
                st.rerun()
                
    if len(g_data["vrienden"]) == 0:
        st.sidebar.warning("⚠️ Er staan nog geen namen in de crew. Voeg hierboven eerst jezelf en je vrienden toe!")
    else:
        st.sidebar.write("**Huidige crew:**", ", ".join(g_data["vrienden"]))
        
    # --- DE NAVIGATIE ---
    st.sidebar.write("---")
    st.sidebar.header("📂 Menu Planner")
    gekozen_menu = st.sidebar.radio(
        "Ga naar:",
        ["👨‍🚀 Liquicity weekend", "💶 Tickets & Spullen Kosten", "🎵 Timetable / Line-up", 
         "🧳 Groeps-Paklijst", "🚗 Autoreis & Parkeren", "🎵 Groeps-Playlist", "🚀 Liquicity Info & Media"],
        key="sb_navigation_radio"
    )
    
    st.markdown(f"### 📍 Je bent nu hier: **{gekozen_menu}**")
    st.write("---")
    
    # [Hieronder plakken we stapsgewijs de stabiele pagina's (Formulieren) die we voor je vrienden-app hebben gebouwd]
