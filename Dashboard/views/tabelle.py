import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

from utils import cached_get_tabelle, SAISON_OPTIONS, calculate_dataframe_height


def show():
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
                tabelle = cached_get_tabelle(saisons[0])  # ← RICHTIG!
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
                    tabelle = cached_get_tabelle(saison)  # ← RICHTIG!

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
