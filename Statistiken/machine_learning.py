import numpy as np
import pandas as pd
import Statistiken.extract_statistiken
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor,
    ExtraTreesRegressor,
)
from sklearn.metrics import mean_squared_error, mean_absolute_error

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

# Falls der Query mehrfach dieselbe Spieler-Saison liefert
df = df.drop_duplicates(subset=["spieler_id", "spieler_saison"]).copy()

# --------------------------------------------------
# Jahr extrahieren
# Beispiel: "2024-2025" -> 2024
# --------------------------------------------------
df["jahr"] = pd.to_numeric(
    df["spieler_saison"].astype(str).str.extract(r"(\d{4})")[0],
    errors="coerce"
)
df = df.dropna(subset=["jahr"]).copy()
df["jahr"] = df["jahr"].astype(int)

# --------------------------------------------------
# Datentypen sauber setzen
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
# Feature Engineering aktuelle Saison
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
# Nach Spieler und Jahr sortieren
# --------------------------------------------------
df = df.sort_values(["spieler_id", "jahr"]).copy()

# --------------------------------------------------
# Lag-Features: Vorjahreswerte
# --------------------------------------------------
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

# Nur Spieler mit genug Einsatzzeit im Vorjahr
df_model = df_model[df_model["minuten_lag"] >= 600].copy()

# Nur positive Marktwerte
df_model = df_model[df_model["marktwert_eur"] > 0].copy()

# --------------------------------------------------
# Zusätzliche starke Features
# --------------------------------------------------
df_model["log_minuten_lag"] = np.log1p(df_model["minuten_lag"])
df_model["alter_sq"] = df_model["alter_lag"] ** 2
df_model["leistung_volumen"] = df_model["tore_pro_90_lag"] * df_model["minuten_lag"]

# Positionsspezifische Tore-Features
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
# team_name bewusst draußen gelassen, um Overfitting zu vermeiden
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
    "groesse",
    "position",
    "fuss",
] + [f"tore_pos_{pos.replace(' ', '_')}" for pos in positions_for_interactions]

X = df_model[feature_cols].copy()
X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
X = pd.get_dummies(X, columns=["position", "fuss"], drop_first=True)

# --------------------------------------------------
# Zeitbasierter Split
# Train: alle älteren Jahre
# Test: neuestes Jahr
# --------------------------------------------------
max_jahr = df_model["jahr"].max()
train_mask = df_model["jahr"] < max_jahr
test_mask = df_model["jahr"] == max_jahr

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]
y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

print("Train-Saisons:", sorted(df_model.loc[train_mask, "jahr"].unique()))
print("Test-Saison:", sorted(df_model.loc[test_mask, "jahr"].unique()))
print("Train Shape:", X_train.shape)
print("Test Shape:", X_test.shape)

if X_train.empty or X_test.empty:
    raise ValueError("Train oder Test ist leer. Prüfe spieler_saison, Lags und Filter.")

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
    mae_log = mean_absolute_error(y_test, y_pred_log)

    # Rücktransformation in Euro
    y_test_eur = np.expm1(y_test)
    y_pred_eur = np.expm1(y_pred_log)

    rmse_eur = np.sqrt(mean_squared_error(y_test_eur, y_pred_eur))
    mae_eur = mean_absolute_error(y_test_eur, y_pred_eur)

    results[name] = (rmse_log, model, y_pred_log, y_pred_eur)

    print(f"\n{name}")
    print("RMSE (log):", rmse_log)
    print("Fehlerfaktor:", np.exp(rmse_log))
    print("MAE (log):", mae_log)
    print("RMSE (EUR):", round(rmse_eur, 2))
    print("MAE (EUR):", round(mae_eur, 2))

# --------------------------------------------------
# Bestes Modell bestimmen
# --------------------------------------------------
best_name = min(results, key=lambda k: results[k][0])
best_rmse, best_model, best_pred_log, best_pred_eur = results[best_name]

print(f"\nBestes Modell: {best_name}")
print("Best RMSE (log):", best_rmse)
print("Bester Fehlerfaktor:", np.exp(best_rmse))

# --------------------------------------------------
# Feature Importance
# --------------------------------------------------
importance = pd.Series(best_model.feature_importances_, index=X.columns)
print("\nTop 20 Features:")
print(importance.sort_values(ascending=False).head(20))

# --------------------------------------------------
# Predictions / Over- und Undervalued Spieler
# nur auf Testdaten
# --------------------------------------------------
result_test = df_model.loc[test_mask, [
    "spieler_id",
    "spieler_saison",
    "team_name",
    "vorname",
    "nachname",
    "position",
    "marktwert_eur",
]].copy()

result_test["pred_marktwert_eur"] = best_pred_eur
result_test["abweichung_eur"] = result_test["pred_marktwert_eur"] - result_test["marktwert_eur"]
result_test["ratio_pred_to_actual"] = result_test["pred_marktwert_eur"] / result_test["marktwert_eur"]

print("\nTop 10 undervalued Spieler (Modell > echter Marktwert):")
print(
    result_test.sort_values("abweichung_eur", ascending=False)[
        [
            "vorname",
            "nachname",
            "team_name",
            "spieler_saison",
            "marktwert_eur",
            "pred_marktwert_eur",
            "abweichung_eur",
            "ratio_pred_to_actual",
        ]
    ].head(10)
)

print("\nTop 10 overvalued Spieler (Modell < echter Marktwert):")
print(
    result_test.sort_values("abweichung_eur", ascending=True)[
        [
            "vorname",
            "nachname",
            "team_name",
            "spieler_saison",
            "marktwert_eur",
            "pred_marktwert_eur",
            "abweichung_eur",
            "ratio_pred_to_actual",
        ]
    ].head(10)
)