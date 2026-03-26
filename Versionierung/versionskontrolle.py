from datetime import datetime, date


def update_tabellen_version(cursor, table_name):
    cursor.execute("""
    INSERT INTO TabellenVersion (TabellenName, AktualisiertAm)
    VALUES (?, datetime('now', 'localtime'))
    ON CONFLICT(TabellenName)
    DO UPDATE SET AktualisiertAm=datetime('now')
    """, (table_name,))


def get_letzte_version(cursor, table_name):
    cursor.execute("""
        SELECT AktualisiertAm
        FROM TabellenVersion
        WHERE TabellenName = ?
    """, (table_name,))

    result = cursor.fetchone()

    if result is None:
        return date(2023, 8, 1)   # oder ein anderes Startdatum

    # Falls AktualisiertAm z.B. "2026-03-13 15:24:10" ist
    return datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S").date()