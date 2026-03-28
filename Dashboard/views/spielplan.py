import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

from utils import cached_get_spiele, SAISON_OPTIONS


def show():

    saison_label = st.selectbox(
        "Saison wählen:",
        options=list(SAISON_OPTIONS.keys()),
        index=2  # "2025/26" per default
    )
    saison = SAISON_OPTIONS[saison_label]

    try:
        # ✅ Nutze cached_get_spiele statt get_spiele_mit_teamnamen
        all_matches = cached_get_spiele()
        saison_matches = all_matches[all_matches["Saison"] == saison]

        if not saison_matches.empty:
            st.markdown(f"## Spielplan {saison_label}")

            spieltage = sorted(saison_matches["Spieltag"].unique())

            selected_spieltage = st.multiselect(
                "Spieltag(e) wählen:",
                options=spieltage,
                default=[spieltage[0]] if spieltage else []
            )

            teams = sorted(saison_matches["heimteam_name"].unique())
            team_filter = st.multiselect(
                "Nach Team filtern (optional):",
                options=teams,
                default=[],
            )

            if selected_spieltage:
                spieltag_matches = saison_matches[saison_matches["Spieltag"].isin(selected_spieltage)].copy()

                if team_filter:
                    spieltag_matches = spieltag_matches[
                        (spieltag_matches["heimteam_name"].isin(team_filter)) |
                        (spieltag_matches["auswaertsteam_name"].isin(team_filter))
                    ]

                if not spieltag_matches.empty:
                    st.markdown("### Spieltag(e)-Statistiken")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Gesamt Spiele", len(spieltag_matches))

                    with col2:
                        gesamt_tore = int(
                            spieltag_matches["Heimtore"].sum() + spieltag_matches["Auswaertstore"].sum())
                        st.metric("Gesamt Tore", gesamt_tore)

                    with col3:
                        ø_tore = round(gesamt_tore / len(spieltag_matches), 2) if len(spieltag_matches) > 0 else 0
                        st.metric("Ø Tore pro Spiel", ø_tore)

                    with col4:
                        null_spiele = sum(
                            (spieltag_matches["Heimtore"] == 0) | (spieltag_matches["Auswaertstore"] == 0))
                        st.metric("Zu-Null-Spiele", null_spiele)

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
