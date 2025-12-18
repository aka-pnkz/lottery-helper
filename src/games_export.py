from __future__ import annotations

import pandas as pd

from src.domain_lottery import pares_impares, baixos_altos, contar_primos


def games_info_to_df(games_info, *, limite_baixo: int, dezenas_ult: set[int]) -> pd.DataFrame:
    rows = []
    for gi in games_info:
        j = sorted(gi.dezenas)
        r = {"jogo_id": gi.jogo_id, "estrategia": gi.estrategia}

        for k, d in enumerate(j, start=1):
            r[f"d{k}"] = int(d)

        soma = sum(j)
        pares, imp = pares_impares(j)
        baixos, altos = baixos_altos(j, limite_baixo)
        primos = contar_primos(j)
        rep = len(set(j) & dezenas_ult)

        r.update(
            {
                "soma": soma,
                "pares": pares,
                "impares": imp,
                "baixos": baixos,
                "altos": altos,
                "nprimos": primos,
                "rep_ultimo": rep,
            }
        )
        rows.append(r)

    return pd.DataFrame(rows)
