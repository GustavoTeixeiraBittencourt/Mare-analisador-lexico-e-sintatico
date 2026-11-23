import pathlib
import unittest

from mare.gramatica import EPSILON, ErroGramatica, Gramatica
from mare.tabelas import tabela_csv, tabela_markdown, tabela_texto

RAIZ = pathlib.Path(__file__).resolve().parent.parent

TEXTO = """
# gramática de exemplo
E  -> T E'
E' -> MAIS T E' | ε
T  -> ID
   | ABRE E FECHA      # continuação com '|'
"""


class TestLeitura(unittest.TestCase):
    def test_producoes_e_simbolos(self):
        g = Gramatica.de_texto(TEXTO)
        self.assertEqual(g.inicial, "E")
        self.assertEqual(g.nao_terminais, ["E", "E'", "T"])
        self.assertEqual(g.terminais, ["MAIS", "ID", "ABRE", "FECHA"])
        self.assertEqual(len(g.producoes), 5)

    def test_epsilon_vira_cadeia_vazia(self):
        g = Gramatica.de_texto(TEXTO)
        vazias = [p for p in g.producoes if p.direita == ()]
        self.assertEqual([p.esquerda for p in vazias], ["E'"])
        self.assertTrue(EPSILON in str(vazias[0]))

    def test_erros_de_formato(self):
        for texto in ("A B C", "| A", "A -> B | ", "A -> ε B"):
            with self.subTest(texto=texto), self.assertRaises(ErroGramatica):
                Gramatica.de_texto(texto)

    def test_aumentada_acrescenta_producao_zero(self):
        g = Gramatica.de_texto(TEXTO).aumentada()
        self.assertEqual(g.inicial, "E''")
        self.assertEqual(str(g.producoes[0]), "E'' → E")
        self.assertEqual(g.producoes[0].numero, 0)

    def test_gramaticas_da_mare_carregam(self):
        ll1 = Gramatica.de_arquivo(str(RAIZ / "gramaticas" / "mare_ll1.txt"))
        slr = Gramatica.de_arquivo(str(RAIZ / "gramaticas" / "mare_slr.txt"))
        self.assertEqual(ll1.inicial, "programa")
        self.assertEqual(slr.inicial, "programa'")
        self.assertEqual(set(ll1.terminais), set(slr.terminais))   # mesma linguagem, mesmos tokens

    def test_formatar_numera_producoes(self):
        saida = Gramatica.de_texto(TEXTO).formatar()
        self.assertIn("  0. E  → T E'", saida)
        self.assertIn("  2.", saida)


class TestTabelas(unittest.TestCase):
    def test_texto_quebra_celulas_largas(self):
        tabela = tabela_texto(["a", "b"], [["x", "palavra " * 20]], largura_max=40)
        self.assertTrue(all(len(linha) <= 40 for linha in tabela.splitlines()))
        self.assertGreater(len(tabela.splitlines()), 5)

    def test_markdown_e_csv(self):
        self.assertIn("a\|b", tabela_markdown(["h"], [["a|b"]]))
        self.assertEqual(tabela_csv(["x", "y"], [["1", "2"]]), "x;y\n1;2")


if __name__ == "__main__":
    unittest.main()
