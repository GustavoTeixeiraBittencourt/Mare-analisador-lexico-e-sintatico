# Maré — Analisador Léxico e Sintático

Projeto do 1º bimestre da disciplina de Automatos e Compiladores (CESUPA). Implementa o
**analisador léxico** e a **versão inicial do analisador sintático** da
linguagem **Maré**, uma linguagem imperativa didática, tipada, com palavras-chave
em português, criada pela equipe.

Implementação **pura em Python** (sem ANTLR/PLY/Bison): scanner baseado em
expressões regulares e parser **descendente recursivo** que constrói a árvore
sintática.

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
regulares) está em [`docs/gramatica.md`](docs/gramatica.md).

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

## Estrutura

```text
mare/
├── mare/
│   ├── tokens.py     # tipos de token, classes de lexemas, palavras reservadas
│   ├── lexer.py      # analisador léxico (regex mestre com grupos nomeados)
│   ├── parser.py     # analisador sintático descendente recursivo
│   ├── arvore.py     # nós da árvore sintática (AST)
│   ├── erros.py      # erros léxicos/sintáticos com linha e coluna
│   └── exibicao.py   # tabelas, cadeia de tokens, árvore (texto, DOT, LaTeX)
├── exemplos/         # programas .mare (válidos e com erros)
├── tests/            # testes unitários (unittest)
├── docs/             # gramática, roteiro da apresentação, saída de exemplo
├── artigo/           # artigo IEEE (.tex para o Overleaf e .pdf)
└── main.py           # interface de linha de comando
```

## Arquitetura

```text
código-fonte ──► Lexer ──► cadeia de tokens ──► Parser ──► árvore sintática
   (.mare)     (regex)     [Token(tipo,        (descendente   (AST, mare/arvore.py)
                            lexema, lin, col)]   recursivo)
```

1. **Léxico** (`lexer.py`): cada classe de lexema é uma expressão regular; todas
   são unidas em uma *regex mestre* com grupos nomeados, aplicada em sequência
   sobre o texto. O nome do grupo que casou define a classe; identificadores são
   conferidos na tabela de palavras reservadas. Erros não interrompem a varredura.
2. **Sintático** (`parser.py`): um método por regra da gramática. A precedência dos
   operadores está na hierarquia das regras (`ou` → `e` → `nao` → relacional →
   `+ -` → `* / %` → unário → `^`). Em caso de erro, o parser usa **modo pânico**
   (descarta tokens até `;`, `}` ou início de comando) e continua, reportando
   vários erros de uma vez.

## Próximas etapas (semestre)

- Análise semântica: tabela de símbolos, escopo, verificação de tipos.
- Interpretação ou geração de código a partir da AST.
