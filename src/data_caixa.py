from __future__ import annotations

from io import BytesIO
import numpy as np
import pandas as pd
import requests

from .config import URL_LOTOFACIL_DOWNLOAD, URL_MEGA_DOWNLOAD, Modalidade
from .http_client import get_session

DEFAULT_HEADERS = {
    # Ajuda a evitar bloqueio/403 em alguns ambientes
    "User-Agent": "Mozilla/5.0 (compatible; LotteryHelper/1.0; +https://streamlit.io)",
    "Accept": "*/*",
}

def baixar_xlsx(url: str) -> BytesIO:
    r = get_session().get(url, timeout=60)
    r.raise_for_status()
    return BytesIO(r.content)

def baixar_xlsx(url: str) -> BytesIO:
    r = requests.get(url, timeout=60, headers=DEFAULT_HEADERS)
    r.raise_for_status()
    return BytesIO(r.content)


def _limpar_concurso_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["concurso"] = pd.to_numeric(df["concurso"], errors="coerce")
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["concurso", "data"])

    hoje = pd.Timestamp.today().normalize()
    df = df[(df["data"] >= "1996-01-01") & (df["data"] <= hoje)]
    df["concurso"] = df["concurso"].astype(int)

    df = df.sort_values(["concurso", "data"]).drop_duplicates(subset=["concurso"], keep="last")
    df = df.sort_values("concurso").reset_index(drop=True)
    return df


def normalizar_megasena(df_raw: pd.DataFrame) -> pd.DataFrame:
    cols = ["Concurso", "Data do Sorteio", "Bola1", "Bola2", "Bola3", "Bola4", "Bola5", "Bola6"]
    faltando = [c for c in cols if c not in df_raw.columns]
    if faltando:
        raise RuntimeError(f"XLSX Mega-Sena inválido; colunas ausentes: {faltando}")

    df = df_raw[cols].copy()
    df.rename(columns={"Concurso": "concurso", "Data do Sorteio": "data"}, inplace=True)
    df = _limpar_concurso_data(df)

    bolas = [f"Bola{i}" for i in range(1, 7)]
    for c in bolas:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=bolas)

    for c in bolas:
        df[c] = df[c].astype(int)
        df = df[df[c].between(1, 60)]

    df.rename(columns={f"Bola{i}": f"d{i}" for i in range(1, 7)}, inplace=True)
    dezenas = [f"d{i}" for i in range(1, 7)]
    df[dezenas] = np.sort(df[dezenas].values, axis=1)

    return df[["concurso", "data"] + dezenas].sort_values("concurso").reset_index(drop=True)


def normalizar_lotofacil(df_raw: pd.DataFrame) -> pd.DataFrame:
    cols = ["Concurso", "Data Sorteio"] + [f"Bola{i}" for i in range(1, 16)]
    faltando = [c for c in cols if c not in df_raw.columns]
    if faltando:
        raise RuntimeError(f"XLSX Lotofácil inválido; colunas ausentes: {faltando}")

    df = df_raw[cols].copy()
    df.rename(columns={"Concurso": "concurso", "Data Sorteio": "data"}, inplace=True)
    df = _limpar_concurso_data(df)

    bolas = [f"Bola{i}" for i in range(1, 16)]
    for c in bolas:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=bolas)

    for c in bolas:
        df[c] = df[c].astype(int)
        df = df[df[c].between(1, 25)]

    df.rename(columns={f"Bola{i}": f"d{i}" for i in range(1, 16)}, inplace=True)
    dezenas = [f"d{i}" for i in range(1, 16)]
    df[dezenas] = np.sort(df[dezenas].values, axis=1)

    return df[["concurso", "data"] + dezenas].sort_values("concurso").reset_index(drop=True)


def load_history_from_caixa(mod: Modalidade) -> pd.DataFrame:
    if mod == "Mega-Sena":
        buf = baixar_xlsx(URL_MEGA_DOWNLOAD)
        df_raw = pd.read_excel(buf)
        return normalizar_megasena(df_raw)

    buf = baixar_xlsx(URL_LOTOFACIL_DOWNLOAD)
    df_raw = pd.read_excel(buf)
    return normalizar_lotofacil(df_raw)
