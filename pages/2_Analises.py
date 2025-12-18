from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.analytics_cached import (
    cached_atraso,
    cached_frequencias,
    cached_padroes,
    cached_somas,
)
from src.charts_data import atraso_top_df, freq_top_df, soma_series_df
from src.config import Modalidade, get_spec
from src.history_cached import load_history_cached
from src.reports import build_html_report, df_to_csv_bytes, df_to_json_bytes, df_to_md_bytes
from src.state import clear_history, get_history, init_state, set_history
from src.ui_components import header_cards
from src.ui_pagination import paginate_df
from src.ui_table_prefs import df_show, table_prefs_sidebar

st.set_page_config(page_title="Análises", page_icon="📊", layout="wide")

init_state()

st.title("Análises estatísticas")

modalidade: Modalidade = st.sidebar.radio("Modalidade", ["Mega-Sena", "Lotofácil"])
spec = get_spec(modalidade)

with st.sidebar.expander("Ações", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Recarregar histórico"):
            clear_history(modalidade)
            st.toast("Histórico da sessão limpo", icon="🧹")
            st.rerun()
    with c2:
        if st.button("Limpar cache (global)"):
            st.cache_data.clear()
            st.toast("Cache limpo", icon="🧼")
            st.rerun()

height = table_prefs_sidebar(prefix="analises")

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

header_cards(spec, df, extra_right="Tabelas paginadas + gráficos com fragment + relatórios.")
st.divider()

freq_df = cached_frequencias(df, spec.n_dezenas_sorteio, spec.n_universo)
atraso_df = cached_atraso(freq_df, df, spec.n_dezenas_sorteio, spec.n_universo)
dfp, dist_pi, dist_ba = cached_padroes(df, spec.n_dezenas_sorteio, spec.limite_baixo)
dfs_soma, dist_soma = cached_somas(df, spec.n_dezenas_sorteio)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Frequência/Atraso", "Padrões", "Somas", "Últimos", "Gráficos/Relatório"]
)

with tab1:
    c1, c2 = st.columns(2)

    c1.subheader("Frequência (total)")
    df_show(
        c1,
        paginate_df(freq_df.sort_values("frequencia", ascending=False), key="anal_freq", default_page_size=50),
        height=height,
    )

    c2.subheader("Atraso atual")
    atraso_sorted = atraso_df.sort_values(["atraso_atual", "frequencia"], ascending=[False, False])
    df_show(c2, paginate_df(atraso_sorted, key="anal_atraso", default_page_size=50), height=height)

with tab2:
    c1, c2 = st.columns(2)

    c1.subheader("Par/Ímpar (distribuição)")
    df_show(c1, paginate_df(dist_pi, key="anal_pi", default_page_size=50), height=height)

    c2.subheader("Baixa/Alta (distribuição)")
    df_show(c2, paginate_df(dist_ba, key="anal_ba", default_page_size=50), height=height)

    with st.expander("Detalhado por concurso (pode ser pesado)"):
        df_show(st, paginate_df(dfp.sort_values("concurso"), key="anal_det", default_page_size=100), height=height)

with tab3:
    c1, c2 = st.columns(2)

    c1.subheader("Soma por concurso (últimos N)")
    ult_n = st.selectbox("Últimos concursos", options=[50, 100, 200, 300, 500], index=2, key="soma_lastn")
    soma_view = dfs_soma.sort_values("concurso").tail(int(ult_n))
    df_show(c1, soma_view, height=height)

    c2.subheader("Distribuição por faixa")
    df_show(c2, paginate_df(dist_soma, key="anal_dist_soma", default_page_size=50), height=height)

with tab4:
    qtd = st.selectbox("Quantidade", options=[10, 15, 20, 30, 50, 80], index=1, key="ult_qtd")
    ult = df.sort_values("concurso", ascending=False).head(int(qtd)).sort_values("concurso")
    df_show(st, ult, height=height)

with tab5:
    st.subheader("Configurações")
    c1, c2 = st.columns(2)

    with c1:
        top_k = st.selectbox("Top K (gráficos)", options=[10, 15, 20, 30, 50], index=2, key="g_topk")
    with c2:
        last_soma = st.selectbox("Soma (últimos N concursos)", options=[50, 100, 200, 300, 500], index=2, key="g_lastsoma")

    @st.fragment
    def render_charts() -> None:
        st.subheader("Gráficos")
        g1, g2, g3 = st.columns(3)

        with g1:
            st.caption("Top frequência")
            st.bar_chart(freq_top_df(freq_df, top=int(top_k)), width="stretch", height=280)

        with g2:
            st.caption("Top atraso")
            st.bar_chart(atraso_top_df(atraso_df, top=int(top_k)), width="stretch", height=280)

        with g3:
            st.caption("Soma ao longo do tempo")
            st.line_chart(soma_series_df(dfs_soma, last_n=int(last_soma)), width="stretch", height=280)

    @st.fragment
    def render_downloads() -> None:
        st.subheader("Relatórios (download)")

        resumo = {
            "Modalidade": spec.modalidade,
            "Concursos": str(len(df)),
            "Concurso máx": str(int(df["concurso"].max())),
            "Universo": f"1–{spec.n_universo}",
        }

        top_freq = freq_df.sort_values("frequencia", ascending=False).head(int(top_k))
        top_atraso = atraso_df.sort_values(["atraso_atual", "frequencia"], ascending=[False, False]).head(int(top_k))

        html_bytes = build_html_report(
            title="Lottery Helper - Relatório",
            subtitle=f"{spec.modalidade} (análises)",
            generated_at=datetime.now(),
            summary=resumo,
            tables=[
                ("Top frequência", top_freq),
                ("Top atraso", top_atraso),
                ("Distribuição Par/Ímpar", dist_pi),
                ("Distribuição Baixa/Alta", dist_ba),
                ("Distribuição de soma", dist_soma),
            ],
        )

        st.download_button(
            "Baixar relatório HTML",
            data=html_bytes,
            file_name=f"relatorio_{spec.modalidade}_{datetime.now().date()}.html",
            mime="text/html",
            use_container_width=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.download_button(
                "Frequência (CSV)",
                data=df_to_csv_bytes(freq_df),
                file_name=f"freq_{spec.modalidade}_{datetime.now().date()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with c2:
            st.download_button(
                "Atraso (CSV)",
                data=df_to_csv_bytes(atraso_df),
                file_name=f"atraso_{spec.modalidade}_{datetime.now().date()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with c3:
            st.download_button(
                "Frequência (JSON)",
                data=df_to_json_bytes(freq_df),
                file_name=f"freq_{spec.modalidade}_{datetime.now().date()}.json",
                mime="application/json",
                use_container_width=True,
            )

        with c4:
            md_bytes = df_to_md_bytes(
                title="Relatório (resumo)",
                dfs=[
                    ("Resumo", pd.DataFrame([resumo])),
                    ("Top frequência", top_freq),
                    ("Top atraso", top_atraso),
                ],
                max_rows=200,
            )
            st.download_button(
                "Resumo (MD)",
                data=md_bytes,
                file_name=f"relatorio_{spec.modalidade}_{datetime.now().date()}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    render_charts()
    st.divider()
    render_downloads()
