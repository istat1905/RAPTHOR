import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from scraper import AuchanScraper

# Configuration de la page
st.set_page_config(
    page_title="RAPTHOR - Auchan Scraper",
    page_icon="🦅",
    layout="wide"
)

# Titre
st.title("🦅 RAPTHOR - Automatisation Auchan")
st.markdown("---")

# Sidebar pour les identifiants
import os

with st.sidebar:
    st.header("🔐 Identifiants Auchan")
    
    # Utiliser les variables d'environnement de Render
    username = os.getenv("auchan_username")
    password = os.getenv("auchan_password")
    
    if username and password:
        st.success("✅ Identifiants configurés")
    else:
        st.error("❌ Variables d'environnement manquantes sur Render")

# Zone principale
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📅 Recherche de commandes")
    
    # Sélection de la date
    date_option = st.radio(
        "Choisir la date",
        ["Demain", "Date personnalisée"],
        horizontal=True
    )
    
    if date_option == "Date personnalisée":
        date_recherche = st.date_input(
            "Date de recherche",
            value=datetime.now() + timedelta(days=1)
        )
        date_str = date_recherche.strftime("%d/%m/%Y")
    else:
        demain = datetime.now() + timedelta(days=1)
        date_str = demain.strftime("%d/%m/%Y")
        st.info(f"📅 Date sélectionnée: {date_str}")

with col2:
    st.header("⚙️ Options")
    show_all = st.checkbox("Afficher toutes les commandes", value=True)
    show_desadv = st.checkbox("DESADV à faire uniquement", value=True)
    show_sup_850 = st.checkbox("Montants > 850€", value=True)

st.markdown("---")

# Bouton de lancement
if st.button("🚀 Lancer le scraping", type="primary", use_container_width=True):
    
    if not username or not password:
        st.error("❌ Veuillez saisir vos identifiants")
    else:
        with st.spinner("🔄 Connexion et extraction en cours..."):
            # Créer le scraper
            scraper = AuchanScraper(username, password)
            
            # Lancer le scraping
            resultats = scraper.scraper_commandes(date_str)
            
            # Afficher les résultats
            if resultats["success"]:
                st.success(f"✅ {resultats['message']}")
                
                # Onglets pour différentes vues
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📋 Toutes les commandes", 
                    "📦 DESADV à faire", 
                    "💰 Commandes > 850€",
                    "👥 Total par client"
                ])
                
                with tab1:
                    if show_all and resultats["commandes"]:
                        st.subheader(f"📋 {len(resultats['commandes'])} commandes trouvées")
                        df = pd.DataFrame(resultats["commandes"])
                        st.dataframe(df, use_container_width=True)
                        
                        # Bouton téléchargement
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📥 Télécharger CSV",
                            csv,
                            f"commandes_{date_str.replace('/', '-')}.csv",
                            "text/csv"
                        )
                    else:
                        st.info("Aucune commande à afficher")
                
                with tab2:
                    if show_desadv and resultats["desadv_a_faire"]:
                        st.subheader(f"📦 {len(resultats['desadv_a_faire'])} DESADV à faire")
                        df_desadv = pd.DataFrame(resultats["desadv_a_faire"])
                        st.dataframe(df_desadv, use_container_width=True)
                        
                        st.metric("Nombre de DESADV", len(resultats["desadv_a_faire"]))
                    else:
                        st.success("✅ Aucun DESADV à faire")
                
                with tab3:
                    if show_sup_850 and resultats["commandes_sup_850"]:
                        st.subheader(f"💰 {len(resultats['commandes_sup_850'])} commandes > 850€")
                        df_850 = pd.DataFrame(resultats["commandes_sup_850"])
                        st.dataframe(df_850, use_container_width=True)
                        
                        total = sum(cmd["montant"] for cmd in resultats["commandes_sup_850"])
                        st.metric("Montant total", f"{total:,.2f} €")
                    else:
                        st.info("Aucune commande > 850€")
                
                with tab4:
                    if resultats["total_par_client"]:
                        st.subheader("👥 Récapitulatif par client")
                        
                        for client, info in resultats["total_par_client"].items():
                            with st.expander(f"**{client}** - {info['nb_commandes']} commande(s)"):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Montant total", f"{info['montant_total']:,.2f} €")
                                with col_b:
                                    st.metric("Nombre de commandes", info['nb_commandes'])
                                
                                st.write("**Numéros de commandes:**")
                                st.write(", ".join(info['commandes']))
                                
                                if info['montant_total'] > 850:
                                    st.warning("⚠️ Total > 850€")
                    else:
                        st.info("Aucun client trouvé")
                        
            else:
                st.error(f"❌ {resultats['message']}")

# Footer
st.markdown("---")
st.caption("🦅 RAPTHOR v1.0 - Automatisation Auchan | Développé avec Streamlit & Playwright")
