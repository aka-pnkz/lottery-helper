import pandas as pd
import streamlit as st
from datetime import datetime

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
from src.state import (
    clear_games,
    clear_history,
    get_games,
    get_history,
    init_state,
    set_games,
    set_history,
)
from src.ui import money_ptbr, parse_lista, validar_dezenas

st.set_page_config(page_title="Gerar jogos", page_icon="🎲", layout="wide")
init_state()


# --------------------------
# Cache (apenas para acelerar UX)
# --------------------------
@st.cache_data(show_spinner=False, ttl=60 * 60)  # 1h
def cached_frequencias(df: pd.DataFrame, n_dezenas_sorteio: int, n_universo: int) -> pd.DataFrame:
    dezenas_cols = [f"d{i}" for i in range(1, n_dezenas_sorteio + 1)]
    todas = df[dezenas_cols].values.ravel()
    freq = (
        pd.Series(todas)
        .value_counts()
        .reindex(range(1, n_universo + 1), fill_value=0)
        .sort_index()
    )
    out = freq.reset_index()
    out.columns = ["dezena", "frequencia"]
    out["dezena"] = out["dezena"].astype(int)
    out["frequencia"] = out["frequencia"].astype(int)
    return out


@st.cache_data(show_spinner=False, ttl=60 * 60)
def cached_ultimos_concursos(df: pd.DataFrame, n: int = 100) -> list[int]:
    return df.sort_values("concurso", ascending=False)["concurso"].head(n).tolist()


def carregar_historico(modalidade: Modalidade) -> pd.DataFrame:
    df = get_history(modalidade)
    if df is not None:
        return df

    with st.sidebar:
        with st.spinner("Baixando histórico..."):
            try:
                df = load_history_from_caixa(modalidade)
            except Exception as e:
                st.error(f"Falha ao baixar/ler histórico: {e}")
                st.stop()
            set_history(modalidade, df)
            return df


def simular_acertos(jogos: list[list[int]], dezenas_sorteadas: list[int]) -> pd.DataFrame:
    s = set(dezenas_sorteadas)
    linhas = []
    for i, jogo in enumerate(jogos, start=1):
        linhas.append({"jogo_id": i, "jogo": formatar_jogo(jogo), "acertos": len(set(jogo) & s)})
    return pd.DataFrame(linhas)


# --------------------------
# Sidebar
# --------------------------
st.sidebar.title("Configurações")
modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

st.sidebar.markdown("### Ações")
cA, cB = st.sidebar.columns(2)
with cA:
    if st.button("Recarregar"):
        clear_history(modalidade)
        clear_games()
        st.rerun()
with cB:
    if st.button("Limpar jogos"):
        clear_games()
        st.rerun()

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
# Carrega histórico e derivados
# --------------------------
df = carregar_historico(modalidade)
freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)

# Dezenas do último concurso (para repetição)
last_row = df.iloc[-1]
dezenas_ult = {int(last_row[f"d{i}"]) for i in range(1, spec.n_dezenas_sorteio + 1)}


# --------------------------
# Header + Cards (UX)
# --------------------------
st.markdown(f"## {spec.modalidade} — Gerador de jogos")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Concursos (hist)", len(df))
c2.metric("Concurso max", int(df["concurso"].max()))
c3.metric("Data do último", str(df["data"].max().date()))
c4.metric("Aposta base", money_ptbr(spec.preco_base))

st.caption(
    f"Universo: 1–{spec.n_universo} | Jogo: {spec.n_min}–{spec.n_max} dezenas | "
    f"Fixas: {len(dezenas_fixas)} | Proibidas: {len(dezenas_proib)}"
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
        s1, s2, s3 = st.columns(3)
        q_quentes = s1.number_input("Quentes", 0, tam, min(5, tam))
        q_frias = s2.number_input("Frias", 0, tam, min(5, tam))
        q_neutras = s3.number_input("Neutras", 0, tam, max(0, tam - q_quentes - q_frias))

    if estrategia == "Sem sequências longas":
        limite_seq = st.slider("Máx. sequência", 2, min(10, tam), 3)

    gerar = st.button("Gerar", type="primary")

else:
    tam = st.slider("Dezenas por jogo", spec.n_min, spec.n_max, spec.n_min, key="tam_misto")

    st.markdown("### Quantidade por estratégia")
    jm = {
        "Aleatório puro": st.number_input("Aleatório puro", 0, 500, 2, 1),
        "Balanceado par/ímpar": st.number_input("Balanceado par/ímpar", 0, 500, 2, 1, key="mix_bal"),
    }

    with st.expander("Quentes/Frias/Mix"):
        jm["Quentes/Frias/Mix"] = st.number_input("Quentes/Frias/Mix", 0, 500, 2, 1)
        s1, s2, s3 = st.columns(3)
        mix_q_quentes = s1.number_input("Quentes (misto)", 0, tam, min(5, tam))
        mix_q_frias = s2.number_input("Frias (misto)", 0, tam, min(5, tam))
        mix_q_neutras = s3.number_input("Neutras (misto)", 0, tam, max(0, tam - mix_q_quentes - mix_q_frias))

    with st.expander("Sem sequências longas"):
        jm["Sem sequências longas"] = st.number_input("Sem sequências longas", 0, 500, 2, 1)
        mix_limite_seq = st.slider("Máx. sequência (misto)", 2, min(10, tam), 3)

    gerar_misto = st.button("Gerar misto", type="primary")

# Estado
jogos, jogos_info = get_games()

# Processa geração
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
        js = gerar_quentes_frias_mix(
            int(jm["Quentes/Frias/Mix"]),
            int(tam),
            freq_df,
            spec.n_universo,
            (int(mix_q_quentes), int(mix_q_frias), int(mix_q_neutras)),
        )
        jogos_info.extend({"estrategia": "Quentes/Frias/Mix", "jogo": j} for j in js)

    if jm.get("Sem sequências longas", 0) > 0:
        js = gerar_sem_sequencias(int(jm["Sem sequências longas"]), int(tam), spec.n_universo, int(mix_limite_seq))
        jogos_info.extend({"estrategia": "Sem sequências longas", "jogo": j} for j in js)

    jogos_info = [
        info for info in jogos_info
        if filtrar_jogo(info["jogo"], dezenas_fixas, dezenas_proib, soma_min_val, soma_max_val)
    ]
    jogos = [info["jogo"] for info in jogos_info]

# Orçamento
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


# --------------------------
# Tabs + Cards do pacote
# --------------------------
tab1, tab2, tab3 = st.tabs(["Jogos", "Tabela/Exportar", "Simulação"])

with tab1:
    if not jogos:
        st.info("Gere jogos para exibir.")
    else:
        ct = custo_total(jogos, spec.n_min, spec.preco_base)
        p = prob_premio_maximo_aprox(jogos, spec.n_min, spec.comb_target)

        # Cards do pacote
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Jogos", len(jogos))
        a2.metric("Custo estimado", money_ptbr(ct))
        a3.metric("Chance aprox.", ("NA" if p <= 0 else f"1 em {1/p:,.0f}".replace(",", ".")))
        a4.metric("Média dezenas/jogo", f"{sum(len(j) for j in jogos)/len(jogos):.1f}")

        for i, info in enumerate(jogos_info, start=1):
            st.code(f"{i:02d} - {info['estrategia']} - {formatar_jogo(info['jogo'])}")

with tab2:
    if not jogos:
        st.info("Sem dados.")
    else:
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

            r.update(
                {
                    "soma": soma,
                    "pares": pares,
                    "impares": imp,
                    "baixos": bax,
                    "altos": alt,
                    "nprimos": primos,
                    "rep_ultimo": rep,
                }
            )
            rows.append(r)

        df_out = pd.DataFrame(rows)

        # Mini-cards de resumo da tabela
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Soma média", f"{df_out['soma'].mean():.1f}")
        b2.metric("Pares médios", f"{df_out['pares'].mean():.1f}")
        b3.metric("Baixos médios", f"{df_out['baixos'].mean():.1f}")
        b4.metric("Rep. último (média)", f"{df_out['rep_ultimo'].mean():.1f}")

        st.dataframe(df_out, width="stretch")

        st.download_button(
            "Baixar CSV",
            df_out.to_csv(index=False).encode("utf-8"),
            file_name=f"jogos_{spec.modalidade}_{datetime.now().date()}.csv",
            mime="text/csv",
        )

with tab3:
    if not jogos:
        st.info("Gere jogos antes de simular.")
    else:
        st.subheader("Simular acertos")
        modo_sim = st.radio("Fonte do resultado", ["Concurso histórico", "Manual"], horizontal=True)

        dezenas_sorteadas: list[int] = []
        if modo_sim == "Concurso histórico":
            ultimos = cached_ultimos_concursos(df, 100)
            conc = st.selectbox("Escolha o concurso", ultimos, format_func=lambda x: f"Concurso {x}")
            linha = df.loc[df["concurso"] == conc].iloc[0]
            dezenas_sorteadas = [int(linha[f"d{i}"]) for i in range(1, spec.n_dezenas_sorteio + 1)]
            st.write("Dezenas:", " - ".join(f"{d:02d}" for d in dezenas_sorteadas))
        else:
            txt = st.text_input(
                f"Digite {spec.n_dezenas_sorteio} dezenas (vírgula/space/;)",
                placeholder="Ex: 05, 12, 23, ...",
            )
            dezenas_sorteadas = parse_lista(txt)
            if txt and len(dezenas_sorteadas) != spec.n_dezenas_sorteio:
                st.warning(f"Informe exatamente {spec.n_dezenas_sorteio} dezenas.")

        if len(dezenas_sorteadas) == spec.n_dezenas_sorteio:
            try:
                validar_dezenas(dezenas_sorteadas, spec.n_universo, "Resultado")
            except ValueError as e:
                st.error(str(e))
            else:
                dfsim = simular_acertos(jogos, dezenas_sorteadas)
                dist = dfsim["acertos"].value_counts().sort_index().reset_index()
                dist.columns = ["acertos", "qtd_jogos"]

                c1, c2 = st.columns([1, 2])
                c1.metric("Melhor acerto", int(dfsim["acertos"].max()))
                c1.metric("Média acertos", f"{dfsim['acertos'].mean():.2f}")
                c1.dataframe(dist, width="content")

                c2.dataframe(dfsim, width="stretch")
