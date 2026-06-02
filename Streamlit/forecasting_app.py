import streamlit as st
from forecasting import generer_previsions

st.title("🤖 Plateforme de Forecasting SACEM")

st.write(
    "Cette interface permet de générer automatiquement les prévisions "
    "des ventes à partir des données stockées dans PostgreSQL."
)

forecast = generer_previsions()

st.subheader("Prévisions des 12 prochains mois")
st.dataframe(forecast[["Mois", "Prévision"]])

st.subheader("Courbe des prévisions")
st.line_chart(
    forecast.set_index("Mois")["Prévision"]
)

st.download_button(
    "Télécharger les prévisions CSV",
    forecast.to_csv(index=False),
    "forecasting_ventes.csv"
)