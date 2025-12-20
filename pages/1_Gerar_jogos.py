from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.analytics_cached import cached_frequencias
from src.config import Modalidade, get_spec
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
from src.games_export import games_info_to_df
from src.history_cached import load_history_cached
from src.models import GameInfo
from src.reports import (
    build_html_report,
    df_to_csv_bytes,
    df_to_json_bytes,
    df_to_md_bytes,
    make_zip_bytes,
)
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
from src.ui_pagination import paginate_df
from src.ui_table_prefs import df_show, table_prefs_sidebar

st.set_page_config(page_title="Gerar jogos", page_icon="🎲", layout="wide")
init_state()

# --------------------------
# Dialogs (confirmação)
# --------------------------
@st.dialog("Confirmar ação")
def confirm_dialog(action_key: str, message: str):
    st.write(message)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Confirmar", type="primary"):
            st.session_state[action_key] = True
            st.rerun()
    with c2:
        if st.button("Cancelar"):
            st.session_state[action_key] = False
            st.rerun()


# --------------------------
# Sidebar
# --------------------------
st.sidebar.title("Configurações")

modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

with st.sidebar.expander("Ações", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Recarregar"):
            confirm_dialog("confirm_reload", "Recarregar histórico e limpar jogos gerados?")
    with c2:
        if st.button("Limpar jogos"):
            confirm_dialog("confirm_clear_games", "Deseja limpar todos os jogos gerados nesta sessão?")

if st.session_state.get("confirm_reload") is True:
    st.session_state["confirm_reload"] = None
    clear_history(modalidade)
    clear_games()
    st.toast("Recarregado", icon="✅")
    st.rerun()

if st.session_state.get("confirm_clear_games") is True:
    st.session_state["confirm_clear_games"] = None
    clear_games()
    st.toast("Jogos limpos", icon="🧹")
    st.rerun()

height = table_prefs_sidebar(prefix="gerar")

with st.sidebar.expander("Filtros (básico)", expanded=False):
    fixas_txt = st.text_input("Dezenas fixas", placeholder="Ex: 10, 11, 12")
    proib_txt = st.text_input("Dezenas proibidas", placeholder="Ex: 1, 2, 3")

    soma_min = st.number_input("Soma mínima", min_value=0, max_value=2000, value=0, step=1)
    soma_max = st.number_input("Soma máxima", min_value=0, max_value=2000, value=0, step=1)

    # key fixo para o widget (ajuda em reruns)
    orcamento_max = st.number_input(
        "Orçamento máximo",
        min_value=0.0,
        max_value=1_000_000.0,
        value=0.0,
        step=10.0,
        key="orcamento_max",
        help="Ao informar um orçamento, a quantidade de jogos é calculada automaticamente.",
    )

dezenas_fixas = parse_lista(fixas_txt)
dezenas_proib = parse_lista(proib_txt)

soma_min_val = int(soma_min) if soma_min > 0 else None
soma_max_val = int(soma_max) if soma_max > 0 else None

if soma_min_val is not None and soma_max_val is not None and soma_min_val > soma_max_val:
    st.sidebar.warning("Soma mínima > soma máxima. Ignorando filtros de soma.")
    soma_min_val, soma_max_val = None, None

with st.sidebar.expander("Filtros (heurísticas)", expanded=False):
    max_rep_ultimo = st.number_input(
        "Máx. repetidas do último",
        min_value=0,
        max_value=spec.n_dezenas_sorteio,
        value=spec.n_dezenas_sorteio,
        step=1,
    )

    pares_min = st.number_input("Pares mín", min_value=0, max_value=spec.n_dezenas_sorteio, value=0, step=1)
    pares_max = st.number_input("Pares máx", min_value=0, max_value=spec.n_dezenas_sorteio, value=spec.n_dezenas_sorteio, step=1)

    primos_min = st.number_input("Primos mín", min_value=0, max_value=spec.n_dezenas_sorteio, value=0, step=1)
    primos_max = st.number_input("Primos máx", min_value=0, max_value=spec.n_dezenas_sorteio, value=spec.n_dezenas_sorteio, step=1)

    baixos_min = st.number_input("Baixos mín", min_value=0, max_value=spec.n_dezenas_sorteio, value=0, step=1)
    baixos_max = st.number_input("Baixos máx", min_value=0, max_value=spec.n_dezenas_sorteio, value=spec.n_dezenas_sorteio, step=1)

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
        with st.spinner("Carregando histórico..."):
            try:
                df = load_history_cached(modalidade)
            except Exception as e:
                st.error(f"Falha ao baixar/ler histórico: {e}")
                st.stop()

    set_history(modalidade, df)
    st.toast("Histórico carregado", icon="✅")

freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)
last_row = df.sort_values("concurso").iloc[-1]
dezenas_ult = {int(last_row[f"d{i}"]) for i in range(1, spec.n_dezenas_sorteio + 1)}

header_cards(
    spec,
    df,
    extra_right=f"Aposta base: {money_ptbr(spec.preco_base)} | Jogo: {spec.n_min}–{spec.n_max} dezenas",
)
st.divider()

# --------------------------
# Filtros combinados
# --------------------------
def passa_heuristicas(j: list[int]) -> bool:
    pares, _ = pares_impares(j)
    if pares < int(pares_min) or pares > int(pares_max):
        return False

    primos = contar_primos(j)
    if primos < int(primos_min) or primos > int(primos_max):
        return False

    baixos, _ = baixos_altos(j, spec.limite_baixo)
    if baixos < int(baixos_min) or baixos > int(baixos_max):
        return False

    rep = len(set(j) & dezenas_ult)
    if rep > int(max_rep_ultimo):
        return False

    return True


def filtro_total(j: list[int]) -> bool:
    if not filtrar_jogo(j, dezenas_fixas, dezenas_proib, soma_min_val, soma_max_val):
        return False
    return passa_heuristicas(j)


# --------------------------
# Geração
# --------------------------
modo = st.radio("Modo de geração", ["Uma estratégia", "Misto"], horizontal=True)
estrategias = ["Aleatório puro", "Balanceado par/ímpar", "Quentes/Frias/Mix", "Sem sequências longas"]

gerar = False
gerar_misto = False

games_info = get_games_info()
usar_orcamento = float(orcamento_max) > 0

if modo == "Uma estratégia":
    estrategia = st.selectbox("Estratégia", estrategias)

    tam = st.slider("Dezenas por jogo", spec.n_min, spec.n_max, spec.n_min, key="tam_uma")

    custo_jogo = float(preco_aposta(int(tam), int(spec.n_min), float(spec.preco_base)))
    if usar_orcamento and custo_jogo > 0:
        qtd_calc = int(float(orcamento_max) // custo_jogo)
        qtd_calc = max(1, min(500, qtd_calc))
    else:
        qtd_calc = 10

    qtd = st.number_input(
        "Quantidade de jogos",
        min_value=1,
        max_value=500,
        value=int(qtd_calc),
        step=1,
        key="qtd_uma",
        disabled=usar_orcamento,
        help="Com orçamento informado, a quantidade é calculada automaticamente.",
    )

    if usar_orcamento:
        st.caption(
            f"Orçamento: {money_ptbr(float(orcamento_max))} | "
            f"Custo/jogo: {money_ptbr(custo_jogo)} | "
            f"Qtd máx: {int(qtd)}"
        )

    q_quentes = q_frias = q_neutras = 0
    limite_seq = 3

    if estrategia == "Quentes/Frias/Mix":
        c1, c2, c3 = st.columns(3)
        q_quentes = c1.number_input("Quentes", 0, int(tam), min(5, int(tam)))
        q_frias = c2.number_input("Frias", 0, int(tam), min(5, int(tam)))
        q_neutras = c3.number_input("Neutras", 0, int(tam), max(0, int(tam) - int(q_quentes) - int(q_frias)))

    if estrategia == "Sem sequências longas":
        limite_seq = st.slider("Máx. sequência", 2, min(10, int(tam)), 3)

    gerar = st.button("Gerar", type="primary")

else:
    tam = st.slider("Dezenas por jogo", spec.n_min, spec.n_max, spec.n_min, key="tam_misto")

    jm: dict[str, int] = {}
    jm["Aleatório puro"] = st.number_input("Aleatório puro", 0, 500, 2, 1)
    jm["Balanceado par/ímpar"] = st.number_input("Balanceado par/ímpar", 0, 500, 2, 1, key="mix_bal")

    mix_q_quentes = mix_q_frias = mix_q_neutras = 0
    mix_limite_seq = 3

    with st.expander("Quentes/Frias/Mix"):
        jm["Quentes/Frias/Mix"] = st.number_input("Quentes/Frias/Mix", 0, 500, 2, 1)
        c1, c2, c3 = st.columns(3)
        mix_q_quentes = c1.number_input("Quentes (misto)", 0, int(tam), min(5, int(tam)))
        mix_q_frias = c2.number_input("Frias (misto)", 0, int(tam), min(5, int(tam)))
        mix_q_neutras = c3.number_input(
            "Neutras (misto)", 0, int(tam), max(0, int(tam) - int(mix_q_quentes) - int(mix_q_frias))
        )

    with st.expander("Sem sequências longas"):
        jm["Sem sequências longas"] = st.number_input("Sem sequências longas", 0, 500, 2, 1)
        mix_limite_seq = st.slider("Máx. sequência (misto)", 2, min(10, int(tam)), 3)

    gerar_misto = st.button("Gerar misto", type="primary")

# --------------------------
# Execução geração
# --------------------------
if modo == "Uma estratégia" and gerar:
    with st.status("Gerando jogos...", expanded=False) as status:
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

        jogos = [j for j in jogos if filtro_total(j)]
        games_info = [GameInfo(jogo_id=i, estrategia=estrategia, dezenas=j) for i, j in enumerate(jogos, start=1)]

        status.update(label=f"Gerados {len(games_info)} jogos", state="complete")
        st.toast(f"Gerados {len(games_info)} jogos", icon="🎲")

if modo == "Misto" and gerar_misto:
    with st.status("Gerando jogos (misto)...", expanded=False) as status:
        itens: list[tuple[str, list[int]]] = []

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

        filtrados = [(estrat, j) for (estrat, j) in itens if filtro_total(j)]
        games_info = [GameInfo(jogo_id=i, estrategia=estrat, dezenas=j) for i, (estrat, j) in enumerate(filtrados, start=1)]

        status.update(label=f"Gerados {len(games_info)} jogos (misto)", state="complete")
        st.toast(f"Gerados {len(games_info)} jogos (misto)", icon="🎲")

# orçamento (corta a lista para caber no orçamento)
if (gerar or gerar_misto) and games_info and float(orcamento_max) > 0:
    dentro: list[GameInfo] = []
    custo_acum = 0.0

    for gi in games_info:
        c = float(preco_aposta(len(gi.dezenas), spec.n_min, spec.preco_base))
        if custo_acum + c > float(orcamento_max):
            break
        custo_acum += c
        dentro.append(gi)

    games_info = dentro
    st.toast(f"Aplicado orçamento: {len(games_info)} jogos mantidos", icon="💰")

if gerar or gerar_misto:
    set_games_info(games_info)

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["Jogos", "Tabela/Exportar", "Relatório"])

with tab1:
    if not games_info:
        st.info("Gere jogos para exibir.")
    else:
        jogos = [gi.dezenas for gi in games_info]
        ct = custo_total(jogos, spec.n_min, spec.preco_base)
        p = prob_premio_maximo_aprox(jogos, spec.n_min, spec.comb_target)
        chance_txt = ("NA" if p <= 0 else f"1 em {1/p:,.0f}".replace(",", "."))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Jogos", len(games_info))
        m2.metric("Custo estimado", money_ptbr(ct))
        m3.metric("Chance aprox.", chance_txt)
        m4.metric("Média dezenas/jogo", f"{sum(len(j) for j in jogos) / len(jogos):.1f}")

        preview = games_info[:100]
        if len(games_info) > 100:
            st.caption("Mostrando os 100 primeiros jogos. Use a aba Tabela/Exportar para paginação/CSV.")

        for gi in preview:
            st.code(f"{gi.jogo_id:02d} - {gi.estrategia} - {formatar_jogo(gi.dezenas)}")

with tab2:
    if not games_info:
        st.info("Sem dados.")
    else:
        df_out_all = games_info_to_df(games_info, limite_baixo=spec.limite_baixo, dezenas_ult=dezenas_ult)

        st.subheader("Tabela (paginada)")
        df_page = paginate_df(df_out_all, key="gerar_out", default_page_size=50)
        df_show(st, df_page, height=height)

        st.download_button(
            "Baixar CSV (completo)",
            data=df_to_csv_bytes(df_out_all),
            file_name=f"jogos_{spec.modalidade}_{datetime.now().date()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

with tab3:
    if not games_info:
        st.info("Gere jogos para habilitar o relatório.")
    else:
        df_out_all = games_info_to_df(games_info, limite_baixo=spec.limite_baixo, dezenas_ult=dezenas_ult)

        jogos = [gi.dezenas for gi in games_info]
        ct = custo_total(jogos, spec.n_min, spec.preco_base)
        p = prob_premio_maximo_aprox(jogos, spec.n_min, spec.comb_target)
        chance_txt = ("NA" if p <= 0 else f"1 em {1/p:,.0f}".replace(",", "."))

        resumo = {
            "Modalidade": spec.modalidade,
            "Jogos": str(len(games_info)),
            "Custo estimado": money_ptbr(ct),
            "Chance aprox.": chance_txt,
            "Dezenas/jogo": f"{min(len(j) for j in jogos)}–{max(len(j) for j in jogos)}",
        }

        filtros_txt = {
            "Fixas": fixas_txt or "-",
            "Proibidas": proib_txt or "-",
            "Soma": f"{soma_min_val or '-'}..{soma_max_val or '-'}",
            "Orçamento": money_ptbr(orcamento_max) if orcamento_max else "-",
            "Máx rep. último": str(int(max_rep_ultimo)),
            "Pares": f"{int(pares_min)}..{int(pares_max)}",
            "Primos": f"{int(primos_min)}..{int(primos_max)}",
            "Baixos": f"{int(baixos_min)}..{int(baixos_max)}",
        }

        by_estrat = (
            df_out_all.groupby("estrategia", as_index=True)
            .agg(
                qtd=("jogo_id", "count"),
                soma_media=("soma", "mean"),
                rep_ultimo_media=("rep_ultimo", "mean"),
            )
            .sort_values("qtd", ascending=False)
        )

        st.subheader("Downloads")
        html_bytes = build_html_report(
            title="Lottery Helper - Relatório de Jogos",
            subtitle=f"{spec.modalidade} (jogos gerados)",
            generated_at=datetime.now(),
            summary={**resumo, **{f"Filtro: {k}": v for k, v in filtros_txt.items()}},
            tables=[
                ("Resumo por estratégia", by_estrat.reset_index()),
                ("Jogos (amostra)", df_out_all.head(50)),
            ],
        )

        md_bytes = df_to_md_bytes(
            title="Relatório de Jogos",
            dfs=[
                ("Resumo", pd.DataFrame([resumo])),
                ("Filtros", pd.DataFrame([filtros_txt])),
                ("Resumo por estratégia", by_estrat.reset_index()),
                ("Jogos (Top 50)", df_out_all.head(50)),
            ],
            max_rows=200,
        )

        zip_bytes = make_zip_bytes(
            [
                (f"relatorio_jogos_{spec.modalidade}.html", html_bytes),
                (f"jogos_{spec.modalidade}.csv", df_to_csv_bytes(df_out_all)),
                (f"estrategias_{spec.modalidade}.csv", df_to_csv_bytes(by_estrat.reset_index())),
                (f"relatorio_jogos_{spec.modalidade}.md", md_bytes),
                (f"jogos_{spec.modalidade}.json", df_to_json_bytes(df_out_all)),
            ]
        )

        st.download_button(
            "Baixar tudo (ZIP)",
            data=zip_bytes,
            file_name=f"bundle_jogos_{spec.modalidade}_{datetime.now().date()}.zip",
            mime="application/zip",
            use_container_width=True,
        )