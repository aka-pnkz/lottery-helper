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

st.set_page_config(page_title="Análises", page_icon="📊", layout="wide")
init_state()

st.title("Análises estatísticas")

# --------------------------
# Sidebar
# --------------------------
modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

st.sidebar.markdown("### Ações")
if st.sidebar.button("Recarregar histórico"):
    clear_history(modalidade)
    st.rerun()

st.sidebar.markdown("### Visual")
altura_tabela = st.sidebar.slider("Altura das tabelas (px)", 250, 900, 420, 10)
top_n = st.sidebar.slider("Top N (tabelas resumidas)", 10, 100, 20, 5)
ver_tudo = st.sidebar.toggle("Ver tudo (ignora Top N)", value=False)

# --------------------------
# Histórico
# --------------------------
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

# Header padrão (cards)
header_cards(
    spec,
    df,
    extra_right="Dica: use 'Top N' e 'Altura' para deixar a página mais leve.",
)

st.divider()

# --------------------------
# Derivados (cacheados)
# --------------------------
freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)
atraso_df = cached_atraso(freq_df, df, spec.n_dezenas_sorteio, spec.n_universo)

tab1, tab2, tab3, tab4 = st.tabs(["Frequência/Atraso", "Padrões", "Somas", "Últimos"])

# --------------------------
# Tab 1: Frequência/Atraso
# --------------------------
with tab1:
    c1, c2 = st.columns(2)

    # Frequência
    freq_sorted = freq_df.sort_values("frequencia", ascending=False)
    if not ver_tudo:
        freq_sorted = freq_sorted.head(top_n)

    c1.subheader("Frequência (total)")
    c1.dataframe(freq_sorted, width="stretch", height=altura_tabela)

    # Atraso
    atraso_sorted = atraso_df.sort_values(["atraso_atual", "frequencia"], ascending=[False, False])
    if not ver_tudo:
        atraso_sorted = atraso_sorted.head(top_n)

    c2.subheader("Atraso atual")
    c2.dataframe(atraso_sorted, width="stretch", height=altura_tabela)

    st.markdown("### Frequência recente vs total")
    nrec = st.slider("Concursos recentes", min_value=20, max_value=300, value=50, step=10)

    df_recent = df.sort_values("concurso", ascending=False).head(nrec)
    freq_recent = cached_frequencias(df_recent, spec.n_dezenas_sorteio, spec.n_universo).rename(
        columns={"frequencia": "freq_recente"}
    )

    merge = freq_df.merge(freq_recent, on="dezena", how="left")
    merge["freq_recente"] = merge["freq_recente"].fillna(0).astype(int)

    # Top por recente e por total
    rec_sorted = merge.sort_values("freq_recente", ascending=False)
    tot_sorted = merge.sort_values("frequencia", ascending=False)

    if not ver_tudo:
        rec_sorted = rec_sorted.head(top_n)
        tot_sorted = tot_sorted.head(top_n)

    c3, c4 = st.columns(2)
    c3.subheader("Top por recente")
    c3.dataframe(rec_sorted, width="stretch", height=altura_tabela)

    c4.subheader("Top por total")
    c4.dataframe(tot_sorted, width="stretch", height=altura_tabela)

# --------------------------
# Tab 2: Padrões
# --------------------------
with tab2:
    dfp, dist_pi, dist_ba = cached_padroes(df, spec.n_dezenas_sorteio, spec.limite_baixo)

    # Cards rápidos
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("P/I mais comum", f"{int(dist_pi.iloc[0]['pares'])}/{int(dist_pi.iloc[0]['impares'])}" if len(dist_pi) else "NA")
    m2.metric("Qtd (P/I top)", int(dist_pi.iloc[0]["qtd"]) if len(dist_pi) else 0)
    m3.metric("B/A mais comum", f"{int(dist_ba.iloc[0]['baixos'])}/{int(dist_ba.iloc[0]['altos'])}" if len(dist_ba) else "NA")
    m4.metric("Qtd (B/A top)", int(dist_ba.iloc[0]["qtd"]) if len(dist_ba) else 0)

    c1, c2 = st.columns(2)

    c1.subheader("Par/Ímpar (distribuição)")
    pi_view = dist_pi if ver_tudo else dist_pi.head(top_n)
    c1.dataframe(pi_view, width="stretch", height=altura_tabela)

    c2.subheader("Baixa/Alta (distribuição)")
    ba_view = dist_ba if ver_tudo else dist_ba.head(top_n)
    c2.dataframe(ba_view, width="stretch", height=altura_tabela)

    with st.expander("Detalhado por concurso (pode ser pesado)"):
        st.dataframe(dfp.sort_values("concurso"), width="stretch", height=altura_tabela)

# --------------------------
# Tab 3: Somas
# --------------------------
with tab3:
    dfs, dist = cached_somas(df, spec.n_dezenas_sorteio)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Soma min", int(dfs["soma"].min()))
    s2.metric("Soma média", f"{dfs['soma'].mean():.1f}")
    s3.metric("Soma max", int(dfs["soma"].max()))
    s4.metric("Faixas", int(dist["faixa_soma"].nunique()) if "faixa_soma" in dist.columns else 0)

    c1, c2 = st.columns(2)
    c1.subheader("Soma por concurso")
    soma_view = dfs.sort_values("concurso")
    # aqui não faz muito sentido "top_n" (é série temporal), então limitamos por "últimos N"
    ult_n = st.slider("Últimos concursos (soma)", 50, 500, 200, 25)
    soma_view = soma_view.tail(ult_n)
    c1.dataframe(soma_view, width="stretch", height=altura_tabela)

    c2.subheader("Distribuição por faixa")
    c2.dataframe(dist, width="stretch", height=altura_tabela)

# --------------------------
# Tab 4: Últimos
# --------------------------
with tab4:
    qtd = st.slider("Quantidade", 5, 80, 15, 5)
    ult = df.sort_values("concurso", ascending=False).head(qtd).sort_values("concurso")

    u1, u2 = st.columns(2)
    u1.metric("Exibindo concursos", qtd)
    u2.metric("Concurso max (exibido)", int(ult["concurso"].max()))

    st.dataframe(ult, width="stretch", height=altura_tabela)
