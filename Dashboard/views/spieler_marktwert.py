import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px

from utils import (
    cached_get_all_teams_for_players,
    cached_get_players_for_team,
    cached_get_player_market_value_history
)


def show():
    try:

        teams = cached_get_all_teams_for_players()
        team_select = st.selectbox(
            "Team wählen:",
            options=sorted(teams),
            index=0
        )

        spieler = cached_get_players_for_team(team_select)
        spieler_select = st.selectbox(
            "Spieler wählen:",
            options=sorted(spieler),
            index=0
        )
        st.markdown("## Marktwert")


        df_spieler = cached_get_player_market_value_history(team_select)

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
