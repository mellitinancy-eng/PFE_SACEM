import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Prévision 2026-2035 SACEM", layout="wide")

st.title("📈 Prévisions Production & Ventes 2026–2035")
st.write("Outil d'aide à la décision pour estimer les quantités futures à produire et à vendre.")

annees = list(range(2026, 2036))

ventes_prevues = [5200, 4800, 6100, 5700, 6900, 6400, 7800, 7300, 8700, 8200]
production_prevue = [18000, 16500, 20500, 19500, 23000, 21500, 26000, 24500, 29000, 27500]

df = pd.DataFrame({
    "Année": annees,
    "Ventes prévues": ventes_prevues,
    "Production prévue": production_prevue
})

annee_debut, annee_fin = st.slider(
    "Choisir la période",
    2026,
    2035,
    (2026, 2035)
)

df = df[
    (df["Année"] >= annee_debut) &
    (df["Année"] <= annee_fin)
]

df["Écart Production - Vente"] = df["Production prévue"] - df["Ventes prévues"]
df["Taux de couverture"] = df["Production prévue"] / df["Ventes prévues"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total ventes prévues", f"{df['Ventes prévues'].sum():,.0f}")
col2.metric("Total production prévue", f"{df['Production prévue'].sum():,.0f}")
col3.metric("Écart total", f"{df['Écart Production - Vente'].sum():,.0f}")
col4.metric("Taux couverture moyen", f"{df['Taux de couverture'].mean():.2f}")

if df["Taux de couverture"].mean() > 2:
    st.warning("⚠ Surproduction potentielle")
elif df["Taux de couverture"].mean() < 1:
    st.error("⚠ Risque de rupture")
else:
    st.success("✅ Situation équilibrée")

st.subheader("📊 Tableau des prévisions")
st.dataframe(df, use_container_width=True)

st.subheader("📈 Évolution Production vs Ventes")

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["Année"], df["Ventes prévues"], marker="o", label="Ventes prévues")
ax.plot(df["Année"], df["Production prévue"], marker="o", label="Production prévue")
ax.set_xlabel("Année")
ax.set_ylabel("Quantité")
ax.set_title("Prévision Production vs Ventes 2026–2035")
ax.legend()
ax.grid(True)

st.pyplot(fig)

st.subheader("📉 Écart Production - Vente")

fig2, ax2 = plt.subplots(figsize=(12, 5))
ax2.bar(df["Année"], df["Écart Production - Vente"])
ax2.set_xlabel("Année")
ax2.set_ylabel("Écart")
ax2.set_title("Écart prévisionnel entre production et ventes")
ax2.grid(True)

st.pyplot(fig2)

st.subheader("🎯 Simulation What-If")

scenario = st.selectbox(
    "Choisir un scénario",
    ["Pessimiste", "Normal", "Optimiste"]
)

ajustement = st.slider("Ajustement manuel des ventes (%)", -30, 50, 0)

if scenario == "Pessimiste":
    taux = -20
elif scenario == "Optimiste":
    taux = 20
else:
    taux = 0

taux_final = taux + ajustement

df_sim = df.copy()
df_sim["Ventes simulées"] = df_sim["Ventes prévues"] * (1 + taux_final / 100)
df_sim["Écart simulé"] = df_sim["Production prévue"] - df_sim["Ventes simulées"]
df_sim["Taux couverture simulé"] = df_sim["Production prévue"] / df_sim["Ventes simulées"]

st.info(f"Scénario choisi : {scenario} | Croissance appliquée : {taux_final}%")

col5, col6, col7 = st.columns(3)
col5.metric("Ventes simulées totales", f"{df_sim['Ventes simulées'].sum():,.0f}")
col6.metric("Écart simulé total", f"{df_sim['Écart simulé'].sum():,.0f}")
col7.metric("Taux couverture simulé", f"{df_sim['Taux couverture simulé'].mean():.2f}")

if df_sim["Taux couverture simulé"].mean() > 2:
    st.warning("⚠ Le scénario indique une surproduction potentielle")
elif df_sim["Taux couverture simulé"].mean() < 1:
    st.error("⚠ Le scénario indique un risque de rupture")
else:
    st.success("✅ Le scénario reste équilibré")

st.dataframe(df_sim, use_container_width=True)

fig3, ax3 = plt.subplots(figsize=(12, 5))
ax3.plot(df_sim["Année"], df_sim["Ventes simulées"], marker="o", label="Ventes simulées")
ax3.plot(df_sim["Année"], df_sim["Production prévue"], marker="o", label="Production prévue")
ax3.set_xlabel("Année")
ax3.set_ylabel("Quantité")
ax3.set_title("Simulation Production vs Ventes")
ax3.legend()
ax3.grid(True)

st.pyplot(fig3)

st.subheader("📥 Export des résultats")

st.download_button(
    "Télécharger les résultats CSV",
    df_sim.to_csv(index=False),
    "simulation_sacem.csv",
    "text/csv"
)