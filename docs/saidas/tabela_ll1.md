# Produções (numeradas)

  0. programa → itens PRINCIPAL bloco
  1. itens → item itens
  2. itens → ε
  3. item → funcao
  4. item → declaracao
  5. funcao → FUNCAO ID ABRE_PAR params_opt FECHA_PAR retorno_opt bloco
  6. params_opt → params
  7. params_opt → ε
  8. params → param params'
  9. params' → VIRGULA param params'
 10. params' → ε
 11. param → ID DOIS_PONTOS tipo
 12. retorno_opt → SETA tipo
 13. retorno_opt → ε
 14. tipo → T_INTEIRO
 15. tipo → T_REAL
 16. tipo → T_LOGICO
 17. tipo → T_TEXTO
 18. bloco → ABRE_CHAVE comandos FECHA_CHAVE
 19. comandos → comando comandos
 20. comandos → ε
 21. comando → declaracao
 22. comando → cmd_id
 23. comando → se
 24. comando → enquanto
 25. comando → para
 26. comando → repita
 27. comando → retorne
 28. comando → mostre
 29. comando → leia
 30. declaracao → SEJA ID DOIS_PONTOS tipo init_opt PONTO_VIRGULA
 31. declaracao → FIXO ID DOIS_PONTOS tipo ATRIB expr PONTO_VIRGULA
 32. init_opt → ATRIB expr
 33. init_opt → ε
 34. cmd_id → ID resto_id
 35. resto_id → ATRIB expr PONTO_VIRGULA
 36. resto_id → ABRE_PAR args_opt FECHA_PAR PONTO_VIRGULA
 37. se → SE ABRE_PAR expr FECHA_PAR bloco senao_opt
 38. senao_opt → SENAO senao_corpo
 39. senao_opt → ε
 40. senao_corpo → se
 41. senao_corpo → bloco
 42. enquanto → ENQUANTO ABRE_PAR expr FECHA_PAR bloco
 43. para → PARA ID DE expr ATE expr passo_opt bloco
 44. passo_opt → PASSO expr
 45. passo_opt → ε
 46. repita → REPITA bloco ATE ABRE_PAR expr FECHA_PAR PONTO_VIRGULA
 47. retorne → RETORNE retorno_expr PONTO_VIRGULA
 48. retorno_expr → expr
 49. retorno_expr → ε
 50. mostre → MOSTRE ABRE_PAR args FECHA_PAR PONTO_VIRGULA
 51. leia → LEIA ABRE_PAR ID FECHA_PAR PONTO_VIRGULA
 52. expr → expr_ou
 53. expr_ou → expr_e expr_ou'
 54. expr_ou' → OU expr_e expr_ou'
 55. expr_ou' → ε
 56. expr_e → expr_nao expr_e'
 57. expr_e' → E expr_nao expr_e'
 58. expr_e' → ε
 59. expr_nao → NAO expr_nao
 60. expr_nao → expr_rel
 61. expr_rel → soma rel_opc
 62. rel_opc → op_rel soma
 63. rel_opc → ε
 64. op_rel → IGUAL
 65. op_rel → DIFERENTE
 66. op_rel → MENOR
 67. op_rel → MENOR_IGUAL
 68. op_rel → MAIOR
 69. op_rel → MAIOR_IGUAL
 70. soma → termo soma'
 71. soma' → MAIS termo soma'
 72. soma' → MENOS termo soma'
 73. soma' → ε
 74. termo → unario termo'
 75. termo' → MULT unario termo'
 76. termo' → DIV unario termo'
 77. termo' → MOD unario termo'
 78. termo' → ε
 79. unario → MENOS unario
 80. unario → potencia
 81. potencia → primario pot_opc
 82. pot_opc → POT unario
 83. pot_opc → ε
 84. primario → NUM_INT
 85. primario → NUM_REAL
 86. primario → TEXTO
 87. primario → VERDADEIRO
 88. primario → FALSO
 89. primario → ID sufixo_id
 90. primario → ABRE_PAR expr FECHA_PAR
 91. sufixo_id → ABRE_PAR args_opt FECHA_PAR
 92. sufixo_id → ε
 93. args_opt → args
 94. args_opt → ε
 95. args → expr args'
 96. args' → VIRGULA expr args'
 97. args' → ε

# Tabela LL(1): célula = número da produção

|  | PRINCIPAL | FUNCAO | ID | ABRE_PAR | FECHA_PAR | VIRGULA | DOIS_PONTOS | SETA | T_INTEIRO | T_REAL | T_LOGICO | T_TEXTO | ABRE_CHAVE | FECHA_CHAVE | SEJA | PONTO_VIRGULA | FIXO | ATRIB | SE | SENAO | ENQUANTO | PARA | DE | ATE | PASSO | REPITA | RETORNE | MOSTRE | LEIA | OU | E | NAO | IGUAL | DIFERENTE | MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL | MAIS | MENOS | MULT | DIV | MOD | POT | NUM_INT | NUM_REAL | TEXTO | VERDADEIRO | FALSO | $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| programa | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | 0 |  | 0 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| itens | 2 | 1 |  |  |  |  |  |  |  |  |  |  |  |  | 1 |  | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| item |  | 3 |  |  |  |  |  |  |  |  |  |  |  |  | 4 |  | 4 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| funcao |  | 5 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| params_opt |  |  | 6 |  | 7 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| params |  |  | 8 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| params' |  |  |  |  | 10 | 9 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| param |  |  | 11 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| retorno_opt |  |  |  |  |  |  |  | 12 |  |  |  |  | 13 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| tipo |  |  |  |  |  |  |  |  | 14 | 15 | 16 | 17 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| bloco |  |  |  |  |  |  |  |  |  |  |  |  | 18 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| comandos |  |  | 19 |  |  |  |  |  |  |  |  |  |  | 20 | 19 |  | 19 |  | 19 |  | 19 | 19 |  |  |  | 19 | 19 | 19 | 19 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| comando |  |  | 22 |  |  |  |  |  |  |  |  |  |  |  | 21 |  | 21 |  | 23 |  | 24 | 25 |  |  |  | 26 | 27 | 28 | 29 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| declaracao |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 30 |  | 31 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| init_opt |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 33 |  | 32 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| cmd_id |  |  | 34 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| resto_id |  |  |  | 36 |  |  |  |  |  |  |  |  |  |  |  |  |  | 35 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| se |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 37 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| senao_opt |  |  | 39 |  |  |  |  |  |  |  |  |  |  | 39 | 39 |  | 39 |  | 39 | 38 | 39 | 39 |  |  |  | 39 | 39 | 39 | 39 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| senao_corpo |  |  |  |  |  |  |  |  |  |  |  |  | 41 |  |  |  |  |  | 40 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| enquanto |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 42 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| para |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 43 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| passo_opt |  |  |  |  |  |  |  |  |  |  |  |  | 45 |  |  |  |  |  |  |  |  |  |  |  | 44 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| repita |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 46 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| retorne |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 47 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| retorno_expr |  |  | 48 | 48 |  |  |  |  |  |  |  |  |  |  |  | 49 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 48 |  |  |  |  |  |  |  | 48 |  |  |  |  | 48 | 48 | 48 | 48 | 48 |  |
| mostre |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 50 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| leia |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 51 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| expr |  |  | 52 | 52 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 52 |  |  |  |  |  |  |  | 52 |  |  |  |  | 52 | 52 | 52 | 52 | 52 |  |
| expr_ou |  |  | 53 | 53 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 53 |  |  |  |  |  |  |  | 53 |  |  |  |  | 53 | 53 | 53 | 53 | 53 |  |
| expr_ou' |  |  |  |  | 55 | 55 |  |  |  |  |  |  | 55 |  |  | 55 |  |  |  |  |  |  |  | 55 | 55 |  |  |  |  | 54 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| expr_e |  |  | 56 | 56 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 56 |  |  |  |  |  |  |  | 56 |  |  |  |  | 56 | 56 | 56 | 56 | 56 |  |
| expr_e' |  |  |  |  | 58 | 58 |  |  |  |  |  |  | 58 |  |  | 58 |  |  |  |  |  |  |  | 58 | 58 |  |  |  |  | 58 | 57 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| expr_nao |  |  | 60 | 60 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 59 |  |  |  |  |  |  |  | 60 |  |  |  |  | 60 | 60 | 60 | 60 | 60 |  |
| expr_rel |  |  | 61 | 61 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 61 |  |  |  |  | 61 | 61 | 61 | 61 | 61 |  |
| rel_opc |  |  |  |  | 63 | 63 |  |  |  |  |  |  | 63 |  |  | 63 |  |  |  |  |  |  |  | 63 | 63 |  |  |  |  | 63 | 63 |  | 62 | 62 | 62 | 62 | 62 | 62 |  |  |  |  |  |  |  |  |  |  |  |  |
| op_rel |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 64 | 65 | 66 | 67 | 68 | 69 |  |  |  |  |  |  |  |  |  |  |  |  |
| soma |  |  | 70 | 70 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 70 |  |  |  |  | 70 | 70 | 70 | 70 | 70 |  |
| soma' |  |  |  |  | 73 | 73 |  |  |  |  |  |  | 73 |  |  | 73 |  |  |  |  |  |  |  | 73 | 73 |  |  |  |  | 73 | 73 |  | 73 | 73 | 73 | 73 | 73 | 73 | 71 | 72 |  |  |  |  |  |  |  |  |  |  |
| termo |  |  | 74 | 74 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 74 |  |  |  |  | 74 | 74 | 74 | 74 | 74 |  |
| termo' |  |  |  |  | 78 | 78 |  |  |  |  |  |  | 78 |  |  | 78 |  |  |  |  |  |  |  | 78 | 78 |  |  |  |  | 78 | 78 |  | 78 | 78 | 78 | 78 | 78 | 78 | 78 | 78 | 75 | 76 | 77 |  |  |  |  |  |  |  |
| unario |  |  | 80 | 80 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 79 |  |  |  |  | 80 | 80 | 80 | 80 | 80 |  |
| potencia |  |  | 81 | 81 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 81 | 81 | 81 | 81 | 81 |  |
| pot_opc |  |  |  |  | 83 | 83 |  |  |  |  |  |  | 83 |  |  | 83 |  |  |  |  |  |  |  | 83 | 83 |  |  |  |  | 83 | 83 |  | 83 | 83 | 83 | 83 | 83 | 83 | 83 | 83 | 83 | 83 | 83 | 82 |  |  |  |  |  |  |
| primario |  |  | 89 | 90 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 84 | 85 | 86 | 87 | 88 |  |
| sufixo_id |  |  |  | 91 | 92 | 92 |  |  |  |  |  |  | 92 |  |  | 92 |  |  |  |  |  |  |  | 92 | 92 |  |  |  |  | 92 | 92 |  | 92 | 92 | 92 | 92 | 92 | 92 | 92 | 92 | 92 | 92 | 92 | 92 |  |  |  |  |  |  |
| args_opt |  |  | 93 | 93 | 94 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 93 |  |  |  |  |  |  |  | 93 |  |  |  |  | 93 | 93 | 93 | 93 | 93 |  |
| args |  |  | 95 | 95 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 95 |  |  |  |  |  |  |  | 95 |  |  |  |  | 95 | 95 | 95 | 95 | 95 |  |
| args' |  |  |  |  | 97 | 96 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
