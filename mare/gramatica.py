"""
Representação de gramáticas livres de contexto (GLC).

Uma gramática é formada por produções `A -> X1 X2 ... Xn`. Aqui ela é lida de
um arquivo de texto simples, no formato:

    # comentário
    expr   -> termo expr'
    expr'  -> MAIS termo expr' | ε
    termo  -> NUM_INT | ABRE_PAR expr FECHA_PAR
           | ID                         # linha começando com '|' continua a regra

Convenções:
  * os símbolos são separados por espaço;
  * `ε` (ou `epsilon`) é a cadeia vazia;
  * o símbolo inicial é o lado esquerdo da PRIMEIRA produção;
  * não-terminal = símbolo que aparece à esquerda de alguma produção;
    terminal = qualquer outro símbolo (nas gramáticas da Maré, os nomes do
    enum TipoToken, como ID, NUM_INT, ABRE_PAR).

Este módulo só descreve a gramática. FIRST/FOLLOW ficam em first_follow.py,
a tabela LL(1) em ll1.py e os itens LR(0) em lr0.py.
"""

from __future__ import annotations

from dataclasses import dataclass

EPSILON = "ε"       # cadeia vazia
FIM = "$"           # marcador de fim de entrada
_SINONIMOS_EPSILON = {EPSILON, "epsilon", "EPSILON"}


class ErroGramatica(Exception):
    """Gramática mal formada (erro de formato no arquivo ou símbolo inválido)."""


@dataclass(frozen=True)
class Producao:
    """Uma produção `esquerda -> direita`. Cadeia vazia = tupla vazia (ε)."""

    numero: int
    esquerda: str
    direita: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.esquerda} → {formatar_cadeia(self.direita)}"


def formatar_cadeia(cadeia: tuple[str, ...] | list[str]) -> str:
    """Escreve uma cadeia de símbolos; a cadeia vazia aparece como ε."""
    return " ".join(cadeia) if cadeia else EPSILON


class Gramatica:
    """Conjunto de produções com símbolo inicial, terminais e não-terminais."""

    def __init__(self, producoes: list[tuple[str, tuple[str, ...]]], nome: str = "gramática"):
        if not producoes:
            raise ErroGramatica("a gramática não tem nenhuma produção")
        self.nome = nome
        self.producoes: list[Producao] = [
            Producao(i, esq, tuple(dir_)) for i, (esq, dir_) in enumerate(producoes)
        ]
        self.inicial: str = self.producoes[0].esquerda

        # Não-terminais na ordem em que aparecem à esquerda (ordem estável,
        # importante para imprimir tabelas sempre do mesmo jeito).
        self.nao_terminais: list[str] = []
        for p in self.producoes:
            if p.esquerda not in self.nao_terminais:
                self.nao_terminais.append(p.esquerda)

        # Terminais: o que aparece à direita e não é não-terminal.
        self.terminais: list[str] = []
        for p in self.producoes:
            for simbolo in p.direita:
                if simbolo not in self.nao_terminais and simbolo not in self.terminais:
                    self.terminais.append(simbolo)
        if FIM in self.terminais or FIM in self.nao_terminais:
            raise ErroGramatica(f"o símbolo '{FIM}' é reservado para o fim da entrada")

        # Índice: não-terminal -> suas produções, em ordem.
        self.por_nao_terminal: dict[str, list[Producao]] = {nt: [] for nt in self.nao_terminais}
        for p in self.producoes:
            self.por_nao_terminal[p.esquerda].append(p)

    # ------------------------------------------------------------ consultas

    def eh_nao_terminal(self, simbolo: str) -> bool:
        return simbolo in self.por_nao_terminal

    def eh_terminal(self, simbolo: str) -> bool:
        return simbolo not in self.por_nao_terminal

    # ------------------------------------------------------------ leitura

    @classmethod
    def de_texto(cls, texto: str, nome: str = "gramática") -> "Gramatica":
        """Lê a gramática do formato descrito no topo deste módulo."""
        regras: list[tuple[str, list[str]]] = []  # (esquerda, alternativas em texto)
        for numero_linha, bruta in enumerate(texto.splitlines(), 1):
            linha = bruta.split("#", 1)[0].strip()
            if not linha:
                continue
            if "->" in linha:
                esquerda, _, resto = linha.partition("->")
                esquerda = esquerda.strip()
                if not esquerda or len(esquerda.split()) != 1:
                    raise ErroGramatica(f"linha {numero_linha}: lado esquerdo inválido '{esquerda}'")
                regras.append((esquerda, [resto]))
            elif linha.startswith("|"):
                if not regras:
                    raise ErroGramatica(f"linha {numero_linha}: '|' sem regra anterior")
                regras[-1][1].append(linha)
            else:
                raise ErroGramatica(f"linha {numero_linha}: esperado 'A -> ...' ou continuação '| ...'")

        producoes: list[tuple[str, tuple[str, ...]]] = []
        for esquerda, pedacos in regras:
            alternativas = " ".join(pedacos).split("|")
            for alternativa in alternativas:
                simbolos = alternativa.split()
                if any(s in _SINONIMOS_EPSILON for s in simbolos):
                    if len(simbolos) != 1:
                        raise ErroGramatica(f"'{esquerda}': ε não pode vir junto de outros símbolos")
                    simbolos = []
                elif not simbolos:
                    raise ErroGramatica(f"'{esquerda}': alternativa vazia (use ε para a cadeia vazia)")
                producoes.append((esquerda, tuple(simbolos)))
        return cls(producoes, nome)

    @classmethod
    def de_arquivo(cls, caminho: str) -> "Gramatica":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_texto(f.read(), nome=caminho)

    # ------------------------------------------------------------ transformação

    def aumentada(self) -> "Gramatica":
        """Devolve G' = G + (S' -> S), com S' como novo símbolo inicial (usada no LR)."""
        novo = self.inicial + "'"
        while novo in self.nao_terminais or novo in self.terminais:
            novo += "'"
        producoes = [(novo, (self.inicial,))] + [(p.esquerda, p.direita) for p in self.producoes]
        return Gramatica(producoes, self.nome + " (aumentada)")

    # ------------------------------------------------------------ exibição

    def formatar(self, numerar: bool = True, agrupar: bool = True) -> str:
        """Imprime a gramática. Com `agrupar`, as alternativas de um mesmo
        não-terminal ficam na mesma linha, separadas por `|`."""
        if not agrupar:
            return "\n".join(
                (f"{p.numero:>3}. " if numerar else "") + str(p) for p in self.producoes
            )
        largura = max(len(nt) for nt in self.nao_terminais)
        linhas = []
        for nt in self.nao_terminais:
            alternativas = self.por_nao_terminal[nt]
            primeira, resto = alternativas[0], alternativas[1:]
            prefixo = f"{primeira.numero:>3}. " if numerar else ""
            linhas.append(f"{prefixo}{nt.ljust(largura)} → {formatar_cadeia(primeira.direita)}")
            for p in resto:
                marca = f"{p.numero:>3}. " if numerar else ""
                linhas.append(f"{marca}{' ' * largura} | {formatar_cadeia(p.direita)}")
        return "\n".join(linhas)

    def resumo(self) -> str:
        return (f"{len(self.producoes)} produções, {len(self.terminais)} terminais, "
                f"{len(self.nao_terminais)} não-terminais, símbolo inicial '{self.inicial}'")

    def __str__(self) -> str:
        return self.formatar()
