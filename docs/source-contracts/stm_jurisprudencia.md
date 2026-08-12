# `stm_jurisprudencia`

## Identidade e escopo

- Fonte oficial: portal de Jurisprudencia da Justica Militar da Uniao / STM.
- Categoria: `court_jurisprudence`.
- Familia tecnica: busca HTML com facetas + documento HTML eproc.
- Busca: `https://jurisprudencia.stm.jus.br/consulta.php`.
- Processo publico relacionado: rota `processo_seleciona_publica` no eproc.
- Status no NanoJuris: provider implementado, com busca, paginacao remota e
  inteiro teor.
- A fonte e setorial: resultados do STM nao representam a jurisprudencia dos
  demais ramos da Justica.

## Canais publicos observados

| Canal | Metodo | Finalidade | Estado no provider |
| --- | --- | --- | --- |
| `/consulta.php` | `GET` | busca, filtros, facetas e paginas HTML | implementado |
| `/externo_controlador.php?acao=visualizar_acordao&uuid=<uuid>` no eproc STM | `GET` | inteiro teor do acordao | implementado |
| `/externo_controlador.php?acao=processo_seleciona_publica&acao_origem=busca_jurisprudencia&num_processo=<cnj_sem_pontuacao>` | `GET` | abrir processo publico relacionado | URL preservada, nao seguido automaticamente |
| botoes `referencia_legislativa`, `notas` e `thesaurus` | modal acionado por HTML/JS | referencias, notas e indexacao | observados; endpoint modal ainda nao promovido |

O provider nao usa cookies pessoais, login, captcha, proxy de contorno ou
tecnica de evasao. Se a fonte responder com bloqueio, login, captcha ou erro,
o resultado deve ser classificado como indisponivel/controle de acesso.

## Contrato de busca HTTP

URL base:

```text
GET https://jurisprudencia.stm.jus.br/consulta.php
```

Parametros usados pelo provider:

| Parametro | Obrigatorio | Significado | Mapeamento atual |
| --- | --- | --- | --- |
| `search_filter_option=jurisprudencia` | sim | seleciona o acervo de jurisprudencia | fixo |
| `search_filter=busca_avancada` | sim | seleciona o modo de busca avancada | fixo |
| `q` | sim | termo geral; o provider usa `*` quando vazio | `text` |
| `fqx_ementa` | nao | busca textual dirigida a ementa | `exact_phrase` ou `text` |
| `fqx_numero_jurisprudencia` | nao | identificador/numero da jurisprudencia | `number` |
| `fqx_data_publicacao_inicio` | nao | inicio do intervalo de publicacao | `published_from` |
| `fqx_data_publicacao_fim` | nao | fim do intervalo de publicacao | `published_to` |
| `fqx_data_decisao_inicio` | nao | inicio do intervalo de julgamento | `updated_from` |
| `fqx_data_decisao_fim` | nao | fim do intervalo de julgamento | `updated_to` |
| `start` | sim para pagina | deslocamento zero-based | `(page - 1) * page_size` |
| `rows` | sim para pagina | quantidade solicitada na pagina | `page_size` |

Formato de data observado no portal: `DD/MM/AAAA`. O STM mostra na interface
as opcoes 25, 50 e 100 registros por pagina; uma consulta HTTP com `rows=2`
tambem foi reproduzida. O provider deve manter `page_size` pequeno em uso
interativo e respeitar `rate_limit_interval`.

### Facetas e filtros descobertos no portal

O HTML de resultados publica links de faceta com os seguintes nomes:

| Faceta observada | Parametro | Estado |
| --- | --- | --- |
| classe processual | `fq_classe` | documentado; ainda nao exposto no modelo unificado |
| assunto/indexacao | `fq_assunto_pesquisa` | documentado; ainda nao exposto no modelo unificado |
| ministro relator | `fq_ministro_relator` | documentado; ainda nao exposto no modelo unificado |
| relator do acordao | `fq_ministro_relator_acordao` | documentado; ainda nao exposto no modelo unificado |
| ministro revisor | `fq_ministro_revisor` | documentado; ainda nao exposto no modelo unificado |
| data de autuacao | `fq_data_autuacao` | documentado; ainda nao exposto no modelo unificado |
| data de decisao | `fq_data_decisao` | documentado; ainda nao exposto no modelo unificado |
| data de publicacao | `fq_data_publicacao` | documentado; ainda nao exposto no modelo unificado |

Esses nomes foram observados em links publicos de refinamento. Eles nao devem
ser confundidos automaticamente com os parametros `fqx_*` enviados pelo
formulario avancado. Antes de promover cada faceta para a API publica do
NanoJuris, deve existir fixture e teste de contrato para o valor e o retorno.

## Resposta de busca

O retorno e HTML, com um painel por resultado. O provider reconhece:

- `div.panel.panel-default` como container;
- botao `title="Exibir Inteiro Teor"` e seu `onclick` como origem do UUID e da
  URL do documento;
- `dl` com pares `dt`/`dd` para relator, revisor e assuntos;
- numero CNJ no texto do painel;
- ementa em `blockquote`;
- datas de autuacao, julgamento e publicacao no corpo do painel;
- classe processual inferida do bloco que acompanha o numero do processo;
- botao de processo publico com `acao=processo_seleciona_publica`.

A pagina tambem exibe texto no formato `1 - 2 de 1017 documentos`. O parser
`parse_stm_total_documents` preserva esse total remoto no `SearchPage.total`.
Se o marcador nao existir, o provider usa a quantidade de paineis parseados e
o trace deve ser interpretado como contagem parcial.

## Campos canonicos

| Origem STM | Campo NanoJuris | Observacao |
| --- | --- | --- |
| numero CNJ no painel | `number` / `case_number` | extraido por regex CNJ |
| `data-id`/UUID do painel | `external_id` / `uuid` | necessario para inteiro teor |
| classe no bloco do processo | `raw.case_class` | pode variar de rotulagem |
| `Relator(a)` | `rapporteur` | preservado em `raw.labels` |
| `Revisor(a)` | `raw.reviewer` | campo bruto para nao perder informacao |
| `Assuntos` | `raw.subject` | campo bruto; pode conter varios assuntos |
| `Data de Julgamento` | `raw.judgment_date` | formato textual do portal |
| `Data de Publicacao` | `publication_date` e `raw.publication_date` | data de publicacao normalizada; o valor original permanece em `publication_date_raw` |
| `blockquote` | `summary` | ementa/resumo da decisao |
| URL do botao de inteiro teor | `raw.document_url` | URL oficial eproc |
| URL do processo | `raw.process_url` quando disponivel | atualmente preservada pelo HTML |

O `raw` deve ser preservado porque o portal possui campos auxiliares de
referencia legislativa, notas e indexacao que ainda nao fazem parte de
`JurisprudenceResult`.

## Inteiro teor

```text
GET https://eproc2g.stm.jus.br/eproc_2g_prod/externo_controlador.php
    ?acao=visualizar_acordao&uuid=<uuid>
```

O provider retorna `CanonicalDocument` e `DecisionBundle` com `text/html`,
`AccessStatus.PUBLIC` quando a resposta e valida, e `SourceTrace` com o UUID.
O documento pode ser grande; o MCP deve oferecer o texto sob demanda e nao
incluir inteiro teor de todos os resultados numa resposta de busca.

## Estados e erros

| Estado | Comportamento esperado |
| --- | --- |
| sucesso | paineis parseados; total remoto e pagina preservados |
| vazio | retorna lista vazia quando o HTML traz marcador de nenhum resultado |
| HTML sem paineis | `ParserContractChangedError`, pois o contrato mudou ou a resposta nao e busca |
| HTTP 401/403, captcha ou login | `AccessControlRequiredError` |
| HTTP 429 | `RateLimitDetectedError` |
| HTTP 5xx ou erro de rede | `SourceUnavailableError` |
| inteiro teor indisponivel | erro de fonte/controle de acesso, sem bypass |

## Limites e responsabilidade

- A paginacao oficial observada e baseada em deslocamento `start`, nao em
  pagina zero/um do NanoJuris; o adapter converte `page` para offset.
- A busca por `*` pode ser ampla; agentes devem exigir termo ou filtro em
  consultas exploratorias e usar `page_size` pequeno.
- Facetas sao parte do HTML e podem mudar sem versionamento.
- Inteiro teor, notas, indexacao e referencias podem conter dados pessoais ou
  dados sensiveis publicados pela fonte; o NanoJuris nao mascara o conteudo
  publico, mas deve preservar a origem e o contexto.
- Resultados do STM devem ser identificados como jurisprudencia militar da
  Uniao, sem generalizacao para outros tribunais.

## Evidencia live

Em 2026-08-11/12, consultas HTTP limpas foram reproduzidas:

- `indulto`, `start=0`, `rows=2`: HTTP 200, dois paineis e marcador de 1017
  documentos;
- `indulto`, `start=2`, `rows=2`: HTTP 200, dois paineis diferentes;
- o inteiro teor de um UUID retornou HTML publico com mais de 269 mil
  caracteres;
- botoes de inteiro teor, referencia legislativa, notas, indexacao e processo
  publico foram observados no mesmo painel.

Essa evidencia e uma fotografia da disponibilidade da fonte. Ela nao e
garantia de SLA nem substitui testes opt-in de rede.

## Fixtures e testes

- [x] busca com resultado e parse de painel;
- [x] busca vazia;
- [x] inteiro teor por UUID;
- [x] tratamento de labels acentuados/variantes;
- [x] controle de acesso;
- [x] parametros `start`/`rows`;
- [x] parse do total remoto quando presente;
- [ ] fixture live versionada sem dados pessoais desnecessarios;
- [ ] contrato offline das facetas `fq_*`;
- [ ] contrato offline dos modais de referencia, notas e indexacao.

## Uso pelo MCP

O MCP deve informar `source=stm_jurisprudencia`, `court=STM`, termo, filtros,
pagina, tamanho, total remoto e URL oficial. Para perguntas que dependam do
inteiro teor, a sequencia correta e buscar, selecionar o UUID e chamar o
documento sob demanda. A resposta deve separar ementa de inteiro teor e
deixar claro quando uma faceta ou canal auxiliar nao foi consultado.

## Referencias oficiais

- [Consulta de Jurisprudencia do STM](https://jurisprudencia.stm.jus.br/consulta.php?search_filter_option=jurisprudencia)
- [Portal de Jurisprudencia do STM](https://jurisprudencia.stm.jus.br/)
