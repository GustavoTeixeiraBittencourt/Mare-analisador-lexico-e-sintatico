# Rastreamento de exemplos: código → tokens → reconhecimento

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
