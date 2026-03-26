import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import os
import json
from google.oauth2 import service_account
import streamlit as st  # Wichtig!

# Client initialisieren
try:
    if os.path.exists(os.path.expanduser("~/Downloads/business-inteligence-490515-b6c96d4e150a.json")):
        client = bigquery.Client.from_service_account_json(
            os.path.expanduser("~/Downloads/business-inteligence-490515-b6c96d4e150a.json"),
            project="business-inteligence-490515"
        )
    else:
        credentials_json = st.secrets["GCP_SERVICE_ACCOUNT_KEY"]  # Korrigiert!
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        client = bigquery.Client(
            credentials=credentials,
            project="business-inteligence-490515"
        )
except Exception as e:
    print(f"Fehler beim Laden der Credentials: {e}")
    client = None

# Rest des Codes...


# Letzte Aktualisierung aus Elo_Aktuell laden
try:
    elo_aktuell = client.query("""
        SELECT team_id, elo_start, gewertete_partien, letzte_aktualisierung
        FROM `business-inteligence-490515.Elo_Berechnung.Elo_Aktuell`
    """).to_dataframe()
except Exception:
    # Alte Tabelle ohne neue Spalten – nur Basis laden
    elo_aktuell = client.query("""
        SELECT team_id, elo_start
        FROM `business-inteligence-490515.Elo_Berechnung.Elo_Aktuell`
    """).to_dataframe()
    elo_aktuell["gewertete_partien"] = 0
    elo_aktuell["letzte_aktualisierung"] = None
    print("ℹ Alte Tabellenstruktur erkannt – starte mit Basis-Daten")
# Letztes Datum ermitteln
if len(elo_aktuell) > 0 and elo_aktuell["letzte_aktualisierung"].notna().any():
    letztes_datum = elo_aktuell["letzte_aktualisierung"].max()
    print(f" Letzte Aktualisierung: {letztes_datum} – lade nur neue Spiele...")
else:
    letztes_datum = None
    print(" Keine vorherige Aktualisierung gefunden – lade alle Spiele...")

# Spiele laden – nur ab letztem Datum
datum_filter = f"AND m.match_date > '{letztes_datum}'" if letztes_datum else ""

spiele = client.query(f"""
    SELECT 
        m.match_id,
        m.match_date,
        m.team          AS heim_name,
        m.opponent      AS ausw_name,
        m.goals_for     AS heim_tore,
        m.goals_against AS ausw_tore,
        ht.ID           AS heim_id,
        aw.ID           AS ausw_id,
        e.Saison,
        e.Spieltag
    FROM `business-inteligence-490515.Spieldateb.MatchView` AS m
    JOIN `business-inteligence-490515.Spieldateb.Teams` AS ht ON m.team = ht.Name
    JOIN `business-inteligence-490515.Spieldateb.Teams` AS aw ON m.opponent = aw.Name
    JOIN `business-inteligence-490515.Spieldateb.Spiele_Extended` AS e ON m.match_id = e.ID
    WHERE m.home = 1
    {datum_filter}
    ORDER BY m.match_date, m.match_id
""").to_dataframe()

if len(spiele) == 0:
    print("✓ Keine neuen Spiele gefunden – nichts zu tun!")
    exit()

print(f"✓ {len(spiele)} neue Spiele gefunden")

# Elo und gewertete Partien aus Elo_Aktuell wiederherstellen
DEFAULT_ELO = 2486.5
elo = dict(zip(elo_aktuell.team_id, elo_aktuell.elo_start))
gewertete_partien = dict(zip(elo_aktuell.team_id, elo_aktuell.gewertete_partien))

LEVERKUSEN_ID = 6

def get_k(team_id):
    partien = gewertete_partien.get(team_id, 0)
    return 32 if partien < 34 else 24

ergebnisse = []
elo_verlauf = []

for _, spiel in spiele.iterrows():
    heim_id = int(spiel["heim_id"])
    ausw_id = int(spiel["ausw_id"])

    elo_heim = elo.get(heim_id, DEFAULT_ELO)
    elo_ausw = elo.get(ausw_id, DEFAULT_ELO)

    k_heim = get_k(heim_id)
    k_ausw = get_k(ausw_id)

    elo_diff = max(-400, min(400, elo_ausw - elo_heim))
    erwartet_heim = 1 / (1 + 10 ** (elo_diff / 400))
    erwartet_ausw = 1 - erwartet_heim

    if spiel["heim_tore"] > spiel["ausw_tore"]:
        ergebnis_heim, ergebnis_ausw = 1, 0
    elif spiel["heim_tore"] == spiel["ausw_tore"]:
        ergebnis_heim, ergebnis_ausw = 0.5, 0.5
    else:
        ergebnis_heim, ergebnis_ausw = 0, 1

    neue_elo_heim = elo_heim + k_heim * (ergebnis_heim - erwartet_heim)
    neue_elo_ausw = elo_ausw + k_ausw * (ergebnis_ausw - erwartet_ausw)

    gewertete_partien[heim_id] = gewertete_partien.get(heim_id, 0) + 1
    gewertete_partien[ausw_id] = gewertete_partien.get(ausw_id, 0) + 1

    ergebnisse.append({
        "match_id":         spiel["match_id"],
        "match_date":       spiel["match_date"],
        "saison":           spiel["Saison"],
        "spieltag":         spiel["Spieltag"],
        "heim_id":          heim_id,
        "heim_name":        spiel["heim_name"],
        "elo_heim_vor":     round(elo_heim, 2),
        "elo_heim_nach":    round(neue_elo_heim, 2),
        "erwartet_heim":    round(erwartet_heim, 4),
        "ergebnis_heim":    ergebnis_heim,
        "k_heim":           k_heim,
        "partien_heim":     gewertete_partien[heim_id],
        "ausw_id":          ausw_id,
        "ausw_name":        spiel["ausw_name"],
        "elo_ausw_vor":     round(elo_ausw, 2),
        "elo_ausw_nach":    round(neue_elo_ausw, 2),
        "erwartet_ausw":    round(erwartet_ausw, 4),
        "ergebnis_ausw":    ergebnis_ausw,
        "k_ausw":           k_ausw,
        "partien_ausw":     gewertete_partien[ausw_id],
    })

    for team_id, team_name, elo_vor, elo_nach, erwartet, ergebnis, k in [
        (heim_id, spiel["heim_name"], elo_heim, neue_elo_heim, erwartet_heim, ergebnis_heim, k_heim),
        (ausw_id, spiel["ausw_name"], elo_ausw, neue_elo_ausw, erwartet_ausw, ergebnis_ausw, k_ausw),
    ]:
        elo_verlauf.append({
            "team_id":           team_id,
            "team_name":         team_name,
            "match_id":          spiel["match_id"],
            "match_date":        spiel["match_date"],
            "saison":            spiel["Saison"],
            "spieltag":          spiel["Spieltag"],
            "elo_vor":           round(elo_vor, 2),
            "elo_nach":          round(elo_nach, 2),
            "elo_veraenderung":  round(elo_nach - elo_vor, 2),
            "erwartet":          round(erwartet, 4),
            "ergebnis":          ergebnis,
            "k_faktor":          k,
            "gewertete_partien": gewertete_partien[team_id],
        })

    elo[heim_id] = neue_elo_heim
    elo[ausw_id] = neue_elo_ausw

df_elo = pd.DataFrame(ergebnisse)
df_verlauf = pd.DataFrame(elo_verlauf)
jetzt = datetime.utcnow()

print(f"\n {len(df_elo)} Spiele berechnet")

# Elo_Verlauf – neue Einträge anhängen (WRITE_APPEND statt TRUNCATE)
print("\nSpeichere Elo_Verlauf...")
job = client.load_table_from_dataframe(
    df_verlauf,
    "business-inteligence-490515.Elo_Berechnung.Elo_Verlauf",
    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
)
job.result()
print(f" Elo_Verlauf gespeichert! ({len(df_verlauf)} neue Einträge)")

# Elo_Aktuell aktualisieren mit letzte_aktualisierung
print("\nAktualisiere Elo_Aktuell...")
df_aktuell = pd.DataFrame([
    {
        "team_id":                k,
        "elo_start":              round(v, 2),
        "gewertete_partien":      gewertete_partien.get(k, 0),
        "letzte_aktualisierung":  jetzt,
    }
    for k, v in elo.items()
])

job2 = client.load_table_from_dataframe(
    df_aktuell,
    "business-inteligence-490515.Elo_Berechnung.Elo_Aktuell",
    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
)
job2.result()
print(f" Elo_Aktuell aktualisiert! ({len(df_aktuell)} Teams)")
print("\nAktuelle Elo-Werte:")
print(df_aktuell.sort_values("elo_start", ascending=False).to_string())