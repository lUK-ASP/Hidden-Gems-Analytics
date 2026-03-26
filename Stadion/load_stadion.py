def set_stadion(cursor, stadion_name):
    cursor.execute("""
        SELECT ID FROM Stadion WHERE Name = ?
    """, (stadion_name,))

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    cursor.execute("""
        INSERT INTO Stadion (Name)
        VALUES (?)
    """, (stadion_name,))

    cursor.execute("""
        SELECT ID FROM Stadion WHERE Name = ?
    """, (stadion_name,))

    return cursor.fetchone()[0]


# Stadienmapping in der extract_team.py
