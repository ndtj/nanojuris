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
GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>
```

Status tecnico das rotas:

| Rota | Conteudo juridico | Condicao segura de uso | Status no provider |
| --- | --- | --- | --- |
| `POST /resultadoCompleta.do` | Sim, quando retorna container de resultado | Rota principal; se voltar formulario/captcha, parar | Implementada |
| `GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>` | Sim, fragmentos paginados com ementas, processos e `cdAcordao` | Apenas depois de um `POST /resultadoCompleta.do` publico e valido na mesma sessao | Implementada como continuacao segura |
| `GET /trocaDePagina.do?...` em sessao limpa | Nao | Retorna `emptySession.jsp`; tratar como sessao ausente | Diagnosticada como controle de acesso |
| `GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>` | Sim, quando o inteiro teor esta publico | Se redirecionar para CAS/login, marcar `login_required` | Implementada com diagnostico |
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

## Pontos fortes

- Fonte juridicamente muito relevante.
- Padrao reutilizavel para a familia CJSG/e-SAJ de outros tribunais.
- Suporta documentos publicos quando a rota de inteiro teor esta acessivel.

## Lacunas a aprofundar

- Separar rotas de pesquisa, detalhe e inteiro teor.
- Descrever mensagens seguras para MCP quando houver controle de acesso.
- Ampliar fixtures por classe, orgao julgador e variacoes de ementa.

## MCP e agentes

Recomendacao: fonte de alto valor, mas risco operacional alto. O agente deve
tratar `AccessControlRequiredError` como evento esperado e sugerir outra fonte
publica quando a consulta for bloqueada.

## Fixtures esperadas

- resultado CJSG com ementa;
- pagina com captcha/access-control;
- pagina de zero resultado;
- inteiro teor publico;

## Proximos passos

- [x] Criar fixture especifica para `diagnose_cjsg_access`.
- [x] Criar fixture de zero resultado.
- [x] Criar fixture de inteiro teor publico com hash e tamanho.
- [x] Adicionar teste de fragmento `trocaDePagina.do`.
- [x] Adicionar teste de `emptySession.jsp`.
- [x] Marcar `getArquivo.do` redirecionado para login como `login_required`.
- [ ] Documentar variacoes de `classe/assunto` por area.
- [ ] Promover dossie da familia CJSG/e-SAJ para ser reutilizado por TJAC,
  TJAL, TJAM e TJMS.
