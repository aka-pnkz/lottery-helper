from __future__ import annotations

from io import BytesIO
import traceback

import pandas as pd
import streamlit as st

from src.config import Modalidade, URL_LOTOFACIL_DOWNLOAD, URL_MEGA_DOWNLOAD, get_spec
from src.data_caixa import load_history_from_caixa
from src.http_client import get_session
from src.state import (
    init_state,
    get_history,
    set_history,
    clear_history,
    get_games_info,
    clear_games,
)

st.set_page_config(page_title="Debug", page_icon="🛠️", layout="wide")
init_state()

st.title("Debug / Diagnóstico")

# --------------------------
# Controls
# --------------------------
modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

st.sidebar.markdown("### Ações")
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Rebaixar histórico"):
        with st.sidebar:
            with st.spinner("Baixando e normalizando..."):
                try:
                    df = load_history_from_caixa(modalidade)
                except Exception as e:
                    st.error("Falha ao baixar/normalizar histórico.")
                    st.exception(e)
                    st.stop()
                set_history(modalidade, df)
        st.success("Histórico carregado na sessão.")
        st.rerun()

with c2:
    if st.button("Limpar sessão"):
        clear_history(modalidade)
        clear_games()
        st.rerun()

st.sidebar.markdown("### Opções")
mostrar_state = st.sidebar.toggle("Mostrar st.session_state (sanitizado)", value=False)
mostrar_excel_cols = st.sidebar.toggle("Inspecionar colunas do XLSX", value=True)
baixar_raw = st.sidebar.toggle("Testar download raw (requests)", value=True)

# --------------------------
# Helpers
# --------------------------
def _url_da_modalidade(mod: Modalidade) -> str:
    return URL_MEGA_DOWNLOAD if mod == "Mega-Sena" else URL_LOTOFACIL_DOWNLOAD


def _sanitize_state(d: dict) -> dict:
    # evita despejar DataFrames enormes no debug
    out = {}
    for k, v in d.items():
        if isinstance(v, pd.DataFrame):
            out[k] = f"<DataFrame shape={v.shape}>"
        elif isinstance(v, (list, tuple)) and len(v) > 200:
            out[k] = f"<{type(v).__name__} len={len(v)}>"
        else:
            out[k] = v
    return out


def _peek_excel_columns(buf: BytesIO) -> dict:
    # Sem assumir nomes: apenas lista sheets e colunas detectadas (amostra)
    buf.seek(0)
    xls = pd.ExcelFile(buf)
    info = {"sheets": {}}
    for sheet in xls.sheet_names[:5]:
        tmp = pd.read_excel(xls, sheet_name=sheet, nrows=5)
        info["sheets"][sheet] = {
            "columns": list(tmp.columns),
            "sample_rows": tmp.head(3).to_dict(orient="records"),
        }
    return info


# --------------------------
# Cards do contexto
# --------------------------
url = _url_da_modalidade(modalidade)

a1, a2, a3, a4 = st.columns(4)
a1.metric("Modalidade", spec.modalidade)
a2.metric("Universo", f"1–{spec.n_universo}")
a3.metric("Dezenas sorteio", spec.n_dezenas_sorteio)
a4.metric("URL fonte", "CAIXA (XLSX)")

st.caption(url)

st.divider()

# --------------------------
# Teste de download (raw)
# --------------------------
if baixar_raw:
    st.subheader("1) Teste de download (raw)")
    with st.spinner("Baixando XLSX via requests..."):
        try:
            r = get_session().get(url, timeout=60)
            status = r.status_code
            size = len(r.content or b"")
            ctype = r.headers.get("Content-Type", "")
        except Exception as e:
            st.error("Falha no download raw.")
            st.exception(e)
            st.stop()

    b1, b2, b3 = st.columns(3)
    b1.metric("HTTP status", status)
    b2.metric("Tamanho (bytes)", size)
    b3.metric("Content-Type", ctype if ctype else "NA")

    if status != 200:
        st.warning("Status diferente de 200. Pode ser bloqueio/rate limit/redirect.")
        st.json({"headers": dict(r.headers)})

    if size < 50_000:
        st.warning("Arquivo muito pequeno para um histórico completo; pode ter vindo HTML/erro no lugar do XLSX.")

    if mostrar_excel_cols:
        st.subheader("1.1) Colunas do XLSX (amostra)")
        try:
            info = _peek_excel_columns(BytesIO(r.content))
            st.json(info)
        except Exception as e:
            st.error("Falha ao inspecionar XLSX (pode não ser um Excel válido).")
            st.exception(e)

    st.divider()

# --------------------------
# Histórico normalizado na sessão
# --------------------------
st.subheader("2) Histórico normalizado (DataFrame da sessão)")

df = get_history(modalidade)
if df is None:
    st.info("Sem histórico carregado na sessão. Clique em 'Rebaixar histórico'.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Linhas", len(df))
c2.metric("Colunas", len(df.columns))
c3.metric("Concurso min", int(df["concurso"].min()))
c4.metric("Concurso max", int(df["concurso"].max()))

st.caption(f"Data min: {df['data'].min().date()} | Data max: {df['data'].max().date()}")

with st.expander("Colunas do DF"):
    st.write(list(df.columns))

with st.expander("Amostra (tail)"):
    st.dataframe(df.tail(30), width="stretch")

# --------------------------
# Sanidade: dezenas
# --------------------------
st.subheader("3) Checks de sanidade")

dezenas_cols = [f"d{i}" for i in range(1, spec.n_dezenas_sorteio + 1)]
faltando = [c for c in dezenas_cols if c not in df.columns]

if faltando:
    st.error(f"Colunas de dezenas faltando no DF: {faltando}")
else:
    ok_range = True
    for c in dezenas_cols:
        if not df[c].between(1, spec.n_universo).all():
            ok_range = False
            break

    s1, s2, s3 = st.columns(3)
    s1.metric("Colunas dezenas OK", "SIM" if not faltando else "NÃO")
    s2.metric("Faixa (1..universo)", "SIM" if ok_range else "NÃO")
    s3.metric("Duplicadas por concurso", int(df["concurso"].duplicated().sum()))

    if not ok_range:
        st.warning("Há dezenas fora do intervalo esperado. Verifique normalização do XLSX.")

# --------------------------
# Estado e jogos
# --------------------------
st.subheader("4) Estado / Jogos")

games_info = get_games_info()
g1, g2 = st.columns(2)
g1.metric("Jogos na sessão", len(games_info))
g2.metric("Keys session_state", len(st.session_state.keys()))

if mostrar_state:
    st.write("st.session_state (sanitizado):")
    st.json(_sanitize_state(dict(st.session_state)))

with st.expander("Jogos (amostra)"):
    if not games_info:
        st.info("Sem jogos gerados.")
    else:
        # Mostra só os primeiros 20
        rows = []
        for gi in games_info[:20]:
            rows.append({"jogo_id": gi.jogo_id, "estrategia": gi.estrategia, "dezenas": gi.dezenas})
        st.dataframe(pd.DataFrame(rows), width="stretch")

# --------------------------
# Área para exceção manual
# --------------------------
st.subheader("5) Execução segura (teste)")
st.caption("Use este botão para forçar uma execução completa de download+normalização e ver o erro detalhado aqui (sem depender só do log).")

if st.button("Rodar teste completo"):
    with st.spinner("Executando teste completo..."):
        try:
            df_test = load_history_from_caixa(modalidade)
            st.success(f"OK: histórico lido e normalizado (shape={df_test.shape}).")
            st.dataframe(df_test.tail(10), width="stretch")
        except Exception as e:
            st.error("Erro no teste completo.")
            st.exception(e)
            st.code(traceback.format_exc())
