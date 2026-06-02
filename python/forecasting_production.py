import pandas as pd
from sqlalchemy import create_engine
from xgboost import XGBRegressor

engine = create_engine(
    "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
)

def generer_previsions_production():

    production = pd.read_sql(
        "SELECT * FROM production",
        engine
    )

    production["Mois"] = pd.to_datetime(
        production["Mois"]
    )

    data = (
        production.groupby("Mois")["Quantité"]
        .sum()
        .reset_index()
    )

    data = data.sort_values("Mois")

    data["Index"] = range(len(data))

    X = data[["Index"]]
    y = data["Quantité"]

    model = XGBRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )

    model.fit(X, y)

    futur = pd.DataFrame({
        "Index": range(
            len(data),
            len(data) + 12
        )
    })

    predictions = model.predict(futur)

    mois_futurs = pd.date_range(
        start=data["Mois"].max(),
        periods=13,
        freq="ME"
    )[1:]

    resultat = pd.DataFrame({
        "Mois": mois_futurs,
        "Prévision": predictions
    })

    return resultat