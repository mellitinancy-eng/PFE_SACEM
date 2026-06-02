import pandas as pd
from sqlalchemy import create_engine
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

engine = create_engine(
    "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
)

def generer_backtesting():

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
    data["Lag_3"] = data["Quantité"].shift(3)
    data["Moyenne_mobile_3"] = data["Quantité"].rolling(3).mean()

    data = data.dropna()

    features = [
        "Index",
        "Mois_num",
        "Annee",
        "Lag_1",
        "Lag_3",
        "Moyenne_mobile_3"
    ]

    train = data.iloc[:-12]
    test = data.iloc[-12:]

    X_train = train[features]
    y_train = train["Quantité"]

    X_test = test[features]
    y_test = test["Quantité"]

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    resultat = pd.DataFrame({
        "mois": test["Mois"].values,
        "reel": y_test.values,
        "prevision": predictions
    })

    resultat["ecart"] = resultat["reel"] - resultat["prevision"]

    resultat["ecart_pourcentage"] = (
        resultat["ecart"] / resultat["reel"]
    ) * 100

    mae = mean_absolute_error(
        resultat["reel"],
        resultat["prevision"]
    )

    resultat["mae"] = mae

    resultat = resultat.fillna(0)

    return resultat


if __name__ == "__main__":

    resultat = generer_backtesting()

    print(resultat)

    resultat.to_sql(
        "comparatif_reel_prevu",
        engine,
        if_exists="replace",
        index=False
    )

    print("Backtesting réel/prévu enregistré dans PostgreSQL")