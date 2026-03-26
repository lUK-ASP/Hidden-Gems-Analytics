import sqlite3
from Team.extract_team import extract_teams
from Team.transform_team import transform_teams
from Team.load_team import load_teams


# Statische Eingaben
season = "2024"
leagueShortcut = "bl1"
url = f"https://api.openligadb.de/getavailableteams/{leagueShortcut}/{season}"

# Datenbank verbindung aufbauen
conn = sqlite3.connect("../storage_DBs/staging_spiel_daten.db")
cursor = conn.cursor()

# Auszuführende Methoden

load_teams(cursor, url)

conn.commit()
conn.close()
