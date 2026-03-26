from Stadion.load_stadion import set_stadion
from Versionierung import versionskontrolle
from Team.transform_team import transform_teams
from Team.extract_team import TEAM_STADIEN


def check_team_existiert(cursor, team_id):
    cursor.execute(
        "SELECT 1 FROM Teams WHERE ID = ?",
        (team_id,)
    )
    return cursor.fetchone() is not None


def set_team(cursor, team_id, team_name, stadion_name):
    stadion_id = set_stadion(cursor, stadion_name)

    cursor.execute("""
        INSERT INTO Teams (ID, Name, HeimstadionID)
        VALUES (?, ?, ?)
    """, (team_id, team_name, stadion_id))


def load_teams(cursor, url):
    data = transform_teams(url)
    inserted = False
    count = 0

    for team_id, team_name in data:
        stadion_name = TEAM_STADIEN.get(team_id)

        if stadion_name is None:
            print(f"Kein Stadion-Mapping für Team {team_name} (ID {team_id}) gefunden")
            continue

        if not check_team_existiert(cursor, team_id):
            set_team(cursor, team_id, team_name, stadion_name)
            inserted = True
            count += 1

    if inserted:
        versionskontrolle.update_tabellen_version(cursor, "Teams")

    print(f"{count} neue Teams eingefügt")