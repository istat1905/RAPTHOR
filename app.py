import streamlit as st
import pandas as pd
from scraper import AuchanScraper
import os

# --- Configuration de la page ---
st.set_page_config(
    page_title="RAPTHOR - Auchan OCR",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 RAPTHOR - Automatisation Auchan (OCR)")
st.markdown("---")

# --- Sidebar pour identifiants ---
with st.sidebar:
    st.header("🔐 Identifiants Auchan")
    
    username = os.getenv("auchan_username")
    password = os.getenv("auchan_password")

    if username and password:
        st.success("✅ Identifiants configurés")
    else:
        st.error("❌ Variables d'environnement manquantes sur Render")
        st.info("Configurez auchan_username et auchan_password dans Environment sur Render")

# --- Options de filtrage ---
st.header("📅 Commandes de la semaine")
st.info("📆 Semaine en cours : du 24/11/2025 au 30/11/2025")

col1, col2 = st.columns(2)
with col1:
    show_all = st.checkbox("Afficher toutes les commandes", value=True)
    show_desadv = st.checkbox("DESADV à faire uniquement", value=True)
with col2:
    show_sup_850 = st.checkbox("Montants > 850€", value=True)
    show_totaux = st.checkbox("Total par client", value=True)

st.markdown("---")

# --- Lancer le scraping ---
if st.button("🚀 Lancer le scraping"):
    
    if not username or not password:
        st.error("❌ Veuillez configurer vos identifiants dans les variables d'environnement")
    else:
        with st.spinner("🔄 Connexion et extraction en cours via OCR..."):
            scraper = AuchanScraper(username, password)
            resultats = scraper.scraper_commandes()

        if resultats["success"]:
            st.success(resultats["message"])

            # --- Onglets pour affichage ---
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Toutes les commandes",
                "📦 DESADV à faire",
                "💰 Commandes > 850€",
                "👥 Total par client"
            ])

            # --- Toutes les commandes ---
            with tab1:
                if show_all and resultats["commandes"]:
                    df = pd.DataFrame(resultats["commandes"])
                    st.dataframe(df, use_container_width=True)

                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Télécharger CSV",
                        csv,
                        "commandes_semaine.csv",
                        "text/csv"
                    )
                else:
                    st.info("Aucune commande à afficher")

            # --- DESADV ---
            with tab2:
                if show_desadv and resultats["desadv_a_faire"]:
                    df_desadv = pd.DataFrame(resultats["desadv_a_faire"])
                    st.dataframe(df_desadv, use_container_width=True)
                    st.metric("Nombre de DESADV", len(resultats["desadv_a_faire"]))
                else:
                    st.info("✅ Aucun DESADV à faire")

            # --- Commandes > 850€ ---
            with tab3:
                if show_sup_850 and resultats["commandes_sup_850"]:
                    df_850 = pd.DataFrame(resultats["commandes_sup_850"])
                    st.dataframe(df_850, use_container_width=True)
                    total = sum(cmd["montant"] for cmd in resultats["commandes_sup_850"])
                    st.metric("Montant total", f"{total:,.2f} €")
                else:
                    st.info("Aucune commande > 850€")

            # --- Totaux par client ---
            with tab4:
                if show_totaux and resultats["total_par_client"]:
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

st.markdown("---")
st.caption("🦅 RAPTHOR v1.0 - Automatisation Auchan | OCR + Streamlit")
