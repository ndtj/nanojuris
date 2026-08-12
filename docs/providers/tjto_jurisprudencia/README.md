# TJTO - Jurisprudencia

Status atual: `candidate_needs_har` para busca automatizada reproduzivel.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado do Tocantins.
- Portal de pesquisa: `https://jurisprudencia.tjto.jus.br/`.
- Consulta observada: `https://jurisprudencia.tjto.jus.br/consulta.php`.
- Categoria: jurisprudencia estadual, acordaos e decisoes.

## Evidencia De Resultado

Paginas oficiais indexadas exibem resultados publicos com campos decisorios
estruturados, incluindo:

- processo;
- classe;
- tipo de julgamento;
- assuntos e competencia;
- relator;
- data de autuacao e julgamento;
- ementa;
- questao em discussao, razoes de decidir e tese de julgamento;
- dispositivos e jurisprudencia relevante citada.

As URLs indexadas tambem revelam filtros como `q`, `fq_assuntos`,
`fq_competencia`, `fq_magistrado` e `soementa`. Esses nomes sao pistas de
contrato da interface, nao uma autorizacao para inventar payload ou endpoint.

## Lacunas Tecnicas

O mapeamento ainda nao confirmou por HTTP limpo:

- metodo e payload da busca;
- pagina e ordenacao;
- catalogos de assuntos, competencia e magistrados;
- identificador estavel de detalhe;
- URL e formato do inteiro teor;
- resposta vazia e limites de volume.

O portal de pesquisa respondeu controle de acesso/indisponibilidade na janela
automatizada atual. Classificacao: `candidate_needs_har`, evidencia `B`.

## Promocao Futura

Capturar uma consulta publica com termo pequeno, um resultado, pagina seguinte,
resultado vazio e abertura de inteiro teor. Depois reproduzir a chamada sem
cookies privados e criar parser offline preservando o texto original e os
campos de tese.

## Validacao live 2026-08-11

- GET de `consulta.php` respondeu HTTP 403.
- A superficie permanece candidata; nao foram inferidos payload, paginacao ou detalhe a partir de URL indexada.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fonte Oficial

- [Consulta de jurisprudencia do TJTO](https://jurisprudencia.tjto.jus.br/consulta.php)
## Contrato E Filtros

As URLs indexadas sugerem q, fq_assuntos, fq_competencia, fq_magistrado e soementa, alem de campos de processo, classe, tipo, assuntos, competencia, relator, datas, ementa, questao, razoes e tese. Esses nomes sao pistas de interface; metodo, payload, pagina, ordenacao, catalogos, ids e limites continuam pendentes por causa do 403.

## MCP

O MCP deve manter TJTO fora da federacao ate uma resposta juridica reproduzida. Nao derivar payload de URLs indexadas, nao contornar 403 e nao afirmar que tese ou inteiro teor estao disponiveis sem campo ou documento oficial retornado.
