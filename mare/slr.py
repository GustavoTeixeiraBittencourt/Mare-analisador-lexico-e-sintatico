"""
Analisador sintático SLR(1): tabela ACTION/GOTO e algoritmo shift/reduce.

Construção da tabela a partir da coleção canônica LR(0) (lr0.py) de uma
gramática aumentada G' (com a produção 0: S' → S):

  Para cada estado Ii:
    * item `A → α • a β` (a terminal) e goto(Ii, a) = Ij   ⇒  ACTION[i, a] = shift j
    * item `A → α •` (A ≠ S'),  para cada a ∈ FOLLOW(A)     ⇒  ACTION[i, a] = reduce (A → α)
    * item `S' → S •`                                       ⇒  ACTION[i, $] = accept
    * goto(Ii, A) = Ij  (A não-terminal)                    ⇒  GOTO[i, A] = j

É o uso de FOLLOW(A) para decidir as reduções que diferencia o SLR(1) do
LR(0) (que reduziria em qualquer terminal). Se uma célula de ACTION receber
duas ações diferentes, há conflito shift/reduce ou reduce/reduce e a gramática
não é SLR(1).

Algoritmo shift/reduce: a pilha guarda estados (e, intercalados, os símbolos
que levaram a eles). Em cada passo olha-se ACTION[estado do topo, token atual]:
  * shift j   : empilha o token e o estado j; avança na entrada;
  * reduce n  : para a produção n (A → β), desempilha 2·|β| itens (símbolo e
                estado de cada símbolo de β), olha o novo topo t e empilha A e
                GOTO[t, A];
  * accept    : fim, a entrada foi reconhecida;
  * vazio     : erro sintático.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from .entrada import SimboloEntrada, de_tokens, erro_esperado
from .first_follow import Conjuntos, calcular_first, calcular_follow
from .gramatica import FIM, Gramatica
from .lr0 import ColecaoLR0, simbolo_apos_ponto
from .rastro import Passo, ResultadoAnalise
from .tabelas import tabela_texto
from .tokens import Token


class Acao(NamedTuple):
    """Ação da tabela: tipo 's' (shift), 'r' (reduce) ou 'acc'; `valor` é o
    estado destino (shift) ou o número da produção (reduce)."""

    tipo: str
    valor: int = 0

    def __str__(self) -> str:
        return "acc" if self.tipo == "acc" else f"{self.tipo}{self.valor}"


@dataclass
class ConflitoSLR:
    """Célula ACTION[estado, terminal] com ações diferentes."""

    estado: int
    terminal: str
    acoes: list[Acao]

    @property
    def tipo(self) -> str:
        tipos = {a.tipo for a in self.acoes}
        return "shift/reduce" if "s" in tipos else "reduce/reduce"

    def __str__(self) -> str:
        return f"conflito {self.tipo} em ACTION[I{self.estado}, {self.terminal}]: " + " / ".join(map(str, self.acoes))


class TabelaSLR:
    """Tabelas ACTION e GOTO de uma gramática (aumentada automaticamente)."""

    def __init__(self, gramatica: Gramatica):
        self.colecao = ColecaoLR0(gramatica)
        self.gramatica = self.colecao.gramatica            # a versão aumentada
        self.first: Conjuntos = calcular_first(self.gramatica)
        self.follow: Conjuntos = calcular_follow(self.gramatica, self.first)
        self.action: dict[tuple[int, str], list[Acao]] = {}
        self.goto: dict[tuple[int, str], int] = {}
        self._preencher()

    def _adicionar(self, estado: int, terminal: str, acao: Acao) -> None:
        celula = self.action.setdefault((estado, terminal), [])
        if acao not in celula:
            celula.append(acao)

    def _preencher(self) -> None:
        g = self.gramatica
        for (estado, simbolo), destino in self.colecao.transicoes.items():
            if g.eh_nao_terminal(simbolo):
                self.goto[(estado, simbolo)] = destino
            else:
                self._adicionar(estado, simbolo, Acao("s", destino))

        for numero, itens in enumerate(self.colecao.estados):
            for item in itens:
                if simbolo_apos_ponto(g, item) is not None:
                    continue                                 # item incompleto: já tratado acima
                producao = g.producoes[item.producao]
                if producao.numero == 0:                     # S' → S •
                    self._adicionar(numero, FIM, Acao("acc"))
                else:                                        # A → α •: reduz em FOLLOW(A)
                    for terminal in self.follow[producao.esquerda]:
                        self._adicionar(numero, terminal, Acao("r", producao.numero))

    # ------------------------------------------------------------ consultas

    @property
    def conflitos(self) -> list[ConflitoSLR]:
        ordem = {t: i for i, t in enumerate([*self.gramatica.terminais, FIM])}
        achados = [ConflitoSLR(e, t, a) for (e, t), a in self.action.items() if len(a) > 1]
        achados.sort(key=lambda c: (c.estado, ordem[c.terminal]))
        return achados

    @property
    def eh_slr1(self) -> bool:
        return not self.conflitos

    def acao(self, estado: int, terminal: str) -> Acao | None:
        """ACTION[estado, terminal]; em caso de conflito, a primeira ação (preferindo shift)."""
        celula = self.action.get((estado, terminal))
        return celula[0] if celula else None

    def esperados(self, estado: int) -> list[str]:
        ordem = {t: i for i, t in enumerate([*self.gramatica.terminais, FIM])}
        return sorted((t for (e, t) in self.action if e == estado), key=lambda t: ordem[t])

    # ------------------------------------------------------------ exibição

    def terminais_coluna(self) -> list[str]:
        return [*self.gramatica.terminais, FIM]

    def nao_terminais_coluna(self) -> list[str]:
        """Colunas de GOTO: todos os não-terminais, menos o símbolo S' aumentado."""
        return [nt for nt in self.gramatica.nao_terminais if nt != self.gramatica.inicial]

    def matriz(self) -> tuple[list[str], list[list[str]]]:
        """Tabela densa: Estado | ACTION (terminais e $) | GOTO (não-terminais)."""
        cols_a, cols_g = self.terminais_coluna(), self.nao_terminais_coluna()
        cabecalho = ["Estado", *cols_a, *cols_g]
        linhas = []
        for e in range(len(self.colecao.estados)):
            linha = [f"I{e}"]
            linha += ["/".join(map(str, self.action.get((e, t), []))) for t in cols_a]
            linha += [str(self.goto[(e, nt)]) if (e, nt) in self.goto else "" for nt in cols_g]
            linhas.append(linha)
        return cabecalho, linhas

    def tabela_compacta(self, largura: int = 120) -> str:
        """Visão para o terminal: por estado, as ações agrupadas (`s7: ID, NUM_INT`)
        e os desvios do GOTO."""
        ordem = {t: i for i, t in enumerate(self.terminais_coluna())}
        linhas = []
        for e in range(len(self.colecao.estados)):
            grupos: dict[Acao, list[str]] = {}
            for (est, t), acoes in self.action.items():
                if est == e:
                    for a in acoes:
                        grupos.setdefault(a, []).append(t)
            texto_action = "; ".join(
                f"{a}: " + ", ".join(sorted(ts, key=lambda t: ordem[t]))
                for a, ts in sorted(grupos.items(), key=lambda kv: (kv[0].tipo, kv[0].valor)))
            texto_goto = ", ".join(f"{nt}={self.goto[(e, nt)]}"
                                   for nt in self.nao_terminais_coluna() if (e, nt) in self.goto)
            linhas.append([f"I{e}", texto_action, texto_goto])
        return tabela_texto(["Estado", "ACTION (ação: terminais)", "GOTO"], linhas, largura_max=largura)

    def resumo(self) -> str:
        if self.eh_slr1:
            situacao = "ZERO conflitos: a gramática é SLR(1)"
        else:
            situacao = f"{len(self.conflitos)} conflito(s): a gramática NÃO é SLR(1)"
        return (f"Tabela SLR(1): {len(self.colecao.estados)} estados, "
                f"{len(self.action)} células em ACTION, {len(self.goto)} em GOTO; {situacao}.")


class AnalisadorSLR:
    """Algoritmo shift/reduce dirigido pela tabela SLR(1)."""

    def __init__(self, gramatica: Gramatica):
        self.tabela = TabelaSLR(gramatica)
        self.gramatica = self.tabela.gramatica

    def analisar_tokens(self, tokens: list[Token]) -> ResultadoAnalise:
        return self.analisar(de_tokens(tokens))

    def analisar(self, entrada: list[SimboloEntrada]) -> ResultadoAnalise:
        g, tabela = self.gramatica, self.tabela
        resultado = ResultadoAnalise()
        pilha: list[str | int] = [0]        # estados e símbolos intercalados: 0 X1 s1 X2 s2 ...
        pos = 0

        def registrar(acao: str) -> None:
            restante = " ".join(s.nome for s in entrada[pos:])
            resultado.passos.append(Passo(len(resultado.passos) + 1, " ".join(map(str, pilha)), restante, acao))

        limite_passos = 100 * (len(entrada) + 1) * (len(g.producoes) + 1)
        while True:
            if len(resultado.passos) > limite_passos:
                raise RuntimeError("análise SLR(1) não termina")
            estado = pilha[-1]
            atual = entrada[pos]
            acao = tabela.acao(estado, atual.nome)

            if acao is None:                                    # célula vazia: erro
                resultado.erros.append(erro_esperado(tabela.esperados(estado), entrada, pos))
                registrar(f"erro: ACTION[I{estado}, {atual.nome}] vazia")
                return resultado

            if acao.tipo == "s":
                registrar(f"shift {acao.valor}")
                pilha += [atual.nome, acao.valor]
                pos += 1
            elif acao.tipo == "r":
                producao = g.producoes[acao.valor]
                registrar(f"reduce {producao.numero}: {producao}")
                if producao.direita:
                    del pilha[len(pilha) - 2 * len(producao.direita):]   # remove |β| pares (símbolo, estado)
                pilha += [producao.esquerda, tabela.goto[(pilha[-1], producao.esquerda)]]
            else:                                                # accept
                registrar("aceita")
                return resultado
