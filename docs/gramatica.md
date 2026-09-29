# Especificação da linguagem Maré

## 1. Gramática livre de contexto (EBNF)

Notação: `{ x }` = zero ou mais repetições, `[ x ]` = opcional, `|` = alternativa,
terminais entre aspas ou em MAIÚSCULAS (tokens do léxico).

```ebnf
(* ---------- estrutura ---------- *)
programa    = { funcao | declaracao } "principal" bloco EOF ;
funcao      = "funcao" ID "(" [ parametros ] ")" [ "->" tipo ] bloco ;
parametros  = parametro { "," parametro } ;
parametro   = ID ":" tipo ;
tipo        = "inteiro" | "real" | "logico" | "texto" ;
bloco       = "{" { comando } "}" ;

(* ---------- comandos ---------- *)
comando     = declaracao | atribuicao | chamada ";" | se | enquanto
            | para | repita | retorne | mostre | leia ;
declaracao  = "seja" ID ":" tipo [ "=" expr ] ";"
            | "fixo" ID ":" tipo "=" expr ";" ;
atribuicao  = ID "=" expr ";" ;
se          = "se" "(" expr ")" bloco [ "senao" ( se | bloco ) ] ;
enquanto    = "enquanto" "(" expr ")" bloco ;
para        = "para" ID "de" expr "ate" expr [ "passo" expr ] bloco ;
repita      = "repita" bloco "ate" "(" expr ")" ";" ;
retorne     = "retorne" [ expr ] ";" ;
mostre      = "mostre" "(" argumentos ")" ";" ;
leia        = "leia" "(" ID ")" ";" ;

(* ---------- expressões: da MENOR para a MAIOR precedência ---------- *)
expr        = ou ;
ou          = e { "ou" e } ;
e           = nao { "e" nao } ;
nao         = "nao" nao | relacional ;
relacional  = soma [ ( "==" | "!=" | "<" | "<=" | ">" | ">=" ) soma ] ;
soma        = termo { ( "+" | "-" ) termo } ;
termo       = unario { ( "*" | "/" | "%" ) unario } ;
unario      = "-" unario | potencia ;
potencia    = primario [ "^" unario ] ;
primario    = NUM_INT | NUM_REAL | TEXTO | "verdadeiro" | "falso"
            | ID | chamada | "(" expr ")" ;
chamada     = ID "(" [ argumentos ] ")" ;
argumentos  = expr { "," expr } ;
```

### Precedência e associatividade

| Nível | Operadores | Associatividade |
|---|---|---|
| 1 (menor) | `ou` | esquerda |
| 2 | `e` | esquerda |
| 3 | `nao` | prefixo (unário) |
| 4 | `== != < <= > >=` | não associativo (`a < b < c` é erro) |
| 5 | `+ -` | esquerda |
| 6 | `* / %` | esquerda |
| 7 | `-` (unário) | prefixo |
| 8 (maior) | `^` | direita (`2^3^2 = 2^9`) |

### Por que a gramática é LL(1) (com um detalhe LL(2))

* Cada comando começa com uma palavra reservada diferente (`seja`, `se`, `enquanto`...),
  então um token de *lookahead* basta para escolher a regra.
* A única exceção são os comandos que começam com `ID`: `x = ...` (atribuição) e
  `f(...)` (chamada). O parser olha **um token a mais** (`=` ou `(`) para decidir.
* Não há recursão à esquerda: as repetições `{ ... }` viram laços `while` no código,
  e a associatividade à esquerda é obtida montando a árvore dentro do laço.
* O "senão pendurado" (*dangling else*) não existe, porque os blocos exigem `{ }`.

## 2. Classes de lexemas, tokens e expressões regulares

| Classe | Token(s) | Lexemas | Expressão regular |
|---|---|---|---|
| Palavra reservada | `PRINCIPAL FUNCAO SEJA FIXO SE SENAO ENQUANTO PARA DE ATE PASSO REPITA RETORNE MOSTRE LEIA` | `principal`, `funcao`, `seja`, ... | casa `ID` e é reclassificada pela tabela de palavras reservadas |
| Tipo primitivo | `T_INTEIRO T_REAL T_LOGICO T_TEXTO` | `inteiro real logico texto` | idem |
| Identificador | `ID` | `nota1`, `eh_par`, `MEDIA_MINIMA` | `[A-Za-z_][A-Za-z0-9_]*` |
| Literal inteiro | `NUM_INT` | `0`, `42` | `\d+` |
| Literal real | `NUM_REAL` | `3.14`, `7.0` | `\d+\.\d+` |
| Literal texto | `TEXTO` | `"Ana"`, `"a \"b\""` | `"(?:\\.\|[^"\\\n])*"` |
| Literal lógico | `VERDADEIRO FALSO` | `verdadeiro falso` | palavra reservada |
| Operador aritmético | `MAIS MENOS MULT DIV MOD POT` | `+ - * / % ^` | `[+\-*/%^]` |
| Operador relacional | `IGUAL DIFERENTE MENOR MENOR_IGUAL MAIOR MAIOR_IGUAL` | `== != < <= > >=` | `==\|!=\|<=\|>=\|<\|>` |
| Operador lógico | `E OU NAO` | `e ou nao` | palavra reservada |
| Atribuição | `ATRIB` | `=` | `=` |
| Delimitador | `ABRE_PAR FECHA_PAR ABRE_CHAVE FECHA_CHAVE PONTO_VIRGULA VIRGULA DOIS_PONTOS SETA` | `( ) { } ; , : ->` | `[(){};,:]\|->` |
| (ignorado) | — | espaços, quebras de linha | `[ \t\r]+`, `\n` |
| (ignorado) | — | comentários | `\#[^\n]*` e `\#\*[\s\S]*?\*\#` |

### Erros léxicos detectados

| Situação | Regex de captura | Exemplo |
|---|---|---|
| Número seguido de letras | `\d+(?:\.\d+)?[A-Za-z_]\w*` | `12abc` |
| Real sem parte decimal | `\d+\.(?!\d)` | `3.` |
| Texto sem aspas de fechamento | `"(?:\\.\|[^"\\\n])*` | `"sem fim` |
| Comentário de bloco sem `*#` | `\#\*` | `#* ...` |
| Caractere fora do alfabeto | `.` | `@`, `$`, `ç` |
