import streamlit as st
import pandas as pd

from .analytics import frequencias, atraso, padroes_par_impar_baixa_alta, somas

@st.cache_data(show_spinner=False, ttl=60 * 60)  # 1h
def cached_frequencias(df: pd.DataFrame, n_dezenas: int, n_universo: int) -> pd.DataFrame:
    return frequencias(df, n_dezenas, n_universo)

@st.cache_data(show_spinner=False, ttl=60 * 60)
def cached_atraso(freq_df: pd.DataFrame, df: pd.DataFrame, n_dezenas: int, n_universo: int) -> pd.DataFrame:
    return atraso(freq_df, df, n_dezenas, n_universo)

@st.cache_data(show_spinner=False, ttl=60 * 60)
def cached_padroes(df: pd.DataFrame, n_dezenas: int, limite_baixo: int):
    return padroes_par_impar_baixa_alta(df, n_dezenas, limite_baixo)

@st.cache_data(show_spinner=False, ttl=60 * 60)
def cached_somas(df: pd.DataFrame, n_dezenas: int):
    return somas(df, n_dezenas)
