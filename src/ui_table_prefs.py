from __future__ import annotations

import streamlit as st

HEIGHT_PRESETS: dict[str, int | str | None] = {
    "Auto": None,          # não passa height
    "Compacto": 320,
    "Normal": 420,
    "Alto": 600,
    "Tela toda": "stretch",
    "Conteúdo": "content",
}

def table_prefs_sidebar(prefix: str = "tabela"):
    with st.sidebar.expander("Tabelas", expanded=False):
        height_label = st.selectbox(
            "Altura",
            options=list(HEIGHT_PRESETS.keys()),
            index=1,
            key=f"{prefix}_height",
        )
    return HEIGHT_PRESETS[height_label]


def df_show(container, df, *, width: str = "stretch", height=None):
    # NUNCA passar height=None para st.dataframe (gera StreamlitInvalidHeightError). [web:182]
    if height is None:
        return container.dataframe(df, width=width)
    return container.dataframe(df, width=width, height=height)
