import pathlib
import unittest

from mare.entrada import de_nomes
from mare.gramatica import FIM, Gramatica
from mare.lexer import tokenizar
from mare.ll1 import AnalisadorLL1, TabelaLL1
from mare.rastro import tabela_rastro

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DRAGAO = """
E  -> T E'
E' -> MAIS T E' | ε
T  -> F T'
T' -> MULT F T' | ε
F  -> ABRE E FECHA | id
"""


def gramatica_mare() -> Gramatica:
    return Gramatica.de_arquivo(str(RAIZ / "gramaticas" / "mare_ll1.txt"))


class TestTabela(unittest.TestCase):
    def test_dragao_tabela_conhecida(self):
        t = TabelaLL1(Gramatica.de_texto(DRAGAO))
        self.assertTrue(t.eh_ll1)
        # M[E, id] = E -> T E'    M[E', FECHA] = E' -> ε    M[T', MAIS] = T' -> ε
        self.assertEqual(str(t.producao("E", "id")), "E → T E'")
        self.assertEqual(str(t.producao("E'", "FECHA")), "E' → ε")
        self.assertEqual(str(t.producao("T'", "MAIS")), "T' → ε")
        self.assertIsNone(t.producao("E", "MAIS"))

    def test_conflito_por_prefixo_comum(self):
        t = TabelaLL1(Gramatica.de_texto("S -> a S | a"))
        self.assertFalse(t.eh_ll1)
        self.assertEqual((t.conflitos[0].nao_terminal, t.conflitos[0].terminal), ("S", "a"))

    def test_conflito_por_ambiguidade(self):
        t = TabelaLL1(Gramatica.de_texto("E -> E MAIS E | id"))   # recursiva à esquerda e ambígua
        self.assertFalse(t.eh_ll1)

    def test_conflito_first_follow(self):
        # S -> A a ; A -> a | ε : a ∈ FIRST(a) e a ∈ FOLLOW(A) => conflito em M[A, a]
        t = TabelaLL1(Gramatica.de_texto("S -> A a\nA -> a | ε"))
        self.assertEqual([(c.nao_terminal, c.terminal) for c in t.conflitos], [("A", "a")])

    def test_mare_nao_tem_conflitos(self):
        t = TabelaLL1(gramatica_mare())
        self.assertEqual(t.conflitos, [])
        self.assertIn("ZERO conflitos", t.resumo())


class TestAnaliseGenerica(unittest.TestCase):
    def setUp(self):
        self.a = AnalisadorLL1(Gramatica.de_texto(DRAGAO))

    def aceita(self, texto: str) -> bool:
        return self.a.analisar(de_nomes(texto.split())).aceito

    def test_aceita_e_rejeita(self):
        self.assertTrue(self.aceita("id MAIS id MULT id"))
        self.assertTrue(self.aceita("ABRE id MAIS id FECHA MULT id"))
        self.assertFalse(self.aceita("id MAIS"))
        self.assertFalse(self.aceita("id id"))
        self.assertFalse(self.aceita("ABRE id"))

    def test_rastro_comeca_com_pilha_dolar_inicial(self):
        r = self.a.analisar(de_nomes(["id"]))
        self.assertEqual(r.passos[0].pilha, f"{FIM} E")
        self.assertEqual(r.passos[0].acao, "E → T E'")
        self.assertEqual(r.passos[-1].acao, "aceita")
        self.assertIn("match id", [p.acao for p in r.passos])

    def test_rastro_termina_com_dolar_dolar(self):
        r = self.a.analisar(de_nomes(["id"]))
        self.assertEqual((r.passos[-1].pilha, r.passos[-1].entrada), (FIM, FIM))


class TestAnaliseMare(unittest.TestCase):
    def setUp(self):
        self.a = AnalisadorLL1(gramatica_mare())

    def analisar(self, fonte: str):
        return self.a.analisar_tokens(tokenizar(fonte))

    def test_programa_minimo(self):
        self.assertTrue(self.analisar("principal { }").aceito)

    def test_atribuicao_e_chamada_fatoradas(self):
        r = self.analisar("principal { x = 1; f(x, 2); y = g(3) + 1; }")
        self.assertTrue(r.aceito, r.erros)
        acoes = [p.acao for p in r.passos]
        self.assertIn("cmd_id → ID resto_id", acoes)
        self.assertIn("sufixo_id → ABRE_PAR args_opt FECHA_PAR", acoes)

    def test_erro_aponta_linha_e_coluna(self):
        r = self.analisar("principal {\n  seja x: inteiro = 1\n}")
        self.assertFalse(r.aceito)
        e = r.erros[0]
        self.assertEqual((e.linha, e.coluna), (2, 22))          # ';' esperado no fim da linha 2
        self.assertIn("';'", e.mensagem)

    def test_comparacao_encadeada_rejeitada(self):
        self.assertFalse(self.analisar("principal { x = a < b < c; }").aceito)

    def test_recuperacao_modo_panico_reporta_varios_erros(self):
        fonte = "principal {\n x = ;\n y = 2;\n z = ;\n}"
        r = self.analisar(fonte)
        self.assertEqual([e.linha for e in r.erros], [2, 4])

    def test_entrada_vazia_e_erro(self):
        self.assertFalse(self.analisar("").aceito)

    def test_rastro_formatado_cabe_na_tela(self):
        r = self.analisar("principal { x = 1 + 2; }")
        tabela = tabela_rastro(r.passos)
        self.assertIn("Passo", tabela.splitlines()[1])
        self.assertTrue(all(len(l) <= 130 for l in tabela.splitlines()))


if __name__ == "__main__":
    unittest.main()
