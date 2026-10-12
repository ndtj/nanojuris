# 0026 — Alinhamento dos contratos TJSP observados pelo REA

Status: `in_progress`

## Intenção

Alinhar os providers `tjsp_cjsg` e `tjsp_eproc_jurisprudencia` aos fluxos
públicos observados nos artefatos de runtime do REA, preservando diagnóstico
explícito de CAPTCHA, login, WAF e demais controles de acesso.

## Escopo

- usar o entry point eproc atual como default configurável;
- enviar no CJSG datas de publicação, origens e ordenação observadas;
- representar a sequência pública de verificação de inteiro teor do CJSG sem
  resolver autenticação ou CAPTCHA;
- declarar e documentar as rotas AJAX e os filtros comprovados do eproc;
- atualizar testes, contratos, dossiês e catálogo gerado.

Fora de escopo: bypass de CAPTCHA, login, WAF, rate limit, WDAC, tokens de
navegador ou controles de autorização; coleta massiva; novas fontes; parser de
PDF; autenticação automatizada.

## Requisitos

- `REQ-001`: o eproc deve usar `https://eproc1g.tjsp.jus.br/eproc` como default,
  sem remover a possibilidade de override por configuração.
- `REQ-002`: o CJSG deve preservar `published_from/to`, `source_origin(s)` e
  `order_by` quando houver mapeamento observado no formulário público.
- `REQ-003`: o fluxo documental CJSG pode tentar apenas as rotas públicas
  observadas (`getArquivo.do`, `verificarLoginArquivo.jsp` e a repetição com
  `casChecked=true`), sempre falhando explicitamente quando a fonte exigir
  login, CAPTCHA ou outro controle.
- `REQ-004`: o eproc deve declarar as rotas de paginação, carregamento de listas
  e geração de PDF observadas, sem presumir que a geração de PDF substitui o
  inteiro teor.
- `REQ-005`: respostas bloqueadas nunca podem ser normalizadas como zero
  resultados ou documento público.
- `REQ-006`: todos os requisitos devem ter teste, documentação e evidência de
  verificação reproduzível.

## Critérios de aceite

- `AC-001`: configuração padrão, payloads e URLs canônicas refletem o contrato
  observado; overrides existentes continuam funcionando.
- `AC-002`: testes cobrem datas/origens/ordenação CJSG, sequência documental e
  filtros/rotas eproc.
- `AC-003`: testes de acesso continuam esperando `AccessControlRequiredError`
  e nenhum código tenta resolver CAPTCHA/login.
- `AC-004`: `validate_sdd.py`, auditoria documental, geração de cobertura e a
  suíte relevante passam.
- `AC-005`: a mudança é entregue via branch e PR; merge só ocorre após a
  verificação final e sem credenciais armazenadas.
