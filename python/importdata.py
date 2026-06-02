import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
)

vente = pd.read_excel("dataset_propre.xlsx")
production = pd.read_excel("production_propre.xlsx")

vente.to_sql("vente", engine, if_exists="replace", index=False)
production.to_sql("production", engine, if_exists="replace", index=False)

print("Import terminé avec succès")
