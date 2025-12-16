import streamlit as st
from src.config import get_spec, Modalidade
from src.state import init_state, get_history, set_history
from src.data_caixa import load_history_from_caixa
from src.analytics import frequencias, atraso, padroes_par_impar_baixa_alta, somas
from src.ui_theme import apply_theme
apply_theme()


st.set_page_config(page_title="Análises", page_icon="📊", layout="wide")
init_state()

st.title("Análises estatísticas")
modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

df = get_history(modalidade)
if df is None:
    with st.sidebar.spinner("Baixando histórico..."):
        df = load_history_from_caixa(modalidade)
        set_history(modalidade, df)

freq_df = frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)
atraso_df = atraso(freq_df, df, spec.n_dezenas_sorteio, spec.n_universo)

tab1, tab2, tab3, tab4 = st.tabs(["Frequência/Atraso", "Padrões", "Somas", "Últimos"])

with tab1:
    c1, c2 = st.columns(2)
    c1.dataframe(freq_df.sort_values("frequencia", ascending=False), use_container_width=True)
    c2.dataframe(atraso_df.sort_values(["atraso_atual", "frequencia"], ascending=[False, False]), use_container_width=True)

with tab2:
    dfp, dist_pi, dist_ba = padroes_par_impar_baixa_alta(df, spec.n_dezenas_sorteio, spec.limite_baixo)
    st.dataframe(dist_pi, use_container_width=True)
    st.dataframe(dist_ba, use_container_width=True)
    with st.expander("Detalhado por concurso"):
        st.dataframe(dfp.sort_values("concurso"), use_container_width=True)

with tab3:
    dfs, dist = somas(df, spec.n_dezenas_sorteio)
    c1, c2 = st.columns(2)
    c1.dataframe(dfs.sort_values("concurso"), use_container_width=True)
    c2.dataframe(dist, use_container_width=True)

with tab4:
    qtd = st.slider("Quantidade", 5, 50, 10, 5)
    ult = df.sort_values("concurso", ascending=False).head(qtd).sort_values("concurso")
    st.dataframe(ult, use_container_width=True)
