import pathlib
import unittest

from mare.conversor import (ErroConversor, _extrair, _tem_recursao_esquerda, converter, converter_arquivo, eliminar_recursao_esquerda,
                            fatorar_esquerda, gramatica_como_arquivo)
from mare.entrada import de_nomes
from mare.gramatica import Gramatica
from mare.ll1 import AnalisadorLL1, TabelaLL1

RAIZ = pathlib.Path(__file__).resolve().parent.parent

MINIMA = """
%left +
%left *
E -> E + E | E * E | id
"""


def producoes(g: Gramatica) -> set[str]:
    """Conjunto de produções em texto, para comparar sem depender da ordem."""
    return {str(p) for p in g.producoes}


class TestEtapas(unittest.TestCase):
    def test_gramatica_original_e_ambigua_e_nao_ll1(self):
        c = converter(MINIMA)
        self.assertFalse(TabelaLL1(c.etapas[0].gramatica).eh_ll1)

    def test_etapa1_um_nivel_por_precedencia(self):
        g = converter(MINIMA).etapas[1].gramatica
        self.assertEqual(producoes(g), {
            "E → E + E1", "E → E1", "E1 → E1 * E2", "E1 → E2", "E2 → id"})

    def test_etapa2_recursao_a_esquerda_direta(self):
        g = converter(MINIMA).etapas[2].gramatica
        self.assertEqual(producoes(g), {
            "E → E1 E'", "E' → + E1 E'", "E' → ε",
            "E1 → E2 E1'", "E1' → * E2 E1'", "E1' → ε", "E2 → id"})

    def test_associatividade_a_direita_vira_fatoracao(self):
        c = converter("%right ^\nE -> E ^ E | id")
        self.assertEqual(producoes(c.etapas[1].gramatica), {"E → E1 ^ E", "E → E1", "E1 → id"})
        self.assertEqual(producoes(c.final), {"E → E1 E'", "E' → ^ E", "E' → ε", "E1 → id"})

    def test_nao_associativo_nao_tem_recursao(self):
        c = converter("%nonassoc <\nE -> E < E | id")
        self.assertEqual(producoes(c.etapas[1].gramatica), {"E → E1 < E1", "E → E1", "E1 → id"})
        self.assertFalse(converter("%nonassoc <\nE -> E < E | id").tabela is None)

    def test_prefixo_unario(self):
        c = converter("%left +\n%prefix -\nE -> E + E | - E | id")
        self.assertEqual(producoes(c.etapas[1].gramatica),
                         {"E → E + E1", "E → E1", "E1 → - E1", "E1 → E2", "E2 → id"})

    def test_recursao_indireta(self):
        g = Gramatica.de_texto("A -> B x | y\nB -> A z | w")
        etapa = eliminar_recursao_esquerda(g)
        self.assertEqual(producoes(etapa.gramatica), {
            "A → B x", "A → y", "B → y z B'", "B → w B'", "B' → x z B'", "B' → ε"})
        # (a gramática resultante ainda não é LL(1) — A → B x e A → y começam igual —, mas não há mais recursão)
        self.assertIsNone(_tem_recursao_esquerda(_extrair(etapa.gramatica)[0]))

    def test_fatoracao_repetida_ate_acabar(self):
        # a b c | a b d | a e  =>  fatora 'a'; depois 'b' dentro do novo não-terminal
        g = Gramatica.de_texto("S -> a b c | a b d | a e")
        etapa = fatorar_esquerda(g)
        self.assertEqual(producoes(etapa.gramatica), {
            "S → a S'", "S' → b S''", "S' → e", "S'' → c", "S'' → d"})

    def test_fatoracao_com_prefixo_que_e_uma_alternativa_inteira(self):
        etapa = fatorar_esquerda(Gramatica.de_texto("S -> a | a b"))
        self.assertEqual(producoes(etapa.gramatica), {"S → a S'", "S' → ε", "S' → b"})


class TestResultado(unittest.TestCase):
    def setUp(self):
        self.c = converter_arquivo(str(RAIZ / "gramaticas" / "ambigua_expr.txt"))

    def test_gramatica_de_exemplo_vira_ll1_sem_conflitos(self):
        self.assertTrue(self.c.eh_ll1)
        self.assertEqual(self.c.tabela.conflitos, [])
        self.assertFalse(TabelaLL1(self.c.etapas[0].gramatica).eh_ll1)          # a original tinha conflitos

    def test_nao_sobra_recursao_nem_prefixo_comum(self):
        for p in self.c.final.producoes:
            self.assertNotEqual(p.direita[:1], (p.esquerda,), f"recursão à esquerda em {p}")
        for nt in self.c.final.nao_terminais:
            iniciais = [p.direita[0] for p in self.c.final.por_nao_terminal[nt] if p.direita]
            self.assertEqual(len(iniciais), len(set(iniciais)), f"prefixo comum em {nt}")

    def test_gramatica_gerada_reconhece_expressoes(self):
        a = AnalisadorLL1(self.c.final)
        aceitas = ["id + num * id", "nao id ou id e id", "( id + id ) * num", "id ( id , num + id )",
                   "- id ^ id ^ num", "id < num", "id * - id", "id ( num )"]
        rejeitadas = ["id +", "id < id < id", "( id", "id id", "* id", "id ( )", "id ( id ,"]
        for texto in aceitas:
            with self.subTest(aceita=texto):
                self.assertTrue(a.analisar(de_nomes(texto.split())).aceito)
        for texto in rejeitadas:
            with self.subTest(rejeita=texto):
                self.assertFalse(a.analisar(de_nomes(texto.split())).aceito)

    def test_precedencia_na_derivacao(self):
        """`id + id * id`: o `*` é expandido DENTRO do operando direito do `+`."""
        a = AnalisadorLL1(self.c.final)
        acoes = [p.acao for p in a.analisar(de_nomes("id + id * id".split())).passos]
        self.assertLess(acoes.index("E4' → + E5 E4'"), acoes.index("E5' → * E6 E5'"))
        # depois do '+', o operando E5 já inclui a multiplicação (E5' → * ...), e E4' fecha com ε
        self.assertEqual(acoes.count("E5' → * E6 E5'"), 1)

    def test_saida_pode_ser_relida(self):
        g = Gramatica.de_texto(gramatica_como_arquivo(self.c.final))
        self.assertEqual(producoes(g), producoes(self.c.final))


class TestErros(unittest.TestCase):
    def test_operador_sem_precedencia(self):
        with self.assertRaises(ErroConversor):
            converter("%left +\nE -> E + E | E * E | id")

    def test_diretiva_sem_operadores(self):
        with self.assertRaises(ErroConversor):
            converter("%left\nE -> id")

    def test_sem_alternativa_base(self):
        with self.assertRaises(ErroConversor):
            converter("%left +\nE -> E + E")

    def test_ambiguidade_alem_de_operadores_continua_nao_ll1(self):
        # "senão pendurado": o conversor não consegue resolver, e diz isso
        c = converter("S -> i S | i S e S | a")
        self.assertFalse(c.eh_ll1)
        self.assertTrue(c.tabela.conflitos)


if __name__ == "__main__":
    unittest.main()
