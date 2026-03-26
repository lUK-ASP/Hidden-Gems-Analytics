from Spiele.transform_spiele import transform_spiele
from Versionierung import versionskontrolle


def load_spiele(cursor, urls):
    last_version = versionskontrolle.get_letzte_version(cursor, "Spiele")
    spiele_rows = transform_spiele(urls, last_version)

    inserted = False

    for spiel in spiele_rows:

        cursor.execute("""
            SELECT HeimstadionID
            FROM Teams
            WHERE ID = ?
        """, (spiel["home_team"],))

        result = cursor.fetchone()

        if result is None:
            print(f"Team {spiel['home_team']} nicht gefunden")
            continue

        stadion_id = result[0]

        cursor.execute("""
            INSERT OR IGNORE INTO Spiele (
                ID,
                Datum,
                Uhrzeit,
                HeimteamID,
                Heimtore,
                AuswaertsteamID,
                Auswaertstore,
                StadionID
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            spiel["match_id"],
            spiel["match_date"].isoformat(),
            spiel["match_zeit"],
            spiel["home_team"],
            spiel["home_goals"],
            spiel["away_team"],
            spiel["away_goals"],
            stadion_id
        ))

        # Wenn wirklich eingefügt wurde
        if cursor.rowcount > 0:
            inserted = True

    if inserted:
        versionskontrolle.update_tabellen_version(cursor, "Spiele")