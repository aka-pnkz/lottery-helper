from dataclasses import dataclass
from typing import Literal

Modalidade = Literal["Mega-Sena", "Lotofácil"]

@dataclass(frozen=True)
class LotterySpec:
    modalidade: Modalidade
    n_universo: int
    n_min: int
    n_max: int
    n_dezenas_sorteio: int
    preco_base: float
    limite_baixo: int
    comb_target: int

PRECO_BASE_MEGA = 6.00
PRECO_BASE_LOTO = 3.50

URL_LOTOFACIL_DOWNLOAD = (
    "https://servicebus2.caixa.gov.br/portaldeloterias/api/resultados/download"
    "?modalidade=Lotof%C3%A1cil"
)
URL_MEGA_DOWNLOAD = (
    "https://servicebus2.caixa.gov.br/portaldeloterias/api/resultados/download"
    "?modalidade=Mega-Sena"
)

def get_spec(modalidade: Modalidade) -> LotterySpec:
    import math
    if modalidade == "Mega-Sena":
        return LotterySpec(
            modalidade="Mega-Sena",
            n_universo=60,
            n_min=6,
            n_max=15,
            n_dezenas_sorteio=6,
            preco_base=PRECO_BASE_MEGA,
            limite_baixo=30,
            comb_target=math.comb(60, 6),
        )
    return LotterySpec(
        modalidade="Lotofácil",
        n_universo=25,
        n_min=15,
        n_max=20,
        n_dezenas_sorteio=15,
        preco_base=PRECO_BASE_LOTO,
        limite_baixo=13,
        comb_target=math.comb(25, 15),
    )
