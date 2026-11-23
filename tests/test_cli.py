import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def rodar(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(RAIZ / "main.py"), *args], capture_output=True,
                          text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})


class TestCLI(unittest.TestCase):
    def test_opcoes_de_gramatica_dispensam_arquivo(self):
        for opcao, trecho in [("--gramatica-ll1", "→ item itens"), ("--first-follow", "FIRST"),
                              ("--tabela-ll1", "ZERO conflitos"), ("--gramatica-slr", "programa' → programa"),
                              ("--itens-lr0", "I0:"), ("--tabela-slr", "ZERO conflitos")]:
            with self.subTest(opcao=opcao):
                r = rodar(opcao)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(trecho, r.stdout)

    def test_rastros_ll1_e_slr(self):
        r = rodar("exemplos/expressao.mare", "--ll1", "--slr")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| Passo | Pilha", r.stdout)
        self.assertIn("match ID", r.stdout)
        self.assertIn("reduce", r.stdout)
        self.assertIn("LL(1): aceito", r.stdout)
        self.assertIn("SLR(1): aceito", r.stdout)

    def test_parser_escolhido_e_codigo_de_saida(self):
        for parser in ("rd", "ll1", "slr"):
            with self.subTest(parser=parser):
                self.assertEqual(rodar("exemplos/mini.mare", "--parser", parser).returncode, 0)
                r = rodar("exemplos/rejeitado.mare", "--parser", parser)
                self.assertEqual(r.returncode, 1)
                self.assertIn("linha 4, coluna 28", r.stderr)

    def test_saida_em_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            for nome, trecho in [("t.csv", "Estado;"), ("t.md", "| Estado |"), ("t.txt", "+--")]:
                caminho = str(pathlib.Path(pasta) / nome)
                r = rodar("--tabela-slr", "--saida", caminho)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(trecho, pathlib.Path(caminho).read_text(encoding="utf-8"))

    def test_sem_argumentos_pede_arquivo(self):
        self.assertEqual(rodar().returncode, 2)

    def test_opcoes_antigas_continuam_funcionando(self):
        r = rodar("exemplos/mini.mare", "--arvore")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Programa", r.stdout)


if __name__ == "__main__":
    unittest.main()
