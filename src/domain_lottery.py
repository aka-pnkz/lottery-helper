import math
import numpy as np
import pandas as pd

PRIMOS_ATE_60 = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59}

def formatar_jogo(jogo: list[int]) -> str:
    return " - ".join(f"{d:02d}" for d in sorted(jogo))

def pares_impares(jogo: list[int]) -> tuple[int,int]:
    pares = sum(1 for d in jogo if d % 2 == 0)
    return pares, len(jogo) - pares

def baixos_altos(jogo: list[int], limite_baixo: int) -> tuple[int,int]:
    baixos = sum(1 for d in jogo if 1 <= d <= limite_baixo)
    return baixos, len(jogo) - baixos

def tem_sequencia_longa(jogo: list[int], limite: int = 3) -> bool:
    j = sorted(jogo)
    atual = 1
    for i in range(1, len(j)):
        if j[i] == j[i-1] + 1:
            atual += 1
            if atual >= limite:
                return True
        else:
            atual = 1
    return False

def contar_primos(jogo: list[int]) -> int:
    return sum(1 for d in jogo if d in PRIMOS_ATE_60)

def gerar_aleatorio_puro(qtd: int, tam: int, n_universo: int) -> list[list[int]]:
    universe = np.arange(1, n_universo + 1)
    return [sorted(np.random.choice(universe, size=tam, replace=False).tolist()) for _ in range(qtd)]

def gerar_balanceado_par_impar(qtd: int, tam: int, n_universo: int) -> list[list[int]]:
    universe = np.arange(1, n_universo + 1)
    jogos: list[list[int]] = []
    for _ in range(qtd):
        tent = 0
        while True:
            tent += 1
            dezenas = np.random.choice(universe, size=tam, replace=False).tolist()
            p, i = pares_impares(dezenas)
            if p not in (0, tam) and i not in (0, tam):
                jogos.append(sorted(dezenas))
                break
            if tent > 50:
                jogos.append(sorted(dezenas))
                break
    return jogos

def gerar_quentes_frias_mix(
    qtd: int,
    tam: int,
    freq_df: pd.DataFrame,
    n_universo: int,
    proporcao: tuple[int,int,int],
) -> list[list[int]]:
    q_quentes, q_frias, q_neutras = proporcao

    freq_ord = freq_df.sort_values("frequencia", ascending=False)
    quentes = freq_ord["dezena"].values[:10]

    frias_raw = freq_df.sort_values("frequencia", ascending=True)["dezena"].values[:10]
    frias = np.setdiff1d(frias_raw, quentes)

    neutras = np.setdiff1d(np.arange(1, n_universo + 1), np.union1d(quentes, frias))

    jogos: list[list[int]] = []
    for _ in range(qtd):
        dezenas: list[int] = []
        qq = min(q_quentes, tam)
        qf = min(q_frias, max(0, tam - qq))
        qn = min(q_neutras, max(0, tam - qq - qf))

        if qq > 0 and len(quentes) > 0:
            dezenas.extend(np.random.choice(quentes, size=min(qq, len(quentes)), replace=False).tolist())
        if qf > 0 and len(frias) > 0:
            dezenas.extend(np.random.choice(frias, size=min(qf, len(frias)), replace=False).tolist())
        if qn > 0 and len(neutras) > 0:
            dezenas.extend(np.random.choice(neutras, size=min(qn, len(neutras)), replace=False).tolist())

        if len(dezenas) < tam:
            rest = np.setdiff1d(np.arange(1, n_universo + 1), np.array(dezenas, dtype=int))
            extra = np.random.choice(rest, size=tam - len(dezenas), replace=False).tolist()
            dezenas.extend(extra)

        jogos.append(sorted(list(map(int, dezenas))))
    return jogos

def gerar_sem_sequencias(qtd: int, tam: int, n_universo: int, limite: int) -> list[list[int]]:
    universe = np.arange(1, n_universo + 1)
    jogos: list[list[int]] = []
    for _ in range(qtd):
        tent = 0
        while True:
            tent += 1
            dezenas = np.random.choice(universe, size=tam, replace=False).tolist()
            if not tem_sequencia_longa(dezenas, limite=limite):
                jogos.append(sorted(dezenas))
                break
            if tent > 100:
                jogos.append(sorted(dezenas))
                break
    return jogos

def filtrar_jogo(jogo: list[int], dezenas_fixas: list[int], dezenas_proibidas: list[int], soma_min: int|None, soma_max: int|None) -> bool:
    s = set(jogo)
    if dezenas_fixas and not set(dezenas_fixas).issubset(s):
        return False
    if dezenas_proibidas and (set(dezenas_proibidas) & s):
        return False
    soma = sum(jogo)
    if soma_min is not None and soma < soma_min:
        return False
    if soma_max is not None and soma > soma_max:
        return False
    return True

def preco_aposta(n_dezenas: int, n_min_base: int, preco_base: float) -> float:
    if n_dezenas < n_min_base:
        return 0.0
    return math.comb(n_dezenas, n_min_base) * preco_base

def custo_total(jogos: list[list[int]], n_min_base: int, preco_base: float) -> float:
    return sum(preco_aposta(len(j), n_min_base, preco_base) for j in jogos)

def prob_premio_maximo_aprox(jogos: list[list[int]], n_min_base: int, comb_target: int) -> float:
    prob_nao = 1.0
    for j in jogos:
        if len(j) < n_min_base:
            continue
        p = math.comb(len(j), n_min_base) / comb_target
        prob_nao *= (1.0 - p)
    return 1.0 - prob_nao
