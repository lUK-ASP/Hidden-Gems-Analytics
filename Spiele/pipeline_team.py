import sqlite3

from Spiele.load_spiele import load_spiele



# Datenbank verbindung aufbauen
conn = sqlite3.connect("../storage_DBs/staging_spiel_daten.db")
cursor = conn.cursor()


# API-Urls
urls = [
    "https://api.openligadb.de/getmatchdata/bl1/2023",
    "https://api.openligadb.de/getmatchdata/bl1/2024",
    "https://api.openligadb.de/getmatchdata/bl1/2025"
]


# Auszuführende Methoden
load_spiele(cursor, urls)


# Datenbankverbindung schließen
conn.commit()
conn.close()