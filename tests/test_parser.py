import pathlib
import unittest

from mare import arvore as A
from mare.lexer import tokenizar
from mare.parser import Parser

EXEMPLOS = pathlib.Path(__file__).resolve().parent.parent / "exemplos"


def analisar(fonte):
    parser = Parser(tokenizar(fonte))
    programa = parser.analisar()
    return programa, parser.erros


def expr(texto):
    """Analisa uma expressão isolada e devolve seu nó."""
    programa, erros = analisar(f"principal {{ x = {texto}; }}")
    assert not erros, erros
    return programa.principal.comandos[0].valor


def pre(no):
    """Forma prefixada totalmente parentizada, para conferir precedência."""
    if isinstance(no, A.Binaria):
        return f"({no.operador} {pre(no.esquerda)} {pre(no.direita)})"
    if isinstance(no, A.Unaria):
        return f"({no.operador} {pre(no.operando)})"
    if isinstance(no, A.Literal):
        return no.valor
    if isinstance(no, A.Variavel):
        return no.nome
    if isinstance(no, A.Chamada):
        return f"{no.nome}({', '.join(pre(a) for a in no.argumentos)})"
    raise TypeError(no)


class TestExpressoes(unittest.TestCase):
    def test_precedencia_aritmetica(self):
        self.assertEqual(pre(expr("1 + 2 * 3")), "(+ 1 (* 2 3))")
        self.assertEqual(pre(expr("(1 + 2) * 3")), "(* (+ 1 2) 3)")

    def test_associatividade(self):
        self.assertEqual(pre(expr("10 - 3 - 2")), "(- (- 10 3) 2)")
        self.assertEqual(pre(expr("2 ^ 3 ^ 2")), "(^ 2 (^ 3 2))")

    def test_unario(self):
        self.assertEqual(pre(expr("-2 ^ 2")), "(- (^ 2 2))")
        self.assertEqual(pre(expr("a * -b")), "(* a (- b))")

    def test_logica(self):
        self.assertEqual(pre(expr("a ou b e nao c")), "(ou a (e b (nao c)))")
        self.assertEqual(pre(expr("x > 1 e y <= 2 ou z == 3")),
                         "(ou (e (> x 1) (<= y 2)) (== z 3))")

    def test_chamada_em_expressao(self):
        self.assertEqual(pre(expr("f(1, g(x)) + 2")), "(+ f(1, g(x)) 2)")


class TestComandos(unittest.TestCase):
    def test_programa_minimo(self):
        programa, erros = analisar("principal { }")
        self.assertEqual(erros, [])
        self.assertEqual(programa.principal.comandos, [])

    def test_senao_se(self):
        programa, erros = analisar("principal { se (a) { } senao se (b) { } senao { } }")
        self.assertEqual(erros, [])
        se = programa.principal.comandos[0]
        self.assertIsInstance(se.senao, A.Se)
        self.assertIsInstance(se.senao.senao, A.Bloco)

    def test_lacos(self):
        fonte = """principal {
            enquanto (i < 3) { i = i + 1; }
            para k de 1 ate 10 passo 2 { mostre(k); }
            repita { i = i - 1; } ate (i == 0);
        }"""
        programa, erros = analisar(fonte)
        self.assertEqual(erros, [])
        self.assertEqual([type(c) for c in programa.principal.comandos], [A.Enquanto, A.Para, A.Repita])

    def test_funcao_e_global(self):
        fonte = "fixo PI: real = 3.14; funcao area(r: real) -> real { retorne PI * r ^ 2; } principal { }"
        programa, erros = analisar(fonte)
        self.assertEqual(erros, [])
        constante, funcao = programa.declaracoes
        self.assertTrue(constante.constante)
        self.assertEqual((funcao.nome, funcao.tipo_retorno), ("area", "real"))
        self.assertEqual([p.nome for p in funcao.parametros], ["r"])

    def test_exemplos_validos(self):
        for nome in ("completo.mare", "fatorial.mare", "mini.mare"):
            with self.subTest(arquivo=nome):
                _, erros = analisar((EXEMPLOS / nome).read_text(encoding="utf-8"))
                self.assertEqual(erros, [])


class TestErrosSintaticos(unittest.TestCase):
    def assertErro(self, fonte, trecho):
        _, erros = analisar(fonte)
        self.assertTrue(erros, "era esperado um erro")
        self.assertIn(trecho, erros[0].mensagem)

    def test_ponto_e_virgula(self):
        self.assertErro("principal { seja x: inteiro = 1 }", "';'")

    def test_parenteses_no_se(self):
        self.assertErro("principal { se x > 1 { } }", "'('")

    def test_sem_principal(self):
        self.assertErro("funcao f() { }", "principal")

    def test_comparacao_encadeada(self):
        self.assertErro("principal { x = a < b < c; }", "encadeadas")

    def test_constante_sem_valor(self):
        self.assertErro("principal { fixo x: inteiro; }", "valor")

    def test_recuperacao_reporta_varios_erros(self):
        _, erros = analisar((EXEMPLOS / "erro_sintatico.mare").read_text(encoding="utf-8"))
        self.assertEqual([e.linha for e in erros], [2, 7, 8, 9, 12, 15])


class TestRastreamento(unittest.TestCase):
    def test_rastro_do_caso_rejeitado(self):
        fonte = (EXEMPLOS / "rejeitado.mare").read_text(encoding="utf-8")
        parser = Parser(tokenizar(fonte), rastrear=True)
        parser.analisar()
        rastro = "\n".join(parser.rastro)
        self.assertEqual(len(parser.erros), 1)
        self.assertIn("▶ se", rastro)
        self.assertIn("ERRO [4:28]", rastro)
        self.assertIn("descarta <ABRE_CHAVE", rastro)

    def test_sem_rastro_por_padrao(self):
        parser = Parser(tokenizar("principal { }"))
        parser.analisar()
        self.assertEqual(parser.rastro, [])


if __name__ == "__main__":
    unittest.main()
