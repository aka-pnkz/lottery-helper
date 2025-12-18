from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.analytics_cached import cached_frequencias
from src.config import Modalidade, get_spec
from src.data_caixa import load_history_from_caixa
from src.domain_lottery import (
    baixos_altos,
    contar_primos,
    custo_total,
    filtrar_jogo,
    formatar_jogo,
    gerar_aleatorio_puro,
    gerar_balanceado_par_impar,
    gerar_quentes_frias_mix,
    gerar_sem_sequencias,
    pares_impares,
    preco_aposta,
    prob_premio_maximo_aprox,
)
from src.models import GameInfo
from src.state import (
    clear_games,
    clear_history,
    get_games_info,
    get_history,
    init_state,
    set_games_info,
    set_history,
)
from src.ui import money_ptbr, parse_lista, validar_dezenas
from src.ui_components import header_cards
from src.ui_table_prefs import table_prefs_sidebar

st.set_page_config(page_title="Gerar jogos", page_icon="🎲", layout="wide")
init_state()

# --------------------------
# Sidebar
# --------------------------
st.sidebar.title("Configurações")
modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

st.sidebar.markdown("### Ações")
a1, a2 = st.sidebar.columns(2)
with a1:
    if st.button("Recarregar"):
        clear_history(modalidade)
        clear_games()
        st.rerun()
with a2:
    if st.button("Limpar jogos"):
        clear_games()
        st.rerun()

height_px, top_n = table_prefs_sidebar(prefix="gerar")

st.sidebar.markdown("### Filtros (opcional)")
fixas_txt = st.sidebar.text_input("Dezenas fixas", placeholder="Ex: 10, 11, 12")
proib_txt = st.sidebar.text_input("Dezenas proibidas", placeholder="Ex: 1, 2, 3")
soma_min = st.sidebar.number_input("Soma mínima", min_value=0, max_value=2000, value=0, step=1)
soma_max = st.sidebar.number_input("Soma máxima", min_value=0, max_value=2000, value=0, step=1)
orcamento_max = st.sidebar.number_input("Orçamento máximo", min_value=0.0, max_value=1_000_000.0, value=0.0, step=10.0)

dezenas_fixas = parse_lista(fixas_txt)
dezenas_proib = parse_lista(proib_txt)

soma_min_val = int(soma_min) if soma_min > 0 else None
soma_max_val = int(soma_max) if soma_max > 0 else None
if soma_min_val is not None and soma_max_val is not None and soma_min_val > soma_max_val:
    st.sidebar.warning("Soma mínima > soma máxima. Ignorando filtros de soma.")
    soma_min_val, soma_max_val = None, None

try:
    validar_dezenas(dezenas_fixas, spec.n_universo, "Fixas")
    validar_dezenas(dezenas_proib, spec.n_universo, "Proibidas")
    conflito = set(dezenas_fixas) & set(dezenas_proib)
    if conflito:
        raise ValueError(f"Conflito fixas/proibidas: {sorted(conflito)}")
except ValueError as e:
    st.sidebar.error(str(e))
    st.stop()

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

freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)

last_row = df.iloc[-1]
dezenas_ult = {int(last_row[f"d{i}"]) for i in range(1, spec.n_dezenas_sorteio + 1)}

# --------------------------
# Header
# --------------------------
header_cards(
    spec,
    df,
    extra_right=f"Aposta base: {money_ptbr(spec.preco_base)} | Jogo: {spec.n_min}–{spec.n_max} dezenas",
)
st.divider()

# --------------------------
# Geração
# --------------------------
modo = st.radio("Modo de geração", ["Uma estratégia", "Misto"], horizontal=True)
estrategias = ["Aleatório puro", "Balanceado par/ímpar", "Quentes/Frias/Mix", "Sem sequências longas"]

gerar = False
gerar_misto = False

if modo == "Uma estratégia":
    estrategia = st.selectbox("Estratégia", estrategias)
    qtd = st.number_input("Quantidade de jogos", min_value=1, max_value=500, value=10, step=1)
    tam = st.slider("Dezenas por jogo", spec.n_min, spec.n_max, spec.n_min)

    q_quentes = q_frias = q_neutras = 0
    limite_seq = 3

    if estrategia == "Quentes/Frias/Mix":
        c1, c2, c3 = st.columns(3)
        q_quentes = c1.number_input("Quentes", 0, tam, min(5, tam))
        q_frias = c2.number_input("Frias", 0, tam, min(5, tam))
        q_neutras = c3.number_input("Neutras", 0, tam, max(0, tam - q_quentes - q_frias))

    if estrategia == "Sem sequências longas":
        limite_seq = st.slider("Máx. sequência", 2, min(10, tam), 3)

    gerar = st.button("Gerar", type="primary")

else:
    tam = st.slider("Dezenas por jogo", spec.n_min, spec.n_max, spec.n_min, key="tam_misto")

    jm = {}
    jm["Aleatório puro"] = st.number_input("Aleatório puro", 0, 500, 2, 1)
    jm["Balanceado par/ímpar"] = st.number_input("Balanceado par/ímpar", 0, 500, 2, 1, key="mix_bal")

    with st.expander("Quentes/Frias/Mix"):
        jm["Quentes/Frias/Mix"] = st.number_input("Quentes/Frias/Mix", 0, 500, 2, 1)
        c1, c2, c3 = st.columns(3)
        mix_q_quentes = c1.number_input("Quentes (misto)", 0, tam, min(5, tam))
        mix_q_frias = c2.number_input("Frias (misto)", 0, tam, min(5, tam))
        mix_q_neutras = c3.number_input("Neutras (misto)", 0, tam, max(0, tam - mix_q_quentes - mix_q_frias))

    with st.expander("Sem sequências longas"):
        jm["Sem sequências longas"] = st.number_input("Sem sequências longas", 0, 500, 2, 1)
        mix_limite_seq = st.slider("Máx. sequência (misto)", 2, min(10, tam), 3)

    gerar_misto = st.button("Gerar misto", type="primary")

games_info = get_games_info()

if modo == "Uma estratégia" and gerar:
    if estrategia == "Aleatório puro":
        jogos = gerar_aleatorio_puro(int(qtd), int(tam), spec.n_universo)
    elif estrategia == "Balanceado par/ímpar":
        jogos = gerar_balanceado_par_impar(int(qtd), int(tam), spec.n_universo)
    elif estrategia == "Quentes/Frias/Mix":
        jogos = gerar_quentes_frias_mix(
            int(qtd),
            int(tam),
            freq_df,
            spec.n_universo,
            (int(q_quentes), int(q_frias), int(q_neutras)),
        )
    else:
        jogos = gerar_sem_sequencias(int(qtd), int(tam), spec.n_universo, int(limite_seq))

    jogos = [j for j in jogos if filtrar_jogo(j, dezenas_fixas, dezenas_proib, soma_min_val, soma_max_val)]
    games_info = [GameInfo(jogo_id=i, estrategia=estrategia, dezenas=j) for i, j in enumerate(jogos, start=1)]

if modo == "Misto" and gerar_misto:
    itens = []

    if jm.get("Aleatório puro", 0) > 0:
        jogos = gerar_aleatorio_puro(int(jm["Aleatório puro"]), int(tam), spec.n_universo)
        itens += [("Aleatório puro", j) for j in jogos]

    if jm.get("Balanceado par/ímpar", 0) > 0:
        jogos = gerar_balanceado_par_impar(int(jm["Balanceado par/ímpar"]), int(tam), spec.n_universo)
        itens += [("Balanceado par/ímpar", j) for j in jogos]

    if jm.get("Quentes/Frias/Mix", 0) > 0:
        jogos = gerar_quentes_frias_mix(
            int(jm["Quentes/Frias/Mix"]),
            int(tam),
            freq_df,
            spec.n_universo,
            (int(mix_q_quentes), int(mix_q_frias), int(mix_q_neutras)),
        )
        itens += [("Quentes/Frias/Mix", j) for j in jogos]

    if jm.get("Sem sequências longas", 0) > 0:
        jogos = gerar_sem_sequencias(int(jm["Sem sequências longas"]), int(tam), spec.n_universo, int(mix_limite_seq))
        itens += [("Sem sequências longas", j) for j in jogos]

    filtrados = [(estrat, j) for (estrat, j) in itens if filtrar_jogo(j, dezenas_fixas, dezenas_proib, soma_min_val, soma_max_val)]
    games_info = [GameInfo(jogo_id=i, estrategia=estrat, dezenas=j) for i, (estrat, j) in enumerate(filtrados, start=1)]

# orçamento
if (gerar or gerar_misto) and games_info and orcamento_max > 0:
    dentro: list[GameInfo] = []
    custo_acum = 0.0
    for gi in games_info:
        c = preco_aposta(len(gi.dezenas), spec.n_min, spec.preco_base)
        if custo_acum + c > float(orcamento_max):
            break
        custo_acum += c
        dentro.append(gi)
    games_info = dentro

if (gerar or gerar_misto):
    set_games_info(games_info)

# --------------------------
# Tabs
# --------------------------
tab1, tab2 = st.tabs(["Jogos", "Tabela/Exportar"])

with tab1:
    if not games_info:
        st.info("Gere jogos para exibir.")
    else:
        jogos = [gi.dezenas for gi in games_info]
        ct = custo_total(jogos, spec.n_min, spec.preco_base)
        p = prob_premio_maximo_aprox(jogos, spec.n_min, spec.comb_target)
        chance_txt = ("NA" if p <= 0 else f"1 em {1/p:,.0f}".replace(",", "."))

        m1, m2, m3, m4
