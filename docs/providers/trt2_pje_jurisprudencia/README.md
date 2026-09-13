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

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos
- [ ] Descobrir contrato completo de filtros sem executar busca bloqueada.
- [ ] Criar fixture de `/opcoes`.
- [ ] Criar teste de classificacao `tokenDesafio`/`imagem`.
- [ ] Mapear outros TRTs que usam o mesmo backend e separar bloqueio CloudFront de desafio PJe.

## Auditoria de contrato 2026-08-28

- O shell oficial e `GET /juris-backend/api/opcoes` responderam HTTP 200.
- `GET /juris-backend/api/token` respondeu sem corpo util.
- Uma chamada publica controlada a `POST /juris-backend/api/documentos`
  retornou `tokenDesafio` e `imagem`, sem documentos.
- Portanto, nao ha contrato reproduzivel de resultados para promover como
  `CanonicalDecision`; nenhuma implementacao foi adicionada nesta rodada.

## Rechecagem bounded 2026-09-07

- O shell e `/juris-backend/api/opcoes` continuaram publicos (HTTP 200).
- As opcoes mantem `captchaOption=2`; a rota `/juris-backend/api/token` respondeu 200 sem corpo util.
- Nenhum contrato de resultados foi obtido sem desafio; o candidato permanece fora do runtime.
- Evidencia: `docs/provider-discovery/falcao-trt2-live-recheck-20260907.json`.

## Descoberta de API e filtros - 2026-09-08

O bundle oficial da versao `1.5.0-i1` confirmou o backend
`https://pje.trt2.jus.br/juris-backend/api`. Uma chamada bounded a
`POST /filtros` respondeu HTTP 200 com agregacoes publicas para assunto, ano,
tipo documental, instancia, orgao julgador, colegiado, meio de tramitacao,
magistrado e classe judicial. A chamada a `POST /documentos` respondeu com
`tokenDesafio`, imagem e audio, sem documentos. O contrato de resultados
continua bloqueado por desafio humano; a resposta nao pode ser tratada como
lista vazia. Evidencia redigida:
`docs/provider-discovery/trt2-jurisprudencia-api-live-20260908.json`.

Fixtures sanitizadas da descoberta: `tests/fixtures/trt2_pje_opcoes.json`,
`tests/fixtures/trt2_pje_filtros.json` e
`tests/fixtures/trt2_pje_challenge.json`. Testes de classificação:
`tests/test_trt2_route_evidence.py`.

## Adapter opt-in de diagnostico — 2026-09-10

Foi adicionada a classe `Trt2PjeJurisprudenciaProvider` para tornar executavel
o contrato publico que pode ser comprovado sem desafio: `GET /opcoes` e
`POST /filtros`. A rota `POST /documentos` tambem e transportada com limite de
bytes, mas qualquer resposta com `tokenDesafio`, `imagem` ou `audio` gera
`AccessControlRequiredError`; ela nunca e convertida em vazio e nenhum token,
cookie ou sessao humana e reutilizado.

O adapter esta disponivel somente em
`NanoJurisClient(include_candidate_providers=True)`, com
`supports_unified_search=false`. Isso implementa o diagnostico do provider sem
afirmar que a busca de decisoes ou a paginacao estao disponiveis. Os testes
sanitizados estao em `tests/test_trt2_pje_jurisprudencia.py`.

## Rechecagem do contrato de filtros - 2026-09-10

O bundle oficial `1.5.0-i1` foi usado somente para reproduzir o formato
publico `QUERY_INICIAL`. O adapter agora envia esse formato para `/filtros` e
`/documentos`, incluindo `andField`, `orField`, `notField`,
`paginationPosition`, `paginationSize`, `tipoDocumento`, `classeJudicial` e
as datas de publicacao. Uma sonda bounded a `/filtros` retornou HTTP 200 com
agregacoes publicas. `/documentos` continua retornando `tokenDesafio`/imagem/
audio; nenhum desafio foi resolvido ou reutilizado e o provider permanece
opt-in. Evidencia: `docs/provider-discovery/trt2-pje-query-contract-live-20260910.json`.

## Busca autorizada por interacao humana - 2026-09-11

`search_authorized` aceita um `challenge_token` obtido pelo usuario no fluxo
oficial e o envia somente no corpo da chamada bounded a `/documentos`. O token
e removido do `SourceTrace`, nao e armazenado nem reutilizado. Quando o portal
retorna `documents`, o parser preserva identidade de TRT2, ramo trabalhista,
grau/instancia de segundo grau, ementa, datas, orgao, relator e campos `raw`.
Sem token, ou se o desafio persistir, o estado continua
`access_control_required`; o provider nao entra na federacao padrao.

Fixture sanitizada adicional: `tests/fixtures/trt2_pje_authorized_success.json`.

Uma resposta `documents=[]` sem `total` ou `hits` autoritativo representa
apenas uma janela vazia não confirmada: `is_complete=false` e extração
`partial`, tanto na busca pública quanto na chamada autorizada efêmera.
Somente contador autoritativo igual a zero confirma ausência de resultados.
