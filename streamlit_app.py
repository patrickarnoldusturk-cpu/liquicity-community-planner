import streamlit as st
import pandas as pd
import json
import re
from supabase import create_client, Client

# App configuratie
st.set_page_config(page_title="Liquicity Community Planner 2026", page_icon="👨‍🚀", layout="wide")
# Kogelvrije styling die direct bij het opstarten het menu vergroot
st.html("""
    <style>
    [data-testid="stSidebarRadio"] label, 
    [data-testid="stSidebarRadio"] label p, 
    [data-testid="stSidebarRadio"] label span {
        font-size: 20px !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebarRadio"] div[role="radiogroup"] {
        gap: 12px !important;
    }
    </style>
""")


# ==========================================
# 🔐 SUPABASE DATABASE CONNECTIE (LIVE)
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    # Haalt de geheime URL en Key veilig op uit de Streamlit Advanced Settings Secrets
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Fout bij het verbinden met de centrale database. Controleer de Secrets!")
    st.stop()

# Helper functies voor data-afhandeling
def haal_groep_data(g_id):
    try:
        response = supabase.table("crews").select("groeps_data").eq("groeps_id", g_id).execute()
        if response.data:
            return response.data[0]["groeps_data"]
        return None
    except Exception:
        return None

def sla_groep_data_op(g_id, data):
    try:
        # Check of de groep al bestaat
        response = supabase.table("crews").select("id").eq("groeps_id", g_id).execute()
        if response.data:
            # Bestaande groep bijwerken
            supabase.table("crews").update({"groeps_data": data}).eq("groeps_id", g_id).execute()
        else:
            # Nieuwe groep invoegen
            supabase.table("crews").insert({"groeps_id": g_id, "groeps_data": data}).execute()
    except Exception as e:
        st.error(f"Fout bij het opslaan in de database: {e}")

# Initialiseer session state
if 'groeps_id' not in st.session_state:
    st.session_state.groeps_id = ""

# --- SCHERM 1: HET INLOGSCHERM ---
if st.session_state.groeps_id == "":
    st.title("👨‍🚀 De Universele Liquicity Community Planner")
    st.write("Maak een crew aan of log in met jullie unieke groepscode!")
    st.info("👋 Welkom! Deze planner is openbaar bruikbaar voor alle Liquicity-gangers. Vul hieronder een unieke naam in voor jouw vriendengroep om te starten.")
    
    with st.form(key="login_form"):
        gekozen_id = st.text_input("Vul jullie unieke Groepscode in (bijv. 'tent-crew-langedijk'):").strip().lower()
        submit_login = st.form_submit_button("🚀 Start Onze Planner")
        
        if submit_login:
            if gekozen_id != "":
                # Probeer data op te halen uit Supabase
                bestaande_data = haal_groep_data(gekozen_id)
                
                if bestaande_data:
                    st.session_state.groeps_data = bestaande_data
                    st.toast("Bestaande crew succesvol ingeladen!")
                else:
                    # Maak een schone, universele startset aan voor een nieuwe groep
                    st.session_state.groeps_data = {
                        "vrienden": [],
                        "datums": {},
                        "uitgaven": [],
                        "timetable": {},
                        "paklijst": [
                            {"Item": "Partytent", "Wie": "Niemand", "Ingepakt": False},
                            {"Item": "Koelbox + Koelementen", "Wie": "Niemand", "Ingepakt": False},
                            {"Item": "Bluetooth Speaker", "Wie": "Niemand", "Ingepakt": False},
                            {"Item": "Ducttape", "Wie": "Niemand", "Ingepakt": False},
                            {"Item": "Haringen & Hamer", "Wie": "Niemand", "Ingepakt": False},
                            {"Item": "Vuilniszakken", "Wie": "Niemand", "Ingepakt": False}
                        ]
                    }
                    # Direct opslaan in Supabase zodat de crew geregistreerd staat
                    sla_groep_data_op(gekozen_id, st.session_state.groeps_data)
                    st.toast("Nieuwe crew succesvol aangemaakt in de database!")
                
                st.session_state.groeps_id = gekozen_id
                st.rerun()
            else:
                st.error("Vul een geldige code in!")

# --- SCHERM 2: DE PLANNER (NA INLOGGEN) ---
else:
    g_data = st.session_state.groeps_data
    
    # Hulpbalken bovenaan
    st.success(f"🔒 Live verbonden met database als crew: **{st.session_state.groeps_id}**")
    st.info("📱 **Gebruik je een telefoon?** Klik op het pijltje **> linksboven** om het menu te openen!")
    
    # --- SIDEBAR: DYNAMISCHE NAMEN TOEVOEGEN ---
    st.sidebar.header("👥 Wie gaan er mee?")
    nieuwe_naam = st.sidebar.text_input("Voeg een vriend(in) toe aan de crew:", key="sb_add_user_input")
    
    if st.sidebar.button("➕ Voeg toe", key="sb_add_user_btn"):
        if nieuwe_naam and nieuwe_naam.strip() != "":
            s_naam = nieuwe_naam.strip()
            if s_naam not in g_data["vrienden"]:
                st.session_state.groeps_data["vrienden"].append(s_naam)
                sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                st.sidebar.success(f"{s_naam} toegevoegd!")
                st.rerun()
                
    if len(g_data["vrienden"]) == 0:
        st.sidebar.warning("⚠️ Er staan nog geen namen in de crew. Voeg hierboven eerst jezelf en je vrienden toe!")
    else:
        st.sidebar.write("**Huidige crew:**", ", ".join(g_data["vrienden"]))
        
    # Uitlog-knop om naar een andere groep te kunnen switchen
    if st.sidebar.button("🚪 Wissel van Groep/Uitloggen", key="sb_logout_btn"):
        st.session_state.groeps_id = ""
        st.rerun()
        
    # --- DE NAVIGATIE ---
    st.sidebar.write("---")
    st.sidebar.header("📂 Menu Planner")
    

    gekozen_menu = st.sidebar.radio(
        "Ga naar:",
        ["👨‍🚀 Liquicity weekend", "💶 Tickets & Spullen Kosten", "🎫 Ticket Status", "🎵 Timetable / Line-up", 
         "🧳 Groeps-Paklijst", "🚗 Autoreis & Parkeren", "🗺️ Festival Plattegrond", "📸 Google Foto's", "🎵 Groeps-Playlist", "🚀 Liquicity Info & Media"],
        key="sb_navigation_radio"
    )
    
    st.markdown(f"### 📍 Je bent nu hier: **{gekozen_menu}**")
    st.write("---")



# ==========================================
# PAGINA 1: DATUMS / FESTIVALS PRIKKEN
# ==========================================
    if gekozen_menu == "👨‍🚀 Liquicity weekend":
        st.header("🌌 Welcome to the Galaxy!")
        
        # Live afteller aangepast naar de échte startdatum: 24 juli 2026!
        import datetime
        festival_datum = datetime.date(2026, 7, 24)
        vandaag = datetime.date.today()
        dagen_te_gaan = (festival_datum - vandaag).days
        
        if dagen_te_gaan > 0:
            st.metric(label="🚀 Dagen tot Liquicity Festival 2026", value=f"{dagen_te_gaan} dagen")
        elif dagen_te_gaan == 0:
            st.balloons()
            st.success("✨ TIME TO FLY! Liquicity begint VANDAAG! ✨")
        else:
            st.info("🌌 Geniet na van een geweldige editie!")

            
        st.write("---")
        
        if len(g_data["vrienden"]) == 0:
            st.info("🌌 Voeg eerst de namen van je festivalcrew toe in de zijbalk om je voorkeuren door te geven!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🪐 Jouw Festival Ticket claimen")
                naam = st.selectbox("Wie van de crew ben je?", g_data["vrienden"], key="p1_user_selectbox")
                
                # Aangepast naar de echte ticket-opties van Liquicity
                opties = ["Volledig Weekend Ticket (incl. Camping)", "Alleen Vrijdag", "Alleen Zaterdag", "Alleen Zondag"]
                
                # 1. Haal de opgeslagen data op
                opgeslagen_voorkeur = g_data["datums"].get(naam, [])
                
                # 2. Filter oude festivalnamen eruit om de crash te voorkomen
                huidige_voorkeur = [v for v in opgeslagen_voorkeur if v in opties]
                
                # 3. Start het formulier met de gefilterde lijst en de knop
                with st.form(key="form_dates_static"):
                    gekozen_datums = st.multiselect(
                        "Welke dagen ben jij erbij in Geestmerambacht?", 
                        opties, 
                        default=huidige_voorkeur, 
                        key="widget_dates_static"
                    )
                    submit_dates = st.form_submit_button("💾 Mijn Voorkeur Opslaan")

                    
                    if submit_dates:
                        st.session_state.groeps_data["datums"][naam] = gekozen_datums
                        sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                        st.success("✨ Crew voorkeur succesvol opgeslagen!")
                        st.rerun()
                    
            with col2:
                st.subheader("📊 Crew Bezettingsgraad")
                stem_data = []
                for persoon, festivals in g_data["datums"].items():
                    for f in festivals:
                        stem_data.append({"Ticket type": f, "Crewlid": persoon, "Aantal": 1})
                if stem_data:
                    df_stemmen = pd.DataFrame(stem_data)
                    # Mooie grafiek van wie welke tickets pakt
                    st.bar_chart(data=df_stemmen, x="Ticket type", y="Aantal", color="Crewlid", stack=True)
                    st.write("**Gedetailleerd overzicht:**")
                    for p, festivals in g_data["datums"].items():
                        if festivals:
                            st.write(f"• 🧑‍🚀 **{p}** rockt mee op: {', '.join(festivals)}")
                else:
                    st.info("Nog geen astronauten die hun aanwezigheid hebben doorgegeven.")



    # ==========================================
    # PAGINA 2: KOSTEN VERREKENEN
    # ==========================================
    elif gekozen_menu == "💶 Tickets & Spullen Kosten":
        st.header("💶 Festival Pot (Tickets, Drank, Muntjes)")
        
        if len(g_data["vrienden"]) == 0:
            st.info("Voeg eerst namen toe in de zijbalk om de kostenpot te gebruiken!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Nieuwe festivaluitgave invoeren")
                
                with st.form(key="form_add_expense_isolated"):
                    wie_betaalt = st.selectbox("Wie heeft betaald?", g_data["vrienden"])
                    bedrag = st.number_input("Bedrag (€)", min_value=0.0, step=0.01, value=0.0)
                    omschrijving = st.text_input("Waarvoor? (bijv. 'Combi-tickets')")
                    submit_expense = st.form_submit_button("Uitgave Toevoegen")
                    
                    if submit_expense:
                        if bedrag > 0 and omschrijving:
                            st.session_state.groeps_data["uitgaven"].append({"Wie": wie_betaalt, "Bedrag": bedrag, "Omschrijving": omschrijving})
                            sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                            st.success("Uitgave toegevoegd!")
                            st.rerun()

            with col2:
                st.subheader("📈 Tussenstand & Balans")
                if g_data["uitgaven"]:
                    df_uitgaven = pd.DataFrame(g_data["uitgaven"])
                    st.dataframe(df_uitgaven, hide_index=True)
                    totaal = df_uitgaven["Bedrag"].sum()
                    per_persoon = totaal / len(g_data["vrienden"]) if g_data["vrienden"] else 0
                    st.metric("Totale kosten festival", f"€ {totaal:.2f}")
                    st.metric("Kosten per persoon", f"€ {per_persoon:.2f}")
                    
                    balans = {vriend: -per_persoon for vriend in g_data["vrienden"]}
                    for u in g_data["uitgaven"]:
                        if u["Wie"] in balans:
                            balans[u["Wie"]] += u["Bedrag"]
                    for persoon, geld in balans.items():
                        if geld > 0.01:
                            st.write(f"🟢 **{persoon}** krijgt nog **€ {geld:.2f}** terug.")
                        elif geld < -0.01:
                            st.write(f"🔴 **{persoon}** moet nog **€ {abs(geld):.2f}** betalen.")
                        else:
                            st.write(f"⚪ **{persoon}** staat precies quitte.")
                    st.write("---")
                    
                    with st.form(key="form_delete_expense_isolated"):
                        opties_verwijderen = [f"{i}: {u['Wie']} - €{u['Bedrag']} ({u['Omschrijving']})" for i, u in enumerate(g_data["uitgaven"])]
                        te_verwijderen = st.selectbox("Welke uitgave wil je wissen?", opties_verwijderen)
                        submit_delete = st.form_submit_button("🔴 Geselecteerde uitgave wissen")
                        
                    if submit_delete:
                        # Pak het allereerste deel van de split-lijst [0] en zet dit om naar een getal
                        index_to_delete = int(te_verwijderen.split(":")[0])
                        st.session_state.groeps_data["uitgaven"].pop(index_to_delete)
                        sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                        st.success("Uitgave verwijderd!")
                        st.rerun()

                else:
                    st.info("Nog geen groepsuitgaven ingevoerd.")
                    
    # ==========================================
    # PAGINA 2.5: TICKET STATUS (VEILIG OVERZICHT)
    # ==========================================
    elif gekozen_menu == "🎫 Ticket Status":
        st.header("🎫 Groeps-Ticket Checklist")
        st.write("Zorg dat iedereen zijn tickets veilig op orde heeft vóór vertrek. Geen rondslingerende barcodes, wel 100% overzicht!")

        if len(g_data["vrienden"]) == 0:
            st.info("Voeg eerst namen toe in de zijbalk om de ticket-checklist te gebruiken!")
        else:
            if "tickets" not in st.session_state.groeps_data:
                st.session_state.groeps_data["tickets"] = {}

            col1_t, col2_t = st.columns(2)
            with col1_t:
                st.subheader("📝 Update jouw status")
                kiezende_vriend = st.selectbox("Wie ben je?", g_data["vrienden"], key="p25_ticket_user_select")
                
                # Haal eventuele oude data veilig op
                oude_ticket_data = g_data["tickets"].get(kiezende_vriend, {"Weekend": False, "Camping": False, "Notitie": ""})
                
                with st.form(key="form_ticket_status"):
                    weekend_ok = st.checkbox("🎟️ Ik heb mijn Entreeticket (Weekend/Dag) veilig opgeslagen", value=oude_ticket_data.get("Weekend", False))
                    camping_ok = st.checkbox("⛺ Ik heb mijn Camping-ticket binnen (indien nodig)", value=oude_ticket_data.get("Camping", False))
                    ticket_notitie = st.text_input("Waar staat je ticket? (bijv. 'Paylogic mail', 'Mijn Ticketswap'):", value=oude_ticket_data.get("Notitie", ""))
                    
                    submit_ticket = st.form_submit_button("💾 Mijn Status Opslaan", type="primary")
                    
                    if submit_ticket:
                        st.session_state.groeps_data["tickets"][kiezende_vriend] = {
                            "Weekend": weekend_ok,
                            "Camping": camping_ok,
                            "Notitie": ticket_notitie.strip()
                        }
                        sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                        st.success("Je ticketstatus is veilig opgeslagen!")
                        st.rerun()

            with col2_t:
                st.subheader("📊 Live Crew Overzicht")
                st.write("Controleer wie er al helemaal klaar is voor de poort:")
                
                ticket_overzicht = []
                for vriend in g_data["vrienden"]:
                    t_info = g_data["tickets"].get(vriend, {"Weekend": False, "Camping": False, "Notitie": "Nog niet ingevuld"})
                    ticket_overzicht.append({
                        "Crewlid": vriend,
                        "Entree OK": "✅ Ja" if t_info.get("Weekend") else "❌ Nee",
                        "Camping OK": "✅ Ja" if t_info.get("Camping") else "❌ Nee",
                        "Waar te vinden?": t_info.get("Notitie") if t_info.get("Notitie") else "—"
                    })
                
                st.dataframe(pd.DataFrame(ticket_overzicht), use_container_width=True, hide_index=True)

    
    # ==========================================
    # PAGINA 3: TIMETABLE / LINE-UP
    # ==========================================
    elif gekozen_menu == "🎵 Timetable / Line-up":
        st.header("🎵 Liquicity Groeps-Timetable (All Stages)")
        
        # Volledige, officiële 2026 line-up verdeeld per dag en stage
        liquicity_acts = [
            # --- VRIJDAG 24 JULI ---
            # GALAXY STAGE
            {"Dag": "Vrijdag", "Tijd": "11:00 - 12:30", "Artiest": "Midaze", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "12:30 - 13:45", "Artiest": "Kietsune", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "13:45 - 15:00", "Artiest": "Hiraeth", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "15:00 - 16:00", "Artiest": "Yue", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "16:00 - 17:15", "Artiest": "Artino", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "17:15 - 18:45", "Artiest": "Hybrid Minds", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "18:45 - 20:00", "Artiest": "Shy FX", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "20:00 - 21:15", "Artiest": "Maduk", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "21:15 - 22:30", "Artiest": "Kanine", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "22:30 - 00:00", "Artiest": "Andy C", "Stage": "Galaxy"},

            # SOLAR STAGE
            {"Dag": "Vrijdag", "Tijd": "11:00 - 12:15", "Artiest": "Astronymous", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "12:15 - 13:30", "Artiest": "48Past", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "13:30 - 14:45", "Artiest": "Mod", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "14:45 - 15:45", "Artiest": "Voxi", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "15:45 - 16:45", "Artiest": "Bcee", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "16:45 - 18:00", "Artiest": "Sless & Loboski", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "18:00 - 19:00", "Artiest": "Natty Lou", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "19:00 - 20:00", "Artiest": "Eskei83", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "20:00 - 21:00", "Artiest": "Voicians", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "21:00 - 22:00", "Artiest": "Tantrum Desire", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "22:00 - 23:00", "Artiest": "Pirapus", "Stage": "Solar"},
            {"Dag": "Vrijdag", "Tijd": "23:00 - 00:00", "Artiest": "Lexurus", "Stage": "Solar"},

            # LUNAR STAGE
            {"Dag": "Vrijdag", "Tijd": "11:00 - 13:00", "Artiest": "Botone", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "13:00 - 14:15", "Artiest": "Noppo", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "14:15 - 15:30", "Artiest": "Imo-Lu", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "15:30 - 16:45", "Artiest": "Edlan", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "16:45 - 18:15", "Artiest": "Monrroe (Liquid Set)", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "18:15 - 19:30", "Artiest": "4AM Kru", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "19:30 - 21:00", "Artiest": "Pola & Bryson", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "21:00 - 22:30", "Artiest": "S.P.Y", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "22:30 - 00:00", "Artiest": "Imanu", "Stage": "Lunar"},

            # NEBULA STAGE
            {"Dag": "Vrijdag", "Tijd": "11:00 - 13:00", "Artiest": "Kubalo", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "13:00 - 14:00", "Artiest": "As:She", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "14:00 - 15:00", "Artiest": "Drum 'N Babes", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "15:00 - 16:30", "Artiest": "Dnbstep Workshop", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "16:30 - 17:30", "Artiest": "Sebass", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "17:30 - 18:30", "Artiest": "Sub Flow & Top Tier", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "18:30 - 19:30", "Artiest": "Amber Jay", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "19:30 - 20:30", "Artiest": "Curious Mind", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "20:30 - 21:30", "Artiest": "Hot Cues", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "21:30 - 22:30", "Artiest": "Something Else with Fox & Yue", "Stage": "Nebula"},
            {"Dag": "Vrijdag", "Tijd": "22:30 - 23:30", "Artiest": "Blackout Baddies", "Stage": "Nebula"},


            # --- ZATERDAG 25 JULI ---
            # GALAXY STAGE
            {"Dag": "Zaterdag", "Tijd": "11:00 - 12:30", "Artiest": "Midaze", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "12:30 - 14:00", "Artiest": "Operator21", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "14:00 - 15:15", "Artiest": "Matt View & Hannelotta", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "15:15 - 16:30", "Artiest": "Dossa", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "16:30 - 17:45", "Artiest": "Jon Void", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "17:45 - 19:00", "Artiest": "Fox Stevenson (Live)", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "19:00 - 20:15", "Artiest": "Sigma", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "20:15 - 21:30", "Artiest": "Æon:Mode", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "21:30 - 22:45", "Artiest": "Delta Heavy", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "22:45 - 00:00", "Artiest": "Andromedik", "Stage": "Galaxy"},

            # SOLAR STAGE
            {"Dag": "Zaterdag", "Tijd": "11:00 - 12:15", "Artiest": "Astronymous", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "12:15 - 13:15", "Artiest": "Zazu", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "13:15 - 14:15", "Artiest": "L.A.O.S", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "14:15 - 15:15", "Artiest": "Rameses B", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "15:15 - 16:15", "Artiest": "Boxplot", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "16:15 - 17:15", "Artiest": "Cartoon", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "17:15 - 18:30", "Artiest": "NCT & Dualistic", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "18:30 - 19:30", "Artiest": "Matrix & Futurebound", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "19:30 - 20:30", "Artiest": "Koven", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "20:30 - 21:45", "Artiest": "Maduk (Anniversary Set)", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "21:45 - 23:00", "Artiest": "T & Sugah", "Stage": "Solar"},
            {"Dag": "Zaterdag", "Tijd": "23:00 - 00:00", "Artiest": "Feint", "Stage": "Solar"},

            # LUNAR STAGE
            {"Dag": "Zaterdag", "Tijd": "11:00 - 12:45", "Artiest": "Botone", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "12:45 - 14:00", "Artiest": "MiesFM", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "14:00 - 15:00", "Artiest": "Styke", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "15:00 - 16:15", "Artiest": "GLXY", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "16:15 - 17:30", "Artiest": "Telomic", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "17:30 - 19:00", "Artiest": "FD & Submorphics (Lenzman Dedication Set)", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "19:00 - 21:00", "Artiest": "Calibre", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "21:00 - 22:30", "Artiest": "Etherwood", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "22:30 - 00:00", "Artiest": "Technimatic", "Stage": "Lunar"},

            # NEBULA STAGE
            {"Dag": "Zaterdag", "Tijd": "11:00 - 12:00", "Artiest": "Kubalo", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "12:00 - 13:00", "Artiest": "Giant Musical Chairs", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "13:00 - 14:00", "Artiest": "Waves & Nebulaheights", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "14:00 - 15:00", "Artiest": "Enter The Rift", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "15:00 - 16:00", "Artiest": "Wet Socks Beach Party", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "16:00 - 17:00", "Artiest": "Next Horizon", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "17:00 - 18:00", "Artiest": "Fryett", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "18:00 - 19:00", "Artiest": "Fiber Family Takeover", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "19:00 - 20:00", "Artiest": "Time Travelomic 2.0", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "20:00 - 21:00", "Artiest": "Rex Hooligan", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "21:00 - 22:00", "Artiest": "Eetlaste Kaksnurk", "Stage": "Nebula"},
            {"Dag": "Zaterdag", "Tijd": "22:00 - 23:30", "Artiest": "Thrasher", "Stage": "Nebula"},


            # --- ZONDAG 26 JULI ---
            # GALAXY STAGE
            {"Dag": "Zondag", "Tijd": "11:00 - 12:30", "Artiest": "Midaze", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "12:30 - 14:30", "Artiest": "Auris & Friends", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "14:30 - 15:45", "Artiest": "Nymfo", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "15:45 - 17:00", "Artiest": "Goddard.", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "17:00 - 18:00", "Artiest": "Catching Cairo", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "18:00 - 19:00", "Artiest": "Aktive", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "19:00 - 20:15", "Artiest": "Culture Shock", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "20:15 - 21:30", "Artiest": "Wilkinson", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "21:30 - 23:00", "Artiest": "Netsky", "Stage": "Galaxy"},

            # SOLAR STAGE
            {"Dag": "Zondag", "Tijd": "11:00 - 12:00", "Artiest": "Astronymous", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "12:00 - 13:00", "Artiest": "Lirios", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "13:00 - 14:30", "Artiest": "Flint & Figure", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "14:30 - 15:45", "Artiest": "Aperio", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "15:45 - 16:45", "Artiest": "Genetics", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "16:45 - 18:00", "Artiest": "Ekko & Sidetrack", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "18:00 - 19:15", "Artiest": "Disrupta", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "19:15 - 20:30", "Artiest": "Subsonic", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "20:30 - 21:45", "Artiest": "A.M.C", "Stage": "Solar"},
            {"Dag": "Zondag", "Tijd": "21:45 - 23:00", "Artiest": "Mandidextrous", "Stage": "Solar"},

            # LUNAR STAGE
            {"Dag": "Zondag", "Tijd": "11:00 - 12:45", "Artiest": "Botone", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "12:45 - 13:45", "Artiest": "Ipkiss", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "13:45 - 14:45", "Artiest": "Creek", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "14:45 - 16:00", "Artiest": "Alb", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "16:00 - 17:15", "Artiest": "Alibi", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "17:15 - 18:30", "Artiest": "Low:r", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "18:30 - 19:45", "Artiest": "Anaïs", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "19:45 - 21:00", "Artiest": "Skantia", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "21:00 - 22:00", "Artiest": "Basstripper", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "22:00 - 23:00", "Artiest": "Pythius", "Stage": "Lunar"},

            # NEBULA STAGE
            {"Dag": "Zondag", "Tijd": "11:00 - 13:00", "Artiest": "Kubalo", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "13:00 - 14:00", "Artiest": "Maud & Mika Morning Workout", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "14:00 - 15:00", "Artiest": "Dossa's Disco Drive", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "15:00 - 16:00", "Artiest": "Lasyen & Lennart Hoffmann", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "16:00 - 17:00", "Artiest": "Liquicity Office Party", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "17:00 - 18:00", "Artiest": "Prodace & Niek", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "18:00 - 19:00", "Artiest": "Reese Roelvink & Wobble Ockles", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "19:00 - 20:00", "Artiest": "Polygon", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "20:00 - 21:00", "Artiest": "Mxtr", "Stage": "Nebula"},
            {"Dag": "Zondag", "Tijd": "21:00 - 22:00", "Artiest": "Rameses B Psytrance Power Hour", "Stage": "Nebula"},
        ]

        
        if len(g_data["vrienden"]) == 0:
            st.info("Voeg eerst namen toe in de zijbalk om de timetable te gebruiken!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🪐 Geef jouw 'Must-Sees' door")
                kiezende_vriend = st.selectbox("Wie ben je?", g_data["vrienden"], key="p3_vriend_select")
                
                # --- INTERACTIEVE FILTERS ---
                dag_filter = st.multiselect("Filter op Dag:", ["Vrijdag", "Zaterdag", "Zondag"], default=["Vrijdag", "Zaterdag", "Zondag"])
                stage_filter = st.multiselect("Filter op Stage:", ["Galaxy", "Lunar", "Solar", "Nebula"], default=["Galaxy", "Lunar", "Solar", "Nebula"])
                
                # Pas filters direct toe op de weergegeven invullijst
                gefilterde_acts = [act for act in liquicity_acts if act["Dag"] in dag_filter and act["Stage"] in stage_filter]
                
                with st.form(key="form_timetable_isolated"):
                    tijdelijke_vinkjes = {}
                    for act in gefilterde_acts:
                        a_name = act["Artiest"]
                        al_gevinkt = kiezende_vriend in g_data["timetable"].get(a_name, [])
                        tijdelijke_vinkjes[a_name] = st.checkbox(f"📅 {act['Dag']} ({act['Tijd']}) | **{a_name}** — [{act['Stage']}]", value=al_gevinkt)
                        
                    submit_timetable = st.form_submit_button("💾 Mijn Voorkeuren Opslaan", type="primary")
                    
                    if submit_timetable:
                        for act in gefilterde_acts:
                            a_name = act["Artiest"]
                            if a_name not in st.session_state.groeps_data["timetable"]:
                                st.session_state.groeps_data["timetable"][a_name] = []
                            
                            vinkje = tijdelijke_vinkjes[a_name]
                            if vinkje and kiezende_vriend not in st.session_state.groeps_data["timetable"][a_name]:
                                st.session_state.groeps_data["timetable"][a_name].append(kiezende_vriend)
                            elif not vinkje and kiezende_vriend in st.session_state.groeps_data["timetable"][a_name]:
                                st.session_state.groeps_data["timetable"][a_name].remove(kiezende_vriend)
                        
                        sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                        st.success("Timetable succesvol bijgewerkt!")
                        st.rerun()

                # =======================================================
                # 📅 OFFLINE AGENDA EXPORTER (.ICS) - GEPLAATST IN COL1
                # =======================================================
                st.write("---")
                st.subheader("📱 Sla op in je Telefoon Agenda")
                st.info("Genereer een agenda-bestand. Je telefoon geeft op het festivalterrein volledig offline een melding (15 min van tevoren) zodat je favoriete artiesten niet mist!")

                # Verzamel alle acts die deze vriend daadwerkelijk heeft aangevinkt
                mijn_acts = []
                for act in liquicity_acts:
                    a_name = act["Artiest"]
                    if kiezende_vriend in g_data["timetable"].get(a_name, []):
                        mijn_acts.append(act)

                if len(mijn_acts) == 0:
                    st.warning("⚠️ Vink hierboven eerst je favoriete artiesten aan en sla ze op om je persoonlijke agenda te downloaden.")
                else:
                    # Juiste festivaldatums voor Liquicity 2026 (24 t/m 26 juli)
                    datum_mapping = {
                        "Vrijdag": "20260724",
                        "Zaterdag": "20260725",
                        "Zondag": "20260726"
                    }

                    # Genereer iCalendar string handmatig op
                    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Liquicity Crew Planner//NL\nCALSCALE:GREGORIAN\n"
                    
                    for act in mijn_acts:
                        dag_datum = datum_mapping.get(act["Dag"], "20260724")
                        artiest = act["Artiest"]
                        stage = act["Stage"]
                        tijdstip = act["Tijd"]

                        # Fallback tijden (omdat we momenteel dagdelen/uren mixen)
                        start_tijd = "140000"
                        eind_tijd = "153000"

                        # Probeert de tijdstip string te ontleden als er harde tijden instaan (bijv. "19:15 - 20:30")
                        tijd_match = re.search(r'(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})', tijdstip)
                        if tijd_match:
                            start_tijd = f"{tijd_match.group(1)}{tijd_match.group(2)}00"
                            eind_tijd = f"{tijd_match.group(3)}{tijd_match.group(4)}00"

                        ics_content += "BEGIN:VEVENT\n"
                        ics_content += f"SUMMARY:🚀 Liquicity: {artiest}\n"
                        ics_content += f"DTSTART;TZID=Europe/Amsterdam:{dag_datum}T{start_tijd}\n"
                        ics_content += f"DTEND;TZID=Europe/Amsterdam:{dag_datum}T{eind_tijd}\n"
                        ics_content += f"LOCATION:🎪 {stage} Stage - Geestmerambacht\n"
                        ics_content += f"DESCRIPTION:Ingeplande tijdslot: {tijdstip}. Gegenereerd via je Liquicity Community Planner.\\n\n"
                        # Voeg een ingebouwd alarm toe dat 15 minuten voor starttijd afgaat
                        ics_content += "BEGIN:VALARM\nTRIGGER:-PT15M\nACTION:DISPLAY\nDESCRIPTION:Festival Reminder\nEND:VALARM\n"
                        ics_content += "END:VEVENT\n"
                    
                    ics_content += "END:VCALENDAR"

                    # Prachtige Streamlit downloadknop
                    st.download_button(
                        label=f"📥 Download Festival Agenda voor {kiezende_vriend} (.ics)",
                        data=ics_content,
                        file_name=f"liquicity_2026_{kiezende_vriend.lower().replace(' ', '_')}.ics",
                        mime="text/calendar",
                        use_container_width=True,
                        type="secondary"
                    )
                    
            with col2:
                st.subheader("📊 Wie staat waar? (Groepsoverzicht)")
                timetable_data = []
                for act in liquicity_acts:
                    a_name = act["Artiest"]
                    wie_gaan = g_data["timetable"].get(a_name, [])
                    timetable_data.append({
                        "Dag": act["Dag"], "Stage": act["Stage"], "Tijd": act["Tijd"], "Artiest": a_name,
                        "Aantal": len(wie_gaan), "Wie gaan er mee?": ", ".join(wie_gaan) if wie_gaan else "Nog niemand (😭)"
                    })
                
                # DataFrame bouwen en sorteren op de meest populaire acts van je crew
                df_tt = pd. DataFrame(timetable_data)
                df_tt_gefilterd = df_tt[df_tt["Dag"].isin(dag_filter) & df_tt["Stage"].isin(stage_filter)]
                df_tt_gesorteerd = df_tt_gefilterd.sort_values(by="Aantal", ascending=False)
                
                st.dataframe(df_tt_gesorteerd, use_container_width=True, hide_index=True)


    # ==========================================
    # PAGINA 4: GROEPS-PAKLIJST
    # ==========================================
    elif gekozen_menu == "🧳 Groeps-Paklijst":
        st.header("🧳 Wie takes what?")
        vrienden_lijst = ["Niemand"] + g_data["vrienden"]
        
        st.subheader("➕ Nieuw item toevoegen")
        with st.form(key="form_add_packing_item"):
            nieuw_item = st.text_input("Wat moet er nog mee? (bijv. 'Verlengsnoer', 'Koepeltent'):")
            submit_new_item = st.form_submit_button("Voeg item toe aan de lijst")
            
            if submit_new_item and nieuw_item.strip() != "":
                st.session_state.groeps_data["paklijst"].append({
                    "Item": nieuw_item.strip(),
                    "Wie": "Niemand",
                    "Ingepakt": False
                })
                sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                st.success(f"'{nieuw_item}' succesvol opgeslagen!")
                st.rerun()

        st.write("---")
        st.subheader("📋 De Groeps-Checklist")
        
        with st.form(key="form_paklijst_isolated"):
            tijdelijke_wie = []
            tijdelijke_done = []
            
            for i, item in enumerate(g_data["paklijst"]):
                col_a, col_b, col_c = st.columns(3)
                with col_a: 
                    st.write(f"🔹 **{item['Item']}**")
                with col_b: 
                    h_idx = vrienden_lijst.index(item['Wie']) if item['Wie'] in vrienden_lijst else 0
                    tijdelijke_wie.append(st.selectbox(f"Wie voor {item['Item']}?", vrienden_lijst, index=h_idx, key=f"pk_w_{i}"))
                with col_c: 
                    tijdelijke_done.append(st.checkbox(f"Ingepakt ({item['Item']})", value=item['Ingepakt'], key=f"pk_d_{i}"))
                    
            submit_packing = st.form_submit_button("💾 Sla Checklist Wijzigingen Op")
            
            if submit_packing:
                for i in range(len(st.session_state.groeps_data["paklijst"])):
                    st.session_state.groeps_data["paklijst"][i]['Wie'] = tijdelijke_wie[i]
                    st.session_state.groeps_data["paklijst"][i]['Ingepakt'] = tijdelijke_done[i]
                
                sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                st.success("Paklijst succesvol bijgewerkt!")
                st.rerun()
    
    # ==========================================
    # PAGINA 5: AUTOREIS & PARKEREN
    # ==========================================
    elif gekozen_menu == "🚗 Autoreis & Parkeren":
        st.header("🚗 Autoreis & Parkeren")
        st.write("Alle logistiek voor de kogelvrije rit naar Geestmerambacht!")
        
        col1_car, col2_car = st.columns(2)
        with col1_car:
            st.subheader("📍 Navigatie naar Parkeerterrein")
            st.write("Klik op de knop hieronder om direct Google Maps te openen met de route naar het festivalterrein:")
            st.link_button("🗺️ Start Google Maps Navigatie", "https://www.google.com/maps/place/Recreatiegebied+Geestmerambacht/@52.6894141,4.7616385,16z/data=!3m1!4b1!4m6!3m5!1s0x47cf572c1575159d:0x93dad4b4d4d1c852!8m2!3d52.6894109!4d4.7642134!16s%2Fg%2F1tfd66rr?entry=ttu&g_ep=EgoyMDI2MDcwOC4wIKXMDSoASAFQAw%3D%3D", type="primary", use_container_width=True)
            
            st.write("---")
            st.subheader("🎫 Parkeerkaart Herinnering")
            st.warning("⚠️ Vergeet niet vooraf jullie **Parkeerticket** online te kopen via de officiële Liquicity website!")
            st.warning("⚠️ Let op: Parkeerkaarten moeten vooraf online worden gekocht en zijn het goedkoopst in de voorverkoop!")
            st.link_button("🎟️ Koop Je Parkeerticket Online", "https://shop.celebratix.io/?t=4a8fb", type="secondary", use_container_width=True)

        
        with col2_car:
            st.subheader("📌 Waar staat de auto?")
            st.write("Vul hier bij aankomst in waar de auto's geparkeerd staan. Wel zo fijn voor de maandagochtend!")
            
            with st.form(key="form_car_location"):
                if "auto_locatie" not in st.session_state.groeps_data:
                    st.session_state.groeps_data["auto_locatie"] = ""
                    
                auto_loc_input = st.text_area("Typ hier de parkeerplek (bijv. Vak B, Rij 3):", value=st.session_state.groeps_data["auto_locatie"])
                submit_car = st.form_submit_button("💾 Parkeerplek Opslaan")
                
                if submit_car:
                    st.session_state.groeps_data["auto_locatie"] = auto_loc_input
                    sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                    st.success("Parkeerplek succesvol opgeslagen!")
                    st.rerun()

    # ==========================================
    # PAGINA 5.5: FESTIVAL PLATTEGROND
    # ==========================================
    elif gekozen_menu == "🗺️ Festival Plattegrond":
        st.header("🗺️ Liquicity Festival Map")
        st.write("Navigeer blindelings tussen de Galaxy, Lunar en Solar stages!")
        st.write("---")
        
        st.subheader("🎪 Live Kaart Bekijken")
        
        # Streamlit laadt hier direct de afbeelding die je zojuist in GitHub hebt gezet
        try:
            st.image(
                "plattegrond.png", 
                caption="Liquicity Festival Terrein - Geestmerambacht",
                use_container_width=True
            )
        except Exception:
            st.info("🌌 De plattegrond wordt geladen zodra 'plattegrond.png' is geüploade naar je GitHub!")

        st.write("---")
        # Handige grote knop voor telefoons op het festivalterrein zelf
        st.link_button(
            "📂 Open Officiële Liquicity Map Website", 
            "https://festival.liquicity.com/practical/map/", 
            type="primary", 
            use_container_width=True
        )



    # ==========================================
    # PAGINA 6: GOOGLE FOTO'S (UNIVERSEEL MET CREATIE-HULP)
    # ==========================================
    elif gekozen_menu == "📸 Google Foto's":
        st.header("📸 Festival Foto's Verzamelen")
        st.write("Deel hier jullie foto's en video's van het weekend!")
        
        if "album_url" not in st.session_state.groeps_data:
            st.session_state.groeps_data["album_url"] = ""
            
        col1_ph, col2_ph = st.columns(2)
        with col1_ph:
            st.subheader("🛠️ Stap 1: Maak een album aan (Indien nodig)")
            st.write("Heeft jullie crew nog geen gezamenlijk album? Gebruik deze directe snelkoppeling om er binnen 5 seconden gratis een aan te maken:")
            # Directe link naar de album-aanmaakpagina van Google Photos
            st.link_button("✨ Snelkoppeling: Maak Nieuw Google Album", "https://photos.google.com/albums", type="secondary", use_container_width=True)
            st.info("💡 **Tip:** Zorg dat je in Google Photos bij de album-instellingen 'Delen' inschakelt en de link kopieert!")

        with col2_ph:
            st.subheader("🔗 Stap 2: Koppel de albumlink")
            with st.form(key="form_photos_url"):
                ingevulde_url = st.text_input("Plak hier de link naar jullie gedeelde Google Foto's album:", value=st.session_state.groeps_data["album_url"])
                submit_photos = st.form_submit_button("💾 Album Link Opslaan")
                
                if submit_photos:
                    st.session_state.groeps_data["album_url"] = ingevulde_url.strip()
                    sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                    st.success("Album link succesvol gekoppeld aan de database!")
                    st.rerun()
                
        if st.session_state.groeps_data["album_url"]:
            st.write("---")
            st.subheader("📂 Ons Gedeelde Festival Album")
            st.link_button("📂 Open Ons Gedeelde Festival Album", st.session_state.groeps_data["album_url"], type="primary", use_container_width=True)
        else:
            st.info("Er is nog geen fotoalbum gekoppeld door jullie crew. Volg de stappen hierboven om jullie album live te zetten!")


    # ==========================================
    # PAGINA 7: GROEPS-PLAYLIST (OFFICIËLE LIQUICITY VERSION)
    # ==========================================
    elif gekozen_menu == "🎵 Groeps-Playlist":
        st.header("🎵 Onze Gezamenlijke Liquicity Playlist")
        st.write("Luister direct naar de playlist of livesets! Elke crew kan hier een eigen Spotify playlist koppelen.")
        
        # De officiële Liquicity afspeellijst ingesteld als de nieuwe universele standaard
        officiele_liquicity_playlist = "https://open.spotify.com/playlist/19y0UVk0bcrJWEqMwBHosj"
        
        # FIX 1: Als de link leeg is, ontbreekt, of de foute basis-URL bevat, overschrijven met de officiële link
        if "playlist_url" not in st.session_state.groeps_data or \
           st.session_state.groeps_data["playlist_url"] == "https://spotify.com" or \
           st.session_state.groeps_data["playlist_url"] == "" or \
           "playlist/" not in st.session_state.groeps_data["playlist_url"]:
            st.session_state.groeps_data["playlist_url"] = officiele_liquicity_playlist
            
        with st.form(key="form_playlist_url"):
            ingevulde_sp = st.text_input("Plak hier de link naar jullie Spotify playlist (of laat de officiële lijst staan):", value=st.session_state.groeps_data["playlist_url"])
            submit_playlist = st.form_submit_button("💾 Playlist Link Opslaan")
            
            if submit_playlist:
                st.session_state.groeps_data["playlist_url"] = ingevulde_sp.strip()
                sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                st.success("Playlist succesvol gekoppeld!")
                st.rerun()
                
        sp_url = st.session_state.groeps_data["playlist_url"]
        playlist_id = "19y0UVk0bcrJWEqMwBHosj" # Gegarandeerde back-up ID
        
        # Filter de 22-cijferige code uit de link
        match = re.search(r'playlist/([a-zA-Z0-9]{22})', sp_url)
        if match:
            playlist_id = match.group(1)
            
        # FIX 2: De kogelvrije embed.spotify.com gateway om de cloud-blokkade en IP-fouten op te lossen
        embed_url = f"https://embed.spotify.com/playlist/{playlist_id}?utm_source=generator&theme=0"
        
        # Maak twee gelijke kolommen naast elkaar voor Spotify en SoundCloud
        col1_sp, col2_sp = st.columns(2)
        
        with col1_sp:
            st.subheader("🟢 Spotify Player")
            # Jouw werkende Spotify iframe
            st.components.v1.iframe(embed_url, height=400, scrolling=False)
            st.link_button("🎶 Open in Spotify-App", sp_url, type="primary", use_container_width=True)
            
        with col2_sp:
            st.subheader("🟠 SoundCloud Sets")
            
            # Sfeervolle festival-infobox in plaats van de weigerende speler
            st.markdown(
                """
                <div style="background-color: #1b1532; padding: 20px; border-radius: 10px; border: 1px solid #3a86ff; text-align: center; margin-bottom: 15px;">
                    <span style="font-size: 40px;">🛸</span>
                    <h4 style="color: #70d6ff; margin-top: 10px; margin-bottom: 5px;">Liquicity Galaxy Mixes</h4>
                    <p style="font-size: 14px; color: #ffffff;">Luister naar de dikste Drum & Bass livesets en legendarische Yearmixes direct via SoundCloud.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Grote opvallende knop die perfect werkt op telefoons
            st.link_button(
                "🔥 Open Liquicity Sets op SoundCloud", 
                "https://soundcloud.com/liquicityrecords/sets/liquicity-festival-2025-full", 
                type="primary", 
                use_container_width=True
            )




    # ==========================================
    # PAGINA 8: LIQUICITY INFO & MEDIA
    # ==========================================
    elif gekozen_menu == "🚀 Liquicity Info & Media":
        st.header("🚀 Liquicity Info & Media")
        st.write("Kom alvast helemaal in de sfeer met de officiële media en socials!")
        
        col1_media, col2_media = st.columns(2)
        with col1_media:
            st.subheader("🎬 Aftermovie 2025")
            st.video("https://www.youtube.com/watch?v=o9ast9cAnLc&t=180s")
        with col2_media:
            st.subheader("📱 Officiële Social Media")
            st.link_button("🌐 Officiële Website", "https://liquicity.com", type="secondary", use_container_width=True)
            st.link_button("📸 Instagram", "https://www.instagram.com/liquicity/", type="secondary", use_container_width=True)
            st.link_button("🎵 TikTok", "https://www.tiktok.com/@liquicity", type="secondary", use_container_width=True)
            st.link_button("💬 Facebook", "https://www.facebook.com/liquicity", type="secondary", use_container_width=True)

