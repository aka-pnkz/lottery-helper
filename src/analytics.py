import pandas as pd

def frequencias(df: pd.DataFrame, n_dezenas_sorteio: int, n_universo: int) -> pd.DataFrame:
    dezenas_cols = [f"d{i}" for i in range(1, n_dezenas_sorteio + 1)]
    todas = df[dezenas_cols].values.ravel()
    freq = pd.Series(todas).value_counts().reindex(range(1, n_universo + 1), fill_value=0).sort_index()
    out = freq.reset_index()
    out.columns = ["dezena", "frequencia"]
    out["dezena"] = out["dezena"].astype(int)
    out["frequencia"] = out["frequencia"].astype(int)
    return out

def atraso(freq_df: pd.DataFrame, df: pd.DataFrame, n_dezenas_sorteio: int, n_universo: int) -> pd.DataFrame:
    dezenas_cols = [f"d{i}" for i in range(1, n_dezenas_sorteio + 1)]
    ultimo: dict[int, int] = {}
    for _, row in df[["concurso"] + dezenas_cols].iterrows():
        conc = int(row["concurso"])
        for d in row[dezenas_cols]:
            ultimo[int(d)] = conc

    max_conc = int(df["concurso"].max())
    linhas = []
    for dezena in range(1, n_universo + 1):
        fr = int(freq_df.loc[freq_df["dezena"] == dezena, "frequencia"].iloc[0])
        ult = ultimo.get(dezena)
        linhas.append(
            {
                "dezena": dezena,
                "frequencia": fr,
                "ultimo_concurso": ult,
                "atraso_atual": (None if ult is None else max_conc - ult),
            }
        )
    return pd.DataFrame(linhas)

def padroes_par_impar_baixa_alta(df: pd.DataFrame, n_dezenas_sorteio: int, limite_baixo: int):
    dezenas_cols = [f"d{i}" for i in range(1, n_dezenas_sorteio + 1)]
    registros = []
    for _, row in df[["concurso"] + dezenas_cols].iterrows():
        dezenas = [int(row[c]) for c in dezenas_cols]
        pares = sum(1 for d in dezenas if d % 2 == 0)
        impares = len(dezenas) - pares
        baixos = sum(1 for d in dezenas if 1 <= d <= limite_baixo)
        altos = len(dezenas) - baixos
        registros.append({"concurso": int(row["concurso"]), "pares": pares, "impares": impares, "baixos": baixos, "altos": altos})

    dfp = pd.DataFrame(registros)
    dist_pi = dfp.groupby(["pares", "impares"]).size().reset_index(name="qtd").sort_values("qtd", ascending=False).reset_index(drop=True)
    dist_ba = dfp.groupby(["baixos", "altos"]).size().reset_index(name="qtd").sort_values("qtd", ascending=False).reset_index(drop=True)
    return dfp, dist_pi, dist_ba

def somas(df: pd.DataFrame, n_dezenas_sorteio: int):
    dezenas_cols = [f"d{i}" for i in range(1, n_dezenas_sorteio + 1)]
    dfx = df.copy()
    dfx["soma"] = dfx[dezenas_cols].sum(axis=1)

    bins = [0, 150, 200, 250, 300, 350, 500]
    labels = ["0-150", "151-200", "201-250", "251-300", "301-350", "351-500"]
    dfx["faixa_soma"] = pd.cut(dfx["soma"], bins=bins, labels=labels, right=True)

    dist = (
        dfx["faixa_soma"]
        .value_counts(dropna=False)
        .sort_index()
        .reset_index()
    )
    # garante nomes estáveis
    dist.columns = ["faixa_soma", "qtd"]

    return dfx[["concurso", "soma", "faixa_soma"]], dist
