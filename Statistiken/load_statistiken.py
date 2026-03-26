import os
import json
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery

from Statistiken.extract_statistiken import (
    get_marktwerte,
    get_tabelle as extract_tabelle,
    get_spiele_mit_teamnamen as extract_spiele_mit_teamnamen,
    get_spielplan_mit_elo_und_tabellenplatz
)
from Statistiken.test_ml import get_underrated_players_df as _get_underrated_players_df


def load_Statistiken():
    # Versuche zuerst die lokale Datei
    creds_path = os.path.expanduser("~/Downloads/business-inteligence-490515-b6c96d4e150a.json")
    if os.path.exists(creds_path):
        return bigquery.Client.from_service_account_json(creds_path, project="business-inteligence-490515")

    # Falls nicht vorhanden, nutze Streamlit Secrets
    try:
        service_account_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_KEY"])
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        return bigquery.Client(credentials=credentials, project="business-inteligence-490515")
    except Exception as e:
        print(f"Fehler beim Laden der Credentials: {e}")
        return None


def get_tabelle(saison: int) -> pd.DataFrame:
    return extract_tabelle(saison)


def get_Teams(saison: int) -> list[str]:
    df = get_tabelle(saison)
    return sorted(df["team"].tolist())


def get_torstatistiken_pro_team(saison: int, team: str) -> dict:
    row = get_tabelle(saison).query("team == @team").iloc[0]
    return {
        "Spiele": int(row["spiele"]), "Siege": int(row["siege"]),
        "Unentschieden": int(row["unentschieden"]), "Niederlagen": int(row["niederlagen"]),
        "Tore": int(row["tore"]), "Gegentore": int(row["gegentore"]),
        "Tordifferenz": int(row["tordifferenz"]), "Punkte": int(row["punkte"])
    }


def get_spiele_mit_teamnamen() -> pd.DataFrame:
    """Wrapper für extract_statistiken Funktion"""
    return extract_spiele_mit_teamnamen()


def get_all_matches_for_team(saison: int, team: str) -> pd.DataFrame:
    df = get_spiele_mit_teamnamen()
    return df.query("(Saison == @saison) & ((heimteam_name == @team) | (auswaertsteam_name == @team))")


def get_efficiency_stats(saison: int, team: str) -> dict:
    m = get_all_matches_for_team(saison, team)
    if m.empty: return None
    total = len(m)
    gf = sum(m.apply(lambda r: r["Heimtore"] if r["heimteam_name"] == team else r["Auswaertstore"], axis=1))
    ga = sum(m.apply(lambda r: r["Auswaertstore"] if r["heimteam_name"] == team else r["Heimtore"], axis=1))
    return {"Spiele": total, "Tore": int(gf), "Gegentore": int(ga),
            "Tore/Spiel": round(gf / total, 2), "Gegentore/Spiel": round(ga / total, 2),
            "Tordiff./Spiel": round((gf / total) - (ga / total), 2)}


def _calc_stats(df, team):
    """Helper-Funktion zur Berechnung von Stats (Heim/Auswärts/Gesamt)"""
    if df.empty:
        return None

    t = len(df)
    # Tore/Gegentore
    gf = sum(df.apply(lambda r: r["Heimtore"] if r["heimteam_name"] == team else r["Auswaertstore"], axis=1))
    ga = sum(df.apply(lambda r: r["Auswaertstore"] if r["heimteam_name"] == team else r["Heimtore"], axis=1))
    # Siege, Remis
    siege = sum(
        ((df["heimteam_name"] == team) & (df["Heimtore"] > df["Auswaertstore"]))
        | ((df["auswaertsteam_name"] == team) & (df["Auswaertstore"] > df["Heimtore"]))
    )
    remis = sum(df["Heimtore"] == df["Auswaertstore"])
    # Zu-Null-Spiele
    null_heim = sum((df["heimteam_name"] == team) & (df["Auswaertstore"] == 0))
    null_aus = sum((df["auswaertsteam_name"] == team) & (df["Heimtore"] == 0))
    zu_null = null_heim + null_aus
    # Punkte
    punkte = 3 * siege + remis

    return {
        "Spiele": t,
        "Tore": int(gf),
        "Gegentore": int(ga),
        "Punkte": punkte,
        "Punkte/Spiel": round(punkte / t, 2),
        "Siegquote (%)": round(siege / t * 100, 1),
        "Zu-Null-Spiele (%)": round(zu_null / t * 100, 1),
        "Tore/Spiel": round(gf / t, 2),
        "Gegentore/Spiel": round(ga / t, 2),
        "Tordiff./Spiel": round((gf - ga) / t, 2)
    }


def get_efficiency_stats_split(saison: int, team: str) -> dict:
    m = get_all_matches_for_team(saison, team)
    if m.empty:
        return None

    return {
        "Gesamt": _calc_stats(m, team),
        "Heim": _calc_stats(m[m["heimteam_name"] == team], team),
        "Auswärts": _calc_stats(m[m["auswaertsteam_name"] == team], team)
    }


def get_team_analysis_stats_split(saison: int, team: str) -> dict:
    return get_efficiency_stats_split(saison, team)


# ============================================================================
# NEU: AGGREGIERTE STATISTIKEN FÜR MEHRERE SAISONS
# ============================================================================

def get_team_analysis_stats_split_aggregated(saisons: list[int], team: str) -> dict:
    """
    Berechnet aggregierte Statistiken über mehrere Saisons hinweg.

    Args:
        saisons: Liste von Saison-Jahren (z.B. [2023, 2024, 2025])
        team: Team-Name

    Returns:
        Dict mit Gesamt/Heim/Auswärts Stats aggregiert
    """
    all_matches = []
    for saison in saisons:
        matches = get_all_matches_for_team(saison, team)
        if not matches.empty:
            all_matches.append(matches)

    if not all_matches:
        return None

    combined_matches = pd.concat(all_matches, ignore_index=True)

    return {
        "Gesamt": _calc_stats(combined_matches, team),
        "Heim": _calc_stats(combined_matches[combined_matches["heimteam_name"] == team], team),
        "Auswärts": _calc_stats(combined_matches[combined_matches["auswaertsteam_name"] == team], team)
    }


def get_team_comparison_stats_aggregated(team1: str, team2: str, saisons: list[int]) -> tuple:
    """
    Berechnet vergleichende Statistiken für zwei Teams über mehrere Saisons.

    Args:
        team1: Erstes Team
        team2: Zweites Team
        saisons: Liste von Saison-Jahren

    Returns:
        Tuple (stats1, stats2) - aggregierte Stats für beide Teams
    """
    stats1 = get_team_analysis_stats_split_aggregated(saisons, team1)
    stats2 = get_team_analysis_stats_split_aggregated(saisons, team2)
    return stats1, stats2


def get_player_market_value_history(team: str = None) -> pd.DataFrame:
    df = get_marktwerte()

    # Entferne NaN-Werte aus spieler_saison und marktwert_eur
    df = df.dropna(subset=['spieler_saison', 'marktwert_eur'])

    df['spieler_saison'] = df['spieler_saison'].astype(str)


    if team:
        df = df[df["team_name"].str.strip() == team]
        print("Nach NaN-Filter: ", df.shape)
        print("Einzigartige Werte in spieler_saison nach Filter: ", df['spieler_saison'].unique())
        print("NaN in marktwert_eur nach Filter: ", df['marktwert_eur'].isna().sum())
        df_test = df.head(20)  # Nur die ersten 20 Zeilen testen
        print(df_test)
    result = df.sort_values(["vorname", "nachname", "spieler_saison"])[
        ["team_name", "spieler_saison", "vorname", "nachname", "position", "marktwert_eur"]]

    return result


def get_all_teams_for_players() -> list[str]:
    return sorted(get_marktwerte()["team_name"].unique())


def get_players_for_team(team: str) -> list[str]:
    df = get_marktwerte()[get_marktwerte()["team_name"].str.strip() == team]
    df["full"] = df["vorname"] + " " + df["nachname"]
    return sorted(df["full"].unique().tolist())


def get_elo_history_for_team(team: str) -> pd.DataFrame:
    df = get_spielplan_mit_elo_und_tabellenplatz()
    return df[df["team_name"].str.strip() == team].sort_values(["Saison", "Spieltag"])


def get_all_teams_for_elo() -> list[str]:
    return sorted(get_spielplan_mit_elo_und_tabellenplatz()["team_name"].unique())


def get_elo_stats_for_team(team: str) -> dict:
    df = get_elo_history_for_team(team)
    if df.empty: return None
    s = df.sort_values(["Saison", "Spieltag"])
    return {
        "elo_start": s.iloc[0]["elo"],
        "elo_current": s.iloc[-1]["elo"],
        "elo_max": s["elo"].max(),
        "elo_min": s["elo"].min(),
        "elo_change": s.iloc[-1]["elo"] - s.iloc[0]["elo"],
        "total_entries": len(s),
        "best_platz": s["platz"].min(),
        "worst_platz": s["platz"].max(),
    }


def get_reiseentfernung():
    client = load_Statistiken()
    df_final = client.query("""
                            SELECT *
                            FROM `business-inteligence-490515.Spieldateb.MatchView`
                            WHERE match_date <= CURRENT_DATE()
                            ORDER BY match_date, match_id
                            """, location="EU").to_dataframe()
    return df_final


def get_team_marktwerte(team, saison):
    client = load_Statistiken()
    query = """
            SELECT m.name               AS team_name, \
                   s.spieler_saison, \
                   SUM(s.marktwert_eur) AS gesamt_marktwert
            FROM `business-inteligence-490515.Spielerinfos.mannschaften` m
                     JOIN `business-inteligence-490515.Spielerinfos.saison` s
                          ON s.vereins_id = m.mannschafts_id
            WHERE m.name = @team
              AND s.spieler_saison = @saison
            GROUP BY m.name, s.spieler_saison \
            """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("team", "STRING", team),
            bigquery.ScalarQueryParameter("saison", "STRING", saison)
        ]
    )
    df = client.query(query, job_config=job_config).to_dataframe()
    return df


def get_marktwerte_mit_teamnamen(team, saison):
    df = get_marktwerte()
    saison_str = f"{saison}-{saison + 1}"
    df_filtered = df[
        (df["team_name"].str.strip() == team) &
        (df["spieler_saison"] == saison_str)
        ]
    df2 = df_filtered.filter(
        items=["team_id", "team_name", "spieler_saison", "spieler_id", "vorname", "nachname", "marktwert_eur"])
    return df2


def get_spielerinfos(spielerID):
    client = load_Statistiken()
    query = """
            SELECT *
            FROM `business-inteligence-490515.Spielerinfos.spieler`
            WHERE spieler_id = @spieler_id \
            """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("spieler_id", "INT64", spielerID)
        ]
    )
    df = client.query(query, job_config=job_config, location="EU").to_dataframe()
    return df


def get_positionen():
    client = load_Statistiken()
    df = client.query("""
                      SELECT DISTINCT position
                      FROM `business-inteligence-490515.Spielerinfos.spieler`
                      WHERE position IS NOT NULL
                      """, location="EU").to_dataframe()
    return sorted(df["position"].tolist())


# ML-Wrapper am Ende
def get_underrated_players(
        min_marktwert: int = 0,
        max_marktwert: int = 20_000_000,
        min_minuten_lag: int = 600,
        min_underrated_score: float = 1.15,
        min_abweichung_eur: int = 0
) -> pd.DataFrame:
    """
    Wrapper für die ML-Funktion. Fängt ZeroDivisionError und ValueError
    ab und gibt im Fehlerfall einen leeren DataFrame zurück.
    """
    try:
        df = _get_underrated_players_df(
            min_marktwert=min_marktwert,
            max_marktwert=max_marktwert,
            min_minuten_lag=min_minuten_lag,
            min_underrated_score=min_underrated_score,
            min_abweichung_eur=min_abweichung_eur
        )
        return df

    except ZeroDivisionError as e:
        print(f"ML-Fehler (ZeroDivision): {e}")
    except ValueError as e:
        print(f"ML-Fehler (ValueError): {e}")

    return pd.DataFrame(columns=[
        "spieler_id", "spieler_saison", "team_name", "vorname", "nachname",
        "position", "marktwert_eur", "pred_marktwert_eur",
        "abweichung_eur", "underrated_score", "name"
    ])


