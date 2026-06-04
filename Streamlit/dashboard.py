```python
import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path

st.set_page_config(
    page_title="Dashboard SACEM",
    layout="wide"
)

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


# ==============================
# Fonctions utiles
# ==============================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "donnee"


def rmse_score(y_true, y_pred):
    y_true = pd.Series(y_true).fillna(0)
    y_pred = pd.Series(y_pred).fillna(0)
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def safe_datetime(df, col):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def create_demo_data():
    mois = pd.date_range("2025-01-01", periods=12, freq="MS")

    vente_demo = pd.DataFrame({
        "Mois": mois,
        "Année": [2025] * 12,
        "Quantité": [120, 180, 150, 210, 190, 240, 260, 230, 250, 280, 300, 320],
        "Désignation article": [
            "Article A", "Article B", "Article C", "Article A",
            "Article B", "Article C", "Article A", "Article B",
            "Article C", "Article A", "Article B", "Article C"
        ]
    })

    production_demo = pd.DataFrame({
        "Mois": mois,
        "Année": [2025] * 12,
        "Quantité": [200, 220, 210, 250, 240, 270, 290, 300, 310, 330, 350, 360]
    })

    previsions_demo = pd.DataFrame({
        "mois": pd.date_range("2026-01-01", periods=12, freq="MS"),
        "prevision": [220, 250, 230, 270, 260, 290, 310, 320, 330, 350, 370, 390],
        "mae": [161.06] * 12
    })

    backtesting_demo = pd.DataFrame({
        "mois": mois,
        "reel": vente_demo["Quantité"],
        "prevision": [110, 170, 160, 200, 185, 235, 255, 240, 245, 275, 310, 315],
    })

    backtesting_demo["ecart"] = backtesting_demo["reel"] - backtesting_demo["prevision"]
    backtesting_demo["ecart_pourcentage"] = (
        backtesting_demo["ecart"] / backtesting_demo["prevision"].replace(0, np.nan)
    ) * 100
    backtesting_demo["mae"] = abs(backtesting_demo["ecart"])

    return vente_demo, production_demo, previsions_demo, previsions_demo.copy(), backtesting_demo


@st.cache_data
def load_data():
    # 1) Essai PostgreSQL local / cloud
    try:
        from sqlalchemy import create_engine

        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
        )

        engine = create_engine(DATABASE_URL)

        vente = pd.read_sql("SELECT * FROM vente", engine)
        production = pd.read_sql("SELECT * FROM production", engine)
        previsions_ventes = pd.read_sql("SELECT * FROM previsions_ventes", engine)
        previsions_production = pd.read_sql("SELECT * FROM previsions_production", engine)
        backtesting = pd.read_sql("SELECT * FROM comparatif_reel_prevu", engine)

        source = "PostgreSQL"
        return vente, production, previsions_ventes, previsions_production, backtesting, source

    except Exception:
        pass

    # 2) Essai fichiers Excel pour Streamlit Cloud
    try:
        vente = pd.read_excel(DATA_DIR / "dataset_propre.xlsx")
        production = pd.read_excel(DATA_DIR / "production_propre.xlsx")

        if (DATA_DIR / "previsions_lstm_ventes.xlsx").exists():
            previsions_ventes = pd.read_excel(DATA_DIR / "previsions_lstm_ventes.xlsx")
        else:
            previsions_ventes = pd.DataFrame()

        if "prevision_lstm" in previsions_ventes.columns:
            previsions_ventes = previsions_ventes.rename(columns={"prevision_lstm": "prevision"})

        if "mae" not in previsions_ventes.columns:
            previsions_ventes["mae"] = 161.06

        if "mois" not in previsions_ventes.columns:
            previsions_ventes["mois"] = pd.date_range("2026-01-01", periods=len(previsions_ventes), freq="MS")

        previsions_production = pd.DataFrame({
            "mois": pd.date_range("2026-01-01", periods=12, freq="MS"),
            "prevision": [0] * 12,
            "mae": [0] * 12
        })

        backtesting = pd.DataFrame({
            "mois": pd.date_range("2025-01-01", periods=12, freq="MS"),
            "reel": [0] * 12,
            "prevision": [0] * 12,
            "ecart": [0] * 12,
            "ecart_pourcentage": [0] * 12,
            "mae": [161.06] * 12
        })

        source = "Fichiers Excel"
        return vente, production, previsions_ventes, previsions_production, backtesting, source

    except Exception:
        vente, production, previsions_ventes, previsions_production, backtesting = create_demo_data()
        source = "Données de démonstration"
        return vente, production, previsions_ventes, previsions_production, backtesting, source


# ==============================
# Chargement
# ==============================

vente, production, previsions_ventes, previsions_production, backtesting, source = load_data()

# Normalisation des colonnes dates
vente = safe_datetime(vente, "Mois")
production = safe_datetime(production, "Mois")
previsions_ventes = safe_datetime(previsions_ventes, "mois")
previsions_production = safe_datetime(previsions_production, "mois")
backtesting = safe_datetime(backtesting, "mois")

# Création colonnes si absentes
if "Année" not in vente.columns and "Mois" in vente.columns:
    vente["Année"] = vente["Mois"].dt.year

if "Année" not in production.columns and "Mois" in production.columns:
    production["Année"] = production["Mois"].dt.year

if "Désignation article" not in vente.columns:
    vente["Désignation article"] = "Article non spécifié"

if "Quantité" not in vente.columns:
    vente["Quantité"] = 0

if "Quantité" not in production.columns:
    production["Quantité"] = 0

if "prevision" not in previsions_ventes.columns:
    previsions_ventes["prevision"] = 0

if "prevision" not in previsions_production.columns:
    previsions_production["prevision"] = 0

if "mae" not in previsions_production.columns:
    previsions_production["mae"] = 0


# ==============================
# Dashboard
# ==============================

st.title("📊 Dashboard SACEM")
st.caption(f"Source des données utilisée : {source}")

col1, col2, col3 = st.columns(3)

col1.metric("Nombre de ventes", len(vente))
col2.metric("Quantité vendue", round(float(vente["Quantité"].sum()), 2))
col3.metric("Nombre de productions", len(production))

st.subheader("🎯 Filtrage dynamique")

annees = sorted(vente["Année"].dropna().unique())

if len(annees) == 0:
    st.warning("Aucune année disponible dans les données.")
    st.stop()

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
    comparatif["Ventes"] / comparatif["Production"].replace(0, np.nan)
) * 100

comparatif["Taux_realisation"] = comparatif["Taux_realisation"].replace(
    [np.inf, -np.inf],
    0
).fillna(0)

st.dataframe(comparatif, use_container_width=True)

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

mae_vente = backtesting["mae"].mean() if "mae" in backtesting.columns else 0

rmse_vente = rmse_score(
    backtesting["reel"],
    backtesting["prevision"]
) if {"reel", "prevision"}.issubset(backtesting.columns) else 0

if {"reel", "prevision"}.issubset(backtesting.columns):
    mape_vente = (
        np.mean(
            np.abs(
                (backtesting["reel"] - backtesting["prevision"])
                / backtesting["reel"].replace(0, np.nan)
            )
        ) * 100
    )
else:
    mape_vente = 0

if pd.isna(mape_vente):
    mape_vente = 0

mae_production = previsions_production["mae"].mean() if "mae" in previsions_production.columns else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("MAE Vente", round(float(mae_vente), 2))
c2.metric("RMSE Vente", round(float(rmse_vente), 2))
c3.metric("MAPE Vente (%)", round(float(mape_vente), 2))
c4.metric("MAE Production", round(float(mae_production), 2))

st.subheader("📈 Courbe Forecast Vente")

if "mois" in previsions_ventes.columns:
    st.line_chart(
        previsions_ventes.set_index("mois")["prevision"]
    )
else:
    st.warning("Prévisions ventes indisponibles.")

st.subheader("🏭 Courbe Forecast Production")

if "mois" in previsions_production.columns:
    st.line_chart(
        previsions_production.set_index("mois")["prevision"]
    )
else:
    st.warning("Prévisions production indisponibles.")

st.subheader("🔄 Backtesting Vente : Réel VS Prévu")

if {"mois", "reel", "prevision"}.issubset(backtesting.columns):
    backtest_graph = backtesting[
        ["mois", "reel", "prevision"]
    ].set_index("mois")

    st.line_chart(backtest_graph)

st.subheader("📉 Distribution des erreurs")

if {"reel", "prevision", "mois"}.issubset(backtesting.columns):
    backtesting["erreur"] = backtesting["reel"] - backtesting["prevision"]

    st.bar_chart(
        backtesting.set_index("mois")["erreur"]
    )

st.subheader("📋 Tableau Backtesting")

cols_backtest = [
    col for col in [
        "mois",
        "reel",
        "prevision",
        "ecart",
        "ecart_pourcentage",
        "mae"
    ] if col in backtesting.columns
]

st.dataframe(
    backtesting[cols_backtest],
    use_container_width=True
)

st.subheader("🔥 Heatmap des ventes mensuelles")

if "Mois" in vente.columns:
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
        pivot_heatmap.style.background_gradient(axis=None),
        use_container_width=True
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

st.dataframe(rapport, use_container_width=True)

st.download_button(
    "Télécharger rapport CSV",
    rapport.to_csv(index=False),
    "rapport_performance_sacem.csv",
    "text/csv"
)
```
