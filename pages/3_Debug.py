import streamlit as st

from src.config import Modalidade
from src.state import init_state, get_history, set_history, clear_history
from src.data_caixa import load_history_from_caixa
from src.ui_status import sidebar_spinner

st.set_page_config(page_title="Debug", page_icon="🛠️", layout="wide")
init_state()

st.title("Debug / Diagnóstico")

modalidade: Modalidade = st.radio("Modalidade", ["Mega-Sena", "Lotofácil"])

col1, col2 = st.columns(2)
with col1:
    if st.button("Rebaixar histórico agora"):
        with st.spinner("Baixando histórico..."):
            try:
                df = load_history_from_caixa(modalidade)
            except Exception as e:
                st.error(f"Falha: {e}")
                st.stop()
            set_history(modalidade, df)
        st.success("Recarregado.")
        st.rerun()

with col2:
    if st.button("Limpar histórico da sessão"):
        clear_history(modalidade)
        st.rerun()

df = get_history(modalidade)
if df is None:
    st.info("Sem histórico na sessão. Use 'Rebaixar histórico agora'.")
    st.stop()

st.subheader("Checklist")
st.write("Linhas:", len(df))
st.write("Concurso min/max:", int(df["concurso"].min()), int(df["concurso"].max()))
st.write("Data min/max:", df["data"].min(), df["data"].max())

st.subheader("Amostra")
st.dataframe(df.tail(30), use_container_width=True)

with st.sidebar:
    with st.expander("Teste spinner sidebar"):
        if st.button("Spinner no sidebar (teste)"):
            with sidebar_spinner("Teste..."):
                pass
            st.sidebar.success("OK")
