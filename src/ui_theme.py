import streamlit as st

def apply_theme() -> None:
    st.markdown(
        """
        <style>
        /* Fundo com gradiente suave (vibrante sem cansar) */
        .stApp {
            background: linear-gradient(180deg, rgba(255,46,136,0.10) 0%, rgba(6,182,212,0.08) 45%, rgba(255,255,255,1) 100%);
        }

        /* Cards e blocos */
        div[data-testid="metric-container"],
        div[data-testid="stVerticalBlockBorderWrapper"]{
            background: #FFFFFF;
            border: 1px solid rgba(15, 23, 42, 0.10);
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
        }

        /* Tabs em “pílula” mais coloridas */
        .stTabs [data-baseweb="tab"]{
            border-radius: 999px !important;
            padding: 8px 14px !important;
            background: rgba(255,46,136,0.12);
            border: 1px solid rgba(255,46,136,0.18);
        }
        .stTabs [aria-selected="true"]{
            background: linear-gradient(90deg, #FF2E88 0%, #06B6D4 100%) !important;
            color: white !important;
            border: 0 !important;
        }

        /* Botões: mais “CTA” */
        .stButton > button{
            border-radius: 14px !important;
            border: 1px solid rgba(255,46,136,0.30) !important;
            box-shadow: 0 10px 18px rgba(255,46,136,0.15);
        }
        .stButton > button:hover{
            border-color: rgba(6,182,212,0.55) !important;
            box-shadow: 0 12px 22px rgba(6,182,212,0.18);
        }

        /* Dataframes mais legíveis */
        .stDataFrame thead tr th { font-size: 0.82rem; }
        .stDataFrame tbody tr td { font-size: 0.82rem; }

        /* Sidebar levemente destacada */
        section[data-testid="stSidebar"]{
            background: linear-gradient(180deg, rgba(255,46,136,0.10) 0%, rgba(6,182,212,0.08) 100%);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
