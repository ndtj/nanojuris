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

Capturar uma busca publica com filtros de justica, sistema, periodo e termo;
registrar a resposta de resultados e abrir um item real. Criar tambem um
provider documental separado para os ementarios PDF, sem misturar esse acervo
curado com a busca geral de acordaos.

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

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Consulta de jurisprudencia do TJES](https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx)
- [Busca legada TJES](https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/cons_jurisp.cfm)
- [Ementario trimestral oficial do TJES](https://www.tjes.jus.br/wp-content/uploads/Ementario_Trimestral_TJES_JAS_2024.pdf)
## Contrato E Filtros Pendentes

Os filtros documentados para a superficie legada sao justica/sistema, periodo e termo; a pagina indexada tambem sugere consulta por numero e resultado detalhado. Nomes de campos, metodo, paginacao, ordenacao e valores nao foram reproduzidos. O portal atual ASP.NET e a superficie ColdFusion legada devem ser tratados como contratos separados.

## MCP

O MCP deve manter a busca interativa fora do roteamento enquanto o portal atual estiver em timeout e a rota legada em 404. Pode oferecer futuramente o ementario PDF como fonte curada separada, com data, edicao e URL oficial.

## Auditoria de contrato 2026-08-28

- O portal atual retornou HTTP 503 na validacao controlada.
- A rota ColdFusion legada de resultados retornou HTTP 404.
- Resultados indexados e ementarios oficiais comprovam conteudo publico, mas
  nao comprovam metodo, filtros, paginacao ou contrato de resposta reproduzivel.
- Nenhum adapter foi promovido; a fonte permanece candidata documental.
