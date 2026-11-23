import unittest

from mare.first_follow import calcular_first, calcular_follow, first_de_cadeia
from mare.gramatica import EPSILON, FIM, Gramatica

# Gramática de expressões do "Livro do Dragão" (Aho et al., ex. 4.x):
#   E  -> T E'      E' -> + T E' | ε
#   T  -> F T'      T' -> * F T' | ε
#   F  -> ( E ) | id
DRAGAO = """
E  -> T E'
E' -> MAIS T E' | ε
T  -> F T'
T' -> MULT F T' | ε
F  -> ABRE E FECHA | id
"""


class TestDragao(unittest.TestCase):
    def setUp(self):
        self.g = Gramatica.de_texto(DRAGAO)
        self.first = calcular_first(self.g)
        self.follow = calcular_follow(self.g, self.first)

    def test_first(self):
        esperado = {
            "E": {"ABRE", "id"}, "T": {"ABRE", "id"}, "F": {"ABRE", "id"},
            "E'": {"MAIS", EPSILON}, "T'": {"MULT", EPSILON},
        }
        for simbolo, conjunto in esperado.items():
            with self.subTest(simbolo=simbolo):
                self.assertEqual(self.first[simbolo], conjunto)

    def test_first_de_terminal_e_de_cadeia(self):
        self.assertEqual(self.first["MAIS"], {"MAIS"})
        self.assertEqual(first_de_cadeia(("E'", "T'"), self.first), {"MAIS", "MULT", EPSILON})
        self.assertEqual(first_de_cadeia(("E'", "F"), self.first), {"MAIS", "ABRE", "id"})
        self.assertEqual(first_de_cadeia((), self.first), {EPSILON})

    def test_follow(self):
        esperado = {
            "E": {FIM, "FECHA"}, "E'": {FIM, "FECHA"},
            "T": {"MAIS", FIM, "FECHA"}, "T'": {"MAIS", FIM, "FECHA"},
            "F": {"MULT", "MAIS", FIM, "FECHA"},
        }
        for simbolo, conjunto in esperado.items():
            with self.subTest(simbolo=simbolo):
                self.assertEqual(self.follow[simbolo], conjunto)


class TestCasosEspeciais(unittest.TestCase):
    def test_cadeia_de_anulaveis(self):
        # S -> A B c ; A -> a | ε ; B -> b | ε  (A e B somem, então c entra no FIRST de S)
        g = Gramatica.de_texto("S -> A B c\nA -> a | ε\nB -> b | ε")
        first = calcular_first(g)
        follow = calcular_follow(g, first)
        self.assertEqual(first["S"], {"a", "b", "c"})
        self.assertEqual(follow["A"], {"b", "c"})
        self.assertEqual(follow["B"], {"c"})

    def test_follow_do_inicial_tem_dolar(self):
        g = Gramatica.de_texto("S -> a")
        self.assertEqual(calcular_follow(g, calcular_first(g))["S"], {FIM})

    def test_ponto_fixo_com_dependencia_circular(self):
        # A depende de B e B de A: só um ponto fixo iterativo resolve.
        g = Gramatica.de_texto("S -> A\nA -> B x | y\nB -> A z | w")
        first = calcular_first(g)
        self.assertEqual(first["A"], {"y", "w"})
        self.assertEqual(first["B"], {"y", "w"})


if __name__ == "__main__":
    unittest.main()
