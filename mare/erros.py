"""Erros reportados pelos analisadores, sempre com linha e coluna."""


class ErroMare(Exception):
    fase = "Erro"

    def __init__(self, mensagem: str, linha: int, coluna: int):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        super().__init__(f"{self.fase} [linha {linha}, coluna {coluna}]: {mensagem}")


class ErroLexico(ErroMare):
    fase = "Erro léxico"


class ErroSintatico(ErroMare):
    fase = "Erro sintático"


def mostrar_contexto(fonte: str, erro: ErroMare) -> str:
    """Devolve a linha do código com um marcador (^) sob a coluna do erro."""
    linhas = fonte.splitlines()
    if not 1 <= erro.linha <= len(linhas):
        return str(erro)
    trecho = linhas[erro.linha - 1].replace("\t", " ")
    prefixo = f"{erro.linha:>4} | "
    marcador = " " * (len(prefixo) + erro.coluna - 1) + "^"
    return f"{erro}\n{prefixo}{trecho}\n{marcador}"
