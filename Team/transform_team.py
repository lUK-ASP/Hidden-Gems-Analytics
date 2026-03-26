import Team.extract_team


def transform_teams(url):
    data = Team.extract_team.extract_teams(url)
    rows = []

    for team in data:
        team_id = team.get("teamId")
        team_name = team.get("teamName")
        rows.append((team_id, team_name))

    return rows


data = [transform_teams("https://api.openligadb.de/getavailableteams/bl1/2025"), transform_teams("https://api.openligadb.de/getavailableteams/bl1/2024"),
        transform_teams("https://api.openligadb.de/getavailableteams/bl1/2023")]

for teams in data:
    for team in teams:
        print(team)