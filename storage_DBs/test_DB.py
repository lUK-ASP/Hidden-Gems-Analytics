import sqlite3

conn = sqlite3.connect("../storage_DBs/staging_spiel_daten.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

#
cursor.execute("SELECT * FROM Teams")
#
rows = cursor.fetchall()
#
for row in rows:
    print(dict(row))

cursor.execute("SELECT * FROM Stadion")
#
rows = cursor.fetchall()
#
for row in rows:
    print(dict(row))



conn.commit()




conn.commit()



conn.close()