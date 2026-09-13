# `tjsp_cjsg`

## Identidade

- Fonte oficial: pesquisa publica de jurisprudencia CJSG/e-SAJ do TJSP.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- Uso preferencial: jurisprudencia estadual paulista quando a fonte publica nao
  exigir controle de acesso.
- Nivel atual esperado: 3.

## Contrato conhecido

O provider cobre busca textual, ementa/resumo, numero CNJ, intervalo de data,
tipo de decisao e inteiro teor quando publico. A fonte pode exigir captcha,
validacao de acesso ou rotas de controle; o NanoJuris deve reportar isso sem
bypass.

Quando `getArquivo.do` retorna HTML publico, `get_document` converte a pagina em
texto limpo para agentes de IA e preserva hash, tamanho, URL, tipo de origem e
warnings nos metadados. Se a fonte retornar PDF puro, o provider registra o
estado como nao parseado em vez de fingir que leu o conteudo.

Rotas declaradas:

```text
POST /resultadoCompleta.do
GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>
GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>&casChecked=true
```

Status tecnico das rotas:

| Rota | Conteudo juridico | Condicao segura de uso | Status no provider |
| --- | --- | --- | --- |
| `POST /resultadoCompleta.do` | Não; confirmação da submissão e criação da sessão | Enviar uma vez; interpretar o conteúdo somente no GET seguinte | Implementada |
| `GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>` | Sim, fragmentos paginados com ementas, processos e `cdAcordao` | Apenas depois de um `POST /resultadoCompleta.do` publico e valido na mesma sessao | Implementada como continuacao segura |
| `GET /trocaDePagina.do?...` em sessao limpa | Nao | Retorna `emptySession.jsp`; tratar como sessao ausente | Diagnosticada como controle de acesso |
| `GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>&casChecked=true` | Sim, quando o inteiro teor esta publico | Continuacao oficial do fluxo anonimo; sem token ou login | Implementada com cabeçalhos de navegador e diagnóstico |
| `POST /captchaControleAcesso.do` | Nao | Rota de controle; nunca usar para bypass | Apenas documentada |

Payload principal da busca:

```text
dados.buscaInteiroTeor=<texto livre>
dados.buscaEmenta=<trecho exato quando informado>
dados.nuProcOrigem=<numero CNJ quando informado>
dados.dtJulgamentoInicio=<data inicial>
dados.dtJulgamentoFim=<data final>
tipoDecisaoSelecionados=<A|M|H>
dados.ordenarPor=dtPublicacao
```

Mapeamento de tipo decisorio:

| Entrada | Codigo enviado |
| --- | --- |
| `A`, `acordao` | `A` |
| `M`, `monocratica` | `M` |
| `H`, `homologacao` | `H` |

Campos extraidos:

- numero do processo;
- tipo decisorio;
- classe/assunto;
- comarca;
- orgao julgador;
- relator;
- data de registro/publicacao;
- ementa/resumo;
- `cd_acordao`;
- `cd_foro`;
- URL publica de inteiro teor quando disponivel.

## Diagnostico de acesso

O provider classifica sinais do HTML sem resolver nenhum controle:

| Sinal | Campo tecnico |
| --- | --- |
| Container de resultado | `has_result_container` |
| Links de ementa/arquivo | `has_download_links` |
| Formulario de busca retornado | `has_search_form` |
| Campo reCAPTCHA | `has_recaptcha_field` |
| Campo uuidCaptcha | `has_uuid_captcha_field` |
| Widget reCAPTCHA | `has_recaptcha_widget` |
| Rota de controle de acesso | `has_access_control_route` |
| Script de login/SAJ | `has_login_script` |
| Sessao vazia do CJSG | `has_empty_session` |

Se houver sinais de captcha/controle sem container de resultado, o provider
levanta `AccessControlRequiredError`.

## Dados

O CJSG/e-SAJ retorna resultados HTML com metadados textuais e links de
documento. A normalizacao deve preservar a distincao entre ementa, campos de
cabecalho e inteiro teor.

| Campo observado | Campo canonico | Observacao |
| --- | --- | --- |
| Numero do processo | `process_number` | deve ser normalizado sem perder a forma exibida |
| Classe/assunto | `class_name`, `subject`, `raw` | em alguns layouts aparece como bloco unico; preservar bruto |
| Comarca/origem | `origin` | nao confundir comarca com orgao julgador |
| Orgao julgador | `judging_body` | camara, turma ou colegiado quando exibido |
| Relator | `reporting_judge` | remover label, preservar nome como exibido |
| Data de julgamento/publicacao/registro | `judgment_date`, `publication_date`, `raw` | nunca usar uma data como substituta silenciosa da outra |
| Ementa/resumo | `summary` | ementa da lista, nao inteiro teor |
| `cdAcordao` e `cdForo` | `raw`, `document_url` | identificadores tecnicos para URL oficial |
| HTML/PDF do arquivo | `CanonicalDocument` | somente quando rota de documento responder publicamente |

Regras de integridade:

- `getArquivo.do` deve calcular hash e tamanho a partir dos bytes originais
  antes de qualquer conversao de texto;
- PDF binario deve ser classificado como documento binario nao parseado ate
  existir parser especifico;
- pagina de login, CAS, captcha ou `emptySession.jsp` nao pode gerar
  `summary` vazio nem documento publico;
- paginacao via `trocaDePagina.do` so e valida na mesma sessao de uma busca
  principal publica bem-sucedida.

## Estados de resposta

| Estado | Como o provider deve tratar |
| --- | --- |
| Resultado publico | Retornar `SearchPage` com metadados e URL de inteiro teor. |
| Zero resultado | Retornar pagina vazia quando a fonte indicar resultado sem itens. |
| Captcha/controle | Levantar `AccessControlRequiredError` com flags diagnosticas. |
| Paginacao sem sessao | Levantar `AccessControlRequiredError` indicando sessao publica ausente. |
| Inteiro teor redirecionado para login/CAS | Retornar `CanonicalDocument` parcial com `access_status=login_required`. |
| HTTP 429 | Levantar `RateLimitDetectedError`. |
| HTTP 5xx | Levantar `SourceUnavailableError`. |
| HTML com total mas sem itens | Levantar `ParserContractChangedError`. |

## Auditoria de rotas 2026-08-07

Equipe tecnica aplicada:

| Papel | Atividade |
| --- | --- |
| Arquiteto de fontes judiciais | Separou busca principal, paginacao, inteiro teor e controle de acesso. |
| Engenheiro de scraping responsavel | Testou as rotas sem reutilizar token do HAR e sem contornar captcha/login. |
| Engenheiro de qualidade | Transformou os achados em testes de parser, sessao vazia e status de documento. |
| Especialista MCP/IA | Garantiu que agentes recebam `login_required`/`access_control_required` em vez de texto vazio enganoso. |

Achados:

- `resultadoCompleta.do` e a rota oficial de busca. Em ambiente live sem token
  de navegador, pode retornar formulario com sinais de controle de acesso.
- `trocaDePagina.do` traz conteudo jurisprudencial valido em fragmento HTML,
  mas depende de sessao criada por uma busca publica anterior. Em sessao limpa,
  retorna `emptySession.jsp`.
- `getArquivo.do` pode redirecionar para `verificarLoginArquivo.jsp` e CAS/login.
  Nesse caso, o provider nao deve classificar o documento como publico.
- `captchaControleAcesso.do` retorna estado de controle de acesso, nao conteudo
  juridico; permanece fora do fluxo de extracao.

Decisao de produto:

- Promover a paginacao somente como continuacao de uma busca principal valida.
- Nao usar `trocaDePagina.do` para extrair resultados quando a busca principal
  indicou captcha, validacao ou retorno ao formulario.
- Manter `tjsp_cjsg` como fonte de alto valor e risco operacional alto, com
  diagnosticos claros para CLI, Python e MCP.

### Rechecagem bounded (2026-09-01, ciclo 11)

Uma chamada POST publica para `resultadoCompleta.do` foi bloqueada pela
superficie: o diagnostico encontrou formulario, reCAPTCHA, UUID de captcha,
rota de controle e script de login. O estado foi registrado como
`blocked_access`; nenhum desafio foi contornado e nenhum corpo live foi salvo.
Metadados: `docs/provider-discovery/tjsp-cjsg-live-recheck-20260901-cycle11.json`.

## Pontos fortes

- Fonte juridicamente muito relevante.
- Padrao reutilizavel para a familia CJSG/e-SAJ de outros tribunais.
- Suporta documentos publicos quando a rota de inteiro teor esta acessivel.

### Alinhamento Juscraper (2026-09-01, ciclo 12)

O POST de `resultadoCompleta.do` apenas cria a sessao publica; a resposta vem
de `GET /trocaDePagina.do?...&pagina=1` e das paginas seguintes na mesma
sessao. O `conversationId` da primeira pagina e propagado em memoria no TJSP.

### Revalidação pública (2026-09-06)

O fluxo público foi revalidado sem credenciais: HTTP 200, uma ementa textual de
segundo grau, total reportado de 2741745 registros e detalhe público (`valid`).
Evidência redigida:
`docs/provider-discovery/cjsg-live-legitimate-recheck-20260906.json`.

## Lacunas a aprofundar

- Separar rotas de pesquisa, detalhe e inteiro teor.
- Descrever mensagens seguras para MCP quando houver controle de acesso.
- Ampliar fixtures por classe, orgao julgador e variacoes de ementa.

## MCP e agentes

Recomendacao: fonte de alto valor, mas risco operacional alto. O agente deve
tratar `AccessControlRequiredError` como evento esperado e sugerir outra fonte
publica quando a consulta for bloqueada.

## Fixtures esperadas

- `tests/fixtures/tjsp_cjsg_result.html` cobre resultado CJSG com ementa;
- `tests/fixtures/tjsp_cjsg_access_control.html` cobre captcha/access-control;
- `tests/fixtures/tjsp_cjsg_empty.html` cobre zero resultado;
- `tests/fixtures/tjsp_cjsg_document.html` cobre inteiro teor HTML publico;

## Proximos passos

- [x] Criar fixture especifica para `diagnose_cjsg_access`.
- [x] Criar fixture de zero resultado.
- [x] Criar fixture de inteiro teor publico com hash e tamanho.
- [x] Adicionar teste de fragmento `trocaDePagina.do`.
- [x] Adicionar teste de `emptySession.jsp`.
- [x] Marcar `getArquivo.do` redirecionado para login como `login_required`.
- [x] Documentar variacoes de `classe/assunto` por area; o parser preserva os
  dois campos separadamente e o fixture cobre classe criminal/assunto.
- [x] Promover o dossie da familia CJSG/e-SAJ para TJAC, TJAL, TJAM e TJMS;
  os adapters reutilizam o contrato comum sem compartilhar estado de sessão.
