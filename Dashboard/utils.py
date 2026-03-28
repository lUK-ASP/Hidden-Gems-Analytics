import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Tuple

import streamlit as st


# ============================================================================
# CACHING-WRAPPER FÜR HÄUFIG GENUTZTE FUNKTIONEN
# ============================================================================

@st.cache_data(ttl=3600)
def cached_get_tabelle(saison):
    from Statistiken.load_statistiken import get_tabelle
    return get_tabelle(saison)


@st.cache_data(ttl=3600)
def cached_get_team_analysis(saison, team):
    from Statistiken.load_statistiken import get_team_analysis_stats_split
    return get_team_analysis_stats_split(saison, team)


@st.cache_data(ttl=3600)
def cached_get_elo_history(team):
    from Statistiken.load_statistiken import get_elo_history_for_team
    return get_elo_history_for_team(team)


@st.cache_data(ttl=3600)
def cached_get_spiele():
    from Statistiken.load_statistiken import get_spiele_mit_teamnamen
    return get_spiele_mit_teamnamen()


@st.cache_data(ttl=3600)
def cached_get_elo_stats(team):
    from Statistiken.load_statistiken import get_elo_stats_for_team
    return get_elo_stats_for_team(team)

@st.cache_data(ttl=3600)
def cached_get_all_teams_for_players():
    from Statistiken.load_statistiken import get_all_teams_for_players
    return get_all_teams_for_players()

@st.cache_data(ttl=3600)
def cached_get_players_for_team(team):
    from Statistiken.load_statistiken import get_players_for_team
    return get_players_for_team(team)

@st.cache_data(ttl=3600)
def cached_get_player_market_value_history(team):
    from Statistiken.load_statistiken import get_player_market_value_history
    return get_player_market_value_history(team)

@st.cache_data(ttl=3600)
def cached_get_positionen():
    from Statistiken.load_statistiken import get_positionen
    return get_positionen()

@st.cache_data(ttl=3600)
def cached_get_underrated_players(min_marktwert, max_marktwert, min_minuten_lag,
                                   min_underrated_score, min_abweichung_eur):
    from Statistiken.load_statistiken import get_underrated_players
    return get_underrated_players(
        min_marktwert=min_marktwert,
        max_marktwert=max_marktwert,
        min_minuten_lag=min_minuten_lag,
        min_underrated_score=min_underrated_score,
        min_abweichung_eur=min_abweichung_eur
    )

@st.cache_data(ttl=3600)
def cached_get_marktwerte():
    from Statistiken.extract_statistiken import get_marktwerte
    return get_marktwerte()



# ============================================================================
# GLOBALE KONSTANTEN UND KONFIGURATIONEN
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

COLORS = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "warning": "#ff7f0e",
    "info": "#1f77b4",
    "grid": "rgba(200, 200, 200, 0.2)",
}

DATAFRAME_HEADER_HEIGHT = 30
DATAFRAME_ROW_HEIGHT = 35

CHART_HEIGHT_SMALL = 350
CHART_HEIGHT_MEDIUM = 400
CHART_HEIGHT_LARGE = 450

TABS = [
    ("Tabelle", "Tabelle"),
    ("Spielplan", "Spielplan"),
    ("Team-Analyse", "Team-Analyse"),
    ("Team-Vergleich", "Team-Vergleiche"),
    ("Marktwert", "Spieler-Marktwert"),
    ("Scouting", "Spieler-Scouting")
]

COMPARISON_COLORS = {
    "team1": "#1f77b4",
    "team2": "#ff7f0e",
    "tore": "#2ca02c",
    "gegentore": "#d62728",
    "siegquote": "#2ca02c",
    "zu_null": "#1f77b4"
}


# ============================================================================
# HILFSFUNKTIONEN FÜR TABELLEN
# ============================================================================

def _extract_metrics_from_analysis(analysis_data: Dict[str, Any], location_key: str) -> List:
    """Extrahiert Metrik-Werte aus Analysedaten."""
    loc_data = analysis_data[location_key]
    return [
        loc_data["Spiele"],
        loc_data["Tore"],
        loc_data["Gegentore"],
        loc_data["Punkte"],
        loc_data["Siegquote (%)"],
        loc_data["Zu-Null-Spiele (%)"],
        loc_data["Tore/Spiel"],
        loc_data["Gegentore/Spiel"],
        loc_data["Tordiff./Spiel"]
    ]


def create_analysis_table(analysis_data: Dict[str, Any], location_key: str) -> pd.DataFrame:
    """Erstellt einheitliche Analyse-Tabelle für Heim/Auswärts/Gesamt."""
    return pd.DataFrame({
        "Metrik": METRIKEN_LISTE,
        "Wert": _extract_metrics_from_analysis(analysis_data, location_key)
    })


def create_comparison_table(stats1: Dict[str, Any], stats2: Dict[str, Any],
                            team1: str, team2: str, location_key: str) -> pd.DataFrame:
    """Erstellt Vergleich-Tabelle für zwei Teams."""
    return pd.DataFrame({
        "Metrik": METRIKEN_LISTE,
        team1: _extract_metrics_from_analysis(stats1, location_key),
        team2: _extract_metrics_from_analysis(stats2, location_key)
    })


# ============================================================================
# HILFSFUNKTIONEN FÜR FORMATIERUNG
# ============================================================================

def add_saison_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Fügt Saison-Labels im Format XX/YY hinzu."""
    df["Saison_Label"] = (
            df["Saison"].astype(str) + "/" +
            (df["Saison"] + 1).astype(str).str[-2:]
    )
    return df


def add_spieltag_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Fügt Spieltag-Labels hinzu."""
    df["Spieltag_Label"] = df["Spieltag"].astype(str)
    return df


def calculate_dataframe_height(num_rows: int, header_height: int = DATAFRAME_HEADER_HEIGHT,
                               row_height: int = DATAFRAME_ROW_HEIGHT) -> int:
    """Berechnet die optimale Höhe für einen DataFrame."""
    return header_height + (num_rows * row_height)


def format_currency(value: float) -> str:
    """Formatiert Wert als Währung (€)."""
    if pd.isna(value):
        return "-"
    return f"{int(value):,}".replace(",", ".")


def format_percentage(value: float, decimals: int = 1) -> str:
    """Formatiert Wert als Prozentsatz."""
    if pd.isna(value):
        return "-"
    return f"{value:.{decimals}f}%".replace(".", ",")


def format_decimal(value: float, decimals: int = 2) -> str:
    """Formatiert Dezimalwert."""
    if pd.isna(value):
        return "-"
    return f"{value:.{decimals}f}".replace(".", ",")


# ============================================================================
# HILFSFUNKTIONEN FÜR CHARTS
# ============================================================================

def get_chart_color(metric_name: str, is_positive: bool = True) -> str:
    """Gibt Farbe basierend auf Metrik-Typ zurück."""
    if "Gegentore" in metric_name or "Niederlagen" in metric_name:
        return COLORS["danger"]
    elif "Tore" in metric_name or "Punkte" in metric_name or "Siegquote" in metric_name:
        return COLORS["success"]
    else:
        return COLORS["primary"]


def calculate_chart_height(data_points: int) -> int:
    """Berechnet optimale Chart-Höhe basierend auf Datenpunkten."""
    if data_points < 10:
        return CHART_HEIGHT_SMALL
    elif data_points < 30:
        return CHART_HEIGHT_MEDIUM
    else:
        return CHART_HEIGHT_LARGE


def calculate_tick_values(df: pd.DataFrame, target_ticks: int = 15) -> Tuple[List, List]:
    """Berechnet optimale Tick-Werte für x-Achse."""
    tick_step = max(1, len(df) // target_ticks)
    tickvals = df["Index"].iloc[::tick_step].tolist() if "Index" in df.columns else []

    if not tickvals and "Spieltag_Label" in df.columns:
        tickvals = df.index[::tick_step].tolist()
        ticktext = df["Spieltag_Label"].iloc[::tick_step].tolist()
    else:
        ticktext = df["Spieltag_Label"].iloc[::tick_step].tolist() if "Spieltag_Label" in df.columns else []

    return tickvals, ticktext


# ============================================================================
# HILFSFUNKTIONEN FÜR DATENAUFBEREITUNG
# ============================================================================

def prepare_elo_data(df: pd.DataFrame, team_name: str = None) -> pd.DataFrame:
    """Bereitet Elo-Daten für Visualisierung vor."""
    df = df.copy()
    df = df.sort_values(["Saison", "Spieltag"]).reset_index(drop=True)
    df = add_saison_labels(df)
    df = add_spieltag_labels(df)
    df["Index"] = range(len(df))
    if team_name:
        df["Team"] = team_name
    return df


def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, on_columns: List[str] = None) -> Dict[str, Any]:
    """Vergleicht zwei DataFrames und gibt Statistiken zurück."""
    return {
        "df1_rows": len(df1),
        "df2_rows": len(df2),
        "df1_columns": df1.columns.tolist(),
        "df2_columns": df2.columns.tolist(),
        "rows_diff": len(df1) - len(df2),
        "matching_columns": list(set(df1.columns) & set(df2.columns))
    }


def prepare_comparison_elo_data(df: pd.DataFrame, min_saison: int = None) -> pd.DataFrame:
    """Bereitet Elo-Daten für Team-Vergleiche vor mit gemeinsamem Index."""
    df = df.copy()
    df = df.sort_values(["Saison", "Spieltag"]).reset_index(drop=True)
    if min_saison is None:
        min_saison = df["Saison"].min()
    df["Index"] = (df["Saison"] - min_saison) * 100 + df["Spieltag"]
    df["Saison_Label"] = df["Saison"].astype(str) + "/" + (df["Saison"] + 1).astype(str).str[-2:]
    df["Spieltag_Label"] = df["Spieltag"].astype(str)
    return df


def create_elo_comparison_figure(df_elo1: pd.DataFrame, df_elo2: pd.DataFrame,
                                 team1: str, team2: str, saison_labels: List[str]) -> go.Figure:
    """Erstellt Elo-Vergleichs-Chart für zwei Teams mit Tabellenplatz in Hover-Box."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_elo1["Index"], y=df_elo1["elo"], mode='lines+markers', name=team1,
        connectgaps=False,
        customdata=df_elo1[["Saison_Label", "Spieltag_Label", "platz"]].values,
        hovertemplate=f'<b>{team1}</b><br>Saison: %{{customdata[0]}}<br>Spieltag: %{{customdata[1]}}<br>Elo: %{{y:.2f}}<br>Platz: %{{customdata[2]:.0f}}<extra></extra>',
        line=dict(color='#1f77b4'), marker=dict(color='#1f77b4')
    ))

    fig.add_trace(go.Scatter(
        x=df_elo2["Index"], y=df_elo2["elo"], mode='lines+markers', name=team2,
        connectgaps=False,
        customdata=df_elo2[["Saison_Label", "Spieltag_Label", "platz"]].values,
        hovertemplate=f'<b>{team2}</b><br>Saison: %{{customdata[0]}}<br>Spieltag: %{{customdata[1]}}<br>Elo: %{{y:.2f}}<br>Platz: %{{customdata[2]:.0f}}<extra></extra>',
        line=dict(color='#ff7f0e'), marker=dict(color='#ff7f0e')
    ))

    combined_index = pd.concat([df_elo1[["Index", "Spieltag_Label"]], df_elo2[["Index", "Spieltag_Label"]]])
    tick_step = max(1, len(combined_index) // 15)
    tickvals = combined_index["Index"][::tick_step].tolist()
    ticktext = combined_index["Spieltag_Label"][::tick_step].tolist()

    fig.update_layout(
        title=f"Elo-Entwicklung {team1} vs {team2} ({' + '.join(saison_labels)})",
        height=400, hovermode="x unified",
        xaxis=dict(tickvals=tickvals, ticktext=ticktext, tickangle=-45),
        yaxis=dict(title="Elo-Rating"),
        legend=dict(x=1.05, y=1, xanchor="left", yanchor="top")
    )
    return fig


def format_player_scouting_data(df_combined: pd.DataFrame) -> pd.DataFrame:
    """Formatiert die Spieler-Scouting-Daten für die Anzeige."""
    display_cols = ["vorname", "nachname", "team_name", "position",
                    "marktwert_eur", "pred_marktwert_eur", "abweichung_eur", "underrated_score",
                    "alter_lag", "elo_lag", "minuten_lag", "tore_pro_90_lag", "vorlagen_pro_90_lag",
                    "einsaetze", "startelfeinsaetze", "minuten",
                    "statistik_tore", "statistik_vorlagen", "gelbe_karten", "rote_karten"]

    df_disp = df_combined[display_cols].copy()
    df_disp.columns = ["Vorname", "Nachname", "Team", "Position",
                       "Aktueller MW (€)", "Prognostizierter MW (€)", "Potenzial (€)", "Scouting-Score",
                       "Alter", "Team ELO", "Minuten (Lag)", "Tore/90 Min (Lag)", "Assists/90 Min (Lag)",
                       "Einsätze", "Startelfeinsätze", "Spielminuten",
                       "Tore", "Assists", "Gelbe Karten", "Rote Karten"]

    for col in ["Aktueller MW (€)", "Prognostizierter MW (€)", "Potenzial (€)"]:
        df_disp[col] = df_disp[col].map(lambda x: f"{int(x):,}".replace(",", "."))

    df_disp["Scouting-Score"] = df_disp["Scouting-Score"].map(lambda x: f"{x:.2f}")
    df_disp["Alter"] = df_disp["Alter"].fillna(0).astype(int)
    df_disp["Team ELO"] = df_disp["Team ELO"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    df_disp["Minuten (Lag)"] = df_disp["Minuten (Lag)"].fillna(0).astype(int)
    df_disp["Tore/90 Min (Lag)"] = df_disp["Tore/90 Min (Lag)"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    df_disp["Assists/90 Min (Lag)"] = df_disp["Assists/90 Min (Lag)"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

    for col in ["Einsätze", "Startelfeinsätze", "Spielminuten", "Tore", "Assists", "Gelbe Karten", "Rote Karten"]:
        df_disp[col] = df_disp[col].fillna(0).astype(int)

    return df_disp


def get_spielplan_title(saison_labels: List[str], all_spieltage: List[int], selected_spieltage: List[int]) -> str:
    """Erstellt dynamischen Titel für Spielplan basierend auf Filtern."""
    if len(selected_spieltage) == len(all_spieltage):
        return f"Saison {' + '.join(saison_labels)}"
    else:
        spieltag_str = ", ".join(map(str, sorted(selected_spieltage)))
        return f"Saison {' + '.join(saison_labels)} - Spieltag {spieltag_str}"
