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
- Paginacao: herdada da familia CJSG/e-SAJ; precisa fixture propria.

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
