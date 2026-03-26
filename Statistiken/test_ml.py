import numpy as np
import pandas as pd
import Statistiken.extract_statistiken
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor,
    ExtraTreesRegressor,
)
from sklearn.metrics import mean_squared_error, mean_absolute_error


def get_underrated_players_df(
    min_marktwert=0,
    max_marktwert=20_000_000,
    min_minuten_lag=600,
    min_underrated_score=1.15,
    min_abweichung_eur=0,
):
    # --------------------------------------------------
    # Daten laden
    # --------------------------------------------------
    df = Statistiken.extract_statistiken.get_marktwerte().copy()

    # --------------------------------------------------
    # Grundbereinigung
    # --------------------------------------------------
    df = df.dropna(
        subset=["spieler_id", "spieler_saison", "geburtsdatum", "marktwert_eur", "elo"]
    ).copy()

    df = df.drop_duplicates(subset=["spieler_id", "spieler_saison"]).copy()

    # --------------------------------------------------
    # Jahr extrahieren
    # --------------------------------------------------
    df["jahr"] = pd.to_numeric(
        df["spieler_saison"].astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce"
    )
    df = df.dropna(subset=["jahr"]).copy()
    df["jahr"] = df["jahr"].astype(int)

    # --------------------------------------------------
    # Datentypen
    # --------------------------------------------------
    df["geburtsdatum"] = pd.to_datetime(df["geburtsdatum"], errors="coerce")
    df = df.dropna(subset=["geburtsdatum"]).copy()

    num_cols = [
        "elo",
        "elo_diff",
        "marktwert_eur",
        "minuten",
        "groesse",
        "startelfeinsaetze",
        "einsaetze",
        "statistik_tore",
        "statistik_vorlagen",
        "gelbe_karten",
        "rote_karten",
    ]

    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --------------------------------------------------
    # Feature Engineering
    # --------------------------------------------------
    df["alter"] = df["jahr"] - df["geburtsdatum"].dt.year

    def safe_divide(a, b):
        a = pd.to_numeric(a, errors="coerce")
        b = pd.to_numeric(b, errors="coerce")
        return np.where((b.notna()) & (b != 0), a / b, np.nan)

    df["startelf_quote"] = safe_divide(df["startelfeinsaetze"], df["einsaetze"])
    df["tore_pro_90"] = safe_divide(df["statistik_tore"], df["minuten"]) * 90
    df["vorlagen_pro_90"] = safe_divide(df["statistik_vorlagen"], df["minuten"]) * 90
    df["gelbekarten_pro_90"] = safe_divide(df["gelbe_karten"], df["minuten"]) * 90
    df["rotekarten_pro_90"] = safe_divide(df["rote_karten"], df["minuten"]) * 90

    # --------------------------------------------------
    # Sortierung + Lags
    # --------------------------------------------------
    df = df.sort_values(["spieler_id", "jahr"]).copy()

    lag_cols = [
        "elo",
        "minuten",
        "startelf_quote",
        "tore_pro_90",
        "vorlagen_pro_90",
        "gelbekarten_pro_90",
        "alter",
    ]

    for col in lag_cols:
        df[f"{col}_lag"] = df.groupby("spieler_id")[col].shift(1)

    # --------------------------------------------------
    # Modell-Datensatz
    # --------------------------------------------------
    df_model = df.dropna(
        subset=[
            "marktwert_eur",
            "elo_lag",
            "minuten_lag",
            "tore_pro_90_lag",
            "vorlagen_pro_90_lag",
            "alter_lag",
        ]
    ).copy()

    df_model = df_model[df_model["minuten_lag"] >= min_minuten_lag].copy()

    df_model = df_model[
        (df_model["marktwert_eur"] > min_marktwert) &
        (df_model["marktwert_eur"] <= max_marktwert)
    ].copy()

    # --------------------------------------------------
    # Zusätzliche Features
    # --------------------------------------------------
    df_model["log_minuten_lag"] = np.log1p(df_model["minuten_lag"])
    df_model["alter_sq"] = df_model["alter_lag"] ** 2
    df_model["leistung_volumen"] = df_model["tore_pro_90_lag"] * df_model["minuten_lag"]
    df_model["age_peak_diff"] = np.abs(df_model["alter_lag"] - 26)
    df_model["team_leistung"] = df_model["elo_lag"] * df_model["tore_pro_90_lag"]

    positions_for_interactions = [
        "Mittelstürmer",
        "Offensives Mittelfeld",
        "Innenverteidiger",
        "Linker Verteidiger",
        "Rechter Verteidiger",
        "Zentrales Mittelfeld",
        "Defensives Mittelfeld",
        "Torwart",
    ]

    for pos in positions_for_interactions:
        col_name = f"tore_pos_{pos.replace(' ', '_')}"
        df_model[col_name] = np.where(
            df_model["position"].astype(str) == pos,
            df_model["tore_pro_90_lag"],
            0
        )

    # --------------------------------------------------
    # Zielvariable
    # --------------------------------------------------
    y = np.log1p(df_model["marktwert_eur"])

    # --------------------------------------------------
    # Features
    # --------------------------------------------------
    feature_cols = [
        "elo_lag",
        "minuten_lag",
        "log_minuten_lag",
        "startelf_quote_lag",
        "tore_pro_90_lag",
        "vorlagen_pro_90_lag",
        "gelbekarten_pro_90_lag",
        "alter_lag",
        "alter_sq",
        "leistung_volumen",
        "age_peak_diff",
        "team_leistung",
        "groesse",
        "position",
        "fuss",
    ] + [f"tore_pos_{pos.replace(' ', '_')}" for pos in positions_for_interactions]

    X = df_model[feature_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
    X = pd.get_dummies(X, columns=["position", "fuss"], drop_first=True)

    # --------------------------------------------------
    # Zeitbasierter Split
    # --------------------------------------------------
    max_jahr = df_model["jahr"].max()
    train_mask = df_model["jahr"] < max_jahr
    test_mask = df_model["jahr"] == max_jahr

    X_train = X.loc[train_mask]
    X_test = X.loc[test_mask]
    y_train = y.loc[train_mask]
    y_test = y.loc[test_mask]

    if X_train.empty or X_test.empty:
        raise ValueError("Train oder Test ist leer. Prüfe Filter, Lags und Saisons.")

    # --------------------------------------------------
    # Modelle vergleichen
    # --------------------------------------------------
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=800,
            max_depth=10,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1
        ),
        "ExtraTrees": ExtraTreesRegressor(
            n_estimators=800,
            max_depth=12,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=500,
            learning_rate=0.02,
            max_depth=2,
            min_samples_leaf=3,
            subsample=0.8,
            random_state=42
        ),
    }

    results = {}

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred_log = model.predict(X_test)
        rmse_log = np.sqrt(mean_squared_error(y_test, y_pred_log))
        y_pred_eur = np.expm1(y_pred_log)
        results[name] = (rmse_log, model, y_pred_eur)

    best_name = min(results, key=lambda k: results[k][0])
    best_rmse, best_model, best_pred_eur = results[best_name]

    # --------------------------------------------------
    # Ergebnis-DF
    # --------------------------------------------------
    result_test = df_model.loc[test_mask, [
        "spieler_id",
        "spieler_saison",
        "team_name",
        "vorname",
        "nachname",
        "position",
        "marktwert_eur",
        "alter_lag",
        "elo_lag",
        "minuten_lag",
        "tore_pro_90_lag",
        "vorlagen_pro_90_lag",
    ]].copy()

    result_test["pred_marktwert_eur"] = best_pred_eur
    result_test["abweichung_eur"] = result_test["pred_marktwert_eur"] - result_test["marktwert_eur"]
    result_test["underrated_score"] = result_test["pred_marktwert_eur"] / result_test["marktwert_eur"]
    result_test["modell"] = best_name
    result_test["rmse_log"] = best_rmse

    result_test["name"] = (
        result_test["vorname"].fillna("").astype(str).str.strip()
        + " "
        + result_test["nachname"].fillna("").astype(str).str.strip()
    ).str.strip()

    # --------------------------------------------------
    # Nur underrated Spieler zurückgeben
    # --------------------------------------------------
    underrated_df = result_test[
        (result_test["abweichung_eur"] >= min_abweichung_eur) &
        (result_test["underrated_score"] >= min_underrated_score)
    ].copy()

    underrated_df = underrated_df.sort_values(
        ["underrated_score", "abweichung_eur"],
        ascending=False
    ).reset_index(drop=True)

    return underrated_df


