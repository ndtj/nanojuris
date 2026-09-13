# TJES - Pesquisa De Jurisprudencia

Status atual: `public_json_contract_candidate` para a nova consulta pública;
a superfície ColdFusion legada permanece `source_unavailable`.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado do Espirito Santo.
- Portal atual observado: `https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx`.
- Superficie legada com resultados: `https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/cons_jurisp.cfm`.
- Detalhe/resultado observado: `https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/det_jurisp.cfm`.

## Evidencia De Resultado

Uma pagina oficial de resultado indexada exibiu registros com:

- numero CNJ;
- classe;
- orgao julgador;
- data de julgamento e publicacao;
- relator e origem;
- ementa e conclusao.

Tambem existem ementarios trimestrais oficiais em PDF, que podem formar uma
fonte documental independente da busca interativa.

## Diagnostico E Lacunas

O portal atual `Pesquisa.aspx` sofreu timeout no mapeamento HTTP anterior. A
rota ColdFusion antiga ja foi encontrada em resultados oficiais, mas ainda
falta reproduzir a consulta, a paginacao, o detalhe e o documento em uma sessao
limpa. Nao tratar uma pagina indexada como contrato completo.

Classificação anterior: `candidate_needs_har`, evidência `B` para a superfície
legada e `blocked_transport` para o portal atual. Essa classificação foi
revisada após a publicação da nova SPA de consulta abaixo.

## Contrato público JSON observado (2026-08-28)

A página oficial
[`consulta-jurisprudencia`](https://sistemas.tjes.jus.br/consulta-jurisprudencia/)
distribui um frontend que chama a API pública no mesmo domínio. Chamadas
controladas, sem autenticação, reproduziram:

| Rota | Método/parâmetros | Campos/resultado | Classificação |
| --- | --- | --- | --- |
| `/consulta-jurisprudencia/api/health` | GET | `service`, `active_cores`, nomes, facetas e contagem de cada core | `implemented_diagnostic_candidate` |
| `/consulta-jurisprudencia/api/cores` | GET | catálogo de `pje1g`, `pje2g`, `pje2g_mono`, `legado`, `turma_recursal_legado` | `implemented_catalog_candidate` |
| `/consulta-jurisprudencia/api/facets?core=pje2g` | GET | facetas de classe, jurisdição, magistrado, órgão e assunto | `implemented_metadata_candidate` |
| `/consulta-jurisprudencia/api/search?core=pje2g&q=gratuidade%20de%20justi%C3%A7a&page=1&per_page=1` | GET | HTTP 200 JSON; `docs`, `facets`, `page`, `per_page`, `total`, `total_pages`; `total=166448` no teste | `candidate_adapter_p1` |

Os documentos PJe expõem `nr_processo`, `classe_judicial`, `magistrado`,
`orgao_julgador`, `ementa`/`ementa_html` e `acordao`/`acordao_html`; o 1º grau
também expõe `inteiro_teor`/`inteiro_teor_html`. O core legado expõe
`numero_processo_legado`, `nome_desembargador`, órgão, datas de julgamento e
publicação e conteúdo decisório HTML/RTF. Os cinco cores e seus totais foram
confirmados por `/health`.

O adapter não deve usar as URLs privadas `172.27.*` devolvidas como informação
de diagnóstico em `/health`, nem assumir que a API é um contrato de
redistribuição. Antes de promoção, registrar fixtures pequenas de sucesso,
vazio, erro, paginação e cada core; testar `per_page` máximo, ordenação e
rate-limit; mapear identidade/datas para `CanonicalDecision`; preservar
`SourceTrace`; e obter revisão das condições de reutilização. A página não
apresenta licença explícita de redistribuição, portanto disponibilidade pública
não equivale a autorização de republicação.

O plano de promoção, os requisitos e os gates pendentes estão registrados na
mudança SDD `0025-tjes-public-json-adapter`.

## Promocao Futura

Completar fixtures sanitizadas de busca, vazio, erro, paginação e cada core;
confirmar filtros, limite, ordenação e reuso. Criar também um provider
documental separado para os ementários PDF, sem misturar esse acervo curado
com a busca geral de acórdãos.

## Validação live 2026-08-16

- Portal atual respondeu HTTP 503; a rota ColdFusion legada respondeu HTTP 404.
- Nenhuma busca, paginação ou detalhe da superfície antiga foi promovida.
  Ementários PDF continuam sendo superfície documental independente.

## Validação live da nova API 2026-08-28

- `/health`, `/cores` e `/facets?core=pje2g`: HTTP 200 e JSON válido.
- `/search` com `core=pje2g`, termo jurídico e `per_page=1`: HTTP 200, um
  documento e total reproduzido; o mesmo contrato respondeu para `pje1g` e
  `legado`.
- Nenhuma credencial, CAPTCHA ou rota privada foi usada; nenhuma alteração em
  produção foi feita.

## Validação live bounded 2026-09-01

`GET /consulta-jurisprudencia/api/search?core=pje2g&q=<termo>&page=1&per_page=1`
respondeu HTTP 200 e JSON com um registro, total declarado 200.397 e campos de
identidade e ementa/acórdão. O corpo foi analisado em memória e não foi
persistido. Metadados e hash estão em
[`juscraper-live-smoke-20260901.json`](../../provider-discovery/juscraper-live-smoke-20260901.json).

Esta evidência atualiza a disponibilidade da superfície para candidata live;
não promove adapter nem autoriza coleta em escala. Fixtures, equivalência,
limites e revisão de reuso continuam gates do SDD `0025`.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

### Fallback de conteudo HTML - 0050

Quando `ementa` ou `acordao` vierem vazios, o parser usa respectivamente
`ementa_html` ou `acordao_html`, remove apenas o markup para os campos
canonicos e conserva o HTML original em `raw`. Os marcadores
`summary_source`/`full_text_source` permitem auditar a origem. Campos planos
presentes sempre vencem o fallback; o contrato continua restrito ao core
`pje2g`/CJSG.

## Fontes Oficiais

- [Consulta de jurisprudencia do TJES](https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx)
- [Busca legada TJES](https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/cons_jurisp.cfm)
- [Ementario trimestral oficial do TJES](https://www.tjes.jus.br/wp-content/uploads/Ementario_Trimestral_TJES_JAS_2024.pdf)

## Contrato E Filtros Pendentes

Os filtros documentados para a superficie legada sao justica/sistema, periodo e termo; a pagina indexada tambem sugere consulta por numero e resultado detalhado. Nomes de campos, metodo, paginacao, ordenacao e valores nao foram reproduzidos. O portal atual ASP.NET e a superficie ColdFusion legada devem ser tratados como contratos separados.

## MCP

O MCP deve manter a busca interativa fora da federação automática enquanto os
gates do SDD não forem concluídos. Pode oferecer futuramente o ementário PDF
como fonte curada separada, com data, edição e URL oficial.

## Auditoria de contrato 2026-08-28

- O portal atual retornou HTTP 503 na validacao controlada.
- A rota ColdFusion legada de resultados retornou HTTP 404.
- Resultados indexados e ementarios oficiais comprovam conteudo publico, mas
  nao comprovam metodo, filtros, paginacao ou contrato de resposta reproduzivel.
- Nenhum adapter foi promovido; a fonte permanece candidata documental.

## Contrato NanoJuris promovido — 0049

O adapter `tjes_jurisprudencia` usa exclusivamente o core `pje2g` da rota
`GET /consulta-jurisprudencia/api/search`, com os parâmetros `core`, `q`,
`page` e `per_page`. Ele representa CJSG/segundo grau e não reutiliza o core
`pje1g` do provider `tjes_cjpg`.

Campos canônicos mapeados: `id`/`id_bin`, `nr_processo`, `ementa`, `acordao`,
`magistrado`, `orgao_julgador`, `classe_judicial`, `assunto_principal` e
`dt_juntada`. O payload integral é preservado em `raw` e cada chamada emite
`SourceTrace` com URL final, status, content-type, hash, bytes e latência.

Fixtures sanitizadas: `tests/fixtures/tjes_cjsg_success.json`,
`tjes_cjsg_empty.json`, `tjes_cjsg_invalid.json` e
`tjes_cjsg_schema_drift.json`. A busca está habilitada na federação padrão para
o recorte CJSG; erros HTTP, timeout e mudança de schema são diagnósticos
explícitos e nunca lista vazia.
