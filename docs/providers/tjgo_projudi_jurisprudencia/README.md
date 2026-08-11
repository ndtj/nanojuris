# tjgo_projudi_jurisprudencia

## Identidade

- Fonte oficial: PROJUDI/TJGO - Consulta de Jurisprudencia.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `projudi_jurisprudencia`.
- URL inicial: `https://projudi.tjgo.jus.br/ConsultaJurisprudencia`.
- Status de acesso: busca publica validada em sessao limpa em 2026-08-07.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas:
  - `GET /ConsultaJurisprudencia`
  - `POST /ConsultaJurisprudencia`
  - `POST /ConsultaJurisprudencia?PaginaAtual=1&Id_Arquivo=<id>&g-recaptcha-response=` pendente; voltou ao formulario no teste sem token.
- Metodos: `GET` para formulario; `POST` para resultados.
- Parametros obrigatorios minimos do POST validado:
  - `PaginaAtual=2`
  - `PosicaoPaginaAtual=0`
  - `Texto=<termo>`
  - `Id_Instancia=0`
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
- Filtros: texto, instancia, area, orgao/materia, serventia, magistrado, tipo de ato, processo e datas.

## Dados retornados

- Campos extraidos pelo provider: numero CNJ, magistrado/relator, orgao/unidade, tipo de ato, data/hora de publicacao, inteiro teor embutido no card e `Id_Arquivo`.
- Campos canonicos: `CanonicalDecision`.
- Campos opcionais: quantidade de ocorrencias no inteiro teor, unidade judicial e id de arquivo.
- Campos instaveis: estrutura HTML de cards e textos longos sem separadores claros.
- Inteiro teor: presente no proprio HTML de resultado no probe com `dano moral`.
- Documentos vinculados: botao `Baixar Inteiro teor` com `Id_Arquivo`, mas download separado ainda nao confirmado.

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
- Documento: o provider converte o texto embutido do resultado em documento canonico via helper; download separado segue pendente.

## MCP e agentes

- Quando usar: consultas amplas de atos/jurisprudencia TJGO por termo ou processo.
- Quando pular: quando o fluxo passar a exigir captcha, token obrigatorio ou sessao autenticada.
- Mensagem segura para o usuario: "A busca retorna conteudo publico do PROJUDI/TJGO; o inteiro teor foi extraido do resultado HTML quando disponivel."
- Riscos: resultados muito grandes, documentos pessoais em decisoes publicas e HTML volumoso. O provider preserva o texto publico retornado pela fonte; qualquer politica de minimizacao deve ser camada de consumo, nao redaction silenciosa do provider.

## Proximos passos

- [x] Criar fixture real de sucesso e fixture real de vazio/formulario sem cards.
- [x] Implementar parser offline antes do fetcher.
- [ ] Validar paginacao em teste live opt-in.
- [ ] Testar `ProcessoNumero` com numero publico.
- [ ] Manter download por `Id_Arquivo` como pendente ate contrato limpo.
