"""
Nós da árvore sintática abstrata (AST) produzida pelo parser.

Cada nó sabe:
  - rotulo(): o texto que o representa na árvore impressa;
  - filhos(): a lista de filhos, na ordem em que aparecem.
Isso permite que um único código (em exibicao.py) desenhe qualquer árvore,
exporte para Graphviz ou para LaTeX, e que as próximas fases do compilador
(semântica, interpretação) percorram a mesma estrutura.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class No:
    linha: int = 0

    def rotulo(self) -> str:
        return type(self).__name__

    def filhos(self) -> list["No"]:
        return []


@dataclass
class Rotulo(No):
    """Nó auxiliar, só para agrupar filhos com um nome (ex.: 'condição')."""

    texto: str
    itens: list[No] = field(default_factory=list)

    def rotulo(self) -> str:
        return self.texto

    def filhos(self) -> list[No]:
        return self.itens


# ------------------------------------------------------------ estrutura


@dataclass
class Programa(No):
    declaracoes: list[No]  # funções e declarações globais, na ordem do código
    principal: Bloco

    def filhos(self):
        return [*self.declaracoes, Rotulo("Principal", [self.principal])]


@dataclass
class Parametro(No):
    nome: str
    tipo: str
    linha: int = 0

    def rotulo(self):
        return f"Parametro {self.nome}: {self.tipo}"


@dataclass
class Funcao(No):
    nome: str
    parametros: list[Parametro]
    tipo_retorno: str | None
    corpo: Bloco
    linha: int = 0

    def rotulo(self):
        retorno = f" -> {self.tipo_retorno}" if self.tipo_retorno else ""
        return f"Funcao {self.nome}{retorno}"

    def filhos(self):
        return [Rotulo("Parametros", list(self.parametros)), self.corpo]


@dataclass
class Bloco(No):
    comandos: list[No]

    def filhos(self):
        return self.comandos


# ------------------------------------------------------------ comandos


@dataclass
class Declaracao(No):
    nome: str
    tipo: str
    valor: No | None
    constante: bool = False
    linha: int = 0

    def rotulo(self):
        tipo = "Constante" if self.constante else "Declaracao"
        return f"{tipo} {self.nome}: {self.tipo}"

    def filhos(self):
        return [self.valor] if self.valor else []


@dataclass
class Atribuicao(No):
    nome: str
    valor: No
    linha: int = 0

    def rotulo(self):
        return f"Atribuicao {self.nome} ="

    def filhos(self):
        return [self.valor]


@dataclass
class Se(No):
    condicao: No
    entao: Bloco
    senao: No | None  # Bloco ou outro Se (senao se ...)
    linha: int = 0

    def filhos(self):
        itens: list[No] = [Rotulo("Condicao", [self.condicao]), Rotulo("Entao", [self.entao])]
        if self.senao:
            itens.append(Rotulo("Senao", [self.senao]))
        return itens


@dataclass
class Enquanto(No):
    condicao: No
    corpo: Bloco
    linha: int = 0

    def filhos(self):
        return [Rotulo("Condicao", [self.condicao]), self.corpo]


@dataclass
class Para(No):
    variavel: str
    inicio: No
    fim: No
    passo: No | None
    corpo: Bloco
    linha: int = 0

    def rotulo(self):
        return f"Para {self.variavel}"

    def filhos(self):
        itens: list[No] = [Rotulo("De", [self.inicio]), Rotulo("Ate", [self.fim])]
        if self.passo:
            itens.append(Rotulo("Passo", [self.passo]))
        return [*itens, self.corpo]


@dataclass
class Repita(No):
    corpo: Bloco
    condicao: No
    linha: int = 0

    def filhos(self):
        return [self.corpo, Rotulo("Ate", [self.condicao])]


@dataclass
class Retorne(No):
    valor: No | None
    linha: int = 0

    def filhos(self):
        return [self.valor] if self.valor else []


@dataclass
class Mostre(No):
    argumentos: list[No]
    linha: int = 0

    def filhos(self):
        return self.argumentos


@dataclass
class Leia(No):
    nome: str
    linha: int = 0

    def rotulo(self):
        return f"Leia {self.nome}"


@dataclass
class ComandoChamada(No):
    chamada: Chamada
    linha: int = 0

    def rotulo(self):
        return "ComandoChamada"

    def filhos(self):
        return [self.chamada]


# ------------------------------------------------------------ expressões


@dataclass
class Binaria(No):
    operador: str
    esquerda: No
    direita: No
    linha: int = 0

    def rotulo(self):
        return f"Binaria '{self.operador}'"

    def filhos(self):
        return [self.esquerda, self.direita]


@dataclass
class Unaria(No):
    operador: str
    operando: No
    linha: int = 0

    def rotulo(self):
        return f"Unaria '{self.operador}'"

    def filhos(self):
        return [self.operando]


@dataclass
class Literal(No):
    tipo: str  # inteiro, real, texto, logico
    valor: str
    linha: int = 0

    def rotulo(self):
        return f"Literal {self.tipo} {self.valor}"


@dataclass
class Variavel(No):
    nome: str
    linha: int = 0

    def rotulo(self):
        return f"Variavel {self.nome}"


@dataclass
class Chamada(No):
    nome: str
    argumentos: list[No]
    linha: int = 0

    def rotulo(self):
        return f"Chamada {self.nome}()"

    def filhos(self):
        return self.argumentos
