import streamlit as st
import numpy as np
import pandas as pd

from src.config import get_spec, Modalidade
from src.state import init_state, get_history, set_history, get_games, set_games
from src.data_caixa import load_history_from_caixa
from src.ui import money_ptbr, parse_lista, validar_dezenas
from src.analytics import frequencias
from src.domain_lottery import (
    gerar_aleatorio_puro,
    gerar_balanceado_par_impar,
    gerar_quentes_frias_mix,
    gerar_sem_sequencias,
    filtrar_jogo,
    preco_aposta,
    custo_total,
    prob_premio_maximo_aprox,
    pares_impares,
    baixos_altos,
    contar_primos,
    formatar_jogo,
)
from src.ui_theme import apply_theme
apply_theme()


st.set_page_config(page_title="Gerar jogos", page_icon="🎲", layout="wide")
init_state()

st.title("Gerar jogos")

modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

df = get_history(modalidade)
if df is None:
    with st.sidebar.spinner("Baixando histórico..."):
        df = load_history_from_caixa(modalidade)
        set_history(modalidade, df)

freq_df = frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)

st.sidebar.markdown("### Filtros (opcional)")
fixas_txt = st.sidebar.text_input("Dezenas fixas", placeholder="Ex: 10, 11, 12")
proib_txt = st.sidebar.text_input("Dezenas proibidas", placeholder="Ex: 1, 2, 3")
soma_min = st.sidebar.number_input("Soma mínima", min_value=0, max_value=1000, value=0, step=1)
soma_max = st.sidebar.number_input("Soma máxima", min_value=0, max_value=1000, value=0, step=1)
orcamento_max = st.sidebar.number_input("Orçamento máximo", min_value=0.0, max_value=1_000_000.0, value=0.0, step=10.0)

dezenas_fixas = parse_lista(fixas_txt)
dezenas_proib = parse_lista(proib_txt)

soma_min_val = int(soma_min) if soma_min > 0 else None
soma_max_val = int(soma_max) if soma_max > 0 else None
if soma_min_val is not None and soma_max_val is not None and soma_min_val > soma_max_val:
    st.sidebar.warning("Soma mínima > soma máxima. Ignorando soma.")
    soma_min_val, soma_max_val = None, None

try:
    validar_dezenas(dezenas_fixas, spec.n_universo, "Fixas")
    validar_dezenas(dezenas_proib, spec.n_universo, "Proibidas")
    conflito = set(dezenas_fixas) & set(dezenas_proib)
    if conflito:
        raise ValueError(f"Conflito fixas/proibidas: {sorted(conflito)}")
except ValueError as e:
    st.error(str(e))
    st.stop()

colA, colB = st.columns(2)
with colA:
    st.subheader("Histórico")
    st.metric("Total de concursos", len(df))
    st.caption(f"Concurso max: {int(df['concurso'].max())} | Data max: {df['data'].max().date()}")

with colB:
    st.subheader("Parâmetros")
    st.write(f"- Universo: 1–{spec.n_universo}")
    st.write(f"- Aposta base: {money_ptbr(spec.preco_base)}")
    if dezenas_fixas:
        st.write(f"- Fixas: {sorted(dezenas_fixas)}")
    if dezenas_proib:
        st.write(f"- Proibidas: {sorted(dezenas_proib)}")
    if orcamento_max > 0:
        st.write(f"- Orçamento: {money_ptbr(orcamento_max)}")

st.divider()

modo = st.radio("Modo de geração", ["Uma estratégia", "Misto"])
gerar = False
gerar_misto = False

estrategias = ["Aleatório puro", "Balanceado par/ímpar", "Quentes/Frias/Mix", "Sem sequências longas"]

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
    jm["Balanceado par/ímpar"] = st.number_input("Balanceado par/ímpar", 0, 500, 2, 1)
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

# estado atual
jogos, jogos_info = get_games()

# geração
if modo == "Uma estratégia" and gerar:
    if estrategia == "Aleatório puro":
        jogos = gerar_aleatorio_puro(int(qtd), int(tam), spec.n_universo)
    elif estrategia == "Balanceado par/ímpar":
        jogos = gerar_balanceado_par_impar(int(qtd), int(tam), spec.n_universo)
    elif estrategia == "Quentes/Frias/Mix":
        jogos = gerar_quentes_frias_mix(int(qtd), int(tam), freq_df, spec.n_universo, (int(q_quentes), int(q_frias), int(q_neutras)))
    else:
        jogos = gerar_sem_sequencias(int(qtd), int(tam), spec.n_universo, int(limite_seq))

    jogos = [j for j in jogos if filtrar_jogo(j, dezenas_fixas, dezenas_proib, soma_min_val, soma_max_val)]
    jogos_info = [{"estrategia": estrategia, "jogo": j} for j in jogos]

if modo == "Misto" and gerar_misto:
    jogos_info = []
    if jm.get("Aleatório puro", 0) > 0:
        js = gerar_aleatorio_puro(int(jm["Aleatório puro"]), int(tam), spec.n_universo)
        jogos_info.extend({"estrategia": "Aleatório puro", "jogo": j} for j in js)
    if jm.get("Balanceado par/ímpar", 0) > 0:
        js = gerar_balanceado_par_impar(int(jm["Balanceado par/ímpar"]), int(tam), spec.n_universo)
        jogos_info.extend({"estrategia": "Balanceado par/ímpar", "jogo": j} for j in js)
    if jm.get("Quentes/Frias/Mix", 0) > 0:
        js = gerar_quentes_frias_mix(int(jm["Quentes/Frias/Mix"]), int(tam), freq_df, spec.n_universo, (int(mix_q_quentes), int(mix_q_frias), int(mix_q_neutras)))
        jogos_info.extend({"estrategia": "Quentes/Frias/Mix", "jogo": j} for j in js)
    if jm.get("Sem sequências longas", 0) > 0:
        js = gerar_sem_sequencias(int(jm["Sem sequências longas"]), int(tam), spec.n_universo, int(mix_limite_seq))
        jogos_info.extend({"estrategia": "Sem sequências longas", "jogo": j} for j in js)

    jogos_info = [info for info in jogos_info if filtrar_jogo(info["jogo"], dezenas_fixas, dezenas_proib, soma_min_val, soma_max_val)]
    jogos = [info["jogo"] for info in jogos_info]

# orçamento
if (gerar or gerar_misto) and jogos and orcamento_max > 0:
    dentro = []
    custo_acum = 0.0
    for info in jogos_info:
        c = preco_aposta(len(info["jogo"]), spec.n_min, spec.preco_base)
        if custo_acum + c > float(orcamento_max):
            break
        custo_acum += c
        dentro.append(info)
    jogos_info = dentro
    jogos = [info["jogo"] for info in jogos_info]

if (gerar or gerar_misto):
    set_games(jogos, jogos_info)

tab1, tab2 = st.tabs(["Jogos", "Tabela/Exportar"])

with tab1:
    if not jogos:
        st.info("Gere jogos para exibir.")
    else:
        ct = custo_total(jogos, spec.n_min, spec.preco_base)
        p = prob_premio_maximo_aprox(jogos, spec.n_min, spec.comb_target)
        c1, c2, c3 = st.columns(3)
        c1.metric("Jogos", len(jogos))
        c2.metric("Custo estimado", money_ptbr(ct))
        c3.metric("Chance aprox. prêmio máximo", ("NA" if p <= 0 else f"1 em {1/p:,.0f}".replace(",", ".")))

        for i, info in enumerate(jogos_info, start=1):
            st.code(f"{i:02d} - {info['estrategia']} - {formatar_jogo(info['jogo'])}")

with tab2:
    if not jogos:
        st.info("Sem dados.")
    else:
        # dezenas do último concurso para repetição
        last = df.iloc[-1]
        dezenas_ult = {int(last[f"d{i}"]) for i in range(1, spec.n_dezenas_sorteio + 1)}

        rows = []
        for idx, info in enumerate(jogos_info, start=1):
            j = sorted(info["jogo"])
            r = {"jogo_id": idx, "estrategia": info["estrategia"]}
            for k, d in enumerate(j, start=1):
                r[f"d{k}"] = int(d)

            soma = sum(j)
            pares, imp = pares_impares(j)
            bax, alt = baixos_altos(j, spec.limite_baixo)
            primos = contar_primos(j)
            rep = len(set(j) & dezenas_ult)

            r.update({"soma": soma, "pares": pares, "impares": imp, "baixos": bax, "altos": alt, "nprimos": primos, "rep_ultimo": rep})
            rows.append(r)

        df_out = pd.DataFrame(rows)
        st.dataframe(df_out, use_container_width=True)
        st.download_button("Baixar CSV", df_out.to_csv(index=False).encode("utf-8"), file_name=f"jogos_{spec.modalidade}.csv", mime="text/csv")
