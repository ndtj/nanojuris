# `tjsp_nugepnac`

## Identidade

- Fonte oficial: NugepNac/TJSP.
- Categoria: `court_precedents`.
- Familia tecnica: `catalogo_precedentes`.
- URL inicial: `https://www.tjsp.jus.br/NugepNac`.
- Status de acesso: publico parcial.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `GET /NugepNac/Irdr`
  - `GET /NugepNac/Iac`
  - `GET /NugepNac/(Irdr|Iac)/DetalheTema?codigoNoticia=<id>&pagina=1`
- Metodos: `GET`.
- Modos de busca: texto, numero, tipo de precedente e detalhe de catalogo.
- Paginacao: pagina de detalhe usa `pagina=1`; demais fluxos precisam
  aprofundamento.
- Total: sem filtro textual, o tamanho do catalogo observado e marcado como
  conhecido; com filtro textual, o total permanece explicitamente desconhecido
  porque o texto exige abrir detalhes e a janela e limitada.

## Dados retornados

- Campos extraidos:
  - numero do tema;
  - tipo de precedente;
  - status;
  - numero do processo;
  - assunto;
  - orgao julgador;
  - relator;
  - data de admissao;
  - data de julgamento de merito;
  - questao;
  - tese;
  - links de decisoes relacionadas.
- Campos canonicos: `CanonicalPrecedent`.
- Inteiro teor: nao declarado; links CJSG podem exigir verificacao separada.

## Comportamento observado

- Catalogo publico em HTML institucional.
- Pagina de detalhe contem questao e tese.
- Links de inteiro teor podem apontar para rotas CJSG com controle.

## Fixtures

- [x] Lista IRDR: `tests/fixtures/tjsp_nugepnac_list.html`.
- [x] Lista IAC: `tests/fixtures/tjsp_nugepnac_iac_list.html` (6 entries observed live).
- [x] Detalhe por `codigoNoticia`: `tests/fixtures/tjsp_nugepnac_detail.html`.
- [x] Detalhe IAC sem tese: `tests/fixtures/tjsp_nugepnac_iac_detail_no_thesis.html`.
- [x] Documento relacionado HTML: `tests/fixtures/tjsp_nugepnac_document.html`.
- [x] Tema sem tese.
- [x] Link relacionado indisponivel (process-search link preserved as context, not a document).

## MCP e agentes

- Quando usar: pesquisa de IRDR/IAC e precedentes locais do TJSP.
- Quando pular: amostragem decisoria comum ou acordaos sem vinculacao a tema.
- Mensagem segura: "Esta fonte cobre precedentes qualificados do TJSP, nao toda
  a jurisprudencia do tribunal."
- Riscos: tratar catalogo de precedentes como base exaustiva de decisoes.

## Proximos passos

- [x] Completar dossie com casos reais publicos.
- [x] Criar fixtures de lista e detalhe.
- [x] Documentar criterio de atualizacao/sincronizacao do catalogo.

### Validacao live de IAC - 2026-09-07

`GET https://www.tjsp.jus.br/NugepNac/Iac` respondeu HTTP 200 com 6 links de
detalhe. O detalhe publico do Tema 2 (`codigoNoticia=52107`) respondeu HTTP
200 e nao possui campo de tese; a questao, status e processo paradigma continuam
disponiveis. Evidencia: `docs/provider-discovery/tjsp-nugepnac-iac-live-20260907.json`.

Links de consulta processual sao mantidos em `related_links`, mas nao sao
tratados como inteiro teor. Somente links oficiais de documento CJSG observados
com rota `cjsg/getArquivo.do` podem ser selecionados para `get_document`.

### Revalidacao live de documento — 2026-09-06

O fluxo publico de NugepNac retornou um link oficial de acordao no e-SAJ. A
tentativa bounded de baixar o documento recebeu HTTP 200, mas o HTML retornado
nao continha texto de decisao extraivel; o adapter rejeitou o resultado com
erro explicito, sem trata-lo como documento vazio valido ou contornar captcha.
Evidencia: `docs/provider-discovery/tjsp-nugepnac-document-live-20260906.json`.
