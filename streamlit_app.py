import streamlit as st
import pandas as pd
import json
import re
from supabase import create_client, Client

# App configuratie
st.set_page_config(page_title="Liquicity Community Planner 2026", page_icon="👨‍🚀", layout="wide")

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
        ["👨‍🚀 Liquicity weekend", "💶 Tickets & Spullen Kosten", "🎵 Timetable / Line-up", 
         "🧳 Groeps-Paklijst", "🚗 Autoreis & Parkeren", "📸 Google Foto's", "🎵 Groeps-Playlist", "🚀 Liquicity Info & Media"],
        key="sb_navigation_radio"
    )
    
    st.markdown(f"### 📍 Je bent nu hier: **{gekozen_menu}**")
    st.write("---")


# ==========================================
# PAGINA 1: DATUMS / FESTIVALS PRIKKEN
# ==========================================
    if gekozen_menu == "👨‍🚀 Liquicity weekend":
        st.header("Welk festival weekend gaan we pakken?")
        
        if len(g_data["vrienden"]) == 0:
            st.info("Voeg eerst namen toe in de zijbalk om je voorkeur door te geven!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Jouw voorkeur doorgeven")
                naam = st.selectbox("Wie ben je?", g_data["vrienden"], key="p1_user_selectbox")
                opties = ["Volledig Liquicity Weekend 2026", "Alleen Vrijdag", "Alleen Zaterdag", "Alleen Zondag"]
                
                huidige_voorkeur = g_data["datums"].get(naam, [])
                
                with st.form(key="form_dates_static"):
                    gekozen_datums = st.multiselect("Welke festivals/weekenden kun jij?", opties, default=huidige_voorkeur, key="widget_dates_static")
                    submit_dates = st.form_submit_button("Voorkeur Opslaan")
                    
                    if submit_dates:
                        st.session_state.groeps_data["datums"][naam] = gekozen_datums
                        sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                        st.success("Voorkeur opgeslagen!")
                        st.rerun()
                    
            with col2:
                st.subheader("📊 Live Stemresultaten")
                stem_data = []
                for persoon, festivals in g_data["datums"].items():
                    for f in festivals:
                        stem_data.append({"Festival": f, "Wie": persoon, "Aantal": 1})
                if stem_data:
                    df_stemmen = pd.DataFrame(stem_data)
                    st.bar_chart(data=df_stemmen, x="Festival", y="Aantal", color="Wie", stack=True)
                    st.write("**Gedetailleerd overzicht:**")
                    for p, festivals in g_data["datums"].items():
                        if festivals:
                            st.write(f"• **{p}** heeft gestemd op: {', '.join(festivals)}")
                else:
                    st.info("Nog geen stemmen uitgebracht.")

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
    # PAGINA 3: TIMETABLE / LINE-UP
    # ==========================================
    elif gekozen_menu == "🎵 Timetable / Line-up":
        st.header("🎵 Liquicity Groeps-Timetable (All Stages)")
        
        # Uitgebreide line-up met de Galaxy, Lunar én Solar stages!
        liquicity_acts = [
            # --- VRIJDAG ---
            {"Dag": "Vrijdag", "Tijd": "21:30 - 23:00", "Artiest": "Netsky", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "20:15 - 21:30", "Artiest": "Wilkinson", "Stage": "Galaxy"},
            {"Dag": "Vrijdag", "Tijd": "19:00 - 20:15", "Artiest": "Technimatic", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "18:00 - 19:15", "Artiest": "Lenzman", "Stage": "Lunar"},
            {"Dag": "Vrijdag", "Tijd": "17:00 - 18:00", "Artiest": "NCT", "Stage": "Solar"},
            
            # --- ZATERDAG ---
            {"Dag": "Zaterdag", "Tijd": "21:30 - 23:00", "Artiest": "Hybrid Minds", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "20:00 - 21:30", "Artiest": "Fox Stevenson (LIVE)", "Stage": "Galaxy"},
            {"Dag": "Zaterdag", "Tijd": "18:30 - 20:00", "Artiest": "Koven", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "17:15 - 18:30", "Artiest": "Fred V", "Stage": "Lunar"},
            {"Dag": "Zaterdag", "Tijd": "16:00 - 17:15", "Artiest": "T&Sugah", "Stage": "Solar"},
            
            # --- ZONDAG ---
            {"Dag": "Zondag", "Tijd": "22:00 - 23:30", "Artiest": "Andy C", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "20:30 - 22:00", "Artiest": "Maduk", "Stage": "Galaxy"},
            {"Dag": "Zondag", "Tijd": "19:15 - 20:30", "Artiest": "Etherwood", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "18:00 - 19:15", "Artiest": "Bcee", "Stage": "Lunar"},
            {"Dag": "Zondag", "Tijd": "16:45 - 18:00", "Artiest": "Edlan", "Stage": "Solar"}
        ]
        
        if len(g_data["vrienden"]) == 0:
            st.info("Voeg eerst namen toe in de zijbalk om de timetable te gebruiken!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🪐 Geef jouw 'Must-Sees' door")
                kiezende_vriend = st.selectbox("Wie ben je?", g_data["vrienden"], key="p3_vriend_select")
                
                with st.form(key="form_timetable_isolated"):
                    tijdelijke_vinkjes = {}
                    for act in liquicity_acts:
                        a_name = act["Artiest"]
                        al_gevinkt = kiezende_vriend in g_data["timetable"].get(a_name, [])
                        tijdelijke_vinkjes[a_name] = st.checkbox(f"⏱️ {act['Dag']} {act['Tijd']} | **{a_name}** ({act['Stage']})", value=al_gevinkt)
                        
                    submit_timetable = st.form_submit_button("Mijn Line-up Voorkeuren Opslaan", type="primary")
                    
                    if submit_timetable:
                        for act in liquicity_acts:
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
                    
            with col2:
                st.subheader("📊 Wie staat waar? (Groepsoverzicht)")
                timetable_data = []
                for act in liquicity_acts:
                    a_name = act["Artiest"]
                    wie_gaan = g_data["timetable"].get(a_name, [])
                    timetable_data.append({
                        "Dag": act["Dag"], "Tijd": act["Tijd"], "Artiest": a_name, "Stage": act["Stage"],
                        "Aantal": len(wie_gaan), "Wie gaan er mee?": ", ".join(wie_gaan) if wie_gaan else "Nog niemand (😭)"
                    })
                # Sorteer netjes per dag en tijd
                df_tt = pd.DataFrame(timetable_data)
                st.dataframe(df_tt, use_container_width=True, hide_index=True)

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
            st.warning("⚠️ Vergeet niet vooraf jullie **Parkeerticket** online te kopen via de offiziële Liquicity website!")

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
    # PAGINA 6: GOOGLE FOTO'S (UNIVERSEEL)
    # ==========================================
    elif gekozen_menu == "📸 Google Foto's":
        st.header("📸 Festival Foto's Verzamelen")
        st.write("Deel hier jullie foto's en video's! Elke crew kan hier uniek een eigen albumlink opslaan.")
        
        if "album_url" not in st.session_state.groeps_data:
            st.session_state.groeps_data["album_url"] = ""
            
        with st.form(key="form_photos_url"):
            ingevulde_url = st.text_input("Plak hier de link naar jullie gedeelde Google Foto's album:", value=st.session_state.groeps_data["album_url"])
            submit_photos = st.form_submit_button("💾 Album Link Opslaan")
            
            if submit_photos:
                st.session_state.groeps_data["album_url"] = ingevulde_url.strip()
                sla_groep_data_op(st.session_state.groeps_id, st.session_state.groeps_data)
                st.success("Album link succesvol gekoppeld!")
                st.rerun()
                
        if st.session_state.groeps_data["album_url"]:
            st.write("---")
            st.link_button("📂 Open Ons Gedeelde Festival Album", st.session_state.groeps_data["album_url"], type="primary", use_container_width=True)
        else:
            st.info("Er is nog geen fotoalbum gekoppeld door jullie crew. Plak de deellink hierboven!")

    # ==========================================
    # PAGINA 7: GROEPS-PLAYLIST (OFFICIËLE LIQUICITY VERSION)
    # ==========================================
    elif gekozen_menu == "🎵 Groeps-Playlist":
        st.header("🎵 Onze Gezamenlijke Liquicity Playlist")
        st.write("Luister direct naar de playlist! Elke crew kan hier een eigen Spotify playlist koppelen, of de officiële Liquicity lijst gebruiken.")
        
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
        
        col1_sp, col2_sp = st.columns(2)
        with col1_sp:
            st.subheader("🔊 Live Luisteren")
            # De iframe laadt nu gegarandeerd de officiële Spotify Player op Streamlit Cloud
            st.components.v1.iframe(embed_url, height=400, scrolling=False)
        with col2_sp:
            st.subheader("🎶 Openen in app")
            st.link_button("🎶 Open Playlist in Spotify-App", sp_url, type="primary", use_container_width=True)


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

