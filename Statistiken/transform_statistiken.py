import math
import os

import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_california_housing
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

import Statistiken.load_statistiken
from Statistiken import extract_statistiken
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

from Statistiken.extract_statistiken import load_Statistiken



def haversine_vec(lat1, lon1, lat2, lon2):
    R = 6371  # km

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c

def run_distance_models(df):
    df = df.copy()

    df["strength_diff"] = df["team_strength"] - df["opp_strength"]
    df["distance"] = haversine_vec(
        df["team_home_lat"],
        df["team_home_lon"],
        df["stadium_lat"],
        df["stadium_lon"]
    )
    df["distance_100km"] = (df["distance"] / 100).round(2)

    df["match_date"] = pd.to_datetime(df["match_date"])
    df["win"] = (df["goal_diff"] > 0).astype(int)

    df["restdays"] = pd.to_numeric(df["restdays"], errors="coerce")
    max_rest = df["restdays"].max()
    df["restdays"] = df["restdays"].fillna(max_rest).astype(float)

    df["long_trip"] = (df["distance_100km"] > 5).astype(int)


    # --- Modell 1: Alle Spiele ---
    model_all = smf.ols(
        "goal_diff ~ distance_100km + home + strength_diff + restdays",
        data=df
    ).fit(cov_type="HC3")

    # --- Modell 2: Nur Auswärtsspiele ---
    df_away = df[df["home"] == 0].copy()

    model_away = smf.ols(
        "goal_diff ~ distance_100km + strength_diff + restdays",
        data=df_away
    ).fit(cov_type="HC3")

    # --- Helper Funktion für Extraktion ---
    def extract_results(model):
        return {
            "params": model.params.to_dict(),
            "pvalues": model.pvalues.to_dict(),
            "std_err": model.bse.to_dict(),
            "rsquared": model.rsquared,
            "rsquared_adj": model.rsquared_adj,
            "nobs": int(model.nobs),
            "conf_int": {
                idx: {
                    "lower": row[0],
                    "upper": row[1]
                }
                for idx, row in model.conf_int().iterrows()
            }
        }

    results = {
        "all_games": extract_results(model_all),
        "away_games": extract_results(model_away)
    }

    return results

def run_marketvalue_model():
    # Daten laden
    df = extract_statistiken.get_marktwerte()

    # Nur numerische Spalten auswählen
    df_numeric = df.select_dtypes(include=['number'])

    # Konstanten-Spalten entfernen
    df_numeric = df_numeric.loc[:, df_numeric.nunique() > 1]

    # NA-Werte auffüllen oder Zeilen löschen
    df_numeric = df_numeric.fillna(0)  # alternativ: df_numeric.dropna()

    # Sicherstellen, dass alle Werte float sind
    df_numeric = df_numeric.astype(float)

    # VIF berechnen
    vif_data = pd.DataFrame()
    vif_data["feature"] = df_numeric.columns
    vif_data["VIF"] = [variance_inflation_factor(df_numeric.values, i)
                       for i in range(df_numeric.shape[1])]

    # Sortieren nach VIF absteigend
    vif_data = vif_data.sort_values(by="VIF", ascending=False).reset_index(drop=True)

    print(vif_data)

run_marketvalue_model()

