import os
from transform_playerstats import transform_playerstats
import undetected_chromedriver as uc


def load_playerstats(conn, cursor, teams):
    cursor.execute("""
        DELETE 
        FROM PlayerStats
        WHERE saison = '2025-2026'
    """)

    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, headless=False)

    try:
        for team_name, url in teams.items():
            html_dir = os.path.join(os.path.dirname(__file__), "html_dateien")
            os.makedirs(html_dir, exist_ok=True)

            html_path = os.path.join(html_dir, f"{team_name}.html")

            try:
                df = transform_playerstats(driver, url, html_path, team_name)

                for _, row in df.iterrows():
                    values = tuple(None if v == "" else v for v in row)
                    cursor.execute("""
                        INSERT INTO PlayerStats 
                            (saison, team, spieler, einsaetze, startelfeinsaetze, 
                            minuten, tore, vorlagen, elfmetertore, 
                            elfmeterversuche, gelbe_karten, rote_karten)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, values)

                conn.commit()
                print(f"✅ {team_name} eingefügt")

            except Exception as e:
                conn.rollback()
                print(f"❌ Fehler bei {team_name}: {e}")

    finally:
        driver.quit()  # ✅ Nur einmal nach allen Teams

