import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from scraper import AuchanScraper # Assurez-vous que cette importation est correcte
import os
import time

# --- FONCTION DE CACHING POUR LE SCRAPING ---
# Utilisation de st.cache_data pour mettre en cache les résultats du scraping
# Le scraping sera relancé uniquement si les identifiants changent.
@st.cache_data(show_spinner="🔄 Connexion et extraction des données en cours...")
def run_scraper_cached(username, password):
    """Exécute le scraping et met les résultats en cache."""
    logging_placeholder = st.empty()
    try:
        # Créer et lancer le scraper
        scraper = AuchanScraper(username, password)
        resultats = scraper.scraper_commandes()
        return resultats
    except Exception as e:
        # st.error n'est pas idéal dans une fonction mise en cache. On renvoie l'erreur.
        return {"success": False, "message": f"Erreur fatale de scraping: {str(e)}", "commandes": [], "desadv_a_faire": [], "commandes_sup_850": [], "total_par_client": {}}

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
with st.sidebar:
    st.header("🔐 Identifiants Auchan")
    
    # 1. Récupérer les identifiants
    # Utiliser les secrets Streamlit (recommandé) ou variables d'environnement
    username = os.getenv("AUCHAN_USERNAME")
    password = os.getenv("AUCHAN_PASSWORD")
    
    if username and password:
        st.success("✅ Identifiants configurés (via variables d'environnement)")
        st.caption("Les variables d'environnement sont 'AUCHAN_USERNAME' et 'AUCHAN_PASSWORD'.")
    else:
        st.error("❌ Variables d'environnement (AUCHAN_USERNAME/PASSWORD) manquantes")
        st.info("Configurez AUCHAN_USERNAME et AUCHAN_PASSWORD dans Environment sur Render")

# Zone principale
st.header("📅 Commandes de la semaine")
st.info("📆 Semaine en cours : du 24/11/2025 au 30/11/2025")

# Widgets de filtrage (ces widgets ne servent plus qu'à filtrer les données déjà extraites)
col1, col2 = st.columns(2)

with col1:
    show_all = st.checkbox("Afficher toutes les commandes", value=True)
    show_desadv = st.checkbox("DESADV à faire uniquement", value=True)

with col2:
    show_sup_850 = st.checkbox("Montants > 850€", value=True)
    show_totaux = st.checkbox("Total par client", value=True)

st.markdown("---")

# Bouton de lancement
# Le bouton lance la fonction mise en cache. Si les entrées sont les mêmes, le résultat sera instantané.
if st.button("🚀 Lancer le scraping", type="primary", use_container_width=True):
    
    if not username or not password:
        st.error("❌ Veuillez configurer vos identifiants dans les variables d'environnement")
    else:
        # Lancer la fonction mise en cache (le spinner est géré par le décorateur @st.cache_data)
        resultats = run_scraper_cached(username, password)
        
        # Afficher les résultats
        if resultats["success"]:
            st.success(f"✅ {resultats['message']}")
            
            # --- Préparation des DataFrames pour les onglets ---
            df_all = pd.DataFrame(resultats["commandes"])
            
            # Application des filtres côté Streamlit
            df_desadv = pd.DataFrame(resultats["desadv_a_faire"])
            df_850 = pd.DataFrame(resultats["commandes_sup_850"])
            
            # Onglets pour différentes vues
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Toutes les commandes", 
                "📦 DESADV à faire", 
                "💰 Commandes > 850€",
                "👥 Total par client"
            ])
            
            with tab1:
                if show_all and not df_all.empty:
                    st.subheader(f"📋 {len(df_all)} commandes trouvées")
                    st.dataframe(df_all, use_container_width=True)
                    
                    # Bouton téléchargement
                    csv = df_all.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Télécharger CSV",
                        csv,
                        f"commandes_semaine_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("Aucune commande à afficher ou filtre désactivé.")
            
            with tab2:
                if show_desadv and not df_desadv.empty:
                    st.subheader(f"📦 {len(df_desadv)} DESADV à faire")
                    st.dataframe(df_desadv, use_container_width=True)
                    
                    st.metric("Nombre de DESADV", len(df_desadv))
                else:
                    st.success("✅ Aucun DESADV à faire ou filtre désactivé.")
            
            with tab3:
                if show_sup_850 and not df_850.empty:
                    st.subheader(f"💰 {len(df_850)} commandes > 850€")
                    st.dataframe(df_850, use_container_width=True)
                    
                    total = df_850["montant"].sum() if "montant" in df_850.columns else 0
                    st.metric("Montant total", f"{total:,.2f} €")
                else:
                    st.info("Aucune commande > 850€ ou filtre désactivé.")
            
            with tab4:
                if show_totaux and resultats["total_par_client"]:
                    st.subheader("👥 Récapitulatif par client")
                    
                    # Trier les totaux pour un affichage plus clair
                    sorted_clients = sorted(
                        resultats["total_par_client"].items(),
                        key=lambda item: item[1]['montant_total'],
                        reverse=True
                    )
                    
                    for client, info in sorted_clients:
                        with st.expander(f"**{client}** - {info['nb_commandes']} commande(s) - {info['montant_total']:,.2f} €"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Montant total", f"{info['montant_total']:,.2f} €")
                            with col_b:
                                st.metric("Nombre de commandes", info['nb_commandes'])
                            
                            st.write("**Numéros de commandes:**")
                            st.write(", ".join(info['commandes']))
                            
                            if info['montant_total'] > 850:
                                st.warning("⚠️ Total > 850€ pour ce client")
                else:
                    st.info("Aucun client trouvé ou filtre 'Total par client' désactivé.")
                    
        else:
            st.error(f"❌ Échec du scraping: {resultats['message']}")

# Footer
st.markdown("---")
st.caption("🦅 RAPTHOR v1.0 - Automatisation Auchan | Développé avec Streamlit & Playwright")
