"""
Definição dos tokens da linguagem Maré.

Cada token produzido pelo analisador léxico possui:
  - tipo    : a classe do token (TipoToken)
  - lexema  : o trecho exato do código-fonte que foi reconhecido
  - linha   : linha onde o lexema começa (1-based)
  - coluna  : coluna onde o lexema começa (1-based)
"""

from dataclasses import dataclass
from enum import Enum


class Classe(Enum):
    """Classes de lexemas (agrupamento usado na tabela de tokens)."""

    PALAVRA_RESERVADA = "Palavra reservada"
    TIPO = "Tipo primitivo"
    IDENTIFICADOR = "Identificador"
    LITERAL = "Literal"
    OP_ARITMETICO = "Operador aritmético"
    OP_RELACIONAL = "Operador relacional"
    OP_LOGICO = "Operador lógico"
    ATRIBUICAO = "Atribuição"
    DELIMITADOR = "Delimitador"
    FIM = "Fim de arquivo"


class TipoToken(Enum):
    """Todos os tokens da linguagem. O valor é (nome, classe)."""

    # --- palavras reservadas (comandos e estrutura) ---
    PRINCIPAL = ("PRINCIPAL", Classe.PALAVRA_RESERVADA)
    FUNCAO = ("FUNCAO", Classe.PALAVRA_RESERVADA)
    SEJA = ("SEJA", Classe.PALAVRA_RESERVADA)
    FIXO = ("FIXO", Classe.PALAVRA_RESERVADA)
    SE = ("SE", Classe.PALAVRA_RESERVADA)
    SENAO = ("SENAO", Classe.PALAVRA_RESERVADA)
    ENQUANTO = ("ENQUANTO", Classe.PALAVRA_RESERVADA)
    PARA = ("PARA", Classe.PALAVRA_RESERVADA)
    DE = ("DE", Classe.PALAVRA_RESERVADA)
    ATE = ("ATE", Classe.PALAVRA_RESERVADA)
    PASSO = ("PASSO", Classe.PALAVRA_RESERVADA)
    REPITA = ("REPITA", Classe.PALAVRA_RESERVADA)
    RETORNE = ("RETORNE", Classe.PALAVRA_RESERVADA)
    MOSTRE = ("MOSTRE", Classe.PALAVRA_RESERVADA)
    LEIA = ("LEIA", Classe.PALAVRA_RESERVADA)

    # --- tipos primitivos ---
    T_INTEIRO = ("T_INTEIRO", Classe.TIPO)
    T_REAL = ("T_REAL", Classe.TIPO)
    T_LOGICO = ("T_LOGICO", Classe.TIPO)
    T_TEXTO = ("T_TEXTO", Classe.TIPO)

    # --- identificadores e literais ---
    ID = ("ID", Classe.IDENTIFICADOR)
    NUM_INT = ("NUM_INT", Classe.LITERAL)
    NUM_REAL = ("NUM_REAL", Classe.LITERAL)
    TEXTO = ("TEXTO", Classe.LITERAL)
    VERDADEIRO = ("VERDADEIRO", Classe.LITERAL)
    FALSO = ("FALSO", Classe.LITERAL)

    # --- operadores aritméticos ---
    MAIS = ("MAIS", Classe.OP_ARITMETICO)
    MENOS = ("MENOS", Classe.OP_ARITMETICO)
    MULT = ("MULT", Classe.OP_ARITMETICO)
    DIV = ("DIV", Classe.OP_ARITMETICO)
    MOD = ("MOD", Classe.OP_ARITMETICO)
    POT = ("POT", Classe.OP_ARITMETICO)

    # --- operadores relacionais ---
    IGUAL = ("IGUAL", Classe.OP_RELACIONAL)
    DIFERENTE = ("DIFERENTE", Classe.OP_RELACIONAL)
    MENOR = ("MENOR", Classe.OP_RELACIONAL)
    MENOR_IGUAL = ("MENOR_IGUAL", Classe.OP_RELACIONAL)
    MAIOR = ("MAIOR", Classe.OP_RELACIONAL)
    MAIOR_IGUAL = ("MAIOR_IGUAL", Classe.OP_RELACIONAL)

    # --- operadores lógicos (são palavras, mas formam sua própria classe) ---
    E = ("E", Classe.OP_LOGICO)
    OU = ("OU", Classe.OP_LOGICO)
    NAO = ("NAO", Classe.OP_LOGICO)

    # --- atribuição ---
    ATRIB = ("ATRIB", Classe.ATRIBUICAO)

    # --- delimitadores ---
    ABRE_PAR = ("ABRE_PAR", Classe.DELIMITADOR)
    FECHA_PAR = ("FECHA_PAR", Classe.DELIMITADOR)
    ABRE_CHAVE = ("ABRE_CHAVE", Classe.DELIMITADOR)
    FECHA_CHAVE = ("FECHA_CHAVE", Classe.DELIMITADOR)
    PONTO_VIRGULA = ("PONTO_VIRGULA", Classe.DELIMITADOR)
    VIRGULA = ("VIRGULA", Classe.DELIMITADOR)
    DOIS_PONTOS = ("DOIS_PONTOS", Classe.DELIMITADOR)
    SETA = ("SETA", Classe.DELIMITADOR)

    EOF = ("EOF", Classe.FIM)

    @property
    def nome(self) -> str:
        return self.value[0]

    @property
    def classe(self) -> Classe:
        return self.value[1]


# Palavras que, embora casem com a expressão regular de identificador,
# são reservadas pela linguagem.
PALAVRAS_RESERVADAS: dict[str, TipoToken] = {
    "principal": TipoToken.PRINCIPAL,
    "funcao": TipoToken.FUNCAO,
    "seja": TipoToken.SEJA,
    "fixo": TipoToken.FIXO,
    "se": TipoToken.SE,
    "senao": TipoToken.SENAO,
    "enquanto": TipoToken.ENQUANTO,
    "para": TipoToken.PARA,
    "de": TipoToken.DE,
    "ate": TipoToken.ATE,
    "passo": TipoToken.PASSO,
    "repita": TipoToken.REPITA,
    "retorne": TipoToken.RETORNE,
    "mostre": TipoToken.MOSTRE,
    "leia": TipoToken.LEIA,
    "inteiro": TipoToken.T_INTEIRO,
    "real": TipoToken.T_REAL,
    "logico": TipoToken.T_LOGICO,
    "texto": TipoToken.T_TEXTO,
    "verdadeiro": TipoToken.VERDADEIRO,
    "falso": TipoToken.FALSO,
    "e": TipoToken.E,
    "ou": TipoToken.OU,
    "nao": TipoToken.NAO,
}

# Operadores e delimitadores de símbolo. A ordem importa: os de dois
# caracteres vêm antes para que "<=" não seja lido como "<" seguido de "=".
SIMBOLOS: dict[str, TipoToken] = {
    "->": TipoToken.SETA,
    "==": TipoToken.IGUAL,
    "!=": TipoToken.DIFERENTE,
    "<=": TipoToken.MENOR_IGUAL,
    ">=": TipoToken.MAIOR_IGUAL,
    "<": TipoToken.MENOR,
    ">": TipoToken.MAIOR,
    "=": TipoToken.ATRIB,
    "+": TipoToken.MAIS,
    "-": TipoToken.MENOS,
    "*": TipoToken.MULT,
    "/": TipoToken.DIV,
    "%": TipoToken.MOD,
    "^": TipoToken.POT,
    "(": TipoToken.ABRE_PAR,
    ")": TipoToken.FECHA_PAR,
    "{": TipoToken.ABRE_CHAVE,
    "}": TipoToken.FECHA_CHAVE,
    ";": TipoToken.PONTO_VIRGULA,
    ",": TipoToken.VIRGULA,
    ":": TipoToken.DOIS_PONTOS,
}


@dataclass(frozen=True)
class Token:
    tipo: TipoToken
    lexema: str
    linha: int
    coluna: int

    def __str__(self) -> str:
        return f"<{self.tipo.nome}, '{self.lexema}', {self.linha}:{self.coluna}>"
