"""
Gerador automático de gramática LL(1) a partir de uma gramática AMBÍGUA de
expressões, com precedência e associatividade declaradas.

Entrada (arquivo de texto):

    # precedência em ordem CRESCENTE: a primeira linha é a que liga MENOS
    %left ou              # associativo à esquerda
    %prefix nao           # operador prefixo (unário)
    %nonassoc == < >      # não associativo
    %left + -
    %right ^              # associativo à direita

    E -> E ou E | nao E | E + E | E ^ E | - E | ( E ) | id

Etapas (cada uma devolve uma gramática nova, para ser exibida):

  1. eliminar_ambiguidade        um não-terminal por nível de precedência;
  2. eliminar_recursao_esquerda  A → A α | β  vira  A → β A',  A' → α A' | ε
                                 (direta e indireta, pelo algoritmo clássico);
  3. fatorar_esquerda            A → α β1 | α β2  vira  A → α A',  A' → β1 | β2
                                 (repetido até não sobrar prefixo comum);
  4. a tabela LL(1) é montada com FIRST/FOLLOW e os conflitos são contados.

Limitações assumidas (como no yacc clássico): o operando direito de um operador
associativo à direita é do mesmo nível, então `2 ^ -3` só é aceito se o menos
unário tiver precedência MENOR que `^`; e só alternativas no formato
`A op A` (binário) ou `op A` (prefixo) são tratadas como operadores.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .first_follow import tabela_first_follow
from .gramatica import EPSILON, ErroGramatica, Gramatica
from .ll1 import TabelaLL1

Cadeia = tuple[str, ...]
Producoes = dict[str, list[Cadeia]]

DIRETIVAS = {"%left": "esquerda", "%right": "direita", "%nonassoc": "não associativo", "%prefix": "prefixo"}


class ErroConversor(ErroGramatica):
    """Entrada inválida para o conversor (diretiva, operador ou gramática)."""


@dataclass
class Nivel:
    """Um nível de precedência: associatividade e operadores (do menor ao maior nível)."""

    tipo: str                   # 'left' | 'right' | 'nonassoc' | 'prefix'
    operadores: list[str]

    def descricao(self) -> str:
        return f"{DIRETIVAS['%' + self.tipo]}: {' '.join(self.operadores)}"


@dataclass
class Etapa:
    titulo: str
    explicacao: list[str]
    gramatica: Gramatica


@dataclass
class Conversao:
    """Resultado completo: níveis lidos, etapas intermediárias e tabela final."""

    niveis: list[Nivel]
    etapas: list[Etapa] = field(default_factory=list)
    tabela: TabelaLL1 | None = None

    @property
    def final(self) -> Gramatica:
        return self.etapas[-1].gramatica

    @property
    def eh_ll1(self) -> bool:
        return self.tabela is not None and self.tabela.eh_ll1


# ------------------------------------------------------------------ utilitários


def _unico(base: str, usados: set[str]) -> str:
    """Primeiro nome livre entre `base`, `base'`, `base''`, ... (e registra o uso)."""
    nome = base
    while nome in usados:
        nome += "'"
    usados.add(nome)
    return nome


def _montar(producoes: Producoes, ordem: list[str], nome: str) -> Gramatica:
    """Cria uma Gramatica; `ordem` define a ordem dos não-terminais (o 1º é o inicial)."""
    lista = [(nt, alt) for nt in ordem for alt in producoes[nt]]
    return Gramatica(lista, nome)


def _extrair(g: Gramatica) -> tuple[Producoes, list[str]]:
    producoes: Producoes = {nt: [p.direita for p in g.por_nao_terminal[nt]] for nt in g.nao_terminais}
    return producoes, list(g.nao_terminais)


def _texto(nt: str, alternativas: list[Cadeia]) -> str:
    return f"{nt} → " + " | ".join(" ".join(a) if a else EPSILON for a in alternativas)


def _simbolos_usados(g: Gramatica) -> set[str]:
    return set(g.nao_terminais) | set(g.terminais)


# ------------------------------------------------------------------ leitura


def ler_entrada(texto: str) -> tuple[list[Nivel], Gramatica]:
    """Separa as diretivas `%left/%right/%nonassoc/%prefix` das produções."""
    niveis: list[Nivel] = []
    restante: list[str] = []
    for numero, linha in enumerate(texto.splitlines(), 1):
        sem_comentario = linha.split("#", 1)[0].strip()
        if sem_comentario.startswith("%") and sem_comentario.split()[0] in DIRETIVAS:
            partes = sem_comentario.split()
            if len(partes) < 2:
                raise ErroConversor(f"linha {numero}: '{partes[0]}' sem operadores")
            niveis.append(Nivel(partes[0][1:], partes[1:]))
        else:
            restante.append(linha)
    return niveis, Gramatica.de_texto("\n".join(restante), nome="gramática ambígua")


# ------------------------------------------------------------------ etapa 1


def eliminar_ambiguidade(g: Gramatica, niveis: list[Nivel]) -> Etapa:
    """Gera um não-terminal por nível de precedência.

    Para um não-terminal A com alternativas `A op A` (binárias) e `op A`
    (prefixas), cria N0 = A, N1, N2, ... em ordem crescente de precedência e
    uma regra por nível, que só aceita o nível seguinte como operando:

        esquerda   N_i → N_i op N_{i+1} | N_{i+1}      (recursão à esquerda)
        direita    N_i → N_{i+1} op N_i | N_{i+1}      (recursão à direita)
        não assoc  N_i → N_{i+1} op N_{i+1} | N_{i+1}  (sem recursão)
        prefixo    N_i → op N_i | N_{i+1}

    O último nível, N_k, recebe as demais alternativas (átomos: `id`, `( A )`...).
    Os operadores de maior precedência acabam mais fundo na árvore.
    """
    binarios = {op: n for n in niveis if n.tipo != "prefix" for op in n.operadores}
    prefixos = {op: n for n in niveis if n.tipo == "prefix" for op in n.operadores}
    producoes, ordem = _extrair(g)
    usados = _simbolos_usados(g)
    explicacao: list[str] = []
    novas: Producoes = {}
    nova_ordem: list[str] = []

    for nt in ordem:
        alternativas = producoes[nt]
        por_nivel: dict[int, list[tuple[str, Cadeia]]] = {}   # índice do nível -> [(operador, alternativa)]
        atomos: list[Cadeia] = []
        for alt in alternativas:
            if len(alt) == 3 and alt[0] == nt and alt[2] == nt and alt[1] not in g.nao_terminais:
                nivel = binarios.get(alt[1])
                if nivel is None:
                    raise ErroConversor(f"operador '{alt[1]}' usado em '{_texto(nt, [alt])}' "
                                        f"não tem precedência declarada (%left, %right ou %nonassoc)")
                por_nivel.setdefault(niveis.index(nivel), []).append((alt[1], alt))
            elif len(alt) == 2 and alt[1] == nt and alt[0] in prefixos:
                por_nivel.setdefault(niveis.index(prefixos[alt[0]]), []).append((alt[0], alt))
            else:
                atomos.append(alt)

        if not por_nivel:                                    # nada a desambiguar neste não-terminal
            novas[nt] = alternativas
            nova_ordem.append(nt)
            continue
        if not atomos:
            raise ErroConversor(f"'{nt}' só tem alternativas com operadores; falta uma base (ex.: id)")

        indices = sorted(por_nivel)                         # níveis usados, do menor ao maior
        nomes = [nt] + [_unico(f"{nt}{i}", usados) for i in range(1, len(indices))]
        nome_atomo = _unico(f"{nt}{len(indices)}", usados)
        nomes.append(nome_atomo)
        explicacao.append(f"{nt}: {len(indices)} nível(is) de operadores + átomos em '{nome_atomo}'.")

        for posicao, indice in enumerate(indices):
            nivel, atual, proximo = niveis[indice], nomes[posicao], nomes[posicao + 1]
            alts: list[Cadeia] = []
            for op, _ in por_nivel[indice]:
                if nivel.tipo == "left":
                    alts.append((atual, op, proximo))
                elif nivel.tipo == "right":
                    alts.append((proximo, op, atual))
                elif nivel.tipo == "nonassoc":
                    alts.append((proximo, op, proximo))
                else:                                        # prefixo
                    alts.append((op, atual))
            alts.append((proximo,))
            novas[atual] = alts
            nova_ordem.append(atual)
            explicacao.append(f"  nível {posicao + 1} ({nivel.descricao()}):  {_texto(atual, alts)}")
        novas[nome_atomo] = atomos
        nova_ordem.append(nome_atomo)
        explicacao.append(f"  átomos:  {_texto(nome_atomo, atomos)}")

    return Etapa("ETAPA 1 — eliminação da ambiguidade (precedência e associatividade)", explicacao,
                 _montar(novas, nova_ordem, "sem ambiguidade"))


# ------------------------------------------------------------------ etapa 2


def _anulaveis(producoes: Producoes) -> set[str]:
    """Não-terminais que derivam ε (ponto fixo simples)."""
    anulaveis: set[str] = set()
    mudou = True
    while mudou:
        mudou = False
        for nt, alternativas in producoes.items():
            if nt not in anulaveis and any(all(s in anulaveis for s in alt) for alt in alternativas):
                anulaveis.add(nt)
                mudou = True
    return anulaveis


def _alcance_a_esquerda(producoes: Producoes) -> dict[str, set[str]]:
    """Para cada A, os não-terminais B tais que A ⇒+ B γ (B aparece como 1º símbolo
    de alguma derivação de A). Considera prefixos anuláveis: em `A → B C`,
    com B ⇒ ε, também C pode ficar na frente."""
    anulaveis = _anulaveis(producoes)
    direto: dict[str, set[str]] = {nt: set() for nt in producoes}
    for nt, alternativas in producoes.items():
        for alt in alternativas:
            for simbolo in alt:
                if simbolo in producoes:
                    direto[nt].add(simbolo)
                if simbolo not in anulaveis:
                    break
    alcance: dict[str, set[str]] = {}
    for inicio in producoes:                                 # fecho transitivo, nt a nt
        visitados: set[str] = set()
        pilha = list(direto[inicio])
        while pilha:
            atual = pilha.pop()
            if atual not in visitados:
                visitados.add(atual)
                pilha.extend(direto[atual])
        alcance[inicio] = visitados
    return alcance


def _tem_recursao_esquerda(producoes: Producoes) -> str | None:
    """Um não-terminal que ainda deriva a si mesmo à esquerda (ou None)."""
    alcance = _alcance_a_esquerda(producoes)
    return next((nt for nt in producoes if nt in alcance[nt]), None)


def eliminar_recursao_esquerda(g: Gramatica) -> Etapa:
    """Elimina recursão à esquerda direta e indireta (algoritmo clássico).

    Ordena os não-terminais A1..An. Para cada Ai:
      * para j < i, substitui cada alternativa `Ai → Aj γ` pelas alternativas
        `Ai → δ γ`, onde `Aj → δ` (isso transforma recursão indireta em direta;
        a substituição só é feita quando Aj realmente leva de volta a Ai);
      * elimina a recursão direta de Ai:   Ai → Ai α | β   ⟹   Ai → β Ai',  Ai' → α Ai' | ε.
    """
    producoes, ordem = _extrair(g)
    usados = _simbolos_usados(g)
    explicacao: list[str] = []
    ordem_final = list(ordem)

    for i, ai in enumerate(ordem):
        for aj in ordem[:i]:
            # Só vale substituir Aj se Aj puder levar de volta a Ai (recursão
            # indireta); senão a substituição só incharia a gramática.
            if ai not in _alcance_a_esquerda(producoes)[aj]:
                continue
            novas: list[Cadeia] = []
            substituiu = False
            for alt in producoes[ai]:
                if alt and alt[0] == aj:
                    novas.extend(delta + alt[1:] for delta in producoes[aj])
                    substituiu = True
                else:
                    novas.append(alt)
            if substituiu:
                explicacao.append(f"{ai}: recursão indireta — '{aj}' no início substituído pelas suas alternativas.")
                producoes[ai] = novas

        recursivas = [alt[1:] for alt in producoes[ai] if alt and alt[0] == ai]
        if not recursivas:
            continue
        bases = [alt for alt in producoes[ai] if not (alt and alt[0] == ai)]
        if not bases:
            raise ErroConversor(f"'{ai}' é recursivo à esquerda e não tem alternativa base (derivação infinita)")
        if any(not alfa for alfa in recursivas):
            raise ErroConversor(f"'{ai} → {ai}' é um ciclo (A ⇒ A); a gramática é inválida")
        antes = _texto(ai, producoes[ai])
        linha = _unico(f"{ai}'", usados)
        producoes[ai] = [base + (linha,) for base in bases]
        producoes[linha] = [alfa + (linha,) for alfa in recursivas] + [()]
        ordem_final.insert(ordem_final.index(ai) + 1, linha)
        explicacao.append(f"direta em {ai}:  {antes}")
        explicacao.append(f"      ⟹  {_texto(ai, producoes[ai])}")
        explicacao.append(f"          {_texto(linha, producoes[linha])}")

    restante = _tem_recursao_esquerda(producoes)
    if restante:
        raise ErroConversor(f"'{restante}' ainda é recursivo à esquerda (via produções ε): caso não suportado")
    if not explicacao:
        explicacao.append("Nenhuma recursão à esquerda encontrada.")
    return Etapa("ETAPA 2 — eliminação da recursão à esquerda", explicacao,
                 _montar(producoes, ordem_final, "sem recursão à esquerda"))


# ------------------------------------------------------------------ etapa 3


def _prefixo_comum(alternativas: list[Cadeia]) -> Cadeia:
    """Maior prefixo de símbolos que todas as alternativas têm em comum."""
    prefixo = alternativas[0]
    for alt in alternativas[1:]:
        k = 0
        while k < len(prefixo) and k < len(alt) and prefixo[k] == alt[k]:
            k += 1
        prefixo = prefixo[:k]
    return prefixo


def fatorar_esquerda(g: Gramatica) -> Etapa:
    """Fatora prefixos comuns até que nenhum não-terminal tenha dois deles.

    A → α β1 | α β2 | γ   ⟹   A → α A' | γ,   A' → β1 | β2   (β vazio vira ε).
    Cada rodada fatora UM grupo; como A' pode ter novo prefixo comum, a rodada
    se repete até não haver mais mudança.
    """
    producoes, ordem = _extrair(g)
    usados = _simbolos_usados(g)
    explicacao: list[str] = []

    mudou = True
    while mudou:
        mudou = False
        for nt in list(ordem):
            grupos: dict[str, list[Cadeia]] = {}
            for alt in producoes[nt]:
                if alt:                                      # ε não tem prefixo para fatorar
                    grupos.setdefault(alt[0], []).append(alt)
            comum = next((alts for alts in grupos.values() if len(alts) > 1), None)
            if comum is None:
                continue
            prefixo = _prefixo_comum(comum)
            novo = _unico(f"{nt}'", usados)
            antes = _texto(nt, producoes[nt])
            primeira = producoes[nt].index(comum[0])
            restantes = [alt for alt in producoes[nt] if alt not in comum]
            restantes.insert(min(primeira, len(restantes)), prefixo + (novo,))
            producoes[nt] = restantes
            producoes[novo] = [alt[len(prefixo):] for alt in comum]
            ordem.insert(ordem.index(nt) + 1, novo)
            explicacao.append(f"prefixo '{' '.join(prefixo)}' em {nt}:  {antes}")
            explicacao.append(f"      ⟹  {_texto(nt, producoes[nt])}")
            explicacao.append(f"          {_texto(novo, producoes[novo])}")
            mudou = True
            break                                            # recomeça: `ordem` mudou
    if not explicacao:
        explicacao.append("Nenhum prefixo comum encontrado.")
    return Etapa("ETAPA 3 — fatoração à esquerda", explicacao, _montar(producoes, ordem, "fatorada"))


# ------------------------------------------------------------------ orquestração


def converter(texto: str) -> Conversao:
    """Executa as etapas 1 a 3 e monta a tabela LL(1) da gramática final (etapa 4)."""
    niveis, original = ler_entrada(texto)
    resultado = Conversao(niveis)
    resultado.etapas.append(Etapa("GRAMÁTICA AMBÍGUA (entrada)", [n.descricao() for n in niveis], original))
    for passo in (lambda g: eliminar_ambiguidade(g, niveis), eliminar_recursao_esquerda, fatorar_esquerda):
        resultado.etapas.append(passo(resultado.final))
    resultado.tabela = TabelaLL1(resultado.final)
    return resultado


def converter_arquivo(caminho: str) -> Conversao:
    with open(caminho, encoding="utf-8") as f:
        return converter(f.read())


def relatorio_final(conversao: Conversao) -> str:
    """Texto da etapa 4: FIRST/FOLLOW, conflitos e veredito sobre ser LL(1)."""
    tabela = conversao.tabela
    linhas = [tabela_first_follow(tabela.gramatica, tabela.first, tabela.follow), ""]
    linhas += [f"  {c}" for c in tabela.conflitos]
    if tabela.eh_ll1:
        linhas.append("Cada célula M[A, a] tem no máximo UMA produção: a gramática gerada é LL(1) (zero conflitos).")
    else:
        linhas.append("A gramática gerada NÃO é LL(1): sobraram conflitos que a conversão automática não resolve "
                      "(ex.: ambiguidade que não vem de operadores, como o 'senão pendurado').")
    return "\n".join(linhas)


def gramatica_como_arquivo(g: Gramatica) -> str:
    """Gramática no formato lido por Gramatica.de_arquivo (para reutilizar a saída)."""
    cabecalho = "# Gramática LL(1) gerada automaticamente por mare/conversor.py\n"
    return cabecalho + "\n".join(
        f"{nt} -> " + " | ".join(" ".join(p.direita) if p.direita else EPSILON for p in g.por_nao_terminal[nt])
        for nt in g.nao_terminais) + "\n"
