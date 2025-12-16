import re

def money_ptbr(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_lista(texto: str) -> list[int]:
    if not texto:
        return []
    tokens = re.split(r"[,\s;]+", texto.strip())
    out: list[int] = []
    seen: set[int] = set()
    for t in tokens:
        if t.isdigit():
            v = int(t)
            if v not in seen:
                out.append(v)
                seen.add(v)
    return out

def validar_dezenas(lista: list[int], n_universo: int, nome: str) -> None:
    if len(set(lista)) != len(lista):
        raise ValueError(f"{nome}: há dezenas repetidas.")
    if any((d < 1 or d > n_universo) for d in lista):
        raise ValueError(f"{nome}: há dezenas fora do intervalo 1–{n_universo}.")
