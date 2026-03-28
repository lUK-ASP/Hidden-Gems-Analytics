import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from Statistiken.load_statistiken import (
    get_Teams,
    get_team_analysis_stats_split_aggregated
)

from utils import (
    SAISON_OPTIONS,
    COLORS,
    CHART_HEIGHT_SMALL,
    CHART_HEIGHT_MEDIUM,
    cached_get_team_analysis,
    cached_get_elo_history,
    cached_get_elo_stats,
    create_analysis_table,
    prepare_elo_data,
    calculate_tick_values
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
        team_select = st.selectbox(
            "Team wählen:",
            options=sorted(teams),
            index=0
        )

        if len(saisons) == 1:
            st.markdown(f"## Team-Analyse {saison_labels[0]}")
            saison = saisons[0]

            analysis = cached_get_team_analysis(saison, team_select)
        else:
            st.markdown(f"## Team-Analyse: {' + '.join(saison_labels)}")
            analysis = get_team_analysis_stats_split_aggregated(saisons, team_select)

        if analysis:
            st.markdown("### Effizienz-Kennzahlen")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(label="Tore/Spiel", value=analysis["Gesamt"]["Tore/Spiel"])
            with col2:
                st.metric(label="Gegentore/Spiel", value=analysis["Gesamt"]["Gegentore/Spiel"])
            with col3:
                st.metric(label="Tordiff./Spiel", value=analysis["Gesamt"]["Tordiff./Spiel"])

            st.markdown("### Detaillierte Statistiken")
            tab_heim, tab_auswaerts, tab_gesamt = st.tabs([" Heim", " Auswärts", " Gesamt"])

            with tab_heim:
                heim_data = create_analysis_table(analysis, "Heim")
                st.dataframe(heim_data, width='stretch', hide_index=True)

            with tab_auswaerts:
                auswaerts_data = create_analysis_table(analysis, "Auswärts")
                st.dataframe(auswaerts_data, width='stretch', hide_index=True)

            with tab_gesamt:
                gesamt_data = create_analysis_table(analysis, "Gesamt")
                st.dataframe(gesamt_data, width='stretch', hide_index=True)

            st.markdown("### Form-Analyse")
            st.markdown("#### Elo-Statistiken")


            elo_stats = cached_get_elo_stats(team_select)

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

            st.markdown("#### Elo-Entwicklung und Tabellenplatz")

            all_elo = []
            for saison in saisons:

                df_elo_temp = cached_get_elo_history(team_select)
                df_elo_temp = df_elo_temp[df_elo_temp["Saison"] == saison]
                if not df_elo_temp.empty:
                    all_elo.append(df_elo_temp)

            if all_elo:
                df_elo_combined = pd.concat(all_elo, ignore_index=True)
                df_elo_combined = prepare_elo_data(df_elo_combined)

                fig_elo = make_subplots(specs=[[{"secondary_y": True}]])

                fig_elo.add_trace(
                    go.Scatter(
                        x=df_elo_combined["Index"],
                        y=df_elo_combined["elo"],
                        mode='lines+markers',
                        name='Elo-Rating',
                        line=dict(color=COLORS["primary"], width=2),
                        marker=dict(color=COLORS["primary"], size=5)
                    ),
                    secondary_y=False
                )

                fig_elo.add_trace(
                    go.Scatter(
                        x=df_elo_combined["Index"],
                        y=df_elo_combined["platz"],
                        mode='lines+markers',
                        name='Tabellenplatz',
                        line=dict(color=COLORS["secondary"], dash='dot', width=2),
                        marker=dict(color=COLORS["secondary"], size=5),
                        customdata=df_elo_combined[["Saison_Label", "Spieltag_Label"]].values,
                        hovertemplate='<b>Saison: %{customdata[0]}</b><br>Spieltag: %{customdata[1]}<br>Platz: %{y}<extra></extra>'
                    ),
                    secondary_y=True
                )

                tickvals, ticktext = calculate_tick_values(df_elo_combined)

                fig_elo.update_layout(
                    title_text=f"Elo-Entwicklung und Tabellenplatz {team_select} ({' + '.join(saison_labels)})",
                    height=CHART_HEIGHT_MEDIUM,
                    xaxis_tickangle=-45,
                    hovermode="x unified",
                    xaxis=dict(
                        tickvals=tickvals,
                        ticktext=ticktext
                    ),
                    font=dict(size=11)
                )

                fig_elo.update_yaxes(
                    title_text="<b>Elo-Rating</b>",
                    secondary_y=False,
                    range=[df_elo_combined["elo"].min() - 50, df_elo_combined["elo"].max() + 50],
                    gridcolor=COLORS["grid"]
                )
                fig_elo.update_yaxes(
                    title_text="<b>Tabellenplatz</b>",
                    secondary_y=True,
                    autorange="reversed",
                    tick0=1,
                    dtick=1,
                    gridcolor=COLORS["grid"]
                )

                st.plotly_chart(fig_elo, width='stretch')
            else:
                st.info("Keine Elo-Daten für diese Saison(en) verfügbar.")

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
                    color_discrete_map={"Tore": COLORS["primary"], "Gegentore": COLORS["secondary"]},
                    labels={"value": "Anzahl", "variable": "Typ"}
                )
                fig1.update_layout(height=CHART_HEIGHT_SMALL, showlegend=True)
                st.plotly_chart(fig1, width='stretch')

            with col2:
                st.markdown("#### Siegquote (%)")
                chart_data_2 = pd.DataFrame({
                    "Typ": ["Heim", "Auswärts"],
                    "Siegquote (%)": [analysis["Heim"]["Siegquote (%)"], analysis["Auswärts"]["Siegquote (%)"]]
                })
                fig2 = px.bar(
                    chart_data_2,
                    x="Typ",
                    y="Siegquote (%)",
                    color="Siegquote (%)",
                    color_continuous_scale="Greens",
                    labels={"value": "Quote (%)", "variable": ""}
                )
                fig2.update_layout(height=CHART_HEIGHT_SMALL, showlegend=False)
                st.plotly_chart(fig2, width='stretch')

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
                    color_continuous_scale="Blues",
                    labels={"value": "Quote (%)", "variable": ""}
                )
                fig3.update_layout(height=CHART_HEIGHT_SMALL, showlegend=False)
                st.plotly_chart(fig3, width='stretch')

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
                    color_continuous_scale="Purples",
                    labels={"value": "Punkte", "variable": ""}
                )
                fig4.update_layout(height=CHART_HEIGHT_SMALL, showlegend=False)
                st.plotly_chart(fig4, width='stretch')

        else:
            st.error("Keine Daten verfügbar für dieses Team.")
    else:
        st.warning("Bitte wähle mindestens eine Saison aus.")
