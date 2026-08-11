# `tjmt_jurisprudencia_api`

## Identidade

- Fonte oficial: Jurisprudencia publica do TJMT.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `spa_api_jurisprudencia`.
- URL inicial: `https://jurisprudencia.tjmt.jus.br/`.
- Status de acesso: `blocked_or_inconclusive` na revalidacao de 2026-08-11.
- Status no NanoJuris: candidato, ainda sem provider implementado.

## Contrato HTTP

- SPA publica observada:
  - `GET /`
  - `GET /main.4fbae9a9bb684a741e57.bundle.js`
- Rotas inferidas do bundle:
  - `https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/<tipoConsulta>`
  - `/jurisprudencia/api/termo/<termo>`
  - `/jurisprudencia/api/consulta/relator?Quantidade=1000`
  - `/jurisprudencia/api/consulta/orgao-julgador?Quantidade=100`
  - `/jurisprudencia/api/consulta/classe?Quantidade=100`
  - `/jurisprudencia/VisualizaRelatorio/RetornaDocumentoAcordao`
- Probe direto em `/api/consulta/1`: HTTP 401 `No API key found in request`.
- Header/chave: existe indicio de header publico emitido pelo frontend; precisa
  validar antes de qualquer provider.

## Revalidacao atual

Em 2026-08-11, o `GET /` respondeu HTTP 200, mas redirecionou para
`/ui/login`. A pagina final carregou apenas scripts de login e nao expoe a SPA
de pesquisa nem um bundle atual com contrato de jurisprudencia. Isso invalida
a classificacao anterior de "portal publico" para esta janela. A API inferida
continua sem evidencia de consulta publica reproduzivel e nao deve ser chamada
com chave presumida ou credencial.

## Dados retornados

- Campos esperados:
  - acordao;
  - relator;
  - orgao julgador;
  - classe;
  - termo;
  - documento/acordao em relatorio.
- Campos canonicos esperados: `CanonicalDecision`.
- Inteiro teor: possivel por rota de relatorio, ainda nao validado.

## Comportamento observado

- GET do portal: HTTP 200 com redirecionamento final para `/ui/login` na
  revalidacao atual.
- API sem header: HTTP 401.
- Busca com resultado: nao reproduzida ainda.
- Risco: alto; a superficie atual exige login e o contrato publico anterior
  nao foi reproduzido.

## Fixtures

- [ ] Bundle publico revisado com rotas relevantes.
- [ ] HAR de busca real.
- [ ] JSON de resultado.
- [ ] JSON vazio.
- [ ] Erro 401 sem header.

## MCP e agentes

- Quando usar: somente depois de uma nova superficie publica e payload
  reproduzivel serem confirmados.
- Quando pular: enquanto o portal redirecionar para login ou a API retornar 401.
- Mensagem segura: "A superficie atual do TJMT exige login; nao foi localizada
  uma rota publica de jurisprudencia reproduzivel nesta verificacao."
- Riscos: promover header de frontend sem validar natureza publica e
  reproduzivel.

## Validacao live 2026-08-11

- Portal respondeu HTTP 200, mas redirecionou para `/ui/login`; API inferida sem chave respondeu HTTP 401.
- Nenhum header ou chave foi presumido. O candidato permanece bloqueado/inconclusivo.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Proximos passos

- [ ] Capturar HAR de busca simples.
- [ ] Identificar headers minimos enviados pelo frontend.
- [ ] Validar endpoint de metadados.
- [ ] Validar endpoint de busca e documento.
