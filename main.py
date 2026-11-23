import argparse
import pathlib
import sys

from mare import exibicao
from mare.erros import mostrar_contexto
from mare.conversor import ErroConversor, converter_arquivo, gramatica_como_arquivo, relatorio_final
from mare.first_follow import calcular_first, calcular_follow, tabela_first_follow
from mare.gramatica import Gramatica
from mare.lexer import Lexer
from mare.ll1 import AnalisadorLL1, TabelaLL1
from mare.lr0 import ColecaoLR0
from mare.parser import Parser
from mare.rastro import CABECALHO_RASTRO, ResultadoAnalise, linhas_rastro, tabela_rastro
from mare.slr import AnalisadorSLR, TabelaSLR
from mare.tabelas import formatar_por_extensao

USA_COR = sys.stdout.isatty()
PASTA_GRAMATICAS = pathlib.Path(__file__).resolve().parent / "gramaticas"
GRAMATICA_LL1 = PASTA_GRAMATICAS / "mare_ll1.txt"
GRAMATICA_SLR = PASTA_GRAMATICAS / "mare_slr.txt"


def titulo(texto: str) -> None:
    linha = "=" * 78
    if USA_COR:
        print(f"\n\033[1;36m{linha}\n  {texto}\n{linha}\033[0m")
    else:
        print(f"\n{linha}\n  {texto}\n{linha}")


def status(ok: bool, texto: str) -> None:
    marca = "[OK]" if ok else "[ERRO]"
    if USA_COR:
        cor = "32" if ok else "31"
        marca = f"\033[1;{cor}m{marca}\033[0m"
    print(f"{marca} {texto}")


class Exportador:
    """Guarda as saídas "tabulares" pedidas na linha de comando para gravá-las
    inteiras (sem abreviações) em um arquivo, quando --saida é usada. O formato
    sai da extensão: .csv, .md ou texto (.txt)."""

    def __init__(self, caminho: str | None):
        self.caminho = caminho
        self.secoes: list[str] = []

    def tabela(self, nome: str, cabecalho: list[str], linhas: list[list[str]]) -> None:
        if self.caminho:
            self.secoes.append(self._com_titulo(nome, formatar_por_extensao(self.caminho, cabecalho, linhas)))

    def texto(self, nome: str, conteudo: str) -> None:
        if self.caminho:
            self.secoes.append(self._com_titulo(nome, conteudo))

    def _com_titulo(self, nome: str, corpo: str) -> str:
        return corpo if self.caminho.lower().endswith(".csv") else f"# {nome}\n\n{corpo}"

    def gravar(self) -> None:
        if self.caminho and self.secoes:
            with open(self.caminho, "w", encoding="utf-8") as f:
                f.write("\n\n".join(self.secoes) + "\n")
            print(f"\nSaída completa gravada em {self.caminho}")


def carregar_gramatica(caminho: pathlib.Path) -> Gramatica:
    return Gramatica.de_arquivo(str(caminho))


# ------------------------------------------------------------------ gramáticas


def mostrar_gramaticas(args, saida: Exportador) -> None:
    """Opções que só dependem das gramáticas (não precisam de código-fonte)."""
    g_ll1 = carregar_gramatica(GRAMATICA_LL1)
    g_slr = carregar_gramatica(GRAMATICA_SLR)

    if args.gramatica_ll1:
        titulo("GRAMÁTICA DA MARÉ EM BNF — FORMATO LL(1)")
        print(g_ll1.formatar())
        print(f"\n{g_ll1.resumo()}")
        saida.texto("Gramática LL(1)", g_ll1.formatar())

    if args.first_follow:
        g = g_slr if args.parser == "slr" else g_ll1
        first = calcular_first(g)
        follow = calcular_follow(g, first)
        titulo(f"FIRST E FOLLOW ({'SLR' if g is g_slr else 'LL(1)'}) — ponto fixo iterativo")
        print(tabela_first_follow(g, first, follow))
        saida.texto("FIRST e FOLLOW", tabela_first_follow(g, first, follow, largura=10_000))

    if args.tabela_ll1:
        tabela = TabelaLL1(g_ll1)
        titulo("TABELA PREDITIVA LL(1)  M[A, a]")
        print(tabela.tabela_compacta())
        print()
        for conflito in tabela.conflitos:
            print(f"  {conflito}")
        print(tabela.resumo())
        cab, linhas = tabela.matriz()
        saida.texto("Produções (numeradas)", g_ll1.formatar(agrupar=False))
        saida.tabela("Tabela LL(1): célula = número da produção", cab, linhas)

    if args.gramatica_slr:
        titulo("GRAMÁTICA DA MARÉ EM BNF — FORMATO SLR(1) (aumentada, produção 0 = S' → S)")
        print(g_slr.formatar(agrupar=False))
        print(f"\n{g_slr.resumo()}")
        saida.texto("Gramática SLR(1)", g_slr.formatar(agrupar=False))

    if args.itens_lr0:
        colecao = ColecaoLR0(g_slr)
        titulo("COLEÇÃO CANÔNICA DE ITENS LR(0)  (• marca a posição do ponto)")
        texto = colecao.formatar()
        print(texto if saida.caminho else _truncar(texto, 120))
        print(f"\n{colecao.resumo()}")
        saida.texto("Itens LR(0)", texto)

    if args.tabela_slr:
        tabela = TabelaSLR(g_slr)
        titulo("TABELA SLR(1)  ACTION / GOTO")
        print(tabela.tabela_compacta() if saida.caminho or len(tabela.colecao.estados) <= 40
              else _truncar(tabela.tabela_compacta(), 80))
        print()
        for conflito in tabela.conflitos:
            print(f"  {conflito}")
        print(tabela.resumo())
        cab, linhas = tabela.matriz()
        saida.texto("Produções (numeradas; reduce n usa estes números)", tabela.gramatica.formatar(agrupar=False))
        saida.tabela("Tabela SLR(1): ACTION (s=shift, r=reduce, acc) e GOTO", cab, linhas)


def executar_conversor(caminho: str, saida_gramatica: str | None) -> int:
    """Gerador automático: ambígua -> sem ambiguidade -> sem recursão à esquerda -> fatorada -> LL(1)."""
    try:
        conversao = converter_arquivo(caminho)
    except OSError as e:
        print(f"Não foi possível abrir '{caminho}': {e}", file=sys.stderr)
        return 2
    except ErroConversor as e:
        print(f"Erro na conversão: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Gramática inválida: {e}", file=sys.stderr)
        return 2

    for etapa in conversao.etapas:
        titulo(etapa.titulo)
        for linha in etapa.explicacao:
            print(linha)
        if etapa.explicacao:
            print()
        print(etapa.gramatica.formatar(numerar=False))
        print(f"\n({etapa.gramatica.resumo()})")

    titulo("ETAPA 4 — FIRST/FOLLOW, TABELA LL(1) E PROVA")
    print(relatorio_final(conversao))
    print()
    print(conversao.tabela.tabela_compacta())
    print(conversao.tabela.resumo())
    status(conversao.eh_ll1, "A gramática final é LL(1)." if conversao.eh_ll1
           else "A gramática final NÃO é LL(1).")
    if saida_gramatica:
        with open(saida_gramatica, "w", encoding="utf-8") as f:
            f.write(gramatica_como_arquivo(conversao.final))
        print(f"Gramática LL(1) gerada gravada em {saida_gramatica}")
    return 0 if conversao.eh_ll1 else 1


def _truncar(texto: str, maximo_linhas: int) -> str:
    """Mostra só as primeiras linhas no terminal e avisa como ver o resto."""
    linhas = texto.splitlines()
    if len(linhas) <= maximo_linhas:
        return texto
    resto = len(linhas) - maximo_linhas
    return "\n".join(linhas[:maximo_linhas]) + f"\n... (+{resto} linhas; use --saida arquivo.txt para gravar tudo)"


# ------------------------------------------------------------------ parsers


def rodar_parser_tabela(nome: str, resultado: ResultadoAnalise, fonte: str, mostrar_rastro: bool,
                        saida: Exportador) -> bool:
    """Imprime rastro (se pedido), erros e veredito de um parser de tabela."""
    if mostrar_rastro:
        titulo(f"RASTRO DA ANÁLISE {nome}  (Passo | Pilha | Entrada | Ação)")
        limite = 60
        passos = resultado.passos
        if saida.caminho or len(passos) <= limite:
            print(tabela_rastro(passos))
        else:
            print(tabela_rastro(passos[:limite]))
            print(f"... (+{len(passos) - limite} passos; use --saida arquivo.txt/.csv/.md para gravar o rastro completo)")
        saida.tabela(f"Rastro {nome}", CABECALHO_RASTRO, linhas_rastro(passos, completo=True))
    if resultado.erros:
        for erro in resultado.erros:
            print(mostrar_contexto(fonte, erro), file=sys.stderr)
        status(False, f"Análise sintática {nome}: {len(resultado.erros)} erro(s).")
        return False
    status(True, f"Análise sintática {nome}: aceito ({len(resultado.passos)} passos).")
    return True


def rodar_parser_recursivo(args, tokens, fonte: str):
    """Parser descendente recursivo original. Devolve (ok, árvore)."""
    parser = Parser(tokens, rastrear=args.rastro)
    programa = parser.analisar()
    if args.rastro:
        titulo("RASTREAMENTO DA ANÁLISE SINTÁTICA (▶ regra aplicada, ✓ token consumido, ✗ erro/descarte)")
        print("\n".join(parser.rastro))
    if parser.erros:
        for erro in parser.erros:
            print(mostrar_contexto(fonte, erro), file=sys.stderr)
        status(False, f"Análise sintática (descendente recursivo): {len(parser.erros)} erro(s).")
        return False, None
    status(True, "Análise sintática (descendente recursivo): o programa está de acordo com a gramática.")
    return True, programa


def main() -> int:
    # Garante acentos e caracteres de desenho da árvore no terminal do Windows.
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description="Analisador léxico e sintático da linguagem Maré")
    ap.add_argument("arquivo", nargs="?", help="arquivo-fonte .mare (dispensável nas opções de gramática)")

    lex = ap.add_argument_group("análise léxica e parser recursivo")
    lex.add_argument("--tokens", action="store_true", help="tabela com a cadeia de tokens (lexema, token, classe, posição)")
    lex.add_argument("--cadeia", action="store_true", help="cadeia de tokens compacta, agrupada por linha")
    lex.add_argument("--lexemas", action="store_true", help="tabela de lexemas distintos e seus tokens")
    lex.add_argument("--regex", action="store_true", help="expressões regulares usadas pelo scanner")
    lex.add_argument("--arvore", action="store_true", help="árvore sintática (parser recursivo)")
    lex.add_argument("--rastro", action="store_true", help="rastreamento do parser recursivo (regras aplicadas e tokens consumidos)")
    lex.add_argument("--dot", metavar="ARQ", help="exporta a árvore para Graphviz (.dot)")
    lex.add_argument("--forest", metavar="ARQ", help="exporta a árvore para LaTeX/forest")

    ll1 = ap.add_argument_group("LL(1) com tabela e pilha")
    ll1.add_argument("--gramatica-ll1", action="store_true", help="gramática final em BNF (formato LL(1))")
    ll1.add_argument("--first-follow", action="store_true", help="conjuntos FIRST e FOLLOW (da gramática LL(1); da SLR com --parser slr)")
    ll1.add_argument("--tabela-ll1", action="store_true", help="tabela M[A, a] e conflitos")
    ll1.add_argument("--ll1", action="store_true", help="analisa o arquivo com o LL(1) e mostra o rastro da pilha")

    slr = ap.add_argument_group("SLR(1)")
    slr.add_argument("--gramatica-slr", action="store_true", help="gramática aumentada em BNF (formato SLR(1))")
    slr.add_argument("--itens-lr0", action="store_true", help="coleção canônica de itens LR(0)")
    slr.add_argument("--tabela-slr", action="store_true", help="tabela ACTION/GOTO e conflitos")
    slr.add_argument("--slr", action="store_true", help="analisa o arquivo com o SLR(1) e mostra o rastro shift/reduce")

    ap.add_argument("--converter", metavar="GRAMATICA.txt",
                    help="converte uma gramática ambígua de expressões (com %%left/%%right/%%nonassoc/%%prefix) "
                         "em LL(1), mostrando cada etapa; com --saida grava a gramática gerada")
    ap.add_argument("--parser", choices=["rd", "ll1", "slr"],
                    help="parser usado na análise sintática: rd (recursivo, padrão), ll1 ou slr")
    ap.add_argument("--saida", metavar="ARQ",
                    help="grava as tabelas/rastros pedidos, completos, em ARQ (.txt, .md ou .csv)")
    args = ap.parse_args()

    opcoes_lexicas = [args.tokens, args.cadeia, args.lexemas, args.regex, args.arvore, args.rastro, args.dot, args.forest]
    opcoes_gramatica = [args.gramatica_ll1, args.first_follow, args.tabela_ll1,
                        args.gramatica_slr, args.itens_lr0, args.tabela_slr]
    opcoes_rastro = [args.ll1, args.slr]
    saida = Exportador(args.saida)

    if args.converter:
        return executar_conversor(args.converter, args.saida)

    # --- opções que só dependem da gramática --------------------------------
    if any(opcoes_gramatica):
        try:
            mostrar_gramaticas(args, saida)
        except (OSError, ValueError) as e:
            print(f"Erro ao ler as gramáticas: {e}", file=sys.stderr)
            return 2

    # --- opções que precisam do código-fonte -------------------------------
    so_gramatica = any(opcoes_gramatica) and not any(opcoes_lexicas + opcoes_rastro) and args.parser is None
    if args.arquivo is None:
        if not any(opcoes_gramatica):
            ap.error("informe o arquivo .mare ou uma opção de gramática (--gramatica-ll1, --tabela-slr, ...)")
        saida.gravar()
        return 0
    if so_gramatica:
        saida.gravar()
        return 0

    tudo = not any(opcoes_lexicas + opcoes_rastro + opcoes_gramatica) and args.parser is None

    try:
        with open(args.arquivo, encoding="utf-8") as f:
            fonte = f.read()
    except OSError as e:
        print(f"Não foi possível abrir '{args.arquivo}': {e}", file=sys.stderr)
        return 2

    lexer = Lexer(fonte)
    tokens = lexer.tokenizar()

    if tudo or args.regex:
        titulo("EXPRESSÕES REGULARES DO SCANNER (ordem de prioridade)")
        print(exibicao.tabela_regras())
    if tudo or args.tokens:
        titulo("CADEIA DE TOKENS")
        print(exibicao.tabela_cadeia(tokens))
    if tudo or args.cadeia:
        titulo("CADEIA DE TOKENS (por linha do código)")
        print(exibicao.cadeia_compacta(tokens))
    if tudo or args.lexemas:
        titulo("TABELA DE LEXEMAS E TOKENS")
        print(exibicao.tabela_lexemas(tokens))
        print()
        print(exibicao.resumo_classes(tokens))

    if tudo:
        titulo("RESULTADO")
    if lexer.erros:
        for erro in lexer.erros:
            print(mostrar_contexto(fonte, erro), file=sys.stderr)
        status(False, f"Análise léxica: {len(lexer.erros)} erro(s). Análise sintática não executada.")
        saida.gravar()
        return 1
    status(True, f"Análise léxica concluída: {len(tokens)} tokens reconhecidos.")

    # ---------------------------------------------------- fase 2: sintático
    # Quais parsers rodar: o escolhido em --parser (padrão rd) e os que têm
    # opção própria de rastro. --arvore/--dot/--forest/--rastro são do rd.
    precisa_rd = args.arvore or args.rastro or args.dot or args.forest
    parsers = []
    if args.parser or precisa_rd or not (args.ll1 or args.slr):
        parsers.append(args.parser or "rd")
    if precisa_rd and "rd" not in parsers:
        parsers.append("rd")
    if args.ll1 and "ll1" not in parsers:
        parsers.append("ll1")
    if args.slr and "slr" not in parsers:
        parsers.append("slr")

    ok_geral = True
    programa = None
    for nome in parsers:
        if nome == "rd":
            ok, programa = rodar_parser_recursivo(args, tokens, fonte)
        elif nome == "ll1":
            resultado = AnalisadorLL1(carregar_gramatica(GRAMATICA_LL1)).analisar_tokens(tokens)
            ok = rodar_parser_tabela("LL(1)", resultado, fonte, args.ll1, saida)
        else:
            resultado = AnalisadorSLR(carregar_gramatica(GRAMATICA_SLR)).analisar_tokens(tokens)
            ok = rodar_parser_tabela("SLR(1)", resultado, fonte, args.slr, saida)
        ok_geral = ok_geral and ok

    saida.gravar()
    if not ok_geral:
        return 1

    if (tudo or args.arvore) and programa is not None:
        titulo("ÁRVORE SINTÁTICA")
        print(exibicao.arvore_texto(programa))
    elif args.arvore:
        print("A árvore sintática só é construída pelo parser recursivo (--parser rd).")
    if args.dot and programa is not None:
        with open(args.dot, "w", encoding="utf-8") as f:
            f.write(exibicao.arvore_dot(programa))
        print(f"Árvore exportada para {args.dot}  (gere a imagem com: dot -Tpng {args.dot} -o arvore.png)")
    if args.forest and programa is not None:
        with open(args.forest, "w", encoding="utf-8") as f:
            f.write(exibicao.arvore_forest(programa))
        print(f"Árvore exportada para {args.forest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
