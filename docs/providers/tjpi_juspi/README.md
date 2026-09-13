# `tjpi_juspi`

## Identidade

- Fonte oficial: Jurisprudencia publica do TJPI/JusPI.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_tribunal`.
- URL inicial: `https://jurisprudencia.tjpi.jus.br/`.
- Status de acesso: candidato validado por rota publica com resultado real.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas observadas:
  - `GET /`
  - `GET /jurisprudences/search?q=<termo>`
  - `GET /jurisprudences/search?page=<n>&q=<termo>`
  - `GET /jurisprudences/<id>/public`
- Probe validado:
  - `GET /jurisprudences/search?q=dano%20moral`
- Metodos: `GET`.
- Parametros conhecidos:
  - `q`: termo de busca.
  - `page`: pagina de resultados.
  - `tipo`: `Acórdão`, `Decisão Terminativa` ou `Súmula`.
  - `relator`: nome textual publicado no formulario.
  - `classe`: classe textual publicada no formulario.
  - `orgao`: orgao/colegiado textual publicado no formulario.
- `data_min`: data inicial.
- Runtime NanoJuris promove `types`, `rapporteur`, `source_origin`, `updated_from`
  e `updated_to` para os campos públicos `tipo`, `relator`, `orgao`, `data_min`
  e `data_max`.
  - `data_max`: data final.
- Paginacao: links oficiais usam `page=<n>`.
- Ordenacao/filtros: filtros textuais do formulario; ordenacao nao observada.

## Dados retornados

- Campos observados:
  - numero CNJ;
  - tipo (`Acordao`, `Decisao Terminativa`, `Sumula`);
  - publicacao;
  - relator;
  - orgao julgador;
  - ementa;
  - total de resultados;
  - paginacao.
- Campos canonicos: `CanonicalDecision` e `CanonicalDocument`.
- Inteiro teor: HTML publico por `GET /jurisprudences/<id>/public`.

## Comportamento observado

- Busca com resultado: HTTP 200 com HTML server-side contendo resultados reais.
- Busca sem resultado: HTTP 200 sem cards `div.callout`, normalizado como zero
  resultados.
- Erro HTTP esperado: pendente.
- Controle de acesso/captcha: nao observado no probe inicial.

## Fixtures

- [x] `q=dano moral` com resultado:
  `tests/fixtures/tjpi_juspi_dano_moral.html`.
- [x] busca vazia:
  `tests/fixtures/tjpi_juspi_empty.html`.
- [x] detalhe/inteiro teor:
  `tests/fixtures/tjpi_juspi_detail.html`.
- [x] `q=<numero CNJ>` com resultado confirmado em chamada live; consultas
  CNJ inexistentes retornam pagina vazia sem erro de transporte.
- [x] pagina 2 especifica: a rota `page=2` retornou janela distinta e o parser
  preserva faixa um-based consistente mesmo limitando `page_size`.

## MCP e agentes

- Quando usar: fonte estadual rapida para perguntas naturais sobre
  jurisprudencia do TJPI, inclusive com detalhe publico quando o resultado traz
  `public_id`.
- Quando pular: quando a pergunta exigir tribunal nacional, outros estados,
  autos de processo, documentos sigilosos ou filtros nao cobertos pelo
  formulario publico.
- Mensagem segura: "Consultei a jurisprudencia publica do TJPI/JusPI e preservei
  link e trace da fonte oficial."
- Riscos: HTML server-side pode mudar; filtros dependem dos valores textuais do
  formulario.

## Proximos passos

- [x] Salvar fixture HTML publica representativa.
- [x] Criar parser offline.
- [x] Identificar paginacao basica.
- [x] Validar detalhe/inteiro teor publico.
- [x] Implementar `tjpi_juspi.py`.
- [x] Adicionar teste live opt-in para duas páginas, número CNJ e vazio
  explícito (`tests/test_tjpi_live.py`).
- [x] Catalogar valores de filtros aceitos pelo formulário no contrato do
  provider (`tipo`, `relator`, `orgao`, `data_min`, `data_max`); valores são
  encaminhados sem inferência.

## Revalidação live 2026-09-05

- `GET /jurisprudences/search?q=dano moral` e `page=2` responderam HTTP 200,
  com texto jurídico, totais positivos e IDs não sobrepostos.
- `GET /jurisprudences/search?q=<numero CNJ>` retornou o registro correspondente;
  um CNJ impossível retornou HTTP 200 sem resultados, classificado como vazio
  não-autoritativo quando o portal omite a faixa de total.
- O parser agora expõe `total_known=True` quando a página publica total
  positivo e nunca devolve faixa impossível (`start > end`).

## Inteiro teor e contrato de bytes

`GET /jurisprudences/<id>/public` e uma rota publica de detalhe HTML validada
por fixture. O provider preserva a resposta original em `raw_bytes`, extrai o
conteudo juridico para `text` e registra SHA-256, tamanho, content-type e
status de extração. A fonte nao foi anunciada como PDF.
## Contrato CJSG fechado - 2026-09-06

- A busca pública é restringida ao filtro oficial `tipo=Acórdão` quando o
  chamador não informa tipo; súmulas e escopos de primeiro grau são rejeitados.
- Cada registro aceito é normalizado com `authority=TJPI`, `branch=state`,
  `degree=second`, `instance=second`, `collection=CJSG` e URL pública de
  inteiro teor, preservando o HTML e a proveniência.
- A rota `GET /jurisprudences/search` foi validada bounded com resultado de
  acórdão e paginação; o detalhe público continua sob demanda.
