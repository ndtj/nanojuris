# TJSE - Pesquisa de Jurisprudencia Judicial

## Authorized human-token path (2026-09-11)

The adapter exposes `search_authorized(query, turnstile_token=...)` for a token
obtained legitimately through the official UI. The token is accepted only for
one bounded request; it is never solved, stored, replayed, or included in
`raw`/`SourceTrace`. Accepted records require a stable identifier and are
stamped with `degree=second`, `instance=second`, `branch=state`, and
`collection=CJSG`.
The session cache also exposes `get_decisions()` for an observed authorized
record; it never fabricates an independent detail route.

This path has not been validated with an authorized live result yet, so TJSE
remains outside the default federation. Without a token, the normal search
continues to report access control rather than an empty result.

Status atual: `blocked_or_inconclusive` para busca decisoria automatizada.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado de Sergipe.
- Portal oficial: `https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial`.
- Superficie de pesquisa: `https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse`.
- Categoria: jurisprudencia judicial estadual.
- O portal principal carrega a pesquisa em um `iframe`.

## Fluxo Observado

A superficie de pesquisa responde com um formulario JSF/PrimeFaces publico,
contendo filtros para:

- termo livre, numero do processo e numero CNJ;
- acordaos ou decisoes monocraticas;
- segundo grau ou turma recursal;
- relator, orgao julgador e classe processual;
- periodo de distribuicao ou julgamento;
- pesquisa na ementa e no voto.

O formulario usa `POST` para a propria rota, `javax.faces.ViewState` dinamico e
uma sessao `JSESSIONID` criada no carregamento inicial. Esses valores devem ser
obtidos por sessao e nunca ficar hardcoded.

## Reproducao Controlada

Com uma sessao HTTP nova, foi reproduzido:

1. `GET` da superficie de pesquisa.
2. Leitura do formulario e do `javax.faces.ViewState` atual.
3. `POST` com o termo `dano moral`, tipo `AC`, competencia `SG` e botao de
   pesquisa.

O retorno foi HTTP 200 e a pagina continuou contendo os filtros, mas o resultado
funcional foi a mensagem `Captcha invalido`. Nao houve decisoes, ementas ou
links de inteiro teor reproduziveis na sessao automatizada.

## Decisao De Mapeamento

Classificacao: `blocked_or_inconclusive`.

O formulario e uma evidencia relevante de uma base jurisprudencial publica,
mas a rota de resultados ainda nao esta validada para uso automatizado sem a
etapa de protecao. O NanoJuris nao deve simular ou contornar captcha, Turnstile,
tokens de desafio ou controles de frequencia.

## Promocao Futura

Para mudar para `candidate_ready`, sera necessario um HAR limpo do fluxo normal
realizado por um usuario, contendo:

- requisicao de busca com token emitido legitimamente pela pagina;
- resposta com pelo menos uma decisao real;
- processo, classe, orgao, relator, datas, ementa e link de inteiro teor,
  quando publicados;
- paginacao ou limite de resultados;
- comportamento de busca vazia e de erro.

Cookies pessoais, credenciais e tokens de sessao nao devem ser versionados.

## Validacao live 2026-08-16

- O formulario JSF respondeu HTTP 200 e confirmou filtros, ViewState, datas e botoes de pesquisa.
- A superficie tambem referencia Cloudflare Turnstile. A busca automatizada
  continuou sem resultado juridico reproduzivel, e nenhuma busca foi promovida
  sem token humano autorizado.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Pagina de jurisprudencia judicial do TJSE](https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial)
- [Pesquisa de jurisprudencia do TJSE](https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse)
- [Regimento Interno do TJSE](https://www.tjse.jus.br/portal/arquivos/documentos/publicacoes/legislacao/tjse/novo_regimento_interno_tjse.pdf?v=18032024)
## Contrato E Dados

Filtros de interface confirmados: termo livre, numero do processo/CNJ, tipo acordao ou decisao monocratica, segundo grau ou turma recursal, relator, orgao, classe, periodo de distribuicao/julgamento e busca na ementa/voto. O POST, ViewState, sessao e tipo AC/SG foram observados, mas o payload de resultado, paginacao, total, detalhe e inteiro teor nao foram validados porque a protecao retornou Captcha invalido.

## MCP

O MCP deve manter TJSE fora da busca automatica e informar blocked_or_inconclusive. Nao simular Turnstile, nao armazenar token humano e nao transformar a resposta de captcha em busca vazia. Uma futura fixture deve comprovar resultado real, vazio e documento antes da promocao.
## Dados

Filtros confirmados: termo, processo/CNJ, acordao ou decisao monocratica,
segundo grau ou turma recursal, relator, orgao, classe, periodo e ementa/voto.
Nenhum schema decisorio foi validado porque a protecao respondeu Captcha invalido.

## Contrato

O POST JSF e ViewState foram observados, mas payload, pagina, total, detalhe e
inteiro teor nao foram reproduzidos sem desafio.

## Capacidade documental

`full_text_access=access_blocked`: a fonte pode oferecer documentos, mas a
unica rota observada esta atras do Turnstile. Isso e diferente de
`not_offered_by_source` e nao autoriza substituir o texto por ementa.

## Adapter de diagnostico

O modulo `nanojuris.providers.tjse_jurisprudencia` executa a descoberta GET,
valida o escopo de segundo grau e levanta `AccessControlRequiredError` quando
detecta Turnstile. Ele nao submete tokens nem anuncia a fonte na federacao.

Evidencia live bounded: [tjse-jurisprudencia-live-20260906.json](../../docs/provider-discovery/tjse-jurisprudencia-live-20260906.json).

## Superfície pública alternativa

O TJSE também publica o **Boletim Jurídico de Ementas** no Diário da Justiça:
`https://diario.tjse.jus.br/revista/internet/pesquisar.wsp`. Essa superfície
permite localizar edições e seções de câmaras, seção especializada e tribunal
pleno sem o Turnstile da pesquisa judicial. O adapter independente
`tjse_boletim_jurisprudencia` extrai as ementas e os links públicos de acórdão,
com escopo explícito `degree=second`/`instance=second`.

Essa publicação é uma coleção de ementas (não o voto integral) e o total entre
edições é desconhecido. Por isso ela permanece opt-in para federação até que o
gate de completude entre edições seja fechado; a pesquisa judicial protegida
continua diagnosticamente bloqueada.
### Metadados pÃºblicos do formulÃ¡rio (2026-09-10)

O GET oficial continua respondendo HTTP 200 e entrega o vocabulÃ¡rio de filtros
JSF (classes, relatores, Ã³rgÃ£os, tipo documental, competÃªncia e perÃ­odo) antes
da submissÃ£o. O adapter expÃµe esse vocabulÃ¡rio via `get_catalog` e
`get_filter_catalog`, mas preserva `challenge_required_for_search=true`: os
metadados nÃ£o sÃ£o resultados e nÃ£o alteram o bloqueio Turnstile.

EvidÃªncia: `docs/provider-discovery/tjse-public-form-metadata-live-20260910.json`.
