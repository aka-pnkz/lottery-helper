from __future__ import annotations

import streamlit as st

from src.analytics_cached import cached_frequencias
from src.config import Modalidade, get_spec
from src.history_cached import load_history_cached
from src.state import init_state, get_history, set_history, clear_history
from src.ui_pagination import paginate_df
from src.ui_table_prefs import table_prefs_sidebar, df_show

st.set_page_config(page_title="Debug", page_icon="🛠️", layout="wide")
init_state()

st.title("Debug / Diagnóstico")

modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

with st.sidebar.expander("Ações", expanded=True):
    if st.button("Recarregar histórico (limpar cache de sessão)"):
        clear_history(modalidade)
        st.rerun()

height = table_prefs_sidebar(prefix="debug")

df = get_history(modalidade)
if df is None:
    with st.status("Carregando histórico...", expanded=False) as status:
        try:
            df = load_history_cached(modalidade)
        except Exception as e:
            status.update(label="Falha ao carregar histórico", state="error", expanded=True)
            st.exception(e)
            st.stop()
        set_history(modalidade, df)
        status.update(label="Histórico carregado", state="complete")
        st.toast("Histórico carregado", icon="✅")

st.divider()

tab1, tab2, tab3 = st.tabs(["Histórico", "Frequências", "Sanity checks"])

with tab1:
    st.subheader("Histórico (paginado)")
    df_sorted = df.sort_values("concurso", ascending=False)
    df_page = paginate_df(df_sorted, key="dbg_hist", default_page_size=50)
    df_show(st, df_page, height=height)

with tab2:
    st.subheader("Frequência (paginado)")
    freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo).sort_values("frequencia", ascending=False)
    df_show(st, paginate_df(freq_df, key="dbg_freq", default_page_size=50), height=height)

with tab3:
    st.subheader("Checagens rápidas")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Linhas", len(df))
    c2.metric("Concurso min", int(df["concurso"].min()))
    c3.metric("Concurso max", int(df["concurso"].max()))
    c4.metric("Universo", f"1–{spec.n_universo}")

    # Último sorteio
    st.markdown("### Último sorteio")
    last = df.sort_values("concurso").iloc[-1]
    dezenas = [int(last[f"d{i}"]) for i in range(1, spec.n_dezenas_sorteio + 1)]
    st.write({"concurso": int(last["concurso"]), "data": str(last["data"]), "dezenas": sorted(dezenas)})
