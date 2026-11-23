# Gramática da Maré para o analisador SLR(1)

Para o analisador **SLR(1)** (`mare/lr0.py` e `mare/slr.py`) usa-se a gramática
**sem ambiguidade da etapa (b)** de [`gramatica_ll1.md`](gramatica_ll1.md) — isto é,
antes de eliminar a recursão à esquerda e de fatorar — escrita em BNF pura e
**aumentada** com a produção `programa' → programa`.

## Por que não é preciso transformar mais nada

| Transformação do LL(1) | No SLR(1) |
|---|---|
| Eliminar recursão à esquerda | **Não precisa.** Um analisador LR constrói a árvore de baixo para cima (*bottom-up*); `soma → soma MAIS termo` é natural e até **preferível**: a pilha vai acumulando `soma` e a associatividade à esquerda sai de graça. |
| Fatorar à esquerda | **Não precisa.** O LR adia a decisão: `ID ATRIB ...` (atribuição) e `ID ABRE_PAR ...` (chamada) compartilham o prefixo `ID` na pilha, e só se decide qual produção reduzir depois de ler o que vem a seguir. |
| Eliminar ambiguidade | **Continua necessário**: uma gramática ambígua gera conflitos shift/reduce (ver abaixo). |

Por isso a gramática SLR é mais fiel à EBNF original: `{ x }` vira recursão à esquerda
(`comandos → comandos comando | ε`, `params → params VIRGULA param | param`) e `[ x ]` vira
duas alternativas (com e sem `x`) ou uma produção ε.

## Gramática aumentada

A construção LR precisa de **um único ponto de aceitação**. Por isso acrescenta-se a
produção **0**:

```text
programa' → programa
```

O analisador aceita exatamente quando está para reduzir `programa' → programa` com o marcador `$`
na entrada (ação `acc`). Esta produção é a de número 0; as da Maré são numeradas de 1 em diante
(`reduce n` no rastro refere-se a esses números).

## Associatividade e precedência na gramática SLR

Mesmos níveis do LL(1), e agora **as recursões à esquerda ficam intactas**:

```text
expr_ou  → expr_ou OU expr_e     | expr_e              # esquerda
expr_e   → expr_e E expr_nao     | expr_nao            # esquerda
expr_nao → NAO expr_nao          | expr_rel            # prefixo
expr_rel → soma op_rel soma      | soma                # NÃO associativo
soma     → soma MAIS termo | soma MENOS termo | termo  # esquerda
termo    → termo MULT unario | ... | unario            # esquerda
unario   → MENOS unario | potencia                     # prefixo
potencia → primario POT unario | primario              # direita
```

## Gramática final (BNF pura, aumentada)

Arquivo lido pelo programa: [`../gramaticas/mare_slr.txt`](../gramaticas/mare_slr.txt).

```text
programa'   -> programa

# ---------------------------------------------------------------- estrutura
programa    -> itens PRINCIPAL bloco
itens       -> itens item | ε
item        -> funcao | declaracao
funcao      -> FUNCAO ID ABRE_PAR params_opt FECHA_PAR retorno_opt bloco
params_opt  -> params | ε
params      -> params VIRGULA param | param
param       -> ID DOIS_PONTOS tipo
retorno_opt -> SETA tipo | ε
tipo        -> T_INTEIRO | T_REAL | T_LOGICO | T_TEXTO
bloco       -> ABRE_CHAVE comandos FECHA_CHAVE
comandos    -> comandos comando | ε

# ---------------------------------------------------------------- comandos
comando     -> declaracao | atribuicao | chamada PONTO_VIRGULA | se | enquanto
             | para | repita | retorne | mostre | leia
declaracao  -> SEJA ID DOIS_PONTOS tipo PONTO_VIRGULA
             | SEJA ID DOIS_PONTOS tipo ATRIB expr PONTO_VIRGULA
             | FIXO ID DOIS_PONTOS tipo ATRIB expr PONTO_VIRGULA
atribuicao  -> ID ATRIB expr PONTO_VIRGULA
se          -> SE ABRE_PAR expr FECHA_PAR bloco
             | SE ABRE_PAR expr FECHA_PAR bloco SENAO se
             | SE ABRE_PAR expr FECHA_PAR bloco SENAO bloco
enquanto    -> ENQUANTO ABRE_PAR expr FECHA_PAR bloco
para        -> PARA ID DE expr ATE expr bloco
             | PARA ID DE expr ATE expr PASSO expr bloco
repita      -> REPITA bloco ATE ABRE_PAR expr FECHA_PAR PONTO_VIRGULA
retorne     -> RETORNE PONTO_VIRGULA | RETORNE expr PONTO_VIRGULA
mostre      -> MOSTRE ABRE_PAR args FECHA_PAR PONTO_VIRGULA
leia        -> LEIA ABRE_PAR ID FECHA_PAR PONTO_VIRGULA

# ---------------------------------------------------------------- expressões
# um não-terminal por nível de precedência (menor -> maior):
#   ou < e < nao < relacional (não associativo) < + - < * / % < - unário < ^ (direita)
expr        -> expr_ou
expr_ou     -> expr_ou OU expr_e | expr_e
expr_e      -> expr_e E expr_nao | expr_nao
expr_nao    -> NAO expr_nao | expr_rel
expr_rel    -> soma op_rel soma | soma
op_rel      -> IGUAL | DIFERENTE | MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL
soma        -> soma MAIS termo | soma MENOS termo | termo
termo       -> termo MULT unario | termo DIV unario | termo MOD unario | unario
unario      -> MENOS unario | potencia
potencia    -> primario POT unario | primario
primario    -> NUM_INT | NUM_REAL | TEXTO | VERDADEIRO | FALSO | ID | chamada
             | ABRE_PAR expr FECHA_PAR
chamada     -> ID ABRE_PAR args_opt FECHA_PAR
args_opt    -> args | ε
args        -> args VIRGULA expr | expr
```

**Números:** 85 produções (contando a produção 0 do aumento), 49 terminais, 36 não-terminais. O autômato LR(0) tem **160 estados (I0 a I159) e 582 transições**.

## Construção da tabela SLR(1)

1. **FIRST e FOLLOW**: o mesmo módulo `mare/first_follow.py` do LL(1) (aplicado à gramática aumentada).
2. **Coleção canônica de itens LR(0)** (`ColecaoLR0`): `I0 = closure({programa' → • programa})`, e
   `goto(I, X)` para cada símbolo `X`, até não surgirem estados novos.
3. **Tabela** (`TabelaSLR`), para cada estado `Ii`:
   * `A → α • a β` e `goto(Ii, a) = Ij` ⇒ `ACTION[i, a] = shift j`;
   * `A → α •` com `A ≠ programa'` ⇒ `ACTION[i, a] = reduce (A → α)` **para todo `a ∈ FOLLOW(A)`**;
   * `programa' → programa •` ⇒ `ACTION[i, $] = acc`;
   * `goto(Ii, A) = Ij` ⇒ `GOTO[i, A] = j`.

### Exemplo real: o estado onde o SLR decide pelo FOLLOW

Depois de ler um `soma` dentro de uma expressão relacional, o autômato chega ao estado:

```text
I61:
    expr_rel → soma • op_rel soma       ← pode ser o começo de "a < b"
    expr_rel → soma •                   ← ou a expressão acabou aqui
    soma → soma • MAIS termo
    soma → soma • MENOS termo
```

Há um item de redução (`expr_rel → soma •`) e vários de deslocamento. Isso **não é conflito** no SLR(1):
a redução só vale para os terminais de `FOLLOW(expr_rel)` — `OU`, `E`, `FECHA_PAR`, `PONTO_VIRGULA`,
`VIRGULA`, `ABRE_CHAVE`, `ATE`, `PASSO` —, enquanto o deslocamento vale para `IGUAL`, `MENOR`, ..., `MAIS`, `MENOS`.
Os dois conjuntos são **disjuntos**, então cada célula de `ACTION` recebe uma única ação.

### Conflitos

O programa detecta e imprime conflitos **shift/reduce** e **reduce/reduce**. Para a gramática da Maré
o resultado é: **zero conflitos** (`python main.py --tabela-slr`). Para ver um conflito de verdade, a
gramática ambígua `E → E MAIS E | id` produz um shift/reduce no estado `E → E MAIS E •`
com lookahead `MAIS` (reduzir = associar à esquerda; deslocar = associar à direita) — é o
mesmo problema que as regras de precedência da etapa (b) resolvem, e está coberto em
`tests/test_slr.py`.

## Verificação feita pelo programa

```bash
python main.py --gramatica-slr         # gramática aumentada e numerada
python main.py --itens-lr0             # coleção canônica: I0, I1, ... com o ponto •
python main.py --tabela-slr            # ACTION/GOTO e relatório de conflitos
python main.py exemplos/expressao.mare --slr    # rastro shift/reduce (Passo | Pilha | Entrada | Ação)
```
