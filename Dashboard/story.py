import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from utils import TABS

from Statistiken.extract_statistiken import get_marktwerte as _get_marktwerte
from views.tabelle import show as show_tabelle
from views.spielplan import show as show_spielplan
from views.team_analyse import show as show_team_analyse
from views.team_vergleiche import show as show_team_vergleiche
from views.spieler_marktwert import show as show_spieler_marktwert
from views.spieler_scouting import show as show_spieler_scouting


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
st.markdown("---")
# Session State für aktive View
if "statistik_view" not in st.session_state:
    st.session_state.statistik_view = "Tabelle"

# Session State initialisieren
if "statistik_view" not in st.session_state:
    st.session_state.statistik_view = "Tabelle"

# Tabs aus utils verwenden
cols = st.columns(len(TABS))

for col, (label, view_name) in zip(cols, TABS):
    with col:
        button_text = f"🔴 {label}" if st.session_state.statistik_view == view_name else f"⚪ {label}"

        if st.button(
                button_text,
                key=f"tab_{view_name}",
                use_container_width=True,
                help=f"Gehe zu {label}"
        ):
            st.session_state.statistik_view = view_name
            st.rerun()

st.markdown("---")
statistik_view = st.session_state.statistik_view




# ============================================================================
# ROUTER - ZEIGE AKTIVE VIEW
# ============================================================================

if statistik_view == "Tabelle":
    show_tabelle()
elif statistik_view == "Spielplan":
    show_spielplan()
elif statistik_view == "Team-Analyse":
    show_team_analyse()
elif statistik_view == "Team-Vergleiche":
    show_team_vergleiche()
elif statistik_view == "Spieler-Marktwert":
    show_spieler_marktwert()
elif statistik_view == "Spieler-Scouting":
    show_spieler_scouting()


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "<small>Powered by Team JALT - Deployed im Rahmen der LV 'Business Intelligence' an der HWR Berlin </small>"
    "</div>",
    unsafe_allow_html=True
)
