# tjma_jurisconsult

## Identidade
- Fonte oficial: Jurisconsult/TJMA.
- Categoria: `court_jurisprudence` e `court_precedents` parcial.
- Familia tecnica: `tjma_jurisconsult`.
- URL inicial: `https://jurisconsult.tjma.jus.br/#/sg-jurisprudence-list`.
- API observada: `https://apijuris.tjma.jus.br/v1`.
- Status de acesso: metadados publicos; busca principal bloqueada por captcha no probe limpo.

## Contrato HTTP
- Rotas publicas auxiliares:
  - `GET /jurisprudencia/lista_relatorios`
  - `GET /jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=<id>`
  - `GET /jurisprudencia/lista_todos_classes?tipoRelatorio=<id>`
  - `GET /jurisprudencia/lista_todos_magistrados?tipoRelatorio=<id>`
  - `GET /jurisprudencia/lista_todos_camaras?tipoRelatorio=<id>`
  - `GET /jurisprudencia/lista_todos_comarcas?tipoRelatorio=<id>`
  - `GET /jurisprudencia/lista_todos_varas?comarca=<id>&tipoRelatorio=<id>`
  - `GET /jurisprudencia/links_pesquisa_sumulas`
- Rotas de busca retornadas por metadados:
  - `/sg/jurisprudencias/processos`
  - `/jurisprudencia/processos/pesquisa_acordaos_tr`
  - `/jurisprudencia/processos/pesquisa_monocraticas`
  - `/jurisprudencia/processos/pesquisa_monocraticas_tr`
  - `/jurisprudencia/processos/sentencas_pg`
  - `/jurisprudencia/processos/sentencas_je`
- Metodos: `GET`.
- Parametros obrigatorios da busca principal observada: `chave`, `tipoPesquisa`, `tokenG`, `keyId`.
- Paginacao: endpoint possui variante `/infinito` no bundle, mas depende de token/validacao.
- Ordenacao: nao mapeada.
- Filtros: relatorio, tipo de pesquisa, sistema, relator, revisor, classe, camara, comarca, vara, datas e frase exata.

## Dados retornados
- Campos extraidos nos metadados: relatorios, rotas, tipos de pesquisa, camaras, links de sumulas/IAC/IRDR.
- Campos canonicos: `CanonicalPrecedent` para links estaticos; `CanonicalDecision` apenas se busca principal tiver fluxo limpo no futuro.
- Campos opcionais: classes, magistrados, comarcas e varas.
- Campos instaveis: nomes de rota expostos pelo bundle e ids de filtros.
- Inteiro teor: nao validado para busca principal.
- Documentos vinculados: pendente.

## Comportamento observado
- Busca com resultado: nao promovida.
- Busca sem resultado: nao promovida.
- Erro HTTP esperado: `GET /sg/jurisprudencias/processos?...&tokenG=&keyId=` retornou HTTP 400 `captcha_not_provided`.
- Controle de acesso/captcha: presente na busca principal.
- Mudanca de layout: risco medio por SPA Ionic/Angular.

## Fixtures
- Sucesso: pendente para metadados.
- Vazio: pendente.
- Erro: `captcha_not_provided` pendente de fixture publica representativa.
- Documento: nao aplicavel nesta fase.

## MCP e agentes
- Quando usar: descoberta de catalogo, filtros, relatorios e links oficiais de sumulas/IAC/IRDR do TJMA.
- Quando pular: pesquisa textual de acordaos, monocraticas e sentencas enquanto exigir captcha.
- Mensagem segura para o usuario: "O Jurisconsult/TJMA tem API publica para metadados, mas a busca principal exige captcha e nao sera automatizada."
- Riscos: confundir metadado valido com provider completo de acordaos.

## Validacao live 2026-08-11

- Relatorios, links de sumulas, tipos, classes, magistrados e camaras responderam HTTP 200.
- A busca principal continua respondendo `captcha_not_provided`; catalogo nao deve ser apresentado como consulta de acordaos.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos
- [ ] Criar parser/contract para `lista_relatorios` e `links_pesquisa_sumulas`.
- [ ] Documentar links finais de Sumulas, IRDR e IAC.
- [ ] Manter busca principal em `ACCESS_CONTROL_REQUIRED`.
- [ ] Reavaliar apenas se surgir rota publica sem captcha.
