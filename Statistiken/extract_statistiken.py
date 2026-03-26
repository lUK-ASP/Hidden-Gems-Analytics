import os
import json
from operator import and_

from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

# Client
def load_Statistiken():

    if os.path.exists(os.path.expanduser("~/Downloads/business-inteligence-490515-b6c96d4e150a.json")):
        client = bigquery.Client.from_service_account_json(
            os.path.expanduser("~/Downloads/business-inteligence-490515-b6c96d4e150a.json"),
            project="business-inteligence-490515"
        )
    else:
        print("test2")
        credentials_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        client = bigquery.Client(
            credentials=credentials,
            project="business-inteligence-490515"
        )

    return client

def get_reiseentfernung():
    client = load_Statistiken()

    df_final = client.query("""
            SELECT *
            FROM `business-inteligence-490515.Spieldateb.MatchView`
            WHERE match_date <= CURRENT_DATE()
            ORDER BY match_date, match_id
        """, location="EU").to_dataframe()
    return df_final

def get_tabelle(saison: int):
    client = load_Statistiken()
    """
    Lädt alle Daten einer Saison aus BigQuery.
    """
    table_name = f"Saisontabelle{saison}-{saison + 1}"  # entspricht deinem Muster

    query = f"""
        SELECT *
        FROM `business-inteligence-490515.Spieldateb.{table_name}`
    """

    df_final = client.query(query, location="EU").to_dataframe()
    return df_final

def get_marktwerte():
    client = load_Statistiken()
    df_final = client.query("""
            SELECT *
            FROM `business-inteligence-490515.View.Scouting_View`
        """, location="EU").to_dataframe()
    return df_final


def get_positionen():
    client = load_Statistiken()

    df = client.query("""
        SELECT DISTINCT position
        FROM `business-inteligence-490515.Spielerinfos.spieler`
        WHERE position IS NOT NULL
    """, location="EU").to_dataframe()

    return sorted(df["position"].tolist())




def get_team_marktwerte(team, saison):
    client = load_Statistiken()

    query = """
        SELECT 
            m.name AS team_name,
            s.spieler_saison,
            SUM(s.marktwert_eur) AS gesamt_marktwert
        FROM `business-inteligence-490515.Spielerinfos.mannschaften` m
        JOIN `business-inteligence-490515.Spielerinfos.saison` s
            ON s.vereins_id = m.mannschafts_id
        WHERE m.name = @team
          AND s.spieler_saison = @saison
        GROUP BY m.name, s.spieler_saison
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("team", "STRING", team),
            bigquery.ScalarQueryParameter("saison", "STRING", saison)
        ]
    )

    df = client.query(query, job_config=job_config).to_dataframe()
    return df


def get_spiele_mit_teamnamen():
    client = load_Statistiken()
    query = """
        SELECT
            s.ID AS match_id,
            s.Datum AS match_date,

            s.HeimteamID,
            ht.Name AS heimteam_name,

            s.AuswaertsteamID,
            away.Name AS auswaertsteam_name,

            s.Heimtore,
            s.Auswaertstore,
            s.Saison,
            s.Spieltag
        FROM `business-inteligence-490515.Spieldateb.Spiele_Extended` s

        LEFT JOIN `business-inteligence-490515.Spieldateb.Teams` ht
            ON s.HeimteamID = ht.ID

        LEFT JOIN `business-inteligence-490515.Spieldateb.Teams` away
            ON s.AuswaertsteamID = away.ID

        ORDER BY s.Datum
    """
    df = client.query(query, location="EU").to_dataframe()
    return df




def get_marktwerte_mit_teamnamen(team, saison):
    df = get_marktwerte()

    saison_str = f"{saison}-{saison + 1}"

    df_filtered = df[
        (df["team_name"].str.strip() == team) &
        (df["spieler_saison"] == saison_str)
    ]

    df2 = df_filtered.filter(items=["team_id", "team_name", "spieler_saison", "spieler_id", "vorname", "nachname", "marktwert_eur"])

    return df2

def get_spielplan_mit_elo_und_tabellenplatz():
    client = load_Statistiken()
    df_final = client.query("""
            SELECT *
            FROM `business-inteligence-490515.View.Tabellenplatz_Elo_Pro_Spieltag`
        """, location="EU").to_dataframe()
    return df_final


def get_spielerinfos(spielerID):
    client = load_Statistiken()

    query = """
        SELECT *
        FROM `business-inteligence-490515.Spielerinfos.spieler`
        WHERE spieler_id = @spieler_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("spieler_id", "INT64", spielerID)
        ]
    )

    df = client.query(query, job_config=job_config, location="EU").to_dataframe()

    return df