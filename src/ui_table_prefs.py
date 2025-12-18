from __future__ import annotations

import streamlit as st


HEIGHT_PRESETS: dict[str, int | None] = {
    "Auto": None,          # deixa o Streamlit decidir
    "Compacto": 320,
    "Normal": 420,
    "Alto": 600,
    "Tela toda": 850,
}

TOP_PRESETS: dict[str, int | None] = {
    "Top 20": 20,
    "Top 50": 50,
    "Top 100": 100,
    "Tudo": None,          # sem limite
}

def table_prefs_sidebar(prefix: str = "tabela"):
    """
    Retorna (height_px, top_n) a partir de presets fáceis.
    height_px: int | None
    top_n: int | None
    """
    st.sidebar.markdown("### Tabelas")
    height_label = st.sidebar.selectbox(
        "Altura",
        options=list(HEIGHT_PRESETS.keys()),
        index=1,  # Compacto
        key=f"{prefix}_height",
        help="Auto deixa o Streamlit escolher; Tela toda ocupa mais espaço.",
    )
    top_label = st.sidebar.selectbox(
        "Quantidade",
        options=list(TOP_PRESETS.keys()),
        index=1,  # Top 50 (ajuste se preferir)
        key=f"{prefix}_top",
        help="‘Tudo’ pode deixar a página mais pesada.",
    )

    height_px = HEIGHT_PRESETS[height_label]
    top_n = TOP_PRESETS[top_label]
    return height_px, top_n
