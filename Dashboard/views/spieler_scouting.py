import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

from utils import (
    cached_get_positionen,
    cached_get_underrated_players,
    cached_get_marktwerte,
    format_player_scouting_data
)


def show():
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

    # ✅ Nutze cached_get_positionen
    pos_filter = st.multiselect("Position filtern (optional)", options=cached_get_positionen())

    # ✅ Nutze cached_get_underrated_players mit den Slider-Werten
    df_ud = cached_get_underrated_players(
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

        # ✅ Nutze cached_get_marktwerte
        df_raw = cached_get_marktwerte()[[
            "spieler_id", "spieler_saison",
            "einsaetze", "startelfeinsaetze", "minuten",
            "statistik_tore", "statistik_vorlagen",
            "gelbe_karten", "rote_karten"
        ]]

        # ML-Daten
        df_ml = df_ud.copy()

        # Merge beider DataFrames
        df_combined = pd.merge(
            df_ml,
            df_raw,
            how="left",
            on=["spieler_id", "spieler_saison"]
        )

        df_disp = format_player_scouting_data(df_combined)

        # Ausgabe
        st.dataframe(df_disp, width="stretch", hide_index=True)
