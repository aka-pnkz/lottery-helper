from __future__ import annotations

import streamlit as st

# Para máxima compatibilidade com versões diferentes:
# - st.dataframe height aceita int (px) e, em algumas versões, "content"/"stretch".
# - Para "Auto", a forma mais segura é NÃO passar o argumento height. [web:182]

HEIGHT_PRESETS: dict[str, int | str | None] = {
    "Auto": None,          # significa: não passar height
    "Compacto": 320,
    "Normal": 420,
    "Alto": 600,
    "Tela toda": "stretch",
    "Conteúdo": "content",
}

TOP_PRESETS: dict[str, int | None] = {
    "Top 20": 20,
    "Top 50": 50,
    "Top 100": 100,
    "Tudo": None,
}

def table_prefs_sidebar(prefix: str = "tabela"):
    st.sidebar.markdown("### Tabelas")

    height_label = st.sidebar.selectbox(
        "Altura",
        options=list(HEIGHT_PRESETS.keys()),
        index=1,  # Compacto
        key=f"{prefix}_height",
        help="Auto = altura padrão do Streamlit; Tela toda/Conteúdo usam modos especiais quando suportados.",
    )

    top_label = st.sidebar.selectbox(
        "Quantidade",
        options=list(TOP_PRESETS.keys()),
        index=1,  # Top 50
        key=f"{prefix}_top",
        help="‘Tudo’ pode deixar a página mais pesada.",
    )

    return HEIGHT_PRESETS[height_label], TOP_PRESETS[top_label]


def df_show(container, df, *, width: str = "stretch", height=None):
    """
    Wrapper para st.dataframe que só passa height quando não é None.
    Isso evita StreamlitInvalidHeightError quando height=None. [web:182]
    """
    if height is None:
        return container.dataframe(df, width=width)
    return container.dataframe(df, width=width, height=height)
