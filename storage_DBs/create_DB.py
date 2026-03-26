import sqlite3

conn = sqlite3.connect("statistiken.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")
#
# # Tabelle Stadion
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS Stadion (
#     ID INTEGER PRIMARY KEY AUTOINCREMENT,
#     Name TEXT NOT NULL UNIQUE,
#     Longitude REAL,
#     Latitude REAL,
#     Stadionkapazitaet INTEGER
# )
# """)
#
# # Tabelle Teams
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS Teams (
#     ID INTEGER PRIMARY KEY,
#     Name TEXT NOT NULL UNIQUE,
#     HeimstadionID INTEGER NOT NULL,
#     FOREIGN KEY (HeimstadionID) REFERENCES Stadion(ID)
# )
# """)
#
# # Tabelle Spiele
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS Spiele (
#     ID INTEGER PRIMARY KEY AUTOINCREMENT,
#     Datum TEXT NOT NULL,
#     Uhrzeit TEXT NOT NULL,
#     HeimteamID INTEGER NOT NULL,
#     Heimtore INTEGER,
#     AuswaertsteamID INTEGER NOT NULL,
#     Auswaertstore INTEGER,
#     StadionID INTEGER NOT NULL,
#     FOREIGN KEY (HeimteamID) REFERENCES Teams(ID),
#     FOREIGN KEY (AuswaertsteamID) REFERENCES Teams(ID),
#     FOREIGN KEY (StadionID) REFERENCES Stadion(ID)
# )
# """)
#
cursor.execute("""
    CREATE TABLE IF NOT EXISTS PlayerStats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        saison TEXT NOT NULL,
        team TEXT NOT NULL,
        spieler TEXT NOT NULL,
        einsaetze INTEGER NOT NULL,
        startelfeinsaetze INTEGER NOT NULL,
        minuten INTEGER,
        tore INTEGER,
        vorlagen INTEGER,
        elfmetertore INTEGER,
        elfmeterversuche INTEGER,
        gelbe_karten INTEGER,
        rote_karten INTEGER
    )
""")
cursor.execute("""
    SELECT *
    FROM PlayerStats
    WHERE saison = '2025-2026' And team='dortmund'
""")
rows = cursor.fetchall()
print(rows)
conn.commit()
conn.close()
#
# print("Datenbank und Tabellen erfolgreich erstellt.")
#
