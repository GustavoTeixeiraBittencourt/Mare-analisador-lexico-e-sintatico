# Maré — Analisador Léxico e Sintático

Projeto da disciplina de Automatos e Compiladores (CESUPA). Implementa o
**analisador léxico** e **três analisadores sintáticos** da linguagem **Maré**, uma
linguagem imperativa didática, tipada, com palavras-chave em português, criada pela equipe:

1. **descendente recursivo** (1º bimestre), que constrói a árvore sintática;
2. **LL(1) guiado por tabela, com pilha** — FIRST/FOLLOW e tabela `M[A, a]` calculados pelo programa;
3. **SLR(1)** — coleção de itens LR(0), tabela ACTION/GOTO e algoritmo shift/reduce;

além de um **gerador automático de gramática LL(1)** a partir de uma gramática ambígua de expressões.

Implementação **pura em Python** (sem ANTLR/PLY/Bison/bibliotecas de parsing): scanner baseado em
expressões regulares e parsers escritos à mão. Os três parsers consomem a mesma cadeia de tokens
do analisador léxico e **aceitam exatamente os mesmos programas** (verificado nos testes).

## Integrantes

| Nome | 
|---|
| Gustavo Teixeira Bittencourt de Oliveira | 
|Christophe Abelem Pinho | 
| Elissandra Nascimento Bernadett Abdon| 
| Edgar Klewert da Costa Araujo|
| Adler Augustus de Castro Mota|

## A linguagem em 20 linhas

```text
fixo MEDIA_MINIMA: real = 7.0;            # constante global

funcao media(p1: real, p2: real) -> real {
    retorne (p1 + p2) / 2;
}

principal {                               # bloco principal (obrigatório)
    seja nota: real = media(6.5, 8.0);    # declaração com tipo
    seja faltas: inteiro = 3;

    se (nota >= MEDIA_MINIMA e nao (faltas > 10)) {
        mostre("Aprovado com ", nota);
    } senao se (nota >= 5.0) {
        mostre("Recuperacao");
    } senao {
        mostre("Reprovado");
    }

    enquanto (faltas > 0) { faltas = faltas - 1; }
    para i de 1 ate 10 passo 2 { mostre(i ^ 2 % 3); }
    repita { leia(nota); } ate (nota >= 0.0);
}
```

| Recurso | Sintaxe |
|---|---|
| Tipos | `inteiro`, `real`, `logico`, `texto` |
| Variável / constante | `seja x: inteiro = 1;` / `fixo PI: real = 3.14;` |
| Bloco principal | `principal { ... }` |
| Condicional | `se (...) { } senao se (...) { } senao { }` |
| Laços | `enquanto (...) { }`, `para i de a ate b passo p { }`, `repita { } ate (...);` |
| Funções | `funcao nome(a: tipo, ...) -> tipo { retorne expr; }` |
| Entrada / saída | `leia(x);`, `mostre(a, b, ...);` |
| Aritméticos | `+ - * / % ^` |
| Relacionais | `== != < <= > >=` |
| Lógicos | `e`, `ou`, `nao` |
| Comentários | `# linha` e `#* bloco *#` |

A especificação completa (gramática EBNF, tabela de tokens e expressões
regulares) está em [`docs/gramatica.md`](docs/gramatica.md). As gramáticas em BNF pura usadas pelos
analisadores de tabela estão documentadas em [`docs/gramatica_ll1.md`](docs/gramatica_ll1.md)
(ambígua → precedência → sem recursão à esquerda → fatorada) e
[`docs/gramatica_slr.md`](docs/gramatica_slr.md) (aumentada, para SLR(1)).

## Como executar

Requer apenas **Python 3.10+** (nenhuma biblioteca externa).

```bash
# análise completa: regex, cadeia de tokens, tabela de lexemas, árvore
python main.py exemplos/completo.mare

# partes específicas
python main.py exemplos/completo.mare --regex     # expressões regulares do scanner
python main.py exemplos/completo.mare --tokens    # cadeia de tokens em tabela
python main.py exemplos/completo.mare --cadeia    # cadeia de tokens por linha
python main.py exemplos/completo.mare --lexemas   # tabela de lexemas e tokens
python main.py exemplos/completo.mare --arvore    # árvore sintática
python main.py exemplos/mini.mare --rastro        # rastreamento passo a passo do parser

# caso rejeitado com rastreamento (regra aplicada → token → erro → recuperação)
python main.py exemplos/rejeitado.mare --rastro

# exportar a árvore como imagem (requer Graphviz)
python main.py exemplos/mini.mare --dot arvore.dot
dot -Tpng arvore.dot -o arvore.png

# exemplos com erros (o analisador aponta linha e coluna)
python main.py exemplos/erro_lexico.mare
python main.py exemplos/erro_sintatico.mare

# testes automatizados
python -m unittest discover -s tests -v
```

### Analisadores LL(1) e SLR(1)

```bash
# --- LL(1) com tabela e pilha ---
python main.py --gramatica-ll1                    # gramática final em BNF, numerada
python main.py --first-follow                     # FIRST e FOLLOW (ponto fixo)
python main.py --tabela-ll1                       # tabela M[A, a] + conflitos (zero)
python main.py exemplos/expressao.mare --ll1      # rastro Passo | Pilha | Entrada | Ação

# --- SLR(1) ---
python main.py --gramatica-slr                    # gramática aumentada (produção 0: programa' → programa)
python main.py --itens-lr0                        # coleção canônica: I0, I1, ... com o ponto •
python main.py --tabela-slr                       # ACTION/GOTO + conflitos (zero)
python main.py exemplos/expressao.mare --slr      # rastro shift/reduce

# --- escolher o parser da análise sintática ---
python main.py exemplos/completo.mare --parser rd     # descendente recursivo (padrão)
python main.py exemplos/completo.mare --parser ll1
python main.py exemplos/completo.mare --parser slr

# --- tabelas grandes: o terminal mostra uma versão abreviada; --saida grava tudo ---
python main.py --tabela-slr --saida tabela_slr.csv    # .csv, .md ou .txt (pela extensão)
python main.py exemplos/completo.mare --ll1 --saida rastro_ll1.md
```

As opções de gramática (`--gramatica-*`, `--first-follow`, `--tabela-*`, `--itens-lr0`) não precisam de
arquivo `.mare`. Saídas já geradas estão em [`docs/saidas/`](docs/saidas/).

### Gerador automático de gramática LL(1)

```bash
python main.py --converter gramaticas/ambigua_expr.txt                  # mostra cada etapa
python main.py --converter gramaticas/ambigua_expr.txt --saida ll1.txt  # grava a gramática gerada
```

O arquivo de entrada traz a gramática **ambígua** e a precedência dos operadores, em ordem crescente
(`%left`, `%right`, `%nonassoc` para binários; `%prefix` para unários):

```text
%left ou
%left e
%prefix nao
%nonassoc == != < <= > >=
%left + -
%left * / %
%prefix -
%right ^

E -> E ou E | E e E | nao E | E == E | E + E | E * E | - E | E ^ E | ( E ) | id | num | id ( A )
A -> E , A | E
```

O programa mostra, nesta ordem: **(1)** gramática sem ambiguidade (um não-terminal por nível de precedência),
**(2)** sem recursão à esquerda (direta e indireta), **(3)** fatorada à esquerda (repetida até não restar prefixo
comum) e **(4)** FIRST/FOLLOW + tabela LL(1) com a contagem de conflitos (para o exemplo, **zero conflitos**).
Ambiguidades que não vêm de operadores (como o "senão pendurado") **não** são resolvidas automaticamente:
o programa informa os conflitos que sobraram. Como no yacc clássico, o operando direito de um operador
associativo à direita é do mesmo nível, então `2 ^ -3` só seria aceito com o menos unário abaixo de `^` na precedência.

## Estrutura

```text
mare/
├── main.py                    # interface de linha de comando
├── mare/
│   ├── tokens.py              # tipos de token, classes de lexemas, palavras reservadas
│   ├── lexer.py               # analisador léxico (regex mestre com grupos nomeados)
│   ├── parser.py              # parser descendente recursivo (constrói a AST)
│   ├── arvore.py              # nós da árvore sintática (AST)
│   ├── erros.py               # erros léxicos/sintáticos com linha e coluna
│   ├── exibicao.py            # tabelas, cadeia de tokens, árvore (texto, DOT, LaTeX)
│   ├── gramatica.py           # classe Gramatica + leitor do formato "A -> B c | ε"
│   ├── first_follow.py        # FIRST e FOLLOW por ponto fixo
│   ├── ll1.py                 # tabela LL(1), conflitos e análise preditiva com pilha
│   ├── lr0.py                 # closure, goto e coleção canônica de itens LR(0)
│   ├── slr.py                 # tabela ACTION/GOTO SLR(1) e algoritmo shift/reduce
│   ├── conversor.py           # gerador: gramática ambígua → LL(1)
│   ├── entrada.py             # adapta os tokens do Lexer aos parsers de tabela
│   ├── rastro.py              # rastro Passo | Pilha | Entrada | Ação
│   └── tabelas.py             # tabelas em texto, markdown e csv
├── gramaticas/
│   ├── mare_ll1.txt           # Maré em BNF, LL(1)
│   ├── mare_slr.txt           # Maré em BNF, aumentada, para SLR(1)
│   └── ambigua_expr.txt       # entrada de exemplo do conversor
├── exemplos/                  # programas .mare (válidos e com erros)
├── tests/                     # testes unitários (unittest)
├── docs/                      # gramáticas (EBNF, LL(1), SLR), rastros, roteiro, saídas geradas
└── artigo/                    # artigo IEEE (.tex para o Overleaf e .pdf)
```

## Arquitetura

```text
                                   ┌─► parser recursivo ─► árvore sintática (AST)
código-fonte ─► Lexer ─► [Token] ──┼─► LL(1):  FIRST/FOLLOW ─► tabela M[A,a] ─► pilha ─► aceito / erro
   (.mare)    (regex)              └─► SLR(1): FIRST/FOLLOW ─► itens LR(0) ─► ACTION/GOTO ─► shift/reduce ─► aceito / erro
                                          ▲
                        gramaticas/*.txt ─┘  (lidas por Gramatica; nada é fixado no código)
```

1. **Léxico** (`lexer.py`): cada classe de lexema é uma expressão regular; todas
   são unidas em uma *regex mestre* com grupos nomeados, aplicada em sequência
   sobre o texto. O nome do grupo que casou define a classe; identificadores são
   conferidos na tabela de palavras reservadas. Erros não interrompem a varredura.
2. **Descendente recursivo** (`parser.py`): um método por regra da gramática. A precedência dos
   operadores está na hierarquia das regras (`ou` → `e` → `nao` → relacional →
   `+ -` → `* / %` → unário → `^`). Em caso de erro, o parser usa **modo pânico**
   (descarta tokens até `;`, `}` ou início de comando) e continua, reportando
   vários erros de uma vez.
3. **LL(1)** (`ll1.py`): não há uma função por regra. A gramática (BNF pura, fatorada, sem recursão à
   esquerda) é lida de arquivo; `first_follow.py` calcula FIRST/FOLLOW; a tabela `M[A, a]` é construída
   e **qualquer célula com 2+ produções é reportada como conflito**. A análise usa uma pilha (`$ S`):
   terminal no topo ⇒ *match*; não-terminal ⇒ expande por `M`. Modo pânico com FOLLOW como
   conjunto de sincronização.
4. **SLR(1)** (`lr0.py`, `slr.py`): coleção canônica de itens LR(0) (`closure`/`goto`), tabela ACTION
   (`s n`, `r n`, `acc`) com reduções em FOLLOW(A), tabela GOTO e o laço shift/reduce com pilha de
   estados e símbolos. Detecta conflitos shift/reduce e reduce/reduce.

### Números das gramáticas

| | LL(1) | SLR(1) |
|---|---|---|
| Produções | 98 | 85 (84 + `programa' → programa`) |
| Terminais | 49 | 49 |
| Não-terminais | 49 | 36 |
| Estados LR(0) | — | 160 (582 transições) |
| Tabela | 300 células preenchidas (de 2450) | ACTION: 1201 células; GOTO: 254 |
| **Conflitos** | **0** | **0** |

### LL(1) × SLR(1) em uma linha

O LL(1) exige uma gramática transformada (sem recursão à esquerda e fatorada, com 98 produções e
rastro de 51 passos em `expressao.mare`) e decide a produção **antes** de ler o que ela gera; o SLR(1)
aceita a gramática natural, recursiva à esquerda, e decide **depois** (38 passos), ao custo de um
autômato maior (160 estados).

## Próximas etapas (semestre)

- Análise semântica: tabela de símbolos, escopo, verificação de tipos.
- Interpretação ou geração de código a partir da AST.
