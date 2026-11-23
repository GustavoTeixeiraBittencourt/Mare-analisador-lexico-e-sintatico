"""
Os três parsers (descendente recursivo, LL(1) e SLR(1)) precisam aceitar
exatamente os mesmos programas. Aqui cada fonte é analisada pelos três e os
veredictos (aceito / erro sintático) são comparados.
"""

import pathlib
import unittest

from mare.gramatica import Gramatica
from mare.lexer import Lexer
from mare.ll1 import AnalisadorLL1
from mare.parser import Parser
from mare.slr import AnalisadorSLR

RAIZ = pathlib.Path(__file__).resolve().parent.parent
EXEMPLOS = RAIZ / "exemplos"

LL1 = AnalisadorLL1(Gramatica.de_arquivo(str(RAIZ / "gramaticas" / "mare_ll1.txt")))
SLR = AnalisadorSLR(Gramatica.de_arquivo(str(RAIZ / "gramaticas" / "mare_slr.txt")))


def veredictos(fonte: str) -> dict[str, bool]:
    """Aceito (True) ou erro sintático (False) em cada parser."""
    lexer = Lexer(fonte)
    tokens = lexer.tokenizar()
    assert not lexer.erros, lexer.erros
    rd = Parser(tokens)
    rd.analisar()
    return {
        "rd": not rd.erros,
        "ll1": LL1.analisar_tokens(tokens).aceito,
        "slr": SLR.analisar_tokens(tokens).aceito,
    }


# (trecho de programa, deve ser aceito?) — cobre cada construção da linguagem.
CASOS = [
    ("principal { }", True),
    ("fixo PI: real = 3.14; seja n: inteiro; principal { }", True),
    ("funcao f() { } principal { }", True),
    ("funcao f(a: inteiro, b: real) -> real { retorne a + b; } principal { }", True),
    ("funcao f() { retorne; } principal { f(); }", True),
    ("principal { seja x: inteiro = 1; fixo y: real = 2.0; seja z: texto; }", True),
    ("principal { x = 1; f(); g(1, h(2)); }", True),
    ("principal { se (a) { } }", True),
    ("principal { se (a) { } senao { } }", True),
    ("principal { se (a) { } senao se (b) { } senao se (c) { } senao { } }", True),
    ("principal { enquanto (a < 3) { a = a + 1; } }", True),
    ("principal { para i de 1 ate 10 { } para j de 1 ate n passo 2 { } }", True),
    ("principal { repita { x = x - 1; } ate (x == 0); }", True),
    ("principal { retorne; retorne 1 + 2; }", True),
    ("principal { mostre(1); mostre(a, \"b\", f(c)); leia(x); }", True),
    ("principal { x = a ou b e nao c; }", True),
    ("principal { x = a < b; y = a >= b e c != d; }", True),
    ("principal { x = 1 + 2 * 3 - 4 / 5 % 6; }", True),
    ("principal { x = -a; y = - -a; z = a * -b; }", True),
    ("principal { x = 2 ^ 3 ^ 2; y = 2 ^ -1; z = -2 ^ 2; }", True),
    ("principal { x = (a + b) * (c - d); w = ((1)); }", True),
    ("principal { x = verdadeiro e falso; t = \"texto\"; r = 1.5; }", True),
    ("principal { x = f(g(1, 2), h()) + 3; }", True),
    # --- rejeitados ---
    ("", False),
    ("funcao f() { }", False),                                  # sem principal
    ("principal", False),
    ("principal { ", False),
    ("principal { } principal { }", False),                     # dois principal
    ("principal { } funcao f() { }", False),                    # função depois do principal
    ("principal { } seja x: inteiro;", False),                  # global depois do principal
    ("principal { seja x: inteiro = 1 }", False),               # falta ;
    ("principal { x = ; }", False),
    ("principal { x = 1 + ; }", False),
    ("principal { x = a < b < c; }", False),                    # relacional não associativo
    ("principal { se a { } }", False),                          # sem parênteses
    ("principal { se (a) { } senao }", False),
    ("principal { senao { } }", False),                         # senao sem se
    ("principal { fixo x: inteiro; }", False),                  # constante sem valor
    ("principal { seja x inteiro; }", False),                   # falta :
    ("principal { mostre(); }", False),                         # mostre sem argumento
    ("principal { leia(1); }", False),                          # leia só aceita ID
    ("principal { para i de 1 { } }", False),                   # falta ate
    ("principal { repita { } ate (x) }", False),                # falta ;
    ("principal { f(1,); }", False),
    ("principal { x = (1 + 2; }", False),
    ("principal { x = 1 2; }", False),
    ("principal { 1 = x; }", False),
    ("principal { x = nao; }", False),
    ("principal { x = 1 + nao a; }", False),                    # 'nao' só no nível lógico
    ("funcao f(a) { } principal { }", False),                   # parâmetro sem tipo
    ("funcao f() -> { } principal { }", False),
    ("principal { funcao f() { } }", False),                    # função dentro de bloco
    ("principal { } }", False),
]


class TestConcordancia(unittest.TestCase):
    def test_casos_curtos(self):
        for fonte, esperado in CASOS:
            with self.subTest(fonte=fonte):
                v = veredictos(fonte)
                self.assertEqual(v, {"rd": esperado, "ll1": esperado, "slr": esperado})

    def test_arquivos_de_exemplos(self):
        """Todo .mare de exemplos/ sem erro léxico: os três parsers concordam."""
        analisados = 0
        for caminho in sorted(EXEMPLOS.glob("*.mare")):
            fonte = caminho.read_text(encoding="utf-8")
            lexer = Lexer(fonte)
            lexer.tokenizar()
            if lexer.erros:                      # erro léxico: nem chega ao sintático
                continue
            with self.subTest(arquivo=caminho.name):
                v = veredictos(fonte)
                self.assertEqual(len(set(v.values())), 1, f"parsers discordam em {caminho.name}: {v}")
                analisados += 1
        self.assertGreaterEqual(analisados, 6)

    def test_exemplos_validos_sao_aceitos_e_invalidos_rejeitados(self):
        validos = ["completo", "fatorial", "mini", "expressao", "chamada"]
        invalidos = ["rejeitado", "erro_sintatico", "expressao_erro"]
        for nome in validos:
            with self.subTest(arquivo=nome):
                self.assertTrue(all(veredictos((EXEMPLOS / f"{nome}.mare").read_text(encoding="utf-8")).values()))
        for nome in invalidos:
            with self.subTest(arquivo=nome):
                self.assertFalse(any(veredictos((EXEMPLOS / f"{nome}.mare").read_text(encoding="utf-8")).values()))

    def test_erro_sintatico_na_mesma_posicao_que_o_recursivo(self):
        """Nos casos com um único erro, rd, ll1 e slr apontam a mesma linha:coluna."""
        for nome in ("rejeitado", "expressao_erro"):
            with self.subTest(arquivo=nome):
                tokens = Lexer((EXEMPLOS / f"{nome}.mare").read_text(encoding="utf-8")).tokenizar()
                rd = Parser(tokens)
                rd.analisar()
                posicoes = {(rd.erros[0].linha, rd.erros[0].coluna),
                            (LL1.analisar_tokens(tokens).erros[0].linha, LL1.analisar_tokens(tokens).erros[0].coluna),
                            (SLR.analisar_tokens(tokens).erros[0].linha, SLR.analisar_tokens(tokens).erros[0].coluna)}
                self.assertEqual(len(posicoes), 1, posicoes)


if __name__ == "__main__":
    unittest.main()
