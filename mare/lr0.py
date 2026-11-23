"""
Coleção canônica de itens LR(0).

Um item LR(0) é uma produção com um ponto (•) marcando até onde já se
reconheceu: `A → α • β` significa "já vi α e espero ver β". Cada conjunto de
itens é um *estado* do autômato LR(0), cujas transições são feitas por
símbolos (terminais e não-terminais).

Duas operações constroem o autômato:

  closure(I)   acrescenta a I todos os itens `B → • γ` para cada `A → α • B β`
               já presente (se espero um B, espero qualquer coisa que B derive),
               repetindo até nada mais ser acrescentado;
  goto(I, X)   avança o ponto sobre X nos itens de I em que X vem logo depois
               do ponto, e aplica closure ao resultado.

A coleção canônica parte de I0 = closure({S' → • S}) e aplica goto com todos os
símbolos a cada estado novo, até não surgirem mais estados.
"""

from __future__ import annotations

from typing import NamedTuple

from .gramatica import Gramatica, Producao, formatar_cadeia


class Item(NamedTuple):
    """Item LR(0): produção (pelo número) e posição do ponto (0 = antes do 1º símbolo)."""

    producao: int
    ponto: int


Estado = frozenset[Item]


def eh_aumentada(g: Gramatica) -> bool:
    """Verdadeiro se a gramática já tem a forma S' → S (símbolo inicial com uma
    única produção, de um só símbolo, e que não aparece em nenhum lado direito)."""
    inicial = g.inicial
    producoes = g.por_nao_terminal[inicial]
    usado_a_direita = any(inicial in p.direita for p in g.producoes)
    return len(producoes) == 1 and len(producoes[0].direita) == 1 and not usado_a_direita


def garantir_aumentada(g: Gramatica) -> Gramatica:
    """Devolve a própria gramática se já for aumentada; senão, acrescenta S' → S."""
    return g if eh_aumentada(g) else g.aumentada()


def simbolo_apos_ponto(g: Gramatica, item: Item) -> str | None:
    """Símbolo logo depois do ponto, ou None se o ponto está no fim (item completo)."""
    direita = g.producoes[item.producao].direita
    return direita[item.ponto] if item.ponto < len(direita) else None


def closure(g: Gramatica, itens: set[Item] | frozenset[Item]) -> Estado:
    """Fecho de um conjunto de itens (ver descrição no topo do módulo)."""
    fecho = set(itens)
    pendentes = list(itens)
    while pendentes:
        item = pendentes.pop()
        simbolo = simbolo_apos_ponto(g, item)
        if simbolo is not None and g.eh_nao_terminal(simbolo):
            for p in g.por_nao_terminal[simbolo]:
                novo = Item(p.numero, 0)
                if novo not in fecho:
                    fecho.add(novo)
                    pendentes.append(novo)
    return frozenset(fecho)


def goto(g: Gramatica, estado: Estado, simbolo: str) -> Estado:
    """Estado alcançado a partir de `estado` lendo `simbolo` (vazio se não há transição)."""
    avancados = {Item(i.producao, i.ponto + 1) for i in estado if simbolo_apos_ponto(g, i) == simbolo}
    return closure(g, avancados) if avancados else frozenset()


class ColecaoLR0:
    """Coleção canônica de conjuntos de itens LR(0) de uma gramática aumentada."""

    def __init__(self, gramatica: Gramatica):
        self.gramatica = garantir_aumentada(gramatica)
        self.estados: list[Estado] = []
        self.transicoes: dict[tuple[int, str], int] = {}
        # Itens "núcleo" de cada estado (os que não vieram do closure): úteis
        # para exibir e para reconhecer estados repetidos.
        self.nucleos: list[frozenset[Item]] = []
        self._construir()

    def _construir(self) -> None:
        g = self.gramatica
        inicial = closure(g, {Item(0, 0)})
        indice: dict[Estado, int] = {inicial: 0}
        self.estados.append(inicial)
        self.nucleos.append(frozenset({Item(0, 0)}))
        simbolos = [*g.nao_terminais, *g.terminais]       # ordem fixa => numeração estável

        fila = [0]
        while fila:
            numero = fila.pop(0)                            # busca em largura: I0, I1, I2...
            for simbolo in simbolos:
                destino = goto(g, self.estados[numero], simbolo)
                if not destino:
                    continue
                if destino not in indice:
                    indice[destino] = len(self.estados)
                    self.estados.append(destino)
                    self.nucleos.append(self._nucleo(self.estados[numero], simbolo))
                    fila.append(indice[destino])
                self.transicoes[(numero, simbolo)] = indice[destino]

    def _nucleo(self, origem: Estado, simbolo: str) -> frozenset[Item]:
        g = self.gramatica
        return frozenset(Item(i.producao, i.ponto + 1) for i in origem if simbolo_apos_ponto(g, i) == simbolo)

    # ------------------------------------------------------------ exibição

    def formatar_item(self, item: Item) -> str:
        p: Producao = self.gramatica.producoes[item.producao]
        antes = formatar_cadeia(p.direita[:item.ponto]) if item.ponto else ""
        depois = " ".join(p.direita[item.ponto:])
        partes = [x for x in (antes, "•", depois) if x]
        return f"{p.esquerda} → {' '.join(partes)}"

    def _ordenar(self, itens: frozenset[Item]) -> list[Item]:
        return sorted(itens, key=lambda i: (i.producao, i.ponto))

    def formatar_estado(self, numero: int, mostrar_fecho: bool = True) -> str:
        """Itens do estado Ik; com `mostrar_fecho=False`, só os itens do núcleo.
        Em seguida, as transições que saem do estado."""
        nucleo = self.nucleos[numero]
        itens = self.estados[numero] if mostrar_fecho else nucleo
        linhas = [f"I{numero}:"]
        for item in self._ordenar(nucleo):
            linhas.append(f"    {self.formatar_item(item)}")
        if mostrar_fecho:
            for item in self._ordenar(itens - nucleo):
                linhas.append(f"    {self.formatar_item(item)}")
        saidas = [(s, d) for (e, s), d in self.transicoes.items() if e == numero]
        for simbolo, destino in saidas:
            linhas.append(f"    goto(I{numero}, {simbolo}) = I{destino}")
        return "\n".join(linhas)

    def formatar(self, mostrar_fecho: bool = True) -> str:
        """Todos os estados, com itens (ponto •) e transições."""
        return "\n\n".join(self.formatar_estado(i, mostrar_fecho) for i in range(len(self.estados)))

    def resumo(self) -> str:
        return (f"{len(self.estados)} estados LR(0) (I0 a I{len(self.estados) - 1}), "
                f"{len(self.transicoes)} transições.")
