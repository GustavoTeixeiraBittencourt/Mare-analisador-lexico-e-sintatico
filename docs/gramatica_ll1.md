# Gramática da Maré no formato LL(1)

Este documento mostra, **na ordem exigida**, como a gramática da Maré (a
EBNF de [`gramatica.md`](gramatica.md)) é transformada até ficar em **BNF pura
e LL(1)**, pronta para o analisador preditivo com tabela e pilha (`mare/ll1.py`):

| Etapa | O que se faz | Resultado |
|---|---|---|
| (a) | Gramática **ambígua** de expressões | duas árvores para a mesma sentença |
| (b) | Eliminação da ambiguidade (precedência e associatividade) | um não-terminal por nível |
| (c) | Eliminação da **recursão à esquerda** | `A → β A'`, `A' → α A' \| ε` |
| (d) | **Fatoração à esquerda** | nenhum par de alternativas com o mesmo prefixo |

Tudo o que não é expressão (estrutura e comandos) já é praticamente LL(1) — só
precisa ser reescrito de EBNF para BNF e ter os pontos de *lookahead 2*
fatorados (etapa d).

> Notação: os terminais usam os nomes do enum `TipoToken` (`ID`, `NUM_INT`,
> `ABRE_PAR`, `MAIS`, ...); não-terminais são minúsculos. `ε` é a cadeia vazia.

---

## Etapa (a) — Gramática ambígua

Escrita do modo mais "natural", com **uma única regra** para expressões e todos os
operadores misturados:

```text
expr → expr OU expr
     | expr E expr
     | NAO expr
     | expr op_rel expr          op_rel → IGUAL | DIFERENTE | MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL
     | expr MAIS expr | expr MENOS expr
     | expr MULT expr | expr DIV expr | expr MOD expr
     | MENOS expr                (menos unário)
     | expr POT expr
     | ABRE_PAR expr FECHA_PAR
     | NUM_INT | NUM_REAL | TEXTO | VERDADEIRO | FALSO
     | ID | ID ABRE_PAR args_opt FECHA_PAR
```

### Prova da ambiguidade

A sentença `a + b * c` (tokens `ID MAIS ID MULT ID`) tem **duas árvores de derivação**:

```text
        Árvore 1: (a + b) * c                    Árvore 2: a + (b * c)

              expr                                        expr
          ┌────┼─────┐                                ┌─────┼─────┐
        expr  MULT  expr                            expr  MAIS   expr
     ┌───┼───┐        │                              │        ┌───┼───┐
   expr MAIS expr     ID(c)                        ID(a)    expr MULT expr
    │         │                                              │          │
  ID(a)     ID(b)                                          ID(b)      ID(c)
```

Duas árvores ⇒ duas "interpretações" (`(a+b)*c` ≠ `a+(b*c)`): a gramática é
**ambígua** e não serve para análise determinística. O mesmo ocorre com a
associatividade: `10 - 3 - 2` pode ser `(10-3)-2 = 5` ou `10-(3-2) = 9`;
com o unário, `- a + b` pode ser `(-a)+b` ou `-(a+b)`; e `a < b < c`
pode ser `(a<b)<c` ou `a<(b<c)`.

---

## Etapa (b) — Eliminação da ambiguidade: precedência e associatividade

Cria-se **um não-terminal por nível de precedência**. Cada nível só pode usar
o nível imediatamente mais forte como operando, o que obriga os operadores
de maior precedência a ficarem mais fundo na árvore. A associatividade vem do
lado em que a recursão é colocada:

| Nível (menor → maior) | Operadores | Associatividade | Forma da regra |
|---|---|---|---|
| 1 | `ou` | esquerda | `expr_ou → expr_ou OU expr_e \| expr_e` (recursiva à esquerda) |
| 2 | `e` | esquerda | `expr_e → expr_e E expr_nao \| expr_nao` |
| 3 | `nao` | prefixo | `expr_nao → NAO expr_nao \| expr_rel` |
| 4 | `== != < <= > >=` | **não associativa** | `expr_rel → soma op_rel soma \| soma` (sem recursão: `a<b<c` não é gerado) |
| 5 | `+ -` | esquerda | `soma → soma MAIS termo \| soma MENOS termo \| termo` |
| 6 | `* / %` | esquerda | `termo → termo MULT unario \| ... \| unario` |
| 7 | `-` unário | prefixo | `unario → MENOS unario \| potencia` |
| 8 | `^` | **direita** | `potencia → primario POT unario \| primario` (recursão à direita, via `unario`) |

Resultado da etapa (b) para as expressões (esta é exatamente a gramática usada pelo
**SLR(1)** — ver [`gramatica_slr.md`](gramatica_slr.md)):

```text
expr      → expr_ou
expr_ou   → expr_ou OU expr_e   | expr_e
expr_e    → expr_e E expr_nao   | expr_nao
expr_nao  → NAO expr_nao        | expr_rel
expr_rel  → soma op_rel soma    | soma
soma      → soma MAIS termo | soma MENOS termo | termo
termo     → termo MULT unario | termo DIV unario | termo MOD unario | unario
unario    → MENOS unario | potencia
potencia  → primario POT unario | primario
primario  → NUM_INT | NUM_REAL | TEXTO | VERDADEIRO | FALSO
          | ID | ID ABRE_PAR args_opt FECHA_PAR
          | ABRE_PAR expr FECHA_PAR
```

Agora `a + b * c` só tem **uma** árvore: `*` está no nível `termo`, mais fundo que
`+` (nível `soma`), então `b * c` precisa ser agrupado antes. E `2 ^ 3 ^ 2` só
é derivável como `2 ^ (3 ^ 2)`, porque o operando direito de `^` é `unario → potencia`,
que pode conter outro `^`, enquanto o esquerdo é `primario`.

Efeito de usar `unario` à direita do `^`: `2 ^ -3` é aceito, e `-2 ^ 2` é `-(2 ^ 2)`
(o unário fica acima da potência), igual ao parser descendente recursivo.

---

## Etapa (c) — Eliminação da recursão à esquerda

Um analisador descendente (LL) entra em laço infinito com `A → A α`: para
expandir `A` ele precisaria expandir `A` de novo, sem consumir nenhum token.
A transformação-padrão para `A → A α | β` é:

```text
A  → β A'
A' → α A' | ε
```

Aplicada a cada regra recursiva à esquerda da etapa (b):

| Antes (recursiva à esquerda) | Depois |
|---|---|
| `expr_ou → expr_ou OU expr_e \| expr_e` | `expr_ou → expr_e expr_ou'`<br>`expr_ou' → OU expr_e expr_ou' \| ε` |
| `expr_e → expr_e E expr_nao \| expr_nao` | `expr_e → expr_nao expr_e'`<br>`expr_e' → E expr_nao expr_e' \| ε` |
| `soma → soma MAIS termo \| soma MENOS termo \| termo` | `soma → termo soma'`<br>`soma' → MAIS termo soma' \| MENOS termo soma' \| ε` |
| `termo → termo MULT unario \| termo DIV unario \| termo MOD unario \| unario` | `termo → unario termo'`<br>`termo' → MULT unario termo' \| DIV unario termo' \| MOD unario termo' \| ε` |

Em cada caso, `α` é "operador + operando" e `β` é a alternativa sem recursão.
A **associatividade à esquerda continua garantida**: a sequência `termo soma' soma' ...`
é lida da esquerda para a direita e cada operador novo "envolve" o que já foi lido.
As demais regras (`expr_nao`, `expr_rel`, `unario`, `potencia`) não têm recursão à
esquerda (as recursões de `expr_nao` e `unario` são à *direita*, o que é permitido em LL).

Na estrutura da linguagem, as repetições EBNF `{ ... }` viram recursão à *direita*
(`itens → item itens | ε`), então também não há recursão à esquerda ali.

---

## Etapa (d) — Fatoração à esquerda

Duas alternativas do mesmo não-terminal que começam com o mesmo símbolo impedem o
LL(1): com um token de lookahead não dá para escolher. A solução para
`A → α β1 | α β2` é `A → α A'`, `A' → β1 | β2`.

### Pontos encontrados

| Regra | Problema | Fatoração |
|---|---|---|
| `expr_rel → soma op_rel soma \| soma` | ambas começam com `soma` | `expr_rel → soma rel_opc`<br>`rel_opc → op_rel soma \| ε` |
| `potencia → primario POT unario \| primario` | ambas começam com `primario` | `potencia → primario pot_opc`<br>`pot_opc → POT unario \| ε` |
| `primario → ID \| ID ABRE_PAR args_opt FECHA_PAR \| ...` | variável e chamada começam com `ID` (**o parser recursivo usa lookahead 2**) | `primario → ID sufixo_id \| ...`<br>`sufixo_id → ABRE_PAR args_opt FECHA_PAR \| ε` |
| `comando → atribuicao \| chamada PONTO_VIRGULA \| ...`, com `atribuicao → ID ATRIB expr ;` e `chamada → ID ( ... )` | atribuição `x = ...;` e chamada `f(...);` começam com `ID` (**lookahead 2** no parser recursivo, `_espiar()`) | `comando → cmd_id \| ...`<br>`cmd_id → ID resto_id`<br>`resto_id → ATRIB expr PONTO_VIRGULA \| ABRE_PAR args_opt FECHA_PAR PONTO_VIRGULA` |

### Outros pontos verificados (já eram LL(1))

* **`se / senao se / senao`:** `se → SE ( expr ) bloco senao_opt`, `senao_opt → SENAO senao_corpo | ε`,
  `senao_corpo → se | bloco`. Não há "senão pendurado" porque o bloco usa `{ }`; a
  tabela confirma: `SENAO` nunca pertence a FOLLOW(`senao_opt`).
* **`declaracao`:** `SEJA ...` e `FIXO ...` começam com tokens diferentes; o `[ = expr ]` de
  `seja` vira `init_opt → ATRIB expr | ε`.
* **`retorne`:** `retorne [expr] ;` vira `retorno_expr → expr | ε`; `PONTO_VIRGULA` ∈ FOLLOW e
  não pertence a FIRST(`expr`), então não há conflito.
* **`para`:** o `[ passo expr ]` vira `passo_opt → PASSO expr | ε`; o que vem depois é `{`
  (`ABRE_CHAVE`), que não inicia expressão.
* **Parâmetros e argumentos:** `p { , p }` vira `params → param params'`,
  `params' → VIRGULA param params' | ε` (e o mesmo para `args`).
* O **não-terminal inicial** não aparece à direita e o token `EOF` do léxico é tratado como o marcador `$`.

O que mais poderia gerar conflito (ε-produções cujo FOLLOW colide com FIRST) é checado
**automaticamente**: o programa monta a tabela e acusa qualquer célula com mais de uma produção.
Resultado para a gramática abaixo: **zero conflitos** (`python main.py --tabela-ll1`).

### Conversão de EBNF para BNF

| EBNF | BNF |
|---|---|
| `{ x }` (zero ou mais) | `L → x L \| ε` |
| `[ x ]` (opcional) | `O → x \| ε` |
| `( x \| y )` (agrupamento) | `G → x \| y` |

---

## Gramática final em BNF pura (LL(1))

Arquivo lido pelo programa: [`../gramaticas/mare_ll1.txt`](../gramaticas/mare_ll1.txt).

```text
programa    -> itens PRINCIPAL bloco
itens       -> item itens | ε
item        -> funcao | declaracao
funcao      -> FUNCAO ID ABRE_PAR params_opt FECHA_PAR retorno_opt bloco
params_opt  -> params | ε
params      -> param params'
params'     -> VIRGULA param params' | ε
param       -> ID DOIS_PONTOS tipo
retorno_opt -> SETA tipo | ε
tipo        -> T_INTEIRO | T_REAL | T_LOGICO | T_TEXTO
bloco       -> ABRE_CHAVE comandos FECHA_CHAVE
comandos    -> comando comandos | ε

# ---------------------------------------------------------------- comandos
comando     -> declaracao | cmd_id | se | enquanto | para | repita
             | retorne | mostre | leia
declaracao  -> SEJA ID DOIS_PONTOS tipo init_opt PONTO_VIRGULA
             | FIXO ID DOIS_PONTOS tipo ATRIB expr PONTO_VIRGULA
init_opt    -> ATRIB expr | ε
# fatoração: atribuição e chamada começam ambas com ID
cmd_id      -> ID resto_id
resto_id    -> ATRIB expr PONTO_VIRGULA
             | ABRE_PAR args_opt FECHA_PAR PONTO_VIRGULA
se          -> SE ABRE_PAR expr FECHA_PAR bloco senao_opt
senao_opt   -> SENAO senao_corpo | ε
senao_corpo -> se | bloco
enquanto    -> ENQUANTO ABRE_PAR expr FECHA_PAR bloco
para        -> PARA ID DE expr ATE expr passo_opt bloco
passo_opt   -> PASSO expr | ε
repita      -> REPITA bloco ATE ABRE_PAR expr FECHA_PAR PONTO_VIRGULA
retorne     -> RETORNE retorno_expr PONTO_VIRGULA
retorno_expr -> expr | ε
mostre      -> MOSTRE ABRE_PAR args FECHA_PAR PONTO_VIRGULA
leia        -> LEIA ABRE_PAR ID FECHA_PAR PONTO_VIRGULA

# ---------------------------------------------------------------- expressões
# da MENOR para a MAIOR precedência: ou < e < nao < relacional < + - < * / % < - unário < ^
expr        -> expr_ou
expr_ou     -> expr_e expr_ou'
expr_ou'    -> OU expr_e expr_ou' | ε
expr_e      -> expr_nao expr_e'
expr_e'     -> E expr_nao expr_e' | ε
expr_nao    -> NAO expr_nao | expr_rel
expr_rel    -> soma rel_opc
rel_opc     -> op_rel soma | ε
op_rel      -> IGUAL | DIFERENTE | MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL
soma        -> termo soma'
soma'       -> MAIS termo soma' | MENOS termo soma' | ε
termo       -> unario termo'
termo'      -> MULT unario termo' | DIV unario termo' | MOD unario termo' | ε
unario      -> MENOS unario | potencia
potencia    -> primario pot_opc
pot_opc     -> POT unario | ε
primario    -> NUM_INT | NUM_REAL | TEXTO | VERDADEIRO | FALSO
             | ID sufixo_id
             | ABRE_PAR expr FECHA_PAR
# fatoração: variável e chamada começam ambas com ID
sufixo_id   -> ABRE_PAR args_opt FECHA_PAR | ε
args_opt    -> args | ε
args        -> expr args'
args'       -> VIRGULA expr args' | ε
```

**Números:** 98 produções, 49 terminais, 49 não-terminais, símbolo inicial 'programa'.

### Verificação feita pelo programa

```bash
python main.py --gramatica-ll1     # imprime a gramática numerada
python main.py --first-follow      # FIRST e FOLLOW calculados por ponto fixo
python main.py --tabela-ll1        # tabela M[A, a] e relatório de conflitos
```

A tabela M[A, a] é construída automaticamente e **não tem nenhuma célula com mais de
uma produção**; portanto a gramática é LL(1) e o parser preditivo com pilha
(`python main.py arquivo.mare --ll1`) decide cada expansão olhando apenas **um** token.
