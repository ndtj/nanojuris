# tjgo_projudi_jurisprudencia

## Identidade

- Fonte oficial: PROJUDI/TJGO - Consulta de Jurisprudencia.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `projudi_jurisprudencia`.
- URL inicial: `https://projudi.tjgo.jus.br/ConsultaJurisprudencia`.
- Status de acesso: busca publica validada em sessao limpa em 2026-08-07.
- Status no NanoJuris: provider promovido tecnicamente para CJSG (segundo grau)
  e CJPG (primeiro grau); a aprovação jurídica permanece uma etapa externa.

## Contrato HTTP

- Rotas:
  - `GET /ConsultaJurisprudencia`
  - `POST /ConsultaJurisprudencia`
  - `POST /ConsultaJurisprudencia?PaginaAtual=1&Id_Arquivo=<id>&g-recaptcha-response=` implementado para o `get_document` (sem resolver token; formulario/bloqueio continua erro explicito).
- Metodos: `GET` para formulario; `POST` para resultados.
- Parametros obrigatorios minimos do POST validado:
  - `PaginaAtual=2`
  - `PosicaoPaginaAtual=0`
  - `Texto=<termo>`
  - `Id_Instancia=15` (segundo grau) ou `Id_Instancia=16` (primeiro grau)
  - `Id_Area=0`
  - `Id_ServentiaSubTipo=0`
  - `Localizar=Consultar`
- Parametros opcionais:
  - `Viewstate`
  - `Id_Serventia`
  - `Id_Usuario`
  - `Id_ArquivoTipo`
  - `ProcessoNumero`
  - `DataInicial`
  - `DataFinal`
  - `g-recaptcha-response`
- Paginacao: payload inicial usa `PaginaAtual` e `PosicaoPaginaAtual`; troca de pagina em escala ainda deve ser validada em teste live opt-in.
- Ordenacao: nao mapeada.
- Filtros: texto, instancia, area, orgao/materia, serventia, magistrado, tipo de ato, processo e datas. O adapter aplica escopo estrito de segundo grau quando nenhum escopo é informado. Para `collection=CJPG`, envia `Id_Instancia=16` e só aceita cartões com unidade de primeiro grau (vara, juizado, comarca, ofício ou UPJ).

## Dados retornados

- Campos extraidos pelo provider: numero CNJ, magistrado/relator, orgao/unidade, tipo de ato, data/hora de publicacao, inteiro teor embutido no card e `Id_Arquivo`.
- Campos canonicos: `CanonicalDecision`.
- Campos opcionais: quantidade de ocorrencias no inteiro teor, unidade judicial e id de arquivo.
- Campos instaveis: estrutura HTML de cards e textos longos sem separadores claros.
- Tipo de ato: reconhecido semanticamente entre os campos do card; a data de
  publicacao nao e usada como `decision_type` quando a ordem do HTML variar.
- Inteiro teor: presente no proprio HTML de resultado no probe com `dano moral`.
- Documentos vinculados: botao `Baixar Inteiro teor` com `Id_Arquivo`; o adapter oferece fetch explicito e valida o bloco publico `.conteudoTexto`.
- `supports_full_text` e verdadeiro para texto embutido no card (`inline_result_text`) e para `get_document(id)` quando a rota devolve o documento.

## Comportamento observado

- Busca com resultado: `Texto=dano moral`, HTTP 200, `1357644 resultados encontrados`, processo, decisao, sentenca e `Baixar Inteiro teor`.
- Busca sem resultado: fixture real de `zzznanojurissemresultado` sem cards de resultado.
- Erro HTTP esperado: normalizado em testes offline para HTTP 400/429/500 e falhas de rede.
- Controle de acesso/captcha: scripts globais aparecem no HTML, mas nao bloquearam o resultado testado; o diagnostico diferencia asset global de desafio real.
- Mudanca de layout: risco alto por HTML de sistema processual.

## Fixtures

- Sucesso: `tests/fixtures/tjgo_projudi_dano_moral.html`.
- Vazio/formulario sem cards: `tests/fixtures/tjgo_projudi_empty.html`.
- Erro: coberto por respostas fake em `tests/test_tjgo_projudi_jurisprudencia.py`.
- Documento: `tjgo_result_to_document(result)` converte o texto embutido; `get_document(file_id)` busca a rota oficial e gera bytes, hash, MIME, texto e `SourceTrace`.

## MCP e agentes

- Quando usar: consultas amplas de atos/jurisprudencia TJGO por termo ou processo.
- Quando pular: quando o fluxo passar a exigir captcha, token obrigatorio ou sessao autenticada.
- Mensagem segura para o usuario: "A busca retorna conteudo publico do PROJUDI/TJGO; o inteiro teor foi extraido do resultado HTML quando disponivel."
- Riscos: resultados muito grandes, documentos pessoais em decisoes publicas e HTML volumoso. O provider preserva o texto publico retornado pela fonte; qualquer politica de minimizacao deve ser camada de consumo, nao redaction silenciosa do provider.

## Proximos passos

- [x] Criar fixture real de sucesso e fixture real de vazio/formulario sem cards.
- [x] Implementar parser offline antes do fetcher.
- [x] Validar uma janela live bounded com identidade, trace, total e texto.
- [x] Validar uma segunda pagina em teste live opt-in; `PosicaoPaginaAtual=1` retorna janela distinta.
- [x] Testar `ProcessoNumero` com numero publico e confirmar vazio explicito.
- [x] Implementar download por `Id_Arquivo` sem contornar captcha; respostas que
  voltam ao formulário são classificadas como mudança de contrato.
## Mapeamento canonico

Resultados PROJUDI preenchem `authority=TJGO`, `branch=state`, `judging_body` e
`document_type`. O escopo `CJSG` usa `Id_Instancia=15` e aceita apenas
Câmara/Desembargador; o escopo `CJPG` usa `Id_Instancia=16` e aceita apenas
vara/juizado/comarca/ofício/UPJ. Assim, os bindings preenchem respectivamente
`degree=second`/`instance=second`/`collection=CJSG` ou
`degree=first`/`instance=first`/`collection=CJPG`; o valor original permanece
em `raw`.

## Rechecagem técnica — 2026-09-05

- A paginação foi corrigida: o formulário mantém `PaginaAtual=2` e usa
  `PosicaoPaginaAtual` zero-based. As páginas 1, 2 e 3 foram reproduzidas
  com resultados não sobrepostos; o filtro por processo e o vazio explícito
  também foram validados.

Uma chamada pública bounded com `responsabilidade` retornou HTTP 200, um
registro textual, total remoto 39.272, hash de conteúdo, tamanho e latência no
`SourceTrace`. O provider continua sujeito a validação adicional de paginação,
download por `Id_Arquivo` e revisão de licença/retencão.

## Fechamento técnico CJSG — 2026-09-06

- Evidência live: `docs/provider-discovery/tjgo-cjsg-live-20260906-cycle58.json`.
- Duas páginas bounded (`page_size=2`) retornaram HTTP 200, total remoto 14.032,
  quatro identificadores distintos, relatores Desembargador e órgãos Câmara Cível.
- O adapter promove esses registros para `degree=second`, `instance=second` e
  `collection=CJSG`, preservando rastros e rejeitando cartões sem evidência
  inequívoca de segundo grau.

## Fechamento técnico CJPG — 2026-09-06

- Evidência live: `docs/provider-discovery/tjgo-cjpg-live-20260906.json`.
- `Id_Instancia=16` retornou HTTP 200, total remoto 21 e decisões textuais de
  primeiro grau em duas páginas bounded sem sobreposição. Os cartões expõem
  processo, unidade judicial, magistrado, data e `.conteudoTexto`.
- O parser promove somente cartões com marcador de vara/juizado/comarca/ofício
  ou UPJ, rejeitando Câmara/Desembargador; o resultado fica em
  `degree=first`, `instance=first`, `collection=CJPG` e `source_origin=16`.

Rechecagem bounded de 2026-09-10: `dano moral` retornou HTTP 200, um registro
de segundo grau e total 19.743; a resposta continua sendo uma janela parcial.
Evidência: `docs/provider-discovery/tjgo-projudi-live-20260910-continue.json`.
