"""
Rastro passo a passo dos analisadores de tabela (LL(1) e SLR(1)).

Cada passo do algoritmo vira uma linha `Passo | Pilha | Entrada | Ação`. O
rastro é guardado por inteiro; só na hora de exibir no terminal é que pilha e
entrada longas são abreviadas com `…` (a exportação para arquivo é completa).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .erros import ErroSintatico
from .tabelas import tabela_texto

CABECALHO_RASTRO = ["Passo", "Pilha", "Entrada", "Ação"]


@dataclass
class Passo:
    numero: int
    pilha: str      # conteúdo da pilha, topo à direita
    entrada: str    # tokens que ainda faltam ler, terminando em $
    acao: str


@dataclass
class ResultadoAnalise:
    """Resultado de uma análise: rastro completo e erros encontrados."""

    passos: list[Passo] = field(default_factory=list)
    erros: list[ErroSintatico] = field(default_factory=list)

    @property
    def aceito(self) -> bool:
        return not self.erros


def _abreviar_pilha(pilha: str, limite: int) -> str:
    """Mantém só o topo da pilha (fim do texto), cortando em símbolos inteiros."""
    if len(pilha) <= limite:
        return pilha
    mantidos: list[str] = []
    tamanho = 2                       # espaço reservado para o "… " do começo
    for simbolo in reversed(pilha.split()):
        if tamanho + len(simbolo) + 1 > limite:
            break
        mantidos.append(simbolo)
        tamanho += len(simbolo) + 1
    return "… " + " ".join(reversed(mantidos))


def _abreviar_entrada(entrada: str, limite: int) -> str:
    """Mantém o começo da entrada (próximos tokens), cortando em tokens inteiros."""
    if len(entrada) <= limite:
        return entrada
    mantidos: list[str] = []
    tamanho = 2                       # espaço reservado para o " …" do fim
    for token in entrada.split():
        if tamanho + len(token) + 1 > limite:
            break
        mantidos.append(token)
        tamanho += len(token) + 1
    return " ".join(mantidos) + " …"


def linhas_rastro(passos: list[Passo], completo: bool = True,
                  limite_pilha: int = 34, limite_entrada: int = 34) -> list[list[str]]:
    """Linhas da tabela; com `completo=False`, pilha/entrada são abreviadas."""
    linhas = []
    for p in passos:
        pilha, entrada = p.pilha, p.entrada
        if not completo:
            pilha = _abreviar_pilha(pilha, limite_pilha)
            entrada = _abreviar_entrada(entrada, limite_entrada)
        linhas.append([str(p.numero), pilha, entrada, p.acao])
    return linhas


def tabela_rastro(passos: list[Passo], completo: bool = False, largura: int = 130) -> str:
    """Tabela `Passo | Pilha | Entrada | Ação` pronta para o terminal."""
    return tabela_texto(CABECALHO_RASTRO, linhas_rastro(passos, completo), largura_max=None if completo else largura)
