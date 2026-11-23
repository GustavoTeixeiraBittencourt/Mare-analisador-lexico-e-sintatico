"""
Adaptação da cadeia de tokens do Lexer para os analisadores LL(1) e SLR(1).

Os analisadores de tabela trabalham com *nomes de terminais* (os mesmos nomes
do enum TipoToken, como `ID` ou `ABRE_PAR`) e com o marcador `$` de fim de
entrada. `SimboloEntrada` guarda o nome do terminal e a posição no código,
para que os erros sintáticos apontem linha e coluna.
"""

from __future__ import annotations

from dataclasses import dataclass

from .erros import ErroSintatico
from .gramatica import FIM
from .parser import descrever
from .tokens import Token, TipoToken

_TIPOS_POR_NOME = {t.nome: t for t in TipoToken}


@dataclass(frozen=True)
class SimboloEntrada:
    """Um terminal da entrada: nome do terminal, lexema e posição no código."""

    nome: str
    lexema: str = ""
    linha: int = 0
    coluna: int = 0


def de_tokens(tokens: list[Token]) -> list[SimboloEntrada]:
    """Converte os tokens do Lexer; o token EOF vira o marcador `$`."""
    return [
        SimboloEntrada(FIM if t.tipo is TipoToken.EOF else t.tipo.nome, t.lexema, t.linha, t.coluna)
        for t in tokens
    ]


def de_nomes(nomes: list[str]) -> list[SimboloEntrada]:
    """Cria uma entrada a partir de nomes de terminais (útil em testes e na
    verificação de gramáticas genéricas). Acrescenta `$` se faltar."""
    simbolos = [SimboloEntrada(n, n, 1, i + 1) for i, n in enumerate(nomes)]
    if not simbolos or simbolos[-1].nome != FIM:
        simbolos.append(SimboloEntrada(FIM, "", 1, len(simbolos) + 1))
    return simbolos


def descrever_terminal(nome: str) -> str:
    """Texto amigável de um terminal para mensagens de erro (ex.: ABRE_PAR → '(')."""
    if nome == FIM:
        return "fim do arquivo"
    tipo = _TIPOS_POR_NOME.get(nome)
    return descrever(tipo) if tipo else nome


def lista_esperados(esperados: list[str], maximo: int = 6) -> str:
    """'a, b ou c' — e '...' quando há muitas alternativas."""
    nomes = [descrever_terminal(e) for e in esperados]
    if len(nomes) > maximo:
        return ", ".join(nomes[:maximo]) + ", ..."
    if len(nomes) <= 1:
        return "".join(nomes)
    return ", ".join(nomes[:-1]) + " ou " + nomes[-1]


def erro_esperado(esperados: list[str], entrada: list[SimboloEntrada], pos: int) -> ErroSintatico:
    """Monta o erro sintático "esperado X, mas foi encontrado Y" na posição `pos`.

    Se um ';' era uma das opções válidas e o token encontrado está em outra linha, o erro
    aponta para o fim da linha anterior (é onde o ';' deveria estar).
    """
    atual = entrada[pos]
    achado = "fim do arquivo" if atual.nome == FIM else f"'{atual.lexema}'"
    anterior = entrada[pos - 1] if pos > 0 else None
    if (TipoToken.PONTO_VIRGULA.nome in esperados and anterior is not None
            and anterior.linha and anterior.linha < atual.linha):
        return ErroSintatico("esperado ';' (faltou ';' no fim da linha)",
                             anterior.linha, anterior.coluna + len(anterior.lexema))
    return ErroSintatico(f"esperado {lista_esperados(esperados)}, mas foi encontrado {achado}",
                         atual.linha, atual.coluna)
