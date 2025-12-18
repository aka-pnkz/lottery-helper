from __future__ import annotations

import streamlit as st

from src.analytics_cached import (
    cached_atraso,
    cached_frequencias,
    cached_padroes,
    cached_somas,
)
from src.config import Modalidade, get_spec
from src.data_caixa import load_history_from_caixa
from src.state import init_state, get_history, set_history, clear_history
from src.ui_components import header_cards
from src.ui_table_prefs import table_prefs_sidebar, df_show

st.set_page_config(page_title="Análises", page_icon="📊", layout="wide")
init_state()

st.title("Análises estatísticas")

modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

st.sidebar.markdown("### Ações")
if st.sidebar.button("Recarregar histórico"):
    clear_history(modalidade)
    st.rerun()

height, top_n = table_prefs_sidebar(prefix="analises")

df = get_history(modalidade)
if df is None:
    with st.sidebar:
        with st.spinner("Baixando histórico..."):
            try:
                df = load_history_from_caixa(modalidade)
            except Exception as e:
                st.error(f"Falha ao baixar/ler histórico: {e}")
                st.stop()
            set_history(modalidade, df)

header_cards(spec, df, extra_right="Dica: ‘Tudo’ pode ficar pesado; use Top 50/Top 100 na maioria dos casos.")
st.divider()

freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)
atraso_df = cached_atraso(freq_df, df, spec.n_dezenas_sorteio, spec.n_universo)

tab1, tab2, tab3, tab4 = st.tabs(["Frequência/Atraso", "Padrões", "Somas", "Últimos"])

with tab1:
    c1, c2 = st.columns(2)

    freq_sorted = freq_df.sort_values("frequencia", ascending=False)
    if top_n is not None:
        freq_sorted = freq_sorted.head(top_n)
    c1.subheader("Frequência (total)")
    df_show(c1, freq_sorted, height=height)

    atraso_sorted = atraso_df.sort_values(["atraso_atual", "frequencia"], ascending=[False, False])
    if top_n is not None:
        atraso_sorted = atraso_sorted.head(top_n)
    c2.subheader("Atraso atual")
    df_show(c2, atraso_sorted, height=height)

    st.markdown("### Frequência recente vs total")
    nrec = st.slider("Concursos recentes", min_value=20, max_value=300, value=50, step=10)

    df_recent = df.sort_values("concurso", ascending=False).head(nrec)
    freq_recent = cached_frequencias(df_recent, spec.n_dezenas_sorteio, spec.n_universo).rename(columns={"frequencia": "freq_recente"})

    merge = freq_df.merge(freq_recent, on="dezena", how="left")
    merge["freq_recente"] = merge["freq_recente"].fillna(0).astype(int)

    rec_sorted = merge.sort_values("freq_recente", ascending=False)
    tot_sorted = merge.sort_values("frequencia", ascending=False)
    if top_n is not None:
        rec_sorted = rec_sorted.head(top_n)
        tot_sorted = tot_sorted.head(top_n)

    c3, c4 = st.columns(2)
    c3.subheader("Top por recente")
    df_show(c3, rec_sorted, height=height)
    c4.subheader("Top por total")
    df_show(c4, tot_sorted, height=height)

with tab2:
    dfp, dist_pi, dist_ba = cached_padroes(df, spec.n_dezenas_sorteio, spec.limite_baixo)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("P/I mais comum", f"{int(dist_pi.iloc[0]['pares'])}/{int(dist_pi.iloc[0]['impares'])}" if len(dist_pi) else "NA")
    m2.metric("Qtd (P/I top)", int(dist_pi.iloc[0]["qtd"]) if len(dist_pi) else 0)
    m3.metric("B/A mais comum", f"{int(dist_ba.iloc[0]['baixos'])}/{int(dist_ba.iloc[0]['altos'])}" if len(dist_ba) else "NA")
    m4.metric("Qtd (B/A top)", int(dist_ba.iloc[0]["qtd"]) if len(dist_ba) else 0)

    c1, c2 = st.columns(2)
    pi_view = dist_pi if top_n is None else dist_pi.head(top_n)
    ba_view = dist_ba if top_n is None else dist_ba.head(top_n)

    c1.subheader("Par/Ímpar (distribuição)")
    df_show(c1, pi_view, height=height)

    c2.subheader("Baixa/Alta (distribuição)")
    df_show(c2, ba_view, height=height)

    with st.expander("Detalhado por concurso (pode ser pesado)"):
        df_show(st, dfp.sort_values("concurso"), height=height)

with tab3:
    dfs, dist = cached_somas(df, spec.n_dezenas_sorteio)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Soma min", int(dfs["soma"].min()))
    s2.metric("Soma média", f"{dfs['soma'].mean():.1f}")
    s3.metric("Soma max", int(dfs["soma"].max()))
    s4.metric("Faixas", int(dist["faixa_soma"].nunique()) if "faixa_soma" in dist.columns else 0)

    c1, c2 = st.columns(2)
    c1.subheader("Soma por concurso (últimos N)")
    ult_n = st.selectbox("Últimos concursos", options=[50, 100, 200, 300, 500], index=2)
    soma_view = dfs.sort_values("concurso").tail(int(ult_n))
    df_show(c1, soma_view, height=height)

    c2.subheader("Distribuição por faixa")
    df_show(c2, dist, height=height)

with tab4:
    qtd = st.selectbox("Quantidade", options=[10, 15, 20, 30, 50, 80], index=1)
    ult = df.sort_values("concurso", ascending=False).head(int(qtd)).sort_values("concurso")
    df_show(st, ult, height=height)
