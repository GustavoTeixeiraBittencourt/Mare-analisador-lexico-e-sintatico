import argparse
import sys

from mare import exibicao
from mare.erros import mostrar_contexto
from mare.lexer import Lexer
from mare.parser import Parser

USA_COR = sys.stdout.isatty()


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


def main() -> int:
    # Garante acentos e caracteres de desenho da árvore no terminal do Windows.
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description="Analisador léxico e sintático da linguagem Maré")
    ap.add_argument("arquivo", help="arquivo-fonte .mare")
    ap.add_argument("--tokens", action="store_true", help="tabela com a cadeia de tokens (lexema, token, classe, posição)")
    ap.add_argument("--cadeia", action="store_true", help="cadeia de tokens compacta, agrupada por linha")
    ap.add_argument("--lexemas", action="store_true", help="tabela de lexemas distintos e seus tokens")
    ap.add_argument("--regex", action="store_true", help="expressões regulares usadas pelo scanner")
    ap.add_argument("--arvore", action="store_true", help="árvore sintática")
    ap.add_argument("--rastro", action="store_true", help="rastreamento passo a passo do parser (regras aplicadas e tokens consumidos)")
    ap.add_argument("--dot", metavar="ARQ", help="exporta a árvore para Graphviz (.dot)")
    ap.add_argument("--forest", metavar="ARQ", help="exporta a árvore para LaTeX/forest")
    args = ap.parse_args()

    tudo = not any([args.tokens, args.cadeia, args.lexemas, args.regex, args.arvore, args.rastro, args.dot, args.forest])

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
        return 1
    status(True, f"Análise léxica concluída: {len(tokens)} tokens reconhecidos.")

    # ---------------------------------------------------- fase 2: sintático
    parser = Parser(tokens, rastrear=args.rastro)
    programa = parser.analisar()

    if args.rastro:
        titulo("RASTREAMENTO DA ANÁLISE SINTÁTICA (▶ regra aplicada, ✓ token consumido, ✗ erro/descarte)")
        print("\n".join(parser.rastro))

    if parser.erros:
        for erro in parser.erros:
            print(mostrar_contexto(fonte, erro), file=sys.stderr)
        status(False, f"Análise sintática: {len(parser.erros)} erro(s).")
        return 1
    status(True, "Análise sintática concluída: o programa está de acordo com a gramática.")

    if tudo or args.arvore:
        titulo("ÁRVORE SINTÁTICA")
        print(exibicao.arvore_texto(programa))
    if args.dot:
        with open(args.dot, "w", encoding="utf-8") as f:
            f.write(exibicao.arvore_dot(programa))
        print(f"Árvore exportada para {args.dot}  (gere a imagem com: dot -Tpng {args.dot} -o arvore.png)")
    if args.forest:
        with open(args.forest, "w", encoding="utf-8") as f:
            f.write(exibicao.arvore_forest(programa))
        print(f"Árvore exportada para {args.forest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
