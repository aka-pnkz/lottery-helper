from __future__ import annotations

from contextlib import contextmanager
import streamlit as st


@contextmanager
def sidebar_spinner(message: str):
    """
    Spinner dentro do sidebar.
    Importante: NÃO existe st.sidebar.spinner(...). O correto é usar st.spinner(...)
    dentro de um contexto `with st.sidebar:`.
    """
    with st.sidebar:
        with st.spinner(message):
            yield
