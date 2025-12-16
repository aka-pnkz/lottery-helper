import pandas as pd
import streamlit as st

from src.analytics import atraso, frequencias, padroes_par_impar_baixa_alta, somas
from src.config import Modalidade, get_spec
from src.data_caixa import load_history_from_caixa
from src.state import clear_history, get_history, init_state, set_history

st.set_page_config(page_title="Análises", page_icon="📊", layout="wide")
init_state()


@st.cache_data(show_spinner=False, ttl=60 * 60)
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


st.title("Análises estatísticas")

modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

st.sidebar.markdown("### Ações")
if st.sidebar.button("Recarregar histórico (página)"):
    clear_history(modalidade)
    st.rerun()

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

# Cards do histórico
c1, c2, c3, c4 = st.columns(4)
c1.metric("Concursos (hist)", len(df))
c2.metric("Concurso max", int(df["concurso"].max()))
c3.metric("Data do último", str(df["data"].max().date()))
c4.metric("Universo", f"1–{spec.n_universo}")

st.divider()

freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)
atraso_df = cached_atraso(freq_df, df, spec.n_dezenas_sorteio, spec.n_universo)

tab1, tab2, tab3, tab4 = st.tabs(["Frequência/Atraso", "Padrões", "Somas", "Últimos"])

with tab1:
    c1, c2 = st.columns(2)
    c1.subheader("Frequência (total)")
    c1.dataframe(freq_df.sort_values("frequencia", ascending=False), width="stretch")

    c2.subheader("Atraso atual")
    c2.dataframe(
        atraso_df.sort_values(["atraso_atual", "frequencia"], ascending=[False, False]),
        width="stretch",
    )

    st.markdown("### Frequência recente vs total")
    nrec = st.slider("Concursos recentes", min_value=20, max_value=300, value=50, step=10)
    df_recent = df.sort_values("concurso", ascending=False).head(nrec)
    freq_recent = cached_frequencias(df_recent, spec.n_dezenas_sorteio, spec.n_universo).rename(columns={"frequencia": "freq_recente"})
    merge = freq_df.merge(freq_recent, on="dezena", how="left")
    merge["freq_recente"] = merge["freq_recente"].fillna(0).astype(int)

    c3, c4 = st.columns(2)
    c3.dataframe(merge.sort_values("freq_recente", ascending=False).head(20), width="stretch")
    c4.dataframe(merge.sort_values("frequencia", ascending=False).head(20), width="stretch")

with tab2:
    dfp, dist_pi, dist_ba = cached_padroes(df, spec.n_dezenas_sorteio, spec.limite_baixo)

    # Cards rápidos
    a1, a2, a3, a4 = st.columns(4)
    # melhor “padrão” = o mais frequente (top 1)
    a1.metric("Padrão P/I mais comum", f"{int(dist_pi.iloc[0]['pares'])}/{int(dist_pi.iloc[0]['impares'])}" if len(dist_pi) else "NA")
    a2.metric("Qtd (P/I top)", int(dist_pi.iloc[0]["qtd"]) if len(dist_pi) else 0)
    a3.metric("Padrão B/A mais comum", f"{int(dist_ba.iloc[0]['baixos'])}/{int(dist_ba.iloc[0]['altos'])}" if len(dist_ba) else "NA")
    a4.metric("Qtd (B/A top)", int(dist_ba.iloc[0]["qtd"]) if len(dist_ba) else 0)

    st.subheader("Par/Ímpar")
    st.dataframe(dist_pi, width="stretch")
    st.subheader("Baixa/Alta")
    st.dataframe(dist_ba, width="stretch")

    with st.expander("Detalhado por concurso"):
        st.dataframe(dfp.sort_values("concurso"), width="stretch")

with tab3:
    dfs, dist = cached_somas(df, spec.n_dezenas_sorteio)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Soma min", int(dfs["soma"].min()))
    s2.metric("Soma média", f"{dfs['soma'].mean():.1f}")
    s3.metric("Soma max", int(dfs["soma"].max()))
    s4.metric("Faixas", dist["faixa_soma"].nunique())

    c1, c2 = st.columns(2)
    c1.subheader("Soma por concurso")
    c1.dataframe(dfs.sort_values("concurso"), width="stretch")
    c2.subheader("Distribuição por faixa")
    c2.dataframe(dist, width="stretch")

with tab4:
    qtd = st.slider("Quantidade", 5, 50, 10, 5)
    ult = df.sort_values("concurso", ascending=False).head(qtd).sort_values("concurso")

    u1, u2 = st.columns(2)
    u1.metric("Exibindo concursos", qtd)
    u2.metric("Concurso (último exibido)", int(ult["concurso"].max()))

    st.dataframe(ult, width="stretch")
