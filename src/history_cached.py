from __future__ import annotations

import streamlit as st
import pandas as pd

from src.data_caixa import load_history_from_caixa
from src.config import Modalidade


@st.cache_data(ttl=3600, show_spinner=False)
def load_history_cached(modalidade: Modalidade) -> pd.DataFrame:
    """
    Cacheia o histórico por 1h (ttl=3600) para evitar rebaixar/reprocessar em reruns. [web:7]
    """
    return load_history_from_caixa(modalidade)
