# trt2_pje_jurisprudencia

## Identidade
- Fonte oficial: PJe Jurisprudencia/TRT da 2a Regiao.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `pje_jurisprudencia`.
- URL inicial: `https://pje.trt2.jus.br/jurisprudencia/`.
- Status de acesso: frontend e opcoes publicas; documentos bloqueados por desafio no probe limpo de 2026-08-07.

## Contrato HTTP
- Frontend:
  - `GET https://pje.trt2.jus.br/jurisprudencia/`
- Endpoints observados no bundle publico:
  - `GET /juris-backend/api/opcoes`
  - `POST /juris-backend/api/filtros`
  - `POST /juris-backend/api/documentos`
  - `GET /juris-backend/api/token`
- Host base observado: `https://pje.trt2.jus.br`.

## Dados retornados
- `GET /juris-backend/api/opcoes` retorna JSON com:
  - regional;
  - URL de consulta processual PJe;
  - versao;
  - configuracao de captcha.
- `POST /juris-backend/api/documentos` nao retornou documentos no fluxo limpo; retornou `tokenDesafio` e `imagem`.
- Campos canonicos possiveis: nenhum provider de `CanonicalDecision` deve ser ativado nesta fase.

## Comportamento observado
- Frontend: HTTP 200, SPA publica "Sistema de Jurisprudencia".
- Opcoes: HTTP 200, JSON publico.
- Filtros: `POST` com payload simples retornou erro de parametros.
- Documentos: `POST` com termo e pagina retornou desafio por imagem/token.
- Token: `GET /token` retornou HTTP 200 sem conteudo util.

## Decisao
- Documentar como contrato parcial P1/P2.
- Nao automatizar `documentos` enquanto houver `tokenDesafio`/`imagem`.
- O `probe-rota` deve classificar esse retorno como `access_control_or_login`.

## MCP e agentes
- Quando usar: diagnostico de fonte e explicacao de limites de acesso.
- Quando pular: pesquisas de jurisprudencia que exigem retorno de documentos.
- Mensagem segura para o usuario: "O portal responde publicamente, mas a rota de documentos exige desafio humano; o NanoJuris nao tenta contornar esse controle."

## Validacao live 2026-08-11

- Shell e `/juris-backend/api/opcoes` responderam HTTP 200; as opcoes incluem configuracao de captcha.
- A rota de documentos retorna `tokenDesafio`/imagem; nao houve coleta nem tentativa de contorno.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos
- [ ] Descobrir contrato completo de filtros sem executar busca bloqueada.
- [ ] Criar fixture de `/opcoes`.
- [ ] Criar teste de classificacao `tokenDesafio`/`imagem`.
- [ ] Mapear outros TRTs que usam o mesmo backend e separar bloqueio CloudFront de desafio PJe.
