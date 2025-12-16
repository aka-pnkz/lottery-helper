import streamlit as st
from src.config import get_spec, Modalidade
from src.state import init_state, get_history, set_history, clear_history
from src.data_caixa import load_history_from_caixa

st.set_page_config(page_title="Lottery Helper", page_icon="🎰", layout="wide")

init_state()

st.title("Lottery Helper")
st.caption("Multipage nativo com lógica separada em src/ e histórico in-memory por sessão.")

modalidade: Modalidade = st.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

col1, col2 = st.columns(2)
with col1:
    if st.button("Baixar/Recarregar histórico"):
        clear_history(modalidade)
        st.rerun()

with col2:
    if st.button("Forçar download agora"):
        df = load_history_from_caixa(modalidade)
        set_history(modalidade, df)
        st.rerun()

df = get_history(modalidade)
if df is None:
    with st.spinner("Baixando histórico da Caixa..."):
        df = load_history_from_caixa(modalidade)
        set_history(modalidade, df)

st.subheader("Checklist da base")
st.write("Total de concursos (linhas):", len(df))
st.write("Concurso min/max:", int(df["concurso"].min()), int(df["concurso"].max()))
st.write("Data min/max:", df["data"].min().date(), df["data"].max().date())

st.info("Use as páginas no menu lateral: Gerar jogos, Análises e Debug.")
