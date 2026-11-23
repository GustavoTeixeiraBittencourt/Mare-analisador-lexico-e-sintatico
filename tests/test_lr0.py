import pathlib
import unittest

from mare.gramatica import Gramatica
from mare.lr0 import ColecaoLR0, Item, closure, goto

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Gramática E/T/F recursiva à esquerda (Dragão, fig. 4.x): a coleção canônica
# tem exatamente 12 estados, I0..I11.
DRAGAO_LR = """
E -> E MAIS T | T
T -> T MULT F | F
F -> ABRE E FECHA | id
"""


class TestLR0(unittest.TestCase):
    def setUp(self):
        self.colecao = ColecaoLR0(Gramatica.de_texto(DRAGAO_LR))
        self.g = self.colecao.gramatica

    def textos(self, estado):
        return {self.colecao.formatar_item(i) for i in self.colecao.estados[estado]}

    def test_gramatica_e_aumentada(self):
        self.assertEqual(str(self.g.producoes[0]), "E' → E")

    def test_closure_de_i0(self):
        self.assertEqual(self.textos(0), {
            "E' → • E", "E → • E MAIS T", "E → • T", "T → • T MULT F",
            "T → • F", "F → • ABRE E FECHA", "F → • id",
        })

    def test_doze_estados(self):
        self.assertEqual(len(self.colecao.estados), 12)

    def test_goto_sobre_E_a_partir_de_i0(self):
        destino = self.colecao.transicoes[(0, "E")]
        self.assertEqual(self.textos(destino), {"E' → E •", "E → E • MAIS T"})

    def test_goto_vazio_quando_nao_ha_transicao(self):
        self.assertEqual(goto(self.g, self.colecao.estados[0], "FECHA"), frozenset())

    def test_closure_nao_duplica_e_e_idempotente(self):
        i0 = closure(self.g, {Item(0, 0)})
        self.assertEqual(closure(self.g, i0), i0)

    def test_estado_com_ponto_no_fim_e_completo(self):
        destino = self.colecao.transicoes[(0, "id")]
        self.assertEqual(self.textos(destino), {"F → id •"})

    def test_formatacao_mostra_ponto_e_transicoes(self):
        saida = self.colecao.formatar()
        self.assertIn("I0:", saida)
        self.assertIn("E → E • MAIS T", saida)
        self.assertIn("goto(I0, E) = I1", saida)

    def test_producao_epsilon_tem_item_completo(self):
        c = ColecaoLR0(Gramatica.de_texto("S -> A a\nA -> ε"))
        self.assertIn("A → •", {c.formatar_item(i) for i in c.estados[0]})

    def test_mare(self):
        c = ColecaoLR0(Gramatica.de_arquivo(str(RAIZ / "gramaticas" / "mare_slr.txt")))
        self.assertEqual(c.gramatica.inicial, "programa'")     # já vinha aumentada
        self.assertGreater(len(c.estados), 100)


if __name__ == "__main__":
    unittest.main()
