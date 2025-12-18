from __future__ import annotations

import streamlit as st
import pandas as pd


def header_cards(spec, df: pd.DataFrame, extra_right: str | None = None) -> None:
    """
    Cards padrão do app (histórico), para reutilizar em todas as páginas.
    spec: objeto retornado por get_spec(modalidade)
    df: histórico normalizado
    """
    st.markdown(f"## {spec.modalidade}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Concursos", len(df))
    c2.metric("Concurso max", int(df["concurso"].max()))
    c3.metric("Data do último", str(df["data"].max().date()))
    c4.metric("Universo", f"1–{spec.n_universo}")

    if extra_right:
        st.caption(extra_right)


def pack_cards(*, spec, jogos_count: int, custo: float, chance_txt: str, media_dezenas: float) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jogos", jogos_count)
    c2.metric("Custo estimado", custo)
    c3.metric("Chance aprox.", chance_txt)
    c4.metric("Média dezenas/jogo", f"{media_dezenas:.1f}")
