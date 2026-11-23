import pathlib
import unittest

from mare.entrada import de_nomes
from mare.gramatica import Gramatica
from mare.lexer import tokenizar
from mare.slr import AnalisadorSLR, TabelaSLR

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DRAGAO_LR = """
E -> E MAIS T | T
T -> T MULT F | F
F -> ABRE E FECHA | id
"""


def gramatica_mare() -> Gramatica:
    return Gramatica.de_arquivo(str(RAIZ / "gramaticas" / "mare_slr.txt"))


class TestTabela(unittest.TestCase):
    def test_dragao_sem_conflitos(self):
        t = TabelaSLR(Gramatica.de_texto(DRAGAO_LR))
        self.assertTrue(t.eh_slr1)
        self.assertEqual(len(t.colecao.estados), 12)

    def test_acoes_conhecidas_do_dragao(self):
        t = TabelaSLR(Gramatica.de_texto(DRAGAO_LR))
        self.assertEqual(str(t.acao(0, "id")), "s5")
        self.assertEqual(str(t.acao(5, "MAIS")), "r6")        # F -> id
        self.assertEqual(str(t.acao(1, "$")), "acc")
        self.assertEqual(t.goto[(0, "E")], 1)
        self.assertIsNone(t.acao(0, "MAIS"))

    def test_conflito_shift_reduce_na_gramatica_ambigua(self):
        t = TabelaSLR(Gramatica.de_texto("E -> E MAIS E | id"))
        self.assertFalse(t.eh_slr1)
        self.assertEqual({c.tipo for c in t.conflitos}, {"shift/reduce"})

    def test_conflito_reduce_reduce(self):
        # A e B reconhecem a mesma cadeia 'x' no mesmo contexto
        t = TabelaSLR(Gramatica.de_texto("S -> A | B\nA -> x\nB -> x"))
        self.assertIn("reduce/reduce", {c.tipo for c in t.conflitos})

    def test_slr_mas_nao_lr0(self):
        # S -> A b ; A -> a : o estado com 'A -> a •' só reduz com 'b' (FOLLOW), não com tudo
        t = TabelaSLR(Gramatica.de_texto("S -> A b\nA -> a"))
        self.assertTrue(t.eh_slr1)
        self.assertIsNone(t.acao(t.colecao.transicoes[(0, "a")], "a"))

    def test_mare_zero_conflitos(self):
        t = TabelaSLR(gramatica_mare())
        self.assertEqual(t.conflitos, [])
        self.assertIn("ZERO conflitos", t.resumo())

    def test_matriz_tem_uma_linha_por_estado(self):
        t = TabelaSLR(Gramatica.de_texto(DRAGAO_LR))
        cabecalho, linhas = t.matriz()
        self.assertEqual(len(linhas), 12)
        self.assertEqual(cabecalho[0], "Estado")
        self.assertEqual(len(cabecalho), len(linhas[0]))


class TestShiftReduce(unittest.TestCase):
    def setUp(self):
        self.a = AnalisadorSLR(Gramatica.de_texto(DRAGAO_LR))

    def test_rastro_do_dragao(self):
        r = self.a.analisar(de_nomes("id MAIS id MULT id".split()))
        self.assertTrue(r.aceito)
        acoes = [p.acao for p in r.passos]
        self.assertEqual(acoes[0], "shift 5")
        self.assertEqual(acoes[1], "reduce 6: F → id")
        self.assertEqual(acoes[-1], "aceita")
        self.assertEqual(r.passos[-1].pilha, "0 E 1")
        self.assertEqual(len(r.passos), 14)

    def test_rejeita(self):
        for texto in ("id MAIS", "MAIS id", "ABRE id", "id id"):
            with self.subTest(texto=texto):
                r = self.a.analisar(de_nomes(texto.split()))
                self.assertFalse(r.aceito)
                self.assertTrue(r.passos[-1].acao.startswith("erro"))

    def test_mare(self):
        a = AnalisadorSLR(gramatica_mare())
        r = a.analisar_tokens(tokenizar("principal { x = 1; f(x); }"))
        self.assertTrue(r.aceito, r.erros)
        self.assertIn("reduce 3: itens → ε", [p.acao for p in r.passos])

    def test_erro_aponta_linha_e_coluna(self):
        a = AnalisadorSLR(gramatica_mare())
        r = a.analisar_tokens(tokenizar("principal {\n  se (x > 1 {\n  }\n}"))
        self.assertFalse(r.aceito)
        self.assertEqual((r.erros[0].linha, r.erros[0].coluna), (2, 13))


if __name__ == "__main__":
    unittest.main()
