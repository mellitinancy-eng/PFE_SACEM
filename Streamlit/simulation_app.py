import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import logging

# ==============================
# Authentification simple
# ==============================

def login():
    st.sidebar.title("🔐 Authentification")

    username = st.sidebar.text_input("Nom utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")

    if st.sidebar.button("Se connecter"):
        if username == "admin" and password == "sacem2026":
            st.session_state["connecte"] = True
            st.sidebar.success("Connexion réussie")
        else:
            st.sidebar.error("Identifiants incorrects")

if "connecte" not in st.session_state:
    st.session_state["connecte"] = False

if not st.session_state["connecte"]:
    login()
    st.warning("Veuillez vous connecter pour accéder à l'application.")
    st.stop()

logging.basicConfig(
    filename="logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Application Streamlit démarrée")

engine = create_engine(
    "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
)

st.title("📈 Simulation What-If SACEM")

previsions_ventes = pd.read_sql(
    "SELECT * FROM previsions_ventes",
    engine
)

previsions_production = pd.read_sql(
    "SELECT * FROM previsions_production",
    engine
)

vente_historique = pd.read_sql(
    "SELECT SUM(\"Quantité\") AS total FROM vente",
    engine
)

production_historique = pd.read_sql(
    "SELECT SUM(\"Quantité\") AS total FROM production",
    engine
)

total_ventes_historique = float(vente_historique["total"].iloc[0])
total_production_historique = float(production_historique["total"].iloc[0])

ratio_historique = (
    total_production_historique / total_ventes_historique
)

st.subheader("🎯 Paramètres de simulation")

scenario = st.selectbox(
    "Choisir un scénario",
    [
        "Pessimiste",
        "Réaliste",
        "Optimiste"
    ]
)

if scenario == "Pessimiste":
    croissance_base = -20

elif scenario == "Réaliste":
    croissance_base = 0

else:
    croissance_base = 20

ajustement = st.slider(
    "Ajustement manuel (%)",
    -50,
    100,
    0
)

croissance = croissance_base + ajustement

st.info(
    f"""
    Scénario : {scenario}

    Croissance finale appliquée : {croissance}%
    """
)

facteur = 1 + (croissance / 100)

simulation_vente = previsions_ventes.copy()
simulation_production = previsions_production.copy()

simulation_vente["prevision_simulee"] = (
    simulation_vente["prevision"] * facteur
)

simulation_production["prevision_simulee"] = (
    simulation_production["prevision"] * facteur
)

simulation_vente["borne_basse"] = (
    simulation_vente["prevision_simulee"] * 0.9
)

simulation_vente["borne_haute"] = (
    simulation_vente["prevision_simulee"] * 1.1
)

simulation_production["borne_basse"] = (
    simulation_production["prevision_simulee"] * 0.9
)

simulation_production["borne_haute"] = (
    simulation_production["prevision_simulee"] * 1.1
)

ventes_totales = simulation_vente["prevision_simulee"].sum()
production_totale = simulation_production["prevision_simulee"].sum()
ecart_total = production_totale - ventes_totales

taux_couverture_brut = production_totale / ventes_totales

taux_couverture = (
    taux_couverture_brut / ratio_historique
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Ventes prévues", round(ventes_totales, 2))
col2.metric("🏭 Production prévue", round(production_totale, 2))
col3.metric("📊 Écart prévu", round(ecart_total, 2))
col4.metric("📦 Taux couverture ajusté", round(taux_couverture, 2))

st.caption(
    f"Taux historique Production/Vente = {ratio_historique:.2f}"
)

if taux_couverture < 0.8:
    st.error("⚠ Risque de rupture par rapport au niveau historique")

elif taux_couverture > 1.2:
    st.warning("⚠ Surproduction supérieure au niveau historique")

else:
    st.success("✅ Situation cohérente avec l’historique")

st.subheader("Simulation ventes")

st.dataframe(
    simulation_vente[
        ["mois", "prevision", "prevision_simulee"]
    ]
)

st.line_chart(
    simulation_vente.set_index("mois")[
        ["prevision", "prevision_simulee"]
    ]
)

st.subheader("Intervalle de confiance - Vente")

st.dataframe(
    simulation_vente[
        ["mois", "borne_basse", "prevision_simulee", "borne_haute"]
    ]
)

st.subheader("Simulation production")

st.dataframe(
    simulation_production[
        ["mois", "prevision", "prevision_simulee"]
    ]
)

st.line_chart(
    simulation_production.set_index("mois")[
        ["prevision", "prevision_simulee"]
    ]
)

st.subheader("Intervalle de confiance - Production")

st.dataframe(
    simulation_production[
        ["mois", "borne_basse", "prevision_simulee", "borne_haute"]
    ]
)

st.subheader("📊 Production VS Vente")

comparatif = pd.DataFrame()

min_len = min(
    len(simulation_vente),
    len(simulation_production)
)

comparatif["mois"] = simulation_vente["mois"].iloc[:min_len].values

comparatif["Ventes"] = (
    simulation_vente["prevision_simulee"]
    .iloc[:min_len]
    .values
)

comparatif["Production"] = (
    simulation_production["prevision_simulee"]
    .iloc[:min_len]
    .values
)

comparatif["Ecart"] = (
    comparatif["Production"] - comparatif["Ventes"]
)

st.dataframe(comparatif)

st.line_chart(
    comparatif.set_index("mois")[
        ["Ventes", "Production"]
    ]
)

st.subheader("🤖 Analyse automatique")

if taux_couverture < 0.8:
    st.write(
        """
        La production simulée est inférieure au niveau historique attendu.
        Cela peut indiquer un risque de rupture ou une capacité de production insuffisante.
        """
    )

elif taux_couverture > 1.2:
    st.write(
        """
        La production simulée dépasse le niveau historique attendu.
        Cela peut indiquer une surproduction potentielle ou un stock important.
        """
    )

else:
    st.write(
        """
        Le scénario simulé reste cohérent avec le comportement historique
        entre la production et les ventes.
        """
    )

csv = pd.concat(
    [
        simulation_vente.assign(type="vente"),
        simulation_production.assign(type="production")
    ],
    ignore_index=True
)

st.download_button(
    "📥 Télécharger les résultats de simulation",
    csv.to_csv(index=False),
    "simulation_what_if.csv",
    "text/csv"
)