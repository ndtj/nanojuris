# `falcao_jt`

## Official API contract (2026-09-11)

The public Angular configuration exposes the backend
`https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api`.
The adapter now implements the documented `GET /no-auth/pesquisa` contract,
including `texto`, `colecao`, pagination, date, court, rapporteur, judicial
class and ementa parameters. It parses `documentos` and
`quantidadeTotal`, preserves full text when present, and supports detail from
an observed result without storing credentials.

The same API returned HTTP 403 during the current bounded probe. Therefore the
provider remains a diagnostic candidate and is not federated. HTTP 403 is
reported as access control, never as an empty search.

## Identidade

- Fonte institucional: Sistema Falcao da Justica do Trabalho.
- Gestao/normalizacao: TRT9 em parceria com CSJT.
- Categoria: `court_jurisprudence`.
- URL publica conhecida: `https://jurisprudencia.jt.jus.br/`.
- Status de acesso no probe NanoJuris: bloqueado/inconclusivo.
- Status no NanoJuris: candidato de alta prioridade, sem provider.

O Falcao deve ser investigado como uma fonte nacional da Justica do Trabalho,
e nao como um provider isolado do TRT9. A comunicacao institucional informa
que o repositorio reune documentos de primeiro e segundo graus, TST e
precedentes qualificados. A cobertura efetiva e o contrato tecnico precisam
ser confirmados na interface e nas respostas reais.

## Evidencia institucional

As paginas oficiais do TRT9 e do CNJ descrevem o Falcao como repositorio
oficial/nacional da jurisprudencia trabalhista, com consulta para o publico em
geral. Os tipos mencionados incluem sentencas, acordaos, decisoes de
admissibilidade de recurso de revista, decisoes monocraticas e precedentes.

## Probe tecnico

Em 2026-08-10, uma requisicao GET limpa para a raiz publica respondeu:

- HTTP 403;
- pagina de bloqueio CloudFront;
- nenhum resultado ou contrato de API observavel;
- sem login ou captcha visivel, mas com `request_blocked`.

Esse resultado pode ser especifico do ambiente, da rede ou de uma politica
temporaria da distribuicao. Nao e evidencia suficiente para afirmar que a
fonte exige autenticacao, nem autoriza contornar o bloqueio.

## Contrato pendente

Ainda precisam ser descobertos e validados:

- rota de entrada e arquivos JavaScript publicos;
- endpoint de pesquisa, metodo e payload;
- filtros por tribunal, classe, tipo documental e datas;
- paginacao, ordenacao e total de resultados;
- identificador e URL de detalhe/inteiro teor;
- limites de requisicao e politica de acesso automatizado;
- formato de exportacao, se houver.

## Decisao de engenharia

- Nao implementar parser ou bypass com base apenas em pagina institucional.
- Nao reutilizar cookies, tokens ou sessao de navegador para contornar 403.
- Priorizar um HAR obtido por consulta publica normal, sem credenciais, para
  fechar o contrato.
- Se o bloqueio persistir, registrar a fonte como indisponivel para o provider
  e manter TST como fonte independente.

## Proximos passos

1. Repetir um GET de baixa frequencia em outra janela controlada.
2. Capturar HAR de uma busca publica curta, se o acesso normal estiver
   disponivel no navegador do mantenedor.
3. Inspecionar somente assets e chamadas publicas do proprio fluxo.
4. Criar fixtures de sucesso, vazio e bloqueio antes de qualquer provider.
5. Avaliar se o Falcao pode substituir parte da coleta individual de TRTs,
   preservando `SourceTrace` com a origem tribunal/documento.

## Validacao live 2026-08-11

- GET da raiz respondeu HTTP 403 com pagina CloudFront; nenhuma rota de busca foi chamada com bypass.
- O candidato permanece bloqueado/inconclusivo e depende de nova evidencia publica normal ou HAR sem credenciais.

## Rechecagem bounded 2026-09-07

- A pagina oficial do TRT9 respondeu HTTP 200 e confirmou o link nacional e o escopo de primeiro e segundo graus.
- A raiz do Falcao respondeu HTTP 200 em uma requisicao GET comum, mas entregou somente o shell Angular, sem contrato de resultados.
- Uma requisicao de navegador comum recebeu HTTP 403 de CloudFront; a disponibilidade e intermitente entre bordas/clientes.
- Um asset lazy esperado como JavaScript retornou o shell HTML, portanto a aplicacao nao pode ser validada de forma reproduzivel nessa janela.
- Nenhum token, cookie, proxy, alteracao de TLS ou outra tecnica de bypass foi usado.
- Evidencia: `docs/provider-discovery/falcao-trt2-live-recheck-20260907.json`.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Rechecagem bounded 2026-09-08

- A raiz `jurisprudencia.jt.jus.br` respondeu HTTP 403 com página de bloqueio
  CloudFront em chamada GET limpa.
- A página institucional do TRT9 respondeu HTTP 200 e confirmou a referência
  oficial ao Falcão, mas não forneceu uma rota decisória reproduzível.
- Corpos completos não foram persistidos; somente status, tamanho, hash e
  classificação foram registrados em
  `docs/provider-discovery/falcao-live-recheck-20260908.json`.
- Nenhum cookie, token, proxy, alteração TLS ou técnica de evasão foi usado.

O candidato continua `blocked_external`. A próxima ação legítima é solicitar
API, exportação ou allowlist ao responsável pela fonte.

## Referencias oficiais

- https://www.trt9.jus.br/portal/pagina.xhtml?pagina=FALCAO&secao=168
- https://www.cnj.jus.br/conheca-o-falcao-o-repositorio-oficial-de-jurisprudencia-da-justica-do-trabalho/
- https://jurisprudencia.jt.jus.br/

## Adapter diagnostico opt-in — 2026-09-10

`nanojuris.providers.falcao_jt.FalcaoJtProvider` agora executa uma sondagem
GET bounded pela origem oficial usando `SharedHttpClient`. HTTP 403/CloudFront
vira `AccessControlRequiredError`; o shell Angular sem contrato vira
`ParserContractChangedError`. Não há `SearchPage` sintético, parser de
documentos ou federação padrão. O provider só aparece com
`NanoJurisClient(include_candidate_providers=True)` e permanece candidato até
que a autoridade forneça uma API, exportação ou allowlist pública reproduzível.

Fixtures e testes: `tests/fixtures/falcao_cloudfront.html`,
`tests/fixtures/falcao_shell.html` e `tests/test_falcao_jt.py`.

Uma resposta JSON com `documentos=[]` sem `quantidadeTotal` autoritativo é
tratada como janela vazia não confirmada (`total_known=false`,
`is_complete=false`, extração `partial`). Somente `quantidadeTotal=0`
confirma ausência de resultados.
## Dados E Campos Do Contrato

Nenhum payload decisorio foi obtido na janela validada. Os campos esperados, a confirmar, sao tribunal de origem, grau, classe, tipo documental, numero, relator, orgao, data, ementa, texto e URL de documento. A cobertura anunciada inclui sentencas, acordaos, decisoes monocraticas, admissibilidade de recurso de revista e precedentes, mas isso e escopo institucional, nao resposta tecnica reproduzida.

## MCP

O MCP deve omitir o Falcao da busca executavel enquanto a disponibilidade for intermitente ou nao houver contrato de resultados reproduzivel. Pode expor a fonte como blocked_or_inconclusive, com o motivo e a data da verificacao. Nunca reutilizar cookies, tokens ou contornar CloudFront.

## Rechecagem do backend oficial (2026-09-10)

## Estado atual do adapter (2026-09-11)

Existe um `FalcaoJtProvider` opt-in com parser independente para o contrato
JSON observado (`documentos` e `quantidadeTotal`), paginacao, catalogo de TRTs
e detalhe somente de resultados observados. A busca live bounded de 2026-09-11
respondeu HTTP 403 no endpoint oficial; o adapter permanece candidato, fora da
federacao padrao. O 403 e preservado como `access_control_required`, nunca como
resultado vazio.

O `config.json` público do frontend confirmou um backend próprio e autenticação
OIDC por redirecionamento. Sondas GET bounded sem credenciais em `/`,
`/swagger-ui/index.html`, `/v3/api-docs` e `/documentos` responderam HTTP 401.
Não foi observado endpoint anônimo de busca ou exportação e nenhum corpo
decisório foi obtido. A evidência está em
`docs/provider-discovery/falcao-backend-contract-live-20260910.json`.

401 é classificado como autenticação necessária, não como resultado vazio. O
provider continua candidato, diagnóstico e fora da federação; não automatiza
login, não reutiliza sessão pessoal e não tenta contornar o controle.

## Busca autorizada OIDC (2026-09-11)

`search_authorized` aceita somente um token OIDC Bearer fornecido pelo chamador
após autenticação oficial. O adapter não realiza login, não armazena ou renova
tokens, não reutiliza cookies e não contorna controles de acesso. O token é
efêmero, permanece fora de `raw`/`SourceTrace` e o corpo é processado pelo
mesmo parser da rota pública.

Esse caminho não altera a classificação do provider: sem resposta autorizada
reproduzível e fixtures de contrato, ele permanece candidato/opt-in.
