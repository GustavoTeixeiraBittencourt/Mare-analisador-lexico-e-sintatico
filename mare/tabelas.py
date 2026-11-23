"""
Formatação de tabelas para o terminal e exportação (.txt, .md, .csv).

As tabelas dos analisadores (FIRST/FOLLOW, LL(1), ACTION/GOTO, rastros) podem
ser largas demais para o terminal. Por isso a tabela em texto quebra o conteúdo
das células em várias linhas quando passa de `largura_max`, e os mesmos dados
podem ser exportados inteiros para arquivo.
"""

from __future__ import annotations

import csv
import io
import textwrap


def _quebrar(texto: str, largura: int) -> list[str]:
    """Quebra o texto em linhas de até `largura` caracteres (preferindo espaços)."""
    if len(texto) <= largura:
        return [texto]
    return textwrap.wrap(texto, width=largura, break_long_words=True, break_on_hyphens=False) or [""]


def _ajustar_larguras(larguras: list[int], largura_max: int | None, minimo: int = 10) -> list[int]:
    """Estreita a coluna mais larga, repetidamente, até a tabela caber."""
    if largura_max is None:
        return larguras
    larguras = larguras[:]
    sobra = lambda: sum(w + 3 for w in larguras) + 1 - largura_max
    while sobra() > 0:
        i = max(range(len(larguras)), key=lambda k: larguras[k])
        if larguras[i] <= minimo:
            break  # não dá para estreitar mais; deixa passar da margem
        larguras[i] -= 1  # tira 1 da mais larga por vez: reparte a perda entre as colunas
    return larguras


def tabela_texto(cabecalho: list[str], linhas: list[list[str]], largura_max: int | None = None,
                 separar_linhas: bool = False) -> str:
    """Tabela ASCII com bordas. Células longas são quebradas em várias linhas."""
    larguras = [max(len(str(c)) for c in col) for col in zip(cabecalho, *linhas)] if linhas \
        else [len(c) for c in cabecalho]
    larguras = _ajustar_larguras(larguras, largura_max)
    borda = "+" + "+".join("-" * (w + 2) for w in larguras) + "+"

    def formatar(celulas: list[str]) -> list[str]:
        pedacos = [_quebrar(str(c), w) for c, w in zip(celulas, larguras)]
        altura = max(len(p) for p in pedacos)
        saida = []
        for k in range(altura):
            partes = [(p[k] if k < len(p) else "").ljust(w) for p, w in zip(pedacos, larguras)]
            saida.append("| " + " | ".join(partes) + " |")
        return saida

    saida = [borda, *formatar(cabecalho), borda]
    for linha in linhas:
        saida.extend(formatar(linha))
        if separar_linhas:
            saida.append(borda)
    if not separar_linhas:
        saida.append(borda)
    return "\n".join(saida)


def tabela_markdown(cabecalho: list[str], linhas: list[list[str]]) -> str:
    """Tabela em Markdown (o caractere `|` dentro das células é escapado)."""
    def esc(c: object) -> str:
        return str(c).replace("|", "\\|")

    saida = ["| " + " | ".join(esc(c) for c in cabecalho) + " |",
             "|" + "|".join("---" for _ in cabecalho) + "|"]
    saida += ["| " + " | ".join(esc(c) for c in linha) + " |" for linha in linhas]
    return "\n".join(saida)


def tabela_csv(cabecalho: list[str], linhas: list[list[str]]) -> str:
    """Tabela em CSV (separador ';' para abrir direto no Excel em português)."""
    buffer = io.StringIO()
    escritor = csv.writer(buffer, delimiter=";", lineterminator="\n")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return buffer.getvalue().rstrip("\n")


def formatar_por_extensao(caminho: str, cabecalho: list[str], linhas: list[list[str]]) -> str:
    """Escolhe o formato pela extensão do arquivo de saída (.csv, .md ou texto)."""
    extensao = caminho.lower().rsplit(".", 1)[-1] if "." in caminho else ""
    if extensao == "csv":
        return tabela_csv(cabecalho, linhas)
    if extensao in ("md", "markdown"):
        return tabela_markdown(cabecalho, linhas)
    return tabela_texto(cabecalho, linhas)
