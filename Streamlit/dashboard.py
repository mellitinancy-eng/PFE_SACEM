import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.metrics import mean_squared_error

engine = create_engine(
    "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
)

st.set_page_config(
    page_title="Dashboard SACEM",
    layout="wide"
)

vente = pd.read_sql("SELECT * FROM vente", engine)
production = pd.read_sql("SELECT * FROM production", engine)
previsions_ventes = pd.read_sql("SELECT * FROM previsions_ventes", engine)
previsions_production = pd.read_sql("SELECT * FROM previsions_production", engine)
backtesting = pd.read_sql("SELECT * FROM comparatif_reel_prevu", engine)

vente["Mois"] = pd.to_datetime(vente["Mois"])
production["Mois"] = pd.to_datetime(production["Mois"])
previsions_ventes["mois"] = pd.to_datetime(previsions_ventes["mois"])
previsions_production["mois"] = pd.to_datetime(previsions_production["mois"])
backtesting["mois"] = pd.to_datetime(backtesting["mois"])

st.title("📊 Dashboard SACEM")
# ==============================
# Authentification simple
# ==============================

if "connecte" not in st.session_state:
    st.session_state["connecte"] = False

if not st.session_state["connecte"]:
    st.sidebar.title("🔐 Authentification")

    username = st.sidebar.text_input("Nom utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")

    if st.sidebar.button("Se connecter"):
        if username == "admin" and password == "sacem2026":
            st.session_state["connecte"] = True
            st.rerun()
        else:
            st.sidebar.error("Identifiants incorrects")

    st.warning("Veuillez vous connecter pour accéder à l'application.")
    st.stop()

col1, col2, col3 = st.columns(3)

col1.metric("Nombre de ventes", len(vente))
col2.metric("Quantité vendue", round(vente["Quantité"].sum(), 2))
col3.metric("Nombre de productions", len(production))

st.subheader("🎯 Filtrage dynamique")

annees = sorted(vente["Année"].dropna().unique())

annee_choisie = st.selectbox(
    "Choisir une année",
    annees
)

vente_filtre = vente[vente["Année"] == annee_choisie]

st.subheader("Top 10 Produits dynamique")

top = (
    vente_filtre.groupby("Désignation article")["Quantité"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

st.bar_chart(top)

st.subheader("Ventes par année")

ventes_annee = vente.groupby("Année")["Quantité"].sum()
st.line_chart(ventes_annee)

st.subheader("Production par année")

prod_annee = production.groupby("Année")["Quantité"].sum()
st.line_chart(prod_annee)

st.subheader("Comparatif Production VS Vente")

comparatif = pd.merge(
    vente.groupby("Année")["Quantité"].sum().reset_index(name="Ventes"),
    production.groupby("Année")["Quantité"].sum().reset_index(name="Production"),
    on="Année",
    how="outer"
).fillna(0)

comparatif["Ecart"] = comparatif["Production"] - comparatif["Ventes"]

comparatif["Taux_realisation"] = (
    comparatif["Ventes"] / comparatif["Production"]
) * 100

comparatif["Taux_realisation"] = comparatif["Taux_realisation"].replace(
    [np.inf, -np.inf],
    0
).fillna(0)

st.dataframe(comparatif)

st.line_chart(
    comparatif.set_index("Année")[["Ventes", "Production"]]
)

st.subheader("Écart Production - Vente")

st.bar_chart(
    comparatif.set_index("Année")["Ecart"]
)

st.subheader("Taux de réalisation (%)")

st.line_chart(
    comparatif.set_index("Année")["Taux_realisation"]
)

st.subheader("🤖 Performance des modèles IA")

mae_vente = backtesting["mae"].mean()

rmse_vente = np.sqrt(
    mean_squared_error(
        backtesting["reel"],
        backtesting["prevision"]
    )
)

mape_vente = (
    np.mean(
        np.abs(
            (backtesting["reel"] - backtesting["prevision"])
            / backtesting["reel"].replace(0, np.nan)
        )
    ) * 100
)

mae_production = previsions_production["mae"].mean()

c1, c2, c3, c4 = st.columns(4)

c1.metric("MAE Vente", round(mae_vente, 2))
c2.metric("RMSE Vente", round(rmse_vente, 2))
c3.metric("MAPE Vente (%)", round(mape_vente, 2))
c4.metric("MAE Production", round(mae_production, 2))

st.subheader("📈 Courbe Forecast Vente")

st.line_chart(
    previsions_ventes.set_index("mois")["prevision"]
)

st.subheader("🏭 Courbe Forecast Production")

st.line_chart(
    previsions_production.set_index("mois")["prevision"]
)

st.subheader("🔄 Backtesting Vente : Réel VS Prévu")

backtest_graph = backtesting[
    ["mois", "reel", "prevision"]
].set_index("mois")

st.line_chart(backtest_graph)

st.subheader("📉 Distribution des erreurs")

backtesting["erreur"] = backtesting["reel"] - backtesting["prevision"]

st.bar_chart(
    backtesting.set_index("mois")["erreur"]
)

st.subheader("📋 Tableau Backtesting")

st.dataframe(
    backtesting[
        [
            "mois",
            "reel",
            "prevision",
            "ecart",
            "ecart_pourcentage",
            "mae"
        ]
    ]
)

st.subheader("🔥 Heatmap des ventes mensuelles")

heatmap_data = (
    vente.groupby(["Année", vente["Mois"].dt.month])["Quantité"]
    .sum()
    .reset_index()
)

heatmap_data.columns = ["Année", "Mois", "Quantité"]

pivot_heatmap = heatmap_data.pivot(
    index="Année",
    columns="Mois",
    values="Quantité"
).fillna(0)

st.dataframe(
    pivot_heatmap.style.background_gradient(axis=None)
)

st.subheader("🚨 Alertes automatiques")

dernier_taux = comparatif["Taux_realisation"].iloc[-1]

if mae_vente > 300:
    st.error("⚠ Le modèle de vente nécessite une amélioration.")

else:
    st.success("✅ Le modèle de vente est acceptable.")

if mae_production > 1500:
    st.warning("⚠ Le modèle de production peut être amélioré.")

else:
    st.success("✅ Le modèle de production est acceptable.")

if dernier_taux < 50:
    st.warning("⚠ Faible taux de réalisation entre ventes et production.")

else:
    st.success("✅ Taux de réalisation acceptable.")

st.subheader("🧠 Analyse automatique de la performance")

if mae_vente < 100:
    st.success("Excellent modèle de prévision des ventes.")

elif mae_vente < 300:
    st.warning("Modèle de prévision des ventes acceptable mais améliorable.")

else:
    st.error("Modèle de prévision des ventes peu performant.")

if mae_production < 500:
    st.success("Excellent modèle de prévision de production.")

elif mae_production < 1500:
    st.warning("Modèle de prévision de production acceptable mais améliorable.")

else:
    st.error("Modèle de prévision de production peu performant.")

st.subheader("📥 Export des résultats")

rapport = pd.DataFrame({
    "Indicateur": [
        "MAE Vente",
        "RMSE Vente",
        "MAPE Vente",
        "MAE Production",
        "Quantité vendue totale",
        "Quantité produite totale"
    ],
    "Valeur": [
        mae_vente,
        rmse_vente,
        mape_vente,
        mae_production,
        vente["Quantité"].sum(),
        production["Quantité"].sum()
    ]
})

st.dataframe(rapport)

st.download_button(
    "Télécharger rapport CSV",
    rapport.to_csv(index=False),
    "rapport_performance_sacem.csv",
    "text/csv"
)