# `tjam_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia CJSG/e-SAJ do TJAM.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://consultasaj.tjam.jus.br/cjsg`.
- Status de acesso: publico, sujeito a indisponibilidade ou controle da fonte.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `POST /resultadoCompleta.do`
  - `GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>`
- Metodos: `POST` para busca e `GET` para arquivo publico.
- Parametros: texto integral, ementa/resumo, numero CNJ, intervalo de data e
  tipo decisorio.
- Paginacao: reproduzida em sessao publica com `POST /resultadoCompleta.do`
  seguido de `GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>`.
- Limite remoto observado: 10 resultados por pagina; a capacidade de coleta
  vem da navegacao por paginas, nao do aumento artificial de `page_size`.

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
- Inteiro teor: suportado quando a rota publica de arquivo responder.

## Comportamento observado

- Busca com resultado: HTML CJSG parseado pelo provider.
- Busca sem resultado: deve ser separada de erro.
- Controle de acesso: captcha/login deve interromper o fluxo.
- Risco: alto-medio por variacao e-SAJ.

## Fixtures

- [ ] Busca com resultado.
- [ ] Busca vazia.
- [ ] Inteiro teor.
- [ ] Controle de acesso.
- [ ] Paginacao.

## MCP e agentes

- Quando usar: pesquisa de jurisprudencia publica do TJAM.
- Quando pular: quando a fonte retornar bloqueio, login ou resposta sem
  resultado parseavel.
- Mensagem segura: "A consulta usa rotas publicas do TJAM/CJSG e preserva
  `SourceTrace`."
- Riscos: instabilidade de HTML e-SAJ e eventual controle de acesso.

## Proximos passos

- [ ] Criar fixture propria do TJAM.
- [ ] Validar labels amazonenses contra parser compartilhado.
- [ ] Validar inteiro teor e resposta vazia.

## Validacao live de capacidade - 2026-08-16

- Consulta: `responsabilidade civil`, duas paginas, 20 itens solicitados.
- Pagina 1: 10 resultados, 10 identificadores unicos, 10 com data.
- Pagina 2: 10 resultados, nenhum identificador repetido, 10 com data.
- Total remoto observado: 39.557.
- Estado: `valid_with_source_page_limit`; a fonte impoe uma janela de 10 itens.
- A mesma janela foi confirmada na Wave 2, com 30 IDs unicos em tres paginas.
- Inteiro teor: capacidade declarada como chamada sob demanda; depende de a
  rota publica `getArquivo.do` responder sem controle adicional.

Evidencia estruturada: `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.json`.
