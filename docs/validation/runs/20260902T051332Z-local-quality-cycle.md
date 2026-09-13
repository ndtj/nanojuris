# Rodada local de fechamento e qualidade — 2026-09-02

Status: `concluída_localmente`

Esta evidência registra a única onda local executada antes de qualquer
commit, push ou deploy. Nenhuma credencial foi usada e nenhuma infraestrutura
foi aplicada.

## Escopo executado

- Reconciliação da topologia nacional e da matriz CJPG/CJSG.
- Regeneração dos catálogos, contratos, auditorias de documentação, ledger de
  fechamento e work-packs SDD a partir das fontes versionadas.
- Verificação estática, testes determinísticos, empacotamento e smoke público
  bounded dos adapters que possuem contrato reproduzível.
- Validação local da plataforma e do Terraform de desenvolvimento sem
  `plan`, `apply`, alteração de OCI ou publicação.

## Resultados da biblioteca

| Gate | Resultado |
| --- | --- |
| Suíte padrão | 1.043 passed, 12 skipped |
| Suíte com smoke público habilitado | 1.054 passed, 1 skipped |
| Cobertura (`pytest-cov`) | 85,51% (gate mínimo 85%) |
| Ruff lint | PASS |
| Ruff format | PASS |
| mypy | PASS (103 módulos) |
| SDD | PASS (62 pacotes) |
| Build sdist/wheel | PASS (`nanojuris-0.4.0`) |
| `twine check` | PASS |
| Limite de assets estáticos | PASS (213.073/300.000 bytes) |

## Smoke público reproduzível

Passaram com resposta real e `SourceTrace` verificável:

- BNP/Pangea (3 cenários);
- TJES/CJPG e TJES/CJSG;
- TJSP/CJPG;
- rechecks de STJ, STF, TJBA, CJF/TRF1, TJPE, TJSP/CJSG e TRF3.

O TJSP/CJSG foi tratado conforme o contrato: resultado válido quando
disponível ou `AccessControlRequiredError` explícito para CAPTCHA/controle de
acesso. Nenhum controle foi contornado.

## Estado dos artefatos

- Catálogo: 59 fontes, 50 runtime, 8 candidatas e 1 família; snapshot
  reconciliado em `2026-09-02`.
- Busca unificada: 43 fontes habilitadas; matriz regenerada com 50 adapters.
- Auditoria offline: 50/50 runtime com fixture versionada; 8 candidatas ainda
  sem adapter.
- Ledger: 109 itens, 68 com evidência local, 27 bloqueados externamente e 14
  candidatos pendentes de adapter.
- Matriz por grau: 148 superfícies mapeadas, 107 lacunas; cobertura medida
  separadamente para CJPG, CJSG, EPROC, JURISPRUDENCIA, PORTAL e SJUR.

## Plataforma e infraestrutura

- Plataforma: 143 testes, Ruff lint/format e mypy PASS.
- Infraestrutura: Terraform `fmt -check` e `validate` PASS para bootstrap e
  dev; SDD (37 pacotes) e guardrails PASS.
- Nenhum `terraform plan/apply`, deploy, push ou commit foi executado.

## Pendências que não podem ser fechadas nesta onda

Os itens abaixo permanecem visíveis no ledger/work-packs e não foram
convertidos artificialmente em sucesso:

1. novas evidências live para fontes com CAPTCHA, WAF, SSO, robots ou
   indisponibilidade;
2. contratos e adapters das 8 fontes candidatas e as lacunas de cobertura
   CJPG/CJSG/SJUR;
3. revisão legal/termos de uso, aprovação de Domain Owner e demais gates
   humanos;
4. pin da plataforma para o SHA da lib após o merge da release;
5. `terraform plan/apply`, publicação PyPI/OCI, migração de produção e smoke
   autenticado do domínio público.

Esses estados são bloqueios externos ou ações de release, não falhas
silenciosas. O ponto de retomada está em
`docs/provider-discovery/provider-closure-ledger.md` e nos work-packs de
`specs/changes/0035-provider-completion-autopilot/`.
