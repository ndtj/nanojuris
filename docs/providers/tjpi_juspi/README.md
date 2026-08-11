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
- [ ] `q=idpj` com resultado ou vazio documentado.
- [ ] pagina 2 especifica.

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
- [ ] Adicionar teste live opt-in.
- [ ] Catalogar valores de filtros com parser de formulario.
