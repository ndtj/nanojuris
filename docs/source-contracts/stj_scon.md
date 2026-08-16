# `stj_scon`

## Identidade

- Fonte oficial: pesquisa publica de acordaos STJ/SCON.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_jurisprudencia_superior`.
- Uso preferencial: acordaos do STJ quando a pagina publica responder sem
  validacao de acesso.
- Nivel atual esperado: 3.

## Contrato conhecido

O HAR publico analisado em 06/08/2026 mostrou que a busca principal de acordaos
usa `GET /SCON/pesquisar.jsp` com parametros na query string. O escopo atual
cobre lista de resultados, parser por fixture HTML publica representativa e parser da
estrutura real `.documento` observada no HAR e carga sob demanda do documento
oficial. `get_document()` aceita o id estavel `stj-scon-<numero_registro>` ou
a URL oficial preservada em `raw.document_url`, calcula o hash dos bytes
recebidos e extrai texto de PDF quando o suporte `pypdf` esta instalado.

Um HAR complementar recebido em 06/08/2026 confirmou que o frontend tambem usa
rotas auxiliares para filtros, sugestoes e selecao de documento. Elas entram no
dossie como contrato observado, mas nao sao promovidas automaticamente como API
estavel ate serem reduzidas a fixtures e testes:

```text
GET  /SCON/SearchFiltroBRS
GET  /SCON/jurisprudencia/pesquisaAjax.jsp
POST /SCON/ActionSelecionaDocumento
GET  /SCON/GetInteiroTeorDoAcordao
```

O mesmo HAR carregou recursos de reCAPTCHA, Cloudflare Insights, Dynatrace,
Google Analytics e scripts do portal. Esses recursos sao sinais de controle e
telemetria do frontend; nao devem ser copiados para o provider nem usados para
bypass.

Parametros principais declarados pelo provider:

```text
b=ACOR
p=true
l=<page_size>
i=<page>
ordenacao=-@DOCN
thesaurus=JURIDICO
O=JT
livre=<texto livre quando informado>
processo=<numero quando informado>
```

Observacao: o HAR recebido tambem continha `preConsultaPP=<id>` para uma
pesquisa pronta especifica. Esse parametro e tratado como contexto da pagina
navegada, nao como contrato geral para busca textual livre.

Campos extraidos quando o HTML segue o contrato esperado:

- numero do processo;
- numero de registro;
- classe/tipo decisorio;
- relator;
- orgao julgador;
- data de julgamento;
- data de publicacao;
- ementa/resumo;
- URL oficial do documento quando houver link no resultado.

Seletores principais observados no HTML real:

| Campo | Seletor/Padrao |
| --- | --- |
| Item de resultado | `.documento` |
| Cabecalho do item | `.clsHeaderDocumento` |
| Identificacao curta | `.clsIdentificacaoDocumento` |
| Pares campo/valor | `.paragrafoBRS` com `.docTitulo` e `.docTexto` |
| Inteiro teor | `javascript:inteiro_teor('/SCON/GetInteiroTeorDoAcordao?...')` |
| Processo relacionado | `javascript:processo('https://processo.stj.jus.br/processo/pesquisa/?num_registro=...')` |

Rotas auxiliares observadas no HAR complementar:

| Rota | Papel observado | Status no provider |
| --- | --- | --- |
| `/SCON/SearchFiltroBRS` | busca/filtro BRS com `livre`, `b`, `l`, `i`, `operador`, `ordenacao` | declarada em capabilities, ainda nao usada como rota primaria |
| `/SCON/jurisprudencia/pesquisaAjax.jsp` | chamadas Ajax da tela de pesquisa por `livre`, `operador`, `pagina` e tipo | contrato observado, aguarda fixture especifica |
| `/SCON/ActionSelecionaDocumento` | acao de selecao/abertura de documento | contrato observado, nao usado como rota primaria |
| `/SCON/GetInteiroTeorDoAcordao` | documento oficial HTML/PDF por `num_registro` | implementado em `get_document()` |

## Dados

A superficie SCON mistura identificacao do documento, metadados processuais,
ementa e links JavaScript para rotas internas. O provider deve extrair somente
o que estiver presente no HTML retornado.

| Campo observado | Campo canonico | Observacao |
| --- | --- | --- |
| `.clsIdentificacaoDocumento` | `title`, `raw.short_identifier` | identificacao exibida pelo STJ |
| Processo | `process_number` | preservar numero exibido e normalizacao CNJ quando possivel |
| Registro | `raw.registry_number`, id estavel | deve ter prioridade na identidade persistente |
| Classe/tipo | `class_name`, `decision_type` | nao inferir base quando a rota for diferente de acordaos |
| Relator | `reporting_judge` | nome como exibido no resultado |
| Orgao julgador | `judging_body` | turma, secao ou corte quando presente |
| Data de julgamento | `judgment_date` | data propria, separada de publicacao |
| Data de publicacao | `publication_date` | data propria, separada de julgamento |
| Ementa | `summary` | texto da ementa/lista, nao inteiro teor completo |
| `inteiro_teor(...)` | `document_url`, `raw` | link oficial; carga sob demanda pode retornar HTML ou PDF |
| `processo(...)` | `raw.process_url` | acompanhamento processual, contexto auxiliar |

Regras de identidade e datas:

- a identidade persistente deve usar `registry_number`, depois
  `process_number` normalizado, depois hash estavel dos campos oficiais;
- indice de pagina jamais deve ser usado como ID persistente;
- `publication_date` e `judgment_date` devem permanecer separados;
- operadores STJ em `livre` devem ser preservados, nao traduzidos por
  heuristica juridica do NanoJuris.

## Estados de resposta

| Estado | Como o provider deve tratar |
| --- | --- |
| Resultado publico | Retornar `SearchPage` com `CanonicalDecision` derivavel. |
| Zero resultado | Retornar `SearchPage` vazia quando o HTML indicar ausencia de resultado. |
| Captcha/controle de acesso | Levantar `AccessControlRequiredError`. |
| Verificacao automatica STJ/Cloudflare | Levantar `AccessControlRequiredError`; nao tentar bypass. |
| HTTP 429 | Levantar `RateLimitDetectedError`. |
| HTTP 5xx | Levantar `SourceUnavailableError`. |
| HTML sem container esperado | Levantar `ParserContractChangedError`. |

## Inteiro teor

O documento e carregado sob demanda, nunca automaticamente para todos os
resultados da busca. O retorno canonico informa `content_type`, `text`,
`sha256`, `byte_size`, `access_status`, `extraction_status` e os traces HTTP e
de extracao. Os bytes originais permanecem preservados em
`CanonicalDocument.raw_bytes`. Uma URL existente ou resposta HTTP 200 sem
conteudo documental nao e promovida como texto integral.

## Teste De Conexao Limpa

Em 06/08/2026, uma sessao limpa sem cookies foi testada contra:

```text
GET /SCON/pesquisar.jsp?b=ACOR&p=true&l=10&i=1&ordenacao=-@DOCN&thesaurus=JURIDICO&livre=publicidade+alimentos+criancas&O=JT
```

Resultado observado a partir deste ambiente: HTTP 403 com mensagem de
verificacao automatica e exigencia de JavaScript/cookies. Esse estado e
esperado em ambientes automatizados e deve ser reportado pelo provider sem
contorno.

## Pontos fortes

- Fonte institucional de alto valor para jurisprudencia superior.
- Parser preserva `SourceTrace` e campos objetivos.
- Parser cobre tanto a fixture simplificada quanto a estrutura real `.documento`
  observada no HAR.
- O provider evita reinterpretar operadores oficiais do STJ.

## Lacunas a aprofundar

- Separar acordaos, monocraticas, sumulas e informativos como superficies
  tecnicas diferentes.
- Ampliar fixtures de monocraticas, sumulas e informativos.
- Adicionar fixture binaria de PDF publico e ampliar a verificacao de completude.
- Documentar operadores oficiais com exemplos seguros.

## MCP e agentes

Recomendacao: fonte estrategica, mas ainda inicial. O agente deve:

- consultar `source_contracts("stj_scon")` antes da busca;
- avisar que a fonte pode exigir validacao de acesso;
- usar `page_size` pequeno;
- preservar operadores STJ fornecidos pelo usuario sem "traduzir" juridicamente;
- sugerir fontes alternativas quando receber `AccessControlRequiredError`.

## Fixtures esperadas

- `tests/fixtures/stj_scon_acordaos_result.html` implementada;
- `tests/fixtures/stj_scon_real_documentos.html` implementada;
- `tests/fixtures/stj_scon_access_control.html` implementada;
- `tests/fixtures/stj_scon_empty.html` implementada;
- fixture de inteiro teor publico ainda deve ser adicionada sem cookies ou
  credenciais; a implementacao offline ja cobre o contrato de bytes.

## Proximos passos

- [x] Capturar HAR publico limpo de busca simples.
- [x] Reduzir headers ao minimo necessario.
- [x] Documentar parametros obrigatorios/opcionais em detalhe.
- [x] Adicionar fixtures de acesso controlado e vazio.
- [x] Reavaliar nivel de contrato para 3 quando o dossie HTTP estiver completo.
- [x] Mapear HAR complementar com rotas `SearchFiltroBRS`, `pesquisaAjax.jsp` e
  `ActionSelecionaDocumento`.
- [x] Implementar `get_document()` com hash, tamanho, content-type e bytes
  originais preservados.
- [ ] Criar teste live opt-in para registrar `AccessControlRequiredError` quando
  a origem exigir verificacao automatica.
