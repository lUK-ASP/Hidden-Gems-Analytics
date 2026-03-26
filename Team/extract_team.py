import requests

def extract_teams(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

# Mapping für die Vereine und Stadien
TEAM_STADIEN = {
    199: "Voith-Arena",                      # 1. FC Heidenheim 1846
    65: "RheinEnergieStadion",               # 1. FC Köln
    80: "Stadion An der Alten Försterei",    # 1. FC Union Berlin
    81: "MEWA Arena",                        # 1. FSV Mainz 05
    6: "BayArena",                           # Bayer 04 Leverkusen
    7: "Signal Iduna Park",                  # Borussia Dortmund
    87: "Borussia-Park",                     # Borussia Mönchengladbach
    91: "Deutsche Bank Park",                # Eintracht Frankfurt
    95: "WWK Arena",                         # FC Augsburg
    40: "Allianz Arena",                     # FC Bayern München
    98: "Millerntor-Stadion",                # FC St. Pauli
    100: "Volksparkstadion",                 # Hamburger SV
    1635: "Red Bull Arena",                  # RB Leipzig
    112: "Europa-Park Stadion",              # SC Freiburg
    134: "Weserstadion",                     # SV Werder Bremen
    175: "PreZero Arena",                    # TSG Hoffenheim
    16: "MHPArena",                          # VfB Stuttgart
    131: "Volkswagen Arena",                 # VfL Wolfsburg
    104: "Holstein-Stadion",                 # Holstein Kiel
    129: "Vonovia Ruhrstadion",              # VfL Bochum
    118: "Merck-Stadion am Böllenfalltor"    # SV Darmstadt 98
}