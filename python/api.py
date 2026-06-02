from fastapi import FastAPI
import pandas as pd
from sqlalchemy import create_engine

app = FastAPI(
    title="API SACEM",
    description="API pour l'analyse, la prévision et le suivi Production/Ventes",
    version="1.0"
)

engine = create_engine(
    "postgresql+psycopg2://postgres:azerty@localhost:5434/sacem_db"
)

@app.get("/")
def accueil():
    return {"message": "API SACEM fonctionne"}

@app.get("/health")
def health():
    try:
        pd.read_sql("SELECT 1", engine)
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "details": str(e)
        }

@app.get("/vente")
def get_vente():
    df = pd.read_sql("SELECT * FROM vente LIMIT 100", engine)
    return df.to_dict(orient="records")

@app.get("/production")
def get_production():
    df = pd.read_sql("SELECT * FROM production LIMIT 100", engine)
    return df.to_dict(orient="records")

@app.get("/stats/vente")
def stats_vente():
    df = pd.read_sql("SELECT * FROM vente", engine)

    return {
        "nombre_lignes": len(df),
        "quantite_totale": float(df["Quantité"].sum()),
        "cout_total": float(df["Coût total (réel)"].sum()),
        "benefice_total": float(df["Bénéfice"].sum())
    }

@app.get("/stats/production")
def stats_production():
    df = pd.read_sql("SELECT * FROM production", engine)

    return {
        "nombre_lignes": len(df),
        "quantite_totale": float(df["Quantité"].sum()),
        "cout_total": float(df["Coût total (réel)"].sum())
    }

@app.get("/top_produits")
def top_produits():
    df = pd.read_sql("SELECT * FROM vente", engine)

    top = (
        df.groupby("Désignation article")["Quantité"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    return top.to_dict()

@app.get("/ventes_par_annee")
def ventes_par_annee():
    df = pd.read_sql("SELECT * FROM vente", engine)

    resultat = (
        df.groupby("Année")["Quantité"]
        .sum()
        .sort_index()
    )

    return resultat.to_dict()

@app.get("/production_par_annee")
def production_par_annee():
    df = pd.read_sql("SELECT * FROM production", engine)

    resultat = (
        df.groupby("Année")["Quantité"]
        .sum()
        .sort_index()
    )

    return resultat.to_dict()

@app.get("/comparatif")
def comparatif():
    vente = pd.read_sql("""
        SELECT "Année",
               SUM("Quantité") as ventes
        FROM vente
        GROUP BY "Année"
        ORDER BY "Année"
    """, engine)

    production = pd.read_sql("""
        SELECT "Année",
               SUM("Quantité") as productions
        FROM production
        GROUP BY "Année"
        ORDER BY "Année"
    """, engine)

    df = pd.merge(
        vente,
        production,
        on="Année",
        how="outer"
    )

    df = df.fillna(0)
    df["ecart"] = df["productions"] - df["ventes"]

    return df.to_dict(orient="records")

@app.get("/previsions_ventes")
def previsions_ventes():
    df = pd.read_sql("SELECT * FROM previsions_ventes", engine)
    return df.to_dict(orient="records")

@app.get("/previsions_production")
def previsions_production():
    df = pd.read_sql("SELECT * FROM previsions_production", engine)
    return df.to_dict(orient="records")

@app.get("/comparatif_reel_prevu")
def comparatif_reel_prevu():
    df = pd.read_sql("SELECT * FROM comparatif_reel_prevu", engine)
    return df.to_dict(orient="records")

@app.get("/predict_ventes")
def predict_ventes():
    df = pd.read_sql("SELECT * FROM previsions_ventes ORDER BY mois", engine)

    return {
        "type": "prévision ventes",
        "horizon": "12 mois",
        "nombre_previsions": len(df),
        "previsions": df.to_dict(orient="records")
    }

@app.get("/predict_production")
def predict_production():
    df = pd.read_sql("SELECT * FROM previsions_production ORDER BY mois", engine)

    return {
        "type": "prévision production",
        "horizon": "12 mois",
        "nombre_previsions": len(df),
        "previsions": df.to_dict(orient="records")
    }