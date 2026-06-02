import streamlit as st
from forecasting_production import generer_previsions_production

st.title("🏭 Forecasting Production SACEM")

previsions = generer_previsions_production()

st.dataframe(previsions)

st.line_chart(
    previsions.set_index("Mois")["Prévision"]
)

csv = previsions.to_csv(index=False)

st.download_button(
    "Télécharger CSV",
    csv,
    "forecast_production.csv",
    "text/csv"
)