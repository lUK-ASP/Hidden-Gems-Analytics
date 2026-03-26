import pandas as pd

# ============================================================================
# GLOBALE KONSTANTEN UND FUNKTIONEN
# ============================================================================

SAISON_OPTIONS = {
    "2023/24": 2023,
    "2024/25": 2024,
    "2025/26": 2025
}

METRIKEN_LISTE = [
    "Spiele", "Tore", "Gegentore", "Punkte",
    "Siegquote (%)", "Zu-Null-Spiele (%)",
    "Tore/Spiel", "Gegentore/Spiel", "Tordiff./Spiel"
]

def create_analysis_table(analysis_data, location_key):
    """Erstellt einheitliche Analyse-Tabelle für Heim/Auswärts/Gesamt."""
    return pd.DataFrame({
        "Metrik": METRIKEN_LISTE,
        "Wert": [
            analysis_data[location_key]["Spiele"],
            analysis_data[location_key]["Tore"],
            analysis_data[location_key]["Gegentore"],
            analysis_data[location_key]["Punkte"],
            analysis_data[location_key]["Siegquote (%)"],
            analysis_data[location_key]["Zu-Null-Spiele (%)"],
            analysis_data[location_key]["Tore/Spiel"],
            analysis_data[location_key]["Gegentore/Spiel"],
            analysis_data[location_key]["Tordiff./Spiel"]
        ]
    })



def create_comparison_table(stats1, stats2, team1, team2, location_key):
    """Erstellt Vergleich-Tabelle für zwei Teams."""
    return pd.DataFrame({
        "Metrik": METRIKEN_LISTE,
        team1: [
            stats1[location_key]["Spiele"],
            stats1[location_key]["Tore"],
            stats1[location_key]["Gegentore"],
            stats1[location_key]["Punkte"],
            stats1[location_key]["Siegquote (%)"],
            stats1[location_key]["Zu-Null-Spiele (%)"],
            stats1[location_key]["Tore/Spiel"],
            stats1[location_key]["Gegentore/Spiel"],
            stats1[location_key]["Tordiff./Spiel"]
        ],
        team2: [
            stats2[location_key]["Spiele"],
            stats2[location_key]["Tore"],
            stats2[location_key]["Gegentore"],
            stats2[location_key]["Punkte"],
            stats2[location_key]["Siegquote (%)"],
            stats2[location_key]["Zu-Null-Spiele (%)"],
            stats2[location_key]["Tore/Spiel"],
            stats2[location_key]["Gegentore/Spiel"],
            stats2[location_key]["Tordiff./Spiel"]
        ]
    })

