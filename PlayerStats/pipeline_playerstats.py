import sqlite3

from PlayerStats.load_playerstats import load_playerstats

conn = sqlite3.connect("../storage_DBs/statistiken.db")
cursor = conn.cursor()

teams = {
        "Dortmund":         "https://fbref.com/en/squads/add600ae/Dortmund-Stats",
        "Bayern":           "https://fbref.com/en/squads/054efa67/Bayern-Munich-Stats",
        "Hoffenheim":       "https://fbref.com/en/squads/033ea6b8/Hoffenheim-Stats",
        "Stuttgart":        "https://fbref.com/en/squads/598bc722/Stuttgart-Stats",
        "RB-Leipzig":       "https://fbref.com/en/squads/acbb6a5b/RB-Leipzig-Stats",
        "Leverkusen":       "https://fbref.com/en/squads/c7a9f859/Leverkusen-Stats",
        "Frankfurt":        "https://fbref.com/en/squads/f0ac8ee6/Eintracht-Frankfurt-Stats",
        "Freiburg":         "https://fbref.com/en/squads/a486e511/Freiburg-Stats",
        "Union-Berlin":     "https://fbref.com/en/squads/7a41008f/Union-Berlin-Stats",
        "Augsburg":         "https://fbref.com/en/squads/0cdc4311/Augsburg-Stats",
        "Hamburger-SV":     "https://fbref.com/en/squads/26790c6a/Hamburger-SV-Stats",
        "Monchengladbach":  "https://fbref.com/en/squads/32f3ee20/Monchengladbach-Stats",
        "Mainz":            "https://fbref.com/en/squads/a224b06a/Mainz-05-Stats",
        "Koln":             "https://fbref.com/en/squads/bc357bf7/Koln-Stats",
        "Werder-Bremen":    "https://fbref.com/en/squads/62add3bf/Werder-Bremen-Stats",
        "St-Pauli":         "https://fbref.com/en/squads/54864664/St-Pauli-Stats",
        "Wolfsburg":        "https://fbref.com/en/squads/4eaa11d7/Wolfsburg-Stats",
        "Heidenheim":       "https://fbref.com/en/squads/18d9d2a7/Heidenheim-Stats",
    }

load_playerstats(conn,cursor,teams)

# Datenbankverbindung schließen
conn.commit()
conn.close()