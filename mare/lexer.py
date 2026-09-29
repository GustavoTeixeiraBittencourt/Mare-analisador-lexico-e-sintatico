"""
Analisador léxico (scanner) da linguagem Maré.

Implementação pura, sem geradores: cada classe de lexema é descrita por uma
expressão regular. As expressões são combinadas em uma única regex mestre com
grupos nomeados (alternância ordenada). Em cada posição do código-fonte a regex
mestre é aplicada e o nome do grupo que casou indica a classe do lexema.

A ordem das regras resolve ambiguidades:
  * comentário de bloco antes de comentário de linha ("#*" x "#");
  * número malformado antes de número válido ("12abc" é erro, não 12 + abc);
  * real antes de inteiro ("3.14" não vira 3, ".", 14);
  * nos símbolos, os de 2 caracteres antes dos de 1 ("<=" antes de "<").
Palavras reservadas casam com a regex de identificador e depois são
reclassificadas por consulta à tabela PALAVRAS_RESERVADAS.
"""

import re

from .erros import ErroLexico
from .tokens import PALAVRAS_RESERVADAS, SIMBOLOS, Token, TipoToken

# (nome da regra, expressão regular) — a ordem é significativa.
REGRAS_LEXICAS: list[tuple[str, str]] = [
    ("ESPACO", r"[ \t\r]+"),
    ("NOVA_LINHA", r"\n"),
    ("COMENTARIO_BLOCO", r"\#\*[\s\S]*?\*\#"),
    ("COMENTARIO_ABERTO", r"\#\*"),
    ("COMENTARIO_LINHA", r"\#[^\n]*"),
    ("NUM_INVALIDO", r"\d+(?:\.\d+)?[A-Za-z_]\w*|\d+\.(?!\d)"),
    ("NUM_REAL", r"\d+\.\d+"),
    ("NUM_INT", r"\d+"),
    ("TEXTO", r'"(?:\\.|[^"\\\n])*"'),
    ("TEXTO_ABERTO", r'"(?:\\.|[^"\\\n])*'),
    ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("SIMBOLO", r"->|==|!=|<=|>=|[<>=+\-*/%^(){};,:]"),
    ("DESCONHECIDO", r"."),
]

REGEX_MESTRE = re.compile("|".join(f"(?P<{nome}>{regex})" for nome, regex in REGRAS_LEXICAS))


class Lexer:
    def __init__(self, fonte: str):
        self.fonte = fonte
        self.erros: list[ErroLexico] = []

    def tokenizar(self) -> list[Token]:
        """Percorre todo o código e devolve a cadeia de tokens (termina em EOF).

        Erros léxicos não interrompem a varredura: são acumulados em
        self.erros para que todos sejam reportados de uma vez.
        """
        tokens: list[Token] = []
        linha, inicio_linha = 1, 0

        for m in REGEX_MESTRE.finditer(self.fonte):
            regra = m.lastgroup
            lexema = m.group()
            coluna = m.start() - inicio_linha + 1

            if regra == "NOVA_LINHA":
                linha += 1
                inicio_linha = m.end()
            elif regra in ("ESPACO", "COMENTARIO_LINHA"):
                pass
            elif regra == "COMENTARIO_BLOCO":
                quebras = lexema.count("\n")
                if quebras:
                    linha += quebras
                    inicio_linha = m.start() + lexema.rfind("\n") + 1
            elif regra == "ID":
                tipo = PALAVRAS_RESERVADAS.get(lexema, TipoToken.ID)
                tokens.append(Token(tipo, lexema, linha, coluna))
            elif regra == "NUM_INT":
                tokens.append(Token(TipoToken.NUM_INT, lexema, linha, coluna))
            elif regra == "NUM_REAL":
                tokens.append(Token(TipoToken.NUM_REAL, lexema, linha, coluna))
            elif regra == "TEXTO":
                tokens.append(Token(TipoToken.TEXTO, lexema, linha, coluna))
            elif regra == "SIMBOLO":
                tokens.append(Token(SIMBOLOS[lexema], lexema, linha, coluna))
            elif regra == "NUM_INVALIDO":
                self._erro(f"número malformado '{lexema}'", linha, coluna)
            elif regra == "TEXTO_ABERTO":
                self._erro("texto não foi fechado com aspas (\") antes do fim da linha", linha, coluna)
            elif regra == "COMENTARIO_ABERTO":
                self._erro("comentário de bloco '#*' não foi fechado com '*#'", linha, coluna)
                break  # o resto do arquivo seria comentário
            else:  # DESCONHECIDO
                dica = " (identificadores não aceitam acentos)" if lexema.isalpha() else ""
                self._erro(f"caractere inválido '{lexema}'{dica}", linha, coluna)

        coluna_eof = len(self.fonte) - inicio_linha + 1
        tokens.append(Token(TipoToken.EOF, "", linha, coluna_eof))
        return tokens

    def _erro(self, mensagem: str, linha: int, coluna: int) -> None:
        self.erros.append(ErroLexico(mensagem, linha, coluna))


def tokenizar(fonte: str) -> list[Token]:
    """Atalho: tokeniza e lança o primeiro erro léxico, se houver."""
    lexer = Lexer(fonte)
    tokens = lexer.tokenizar()
    if lexer.erros:
        raise lexer.erros[0]
    return tokens
