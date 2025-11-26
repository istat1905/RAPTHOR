import streamlit as st
import pandas as pd
from scraper import RapthorScraper
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Rapthor | Supply Chain",
    page_icon="🦖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ (Minimaliste & Moderne) ---
st.markdown("""
    <style>
        /* Supprimer le menu hamburger standard et le footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Titres plus fins */
        h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 300; }
        
        /* Style des métriques */
        [data-testid="stMetricValue"] { font-size: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.write("🦖 **RAPTHOR**") # Tu pourras mettre un logo.png ici
with col_title:
    st.title("Pilotage WebEDI")

# --- SIDEBAR (Contrôles) ---
with st.sidebar:
    st.header("Synchronisation")
    
    if st.button("🔄 Lancer le Scraping", type="primary"):
        with st.spinner("Connexion à Auchan @GP..."):
            scraper = RapthorScraper()
            df_new = scraper.fetch_orders()
            
            if df_new is not None:
                st.session_state['data'] = df_new
                st.session_state['last_update'] = time.strftime("%H:%M:%S")
                st.success("Données synchronisées.")
            else:
                st.error("Erreur de connexion.")

    if 'last_update' in st.session_state:
        st.caption(f"Dernière màj : {st.session_state['last_update']}")
    
    st.divider()
    st.write("Filtres globaux")
    client_filter = st.multiselect("Client", ["Auchan France", "Auchan Super"], default=[])

# --- DONNÉES (Initialisation ou récupération) ---
if 'data' not in st.session_state:
    # Données vides au démarrage
    st.info("Aucune donnée chargée. Lancez le scraping via la barre latérale.")
    df = pd.DataFrame(columns=["Numéro", "Client", "Lieu", "Date Commande", "Date Livraison", "Montant", "Statut"])
else:
    df = st.session_state['data']

# --- LOGIQUE DE TRI (À COMPLÉTER AVEC TES CRITÈRES) ---
# Simulation simple : Si statut est "Nouveau", alors DESADV à faire
df['Action Requise'] = df['Statut'].apply(lambda x: 'Générer DESADV' if x == 'Nouveau' else 'Aucune')

# --- INTERFACE PRINCIPALE ---
tab1, tab2 = st.tabs(["📥 Commandes Reçues", "📦 DESADV à Traiter"])

with tab1:
    # Indicateurs clés (KPI)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Commandes Totales", len(df))
    kpi2.metric("Montant Total", f"{df['Montant'].sum():,.2f} €")
    kpi3.metric("Nouvelles", len(df[df['Statut'] == 'Nouveau']))
    
    st.markdown("### 📋 Liste détaillée")
    
    # Configuration du tableau pour un look moderne
    st.dataframe(
        df,
        column_config={
            "Montant": st.column_config.NumberColumn(
                "Montant HT",
                format="%.2f €"
            ),
            "Statut": st.column_config.SelectboxColumn(
                "Statut Actuel",
                width="medium",
                options=["Nouveau", "Accepté", "Expédié", "Annulé"],
                required=True,
            ),
             "Action Requise": st.column_config.TextColumn(
                "Action",
                disabled=True
            ),
        },
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.markdown("### 🚀 Prêt pour expédition")
    
    # Filtre automatique : On ne montre que ce qui nécessite un DESADV
    df_todo = df[df['Action Requise'] == 'Générer DESADV']
    
    if not df_todo.empty:
        st.dataframe(df_todo, use_container_width=True, hide_index=True)
        
        st.write("---")
        col_btn, _ = st.columns([2, 5])
        with col_btn:
            if st.button("⚡ Traiter les expéditions (Batch)"):
                st.toast("Traitement des DESADV lancé...", icon="✅")
                # Ici viendra la logique d'envoi des DESADV
    else:
        st.success("Tout est à jour ! Aucun DESADV en attente.")
