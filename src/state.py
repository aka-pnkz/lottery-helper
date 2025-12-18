from __future__ import annotations

import streamlit as st
import pandas as pd

from .config import Modalidade
from .models import GameInfo

HIST_KEY = "history_by_mod"
GAMES_KEY = "games_info"  # list[GameInfo]

def init_state() -> None:
    st.session_state.setdefault(HIST_KEY, {})
    st.session_state.setdefault(GAMES_KEY, [])

def get_history(mod: Modalidade) -> pd.DataFrame | None:
    return st.session_state[HIST_KEY].get(mod)

def set_history(mod: Modalidade, df: pd.DataFrame) -> None:
    st.session_state[HIST_KEY][mod] = df

def clear_history(mod: Modalidade) -> None:
    st.session_state[HIST_KEY].pop(mod, None)

def get_games_info() -> list[GameInfo]:
    return st.session_state[GAMES_KEY]

def set_games_info(games: list[GameInfo]) -> None:
    st.session_state[GAMES_KEY] = games

def clear_games() -> None:
    st.session_state[GAMES_KEY] = []
