import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from Statistiken.load_statistiken import (
    get_Teams,
    get_team_comparison_stats_aggregated
)

from utils import (
    SAISON_OPTIONS,
    cached_get_team_analysis,
    cached_get_elo_history,
    cached_get_elo_stats,
    create_comparison_table,
    prepare_comparison_elo_data,
    create_elo_comparison_figure
)


def show():
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

                stats1 = cached_get_team_analysis(saison, team1)
                stats2 = cached_get_team_analysis(saison, team2)

            else:
                st.markdown(f"## Team-Vergleiche: {' + '.join(saison_labels)}")
                stats1, stats2 = get_team_comparison_stats_aggregated(team1, team2, saisons)

            if stats1 and stats2:
                st.markdown("### Team Vergleich")

                tab_heim, tab_auswaerts, tab_gesamt = st.tabs(["Heim", "Auswärts", "Gesamt"])

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
                st.markdown("#### Elo-Statistiken")


                elo_stats_team1 = cached_get_elo_stats(team1)
                elo_stats_team2 = cached_get_elo_stats(team2)

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

                st.markdown("#### Elo-Entwicklung")

                all_elo_team1 = []
                all_elo_team2 = []

                for saison in saisons:

                    df_elo_t1 = cached_get_elo_history(team1)
                    df_elo_t1 = df_elo_t1[df_elo_t1["Saison"] == saison]
                    if not df_elo_t1.empty:
                        all_elo_team1.append(df_elo_t1)

                    df_elo_t2 = cached_get_elo_history(team2)
                    df_elo_t2 = df_elo_t2[df_elo_t2["Saison"] == saison]
                    if not df_elo_t2.empty:
                        all_elo_team2.append(df_elo_t2)

                min_saison = None
                if all_elo_team1:
                    min_saison = pd.concat(all_elo_team1)["Saison"].min()
                elif all_elo_team2:
                    min_saison = pd.concat(all_elo_team2)["Saison"].min()

                if all_elo_team1:
                    df_elo1_combined = pd.concat(all_elo_team1, ignore_index=True)
                    df_elo1_combined = prepare_comparison_elo_data(df_elo1_combined, min_saison)

                if all_elo_team2:
                    df_elo2_combined = pd.concat(all_elo_team2, ignore_index=True)
                    df_elo2_combined = prepare_comparison_elo_data(df_elo2_combined, min_saison)

                if all_elo_team1 and all_elo_team2:
                    fig_elo = create_elo_comparison_figure(df_elo1_combined, df_elo2_combined, team1, team2,
                                                           saison_labels)
                    st.plotly_chart(fig_elo, use_container_width=True)
                else:
                    st.info("Keine Elo-Daten für diese Saison(en) verfügbar.")

                st.markdown("### Leistungsvergleiche")

                col1, col2 = st.columns(2)

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
