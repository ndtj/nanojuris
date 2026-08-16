# `tjal_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia CJSG/e-SAJ do TJAL.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://www2.tjal.jus.br/cjsg`.
- Status de acesso: publico, sujeito a indisponibilidade ou controle da fonte.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `POST /resultadoCompleta.do`
  - `GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>`
- Metodos: `POST` para busca e `GET` para arquivo publico.
- Parametros: texto integral, ementa/resumo, numero CNJ, intervalo de data e
  tipo de decisao.
- Paginacao: reproduzida em sessao publica com `POST /resultadoCompleta.do`
  seguido de `GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>`.

## Dados retornados

- Campos extraidos:
  - numero CNJ;
  - tipo decisorio;
  - classe;
  - assunto;
  - relator;
  - comarca/origem;
  - orgao julgador;
  - data de publicacao;
  - ementa;
  - URL do documento;
  - `cdAcordao` e `cdForo`.
- Campos canonicos: `CanonicalDecision` e `CanonicalDocument`.
- Inteiro teor: suportado quando `getArquivo.do` responder publicamente.

## Comportamento observado

- Busca com resultado: HTML CJSG parseado pelo provider.
- Busca sem resultado: deve retornar pagina vazia.
- Controle de acesso: qualquer captcha/login deve ser reportado, sem bypass.
- Risco: alto-medio por variacao e-SAJ.

## Fixtures

- [ ] Busca com resultado.
- [ ] Busca vazia.
- [ ] Inteiro teor.
- [ ] Controle de acesso.
- [ ] Paginacao.

## MCP e agentes

- Quando usar: pesquisa de jurisprudencia publica do TJAL.
- Quando pular: se o retorno nao trouxer container de resultado ou exigir
  validacao humana.
- Mensagem segura: "A fonte TJAL/CJSG foi consultada apenas por rotas publicas
  e sem reutilizar sessao privada."
- Riscos: captcha eventual e layout e-SAJ instavel.

## Proximos passos

- [ ] Criar fixture propria do TJAL.
- [ ] Comparar labels reais com TJSP/TJMS/TJAC.
- [ ] Validar inteiro teor por `cdAcordao` e `cdForo`.

## Validacao live de capacidade - 2026-08-16

- Consulta: `responsabilidade civil`, duas paginas, 20 itens solicitados.
- Pagina 1: 20 resultados, 20 identificadores unicos, 20 com data.
- Pagina 2: 20 resultados, nenhum identificador repetido, 20 com data.
- Total remoto observado: 157.021.
- Estado: `valid` para a paginacao observada.
- Inteiro teor: capacidade declarada como chamada sob demanda; depende de a
  rota publica `getArquivo.do` responder sem controle adicional.

Evidencia estruturada: `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.json`.
