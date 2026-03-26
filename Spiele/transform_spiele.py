import pandas as pd
import requests
import extract_spiele
from datetime import datetime, date


def transform_spiele(urls, letzteVersionierung):
    rows = []

    for url in urls:
        data = extract_spiele.extract_spiele(url)

        for spiel in data:
            if not spiel.get("matchIsFinished"):
                continue

            spiel_datum = datetime.strptime(spiel["matchDateTime"].split("T")[0], "%Y-%m-%d").date()
            spiel_zeit = spiel["matchDateTime"].split("T")[1]

            if spiel_datum <= letzteVersionierung:
                continue

            results = spiel.get("matchResults", [])
            if len(results) <= 1:
                continue

            rows.append({
                "match_id": spiel.get("matchID"),
                "match_date": spiel_datum,
                "match_zeit": spiel_zeit,
                "home_team": spiel["team1"]["teamId"],
                "away_team": spiel["team2"]["teamId"],
                "home_goals": results[1]["pointsTeam1"],
                "away_goals": results[1]["pointsTeam2"],
            })

    return rows








