import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
import streamlit as st
import pandas as pd
import plotly.express as px
from Statistiken.load_statistiken import (
    get_tabelle,
    get_Teams,
    get_team_analysis_stats_split,
    get_player_market_value_history,
    get_all_teams_for_players,
    get_players_for_team,
    get_elo_history_for_team,
    get_elo_stats_for_team,
    get_positionen,
    get_underrated_players,
    get_spiele_mit_teamnamen,
    get_team_analysis_stats_split_aggregated,
    get_team_comparison_stats_aggregated
)
from utils import SAISON_OPTIONS, create_analysis_table, create_comparison_table
from Statistiken.extract_statistiken import get_marktwerte as _get_marktwerte


# ============================================================================
# DEBUG: WOHER KOMMEN DIE DATEN?
# ============================================================================

if st.checkbox("🔍 DEBUG: Datenquelle überprüfen"):
    st.markdown("### Debug: Verfolgung der Datenquellen")

    # 1. Check get_marktwerte() aus extract_statistiken
    st.markdown("#### 1️⃣ get_marktwerte() (extract_statistiken.py):")
    try:
        from Statistiken.extract_statistiken import get_marktwerte as extract_marktwerte

        df_extract = extract_marktwerte()
        st.write(f"**Verfügbare Spalten:**")
        st.write(sorted(df_extract.columns.tolist()))
    except Exception as e:
        st.error(f"Fehler: {e}")

    # 2. Check get_underrated_players() aus load_statistiken
    st.markdown("#### 2️⃣ get_underrated_players() (load_statistiken.py):")
    try:
        from Statistiken.load_statistiken import get_underrated_players

        df_underrated = get_underrated_players(min_marktwert=0, max_marktwert=50_000_000)
        st.write(f"**Verfügbare Spalten:**")
        st.write(sorted(df_underrated.columns.tolist()))
        st.write(f"\n**Sample-Daten:**")
        st.dataframe(df_underrated.head(1), width='stretch')
    except Exception as e:
        st.error(f"Fehler: {e}")

    st.divider()

# ============================================================================
# STREAMLIT KONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Hidden Gems Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# NAVIGATION MIT TABS OBEN
# ============================================================================

st.title("Hidden Gems Analytics")

# Session State für aktive View
if "statistik_view" not in st.session_state:
    st.session_state.statistik_view = "Tabelle"

# Tabs-Definition
tabs = [
    ("Tabelle", "Tabelle"),
    ("Spielplan", "Spielplan"),
    ("Team-Analyse", "Team-Analyse"),
    ("Team-Vergleich", "Team-Vergleiche"),
    ("Marktwert", "Spieler-Marktwert"),
    ("Scouting", "Spieler-Scouting")
]

# Erstelle Tabs mit Buttons
col1, col2, col3, col4, col5, col6 = st.columns(6)

cols = [col1, col2, col3, col4, col5, col6]

for idx, (col, (label, view_name)) in enumerate(zip(cols, tabs)):
    with col:
        # Button Styling basierend auf aktiver View
        if st.session_state.statistik_view == view_name:
            button_text = f"🔴 {label}"
            #button_style = "background-color: #FF2B2B; color: white;"
        else:
            button_text = f"⚪ {label}"
            #button_style = "background-color: #f0f2f6; color: #31333f;"

        if st.button(
            button_text,
            key=f"tab_{view_name}",
            use_container_width=True,
            help=f"Gehe zu {label}"
        ):
            st.session_state.statistik_view = view_name
            st.rerun()

st.markdown("---")

# Hole die aktuelle View aus Session State
statistik_view = st.session_state.statistik_view

# ============================================================================
# HAUPTBEREICH - SAISONTABELLE
# ============================================================================

if statistik_view == "Tabelle":

    saison_options = {
        "2023/24": 2023,
        "2024/25": 2024,
        "2025/26": 2025
    }

    saison_labels = st.multiselect(
        "Saison(s) wählen:",
        options=list(SAISON_OPTIONS.keys()),
        default=["2025/26"]
    )
    saisons = [SAISON_OPTIONS[label] for label in saison_labels]

    if saisons:
        if len(saisons) == 1:
            # ===== EINZELNE SAISON =====
            st.markdown(f"## Saisontabelle {saison_labels[0]}")
            try:
                tabelle = get_tabelle(saisons[0])
                tabelle.index = tabelle.index + 1
                dynamic_height = 30 + (len(tabelle) * 35)
                st.dataframe(tabelle, width='stretch', height=dynamic_height)
            except Exception as e:
                st.error(f"Fehler beim Laden der Tabelle: {e}")

        else:
            # ===== MEHRERE SAISONS - AGGREGIERT ("BEST-OF") =====
            st.markdown(f"## Bundesliga Best-Of: {' + '.join(saison_labels)}")

            try:
                aggregated_data = []
                for saison in saisons:
                    tabelle = get_tabelle(saison)
                    if not tabelle.empty:
                        tabelle["saison"] = saison
                        aggregated_data.append(tabelle)

                if aggregated_data:
                    combined_df = pd.concat(aggregated_data, ignore_index=True)
                    agg_dict = {
                        "spiele": "sum",
                        "siege": "sum",
                        "unentschieden": "sum",
                        "niederlagen": "sum",
                        "tore": "sum",
                        "gegentore": "sum",
                        "tordifferenz": "sum",
                        "punkte": "sum"
                    }
                    best_of_tabelle = combined_df.groupby("team").agg(agg_dict).reset_index()
                    best_of_tabelle = best_of_tabelle.sort_values("punkte", ascending=False).reset_index(drop=True)
                    best_of_tabelle.index = best_of_tabelle.index + 1
                    best_of_tabelle["tordifferenz"] = best_of_tabelle["tore"] - best_of_tabelle["gegentore"]

                    fixed_height = 30 + (18 * 35)
                    st.dataframe(best_of_tabelle, width='stretch', height=fixed_height)

                    st.markdown("### Best-Of Statistiken")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Gesamt Spiele", int(best_of_tabelle["spiele"].sum()))
                    with col2:
                        st.metric("Gesamt Tore", int(best_of_tabelle["tore"].sum()))
                    with col3:
                        st.metric("Gesamt Gegentore", int(best_of_tabelle["gegentore"].sum()))
                    with col4:
                        st.metric("Top-Team Punkte", int(best_of_tabelle["punkte"].iloc[0]))
                else:
                    st.warning("Keine Daten für die gewählten Saisons gefunden.")

            except Exception as e:
                st.error(f"Fehler beim Aggregieren der Tabelle: {e}")
    else:
        st.warning("Bitte wähle mindestens eine Saison aus.")


# ============================================================================
# HAUPTBEREICH - SPIELPLAN
# ============================================================================

elif statistik_view == "Spielplan":
    # # st.markdown("### Saison- und Spieltag-Auswahl")  # ← kommentiert

    saison_options = {
        "2023/24": 2023,
        "2024/25": 2024,
        "2025/26": 2025
    }

    saison_label = st.selectbox(
        "Saison wählen:",
        options=list(saison_options.keys()),
        index=0,
        key="saison_spielplan"
    )
    saison = saison_options[saison_label]

    try:
        # Lade alle Spiele für die Saison
        all_matches = get_spiele_mit_teamnamen()
        saison_matches = all_matches[all_matches["Saison"] == saison]

        if not saison_matches.empty:
            # Bestimme verfügbare Spieltage
            spieltage = sorted(saison_matches["Spieltag"].unique())

            # Filter für Spieltag (Multi-Select)
            selected_spieltage = st.multiselect(
                "Spieltag(e) wählen:",
                options=spieltage,
                default=[spieltage[0]] if spieltage else []
            )

            # Optional: Filter nach Team
            teams = sorted(saison_matches["heimteam_name"].unique())
            team_filter = st.multiselect(
                "Nach Team filtern (optional):",
                options=teams,
                default=[],
            )

            # ← NEU: Dynamische Überschrift basierend auf Filtern
            if selected_spieltage:
                all_spieltage = sorted(saison_matches["Spieltag"].unique())

                if len(selected_spieltage) == len(all_spieltage):
                    # Alle Spieltage ausgewählt → nur Saison anzeigen
                    filter_title = f"Saison {saison_label}"
                else:
                    # Nur einige Spieltage ausgewählt
                    spieltag_str = ", ".join(map(str, sorted(selected_spieltage)))
                    filter_title = f"Saison {saison_label} - Spieltag {spieltag_str}"

                st.markdown(f"## Spielplan {filter_title}")

            if selected_spieltage:
                # Filtere nach Spieltagen
                spieltag_matches = saison_matches[saison_matches["Spieltag"].isin(selected_spieltage)].copy()

                # Filtere nach Teams, falls ausgewählt
                if team_filter:
                    spieltag_matches = spieltag_matches[
                        (spieltag_matches["heimteam_name"].isin(team_filter)) |
                        (spieltag_matches["auswaertsteam_name"].isin(team_filter))
                        ]

                if not spieltag_matches.empty:
                    # Zusatz-Statistiken
                    st.markdown("### Spieltag(e)-Statistiken")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Gesamt Spiele", len(spieltag_matches))

                    with col2:
                        gesamt_tore = int(spieltag_matches["Heimtore"].sum() + spieltag_matches["Auswaertstore"].sum())
                        st.metric("Gesamt Tore", gesamt_tore)

                    with col3:
                        ø_tore = round(gesamt_tore / len(spieltag_matches), 2) if len(spieltag_matches) > 0 else 0
                        st.metric("Ø Tore pro Spiel", ø_tore)

                    with col4:
                        null_spiele = sum(
                            (spieltag_matches["Heimtore"] == 0) | (spieltag_matches["Auswaertstore"] == 0))
                        st.metric("Zu-Null-Spiele", null_spiele)

                    # Detailansicht der Spiele
                    st.markdown("### Detaillierte Spielübersicht")

                    for idx, spiel in spieltag_matches.iterrows():
                        col1, col2, col3 = st.columns([2, 1, 2])

                        with col1:
                            st.write(f"**{spiel['heimteam_name']}**")

                        with col2:
                            st.write(f"**{int(spiel['Heimtore'])}:{int(spiel['Auswaertstore'])}**")
                            st.caption(
                                f"ST {int(spiel['Spieltag'])} | {spiel['match_date'].strftime('%d.%m.%Y') if pd.notna(spiel['match_date']) else '-'}")

                        with col3:
                            st.write(f"**{spiel['auswaertsteam_name']}**")

                        st.divider()

                else:
                    st.info("Keine Spiele für diese Auswahl gefunden.")
            else:
                st.warning("Bitte wähle mindestens einen Spieltag aus.")

        else:
            st.error("Keine Spiele für diese Saison gefunden.")

    except Exception as e:
        st.error(f"Fehler beim Laden des Spielplans: {e}")




# ============================================================================
# HAUPTBEREICH - TEAM-ANALYSE
# ============================================================================

elif statistik_view == "Team-Analyse":
    # Lokaler Saison-Filter (Multi-Select)

    saison_options = {
        "2023/24": 2023,
        "2024/25": 2024,
        "2025/26": 2025
    }
    saison_labels = st.multiselect(
        "Saison(s) wählen:",
        options=list(saison_options.keys()),
        default=["2025/26"],
        key="saison_team_analyse"
    )
    saisons = [saison_options[label] for label in saison_labels]

    if saisons:
        # Lade alle Teams für die erste Saison
        teams = get_Teams(saisons[0])
        team_select = st.selectbox(
            "Team wählen:",
            options=sorted(teams),
            index=0
        )

        if len(saisons) == 1:
            # ===== EINZELNE SAISON =====
            st.markdown(f"## Team-Analyse {saison_labels[0]}")
            saison = saisons[0]
            analysis = get_team_analysis_stats_split(saison, team_select)

        else:
            # ===== MEHRERE SAISONS - AGGREGIERT =====
            st.markdown(f"## Team-Analyse: {' + '.join(saison_labels)}")


            analysis = get_team_analysis_stats_split_aggregated(saisons, team_select)

        if analysis:
            # 1. DREI GROSSE METRIKEN
            st.markdown("### Effizienz-Kennzahlen")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(label="Tore/Spiel", value=analysis["Gesamt"]["Tore/Spiel"])
            with col2:
                st.metric(label="Gegentore/Spiel", value=analysis["Gesamt"]["Gegentore/Spiel"])
            with col3:
                st.metric(label="Tordiff./Spiel", value=analysis["Gesamt"]["Tordiff./Spiel"])

            # 2. DETAILTABELLE MIT TABS
            st.markdown("### Detaillierte Statistiken")

            tab_heim, tab_auswaerts, tab_gesamt = st.tabs([" Heim", " Auswärts", " Gesamt"])

            with tab_heim:
                heim_data = create_analysis_table(analysis, "Heim")
                st.dataframe(heim_data, width='stretch', hide_index=True)

            with tab_auswaerts:
                auswaerts_data = create_analysis_table(analysis, "Auswärts")
                st.dataframe(auswaerts_data, width='stretch', hide_index=True)  # Korrigiert

            with tab_gesamt:
                gesamt_data = create_analysis_table(analysis, "Gesamt")
                st.dataframe(gesamt_data, width='stretch', hide_index=True)  # Korrigiert

            # 4. ELO-VERLAUF
            st.markdown("### Form-Analyse")

            # ===== ELO-STATISTIKEN =====
            st.markdown("#### Elo-Statistiken")

            elo_stats = get_elo_stats_for_team(team_select)

            if elo_stats:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Aktueller Elo", f"{elo_stats['elo_current']:.0f}")
                with c2:
                    st.metric("Elo Start", f"{elo_stats['elo_start']:.0f}")
                with c3:
                    st.metric("Elo Höchst", f"{elo_stats['elo_max']:.0f}")
                with c4:
                    st.metric("Elo Tief", f"{elo_stats['elo_min']:.0f}")

            # ===== ELO-VERLAUF CHART =====
            st.markdown("#### Elo-Entwicklung")

            all_elo = []
            for saison in saisons:
                df_elo_temp = get_elo_history_for_team(team_select)
                df_elo_temp = df_elo_temp[df_elo_temp["Saison"] == saison]
                if not df_elo_temp.empty:
                    all_elo.append(df_elo_temp)

            if all_elo:
                df_elo_combined = pd.concat(all_elo, ignore_index=True)
                df_elo_combined = df_elo_combined.sort_values(["Saison", "Spieltag"])

                df_elo_combined["Saison_Label"] = (df_elo_combined["Saison"].astype(str) + "/" +
                                                   (df_elo_combined["Saison"] + 1).astype(str).str[-2:])
                df_elo_combined["Zeitpunkt"] = df_elo_combined["Spieltag"].astype(str)

                fig_elo = px.line(
                    df_elo_combined,
                    x="Zeitpunkt",
                    y="elo",
                    markers=True,
                    title=f"Elo-Entwicklung {team_select} ({' + '.join(saison_labels)})",
                    labels={"Zeitpunkt": "Saison-Spieltag", "elo": "Elo-Rating"},
                    color_discrete_sequence=["#1f77b4"]
                )
                fig_elo.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_elo, use_container_width=True)
            else:
                st.info("Keine Elo-Daten für diese Saison(en) verfügbar.")

            # 3. CHARTS


            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Tore vs. Gegentore")
                chart_data_1 = pd.DataFrame({
                    "Kategorie": ["Heim", "Auswärts"],
                    "Tore": [analysis["Heim"]["Tore"], analysis["Auswärts"]["Tore"]],
                    "Gegentore": [analysis["Heim"]["Gegentore"], analysis["Auswärts"]["Gegentore"]]
                })
                fig1 = px.bar(
                    chart_data_1,
                    x="Kategorie",
                    y=["Tore", "Gegentore"],
                    barmode="group",
                    color_discrete_map={"Tore": "#1f77b4", "Gegentore": "#ff7f0e"}
                )
                fig1.update_layout(height=350)
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.markdown("#### Siegquote")
                chart_data_2 = pd.DataFrame({
                    "Typ": ["Heim", "Auswärts"],
                    "Siegquote (%)": [analysis["Heim"]["Siegquote (%)"], analysis["Auswärts"]["Siegquote (%)"]]
                })
                fig2 = px.bar(
                    chart_data_2,
                    x="Typ",
                    y="Siegquote (%)",
                    color="Siegquote (%)",
                    color_continuous_scale="Greens"
                )
                fig2.update_layout(height=350)
                st.plotly_chart(fig2, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Zu-Null-Spiele (%)")
                chart_data_3 = pd.DataFrame({
                    "Typ": ["Heim", "Auswärts"],
                    "Zu-Null (%)": [analysis["Heim"]["Zu-Null-Spiele (%)"], analysis["Auswärts"]["Zu-Null-Spiele (%)"]]
                })
                fig3 = px.bar(
                    chart_data_3,
                    x="Typ",
                    y="Zu-Null (%)",
                    color="Zu-Null (%)",
                    color_continuous_scale="Blues"
                )
                fig3.update_layout(height=350)
                st.plotly_chart(fig3, use_container_width=True)

            with col2:
                st.markdown("#### Punkte/Spiel")
                chart_data_4 = pd.DataFrame({
                    "Typ": ["Heim", "Auswärts"],
                    "Punkte/Spiel": [analysis["Heim"]["Punkte/Spiel"], analysis["Auswärts"]["Punkte/Spiel"]]
                })
                fig4 = px.bar(
                    chart_data_4,
                    x="Typ",
                    y="Punkte/Spiel",
                    color="Punkte/Spiel",
                    color_continuous_scale="Purples"
                )
                fig4.update_layout(height=350)
                st.plotly_chart(fig4, use_container_width=True)

        else:
            st.error("Keine Daten verfügbar für dieses Team.")

    else:
        st.warning("Bitte wähle mindestens eine Saison aus.")


# ============================================================================
# HAUPTBEREICH - TEAM-VERGLEICHE
# ============================================================================

elif statistik_view == "Team-Vergleiche":
    saison_labels = st.multiselect(
        "Saison(s) wählen:",
        options=list(SAISON_OPTIONS.keys()),
        default=["2025/26"]
    )
    saisons = [SAISON_OPTIONS[label] for label in saison_labels]

    if saisons:
        teams = get_Teams(saisons[0])

        col1, col2 = st.columns(2)

        with col1:
            team1 = st.selectbox(
                "Team 1 wählen:",
                options=sorted(teams),
                index=0,
                key="team_vergleich_1"
            )

        with col2:
            team2 = st.selectbox(
                "Team 2 wählen:",
                options=sorted(teams),
                index=1 if len(teams) > 1 else 0,
                key="team_vergleich_2"
            )

        if team1 != team2:
            if len(saisons) == 1:
                st.markdown(f"## Team-Vergleiche {saison_labels[0]}")
                saison = saisons[0]
                stats1 = get_team_analysis_stats_split(saison, team1)
                stats2 = get_team_analysis_stats_split(saison, team2)

            else:
                st.markdown(f"## Team-Vergleiche: {' + '.join(saison_labels)}")
                stats1, stats2 = get_team_comparison_stats_aggregated(team1, team2, saisons)

            if stats1 and stats2:
                st.markdown("### Team Vergleich")

                tab_heim, tab_auswaerts, tab_gesamt = st.tabs(["Heim", "Auswärts", "Gesamt"])


                # In der TEAM-VERGLEICHE Sektion

                with tab_gesamt:
                    gesamt_data = create_comparison_table(stats1, stats2, team1, team2, "Gesamt")
                    st.dataframe(gesamt_data, width='stretch', hide_index=True)

                with tab_heim:
                    heim_data = create_comparison_table(stats1, stats2, team1, team2, "Heim")
                    st.dataframe(heim_data, width='stretch', hide_index=True)

                with tab_auswaerts:
                    auswaerts_data = create_comparison_table(stats1, stats2, team1, team2, "Auswärts")
                    st.dataframe(auswaerts_data, width='stretch', hide_index=True)

                st.markdown("### Form-Analyse")

                # ===== ELO-STATISTIKEN FÜR BEIDE TEAMS =====
                st.markdown("#### Elo-Statistiken")

                elo_stats_team1 = get_elo_stats_for_team(team1)
                elo_stats_team2 = get_elo_stats_for_team(team2)

                if elo_stats_team1 and elo_stats_team2:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**{team1}**")
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.metric("Aktueller Elo", f"{elo_stats_team1['elo_current']:.0f}")
                        with c2:
                            st.metric("Elo Start", f"{elo_stats_team1['elo_start']:.0f}")
                        with c3:
                            st.metric("Elo Höchst", f"{elo_stats_team1['elo_max']:.0f}")
                        with c4:
                            st.metric("Elo Tief", f"{elo_stats_team1['elo_min']:.0f}")

                    with col2:
                        st.markdown(f"**{team2}**")
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.metric("Aktueller Elo", f"{elo_stats_team2['elo_current']:.0f}")
                        with c2:
                            st.metric("Elo Start", f"{elo_stats_team2['elo_start']:.0f}")
                        with c3:
                            st.metric("Elo Höchst", f"{elo_stats_team2['elo_max']:.0f}")
                        with c4:
                            st.metric("Elo Tief", f"{elo_stats_team2['elo_min']:.0f}")

                # ===== ELO-VERLAUF CHART =====
                st.markdown("#### Elo-Entwicklung")

                all_elo_team1 = []
                all_elo_team2 = []

                for saison in saisons:
                    df_elo_t1 = get_elo_history_for_team(team1)
                    df_elo_t1 = df_elo_t1[df_elo_t1["Saison"] == saison]
                    if not df_elo_t1.empty:
                        all_elo_team1.append(df_elo_t1)

                    df_elo_t2 = get_elo_history_for_team(team2)
                    df_elo_t2 = df_elo_t2[df_elo_t2["Saison"] == saison]
                    if not df_elo_t2.empty:
                        all_elo_team2.append(df_elo_t2)

                if all_elo_team1 and all_elo_team2:
                    df_elo1_combined = pd.concat(all_elo_team1, ignore_index=True)
                    df_elo2_combined = pd.concat(all_elo_team2, ignore_index=True)

                    df_elo1_combined = df_elo1_combined.sort_values(["Saison", "Spieltag"])
                    df_elo2_combined = df_elo2_combined.sort_values(["Saison", "Spieltag"])

                    df_elo1_combined["Saison_Label"] = (df_elo1_combined["Saison"].astype(str) + "/" +
                                                        (df_elo1_combined["Saison"] + 1).astype(str).str[-2:])
                    df_elo1_combined["Zeitpunkt"] = df_elo1_combined["Spieltag"].astype(str)

                    df_elo2_combined["Saison_Label"] = (df_elo2_combined["Saison"].astype(str) + "/" +
                                                        (df_elo2_combined["Saison"] + 1).astype(str).str[-2:])
                    df_elo2_combined["Zeitpunkt"] = df_elo2_combined["Spieltag"].astype(str)

                    data_elo = pd.concat([
                        df_elo1_combined[["Zeitpunkt", "elo"]].assign(Team=team1),
                        df_elo2_combined[["Zeitpunkt", "elo"]].assign(Team=team2)
                    ])

                    fig_elo = px.line(
                        data_elo,
                        x="Zeitpunkt",
                        y="elo",
                        color="Team",
                        markers=True,
                        title=f"Elo-Entwicklung {team1} vs {team2} ({' + '.join(saison_labels)})",
                        labels={"Zeitpunkt": "Saison-Spieltag", "elo": "Elo-Rating"}
                    )
                    fig_elo.update_layout(height=400, xaxis_tickangle=-45)
                    st.plotly_chart(fig_elo, use_container_width=True)
                else:
                    st.info("Keine Elo-Daten für diese Saison(en) verfügbar.")

                # ===== VERGLEICHS-CHARTS =====
                st.markdown("### Leistungsvergleiche")

                col1, col2 = st.columns(2)

                # Chart 1: Tore vs. Gegentore
                with col1:
                    st.markdown("#### Tore & Gegentore (Gesamt)")
                    comparison_data_1 = pd.DataFrame({
                        "Metrik": ["Tore", "Gegentore"],
                        team1: [stats1["Gesamt"]["Tore"], stats1["Gesamt"]["Gegentore"]],
                        team2: [stats2["Gesamt"]["Tore"], stats2["Gesamt"]["Gegentore"]]
                    })
                    fig_1 = px.bar(
                        comparison_data_1,
                        x="Metrik",
                        y=[team1, team2],
                        barmode="group",
                        color_discrete_map={team1: "#1f77b4", team2: "#ff7f0e"},
                        labels={"value": "Anzahl", "variable": "Team"}
                    )
                    fig_1.update_layout(height=350, showlegend=True)
                    st.plotly_chart(fig_1, use_container_width=True)

                # Chart 2: Punkte pro Spiel
                with col2:
                    st.markdown("#### Punkte pro Spiel")
                    comparison_data_2 = pd.DataFrame({
                        "Kategorie": ["Heim", "Auswärts", "Gesamt"],
                        team1: [
                            stats1["Heim"]["Punkte/Spiel"],
                            stats1["Auswärts"]["Punkte/Spiel"],
                            stats1["Gesamt"]["Punkte/Spiel"]
                        ],
                        team2: [
                            stats2["Heim"]["Punkte/Spiel"],
                            stats2["Auswärts"]["Punkte/Spiel"],
                            stats2["Gesamt"]["Punkte/Spiel"]
                        ]
                    })
                    fig_2 = px.bar(
                        comparison_data_2,
                        x="Kategorie",
                        y=[team1, team2],
                        barmode="group",
                        color_discrete_map={team1: "#1f77b4", team2: "#ff7f0e"},
                        labels={"value": "Punkte/Spiel", "variable": "Team"}
                    )
                    fig_2.update_layout(height=350, showlegend=True)
                    st.plotly_chart(fig_2, use_container_width=True)

                col1, col2 = st.columns(2)

                # Chart 3: Siegquote
                with col1:
                    st.markdown("#### Siegquote (%)")
                    comparison_data_3 = pd.DataFrame({
                        "Kategorie": ["Heim", "Auswärts", "Gesamt"],
                        team1: [
                            stats1["Heim"]["Siegquote (%)"],
                            stats1["Auswärts"]["Siegquote (%)"],
                            stats1["Gesamt"]["Siegquote (%)"]
                        ],
                        team2: [
                            stats2["Heim"]["Siegquote (%)"],
                            stats2["Auswärts"]["Siegquote (%)"],
                            stats2["Gesamt"]["Siegquote (%)"]
                        ]
                    })
                    fig_3 = px.bar(
                        comparison_data_3,
                        x="Kategorie",
                        y=[team1, team2],
                        barmode="group",
                        color_discrete_map={team1: "#2ca02c", team2: "#d62728"},
                        labels={"value": "Siegquote (%)", "variable": "Team"}
                    )
                    fig_3.update_layout(height=350, showlegend=True)
                    st.plotly_chart(fig_3, use_container_width=True)

                # Chart 4: Zu-Null-Spiele
                with col2:
                    st.markdown("#### Zu-Null-Spiele (%)")
                    comparison_data_4 = pd.DataFrame({
                        "Kategorie": ["Heim", "Auswärts", "Gesamt"],
                        team1: [
                            stats1["Heim"]["Zu-Null-Spiele (%)"],
                            stats1["Auswärts"]["Zu-Null-Spiele (%)"],
                            stats1["Gesamt"]["Zu-Null-Spiele (%)"]
                        ],
                        team2: [
                            stats2["Heim"]["Zu-Null-Spiele (%)"],
                            stats2["Auswärts"]["Zu-Null-Spiele (%)"],
                            stats2["Gesamt"]["Zu-Null-Spiele (%)"]
                        ]
                    })
                    fig_4 = px.bar(
                        comparison_data_4,
                        x="Kategorie",
                        y=[team1, team2],
                        barmode="group",
                        color_discrete_map={team1: "#9467bd", team2: "#8c564b"},
                        labels={"value": "Zu-Null (%)", "variable": "Team"}
                    )
                    fig_4.update_layout(height=350, showlegend=True)
                    st.plotly_chart(fig_4, use_container_width=True)

            else:
                st.error("Keine Daten verfügbar für einen oder beide Teams.")

        else:
            st.warning("Bitte wähle zwei unterschiedliche Teams!")

    else:
        st.warning("Bitte wähle mindestens eine Saison aus.")


# ============================================================================
# HAUPTBEREICH - SPIELER-MARKTWERT
# ============================================================================

elif statistik_view == "Spieler-Marktwert":


    try:
        teams = get_all_teams_for_players()
        team_select = st.selectbox(
            "Team wählen:",
            options=sorted(teams),
            index=0
        )

        spieler = get_players_for_team(team_select)
        spieler_select = st.selectbox(
            "Spieler wählen:",
            options=sorted(spieler),
            index=0
        )
        st.markdown("## Marktwert")
        df_spieler = get_player_market_value_history(team_select)


        vorname, nachname = spieler_select.split(" ", 1)
        df_spieler_filtered = df_spieler[
            (df_spieler["vorname"] == vorname) &
            (df_spieler["nachname"] == nachname)
        ]

        if len(df_spieler_filtered) > 0:
            st.markdown("### Marktwertentwicklung")

            fig = px.line(
                df_spieler_filtered,
                x="spieler_saison",
                y="marktwert_eur",
                markers=True,
                title=f"{spieler_select} - Marktwertentwicklung",
                labels={
                    "spieler_saison": "Saison",
                    "marktwert_eur": "Marktwert (€)"
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Details")
            df_display = df_spieler_filtered[
                ["spieler_saison", "position", "marktwert_eur"]
            ].copy()
            df_display.columns = ["Saison", "Position", "Marktwert (€)"]

            df_display["Marktwert (€)"] = df_display["Marktwert (€)"].apply(
                lambda x: f"{x:,.0f}".replace(",", ".")
            )

            st.dataframe(df_display, width='stretch', hide_index=True)
        else:
            st.info("Keine Daten für diesen Spieler gefunden.")

    except Exception as e:
        st.error(f"Fehler bei Spieler-Marktwert: {e}")


# ============================================================================
# HAUPTBEREICH - SPIELER-SCOUTING
# ============================================================================

elif statistik_view == "Spieler-Scouting":
    st.markdown("## Spieler-Scouting")

    # Filter-Controls
    col1, col2, col3 = st.columns(3)
    with col1:
        min_mw = st.slider("Min. Marktwert (€)", 0, 50_000_000, 0, step=500_000)
    with col2:
        max_mw = st.slider("Max. Marktwert (€)", 0, 50_000_000, 20_000_000, step=500_000)
    with col3:
        min_min = st.slider("Min. Minuten (letzte Saison)", 0, 3000, 600, step=100)

    col4, col5 = st.columns(2)
    with col4:
        min_score = st.slider("Min. Scouting-Score", 1.0, 5.0, 1.15, step=0.05)
    with col5:
        min_diff = st.slider("Min. Abweichung (€)", 0, 10_000_000, 0, step=500_000)

    pos_filter = st.multiselect("Position filtern (optional)", options=get_positionen())

    # ML-Output
    df_ud = get_underrated_players(
        min_marktwert=min_mw,
        max_marktwert=max_mw,
        min_minuten_lag=min_min,
        min_underrated_score=min_score,
        min_abweichung_eur=min_diff
    )

    # Überblicks-Metriken
    st.markdown("### Scouting-Übersicht")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gesamt Spieler", len(df_ud))
    with col2:
        avg_score = df_ud["underrated_score"].mean() if not df_ud.empty else 0
        st.metric("Ø Scouting-Score", f"{avg_score:.2f}")
    with col3:
        total_potential = df_ud["abweichung_eur"].sum() if not df_ud.empty else 0
        st.metric("Gesamtes Potenzial (€)", f"{int(total_potential):,}".replace(",", "."))

    # Optional nach Position filtern
    if pos_filter:
        df_ud = df_ud[df_ud["position"].isin(pos_filter)]

    if df_ud.empty:
        st.info("Keine unterbewerteten Spieler gefunden mit diesen Filtern.")
    else:
        st.markdown("### Scout-Ergebnisse")

        # 1) Rohdaten aus Scouting_View
        from Statistiken.extract_statistiken import get_marktwerte as _get_marktwerte
        df_raw = _get_marktwerte()[[
            "spieler_id", "spieler_saison",
            "einsaetze", "startelfeinsaetze", "minuten",
            "statistik_tore", "statistik_vorlagen",
            "gelbe_karten", "rote_karten"
        ]]

        # 2) ML-Daten
        df_ml = df_ud.copy()

        # 3) Merge beider DataFrames
        df_combined = pd.merge(
            df_ml,
            df_raw,
            how="left",
            on=["spieler_id", "spieler_saison"]
        )


        # 4) Spalten-Auswahl und Umbenennung
        display_cols = [
            "vorname", "nachname", "team_name", "position",
            "marktwert_eur", "pred_marktwert_eur", "abweichung_eur", "underrated_score",
            "alter_lag", "elo_lag", "minuten_lag", "tore_pro_90_lag", "vorlagen_pro_90_lag",
            "einsaetze", "startelfeinsaetze", "minuten",
            "statistik_tore", "statistik_vorlagen",
            "gelbe_karten", "rote_karten"
        ]

        df_disp = df_combined[display_cols].copy()
        df_disp.columns = [
            "Vorname", "Nachname", "Team", "Position",
            "Aktueller MW (€)", "Prognostizierter MW (€)", "Potenzial (€)", "Scouting-Score",
            "Alter", "Team ELO", "Minuten (Lag)", "Tore/90 Min (Lag)", "Assists/90 Min (Lag)",
            "Einsätze", "Startelfeinsätze", "Spielminuten",
            "Tore", "Assists",
            "Gelbe Karten", "Rote Karten"
        ]

        # 5) Formatierung
        for c in ["Aktueller MW (€)", "Prognostizierter MW (€)", "Potenzial (€)"]:
            df_disp[c] = df_disp[c].map(lambda x: f"{int(x):,}".replace(",", "."))
        df_disp["Scouting-Score"] = df_disp["Scouting-Score"].map(lambda x: f"{x:.2f}")
        df_disp["Alter"] = df_disp["Alter"].fillna(0).astype(int)
        df_disp["Team ELO"] = df_disp["Team ELO"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
        df_disp["Minuten (Lag)"] = df_disp["Minuten (Lag)"].fillna(0).astype(int)
        df_disp["Tore/90 Min (Lag)"] = df_disp["Tore/90 Min (Lag)"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
        df_disp["Assists/90 Min (Lag)"] = df_disp["Assists/90 Min (Lag)"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

        for col in ["Einsätze", "Startelfeinsätze", "Spielminuten", "Tore", "Assists", "Gelbe Karten", "Rote Karten"]:
            df_disp[col] = df_disp[col].fillna(0).astype(int)

        # 6) Ausgabe
        st.dataframe(df_disp, width="stretch", hide_index=True)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "<small>Powered by Team JALT - Deployed im Rahmen der LV Business Intelligence der HWR Berlin </small>"
    "</div>",
    unsafe_allow_html=True
)
