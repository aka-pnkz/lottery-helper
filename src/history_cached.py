from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import Modalidade
from src.data_caixa import load_history_from_caixa


@st.cache_data(ttl=3600, show_spinner=False)
def load_history_cached(modalidade: Modalidade) -> pd.DataFrame:
    return load_history_from_caixa(modalidade)
