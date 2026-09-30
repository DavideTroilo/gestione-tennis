import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestione Tennistavolo", layout="wide", page_icon="🏓")

# Inizializzazione del Database nello stato dell'applicazione
if "atleti" not in st.session_state:
    atleti_data = {
        "ID": [f"ATL{i:02d}" for i in range(1, 26)],
        "Nome": [
            "Marco Rossi", "Luca Bianchi", "Andrea Verdi", "Giuseppe Neri", "Antonio Gialli",
            "Giovanni Sergio", "Roberto Viola", "Francesco Marroni", "Alessandro Rosa", "Stefano Azzurri",
            "Davide Arancioni", "Michele Grigi", "Lorenzo Bianchi", "Filippo Neri", "Matteo Rossi",
            "Simone Verdi", "Federico Gialli", "Mattia Sergio", "Gabriele Viola", "Tommaso Marroni",
            "Christian Rosa", "Edoardo Azzurri", "Samuele Arancioni", "Pietro Grigi", "Daniele Marroni"
        ],
        "Categoria": ["A", "A", "A", "A", "B", "B", "B", "B", "B", "B", "C", "C", "C", "C", "C", "D", "D", "D", "D", "D", "E", "E", "E", "E", "E"],
        "Punti": [1500 - (i * 25) for i in range(25)]
    }
    df = pd.DataFrame(atleti_data)
    df = df.sort_values(by=["Categoria", "Punti"], ascending=[True, False]).reset_index(drop=True)
    df["Classifica"] = df.index + 1
    st.session_state.atleti = df

if "prenotazioni" not in st.session_state:
    st.session_state.prenotazioni = []

if "storico" not in st.session_state:
    st.session_state.storico = []

if "tavoli_pubblicati" not in st.session_state:
    st.session_state.tavoli_pubblicati = {}

if "automatico_generato" not in st.session_state:
    st.session_state.automatico_generato = set()

# Sistema di tracciamento dei dispositivi hardware per la sicurezza
if "dispositivi_associati" not in st.session_state:
    st.session_state.dispositivi_associati = {}  # Formato: {"Nome Atleta": "ID_Dispositivo"}

st.title("🏓 Sistema Gestione Allenamenti Tennistavolo")

# Sidebar di controllo simulazione
st.sidebar.header("⚙️ Configurazione Simulazione")
ruolo = st.sidebar.radio("Seleziona il tuo ruolo d'accesso:", ["Atleta", "Amministratore"])

st.sidebar.markdown("---")
st.sidebar.subheader("🕒 Simulazione Orario e Giorno")
giorno = st.sidebar.selectbox("Giorno di allenamento:", ["Lunedì", "Mercoledì", "Venerdì"])
orario_corrente = st.sidebar.slider("Orario attuale:", 8, 22, 12, format="%d:00")
ora_limite = 14

st.sidebar.markdown("---")
st.sidebar.subheader("📱 Simulatore Hardware")
id_telefono_attuale = st.sidebar.text_input("ID del telefono attuale (Simulato):", "Telefono_Di_Prova_A")

tavoli_totali = 6
tavoli_ragazzi = 4 if giorno in ["Lunedì", "Mercoledì"] else 0
posti_turno1 = (tavoli_totali - tavoli_ragazzi) * 2
posti_turno2 = tavoli_totali * 2

def ricalcola_stati(giorno_sel, turno_sel):
    p_turno = [p for p in st.session_state.prenotazioni if p["Giorno"] == giorno_sel and p["Turno"] == turno_sel]
    cap_max = posti_turno1 if "Turno 1" in turno_sel else posti_turno2
    for i, p in enumerate(p_turno):
        p["Stato"] = "Confermato" if i < cap_max else "In Lista d'Attesa"

def genera_accoppiamenti_automatici(giorno_sel, turno_sel):
    presenti = [p for p in st.session_state.prenotazioni if p["Giorno"] == giorno_sel and p["Turno"] == turno_sel and p["Stato"] == "Confermato"]
    if len(presenti) < 2:
        return
    
    nomi_presenti = [p["Nome"] for p in presenti]
    df_presenti = st.session_state.atleti[st.session_state.atleti["Nome"].isin(nomi_presenti)].copy()
    
    tavolo_num = 1
    coppie_generate = []
    rimasti_per_categoria = []
    
    for cat, group in df_presenti.groupby("Categoria"):
        lista_atleti = group.sort_values(by="Classifica")["Nome"].tolist()
        while len(lista_atleti) >= 2:
            coppie_generate.append({"Tavolo": tavolo_num, "Tipo": f"Categoria {cat}", "Giocatore Uno": lista_atleti.pop(0), "Giocatore Due": lista_atleti.pop(0)})
            tavolo_num += 1
        if len(lista_atleti) == 1:
            rimasti_per_categoria.append(lista_atleti.pop(0))
    
    while len(rimasti_per_categoria) >= 2:
        coppie_generate.append({"Tavolo": tavolo_num, "Tipo": "Misto (Salvagente)", "Giocatore Uno": rimasti_per_categoria.pop(0), "Giocatore Due": rimasti_per_categoria.pop(0)})
        tavolo_num += 1
    
    if len(rimasti_per_categoria) == 1:
        coppie_generate.append({"Tavolo": tavolo_num, "Tipo": "Riposo", "Giocatore Uno": rimasti_per_categoria.pop(0), "Giocatore Due": "Nessuno (Riposo)"})
    
    st.session_state.tavoli_pubblicati[f"{giorno_sel}_{turno_sel}"] = coppie_generate

# CONTROLLO SCADENZA ORARIO - AUTOMAZIONE
if orario_corrente >= ora_limite:
    for t_id in ["Turno 1 (18:00 - 20:00)", "Turno 2 (20:00 - 22:00)"]:
        chiave_auto = f"{giorno}_{t_id}"
        if chiave_auto not in st.session_state.automatico_generato:
            genera_accoppiamenti_automatici(giorno, t_id)
            st.session_state.automatico_generato.add(chiave_auto)

# --- INTERFACCIA ATLETA ---
if ruolo == "Atleta":
    st.header("👋 Area Atleti")
    st.markdown("### 🔐 Accesso Profilo Personale")
    
    # Verifica se questo telefono è già registrato a un nome
    atleta_riconosciuto = None
    for nome, token in st.session_state.dispositivi_associati.items():
        if token == id_telefono_attuale:
            atleta_riconosciuto = nome
            break
            
    if atleta_riconosciuto is not None:
        st.success(f"📱 Telefono riconosciuto ed associato a: **{atleta_riconosciuto}** (Accesso Automatico)")
        atleta_loggato = atleta_riconosciuto
    else:
        st.warning("⚠️ Questo telefono non è ancora associato a nessun atleta.")
        lista_nomi_liberi = [n for n in st.session_state.atleti["Nome"].tolist() if n not in st.session_state.dispositivi_associati]
        atleta_selezionato = st.selectbox("Seleziona il tuo Nome per registrarlo su questo smartphone:", ["-- Scegli il tuo nome --"] + lista_nomi_liberi)
        
        if atleta_selezionato != "-- Scegli il tuo nome --":
            if st.button("📌 Registra questo telefono a mio nome"):
                st.session_state.dispositivi_associati[atleta_selezionato] = id_telefono_attuale
                st.success(f"Associazione completata! Ora questo telefono è bloccato su {atleta_selezionato}.")
                st.rerun()
        atleta_loggato = None

    if atleta_loggato:
        tab_atleta1, tab_atleta2 = st.tabs(["📝 La tua Disponibilità", "🎯 Tabellone Accoppiamenti di Oggi"])
        
        with tab_atleta1:
            if orario_corrente >= ora_limite:
                st.error("⚠️ Le prenotazioni sono chiuse. È stato superato l'orario consentito. Gli accoppiamenti sono stati generati automaticamente ed è possibile visualizzarli nel pannello dedicato.")
            else:
                st.success(f"🟢 Prenotazioni aperte. Puoi inserire la tua disponibilità entro le ore {ora_limite}:00.")
                turno_scelto = st.selectbox("Seleziona il turno:", ["Turno 1 (18:00 - 20:00)", "Turno 2 (20:00 - 22:00)"], key="turno_iscriviti")
                
                if st.button("Invia Disponibilità"):
                    gia_prenotato = any(p["Nome"] == atleta_loggato and p["Giorno"] == giorno and p["Turno"] == turno_scelto for p in st.session_state.prenotazioni)
                    if gia_prenotato:
                        st.warning("Ti sei già prenotato per questo turno!")
                    else:
                        iscritti_oggi = [p for p in st.session_state.prenotazioni if p["Giorno"] == giorno and p["Turno"] == turno_scelto]
                        capienza_max = posti_turno1 if "Turno 1" in turno_scelto else posti_turno2
                        stato = "Confermato" if len(iscritti_oggi) < capienza_max else "In Lista d'Attesa"
                        
                        st.session_state.prenotazioni.append({
                            "Nome": atleta_loggato, "Giorno": giorno, "Turno": turno_scelto,
                            "Orario_Inserimento": f"{orario_corrente}:00", "Stato": stato
                        })
                        st.rerun()

            st.subheader("📋 Stato della tua prenotazione")
            prenotazioni_personali = [p for p in st.session_state.prenotazioni if p["Giorno"] == giorno and p["Nome"] == atleta_loggato]
            
            if prenotazioni_personali:
                for p in prenotazioni_personali:
                    col1, col2 = st.columns()
                    with col1:
                        if p["Stato"] == "Confermato":
                            st.info(f"🟢 **{p['Turno']}**: Stato **{p['Stato']}**")
                            confermati_totali = len([x for x in st.session_state.prenotazioni if x["Giorno"] == giorno and x["Turno"] == p["Turno"] and x["Stato"] == "Confermato"])
                            if orario_corrente >= ora_limite and confermati_totali % 2 != 0:
                                confermati_lista = [x["Nome"] for x in st.session_state.prenotazioni if x["Giorno"] == giorno and x["Turno"] == p["Turno"] and x["Stato"] == "Confermato"]
                                if confermati_lista[-1] == atleta_loggato:
                                    st.error("⚠️ Avviso: Oggi non potrai allenarti perché non hai più un compagno con cui allenarsi.")
                        elif p["Stato"] == "In Lista d'Attesa":
                            st.warning(f"🟡 **{p['Turno']}**: Stato **{p['Stato']}**")
                            if orario_corrente >= ora_limite:
                                st.error("⚠️ Avviso: In assenza del tavolo o del mancato accoppiamento non ti allenerai.")
                    with col2:
                        if st.button("Cancella", key=f"del_{p['Turno']}"):
                            st.session_state.prenotazioni.remove(p)
                            ricalcola_stati(giorno, p["Turno"])
                            if orario_corrente >= ora_limite:
                                genera_accoppiamenti_automatici(giorno, p["Turno"])
