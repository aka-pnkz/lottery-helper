from __future__ import annotations

import pandas as pd

from src.domain_lottery import pares_impares, baixos_altos, contar_primos
from src.models import GameInfo


def games_info_to_df(
    games_info: list[GameInfo], *, limite_baixo: int, dezenas_ult: set[int]
) -> pd.DataFrame:
    rows: list[dict] = []

    for gi in games_info:
        j = sorted(gi.dezenas)
        r: dict = {"jogo_id": int(gi.jogo_id), "estrategia": str(gi.estrategia)}

        for k, d in enumerate(j, start=1):
            r[f"d{k}"] = int(d)

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

    # Mantém schema mínimo mesmo vazio (para não quebrar groupby/export)
    base_cols = ["jogo_id", "estrategia", "soma", "pares", "impares", "baixos", "altos", "nprimos", "rep_ultimo"]
    for c in base_cols:
        if c not in df.columns:
            df[c] = pd.Series(dtype="int64" if c != "estrategia" else "object")

    return df
