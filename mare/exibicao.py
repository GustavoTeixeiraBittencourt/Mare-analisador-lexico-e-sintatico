"""Funções de exibição: tabelas de tokens, cadeia de tokens e árvore sintática."""

from __future__ import annotations

from collections import OrderedDict

from .arvore import No
from .lexer import REGRAS_LEXICAS
from .tokens import Classe, Token, TipoToken


def _tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    larguras = [max(len(str(c)) for c in col) for col in zip(cabecalho, *linhas)]
    borda = "+" + "+".join("-" * (w + 2) for w in larguras) + "+"

    def fmt(cols):
        return "| " + " | ".join(str(c).ljust(w) for c, w in zip(cols, larguras)) + " |"

    return "\n".join([borda, fmt(cabecalho), borda, *(fmt(l) for l in linhas), borda])


def tabela_cadeia(tokens: list[Token]) -> str:
    """Cada token na ordem em que aparece no código (cadeia de tokens)."""
    linhas = [
        [str(i), f"{t.linha}:{t.coluna}", t.lexema or "(fim)", t.tipo.nome, t.tipo.classe.value]
        for i, t in enumerate(tokens, 1)
    ]
    return _tabela(["#", "Lin:Col", "Lexema", "Token", "Classe"], linhas)


def cadeia_compacta(tokens: list[Token], por_linha: bool = True) -> str:
    """Cadeia de tokens no formato <TOKEN, lexema>, agrupada por linha do código."""

    def fmt(t: Token) -> str:
        if t.tipo in (TipoToken.ID, TipoToken.NUM_INT, TipoToken.NUM_REAL, TipoToken.TEXTO):
            return f"<{t.tipo.nome}, {t.lexema}>"
        return f"<{t.tipo.nome}>"

    if not por_linha:
        return " ".join(fmt(t) for t in tokens)
    grupos: OrderedDict[int, list[str]] = OrderedDict()
    for t in tokens:
        grupos.setdefault(t.linha, []).append(fmt(t))
    return "\n".join(f"{linha:>4} | {' '.join(itens)}" for linha, itens in grupos.items())


def tabela_lexemas(tokens: list[Token]) -> str:
    """Tabela de lexemas distintos: lexema, token, classe e nº de ocorrências."""
    contagem: OrderedDict[tuple[str, TipoToken], int] = OrderedDict()
    for t in tokens:
        if t.tipo is TipoToken.EOF:
            continue
        chave = (t.lexema, t.tipo)
        contagem[chave] = contagem.get(chave, 0) + 1
    ordem_classe = {c: i for i, c in enumerate(Classe)}
    itens = sorted(contagem.items(), key=lambda kv: (ordem_classe[kv[0][1].classe], kv[0][1].nome, kv[0][0]))
    linhas = [[lex, tipo.nome, tipo.classe.value, str(n)] for (lex, tipo), n in itens]
    return _tabela(["Lexema", "Token", "Classe", "Ocorrências"], linhas)


def tabela_regras() -> str:
    """Expressões regulares usadas pelo scanner, na ordem de prioridade."""
    linhas = [[str(i), nome, regex] for i, (nome, regex) in enumerate(REGRAS_LEXICAS, 1)]
    return _tabela(["Prior.", "Regra", "Expressão regular"], linhas)


def resumo_classes(tokens: list[Token]) -> str:
    contagem: OrderedDict[Classe, int] = OrderedDict((c, 0) for c in Classe)
    for t in tokens:
        contagem[t.tipo.classe] += 1
    linhas = [[c.value, str(n)] for c, n in contagem.items() if n]
    linhas.append(["TOTAL", str(len(tokens))])
    return _tabela(["Classe de lexema", "Tokens"], linhas)


# ------------------------------------------------------------ árvore


def arvore_texto(no: No) -> str:
    """Desenha a árvore com caracteres de caixa (├──, └──)."""
    saida = [no.rotulo()]

    def visitar(atual: No, prefixo: str) -> None:
        filhos = atual.filhos()
        for i, filho in enumerate(filhos):
            ultimo = i == len(filhos) - 1
            saida.append(prefixo + ("└── " if ultimo else "├── ") + filho.rotulo())
            visitar(filho, prefixo + ("    " if ultimo else "│   "))

    visitar(no, "")
    return "\n".join(saida)


def arvore_dot(no: No) -> str:
    """Exporta a árvore no formato DOT do Graphviz (dot -Tpng arvore.dot -o arvore.png)."""
    linhas = [
        "digraph AST {",
        '  node [shape=box, style="rounded,filled", fillcolor="#eef4fb", fontname="Helvetica", fontsize=10];',
        '  edge [color="#555555"];',
    ]
    contador = [0]

    def visitar(atual: No) -> str:
        ident = f"n{contador[0]}"
        contador[0] += 1
        rotulo = atual.rotulo().replace("\\", "\\\\").replace('"', '\\"')
        linhas.append(f'  {ident} [label="{rotulo}"];')
        for filho in atual.filhos():
            linhas.append(f"  {ident} -> {visitar(filho)};")
        return ident

    visitar(no)
    linhas.append("}")
    return "\n".join(linhas)


def arvore_forest(no: No) -> str:
    """Exporta a árvore para o pacote LaTeX 'forest' (usado no artigo)."""
    especiais = str.maketrans({c: f"\\{c}" for c in "#$%&_{}"} | {"^": r"\^{}", "\\": r"\textbackslash{}"})

    def visitar(atual: No) -> str:
        rotulo = atual.rotulo().translate(especiais).replace("'", "")
        filhos = "".join(" " + visitar(f) for f in atual.filhos())
        return f"[{{{rotulo}}}{filhos}]"

    return visitar(no)
