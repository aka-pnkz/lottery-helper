from __future__ import annotations

from typing import TypedDict

import pandas as pd

from src.domain_lottery import baixos_altos, contar_primos, pares_impares
from src.models import GameInfo


class GameRow(TypedDict, total=False):
    jogo_id: int
    estrategia: str
    soma: int
    pares: int
    impares: int
    baixos: int
    altos: int
    nprimos: int
    rep_ultimo: int
    # d1..dN entram dinamicamente (total=False)


def games_info_to_df(
    games_info: list[GameInfo],
    *,
    limite_baixo: int,
    dezenas_ult: set[int],
) -> pd.DataFrame:
    rows: list[GameRow] = []
    max_dezenas = 0

    for gi in games_info:
        j = sorted(gi.dezenas)
        max_dezenas = max(max_dezenas, len(j))

        r: GameRow = {"jogo_id": int(gi.jogo_id), "estrategia": str(gi.estrategia)}

        for k, d in enumerate(j, start=1):
            r[f"d{k}"] = int(d)  # type: ignore[literal-required]

        soma = int(sum(j))
        pares, imp = pares_impares(j)
        baixos, altos = baixos_altos(j, limite_baixo)
        primos = contar_primos(j)
        rep = len(set(j) & dezenas_ult)

        r.update(
            {
                "soma": soma,
                "pares": int(pares),
                "impares": int(imp),
                "baixos": int(baixos),
                "altos": int(altos),
                "nprimos": int(primos),
                "rep_ultimo": int(rep),
            }
        )

        rows.append(r)

    df = pd.DataFrame(rows)

    # Schema mínimo (mesmo vazio) para não quebrar groupby/export/paginação
    base_cols: list[tuple[str, str]] = [
        ("jogo_id", "int64"),
        ("estrategia", "object"),
        ("soma", "int64"),
        ("pares", "int64"),
        ("impares", "int64"),
        ("baixos", "int64"),
        ("altos", "int64"),
        ("nprimos", "int64"),
        ("rep_ultimo", "int64"),
    ]

    for col, dtype in base_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype=dtype)

    # Garante colunas d1..dN (com base no maior jogo gerado)
    for k in range(1, max_dezenas + 1):
        col = f"d{k}"
        if col not in df.columns:
            df[col] = pd.Series(dtype="int64")

    # Ordena as colunas para ficar previsível
    d_cols = [f"d{k}" for k in range(1, max_dezenas + 1)]
    ordered = ["jogo_id", "estrategia", *d_cols, "soma", "pares", "impares", "baixos", "altos", "nprimos", "rep_ultimo"]
    df = df.reindex(columns=[c for c in ordered if c in df.columns])

    return df
