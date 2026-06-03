import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

# ==============================
# Chargement des données
# ==============================

df = pd.read_excel("donnee/dataset_propre.xlsx")

ventes = (
    df.groupby("Mois")["Quantité"]
    .sum()
    .reset_index()
)

ventes["Mois"] = pd.to_datetime(ventes["Mois"])
ventes = ventes.sort_values("Mois")

serie = ventes["Quantité"].values.reshape(-1, 1)

# ==============================
# Normalisation
# ==============================

scaler = MinMaxScaler()
serie_scaled = scaler.fit_transform(serie)

# ==============================
# Création des séquences
# ==============================

def creer_sequences(data, n_steps):
    X = []
    y = []

    for i in range(len(data) - n_steps):
        X.append(data[i:i + n_steps])
        y.append(data[i + n_steps])

    return np.array(X), np.array(y)

n_steps = 12

X, y = creer_sequences(serie_scaled, n_steps)

# ==============================
# Split train/test
# ==============================

split = int(len(X) * 0.8)

X_train = X[:split]
X_test = X[split:]

y_train = y[:split]
y_test = y[split:]

# ==============================
# Modèle LSTM
# ==============================

model = Sequential()

model.add(
    LSTM(
        64,
        activation="tanh",
        input_shape=(n_steps, 1)
    )
)

model.add(Dense(1))

model.compile(
    optimizer="adam",
    loss="mse"
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=10,
    restore_best_weights=True
)

model.fit(
    X_train,
    y_train,
    epochs=100,
    batch_size=8,
    validation_data=(X_test, y_test),
    callbacks=[early_stop],
    verbose=1
)

# ==============================
# Evaluation
# ==============================

pred_test = model.predict(X_test)

pred_test_inv = scaler.inverse_transform(pred_test)
y_test_inv = scaler.inverse_transform(y_test)

mae = mean_absolute_error(
    y_test_inv,
    pred_test_inv
)

print("MAE LSTM =", mae)

# ==============================
# Prévisions 12 mois futurs
# ==============================

last_sequence = serie_scaled[-n_steps:]
future_predictions = []

for i in range(12):

    input_seq = last_sequence.reshape(1, n_steps, 1)

    pred = model.predict(
        input_seq,
        verbose=0
    )[0][0]

    future_predictions.append(pred)

    last_sequence = np.append(
        last_sequence[1:],
        [[pred]],
        axis=0
    )

future_predictions = np.array(future_predictions).reshape(-1, 1)

future_predictions_inv = scaler.inverse_transform(
    future_predictions
)

future_dates = pd.date_range(
    start=ventes["Mois"].max() + pd.DateOffset(months=1),
    periods=12,
    freq="MS"
)

resultat = pd.DataFrame({
    "mois": future_dates,
    "prevision_lstm": future_predictions_inv.flatten()
})

print(resultat)

# ==============================
# Graphique
# ==============================

plt.figure(figsize=(12, 5))

plt.plot(
    ventes["Mois"],
    ventes["Quantité"],
    label="Ventes réelles"
)

plt.plot(
    resultat["mois"],
    resultat["prevision_lstm"],
    label="Prévision LSTM",
    marker="o"
)

plt.title("Prévision des ventes avec LSTM")
plt.xlabel("Mois")
plt.ylabel("Quantité")
plt.legend()
plt.grid(True)

plt.show()

# ==============================
# Export Excel
# ==============================

resultat.to_excel(
    "previsions_lstm_ventes.xlsx",
    index=False
)

print("Prévisions LSTM enregistrées dans previsions_lstm_ventes.xlsx")