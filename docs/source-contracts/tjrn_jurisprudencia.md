# TJRN - Pesquisa De Jurisprudencia

Status atual: `blocked_or_inconclusive` para replay HTTP limpo.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado do Rio Grande do Norte.
- Portal oficial: `https://jurisprudencia.tjrn.jus.br/`.
- Categoria: jurisprudencia estadual unificada.
- Escopo anunciado: PJe e, progressivamente, acervo legado SAJ.

## Contrato Minimo Observado

Comunicacao institucional do TJRN descreve uma busca unificada para:

- acordaos;
- decisoes colegiadas;
- decisoes monocraticas;
- primeiro e segundo graus;
- pesquisa livre, ementa, classe processual e numero de processo.

O endpoint de consulta, metodo, payload, paginacao, detalhe e documento ainda
nao foram reproduzidos de forma confiavel. O endpoint e-SAJ legado
`https://esaj.tjrn.jus.br/cjsg/resultadoCompleta.do` respondeu HTTP 403 no
mapeamento anterior, portanto nao deve ser confundido com o portal unificado.

## Diagnostico De Acesso

O portal principal respondeu 403 no acesso automatizado atual. Isso e evidencia
de controle ou politica de acesso na janela testada, nao prova de que o acervo
nao exista. Nenhuma credencial ou bypass deve ser tentado.

Classificacao: `blocked_or_inconclusive`, evidencia `B`.

## Promocao Futura

Capturar uma sessao publica normal e registrar somente o contrato necessario:
rota de busca, payload, resposta JSON/HTML, campos, pagina, vazio, detalhe e
inteiro teor. Reproduzir depois por HTTP limpo sem cookies pessoais e criar
fixtures de sucesso, vazio e erro.

## Validacao live 2026-08-11

- Uma janela anterior respondeu HTTP 200, mas a repeticao atual respondeu HTTP 403.
- A rota de busca, payload, paginacao e detalhe continuam sem contrato estavel; nao implementar com base no GET isolado.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Portal de jurisprudencia do TJRN](https://jurisprudencia.tjrn.jus.br/)
- [Noticia institucional sobre a busca unificada](https://glaucialima.com/2019/11/18/nova-versao-do-sistema-de-consulta-de-jurisprudencia-esta-a-disposicao-dos-usuarios/)
## Contrato E Dados

Filtros institucionais confirmados: texto livre, ementa, classe processual, numero, grau, tipo colegiado/monocratico e origem PJe/SAJ. Metodo, names, payload, catalogos, pagina, ordenacao, total, identificador, ementa e inteiro teor continuam nao observados em resposta reproduzida.

## MCP

O MCP deve manter TJRN fora da federacao automatica enquanto o portal responder 403 ou faltar contrato. O provider futuro deve separar PJe e SAJ e preservar qualquer indicacao de fonte, grau e tipo documental.
## Dados

Filtros institucionais confirmados: texto livre, ementa, classe processual,
numero, grau, tipo colegiado/monocratico e origem PJe/SAJ. Nao ha schema de
resultado reproduzido; identificador, ementa, total, paginacao e documento
permanecem pendentes.

## Contrato

O endpoint, metodo, payload, catalogos, pagina e ordenacao ainda nao foram
confirmados. O 403 atual nao deve ser convertido em vazio.
