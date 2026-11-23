# Rastreamento de exemplos: código → tokens → reconhecimento

# Parte 1 — Parser descendente recursivo

## 1. Caso aceito — `exemplos/mini.mare`

```text
principal {
    seja x: inteiro = 2 + 3 * 4;
    se (x > 10 e nao falso) {
        mostre(x);
    }
}
```

**Cadeia de tokens** (`python main.py exemplos/mini.mare --cadeia`):

```text
1 | <PRINCIPAL> <ABRE_CHAVE>
2 | <SEJA> <ID, x> <DOIS_PONTOS> <T_INTEIRO> <ATRIB> <NUM_INT, 2> <MAIS> <NUM_INT, 3> <MULT> <NUM_INT, 4> <PONTO_VIRGULA>
3 | <SE> <ABRE_PAR> <ID, x> <MAIOR> <NUM_INT, 10> <E> <NAO> <FALSO> <FECHA_PAR> <ABRE_CHAVE>
4 | <MOSTRE> <ABRE_PAR> <ID, x> <FECHA_PAR> <PONTO_VIRGULA>
5 | <FECHA_CHAVE>
6 | <FECHA_CHAVE>
7 | <EOF>
```

**Reconhecimento** (resumo do `--rastro`):

1. `programa` vê `PRINCIPAL` → consome e chama `bloco`, que consome `{`.
2. `comando` vê `SEJA` → regra `declaracao`: consome `seja`, `ID x`, `:`, tipo `inteiro`, `=`.
3. `expr` desce até `soma`: `termo` reconhece `2`; vê `+` → consome; novo `termo` reconhece
   `3`, vê `*` → consome, reconhece `4`. Por isso `3 * 4` vira filho direito do `+`.
4. `esperar(PONTO_VIRGULA)` → ok. Declaração concluída.
5. `comando` vê `SE` → consome `se`, `(`; `expr` reconhece `x > 10 e nao falso`
   (`e` fica acima de `>` e de `nao`, pois tem menor precedência); `esperar(FECHA_PAR)` ok; `bloco`.
6. Dois `}` fecham os blocos do `se` e do `principal`; `EOF` → aceito.

**Derivação mais à esquerda** da expressão (com ⇒* para cadeias unitárias):

```text
expr ⇒* soma ⇒ termo + termo ⇒* 2 + termo ⇒ 2 + unario * unario ⇒* 2 + 3 * unario ⇒* 2 + 3 * 4
```

Árvore: `python main.py exemplos/mini.mare --arvore` (ou a figura `artigo/arvore_mini.png`).

## 2. Caso rejeitado — `exemplos/rejeitado.mare`

Mesmo programa, mas **sem o `)`** na linha 4: `se (x > 10 e nao falso {`

Tokens da linha 4: `<SE> <ABRE_PAR> <ID,x> <MAIOR> <NUM_INT,10> <E> <NAO> <FALSO> <ABRE_CHAVE>`
— todos válidos, então **não é erro léxico**.

`python main.py exemplos/rejeitado.mare --rastro` (trecho):

```text
▶ se   [próximo token: <SE, 'se'>]
│ ✓ consome <SE, 'se'>  (4:5)
│ ✓ consome <ABRE_PAR, '('>  (4:8)
│ ▶ expr   [próximo token: <ID, 'x'>]
│ │ ... reconhece x > 10 e nao falso ...
│ │ ✓ consome <FALSO, 'falso'>  (4:22)
✗ ERRO [4:28] esperado ')' para fechar a condição do 'se', mas foi encontrado '{'
  → recuperação (modo pânico)
✗ descarta <ABRE_CHAVE, '{'> ... ✗ descarta <FECHA_CHAVE, '}'>
✓ consome <FECHA_CHAVE, '}'>  (7:1)
```

**Por que foi rejeitado:** a produção é `se = "se" "(" expr ")" bloco`. Depois que
`expr` reconhece `x > 10 e nao falso`, o próximo token é `{`. Nenhuma regra de
expressão continua com `{` (não é operador), então `expr` retorna; a produção de `se`
exige `)` nessa posição → `esperar(FECHA_PAR)` falha → erro na coluna 28.

**Recuperação:** o parser descarta o bloco `{ ... }` inteiro (contando chaves) para que
o `}` dele não feche o `principal`. O `}` da linha 7 fecha o `principal` normalmente:
**1 erro, sem cascata**.

---

# Parte 2 — Analisadores de tabela: LL(1) e SLR(1)

Os dois novos parsers consomem **a mesma cadeia de tokens** do analisador léxico
(`Lexer` → lista de `Token` → parser), mas decidem tudo por uma tabela:

```text
código .mare ──► Lexer ──► [Token] ──┬─► parser recursivo (parser.py)   ─► árvore
                                     ├─► LL(1)  (ll1.py)  tabela M[A,a] + pilha ─► aceito / erro
                                     └─► SLR(1) (slr.py)  ACTION/GOTO + pilha   ─► aceito / erro
```

O exemplo usado nas demonstrações é `exemplos/expressao.mare` (propositalmente curto):

```text
principal {
    x = a + b * c;
}
```

Tokens: `PRINCIPAL ABRE_CHAVE ID ATRIB ID MAIS ID MULT ID PONTO_VIRGULA FECHA_CHAVE` (+ `$`).

## 3. LL(1) — expansão de não-terminais com pilha

`python main.py exemplos/expressao.mare --ll1`

A pilha começa com `$ programa` (topo à **direita**). A cada passo:

* topo **terminal** → compara com o token atual: igual ⇒ `match` (desempilha e avança); diferente ⇒ erro;
* topo **não-terminal** `A` → consulta `M[A, token]`: desempilha `A` e empilha o lado direito da produção
  **de trás para frente** (o 1º símbolo fica no topo); célula vazia ⇒ erro;
* `$` no topo e `$` na entrada ⇒ **aceita**.

```text
==============================================================================
+-------+------------------------------------+----------------------------------+-----------------------------------------+
| Passo | Pilha                              | Entrada                          | Ação                                    |
+-------+------------------------------------+----------------------------------+-----------------------------------------+
| 1     | $ programa                         | PRINCIPAL ABRE_CHAVE ID ATRIB …  | programa → itens PRINCIPAL bloco        |
| 2     | $ bloco PRINCIPAL itens            | PRINCIPAL ABRE_CHAVE ID ATRIB …  | itens → ε                               |
| 3     | $ bloco PRINCIPAL                  | PRINCIPAL ABRE_CHAVE ID ATRIB …  | match PRINCIPAL                         |
| 4     | $ bloco                            | ABRE_CHAVE ID ATRIB ID MAIS ID … | bloco → ABRE_CHAVE comandos FECHA_CHAVE |
| 5     | $ FECHA_CHAVE comandos ABRE_CHAVE  | ABRE_CHAVE ID ATRIB ID MAIS ID … | match ABRE_CHAVE                        |
| 6     | $ FECHA_CHAVE comandos             | ID ATRIB ID MAIS ID MULT ID …    | comandos → comando comandos             |
| 7     | $ FECHA_CHAVE comandos comando     | ID ATRIB ID MAIS ID MULT ID …    | comando → cmd_id                        |
| 8     | $ FECHA_CHAVE comandos cmd_id      | ID ATRIB ID MAIS ID MULT ID …    | cmd_id → ID resto_id                    |
| 9     | $ FECHA_CHAVE comandos resto_id ID | ID ATRIB ID MAIS ID MULT ID …    | match ID                                |
| 10    | $ FECHA_CHAVE comandos resto_id    | ATRIB ID MAIS ID MULT ID …       | resto_id → ATRIB expr PONTO_VIRGULA     |
| 11    | … PONTO_VIRGULA expr ATRIB         | ATRIB ID MAIS ID MULT ID …       | match ATRIB                             |
| 12    | … comandos PONTO_VIRGULA expr      | ID MAIS ID MULT ID …             | expr → expr_ou                          |
| 13    | … comandos PONTO_VIRGULA expr_ou   | ID MAIS ID MULT ID …             | expr_ou → expr_e expr_ou'               |
| 14    | … PONTO_VIRGULA expr_ou' expr_e    | ID MAIS ID MULT ID …             | expr_e → expr_nao expr_e'               |
| 15    | … expr_ou' expr_e' expr_nao        | ID MAIS ID MULT ID …             | expr_nao → expr_rel                     |
| 16    | … expr_ou' expr_e' expr_rel        | ID MAIS ID MULT ID …             | expr_rel → soma rel_opc                 |
| 17    | … expr_ou' expr_e' rel_opc soma    | ID MAIS ID MULT ID …             | soma → termo soma'                      |
| 18    | … expr_e' rel_opc soma' termo      | ID MAIS ID MULT ID …             | termo → unario termo'                   |
| 19    | … rel_opc soma' termo' unario      | ID MAIS ID MULT ID …             | unario → potencia                       |
| 20    | … rel_opc soma' termo' potencia    | ID MAIS ID MULT ID …             | potencia → primario pot_opc             |
| 21    | … soma' termo' pot_opc primario    | ID MAIS ID MULT ID …             | primario → ID sufixo_id                 |
| 22    | … termo' pot_opc sufixo_id ID      | ID MAIS ID MULT ID …             | match ID                                |
| 23    | … soma' termo' pot_opc sufixo_id   | MAIS ID MULT ID PONTO_VIRGULA …  | sufixo_id → ε                           |
| 24    | … rel_opc soma' termo' pot_opc     | MAIS ID MULT ID PONTO_VIRGULA …  | pot_opc → ε                             |
| 25    | … expr_e' rel_opc soma' termo'     | MAIS ID MULT ID PONTO_VIRGULA …  | termo' → ε                              |
| 26    | … expr_ou' expr_e' rel_opc soma'   | MAIS ID MULT ID PONTO_VIRGULA …  | soma' → MAIS termo soma'                |
| 27    | … rel_opc soma' termo MAIS         | MAIS ID MULT ID PONTO_VIRGULA …  | match MAIS                              |
| 28    | … expr_e' rel_opc soma' termo      | ID MULT ID PONTO_VIRGULA …       | termo → unario termo'                   |
| 29    | … rel_opc soma' termo' unario      | ID MULT ID PONTO_VIRGULA …       | unario → potencia                       |
| 30    | … rel_opc soma' termo' potencia    | ID MULT ID PONTO_VIRGULA …       | potencia → primario pot_opc             |
| 31    | … soma' termo' pot_opc primario    | ID MULT ID PONTO_VIRGULA …       | primario → ID sufixo_id                 |
| 32    | … termo' pot_opc sufixo_id ID      | ID MULT ID PONTO_VIRGULA …       | match ID                                |
| 33    | … soma' termo' pot_opc sufixo_id   | MULT ID PONTO_VIRGULA …          | sufixo_id → ε                           |
| 34    | … rel_opc soma' termo' pot_opc     | MULT ID PONTO_VIRGULA …          | pot_opc → ε                             |
| 35    | … expr_e' rel_opc soma' termo'     | MULT ID PONTO_VIRGULA …          | termo' → MULT unario termo'             |
| 36    | … soma' termo' unario MULT         | MULT ID PONTO_VIRGULA …          | match MULT                              |
| 37    | … rel_opc soma' termo' unario      | ID PONTO_VIRGULA FECHA_CHAVE $   | unario → potencia                       |
| 38    | … rel_opc soma' termo' potencia    | ID PONTO_VIRGULA FECHA_CHAVE $   | potencia → primario pot_opc             |
| 39    | … soma' termo' pot_opc primario    | ID PONTO_VIRGULA FECHA_CHAVE $   | primario → ID sufixo_id                 |
| 40    | … termo' pot_opc sufixo_id ID      | ID PONTO_VIRGULA FECHA_CHAVE $   | match ID                                |
| 41    | … soma' termo' pot_opc sufixo_id   | PONTO_VIRGULA FECHA_CHAVE $      | sufixo_id → ε                           |
| 42    | … rel_opc soma' termo' pot_opc     | PONTO_VIRGULA FECHA_CHAVE $      | pot_opc → ε                             |
| 43    | … expr_e' rel_opc soma' termo'     | PONTO_VIRGULA FECHA_CHAVE $      | termo' → ε                              |
| 44    | … expr_ou' expr_e' rel_opc soma'   | PONTO_VIRGULA FECHA_CHAVE $      | soma' → ε                               |
| 45    | … expr_ou' expr_e' rel_opc         | PONTO_VIRGULA FECHA_CHAVE $      | rel_opc → ε                             |
| 46    | … PONTO_VIRGULA expr_ou' expr_e'   | PONTO_VIRGULA FECHA_CHAVE $      | expr_e' → ε                             |
| 47    | … comandos PONTO_VIRGULA expr_ou'  | PONTO_VIRGULA FECHA_CHAVE $      | expr_ou' → ε                            |
| 48    | … comandos PONTO_VIRGULA           | PONTO_VIRGULA FECHA_CHAVE $      | match PONTO_VIRGULA                     |
| 49    | $ FECHA_CHAVE comandos             | FECHA_CHAVE $                    | comandos → ε                            |
| 50    | $ FECHA_CHAVE                      | FECHA_CHAVE $                    | match FECHA_CHAVE                       |
| 51    | $                                  | $                                | aceita                                  |
+-------+------------------------------------+----------------------------------+-----------------------------------------+
```

Pontos para comentar:

* **Passo 8–10:** `x = ...` e `f(...)` têm o mesmo começo (`ID`). A gramática foi fatorada
  (`cmd_id → ID resto_id`), então o parser consome o `ID` e só **depois** olha o `ATRIB` para escolher `resto_id`.
* **Precedência:** `b * c` é expandido dentro de `soma'`/`termo'` — `termo' → MULT unario termo'` aparece **antes**
  de `soma'` terminar. A multiplicação está "mais funda" na derivação.
* **ε-produções:** `sufixo_id → ε`, `pot_opc → ε`, `rel_opc → ε`... só são escolhidas porque o token atual está no
  **FOLLOW** do não-terminal (é por isso que o FOLLOW entra na tabela).

## 4. SLR(1) — shift/reduce com pilha de estados

`python main.py exemplos/expressao.mare --slr`

A pilha guarda `estado símbolo estado símbolo ...` (topo à direita). Em cada passo consulta-se
`ACTION[estado do topo, token]`:

* `shift j` → empilha o token e o estado `j`, avança;
* `reduce n` (produção `A → β`) → desempilha `|β|` pares (símbolo, estado), olha o novo estado `t` e empilha
  `A` e `GOTO[t, A]`;
* `acc` → aceita; célula vazia → erro.

```text
==============================================================================
+-------+-----------------------------------+----------------------------------+-------------------------------------------------+
| Passo | Pilha                             | Entrada                          | Ação                                            |
+-------+-----------------------------------+----------------------------------+-------------------------------------------------+
| 1     | 0                                 | PRINCIPAL ABRE_CHAVE ID ATRIB …  | reduce 3: itens → ε                             |
| 2     | 0 itens 2                         | PRINCIPAL ABRE_CHAVE ID ATRIB …  | shift 6                                         |
| 3     | 0 itens 2 PRINCIPAL 6             | ABRE_CHAVE ID ATRIB ID MAIS ID … | shift 11                                        |
| 4     | … 2 PRINCIPAL 6 ABRE_CHAVE 11     | ID ATRIB ID MAIS ID MULT ID …    | reduce 20: comandos → ε                         |
| 5     | … 6 ABRE_CHAVE 11 comandos 15     | ID ATRIB ID MAIS ID MULT ID …    | shift 30                                        |
| 6     | … ABRE_CHAVE 11 comandos 15 ID 30 | ATRIB ID MAIS ID MULT ID …       | shift 51                                        |
| 7     | … 11 comandos 15 ID 30 ATRIB 51   | ID MAIS ID MULT ID …             | shift 67                                        |
| 8     | … 15 ID 30 ATRIB 51 ID 67         | MAIS ID MULT ID PONTO_VIRGULA …  | reduce 77: primario → ID                        |
| 9     | … 15 ID 30 ATRIB 51 primario 65   | MAIS ID MULT ID PONTO_VIRGULA …  | reduce 71: potencia → primario                  |
| 10    | … 15 ID 30 ATRIB 51 potencia 64   | MAIS ID MULT ID PONTO_VIRGULA …  | reduce 69: unario → potencia                    |
| 11    | … 15 ID 30 ATRIB 51 unario 63     | MAIS ID MULT ID PONTO_VIRGULA …  | reduce 67: termo → unario                       |
| 12    | … 15 ID 30 ATRIB 51 termo 62      | MAIS ID MULT ID PONTO_VIRGULA …  | reduce 63: soma → termo                         |
| 13    | … 15 ID 30 ATRIB 51 soma 61       | MAIS ID MULT ID PONTO_VIRGULA …  | shift 103                                       |
| 14    | … ID 30 ATRIB 51 soma 61 MAIS 103 | ID MULT ID PONTO_VIRGULA …       | shift 67                                        |
| 15    | … ATRIB 51 soma 61 MAIS 103 ID 67 | MULT ID PONTO_VIRGULA …          | reduce 77: primario → ID                        |
| 16    | … 51 soma 61 MAIS 103 primario 65 | MULT ID PONTO_VIRGULA …          | reduce 71: potencia → primario                  |
| 17    | … 51 soma 61 MAIS 103 potencia 64 | MULT ID PONTO_VIRGULA …          | reduce 69: unario → potencia                    |
| 18    | … 51 soma 61 MAIS 103 unario 63   | MULT ID PONTO_VIRGULA …          | reduce 67: termo → unario                       |
| 19    | … 51 soma 61 MAIS 103 termo 130   | MULT ID PONTO_VIRGULA …          | shift 105                                       |
| 20    | … 61 MAIS 103 termo 130 MULT 105  | ID PONTO_VIRGULA FECHA_CHAVE $   | shift 67                                        |
| 21    | … 103 termo 130 MULT 105 ID 67    | PONTO_VIRGULA FECHA_CHAVE $      | reduce 77: primario → ID                        |
| 22    | … termo 130 MULT 105 primario 65  | PONTO_VIRGULA FECHA_CHAVE $      | reduce 71: potencia → primario                  |
| 23    | … termo 130 MULT 105 potencia 64  | PONTO_VIRGULA FECHA_CHAVE $      | reduce 69: unario → potencia                    |
| 24    | … termo 130 MULT 105 unario 132   | PONTO_VIRGULA FECHA_CHAVE $      | reduce 64: termo → termo MULT unario            |
| 25    | … 51 soma 61 MAIS 103 termo 130   | PONTO_VIRGULA FECHA_CHAVE $      | reduce 61: soma → soma MAIS termo               |
| 26    | … 15 ID 30 ATRIB 51 soma 61       | PONTO_VIRGULA FECHA_CHAVE $      | reduce 54: expr_rel → soma                      |
| 27    | … 15 ID 30 ATRIB 51 expr_rel 60   | PONTO_VIRGULA FECHA_CHAVE $      | reduce 52: expr_nao → expr_rel                  |
| 28    | … 15 ID 30 ATRIB 51 expr_nao 59   | PONTO_VIRGULA FECHA_CHAVE $      | reduce 50: expr_e → expr_nao                    |
| 29    | … 15 ID 30 ATRIB 51 expr_e 58     | PONTO_VIRGULA FECHA_CHAVE $      | reduce 48: expr_ou → expr_e                     |
| 30    | … 15 ID 30 ATRIB 51 expr_ou 57    | PONTO_VIRGULA FECHA_CHAVE $      | reduce 46: expr → expr_ou                       |
| 31    | … 15 ID 30 ATRIB 51 expr 88       | PONTO_VIRGULA FECHA_CHAVE $      | shift 122                                       |
| 32    | … 51 expr 88 PONTO_VIRGULA 122    | FECHA_CHAVE $                    | reduce 34: atribuicao → ID ATRIB expr           |
|       |                                   |                                  | PONTO_VIRGULA                                   |
| 33    | … 11 comandos 15 atribuicao 21    | FECHA_CHAVE $                    | reduce 22: comando → atribuicao                 |
| 34    | … 11 comandos 15 comando 19       | FECHA_CHAVE $                    | reduce 19: comandos → comandos comando          |
| 35    | … 6 ABRE_CHAVE 11 comandos 15     | FECHA_CHAVE $                    | shift 31                                        |
| 36    | … 11 comandos 15 FECHA_CHAVE 31   | $                                | reduce 18: bloco → ABRE_CHAVE comandos          |
|       |                                   |                                  | FECHA_CHAVE                                     |
| 37    | 0 itens 2 PRINCIPAL 6 bloco 10    | $                                | reduce 1: programa → itens PRINCIPAL bloco      |
| 38    | 0 programa 1                      | $                                | aceita                                          |
+-------+-----------------------------------+----------------------------------+-------------------------------------------------+
```

Pontos para comentar:

* **Passo 13 (`shift 103`) × passo 25 (`reduce 61`):** com `soma` no topo e `MAIS` na entrada, o parser **desloca**
  (ainda há operando a ler). Depois de ler `b * c` (passo 24), o `MULT` já foi reduzido, então `soma → soma MAIS termo` é
  reduzida. O `*` ganha do `+` porque, com `termo` no topo e `MULT` na entrada (passo 19), a tabela manda **deslocar**,
  não reduzir `soma`.
* **Passo 1:** `reduce 3: itens → ε` — as ε-produções também são reduções (com `|β| = 0`, nada é desempilhado).
* O rastro lê a derivação **de baixo para cima**: as reduções, de trás para frente, dão a **derivação mais à direita**.

## 5. Caso rejeitado nos três parsers

`exemplos/expressao_erro.mare` (`x = a + * c;`) — falta o operando depois do `+`:

| Parser | Mensagem |
|---|---|
| recursivo | `[3:13] esperada uma expressão (número, texto, variável, chamada ou '('), mas foi encontrado '*'` |
| LL(1) | `[3:13] esperado identificador, '(', '-', número inteiro, ..., mas foi encontrado '*'` |
| SLR(1) | `[3:13] esperado identificador, '(', '-', número inteiro, ..., mas foi encontrado '*'` |

Os três param **no mesmo token** (linha 3, coluna 13). No LL(1), o erro aparece como `M[termo, MULT] vazia`; o modo pânico
descarta `* c` (tokens fora de FOLLOW(termo)) e a análise continua até o fim, reportando um único erro.

---

# Parte 3 — Roteiro da apresentação (15 minutos)

| Tempo | Assunto | Comando / o que mostrar |
|---|---|---|
| 0:00–2:00 | **Léxico**: linguagem Maré e cadeia de tokens | `python main.py exemplos/expressao.mare --cadeia` |
| 2:00–4:30 | **Gramática e transformações**: ambígua → precedência → sem recursão à esquerda → fatorada; prova da ambiguidade (`a + b * c`) | `docs/gramatica_ll1.md`; `python main.py --gramatica-ll1` |
| 4:30–6:00 | **FIRST/FOLLOW** por ponto fixo (mostrar `E/T/F` do Dragão no teste e o da Maré) | `python main.py --first-follow` |
| 6:00–7:30 | **Tabela LL(1)** `M[A,a]`: como cada produção entra; **zero conflitos** | `python main.py --tabela-ll1` |
| 7:30–9:30 | **Pilha LL(1)** ao vivo (51 passos) e um erro | `python main.py exemplos/expressao.mare --ll1`; `python main.py exemplos/expressao_erro.mare --ll1` |
| 9:30–11:00 | **Itens LR(0)**: `closure`, `goto`, estados I0…I159 (mostrar I0 e I61) | `python main.py --itens-lr0` |
| 11:00–12:30 | **Tabela SLR(1)** ACTION/GOTO; redução por FOLLOW; **zero conflitos** | `python main.py --tabela-slr` |
| 12:30–14:00 | **Shift/reduce** ao vivo (38 passos) | `python main.py exemplos/expressao.mare --slr` |
| 14:00–15:00 | **Comparação** LL(1) × SLR(1) + conversor automático | `python main.py --converter gramaticas/ambigua_expr.txt`; `python -m unittest discover -s tests` |

**Dicas:** o rastro curto (`expressao.mare`) cabe em uma tela; para tabelas completas use
`--saida arquivo.md|.csv|.txt` (o terminal mostra uma versão abreviada). Todos os arquivos pré-gerados estão em
[`docs/saidas/`](saidas/).
