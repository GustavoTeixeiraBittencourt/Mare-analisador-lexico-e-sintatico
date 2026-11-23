"""
Analisador sintático LL(1) guiado por tabela, com pilha explícita.

Ao contrário do parser descendente recursivo (parser.py), aqui NÃO existe um
método por regra: o "conhecimento" da gramática está inteiro na tabela
preditiva M[A, a], construída automaticamente a partir de FIRST e FOLLOW.

Construção da tabela (para cada produção A -> α):
  1. para cada terminal a ∈ FIRST(α):             M[A, a] recebe A -> α
  2. se ε ∈ FIRST(α), para cada b ∈ FOLLOW(A):    M[A, b] recebe A -> α
     (b pode ser o marcador $)
A gramática é LL(1) se e somente se nenhuma célula receber mais de uma produção.

Algoritmo preditivo com pilha:
  * a pilha começa com `$ S` (símbolo inicial no topo);
  * topo é terminal:      se for igual ao token atual, MATCH (desempilha e avança);
                          senão, erro;
  * topo é não-terminal:  consulta M[topo, token]; se há produção A -> X1...Xn,
                          desempilha A e empilha Xn ... X1 (X1 fica no topo);
                          se a célula está vazia, erro;
  * topo é $ e a entrada é $: aceita.

Recuperação de erros (modo pânico): ao errar com o não-terminal A no topo,
descartam-se tokens até aparecer um que esteja em FOLLOW(A) (o conjunto de
sincronização); então A é desempilhado, como se tivesse derivado ε. Se o erro
for um terminal esperado que não veio, ele é desempilhado (como se tivesse sido
inserido). Erros repetidos na mesma posição são suprimidos para evitar cascata.
"""

from __future__ import annotations

from dataclasses import dataclass

from .entrada import SimboloEntrada, de_tokens, erro_esperado
from .first_follow import Conjuntos, calcular_first, calcular_follow, first_de_cadeia
from .gramatica import EPSILON, FIM, Gramatica, Producao
from .rastro import Passo, ResultadoAnalise
from .tabelas import tabela_texto
from .tokens import Token


@dataclass
class ConflitoLL1:
    """Célula M[A, a] com mais de uma produção: a gramática não é LL(1)."""

    nao_terminal: str
    terminal: str
    producoes: list[Producao]

    def __str__(self) -> str:
        alternativas = "  /  ".join(str(p) for p in self.producoes)
        return f"conflito em M[{self.nao_terminal}, {self.terminal}]: {alternativas}"


class TabelaLL1:
    """Tabela preditiva M[A, a] e os conflitos encontrados ao construí-la."""

    def __init__(self, gramatica: Gramatica):
        self.gramatica = gramatica
        self.first: Conjuntos = calcular_first(gramatica)
        self.follow: Conjuntos = calcular_follow(gramatica, self.first)
        self.celulas: dict[tuple[str, str], list[Producao]] = {}
        self._preencher()

    def _preencher(self) -> None:
        for p in self.gramatica.producoes:
            first_alfa = first_de_cadeia(p.direita, self.first)
            # Regra 1: terminais que podem iniciar a cadeia α.
            candidatos = first_alfa - {EPSILON}
            # Regra 2: se α pode sumir, A -> α vale quando vem algo de FOLLOW(A).
            if EPSILON in first_alfa:
                candidatos |= self.follow[p.esquerda]
            for terminal in candidatos:
                self.celulas.setdefault((p.esquerda, terminal), []).append(p)

    @property
    def conflitos(self) -> list[ConflitoLL1]:
        """Células com mais de uma produção, em ordem estável."""
        ordem = self._ordem_terminais()
        achados = [ConflitoLL1(nt, t, ps) for (nt, t), ps in self.celulas.items() if len(ps) > 1]
        achados.sort(key=lambda c: (self.gramatica.nao_terminais.index(c.nao_terminal), ordem[c.terminal]))
        return achados

    @property
    def eh_ll1(self) -> bool:
        return not self.conflitos

    def _ordem_terminais(self) -> dict[str, int]:
        ordem = {t: i for i, t in enumerate(self.gramatica.terminais)}
        ordem[FIM] = len(ordem)
        return ordem

    def producao(self, nao_terminal: str, terminal: str) -> Producao | None:
        """M[A, a]; em caso de conflito, usa a primeira produção da célula."""
        celula = self.celulas.get((nao_terminal, terminal))
        return celula[0] if celula else None

    def esperados(self, nao_terminal: str) -> list[str]:
        """Terminais com entrada na linha de A (o que seria aceito ali)."""
        ordem = self._ordem_terminais()
        achados = {t for (nt, t) in self.celulas if nt == nao_terminal}
        return sorted(achados, key=lambda t: ordem[t])

    # ------------------------------------------------------------ exibição

    def colunas(self) -> list[str]:
        return [*self.gramatica.terminais, FIM]

    def matriz(self) -> tuple[list[str], list[list[str]]]:
        """Tabela densa (linhas = não-terminais, colunas = terminais e $).
        Cada célula traz o número da produção; células com conflito mostram
        todos os números separados por '/'; células vazias ficam em branco."""
        cabecalho = ["", *self.colunas()]
        linhas = []
        for nt in self.gramatica.nao_terminais:
            linha = [nt]
            for t in self.colunas():
                celula = self.celulas.get((nt, t), [])
                linha.append("/".join(str(p.numero) for p in celula))
            linhas.append(linha)
        return cabecalho, linhas

    def tabela_compacta(self, largura: int = 110) -> str:
        """Visão compacta para o terminal: uma linha por produção, listando os
        terminais (lookahead) em que ela é escolhida."""
        linhas = []
        ordem = self._ordem_terminais()
        for nt in self.gramatica.nao_terminais:
            for p in self.gramatica.por_nao_terminal[nt]:
                terminais = sorted((t for (n, t), ps in self.celulas.items() if n == nt and p in ps),
                                   key=lambda t: ordem[t])
                linhas.append([nt, ", ".join(terminais), f"{p.numero}. {p}"])
        return tabela_texto(["M[A, ·]", "Lookahead (terminais)", "Produção"], linhas, largura_max=largura)

    def resumo(self) -> str:
        preenchidas = len(self.celulas)
        total = len(self.gramatica.nao_terminais) * len(self.colunas())
        if self.eh_ll1:
            situacao = "ZERO conflitos: a gramática é LL(1)"
        else:
            situacao = f"{len(self.conflitos)} conflito(s): a gramática NÃO é LL(1)"
        return f"Tabela LL(1): {preenchidas} células preenchidas de {total}; {situacao}."


class AnalisadorLL1:
    """Análise preditiva com pilha, usando a tabela LL(1) de uma gramática."""

    def __init__(self, gramatica: Gramatica):
        self.tabela = TabelaLL1(gramatica)
        self.gramatica = gramatica

    def analisar_tokens(self, tokens: list[Token]) -> ResultadoAnalise:
        """Analisa a cadeia de tokens gerada pelo Lexer."""
        return self.analisar(de_tokens(tokens))

    def analisar(self, entrada: list[SimboloEntrada]) -> ResultadoAnalise:
        g, tabela = self.gramatica, self.tabela
        resultado = ResultadoAnalise()
        pilha: list[str] = [FIM, g.inicial]
        pos = 0
        pos_ultimo_erro = -1   # evita reportar vários erros para o mesmo token

        def registrar(acao: str) -> None:
            restante = " ".join(s.nome for s in entrada[pos:])
            resultado.passos.append(Passo(len(resultado.passos) + 1, " ".join(pilha), restante, acao))

        def erro(esperados: list[str]) -> None:
            nonlocal pos_ultimo_erro
            if pos != pos_ultimo_erro:
                resultado.erros.append(erro_esperado(esperados, entrada, pos))
                pos_ultimo_erro = pos

        limite_passos = 100 * (len(entrada) + 1) * (len(g.producoes) + 1)  # proteção contra gramática recursiva à esquerda
        while pilha:
            if len(resultado.passos) > limite_passos:
                raise RuntimeError("análise LL(1) não termina: a gramática tem recursão à esquerda?")
            topo = pilha[-1]
            atual = entrada[pos].nome

            if topo == FIM:
                if atual == FIM:
                    registrar("aceita")
                else:
                    erro([FIM])
                    registrar(f"erro: sobrou '{entrada[pos].lexema}' após o fim do programa")
                break

            if g.eh_terminal(topo):
                if topo == atual:
                    registrar(f"match {topo}")
                    pilha.pop()
                    pos += 1
                else:
                    erro([topo])
                    registrar(f"erro: esperado {topo}, encontrado {atual}; desempilha {topo}")
                    pilha.pop()          # supõe que o terminal faltante foi inserido
                continue

            producao = tabela.producao(topo, atual)
            if producao is not None:
                registrar(str(producao))
                pilha.pop()
                pilha.extend(reversed(producao.direita))   # X1 fica no topo
                continue

            # Célula vazia: erro. Modo pânico com FOLLOW(topo) como sincronização.
            erro(tabela.esperados(topo))
            descartados = []
            sincronia = tabela.follow[topo] | {FIM}
            while entrada[pos].nome not in sincronia:
                descartados.append(entrada[pos].nome)
                pos += 1
            extra = f"; descarta {' '.join(descartados)}" if descartados else ""
            registrar(f"erro: M[{topo}, {atual}] vazia{extra}; desempilha {topo}")
            pilha.pop()

        return resultado
