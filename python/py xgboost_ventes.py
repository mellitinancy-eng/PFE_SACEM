import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt

df = pd.read_excel("donnee/dataset_propre.xlsx")

# Agrégation mensuelle
ventes = (
    df.groupby("Mois")["Quantité"]
    .sum()
    .reset_index()
)

ventes["Mois"] = pd.to_datetime(ventes["Mois"])

# Variables temporelles
ventes["annee"] = ventes["Mois"].dt.year
ventes["mois_num"] = ventes["Mois"].dt.month

X = ventes[["annee", "mois_num"]]
y = ventes["Quantité"]

# Modèle XGBoost
model = XGBRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    random_state=42
)

model.fit(X, y)

# Prévisions 2026
future = pd.DataFrame({
    "annee": [2026]*12,
    "mois_num": list(range(1,13))
})

future["prediction"] = model.predict(future)

print(future)

# Graphe
plt.figure(figsize=(12,5))

plt.plot(
    ventes["Mois"],
    ventes["Quantité"],
    label="Réel"
)

future_dates = pd.date_range(
    "2026-01-01",
    periods=12,
    freq="MS"
)

plt.plot(
    future_dates,
    future["prediction"],
    label="Prévision XGBoost"
)

plt.legend()
plt.grid()
plt.show()

mae = mean_absolute_error(
    y,
    model.predict(X)
)

print("MAE =", mae)