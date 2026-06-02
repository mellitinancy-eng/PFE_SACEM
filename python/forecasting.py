import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

engine = create_engine(
    "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
)

def generer_previsions():

    vente = pd.read_sql("SELECT * FROM vente", engine)

    data = (
        vente.groupby("Mois")["Quantité"]
        .sum()
        .reset_index()
    )

    data["Mois"] = pd.to_datetime(data["Mois"])
    data = data.sort_values("Mois")

    data["Index"] = range(len(data))
    data["Mois_num"] = data["Mois"].dt.month
    data["Annee"] = data["Mois"].dt.year

    data["Lag_1"] = data["Quantité"].shift(1)
    data["Lag_2"] = data["Quantité"].shift(2)
    data["Lag_3"] = data["Quantité"].shift(3)
    data["Moyenne_mobile_3"] = data["Quantité"].rolling(3).mean()
    data["Moyenne_mobile_6"] = data["Quantité"].rolling(6).mean()
    data["Moyenne_mobile_12"] = data["Quantité"].rolling(12).mean()

    data = data.dropna()

    features = [
        "Index",
        "Mois_num",
        "Annee",
        "Lag_1",
        "Lag_2",
        "Lag_3",
        "Moyenne_mobile_3",
        "Moyenne_mobile_6",
        "Moyenne_mobile_12"
    ]

    X = data[features]
    y = data["Quantité"]

    split = int(len(data) * 0.8)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    model = XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=3,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)

    rmse = np.sqrt(
        mean_squared_error(y_test, y_pred)
    )

    mape = (
        np.mean(
            np.abs(
                (y_test - y_pred) / y_test.replace(0, np.nan)
            )
        ) * 100
    )

    model.fit(X, y)

    dernier_mois = data["Mois"].max()
    future_rows = []
    last_values = data["Quantité"].tolist()

    # moyenne des 12 derniers mois باش ما يهبطش prediction برشة
    moyenne_recente = data["Quantité"].tail(12).mean()

    for i in range(12):

        mois_futur = dernier_mois + pd.DateOffset(months=i + 1)

        lag_1 = last_values[-1]
        lag_2 = last_values[-2]
        lag_3 = last_values[-3]

        moyenne_mobile_3 = sum(last_values[-3:]) / 3
        moyenne_mobile_6 = sum(last_values[-6:]) / 6
        moyenne_mobile_12 = sum(last_values[-12:]) / 12

        row = {
            "Mois": mois_futur,
            "Index": len(data) + i,
            "Mois_num": mois_futur.month,
            "Annee": mois_futur.year,
            "Lag_1": lag_1,
            "Lag_2": lag_2,
            "Lag_3": lag_3,
            "Moyenne_mobile_3": moyenne_mobile_3,
            "Moyenne_mobile_6": moyenne_mobile_6,
            "Moyenne_mobile_12": moyenne_mobile_12
        }

        X_future = pd.DataFrame([row])[features]

        prediction = model.predict(X_future)[0]

        # Correction باش prediction ما تهبطش تحت 60% من moyenne récente
        prediction_corrigee = max(
            prediction,
            moyenne_recente * 0.6
        )

        row["Prévision"] = prediction_corrigee
        row["MAE"] = mae
        row["RMSE"] = rmse
        row["MAPE"] = mape

        future_rows.append(row)
        last_values.append(prediction_corrigee)

    future = pd.DataFrame(future_rows)

    return future


if __name__ == "__main__":

    resultat = generer_previsions()

    print(
        resultat[
            ["Mois", "Prévision", "MAE", "RMSE", "MAPE"]
        ]
    )

    resultat[
        ["Mois", "Prévision", "MAE", "RMSE", "MAPE"]
    ].rename(
        columns={
            "Mois": "mois",
            "Prévision": "prevision",
            "MAE": "mae",
            "RMSE": "rmse",
            "MAPE": "mape"
        }
    ).to_sql(
        "previsions_ventes",
        engine,
        if_exists="replace",
        index=False
    )

    print("Prévisions ventes améliorées enregistrées dans PostgreSQL")