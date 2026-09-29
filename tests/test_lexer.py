import unittest

from mare.erros import ErroLexico
from mare.lexer import Lexer, tokenizar
from mare.tokens import TipoToken as T


def tipos(fonte):
    return [t.tipo for t in tokenizar(fonte)][:-1]  # sem EOF


class TestLexer(unittest.TestCase):
    def test_palavras_reservadas_x_identificadores(self):
        self.assertEqual(tipos("se senao seja sejam principal2"), [T.SE, T.SENAO, T.SEJA, T.ID, T.ID])

    def test_operadores_logicos_sao_palavras(self):
        self.assertEqual(tipos("a e b ou nao c"), [T.ID, T.E, T.ID, T.OU, T.NAO, T.ID])

    def test_numeros(self):
        toks = tokenizar("10 3.14 0")
        self.assertEqual([(t.tipo, t.lexema) for t in toks[:-1]],
                         [(T.NUM_INT, "10"), (T.NUM_REAL, "3.14"), (T.NUM_INT, "0")])

    def test_simbolos_de_dois_caracteres_tem_prioridade(self):
        self.assertEqual(tipos("<= >= == != -> < > = -"),
                         [T.MENOR_IGUAL, T.MAIOR_IGUAL, T.IGUAL, T.DIFERENTE, T.SETA,
                          T.MENOR, T.MAIOR, T.ATRIB, T.MENOS])

    def test_texto_com_escape(self):
        toks = tokenizar(r'"ola \"mundo\""')
        self.assertEqual(toks[0].tipo, T.TEXTO)
        self.assertEqual(toks[0].lexema, r'"ola \"mundo\""')

    def test_comentarios_sao_ignorados_e_linhas_contadas(self):
        fonte = "# linha\n#* bloco\n com duas *# x\ny"
        toks = tokenizar(fonte)
        self.assertEqual([(t.lexema, t.linha, t.coluna) for t in toks[:-1]], [("x", 3, 14), ("y", 4, 1)])

    def test_posicao(self):
        toks = tokenizar("principal {\n  seja x: inteiro;\n}")
        x = toks[3]
        self.assertEqual((x.lexema, x.linha, x.coluna), ("x", 2, 8))

    def test_eof(self):
        self.assertEqual(tokenizar("")[-1].tipo, T.EOF)

    def test_erros_lexicos_acumulados(self):
        lexer = Lexer('a @ 12abc "sem fim\n3. ç')
        lexer.tokenizar()
        mensagens = [e.mensagem for e in lexer.erros]
        self.assertEqual(len(mensagens), 5)
        self.assertIn("caractere inválido '@'", mensagens[0])
        self.assertIn("12abc", mensagens[1])
        self.assertIn("aspas", mensagens[2])
        self.assertIn("'3.'", mensagens[3])
        self.assertIn("acentos", mensagens[4])

    def test_comentario_nao_fechado(self):
        with self.assertRaises(ErroLexico):
            tokenizar("x #* nunca fecha")


if __name__ == "__main__":
    unittest.main()
