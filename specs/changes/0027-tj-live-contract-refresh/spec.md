# 0027 — Atualização dos contratos live dos providers TJ

Status: `in_progress`

## Intenção

Usar a descoberta live bounded e os artefatos REA disponíveis para melhorar a
precisão operacional dos providers de tribunais estaduais, começando pela
família eproc compartilhada por TJSP, TJRJ e TJSC.

## Escopo

- registrar a rota pública de formulário de jurisprudência eproc nas
  capabilities dos adapters;
- preservar o diagnóstico explícito de CAPTCHA, WAF, login, robots e
  indisponibilidade;
- versionar a evidência live bounded dos 26 providers `tj*` atualmente
  implementados;
- alinhar dossiês, contratos, testes e catálogo gerado.

Fora de escopo: bypass de CAPTCHA/WAF/login, reutilização de cookies ou tokens,
submissão de POSTs adivinhados, coleta massiva, novos adapters sem contrato e
alteração de regras de acesso das fontes.

## Requisitos

- `REQ-001`: TJSP, TJRJ e TJSC eproc devem declarar a rota GET pública de
  pesquisa observada, além das rotas de resultado e documento.
- `REQ-002`: a descoberta live deve permanecer bounded, respeitar robots e não
  submeter POST sem payload contratado.
- `REQ-003`: estados de acesso, vazio, robots, redirect e indisponibilidade
  devem permanecer distintos e auditáveis.
- `REQ-004`: a evidência live dos providers `tj*` deve ser versionada com data,
  limites e interpretação explícita.
- `REQ-005`: testes devem impedir regressão da rota GET declarada e da política
  de não-bypass.

## Critérios de aceite

- `AC-001`: capabilities e dossiês eproc declaram a mesma rota de formulário.
- `AC-002`: a suíte cobre a nova declaração nos três adapters e mantém os
  testes de acesso controlado.
- `AC-003`: o relatório bounded registra 26 providers, 87 rotas declaradas,
  172 filtros declarados e 5 observações de controle de acesso.
- `AC-004`: auditoria SDD, documentação, cobertura e testes passam.
- `AC-005`: nenhum código tenta resolver CAPTCHA, fabricar token ou ignorar
  robots/WAF/login.
