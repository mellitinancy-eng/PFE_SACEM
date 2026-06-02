import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np

# ===== Chargement du fichier =====

file_path = "Production - Copie.xlsx"

data = pd.read_excel(
    file_path,
    sheet_name="Feuil1"
)

# ===== Colonnes utiles =====

colonnes_utiles = [
    "Date comptabilisation",
    "Année",
    "Section",
    "Quantité",
    "Désignation article",
    "Code magasin",
    "Coût total (réel)",
    "Montant vente (réel)",
    "Nom Client",
    "Projet",
    "Puissance"
]

data = data[colonnes_utiles]

print(data.head())

# ===== Nettoyage =====

data = data.dropna(subset=[
    "Date comptabilisation",
    "Quantité"
])

data["Date comptabilisation"] = pd.to_datetime(
    data["Date comptabilisation"],
    errors="coerce"
)

data["Quantité"] = pd.to_numeric(
    data["Quantité"],
    errors="coerce"
)

data = data.dropna(subset=[
    "Date comptabilisation",
    "Quantité"
])

data["Quantité"] = data["Quantité"].abs()

# ===== Création Année et Mois =====

data["Année"] = data["Date comptabilisation"].dt.year

data["Mois"] = data["Date comptabilisation"].dt.to_period("M").dt.to_timestamp()

# =====================================================
# ===== Analyse de la production par année =====
# =====================================================

production_par_annee = data.groupby("Année")["Quantité"].sum()

print("\nProduction par année :")
print(production_par_annee)

plt.figure(figsize=(10, 5))

production_par_annee.plot(kind="bar")

plt.title("Evolution de la production par année")
plt.xlabel("Année")
plt.ylabel("Quantité produite")
plt.xticks(rotation=0)

plt.show()

# =====================================================
# ===== Analyse de la production par section =====
# =====================================================

production_par_section = data.groupby("Section")["Quantité"].sum().sort_values(ascending=False)

print("\nProduction par section :")
print(production_par_section)

plt.figure(figsize=(10, 5))

production_par_section.plot(kind="bar")

plt.title("Production par section")
plt.xlabel("Section")
plt.ylabel("Quantité produite")
plt.xticks(rotation=45)

plt.show()

# =====================================================
# ===== Analyse mensuelle =====
# =====================================================

production_par_mois = data.groupby("Mois")["Quantité"].sum()

print("\nProduction par mois :")
print(production_par_mois)

plt.figure(figsize=(12, 5))

plt.plot(
    production_par_mois.index,
    production_par_mois.values,
    label="Production mensuelle"
)

plt.title("Evolution mensuelle de la production")
plt.xlabel("Mois")
plt.ylabel("Quantité produite")
plt.xticks(rotation=45)
plt.legend()

plt.show()

# =====================================================
# ===== Prévision de la production =====
# =====================================================

production_par_mois = production_par_mois.reset_index()

production_par_mois["Index"] = np.arange(len(production_par_mois))

X = production_par_mois[["Index"]]
y = production_par_mois["Quantité"]

model = LinearRegression()
model.fit(X, y)

future_index = np.arange(
    len(production_par_mois),
    len(production_par_mois) + 12
).reshape(-1, 1)

future_index_df = pd.DataFrame(
    future_index,
    columns=["Index"]
)

prediction = model.predict(future_index_df)

future_months = pd.date_range(
    start=production_par_mois["Mois"].max(),
    periods=13,
    freq="ME"
)[1:]

print("\nPrévisions des 12 prochains mois :")

for mois, pred in zip(future_months, prediction):
    print(mois.strftime("%Y-%m"), ":", round(pred, 2))

plt.figure(figsize=(12, 5))

plt.plot(
    production_par_mois["Mois"],
    y,
    label="Production réelle"
)

plt.plot(
    future_months,
    prediction,
    linestyle="dashed",
    label="Prévisions"
)

plt.title("Prévision de la production")
plt.xlabel("Temps")
plt.ylabel("Quantité")
plt.legend()
plt.xticks(rotation=45)

plt.show()

# ===== Export =====

data.to_csv("production_propre.csv", index=False)
data.to_excel("production_propre.xlsx", index=False)

print("\nFichiers exportés avec succès !")