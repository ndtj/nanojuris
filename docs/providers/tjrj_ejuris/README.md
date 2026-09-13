# TJRJ eJURIS - Jurisprudencia de segundo grau

## Identidade

- Fonte oficial: eJURIS do Tribunal de Justica do Estado do Rio de Janeiro.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `webforms_jurisprudence`.
- Entrada institucional: `https://www.tjrj.jus.br/web/portal-conhecimento/consulta-a-jurisprudencia`.
- Superficie: `https://www3.tjrj.jus.br/EJURIS/ConsultarJurisprudencia.aspx`.
- Status: `implemented`; adapter independente promovido ao runtime e a
  federacao apos contrato, fixtures, smoke live e qualidade tecnica.

## Contrato observado

O fluxo publico usa GET do formulario WebForms, POST com os campos ocultos
(`__VIEWSTATE`, `__EVENTVALIDATION` e lista de palavras bloqueadas) e XHR JSON
para `POST /EJURIS/ProcessarConsJurisES.aspx/ExecutarConsultarJurisprudencia`.
O adapter fixa `cmbOrigem=1`, que corresponde ao segundo grau, e nao envia nem
contorna token de CAPTCHA.

O envelope precisa conter `d.TotalDocs` e `d.DocumentosConsulta`. A pagina tem
dez registros; `numPagina` e zero-based. O parser preserva o JSON bruto, CNJ,
classe, orgao julgador, relator, tipo, datas e texto sem formatacao.

## Dados e filtros

Texto, frase exata e numero sao traduzidos para os campos nativos. Intervalos
temporais sao traduzidos para anos. Grau, instancia, ramo, autoridade e
colecao sao validados como escopo canonico. Filtros sem suporte ficam
explicitamente marcados como `unsupported`.

## Estados e limites

- O resultado vazio so e aceito quando o payload JSON e valido e o total e zero.
- HTTP 401/403, 429, 5xx, timeout, TLS e schema invalido sao erros explicitos.
- O inteiro teor e o texto inline do resultado; nao existe download separado
  promovido.
- A chamada live bounded de 2026-09-06 retornou HTTP 200, total 45643 e um
  registro textual de segundo grau. Isso e evidencia tecnica, nao promocao
  automatica.

## Rechecagem de escopo - 2026-09-07

A inspeção bounded do formulário oficial confirmou as opções de origem
disponíveis: Tribunal de Justiça do Rio de Janeiro 2a Instância, Tribunal de
Alçada Cível, Tribunal de Alçada Criminal, Turma Recursal e Conselho da
Magistratura. Não foi exposta uma opção de primeiro grau. O artefato redigido
é `docs/provider-discovery/tjrj-ejuris-origin-options-live-20260907.json`.
Este resultado confirma o escopo CJSG do adapter, mas não cria cobertura CJPG.

## Revalidacao de paginacao - 2026-09-10

Uma sonda bounded na mesma sessao WebForms consultou duas paginas distintas
para `responsabilidade civil`, com uma entrada por pagina. Ambas responderam
HTTP 200, preservaram o total conhecido (46.191) e retornaram IDs diferentes,
confirmando paginacao remota sem sobreposicao nessa amostra. A evidencia
redigida esta em
`docs/provider-discovery/tjrj-ejuris-pagination-live-20260910.json`.
Como a latencia observada ficou acima do timeout padrao de oito segundos, a
federacao permanece habilitada com monitoramento; a sonda nao altera esse
timeout operacional nem persiste o corpo da resposta.

## Fixtures e testes

- `tests/fixtures/tjrj_ejuris_form.html`;
- `tests/fixtures/tjrj_ejuris_page.json`;
- `tests/fixtures/tjrj_ejuris_empty.json`;
- `tests/fixtures/tjrj_ejuris_invalid.json`;
- `tests/fixtures/tjrj_ejuris_page2.json`;
- `tests/test_tjrj_ejuris.py`.

Os testes cobrem sucesso, vazio autoritativo, identidade, datas, texto inline,
escopo incompativel, schema drift, acesso controlado, pagina dois e capacidades.

## Federacao

O provider participa do runtime e da federacao padrao. `include_candidate_providers`
continua aceito apenas por compatibilidade.

## MCP

O provider pode ser inspecionado pelo MCP com limites e estado opt-in
preservados; nenhuma chamada e roteada por padrao.

## Proximos passos

- [x] adicionar evidencias persistidas de busca publica e segundo grau;
- [x] concluir os gates tecnicos e habilitar a promocao federada local.

## Transporte compartilhado (2026-09-08)

As tres requisicoes da sessao WebForms (GET do formulario, POST do estado e
POST XHR JSON) usam o `SharedHttpClient` com allowlist exclusiva de
`www3.tjrj.jus.br`, HTTPS/TLS verificado, limite de 16 MB, timeout configurado
e intervalo por host. POSTs nao sao repetidos automaticamente, preservando o
ViewState e evitando replay de estado ou desafio. Redirecionamentos fora da
allowlist, timeout, TLS, resposta excessiva, HTTP 403/429 e schema invalido
permanecem estados explicitos; nenhum deles e convertido em resultado vazio.
Metadados de status, URL final, hash, tamanho e latencia entram no
`SourceTrace`.
## Rechecagem de transporte — 2026-09-08

Após a migração para `SharedHttpClient`, uma busca pública bounded de
`responsabilidade civil` (página 1, tamanho 1) respondeu HTTP 200, total
conhecido 45.674 e um resultado com `degree=second`. O envelope redigido é
`docs/provider-discovery/tjrj-ejuris-live-20260908-transport-recheck.json`.
