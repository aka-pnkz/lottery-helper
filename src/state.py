import streamlit as st
import pandas as pd
from .config import Modalidade

HIST_KEY = "history_by_mod"
GAMES_KEY = "jogos"
GAMES_INFO_KEY = "jogos_info"

def init_state() -> None:
    st.session_state.setdefault(HIST_KEY, {})      # {modalidade: df}
    st.session_state.setdefault(GAMES_KEY, [])     # list[list[int]]
    st.session_state.setdefault(GAMES_INFO_KEY, [])# list[dict]

def get_history(mod: Modalidade) -> pd.DataFrame | None:
    return st.session_state[HIST_KEY].get(mod)

def set_history(mod: Modalidade, df: pd.DataFrame) -> None:
    st.session_state[HIST_KEY][mod] = df

def clear_history(mod: Modalidade) -> None:
    st.session_state[HIST_KEY].pop(mod, None)

def clear_games() -> None:
    st.session_state[GAMES_KEY] = []
    st.session_state[GAMES_INFO_KEY] = []

def get_games():
    return st.session_state[GAMES_KEY], st.session_state[GAMES_INFO_KEY]

def set_games(jogos, jogos_info) -> None:
    st.session_state[GAMES_KEY] = jogos
    st.session_state[GAMES_INFO_KEY] = jogos_info
