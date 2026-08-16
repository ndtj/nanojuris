# `tjms_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia CJSG/e-SAJ do TJMS.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://esaj.tjms.jus.br/cjsg`.
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
- Inteiro teor: suportado quando `getArquivo.do` estiver publico.

## Comportamento observado

- Busca com resultado: usa parser compartilhado da familia CJSG/e-SAJ.
- Busca sem resultado: deve retornar vazio.
- Controle de acesso: sem bypass.
- Risco: medio-alto por variacao e-SAJ.

## Fixtures

- [ ] Busca com resultado.
- [ ] Busca vazia.
- [ ] Inteiro teor.
- [ ] Controle de acesso.
- [ ] Paginacao.

## MCP e agentes

- Quando usar: pesquisa de jurisprudencia publica do TJMS.
- Quando pular: se houver captcha, login ou pagina de sessao vazia.
- Mensagem segura: "A consulta usa jurisprudencia publica do TJMS/CJSG e
  preserva metadados de origem."
- Riscos: tratar bloqueio como erro de parser.

## Proximos passos

- [ ] Completar fixture propria de TJMS.
- [ ] Validar diferencas de labels em relator/orgao/data.
- [ ] Aprofundar inteiro teor e paginacao.

## Validacao live de capacidade - 2026-08-16

- Consulta: `responsabilidade civil`, duas paginas, 20 itens solicitados.
- Pagina 1: 20 resultados, 20 identificadores unicos, 20 com data.
- Pagina 2: 20 resultados, nenhum identificador repetido, 20 com data.
- Total remoto observado: 229.013.
- Estado: `valid` para a paginacao observada.
- Inteiro teor: capacidade declarada como chamada sob demanda; depende de a
  rota publica `getArquivo.do` responder sem controle adicional.

Evidencia estruturada: `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.json`.
