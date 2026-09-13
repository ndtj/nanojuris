# TJAP - Tucujuris Jurisprudencia

Status atual: `blocked_or_inconclusive` para busca decisoria automatizada.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado do Amapa.
- Familia tecnica observada: Tucujuris, com portal institucional e paginas
  publicas de consulta.
- Entrada historica: `https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html`.
- Entrada alternativa observada: `https://services.tjap.jus.br/pages/consultar-jurisprudencia/consultar-jurisprudencia.html`.
- Categoria: jurisprudencia estadual, turmas recursais e sumulas.

## Evidencia Observada

Registro institucional do CNJ descreve uma consulta integrada ao Tucujuris para
decisoes da Turma Recursal, orgaos do tribunal e sumulas, com acesso ao inteiro
teor, copia do acordao e ponte para a movimentacao processual.

O mapeamento tecnico anterior observou:

- o host `services.tjap.jus.br` sem resolucao DNS no ambiente de teste;
- o host `tucujuris.tjap.jus.br` respondendo desafio de JavaScript/Cloudflare;
- nenhum contrato HTTP limpo de busca, detalhe ou documento reproduzivel.

Esses sinais provam a existencia da superficie, mas nao autorizam provider live.

## Decisao De Mapeamento

Classificacao: `blocked_or_inconclusive`, evidencia `B/C`.

O NanoJuris deve preservar o candidato e nao simular ou contornar desafio,
captcha, WAF ou sessao de navegador. O eventual provider deve separar sumulas,
acordaos, detalhe e movimentacao, pois a fonte pode expor contratos distintos.

## Promocao Futura

Exigir HAR publico sem credenciais, resposta de busca com um item real, detalhe,
inteiro teor e comportamento vazio. Depois, reproduzir a chamada por HTTP limpo
com headers minimos e criar fixtures offline.

## Validacao live 2026-08-16

- A entrada Tucujuris respondeu HTTP 403 na revalidacao limpa.
- O estado permanece bloqueado/inconclusivo; nao foi inferido endpoint a partir
  de resposta de busca.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Consulta Tucujuris](https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html)
- [Consulta alternativa](https://services.tjap.jus.br/pages/consultar-jurisprudencia/consultar-jurisprudencia.html)
- [Registro institucional do CNJ](https://www.cnj.jus.br/sistema-moderniza-busca-de-jurisprudencia-em-tribunal-do-amapa/)
## Contrato E Filtros

A interface/superficie foi identificada, mas nenhum metodo, payload, filtro, paginacao, ordenacao ou rota de detalhe foi reproduzido por HTTP limpo. Os escopos institucionais indicam filtros ou colecoes para tribunal, orgao, turma recursal, sumula e processo paradigma, mas os nomes e valores nao sao contrato confirmado.

## Dados E MCP

Nao ha resposta decisoria fixtureada. Os campos que deverao ser confirmados sao identificador, tipo, processo, orgao, ementa, inteiro teor e ponte de movimentacao. O MCP deve manter a fonte fora da busca automatica e diferenciar shell HTML, desafio e resposta juridica real.

## Contrato

A interface foi identificada, mas metodo, payload, filtros, paginacao,
ordenacao e detalhe nao foram reproduzidos por HTTP limpo. As referencias
institucionais a tribunal, orgao, turma recursal, sumula e processo paradigma
sao escopo, nao nomes de parametros confirmados.

## Dados

Nao existe resposta decisoria fixtureada. Confirmar identificador, tipo,
processo, orgao, ementa, inteiro teor e ponte de movimentacao quando houver
sessao publica reproduzivel.

## MCP

Manter fora da busca automatica e diferenciar shell HTML, desafio e resposta
juridica real.

## Diagnostico NanoJuris 2026-09-06

O adapter independente `tjap_tucujuris` agora reproduz o endpoint observado
no Juscraper (`POST /api/publico/consultar-jurisprudencia`) em modo opt-in. Ele
preserva o payload de filtros e converte a resposta de erro de "nenhum
resultado" em vazio autoritativo somente quando a própria fonte informa isso.
Respostas Turnstile/WAF continuam como `access_controlled`, sem bypass. A
evidência bounded está em
`docs/provider-discovery/juscraper-captcha-boundary-live-20260906.json`.
Fixtures sanitizadas: `tests/fixtures/tjap_tucujuris_empty.json` e
`tests/fixtures/tjap_tucujuris_access_control.json`.

### Rechecagem legítima (2026-09-06)

O portal e a rota REST continuam acessíveis apenas até a camada de aplicação:
uma requisição sem token recebeu envelope de erro e as tentativas seguintes
receberam página gerenciada do Cloudflare (`Just a moment...`). A busca exige
Turnstile validado no servidor. O estado permanece `access_controlled`; nenhum
token, cookie de desafio ou técnica de evasão foi utilizado.

### Alternativas oficiais rechecadas (2026-09-07)

A entrada oficial sem o prefixo legado respondeu HTTP 200 e confirmou que a
interface oferece consulta de acórdãos com filtros de órgão, número, classe,
origem, relator, secretaria e votação. A submissão pública bounded ao endpoint
documentado, porém, respondeu o envelope `A verificação de segurança falhou`;
isso é `access_controlled`, não vazio. A entrada legada também retornou apenas
o shell Angular, e o host `services.tjap.jus.br` não resolveu por DNS.

Evidência: `docs/provider-discovery/tjap-official-alternatives-live-20260907.json`.
Nenhum token, cookie de desafio, automação de navegador ou técnica de bypass foi
utilizado. O provider continua fora da federação até existir uma rota pública
reproduzível sem validação de desafio.

### Caminho autorizado com passe humano (2026-09-10)

O frontend oficial confirma que a rota `POST /api/publico/consultar-jurisprudencia`
recebe o passe Turnstile no campo JSON `captcha`. O adapter agora oferece
`search_authorized(query, turnstile_token=...)` para uma única chamada bounded
quando o passe for obtido pelo usuário no próprio portal. O passe não é gerado,
armazenado, renovado, reutilizado ou incluído em `SourceTrace`/`raw`.
Resultados autorizados observados ficam disponíveis em memória para
`get_decisions()` durante a mesma sessão; nenhuma rota de detalhe é presumida.

Isso não altera o estado de promoção: sem uma resposta autorizada reproduzível,
fixture de sucesso/detalhe e validação de inteiro teor, TJAP permanece
`candidate` e fora da federação padrão.

Rechecagem adicional de 2026-09-10: a API respondeu HTTP 200 com envelope
`ERRO` de verificacao de seguranca. O contrato autorizado observado no frontend
e o campo `captcha`, a lista `dados`, `offset` e as rotas de detalhe/exportacao;
isso nao constitui resultado live sem passe humano. Evidencia:
`docs/provider-discovery/candidate-live-recheck-20260910-continue.json`.
### Metadados pÃºblicos (2026-09-10)

Foram confirmadas duas rotas sem desafio no frontend oficial:
`GET /api/publico/carregar-filtros-combo-jurisprudencia`, que fornece
relatores, classes, origens e secretarias, e
`GET /api/publico/buscar-data-banco-dados-jurisprudencia`, que informa a data de
atualizaÃ§Ã£o do banco. O adapter expÃµe essas rotas via `get_catalog`,
`get_filter_catalog` e `get_last_update`; elas sÃ£o metadados e nÃ£o sÃ£o
consideradas resultados de busca.
EvidÃªncia bounded: `docs/provider-discovery/tjap-public-metadata-live-20260910.json`.
