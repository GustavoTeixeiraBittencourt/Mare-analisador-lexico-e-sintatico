"""
Cálculo dos conjuntos FIRST e FOLLOW por ponto fixo.

Nada aqui depende da gramática da Maré: tudo é calculado a partir das
produções de uma `Gramatica`.

FIRST(α)  = terminais que podem iniciar uma cadeia derivada de α
            (e ε ∈ FIRST(α) se α pode derivar a cadeia vazia).
FOLLOW(A) = terminais que podem aparecer imediatamente depois de A em alguma
            forma sentencial ($ marca o fim da entrada).

Algoritmo (ponto fixo iterativo): aplicam-se as regras abaixo, em laço, até
que uma passada completa não acrescente mais nenhum símbolo a nenhum conjunto.
Como os conjuntos só crescem e são finitos, o laço termina.
"""

from __future__ import annotations

from .gramatica import EPSILON, FIM, Gramatica

Conjuntos = dict[str, set[str]]


def calcular_first(g: Gramatica) -> Conjuntos:
    """FIRST de cada símbolo da gramática.

    Regras:
      1. terminal a:           FIRST(a) = {a}
      2. A -> ε:               ε ∈ FIRST(A)
      3. A -> X1 X2 ... Xn:    acrescenta FIRST(X1) - {ε} a FIRST(A); se
         ε ∈ FIRST(X1), continua com X2, e assim por diante; se TODOS os Xi
         derivam ε, então ε ∈ FIRST(A).
    """
    first: Conjuntos = {t: {t} for t in g.terminais}
    for nt in g.nao_terminais:
        first[nt] = set()

    mudou = True
    while mudou:
        mudou = False
        for p in g.producoes:
            novos = first_de_cadeia(p.direita, first)
            if not novos <= first[p.esquerda]:
                first[p.esquerda] |= novos
                mudou = True
    return first


def first_de_cadeia(cadeia: tuple[str, ...] | list[str], first: Conjuntos) -> set[str]:
    """FIRST de uma cadeia de símbolos X1 X2 ... Xn (a cadeia vazia dá {ε})."""
    resultado: set[str] = set()
    for simbolo in cadeia:
        f = first[simbolo]
        resultado |= f - {EPSILON}
        if EPSILON not in f:
            return resultado          # Xi não some: os próximos não contam
    resultado.add(EPSILON)            # todos os símbolos (ou nenhum) derivam ε
    return resultado


def calcular_follow(g: Gramatica, first: Conjuntos) -> Conjuntos:
    """FOLLOW de cada não-terminal.

    Regras (para cada produção A -> α B β):
      1. $ ∈ FOLLOW(símbolo inicial)
      2. FOLLOW(B) recebe FIRST(β) - {ε}
      3. se β é vazio ou ε ∈ FIRST(β): FOLLOW(B) recebe FOLLOW(A)
    """
    follow: Conjuntos = {nt: set() for nt in g.nao_terminais}
    follow[g.inicial].add(FIM)

    mudou = True
    while mudou:
        mudou = False
        for p in g.producoes:
            for i, simbolo in enumerate(p.direita):
                if not g.eh_nao_terminal(simbolo):
                    continue
                resto = first_de_cadeia(p.direita[i + 1:], first)
                novos = resto - {EPSILON}
                if EPSILON in resto:
                    novos |= follow[p.esquerda]
                if not novos <= follow[simbolo]:
                    follow[simbolo] |= novos
                    mudou = True
    return follow


# ------------------------------------------------------------ exibição


def _ordenar(conjunto: set[str], ordem: list[str]) -> list[str]:
    """Ordena um conjunto pela ordem de aparição na gramática (ε e $ no fim)."""
    posicao = {s: i for i, s in enumerate(ordem)}
    especiais = {EPSILON: 1, FIM: 2}
    return sorted(conjunto, key=lambda s: (especiais.get(s, 0), posicao.get(s, 0)))


def tabela_first_follow(g: Gramatica, first: Conjuntos, follow: Conjuntos, largura: int = 100) -> str:
    """Tabela `Não-terminal | FIRST | FOLLOW`; conjuntos longos quebram em várias linhas."""
    from .tabelas import tabela_texto

    ordem = g.terminais
    linhas: list[list[str]] = []
    for nt in g.nao_terminais:
        f = "{ " + ", ".join(_ordenar(first[nt], ordem)) + " }"
        s = "{ " + ", ".join(_ordenar(follow[nt], ordem)) + " }"
        linhas.append([nt, f, s])
    return tabela_texto(["Não-terminal", "FIRST", "FOLLOW"], linhas, largura_max=largura)
