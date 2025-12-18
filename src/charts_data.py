from __future__ import annotations

import pandas as pd


def freq_top_df(freq_df: pd.DataFrame, top: int = 20) -> pd.DataFrame:
    # Espera colunas: dezena, frequencia
    d = freq_df.sort_values("frequencia", ascending=False).head(top).copy()
    d["dezena"] = d["dezena"].astype(str)
    d = d.set_index("dezena")[["frequencia"]]
    return d


def atraso_top_df(atraso_df: pd.DataFrame, top: int = 20) -> pd.DataFrame:
    # Espera colunas: dezena, atraso_atual (e possivelmente frequencia)
    d = atraso_df.sort_values("atraso_atual", ascending=False).head(top).copy()
    d["dezena"] = d["dezena"].astype(str)
    d = d.set_index("dezena")[["atraso_atual"]]
    return d


def soma_series_df(dfs: pd.DataFrame, last_n: int = 200) -> pd.DataFrame:
    # Espera colunas: concurso, soma
    d = dfs.sort_values("concurso").tail(last_n).copy()
    d = d.set_index("concurso")[["soma"]]
    return d
