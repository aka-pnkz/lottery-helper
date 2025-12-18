from __future__ import annotations

import math
import streamlit as st
import pandas as pd


def paginate_df(df: pd.DataFrame, *, key: str, default_page_size: int = 50) -> pd.DataFrame:
    total_rows = len(df)
    if total_rows == 0:
        return df

    page_sizes = [20, 50, 100, 200]
    if default_page_size not in page_sizes:
        page_sizes = [default_page_size] + page_sizes

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        page_size = st.selectbox("Linhas/página", options=page_sizes, index=page_sizes.index(default_page_size), key=f"{key}_ps")

    total_pages = max(1, math.ceil(total_rows / int(page_size)))
    with c2:
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1, key=f"{key}_p")

    with c3:
        start = (int(page) - 1) * int(page_size)
        end = min(start + int(page_size), total_rows)
        st.caption(f"Mostrando linhas {start + 1}–{end} de {total_rows}")

    start = (int(page) - 1) * int(page_size)
    end = min(start + int(page_size), total_rows)
    return df.iloc[start:end]
