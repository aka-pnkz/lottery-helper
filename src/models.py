from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Filters:
    dezenas_fixas: list[int]
    dezenas_proibidas: list[int]
    soma_min: Optional[int]
    soma_max: Optional[int]
    orcamento_max: float

@dataclass(frozen=True)
class GameInfo:
    jogo_id: int
    estrategia: str
    dezenas: list[int]
