"""
Analisador sintático (parser) da linguagem Maré.

Estratégia: descendente recursivo preditivo (LL), implementado à mão.
Cada não-terminal da gramática (ver docs/gramatica.md) corresponde a um
método `_<regra>()`. O parser consome a cadeia de tokens produzida pelo
Lexer e constrói a árvore sintática abstrata (mare.arvore).

A precedência e a associatividade dos operadores ficam codificadas na
própria hierarquia das regras de expressão:

    ou  <  e  <  nao  <  relacional  <  + -  <  * / %  <  - (unário)  <  ^

Recuperação de erros (modo pânico): ao encontrar um erro dentro de um
comando, o parser o registra, descarta tokens até um ponto seguro
(';', '}' ou início de outro comando) e continua. Assim vários erros podem
ser reportados em uma única execução.
"""

from __future__ import annotations

from . import arvore as A
from .erros import ErroSintatico
from .tokens import PALAVRAS_RESERVADAS, SIMBOLOS, Token, TipoToken as T

# Texto amigável para cada tipo de token, usado nas mensagens de erro.
_DESCRICAO = {tipo: f"'{lex}'" for lex, tipo in {**PALAVRAS_RESERVADAS, **SIMBOLOS}.items()}
_DESCRICAO.update({
    T.ID: "identificador",
    T.NUM_INT: "número inteiro",
    T.NUM_REAL: "número real",
    T.TEXTO: "texto",
    T.EOF: "fim do arquivo",
})

TIPOS = {T.T_INTEIRO: "inteiro", T.T_REAL: "real", T.T_LOGICO: "logico", T.T_TEXTO: "texto"}
RELACIONAIS = {T.IGUAL, T.DIFERENTE, T.MENOR, T.MENOR_IGUAL, T.MAIOR, T.MAIOR_IGUAL}
INICIO_COMANDO = {T.SEJA, T.FIXO, T.SE, T.ENQUANTO, T.PARA, T.REPITA, T.RETORNE, T.MOSTRE, T.LEIA}


def descrever(tipo: T) -> str:
    return _DESCRICAO.get(tipo, tipo.nome)


class Parser:
    def __init__(self, tokens: list[Token], rastrear: bool = False):
        self.tokens = tokens
        self.pos = 0
        self.erros: list[ErroSintatico] = []
        # Rastreamento: registra cada regra aplicada, cada token consumido e
        # cada erro, mostrando passo a passo como o parser reconhece o código.
        self.rastrear = rastrear
        self.rastro: list[str] = []
        self._nivel = 0
        self._descartando = False

    def _registrar(self, texto: str) -> None:
        if self.rastrear:
            self.rastro.append("│ " * self._nivel + texto)

    # ================================================== utilitários

    @property
    def atual(self) -> Token:
        return self.tokens[self.pos]

    def _espiar(self, distancia: int = 1) -> Token:
        i = min(self.pos + distancia, len(self.tokens) - 1)
        return self.tokens[i]

    def _verificar(self, *tipos: T) -> bool:
        return self.atual.tipo in tipos

    def _avancar(self) -> Token:
        token = self.atual
        if token.tipo != T.EOF:
            acao = "✗ descarta" if self._descartando else "✓ consome"
            self._registrar(f"{acao} <{token.tipo.nome}, '{token.lexema}'>  ({token.linha}:{token.coluna})")
            self.pos += 1
        return token

    def _aceitar(self, *tipos: T) -> Token | None:
        """Consome o token se ele for de um dos tipos; senão, não faz nada."""
        if self._verificar(*tipos):
            return self._avancar()
        return None

    def _esperar(self, tipo: T, contexto: str) -> Token:
        """Consome o token obrigatório ou lança erro sintático."""
        if self._verificar(tipo):
            return self._avancar()
        anterior = self.tokens[self.pos - 1] if self.pos > 0 else None
        if tipo == T.PONTO_VIRGULA and anterior and anterior.linha < self.atual.linha:
            # O ';' esquecido pertence à linha anterior: aponta para lá.
            erro = ErroSintatico(
                f"esperado ';' {contexto} (faltou ';' no fim da linha)",
                anterior.linha, anterior.coluna + len(anterior.lexema))
            raise erro
        raise self._erro(f"esperado {descrever(tipo)} {contexto}")

    def _erro(self, mensagem: str, citar_token: bool = True) -> ErroSintatico:
        t = self.atual
        if citar_token:
            encontrado = descrever(t.tipo) if t.tipo == T.EOF else f"'{t.lexema}'"
            mensagem = f"{mensagem}, mas foi encontrado {encontrado}"
        return ErroSintatico(mensagem, t.linha, t.coluna)

    def _registrar_erro(self, erro: ErroSintatico) -> None:
        self.erros.append(erro)
        self._registrar(f"✗ ERRO [{erro.linha}:{erro.coluna}] {erro.mensagem}")
        self._registrar("  → recuperação (modo pânico): descartando tokens até ';', '}' ou início de comando")

    def _sincronizar(self, inicio: int) -> None:
        """Modo pânico: pula tokens até um ponto onde é seguro recomeçar.

        `inicio` é a posição onde o comando com erro começou; se nenhum token
        foi consumido desde então, um é descartado para garantir progresso.
        Um bloco '{ ... }' encontrado no caminho é pulado por inteiro (com
        chaves balanceadas), para que o '}' dele não feche o bloco externo.
        """
        self._descartando = True
        try:
            if self.pos == inicio:
                self._avancar()
            while not self._verificar(T.EOF):
                if self._aceitar(T.PONTO_VIRGULA):
                    return
                if self._verificar(T.ABRE_CHAVE):
                    self._pular_bloco()
                    return
                if self._verificar(T.FECHA_CHAVE, T.FUNCAO, T.PRINCIPAL, *INICIO_COMANDO):
                    return
                self._avancar()
        finally:
            self._descartando = False

    def _pular_bloco(self) -> None:
        """Descarta um bloco '{ ... }' inteiro, respeitando o aninhamento."""
        profundidade = 0
        while not self._verificar(T.EOF):
            token = self._avancar()
            if token.tipo == T.ABRE_CHAVE:
                profundidade += 1
            elif token.tipo == T.FECHA_CHAVE:
                profundidade -= 1
                if profundidade == 0:
                    return

    # ================================================== programa

    def analisar(self) -> A.Programa | None:
        """programa → { funcao | declaracao } principal EOF"""
        declaracoes: list[A.No] = []
        principal: A.Bloco | None = None

        while not self._verificar(T.EOF):
            inicio = self.pos
            try:
                if self._verificar(T.FUNCAO):
                    declaracoes.append(self._funcao())
                elif self._verificar(T.SEJA, T.FIXO):
                    declaracoes.append(self._declaracao())
                elif self._verificar(T.PRINCIPAL):
                    if principal is not None:
                        raise self._erro("o bloco 'principal' só pode ser declarado uma vez", False)
                    self._avancar()
                    principal = self._bloco()
                else:
                    raise self._erro("esperado 'funcao', 'seja', 'fixo' ou 'principal' no nível do programa")
            except ErroSintatico as e:
                self._registrar_erro(e)
                self._pular_ate(inicio, T.FUNCAO, T.PRINCIPAL, T.SEJA, T.FIXO)

        if principal is None and not self.erros:
            self.erros.append(self._erro("o programa precisa de um bloco 'principal'", False))
        return A.Programa(declaracoes, principal) if principal is not None else None

    def _pular_ate(self, inicio: int, *tipos: T) -> None:
        """Recuperação no nível do programa: pula até o próximo item de topo
        (fora de qualquer bloco)."""
        self._descartando = True
        try:
            self._pular_ate_topo(inicio, *tipos)
        finally:
            self._descartando = False

    def _pular_ate_topo(self, inicio: int, *tipos: T) -> None:
        if self.pos == inicio:  # garante progresso
            self._avancar()
        profundidade = 0
        while not self._verificar(T.EOF):
            if profundidade == 0 and self._verificar(*tipos):
                return
            token = self._avancar()
            if token.tipo == T.ABRE_CHAVE:
                profundidade += 1
            elif token.tipo == T.FECHA_CHAVE:
                profundidade = max(0, profundidade - 1)

    # ================================================== declarações de função

    def _funcao(self) -> A.Funcao:
        """funcao → "funcao" ID "(" [ params ] ")" [ "->" tipo ] bloco"""
        linha = self._avancar().linha
        nome = self._esperar(T.ID, "como nome da função").lexema
        self._esperar(T.ABRE_PAR, f"após o nome da função '{nome}'")
        parametros: list[A.Parametro] = []
        if not self._verificar(T.FECHA_PAR):
            parametros.append(self._parametro())
            while self._aceitar(T.VIRGULA):
                parametros.append(self._parametro())
        self._esperar(T.FECHA_PAR, "para fechar a lista de parâmetros")
        retorno = self._tipo() if self._aceitar(T.SETA) else None
        corpo = self._bloco()
        return A.Funcao(nome, parametros, retorno, corpo, linha)

    def _parametro(self) -> A.Parametro:
        """param → ID ":" tipo"""
        token = self._esperar(T.ID, "como nome do parâmetro")
        self._esperar(T.DOIS_PONTOS, f"após o parâmetro '{token.lexema}'")
        return A.Parametro(token.lexema, self._tipo(), token.linha)

    def _tipo(self) -> str:
        """tipo → "inteiro" | "real" | "logico" | "texto" """
        if self.atual.tipo in TIPOS:
            return TIPOS[self._avancar().tipo]
        raise self._erro("esperado um tipo (inteiro, real, logico ou texto)")

    # ================================================== blocos e comandos

    def _bloco(self) -> A.Bloco:
        """bloco → "{" { comando } "}" """
        self._esperar(T.ABRE_CHAVE, "para abrir o bloco")
        comandos: list[A.No] = []
        # 'funcao' e 'principal' nunca aparecem dentro de um bloco: se surgirem,
        # faltou fechar o bloco com '}' e o erro é reportado abaixo.
        while not self._verificar(T.FECHA_CHAVE, T.EOF, T.FUNCAO, T.PRINCIPAL):
            inicio = self.pos
            try:
                comandos.append(self._comando())
            except ErroSintatico as e:
                self._registrar_erro(e)
                self._sincronizar(inicio)
        self._esperar(T.FECHA_CHAVE, "para fechar o bloco")
        return A.Bloco(comandos)

    def _comando(self) -> A.No:
        """comando → declaracao | atribuicao | chamada ";" | se | enquanto
                   | para | repita | retorne | mostre | leia"""
        t = self.atual.tipo
        if t in (T.SEJA, T.FIXO):
            return self._declaracao()
        if t == T.SE:
            return self._se()
        if t == T.ENQUANTO:
            return self._enquanto()
        if t == T.PARA:
            return self._para()
        if t == T.REPITA:
            return self._repita()
        if t == T.RETORNE:
            return self._retorne()
        if t == T.MOSTRE:
            return self._mostre()
        if t == T.LEIA:
            return self._leia()
        if t == T.ID:
            # Um token de lookahead extra decide entre atribuição e chamada.
            if self._espiar().tipo == T.ABRE_PAR:
                chamada = self._chamada()
                self._esperar(T.PONTO_VIRGULA, "após a chamada de função")
                return A.ComandoChamada(chamada, chamada.linha)
            return self._atribuicao()
        if t == T.SENAO:
            raise self._erro("'senao' sem um 'se' correspondente", False)
        raise self._erro("esperado um comando")

    def _declaracao(self) -> A.Declaracao:
        """declaracao → ("seja" ID ":" tipo [ "=" expr ] | "fixo" ID ":" tipo "=" expr) ";" """
        inicio = self._avancar()
        constante = inicio.tipo == T.FIXO
        nome = self._esperar(T.ID, f"após '{inicio.lexema}'").lexema
        self._esperar(T.DOIS_PONTOS, f"após o nome '{nome}' (formato: {inicio.lexema} {nome}: tipo)")
        tipo = self._tipo()
        valor = None
        if constante:
            self._esperar(T.ATRIB, f"— a constante '{nome}' precisa de um valor")
            valor = self._expressao()
        elif self._aceitar(T.ATRIB):
            valor = self._expressao()
        self._esperar(T.PONTO_VIRGULA, "ao final da declaração")
        return A.Declaracao(nome, tipo, valor, constante, inicio.linha)

    def _atribuicao(self) -> A.Atribuicao:
        """atribuicao → ID "=" expr ";" """
        token = self._avancar()
        self._esperar(T.ATRIB, f"após '{token.lexema}' (atribuição)")
        valor = self._expressao()
        self._esperar(T.PONTO_VIRGULA, "ao final da atribuição")
        return A.Atribuicao(token.lexema, valor, token.linha)

    def _se(self) -> A.Se:
        """se → "se" "(" expr ")" bloco [ "senao" ( se | bloco ) ]"""
        linha = self._avancar().linha
        self._esperar(T.ABRE_PAR, "após 'se'")
        condicao = self._expressao()
        self._esperar(T.FECHA_PAR, "para fechar a condição do 'se'")
        entao = self._bloco()
        senao = None
        if self._aceitar(T.SENAO):
            senao = self._se() if self._verificar(T.SE) else self._bloco()
        return A.Se(condicao, entao, senao, linha)

    def _enquanto(self) -> A.Enquanto:
        """enquanto → "enquanto" "(" expr ")" bloco"""
        linha = self._avancar().linha
        self._esperar(T.ABRE_PAR, "após 'enquanto'")
        condicao = self._expressao()
        self._esperar(T.FECHA_PAR, "para fechar a condição do 'enquanto'")
        return A.Enquanto(condicao, self._bloco(), linha)

    def _para(self) -> A.Para:
        """para → "para" ID "de" expr "ate" expr [ "passo" expr ] bloco"""
        linha = self._avancar().linha
        variavel = self._esperar(T.ID, "como variável de controle do 'para'").lexema
        self._esperar(T.DE, f"após 'para {variavel}'")
        inicio = self._expressao()
        self._esperar(T.ATE, "no laço 'para' (formato: para i de 1 ate 10)")
        fim = self._expressao()
        passo = self._expressao() if self._aceitar(T.PASSO) else None
        return A.Para(variavel, inicio, fim, passo, self._bloco(), linha)

    def _repita(self) -> A.Repita:
        """repita → "repita" bloco "ate" "(" expr ")" ";" """
        linha = self._avancar().linha
        corpo = self._bloco()
        self._esperar(T.ATE, "após o bloco do 'repita'")
        self._esperar(T.ABRE_PAR, "após 'ate'")
        condicao = self._expressao()
        self._esperar(T.FECHA_PAR, "para fechar a condição do 'repita'")
        self._esperar(T.PONTO_VIRGULA, "ao final do 'repita ... ate (...)'")
        return A.Repita(corpo, condicao, linha)

    def _retorne(self) -> A.Retorne:
        """retorne → "retorne" [ expr ] ";" """
        linha = self._avancar().linha
        valor = None if self._verificar(T.PONTO_VIRGULA) else self._expressao()
        self._esperar(T.PONTO_VIRGULA, "ao final do 'retorne'")
        return A.Retorne(valor, linha)

    def _mostre(self) -> A.Mostre:
        """mostre → "mostre" "(" argumentos ")" ";" """
        linha = self._avancar().linha
        self._esperar(T.ABRE_PAR, "após 'mostre'")
        argumentos = self._argumentos()
        self._esperar(T.FECHA_PAR, "para fechar o 'mostre'")
        self._esperar(T.PONTO_VIRGULA, "ao final do 'mostre'")
        return A.Mostre(argumentos, linha)

    def _leia(self) -> A.Leia:
        """leia → "leia" "(" ID ")" ";" """
        linha = self._avancar().linha
        self._esperar(T.ABRE_PAR, "após 'leia'")
        nome = self._esperar(T.ID, "dentro de 'leia'").lexema
        self._esperar(T.FECHA_PAR, "para fechar o 'leia'")
        self._esperar(T.PONTO_VIRGULA, "ao final do 'leia'")
        return A.Leia(nome, linha)

    # ================================================== expressões

    def _expressao(self) -> A.No:
        """expr → ou"""
        return self._ou()

    def _ou(self) -> A.No:
        """ou → e { "ou" e }"""
        no = self._e()
        while op := self._aceitar(T.OU):
            no = A.Binaria("ou", no, self._e(), op.linha)
        return no

    def _e(self) -> A.No:
        """e → nao { "e" nao }"""
        no = self._nao()
        while op := self._aceitar(T.E):
            no = A.Binaria("e", no, self._nao(), op.linha)
        return no

    def _nao(self) -> A.No:
        """nao → "nao" nao | relacional"""
        if op := self._aceitar(T.NAO):
            return A.Unaria("nao", self._nao(), op.linha)
        return self._relacional()

    def _relacional(self) -> A.No:
        """relacional → soma [ ("=="|"!="|"<"|"<="|">"|">=") soma ]   (não associativo)"""
        no = self._soma()
        if self.atual.tipo in RELACIONAIS:
            op = self._avancar()
            no = A.Binaria(op.lexema, no, self._soma(), op.linha)
            if self.atual.tipo in RELACIONAIS:
                raise self._erro("comparações não podem ser encadeadas; use 'e' (ex.: a < b e b < c)", False)
        return no

    def _soma(self) -> A.No:
        """soma → termo { ("+"|"-") termo }   (associativo à esquerda)"""
        no = self._termo()
        while op := self._aceitar(T.MAIS, T.MENOS):
            no = A.Binaria(op.lexema, no, self._termo(), op.linha)
        return no

    def _termo(self) -> A.No:
        """termo → unario { ("*"|"/"|"%") unario }   (associativo à esquerda)"""
        no = self._unario()
        while op := self._aceitar(T.MULT, T.DIV, T.MOD):
            no = A.Binaria(op.lexema, no, self._unario(), op.linha)
        return no

    def _unario(self) -> A.No:
        """unario → "-" unario | potencia"""
        if op := self._aceitar(T.MENOS):
            return A.Unaria("-", self._unario(), op.linha)
        return self._potencia()

    def _potencia(self) -> A.No:
        """potencia → primario [ "^" unario ]   (associativo à direita)"""
        base = self._primario()
        if op := self._aceitar(T.POT):
            return A.Binaria("^", base, self._unario(), op.linha)
        return base

    def _primario(self) -> A.No:
        """primario → NUM_INT | NUM_REAL | TEXTO | "verdadeiro" | "falso"
                    | ID | chamada | "(" expr ")" """
        t = self.atual
        if self._aceitar(T.NUM_INT):
            return A.Literal("inteiro", t.lexema, t.linha)
        if self._aceitar(T.NUM_REAL):
            return A.Literal("real", t.lexema, t.linha)
        if self._aceitar(T.TEXTO):
            return A.Literal("texto", t.lexema, t.linha)
        if self._aceitar(T.VERDADEIRO, T.FALSO):
            return A.Literal("logico", t.lexema, t.linha)
        if t.tipo == T.ID:
            if self._espiar().tipo == T.ABRE_PAR:
                return self._chamada()
            self._avancar()
            return A.Variavel(t.lexema, t.linha)
        if self._aceitar(T.ABRE_PAR):
            no = self._expressao()
            self._esperar(T.FECHA_PAR, "para fechar a expressão entre parênteses")
            return no
        raise self._erro("esperada uma expressão (número, texto, variável, chamada ou '(')")

    def _chamada(self) -> A.Chamada:
        """chamada → ID "(" [ argumentos ] ")" """
        token = self._avancar()
        self._avancar()  # '('
        argumentos = [] if self._verificar(T.FECHA_PAR) else self._argumentos()
        self._esperar(T.FECHA_PAR, f"para fechar a chamada de '{token.lexema}'")
        return A.Chamada(token.lexema, argumentos, token.linha)

    def _argumentos(self) -> list[A.No]:
        """argumentos → expr { "," expr }"""
        argumentos = [self._expressao()]
        while self._aceitar(T.VIRGULA):
            argumentos.append(self._expressao())
        return argumentos


# ====================================================== rastreamento
# Cada método de regra é "embrulhado" para registrar a entrada na regra
# (com o próximo token) quando o rastreamento está ativo.

_REGRAS = {
    "analisar": "programa", "_funcao": "funcao", "_parametro": "parametro",
    "_tipo": "tipo", "_bloco": "bloco", "_comando": "comando",
    "_declaracao": "declaracao", "_atribuicao": "atribuicao", "_se": "se",
    "_enquanto": "enquanto", "_para": "para", "_repita": "repita",
    "_retorne": "retorne", "_mostre": "mostre", "_leia": "leia",
    "_expressao": "expr", "_ou": "ou", "_e": "e", "_nao": "nao",
    "_relacional": "relacional", "_soma": "soma", "_termo": "termo",
    "_unario": "unario", "_potencia": "potencia", "_primario": "primario",
    "_chamada": "chamada", "_argumentos": "argumentos",
}


def _rastreado(metodo, nome_regra):
    def envoltorio(self, *args, **kwargs):
        if not self.rastrear:
            return metodo(self, *args, **kwargs)
        t = self.atual
        self._registrar(f"▶ {nome_regra}   [próximo token: <{t.tipo.nome}, '{t.lexema}'>]")
        self._nivel += 1
        try:
            return metodo(self, *args, **kwargs)
        finally:
            self._nivel -= 1

    envoltorio.__name__ = metodo.__name__
    envoltorio.__doc__ = metodo.__doc__
    return envoltorio


for _metodo, _regra in _REGRAS.items():
    setattr(Parser, _metodo, _rastreado(getattr(Parser, _metodo), _regra))
